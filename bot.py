import sys
import time
from web3 import Web3
from telebot import TeleBot
from dotenv import load_dotenv
import os
import requests
import json


load_dotenv()
BOT_TOKEN = os.environ['BOT_TOKEN']
bot = TeleBot(BOT_TOKEN)
API_KEY = os.getenv('API_KEY') #API ETH network in Quicknode
API_TOKEN = os.getenv('API_TOKEN') #API info token in Quicknode
start_block = 18531032

url = f"https://holy-thrumming-cloud.quiknode.pro/{API_KEY}"
urlToken = f"https://solitary-quiet-sun.quiknode.pro/{API_TOKEN}"

def get_latest_block():
    payload = json.dumps({
    "method": "eth_blockNumber",
    "params": [],
    "id": 1,
    "jsonrpc": "2.0"
    })
    headers = {
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    block_number = response.json()["result"]

    return block_number

def get_latest_block_id(hex_string):
    integer_value = int(hex_string, 16)
    return integer_value

def get_current_block(val):
    return f"0x{hex(val)[2:]}"

def get_max_wallet_txs(contract_address):
    url = f"https://api.staysafu.org/api/simulatebuy?tokenAddress={contract_address}&chain=ETH"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()

        if "result" in data:
            result = data["result"]

            max_wallet = result.get("maxWallet", None)
            max_txn = result.get("maxTxn", None)
            buy_fee = result.get("buyFee", None)
            sell_fee = result.get("sellFee", None)
            isHoneypot = result.get("isHoneypot", None)

            return max_wallet, max_txn, buy_fee, sell_fee, isHoneypot

    return None, None, None, None, None

def get_contract_analysis(contract_address):
    url = f"https://api.staysafu.org/api/2/analysecode?tokenAddress={contract_address}&chain=ETH"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        result = data.get("result", {})
        verified = result.get("verified", False)
        social_links = result.get("socialLinks", {})
        return verified, social_links

    return False, {}

def adjust_decimals(value, decimals):
    value = float(value)
    return value / (10 ** decimals)

def convert_to_bool(value):
    return value == 0

def get_list_contracts(block_number):
    print(block_number)
    payload = json.dumps({
        "method": "trace_block",
        "params": [
            block_number
        ],
        "id": 1,
        "jsonrpc": "2.0"
    })
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    contracts = []

    if response.status_code == 200:
        data = response.json()
        if "result" in data:
            result = data["result"]

            for item in result:
                if "result" in item:
                    resultData = item["result"]
                    if resultData and "code" in resultData and resultData["code"]:
                        contracts.append(item)

    return contracts

def get_transaction_reciept(transaction):
    payload = json.dumps({
        "method": "eth_getTransactionReceipt",
        "params": [
            transaction
        ],
        "id": 1,
        "jsonrpc": "2.0"
    })
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    if response.status_code == 200:
        data = response.json()
        if "result" in data:
            result = data["result"]
            return result, result["to"]
    return None, None

def get_token_check(contract_address):
    url = f"https://api.honeypot.is/v2/IsHoneypot?address={contract_address}&forceSimulateLiquidity=true&chainID=1"
    response = requests.get(url)

    if response.status_code == 200:
        result = response.json()
        token = result.get("token", None)
        name = token.get("name", None)
        symbol = token.get("symbol", None)
        decimals = token.get("decimals", None)
        totalHolders = token.get("totalHolders", None)
        simulationSuccess = result.get("simulationSuccess", None)
        simulationError = result.get("simulationError", None)
        honeypotResult = result.get("honeypotResult", None)
        if honeypotResult is not None:
            isHoneypot = honeypotResult.get("isHoneypot", None)
        else:
            isHoneypot = None
        simulationResult = result.get("simulationResult", None)
        if simulationResult is not None:
            buyTax = simulationResult.get("buyTax", None)
            sellTax = simulationResult.get("sellTax", None)
            transferTax = simulationResult.get("transferTax", None)
            buyGas = simulationResult.get("buyGas", None)
            sellGas = simulationResult.get("sellGas", None)
        else:
            buyTax = None
            sellTax = None
            transferTax = None
            buyGas = None
            sellGas = None
        flags = result.get("flags", [])

        return name, symbol, decimals, totalHolders, simulationSuccess, simulationError, isHoneypot, buyTax, sellTax, transferTax, buyGas, sellGas, flags
    
    return None, None, None, None, None, None, None, None, None, None, None, None, None

def search_new_contracts(latest_block):
    block_transactions = get_list_contracts(latest_block)

    for transaction in block_transactions:
        tx_receipt, to = get_transaction_reciept(transaction["transactionHash"])

        if to is None and tx_receipt is not None:
            owner = tx_receipt['from']
            contract_address = tx_receipt["contractAddress"]
            name, symbol, decimals, totalHolders, simulationSuccess, simulationError, isHoneypot, buyTax, sellTax, transferTax, buyGas, sellGas, flags  = get_token_check(contract_address)

            if name is not None and symbol is not None:
                max_wallet, max_txn, buy_fee, sell_fee, isHoneypot2 = get_max_wallet_txs(contract_address)
                verified, social_links = get_contract_analysis(contract_address)
                website = social_links.get("website")
                website = str(website)
                if website.endswith('/'):
                    website = website[:-1]
                twitter = social_links.get("twitter")
                twitter = str(twitter)
                if twitter.endswith('/'):
                    twitter = twitter[:-1]
                telegram = social_links.get("telegram")
                telegram = str(telegram)
                if telegram.endswith('/'):
                    telegram = telegram[:-1]
                buyTax_display = buyTax if buyTax is not None else buy_fee
                sellTax_display = sellTax if sellTax is not None else sell_fee

                if isinstance(max_wallet, str):
                    max_wallet = float(max_wallet)
                    if max_wallet > 10**decimals:
                        max_wallet /= 10**decimals
                if isinstance(max_txn, str):
                    max_txn = float(max_txn)
                    if max_txn > 10**decimals:
                        max_txn /= 10**decimals

                if isHoneypot is None and isHoneypot2 is None:
                    isHoneypotMsg = "🍯"
                elif isHoneypot or isHoneypot2:
                    isHoneypotMsg = "🍯"
                else:
                    isHoneypotMsg = "✅"

                message = f"""
Ethereum Network: `{name}` `\({symbol}\)`

⭐️ Contract Verified: {'❌' if not verified else '✅'}
⚙️ CA: `{contract_address}`
👨‍💻 Owner: [{owner[:5]}\.\.\.{owner[-5:]}](https://etherscan.io/address/{owner})
📈 Buy Tax: `{buyTax_display if buyTax_display is not None else ""}`%
📉 Sell Tax: `{sellTax_display if sellTax_display is not None else ""}`%
💡 Transfer Tax: `{transferTax if transferTax is not None else ""}`%
⚙️ Buy Gas: {buyGas if buyGas is not None else ""}
⚙️ Sell Gas: {sellGas if sellGas is not None else ""}
💎 Max Wallet: `{max_wallet if max_wallet is not None else ""}`
💰 Max Txn: `{max_txn if max_txn is not None else ""}`
🪙 Holders: {totalHolders}

🧑🏻‍💻 Simulation Success: {'❌' if not simulationSuccess else '✅'}
🧑🏻‍💻 Simulation Error: `{simulationError}`
🧸 Check Honeypot: {isHoneypotMsg}
❌ Flag Scam: `{flags}`

📊 Chart: [Dexview](https://www.dexview.com/eth/{contract_address})

🌐 Socials: {f"[Telegram]({telegram})" if telegram is not None else ''}{f" : [Website]({website})" if website is not None else ''}{f" : [Twitter]({twitter})" if twitter is not None else ''}
            """

                print(message)

                send_telegram_message(message)

    print("Block searching done")

def send_telegram_message(message):
    bot.send_message(chat_id="@TokenFomoERC20", text=message, parse_mode="MarkdownV2")

if __name__ == "__main__":

    current_block_number = 18667153 # Get start block in ETH network

    while True:

        latest_block = get_latest_block()
        latest_block_id = get_latest_block_id(latest_block)

        if current_block_number < latest_block_id:
            try:
                current_block = get_current_block(current_block_number)
                print(f'New block detected: {current_block_number}')
                search_new_contracts(current_block)
                current_block_number += 1
            except Exception as e:
                print(f'An error occurred: {str(e)}')
                pass 
        time.sleep(7)