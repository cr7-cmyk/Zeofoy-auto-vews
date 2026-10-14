import os
import random
import threading
import time
import requests
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Safely fetching token from Render environment variables
TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN environment variable is missing! Please set it in your Render dashboard.")

CHANNEL_USERNAME = "@ZenmodsXads"  # Target Channel for Force Subscribe

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

USER_STATES = {}

def generate_fresh_user_agent():
    """Dynamically generates a fresh and randomized User-Agent string."""
    browsers = ["Chrome", "Firefox", "Safari", "Edge"]
    os_platforms = [
        ("Windows NT 10.0; Win64; x64", "AppleWebKit/537.36 (KHTML, like Gecko)"),
        ("Macintosh; Intel Mac OS X 10_15_7", "AppleWebKit/605.1.15 (KHTML, like Gecko)"),
        ("X11; Linux x86_64", "Gecko/20100101"),
        ("Windows NT 10.0; Win64; x64", "Chrome/122.0.0.0 Safari/537.36")
    ]
    browser = random.choice(browsers)
    os_p, engine = random.choice(os_platforms)
    ver_major = random.randint(115, 125)
    ver_minor = random.randint(0, 9)
    build = random.randint(1000, 9999)
    
    if browser == "Chrome":
        return f"Mozilla/5.0 ({os_p}) {engine} Chrome/{ver_major}.0.{build}.{ver_minor} Safari/537.36"
    elif browser == "Firefox":
        return f"Mozilla/5.0 ({os_p}; rv:{ver_major}.0) Gecko/20100101 Firefox/{ver_major}.0"
    elif browser == "Safari":
        return f"Mozilla/5.0 ({os_p}) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.{random.randint(0,5)} Safari/605.1.15"
    else:
        return f"Mozilla/5.0 ({os_p}) {engine} Chrome/{ver_major}.0.{build}.{ver_minor} Safari/537.36 Edg/{ver_major}.0.{build}.{ver_minor}"

def is_user_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except Exception:
        return True

def send_subscription_prompt(chat_id):
    markup = InlineKeyboardMarkup()
    join_btn = InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")
    verify_btn = InlineKeyboardButton("✅ Verify Subscription", callback_data="verify_sub")
    markup.row(join_btn)
    markup.row(verify_btn)
    
    msg_text = (
        "⚠️ *Access Denied!*\n\n"
        f"Before using this bot, you must join our official channel: {CHANNEL_USERNAME}\n\n"
        "Click the button below to join and then click 'Verify Subscription'."
    )
    bot.send_message(chat_id, msg_text, parse_mode="Markdown", reply_markup=markup)

def check_single_bin_sync(bin_num, custom_ua):
    api_url = f"https://zmshortener.xo.je/?bin={bin_num}"
    
    headers = {
        "User-Agent": custom_ua,
        "Accept": "application/json, text/plain, */*"
    }
    
    try:
        response = requests.get(api_url, headers=headers, timeout=8)
        if response.status_code == 200:
            try:
                res = response.json()
            except Exception:
                return {"status": "DEAD", "bin": bin_num, "reason": "Invalid JSON response from server"}

            if res and isinstance(res, dict):
                scheme = res.get('Scheme') or res.get('scheme') or res.get('brand') or 'Unknown'
                
                card_type = res.get('Type') or res.get('type') or ''
                card_tier = res.get('CardTier') or res.get('Brand') or res.get('tier') or res.get('category') or ''
                
                full_type = card_type
                if card_tier and card_tier.lower() != card_type.lower():
                    full_type += f" ({card_tier})"
                if not full_type:
                    full_type = "Unknown"

                bank_name = "Unknown"
                if "Issuer" in res and res["Issuer"]:
                    bank_name = res["Issuer"]
                elif isinstance(res.get('Bank'), dict):
                    bank_name = res['Bank'].get('Name') or res['Bank'].get('name') or 'Unknown'
                elif isinstance(res.get('bank'), dict):
                    bank_name = res['bank'].get('name') or 'Unknown'
                elif isinstance(res.get('Bank'), str):
                    bank_name = res['Bank']
                elif isinstance(res.get('bank'), str):
                    bank_name = res['bank']

                cou_code = 'Unknown'
                cou_name = 'Unknown'
                country_info = res.get('Country') or res.get('country')
                if isinstance(country_info, dict):
                    cou_code = country_info.get('A2') or country_info.get('alpha2') or country_info.get('code') or 'Unknown'
                    cou_name = country_info.get('Name') or country_info.get('name') or 'Unknown'
                elif isinstance(country_info, str):
                    cou_name = country_info

                if scheme != 'Unknown' or bank_name != 'Unknown':
                    return {
                        "status": "VALID",
                        "bin": bin_num,
                        "scheme": scheme,
                        "type": full_type,
                        "bank": bank_name,
                        "country_code": cou_code,
                        "country_name": cou_name
                    }
        elif response.status_code == 429:
            return {"status": "RATE_LIMITED", "bin": bin_num, "reason": "API Rate Limit (429)"}
    except requests.exceptions.Timeout:
        return {"status": "TIMEOUT", "bin": bin_num, "reason": "Request Timeout"}
    except Exception as e:
        return {"status": "DEAD", "bin": bin_num, "reason": str(e)}
        
    return {"status": "DEAD", "bin": bin_num, "reason": "Lookup failed / Not found"}

@app.route('/')
def home():
    return "ZMSHORTENER Pipeline Bot is running successfully!"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not is_user_subscribed(message.from_user.id):
        send_subscription_prompt(message.chat.id)
        return

    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("⚡ Hunt Bins", callback_data="btn_hunt"), InlineKeyboardButton("💳 Generate Cards", callback_data="btn_gen"))
    markup.row(InlineKeyboardButton("🔍 Check Bin", callback_data="btn_check"))
    
    welcome_text = (
        "🔥 *Welcome to ZMSHORTENER Tool Bot* 🔥\n\n"
        "Use buttons or commands below:\n"
        "• `/check <bin>`\n"
        "• `/hunt <prefix> <count> <country>`\n"
        "• `/gen <bin> [amount]`"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    user_id = call.from_user.id
    if call.data == "verify_sub":
        if is_user_subscribed(user_id):
            bot.answer_callback_query(call.id, "✅ Verification Successful!")
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            send_welcome(call.message)
        else:
            bot.answer_callback_query(call.id, "❌ You haven't joined the channel yet!", show_alert=True)
            
    elif call.data == "btn_hunt":
        USER_STATES[user_id] = {"action": "hunt_prefix"}
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "📥 *Hunt Setup*\n\nSend **BIN Prefix** (e.g., `4147`, `52`, `37`):", parse_mode="Markdown")
        
    elif call.data == "btn_gen":
        USER_STATES[user_id] = {"action": "gen_bin"}
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "📥 *Generator Setup*\n\nSend **BIN number**:", parse_mode="Markdown")
        
    elif call.data == "btn_check":
        USER_STATES[user_id] = {"action": "check_bin"}
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "📥 *Checker Setup*\n\nSend **BIN** to check:", parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.from_user.id in USER_STATES)
def handle_interactive_steps(message):
    user_id = message.from_user.id
    state = USER_STATES.get(user_id)
    if not state:
        return
    
    action = state.get("action")
    text = message.text.strip()
    
    if action == "hunt_prefix":
        state["prefix"] = text
        state["action"] = "hunt_count"
        bot.reply_to(message, "🔢 Send how many bins to scan (e.g., `20`, `50`):", parse_mode="Markdown")
        
    elif action == "hunt_count":
        if not text.isdigit():
            bot.reply_to(message, "⚠️ Enter a valid number.")
            return
        state["count"] = int(text)
        state["action"] = "hunt_country"
        bot.reply_to(message, "🌍 Send **Country Code** (e.g., `US`, `JP`, `BR`) or type `all`:", parse_mode="Markdown")
        
    elif action == "hunt_country":
        prefix = state.get("prefix")
        count = state.get("count")
        country = None if text.lower() == "all" else text.upper()
        
        del USER_STATES[user_id]
        
        msg = bot.reply_to(message, f"⚡ *Scanning {count} bins via zmshortener.xo.je pipeline...*", parse_mode="Markdown")
        
        length = 4 if prefix != '574' else 3
        chars = '0987654321'
        
        generated_bins = []
        for _ in range(count * 2):
            us = "".join(random.choice(chars) for _ in range(length))
            u1 = prefix + us
            if len(u1) >= 6:
                generated_bins.append(u1[:6])
        generated_bins = list(set(generated_bins))[:count]
        
        valid_records = []
        report_lines = [
            f"=== ZMSHORTENER HUNT REPORT ===",
            f"Prefix: {prefix} | Target Count: {count} | Filter Country: {country or 'ANY'}\n"
        ]
        
        current_ua = generate_fresh_user_agent()
        total_bins = len(generated_bins)
        
        for idx, b in enumerate(generated_bins, 1):
            if (idx - 1) % 4 == 0 and idx > 1:
                current_ua = generate_fresh_user_agent()
            
            try:
                progress_text = (
                    f"⚡ *Hunting in Progress...*\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"📊 Checked: `{idx}/{total_bins}`\n"
                    f"✅ Valid Found: `{len(valid_records)}`\n"
                    f"🔍 Current BIN: `{b}`\n"
                    f"━━━━━━━━━━━━━━━━━━━"
                )
                bot.edit_message_text(progress_text, chat_id=message.chat.id, message_id=msg.message_id, parse_mode="Markdown")
            except Exception:
                pass
            
            result = check_single_bin_sync(b, current_ua)
            status = result["status"]
            
            if status == "VALID":
                cou_code = result['country_code']
                if country and cou_code.upper() != country:
                    report_lines.append(f"[{idx}] BIN: {b} -> SUCCESS but Skipped (Country mismatch: {cou_code})")
                else:
                    valid_records.append(f"Bin: {result['bin']} | Scheme: {result['scheme']} | Type: {result['type']} | Country: {cou_code} ({result['country_name']}) | Bank: {result['bank']}")
                    report_lines.append(f"[{idx}] BIN: {b} -> VALID ✅ ({result['scheme']}, {result['type']}, {cou_code}, {result['bank']})")
            elif status == "RATE_LIMITED":
                report_lines.append(f"[{idx}] BIN: {b} -> FAILED ❌ (Rate Limited - 429)")
                time.sleep(1.5)
            elif status == "TIMEOUT":
                report_lines.append(f"[{idx}] BIN: {b} -> FAILED ❌ (Request Timeout)")
            else:
                report_lines.append(f"[{idx}] BIN: {b} -> DEAD ❌ ({result.get('reason', 'Not found')})")
                
            time.sleep(0.3)
            
        report_filename = f"hunt_report_{user_id}.txt"
        with open(report_filename, "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))
            
        with open(report_filename, "rb") as f:
            bot.send_document(message.chat.id, f, caption=f"📊 *Hunt Report Completed!*\nChecked {total_bins} bins, found {len(valid_records)} valid ones.", parse_mode="Markdown")
            
        if valid_records:
            valid_filename = f"valid_bins_{user_id}.txt"
            with open(valid_filename, "w", encoding="utf-8") as f:
                f.write("\n".join(valid_records))
            with open(valid_filename, "rb") as f:
                bot.send_document(message.chat.id, f, caption=f"✅ *Valid Bins List*", parse_mode="Markdown")
            os.remove(valid_filename)
            
        os.remove(report_filename)
        bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)

    elif action == "gen_bin":
        state["bin"] = text
        state["action"] = "gen_amount"
        bot.reply_to(message, "💳 How many cards to generate? (e.g., `10`):", parse_mode="Markdown")
        
    elif action == "gen_amount":
        if not text.isdigit():
            bot.reply_to(message, "⚠️ Enter a valid number.")
            return
        
        bin_input = state.get("bin")
        amount = int(text)
        del USER_STATES[user_id]
        
        generated_list = []
        target_len = 16 if not bin_input.startswith("3") else 15
        rem_len = target_len - len(bin_input)
        
        for _ in range(amount):
            rand_digits = "".join([str(random.randint(0, 9)) for _ in range(rem_len)])
            card_num = bin_input + rand_digits
            c_month = str(random.randint(1, 12)).zfill(2)
            c_year = str(random.randint(2027, 2032))
            c_cvv = str(random.randint(100, 9999)) if bin_input.startswith("3") else str(random.randint(100, 999))
            generated_list.append(f"{card_num}|{c_month}|{c_year}|{c_cvv}")
            
        filename = f"generated_{user_id}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(generated_list))
        with open(filename, "rb") as f:
            bot.send_document(message.chat.id, f, caption=f"✅ *Successfully generated {amount} cards!*", parse_mode="Markdown")
        os.remove(filename)

    elif action == "check_bin":
        bin_num = text
        del USER_STATES[user_id]
        
        msg = bot.reply_to(message, "⏳ *Checking bin details via zmshortener.xo.je...*", parse_mode="Markdown")
        fresh_ua = generate_fresh_user_agent()
        res = check_single_bin_sync(bin_num, fresh_ua)
        
        if res["status"] == "VALID":
            out = (f"✅ *Bin Info Found*\n"
                   f"━━━━━━━━━━━━━━━━━━━\n"
                   f"📌 *Bin:* `{res['bin']}`\n"
                   f"💳 *Scheme:* `{res['scheme']}`\n"
                   f"🏷 *Type:* `{res['type']}`\n"
                   f"🌍 *Country:* `{res['country_code']}` ({res['country_name']})\n"
                   f"🏛 *Bank:* `{res['bank']}`\n"
                   f"━━━━━━━━━━━━━━━━━━━")
            bot.edit_message_text(out, chat_id=message.chat.id, message_id=msg.message_id, parse_mode="Markdown")
        else:
            bot.edit_message_text(f"❌ *Invalid or dead bin:* `{bin_num}` ({res.get('reason', 'Dead')})", chat_id=message.chat.id, message_id=msg.message_id, parse_mode="Markdown")

@bot.message_handler(commands=['check'])
def check_single_bin(message):
    if not is_user_subscribed(message.from_user.id):
        send_subscription_prompt(message.chat.id)
        return
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "Usage: `/check 527917`", parse_mode="Markdown")
            return
        bin_num = parts[1]
        msg = bot.reply_to(message, "⏳ *Checking...*", parse_mode="Markdown")
        fresh_ua = generate_fresh_user_agent()
        res = check_single_bin_sync(bin_num, fresh_ua)
        if res["status"] == "VALID":
            out = f"✅ Bin: {res['bin']} | Scheme: {res['scheme']} | Type: {res['type']} | Country: {res['country_code']} | Bank: {res['bank']}"
            bot.edit_message_text(out, chat_id=message.chat.id, message_id=msg.message_id)
        else:
            bot.edit_message_text(f"❌ Dead bin: {bin_num}", chat_id=message.chat.id, message_id=msg.message_id)
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

def run_bot():
    bot.remove_webhook()
    bot.infinity_polling()

if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
