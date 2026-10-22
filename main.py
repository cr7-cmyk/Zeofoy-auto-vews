import os
import random
import threading
import csv
import requests
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

# GitHub Raw CSV Link configuration
CSV_URL = "https://raw.githubusercontent.com/cr7-cmyk/fuck/main/master_bin_list.csv"
CSV_FILENAME = "master_bin_list.csv"
BIN_DATABASE = {}
is_db_loaded = False

def download_and_load_csv():
    global BIN_DATABASE, is_db_loaded
    
    if not os.path.exists(CSV_FILENAME):
        print("📥 Downloading Master BIN CSV file from GitHub...")
        try:
            response = requests.get(CSV_URL, stream=True, timeout=120)
            if response.status_code == 200:
                with open(CSV_FILENAME, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                print("✅ CSV file downloaded successfully from GitHub!")
            else:
                print(f"⚠️ Failed to download CSV. Status code: {response.status_code}")
                return
        except Exception as e:
            print(f"⚠️ Error downloading CSV: {e}")
            return

    print("⏳ Loading BIN database using exact column mapping...")
    temp_db = {}
    try:
        with open(CSV_FILENAME, mode="r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row or len(row) < 2:
                    continue
                
                # Header row filter
                first_item = str(row[0]).strip().lower()
                if "bin" in first_item or "iin" in first_item or not first_item.replace('.', '', 1).isdigit():
                    continue

                # Clean BIN
                clean_bin = first_item.split('.')[0].strip().zfill(6)[:6]
                if not clean_bin.isdigit() or len(clean_bin) < 6:
                    continue

                # Exact mapping based on provided layout:
                # [0]=bin, [1]=brand, [2]=type, [3]=category, [4]=issuer, [7]=alpha_2, [9]=country
                brand = row[1].strip() if len(row) > 1 and row[1] else "UNKNOWN"
                b_type = row[2].strip() if len(row) > 2 and row[2] else "UNKNOWN"
                category = row[3].strip() if len(row) > 3 and row[3] else ""
                bank = row[4].strip() if len(row) > 4 and row[4] else "UNKNOWN"
                country_code = row[7].strip() if len(row) > 7 and row[7] else "UNKNOWN"
                country_name = row[9].strip() if len(row) > 9 and row[9] else "UNKNOWN"

                full_type = b_type
                if category and category.lower() != b_type.lower():
                    full_type += f" ({category})"

                temp_db[clean_bin] = {
                    "bin": clean_bin,
                    "scheme": brand.upper(),
                    "type": full_type.upper(),
                    "bank": bank,
                    "country_code": country_code.upper(),
                    "country_name": country_name
                }
                    
        BIN_DATABASE = temp_db
        is_db_loaded = True
        print(f"✅ Loaded {len(BIN_DATABASE)} unique bins into memory successfully!")
    except Exception as e:
        print(f"⚠️ Error parsing CSV file: {e}")

def search_bin_locally(bin_num):
    bin6 = str(bin_num)[:6].zfill(6)
    if bin6 in BIN_DATABASE:
        data = BIN_DATABASE[bin6]
        return {
            "status": "VALID",
            "bin": bin_num,
            "scheme": data["scheme"],
            "type": data["type"],
            "bank": data["bank"],
            "country_code": data["country_code"],
            "country_name": data["country_name"]
        }
    return {"status": "DEAD", "bin": bin_num, "reason": "Not found in local CSV"}

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
    status = "Ready" if is_db_loaded else "Downloading/Loading Database..."
    return f"Zenmods Bot is running! Status: {status} (Total Bins: {len(BIN_DATABASE)})"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not is_user_subscribed(message.from_user.id):
        send_subscription_prompt(message.chat.id)
        return

    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("⚡ Hunt Bins", callback_data="btn_hunt"), InlineKeyboardButton("💳 Generate Cards", callback_data="btn_gen"))
    markup.row(InlineKeyboardButton("🔍 Check Bin", callback_data="btn_check"))
    
    welcome_text = (
        "🔥 *Welcome to Zenmods Advanced Checker* 🔥\n\n"
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
        bot.send_message(call.message.chat.id, "📥 *Hunt Setup*\n\nSend **BIN Prefix** (e.g., `5279`, `4241`):", parse_mode="Markdown")
        
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
        
        if not is_db_loaded:
            bot.reply_to(message, "⏳ *Database is still downloading/loading. Please wait a few seconds and try again.*", parse_mode="Markdown")
            return
        
        msg = bot.reply_to(message, f"⚡ *Searching for {count} bins matching `{prefix}`...*", parse_mode="Markdown")
        
        valid_records = []
        seen_bins = set()
        
        for b_code, item in BIN_DATABASE.items():
            if b_code.startswith(prefix):
                cou_code = item["country_code"].upper()
                if country and country != "ALL" and cou_code != country:
                    continue
                if b_code not in seen_bins:
                    seen_bins.add(b_code)
                    valid_records.append(f"Bin: {item['bin']} | Scheme: {item['scheme']} | Type: {item['type']} | Country: {cou_code} ({item['country_name']}) | Bank: {item['bank']}")
                    if len(valid_records) >= count:
                        break

        try:
            bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)
        except Exception:
            pass

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
                        caption=f"✅ *Zenmods Valid Bins List*\nFound {len(valid_records)} unique valid bins matching prefix `{prefix}`.", 
                        parse_mode="Markdown"
                    )
            except Exception as e:
                bot.send_message(message.chat.id, f"⚠️ Error sending valid bins file: {e}")
            finally:
                if os.path.exists(valid_filename):
                    os.remove(valid_filename)
        else:
            bot.send_message(message.chat.id, f"❌ No valid bins found matching prefix `{prefix}` with country `{country or 'ANY'}`.")

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
                bot.send_document(message.chat.id, f, caption=f"✅ *Zenmods Generator: Successfully generated {amount} cards!*", parse_mode="Markdown")
        finally:
            if os.path.exists(filename):
                os.remove(filename)

    elif action == "check_bin":
        bin_num = text
        del USER_STATES[user_id]
        
        if not is_db_loaded:
            bot.reply_to(message, "⏳ *Database is still loading. Please try again in a moment.*", parse_mode="Markdown")
            return
        
        msg = bot.reply_to(message, "⏳ *Zenmods Checker: Looking up in local CSV...*", parse_mode="Markdown")
        res = search_bin_locally(bin_num)
        
        if res["status"] == "VALID":
            out = (f"✅ *Zenmods Local Check Result*\n"
                   f"━━━━━━━━━━━━━━━━━━━\n"
                   f"📌 *Bin:* `{res['bin']}`\n"
                   f"💳 *Scheme:* `{res['scheme']}`\n"
                   f"🏷 *Type:* `{res['type']}`\n"
                   f"🌍 *Country:* `{res['country_code']}` ({res['country_name']})\n"
                   f"🏛 *Bank:* `{res['bank']}`\n"
                   f"━━━━━━━━━━━━━━━━━━━")
            bot.edit_message_text(out, chat_id=message.chat.id, message_id=msg.message_id, parse_mode="Markdown")
        else:
            bot.edit_message_text(f"❌ *Not found in database:* `{bin_num}`", chat_id=message.chat.id, message_id=msg.message_id, parse_mode="Markdown")

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
        
        if not is_db_loaded:
            bot.reply_to(message, "⏳ *Database is still loading. Please try again in a moment.*", parse_mode="Markdown")
            return
            
        msg = bot.reply_to(message, "⏳ *Checking...*", parse_mode="Markdown")
        res = search_bin_locally(bin_num)
        if res["status"] == "VALID":
            out = f"✅ Bin: {res['bin']} | Scheme: {res['scheme']} | Type: {res['type']} | Country: {res['country_code']} | Bank: {res['bank']}"
            bot.edit_message_text(out, chat_id=message.chat.id, message_id=msg.message_id)
        else:
            bot.edit_message_text(f"❌ Not found: {bin_num}", chat_id=message.chat.id, message_id=msg.message_id)
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

def run_bot():
    bot.remove_webhook()
    bot.infinity_polling()

if __name__ == '__main__':
    csv_thread = threading.Thread(target=download_and_load_csv, daemon=True)
    csv_thread.start()
    
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
