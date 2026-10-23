import os
import random
import threading
import time
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

CSV_URL = "https://media.githubusercontent.com/media/cr7-cmyk/fuck/refs/heads/main/master_bin_list.csv"
CSV_FILENAME = "master_bin_list.csv"
BIN_DATABASE = {}
COUNTRY_BINS = {}
is_db_loaded = False

def download_and_load_csv():
    global BIN_DATABASE, COUNTRY_BINS, is_db_loaded
    
    if not os.path.exists(CSV_FILENAME):
        try:
            response = requests.get(CSV_URL, stream=True, timeout=120)
            if response.status_code == 200:
                with open(CSV_FILENAME, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            else:
                return
        except Exception:
            return

    temp_db = {}
    temp_country_bins = {}
    
    try:
        with open(CSV_FILENAME, mode="r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row or len(row) < 2:
                    continue
                
                clean_bin = None
                brand = "UNKNOWN"
                b_type = "UNKNOWN"
                category = ""
                bank = "UNKNOWN"
                phone = ""
                url = ""
                country_code = "UNKNOWN"
                country_name = "UNKNOWN"

                for col in row:
                    col_str = str(col).strip().replace('"', '')
                    if not col_str:
                        continue
                    
                    if not clean_bin and (col_str.isdigit() or (col_str.endswith('.0') and col_str[:-2].isdigit())):
                        potential_bin = col_str.split('.')[0]
                        if len(potential_bin) >= 6:
                            clean_bin = potential_bin.zfill(6)[:6]
                    
                    if country_code == "UNKNOWN" and len(col_str) == 2 and col_str.isalpha() and col_str.isupper():
                        if col_str not in ["DE", "CR", "PR"]:
                            country_code = col_str

                    if brand == "UNKNOWN" and col_str.upper() in ["MASTERCARD", "VISA", "AMEX", "DISCOVER", "JCB", "UNIONPAY", "RUPAY", "PRIVATE LABEL", "LOCAL BRAND"]:
                        brand = col_str.upper()

                    if b_type == "UNKNOWN" and col_str.upper() in ["CREDIT", "DEBIT", "PREPAID"]:
                        b_type = col_str.upper()

                if len(row) > 1 and brand == "UNKNOWN" and row[1]: brand = row[1].strip().replace('"', '')
                if len(row) > 2 and b_type == "UNKNOWN" and row[2]: b_type = row[2].strip().replace('"', '')
                if len(row) > 3 and not category and row[3]: category = row[3].strip().replace('"', '')
                if len(row) > 4 and bank == "UNKNOWN" and row[4]: bank = row[4].strip().replace('"', '')
                if len(row) > 5 and row[5]: phone = row[5].strip().replace('"', '')
                if len(row) > 6 and row[6]: url = row[6].strip().replace('"', '')
                
                if country_code == "UNKNOWN":
                    for i in range(len(row)):
                        val = str(row[i]).strip().replace('"', '')
                        if len(val) == 2 and val.isalpha() and val.isupper():
                            country_code = val
                            if i + 2 < len(row):
                                country_name = str(row[i+2]).strip().replace('"', '')
                            break

                if clean_bin:
                    full_type = b_type
                    if category and category.lower() != b_type.lower():
                        full_type += f" ({category})"

                    c_code = country_code.upper()
                    c_name = country_name if country_name != "UNKNOWN" else "JAPAN" if c_code == "JP" else "UNKNOWN"

                    temp_db[clean_bin] = {
                        "bin": clean_bin,
                        "scheme": brand.upper(),
                        "type": full_type.upper(),
                        "bank": bank,
                        "phone": phone if phone else "N/A",
                        "url": url if url else "N/A",
                        "country_code": c_code,
                        "country_name": c_name
                    }
                    
                    if c_code not in temp_country_bins:
                        temp_country_bins[c_code] = []
                    temp_country_bins[c_code].append(clean_bin)
                    
        BIN_DATABASE = temp_db
        COUNTRY_BINS = temp_country_bins
        is_db_loaded = True
    except Exception:
        pass

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
            "phone": data["phone"],
            "url": data["url"],
            "country_code": data["country_code"],
            "country_name": data["country_name"]
        }
    return {"status": "DEAD", "bin": bin_num}

def is_user_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except Exception:
        return False

def send_subscription_prompt(chat_id):
    markup = InlineKeyboardMarkup()
    join_btn = InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")
    verify_btn = InlineKeyboardButton("✅ Verify Subscription", callback_data="verify_sub")
    markup.row(join_btn)
    markup.row(verify_btn)
    
    msg_text = (
        "⚠️ *Access Denied!*\n\n"
        f"Please join our official channel first: {CHANNEL_USERNAME}\n\n"
        "After joining, click the 'Verify Subscription' button below."
    )
    bot.send_message(chat_id, msg_text, parse_mode="Markdown", reply_markup=markup)

@app.route('/')
def home():
    return "Bot is active and running."

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not is_user_subscribed(message.from_user.id):
        send_subscription_prompt(message.chat.id)
        return

    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("⚡ Hunt Bins", callback_data="btn_hunt"), InlineKeyboardButton("💳 Generate Cards", callback_data="btn_gen"))
    markup.row(InlineKeyboardButton("🌐 Country Dump", callback_data="btn_dump"), InlineKeyboardButton("🔍 Check Bin", callback_data="btn_check"))
    
    welcome_text = (
        "🔥 *Welcome to Card Tools Bot* 🔥\n\n"
        "Choose an option below to get started:"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    user_id = call.from_user.id
    if call.data == "verify_sub":
        if is_user_subscribed(user_id):
            bot.answer_callback_query(call.id, "✅ Verified successfully!")
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            send_welcome(call.message)
        else:
            bot.answer_callback_query(call.id, "❌ You haven't joined the channel yet!", show_alert=True)
            
    elif call.data == "btn_hunt":
        if not is_user_subscribed(user_id):
            send_subscription_prompt(call.message.chat.id)
            return
        USER_STATES[user_id] = {"action": "hunt_prefix"}
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "📥 Send **BIN Prefix** (e.g., `5279`, `4241`):", parse_mode="Markdown")
        
    elif call.data == "btn_gen":
        if not is_user_subscribed(user_id):
            send_subscription_prompt(call.message.chat.id)
            return
        USER_STATES[user_id] = {"action": "gen_bin"}
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "📥 Send **BIN number**:", parse_mode="Markdown")

    elif call.data == "btn_dump":
        if not is_user_subscribed(user_id):
            send_subscription_prompt(call.message.chat.id)
            return
        USER_STATES[user_id] = {"action": "dump_country"}
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🌍 Send **Country Code** (e.g., `JP`, `US`, `BR`):", parse_mode="Markdown")
        
    elif call.data == "btn_check":
        if not is_user_subscribed(user_id):
            send_subscription_prompt(call.message.chat.id)
            return
        USER_STATES[user_id] = {"action": "check_bin"}
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "📥 Send **BIN** to check:", parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.from_user.id in USER_STATES)
def handle_interactive_steps(message):
    user_id = message.from_user.id
    if not is_user_subscribed(user_id):
        send_subscription_prompt(message.chat.id)
        return

    state = USER_STATES.get(user_id)
    if not state:
        return
    
    action = state.get("action")
    text = message.text.strip()
    
    if action == "hunt_prefix":
        state["prefix"] = text
        state["action"] = "hunt_count"
        bot.reply_to(message, "🔢 Send how many bins to scan (Max 1000):", parse_mode="Markdown")
        
    elif action == "hunt_count":
        if not text.isdigit():
            bot.reply_to(message, "⚠️ Please enter a valid number.")
            return
        count = int(text)
        if count > 1000:
            bot.reply_to(message, "⚠️ Maximum limit is 1000.")
            return
        state["count"] = count
        state["action"] = "hunt_country"
        bot.reply_to(message, "🌍 Send **Country Code** (e.g., `US`, `JP`, `BR`) or type `all`:", parse_mode="Markdown")
        
    elif action == "hunt_country":
        prefix = state.get("prefix")
        count = state.get("count")
        country = None if text.lower() == "all" else text.upper()
        
        del USER_STATES[user_id]
        
        if not is_db_loaded:
            bot.reply_to(message, "⏳ Please wait, database is loading...", parse_mode="Markdown")
            return
        
        msg = bot.reply_to(message, "⏳ Processing.", parse_mode="Markdown")
        for dot in ["..", "..."]:
            time.sleep(0.3)
            try:
                bot.edit_message_text(f"⏳ Processing{dot}", chat_id=message.chat.id, message_id=msg.message_id)
            except Exception:
                pass
        
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
            valid_filename = f"Valid_Bins_{valid_rand_id}.txt"
            try:
                with open(valid_filename, "w", encoding="utf-8") as f:
                    f.write("\n".join(valid_records))
                
                with open(valid_filename, "rb") as f:
                    bot.send_document(
                        message.chat.id, 
                        f, 
                        caption=f"✅ Found {len(valid_records)} bins matching `{prefix}`.", 
                        parse_mode="Markdown"
                    )
            except Exception as e:
                bot.send_message(message.chat.id, f"⚠️ Error: {e}")
            finally:
                if os.path.exists(valid_filename):
                    os.remove(valid_filename)
        else:
            bot.reply_to(message, f"❌ No bins found matching prefix `{prefix}`.")

    elif action == "dump_country":
        state["country"] = text.upper()
        state["action"] = "dump_count"
        bot.reply_to(message, "🔢 How many cards to dump? (Max 1000):", parse_mode="Markdown")

    elif action == "dump_count":
        if not text.isdigit():
            bot.reply_to(message, "⚠️ Please enter a valid number.")
            return
        
        amount = int(text)
        if amount > 1000:
            bot.reply_to(message, "⚠️ Maximum limit is 1000 cards per request.")
            return

        country_code = state.get("country")
        del USER_STATES[user_id]

        if not is_db_loaded:
            bot.reply_to(message, "⏳ Please wait, database is loading...", parse_mode="Markdown")
            return

        available_bins = COUNTRY_BINS.get(country_code, [])
        if not available_bins:
            bot.reply_to(message, f"❌ No bins found for country code `{country_code}` in database.")
            return

        msg = bot.reply_to(message, "⏳ Generating country dump.", parse_mode="Markdown")
        for dot in ["..", "..."]:
            time.sleep(0.3)
            try:
                bot.edit_message_text(f"⏳ Generating country dump{dot}", chat_id=message.chat.id, message_id=msg.message_id)
            except Exception:
                pass

        dumped_list = []
        for _ in range(amount):
            chosen_bin = random.choice(available_bins)
            target_len = 16 if not chosen_bin.startswith("3") else 15
            rem_len = target_len - len(chosen_bin)
            rand_digits = "".join([str(random.randint(0, 9)) for _ in range(rem_len)])
            card_num = chosen_bin + rand_digits
            c_month = str(random.randint(1, 12)).zfill(2)
            c_year = str(random.randint(2027, 2032))
            c_cvv = str(random.randint(100, 9999)) if chosen_bin.startswith("3") else str(random.randint(100, 999))
            dumped_list.append(f"{card_num}|{c_month}|{c_year}|{c_cvv}")

        try:
            bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)
        except Exception:
            pass

        dump_rand_id = random.randint(10000, 99999)
        filename = f"Country_Dump_{country_code}_{dump_rand_id}.txt"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("\n".join(dumped_list))
            with open(filename, "rb") as f:
                bot.send_document(
                    message.chat.id, 
                    f, 
                    caption=f"✅ Country Dump Successful!\nCountry: `{country_code}`\nTotal Cards: `{amount}`", 
                    parse_mode="Markdown"
                )
        finally:
            if os.path.exists(filename):
                os.remove(filename)

    elif action == "gen_bin":
        state["bin"] = text
        state["action"] = "gen_amount"
        bot.reply_to(message, "💳 How many cards to generate? (<=50 in chat, >50 as file, Max 1000):", parse_mode="Markdown")
        
    elif action == "gen_amount":
        if not text.isdigit():
            bot.reply_to(message, "⚠️ Please enter a valid number.")
            return
        
        amount = int(text)
        if amount > 1000:
            bot.reply_to(message, "⚠️ Maximum limit is 1000 cards per request.")
            return

        bin_input = state.get("bin")
        del USER_STATES[user_id]
        
        msg = bot.reply_to(message, "⏳ Generating cards.", parse_mode="Markdown")
        for dot in ["..", "..."]:
            time.sleep(0.3)
            try:
                bot.edit_message_text(f"⏳ Generating cards{dot}", chat_id=message.chat.id, message_id=msg.message_id)
            except Exception:
                pass
        
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
            
        try:
            bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)
        except Exception:
            pass

        if amount <= 50:
            cards_text = "\n".join(generated_list)
            response_msg = f"✅ *Generated Cards ({amount}):*\n```text\n{cards_text}\n```"
            bot.send_message(message.chat.id, response_msg, parse_mode="Markdown")
        else:
            gen_rand_id = random.randint(10000, 99999)
            filename = f"Generated_Cards_{gen_rand_id}.txt"
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write("\n".join(generated_list))
                with open(filename, "rb") as f:
                    bot.send_document(message.chat.id, f, caption=f"✅ Successfully generated {amount} cards (sent as file because it's over 50).", parse_mode="Markdown")
            finally:
                if os.path.exists(filename):
                    os.remove(filename)

    elif action == "check_bin":
        bin_num = text
        del USER_STATES[user_id]
        
        if not is_db_loaded:
            bot.reply_to(message, "⏳ Please wait, database is loading...", parse_mode="Markdown")
            return
        
        msg = bot.reply_to(message, "⏳ Searching database.", parse_mode="Markdown")
        for dot in ["..", "..."]:
            time.sleep(0.3)
            try:
                bot.edit_message_text(f"⏳ Searching database{dot}", chat_id=message.chat.id, message_id=msg.message_id)
            except Exception:
                pass

        res = search_bin_locally(bin_num)
        
        if res["status"] == "VALID":
            out = (f"✅ *Bin Information Found*\n"
                   f"━━━━━━━━━━━━━━━━━━━\n"
                   f"📌 *Bin:* `{res['bin']}`\n"
                   f"💳 *Scheme:* `{res['scheme']}`\n"
                   f"🏷 *Type:* `{res['type']}`\n"
                   f"🌍 *Country:* `{res['country_code']}` ({res['country_name']})\n"
                   f"🏛 *Bank:* `{res['bank']}`\n"
                   f"📞 *Phone:* `{res['phone']}`\n"
                   f"🌐 *Website:* `{res['url']}`\n"
                   f"━━━━━━━━━━━━━━━━━━━")
            bot.edit_message_text(out, chat_id=message.chat.id, message_id=msg.message_id, parse_mode="Markdown")
        else:
            bot.edit_message_text(f"❌ Not found in database: `{bin_num}`", chat_id=message.chat.id, message_id=msg.message_id, parse_mode="Markdown")

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
            bot.reply_to(message, "⏳ Please wait, database is loading...", parse_mode="Markdown")
            return
            
        msg = bot.reply_to(message, "⏳ Checking.", parse_mode="Markdown")
        for dot in ["..", "..."]:
            time.sleep(0.2)
            try:
                bot.edit_message_text(f"⏳ Checking{dot}", chat_id=message.chat.id, message_id=msg.message_id)
            except Exception:
                pass

        res = search_bin_locally(bin_num)
        if res["status"] == "VALID":
            out = (f"✅ *Bin Information Found*\n"
                   f"━━━━━━━━━━━━━━━━━━━\n"
                   f"📌 *Bin:* `{res['bin']}`\n"
                   f"💳 *Scheme:* `{res['scheme']}`\n"
                   f"🏷 *Type:* `{res['type']}`\n"
                   f"🌍 *Country:* `{res['country_code']}` ({res['country_name']})\n"
                   f"🏛 *Bank:* `{res['bank']}`\n"
                   f"📞 *Phone:* `{res['phone']}`\n"
                   f"🌐 *Website:* `{res['url']}`\n"
                   f"━━━━━━━━━━━━━━━━━━━")
            bot.edit_message_text(out, chat_id=message.chat.id, message_id=msg.message_id, parse_mode="Markdown")
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
