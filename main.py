import os
import random
import threading
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN environment variable is missing! Please set it in your Render dashboard.")

CHANNEL_USERNAME = "@ZenmodsXads"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

USER_STATES = {}

def check_single_bin_sync(bin_num):
    bin6 = bin_num[:6]
    url = f"https://binlist.io/lookup/{bin6}/"
    
    headers = {
        "User-Agent": "ZenmodsCheckerBot/2.0",
        "Accept": "application/json"
    }
    
    for attempt in range(2):
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                try:
                    res = response.json()
                except Exception:
                    continue

                if res and isinstance(res, dict) and res.get("success") is True:
                    scheme = res.get('scheme') or 'Unknown'
                    card_type = res.get('type') or 'Unknown'
                    category = res.get('category') or ''
                    
                    full_type = card_type
                    if category and category.lower() != card_type.lower():
                        full_type += f" ({category})"
                        
                    bank_info = res.get('bank') or {}
                    bank_name = bank_info.get('name') or 'Unknown'
                    
                    country_info = res.get('country') or {}
                    cou_code = country_info.get('alpha2') or 'Unknown'
                    cou_name = country_info.get('name') or 'Unknown'
                    
                    return {
                        "status": "VALID",
                        "bin": bin_num,
                        "scheme": scheme.upper(),
                        "type": full_type.upper(),
                        "bank": bank_name,
                        "country_code": cou_code.upper(),
                        "country_name": cou_name
                    }
                elif res.get("success") is False:
                    return {"status": "DEAD", "bin": bin_num, "reason": res.get("reason", "Not found")}
            elif response.status_code == 429:
                time.sleep(1)
        except Exception:
            continue
            
    return {"status": "DEAD", "bin": bin_num, "reason": "Lookup failed / Not found"}

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

@app.route('/')
def home():
    return "Zenmods Fast Binlist Bot is running successfully!"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not is_user_subscribed(message.from_user.id):
        send_subscription_prompt(message.chat.id)
        return

    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("⚡ Hunt Bins", callback_data="btn_hunt"), InlineKeyboardButton("💳 Generate Cards", callback_data="btn_gen"))
    markup.row(InlineKeyboardButton("🔍 Check Bin", callback_data="btn_check"))
    
    welcome_text = (
        "🔥 *Welcome to Zenmods Fast Checker* 🔥\n\n"
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
        
        msg = bot.reply_to(message, f"⚡ *Super Fast Binlist Scanning {count} bins...*", parse_mode="Markdown")
        
        length = 4 if prefix != '574' else 3
        chars = '0987654321'
        
        generated_bins = []
        for _ in range(count * 3):
            us = "".join(random.choice(chars) for _ in range(length))
            u1 = prefix + us
            if len(u1) >= 6:
                generated_bins.append(u1[:6])
        generated_bins = list(set(generated_bins))[:count]
        
        valid_records = []
        report_lines = [
            f"=== ZENMODS FAST BINLIST HUNT REPORT ===",
            f"Prefix: {prefix} | Target Count: {count} | Filter Country: {country or 'ANY'}\n"
        ]
        
        total_bins = len(generated_bins)
        completed_count = 0
        
        # Optimized with ThreadPoolExecutor (max_workers=5 for smooth rate control)
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_bin = {executor.submit(check_single_bin_sync, b): b for b in generated_bins}
            
            for future in as_completed(future_to_bin):
                b = future_to_bin[future]
                completed_count += 1
                try:
                    result = future.result()
                except Exception:
                    result = {"status": "DEAD", "bin": b, "reason": "Error"}
                
                status = result["status"]
                if status == "VALID":
                    cou_code = result['country_code']
                    if country and cou_code.upper() != country:
                        report_lines.append(f"[{completed_count}] BIN: {b} -> SUCCESS but Skipped (Country mismatch: {cou_code})")
                    else:
                        valid_records.append(f"Bin: {result['bin']} | Scheme: {result['scheme']} | Type: {result['type']} | Country: {cou_code} ({result['country_name']}) | Bank: {result['bank']}")
                        report_lines.append(f"[{completed_count}] BIN: {b} -> VALID ✅ ({result['scheme']}, {result['type']}, {cou_code}, {result['bank']})")
                else:
                    report_lines.append(f"[{completed_count}] BIN: {b} -> DEAD ❌ ({result.get('reason', 'Not found')})")
                
                try:
                    progress_text = (
                        f"⚡ *Binlist Hunter Running...*\n"
                        f"━━━━━━━━━━━━━━━━━━━\n"
                        f"📊 Checked: `{completed_count}/{total_bins}`\n"
                        f"✅ Valid Found: `{len(valid_records)}`\n"
                        f"━━━━━━━━━━━━━━━━━━━"
                    )
                    bot.edit_message_text(progress_text, chat_id=message.chat.id, message_id=msg.message_id, parse_mode="Markdown")
                except Exception:
                    pass
            
        try:
            bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)
        except Exception:
            pass

        rand_id = random.randint(10000, 99999)
        report_filename = f"Zenmods_Report_{rand_id}.txt"
        try:
            with open(report_filename, "w", encoding="utf-8") as f:
                f.write("\n".join(report_lines))
            
            with open(report_filename, "rb") as f:
                bot.send_document(
                    message.chat.id, 
                    f, 
                    caption=f"📊 *Zenmods Report Completed!*\nChecked {total_bins} bins, found {len(valid_records)} valid ones.", 
                    parse_mode="Markdown"
                )
        except Exception as e:
            bot.send_message(message.chat.id, f"⚠️ Error sending report file: {e}")
        finally:
            if os.path.exists(report_filename):
                os.remove(report_filename)
            
        if valid_records:
            valid_rand_id = random.randint(10000, 99999)
            valid_filename = f"Zenmods_ValidBins_{valid_rand_id}.txt"
            try:
                with open(valid_filename, "w", encoding="utf-8") as f:
                    f.write("\n".join(valid_records))
                
                with open(valid_filename, "rb") as f:
                    bot.send_document(
                        message.chat.id, 
                        f, 
                        caption=f"✅ *Zenmods Valid Bins List*", 
                        parse_mode="Markdown"
                    )
            except Exception as e:
                bot.send_message(message.chat.id, f"⚠️ Error sending valid bins file: {e}")
            finally:
                if os.path.exists(valid_filename):
                    os.remove(valid_filename)

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
            
        gen_rand_id = random.randint(10000, 99999)
        filename = f"Zenmods_Cards_{gen_rand_id}.txt"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("\n".join(generated_list))
            with open(filename, "rb") as f:
                bot.send_document(message.chat.id, f, caption=f"✅ *Zenmods Checker: Successfully generated {amount} cards!*", parse_mode="Markdown")
        finally:
            if os.path.exists(filename):
                os.remove(filename)

    elif action == "check_bin":
        bin_num = text
        del USER_STATES[user_id]
        
        msg = bot.reply_to(message, "⏳ *Zenmods Checker: Checking details...*", parse_mode="Markdown")
        res = check_single_bin_sync(bin_num)
        
        if res["status"] == "VALID":
            out = (f"✅ *Zenmods Checker Result*\n"
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
        res = check_single_bin_sync(bin_num)
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
