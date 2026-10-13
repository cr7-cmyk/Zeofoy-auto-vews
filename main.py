import os
import random
import threading
import asyncio
import time
try:
    import aiohttp
except ImportError:
    aiohttp_available = False

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

# Temporary user states for interactive input flow
USER_STATES = {}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
]

def get_random_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json, text/plain, */*"
    }

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

async def fetch_api(session, url, headers):
    try:
        async with session.get(url, headers=headers, timeout=5) as response:
            if response.status == 200:
                return await response.json()
    except:
        pass
    return None

async def async_check_bin(bin_num):
    headers = get_random_headers()
    urls = [
        f"https://bin-checker.net/api/{bin_num}",
        f"https://data.handyapi.com/bin/{bin_num}",
        f"https://lookup.binlist.net/{bin_num}",
        f"https://binlist.io/lookup/{bin_num}/",
        f"https://api.bincodes.com/bin/{bin_num}.json"
    ]
    
    async with aiohttp.ClientSession() as session:
        for url in urls:
            res = await fetch_api(session, url, headers)
            if res and isinstance(res, dict):
                scheme = res.get('scheme') or res.get('Scheme') or res.get('card', {}).get('scheme') or 'Unknown'
                bank_info = res.get('bank', {})
                bank_name = bank_info.get('name') if isinstance(bank_info, dict) else res.get('Bank', 'Unknown')
                
                country_info = res.get('country', {})
                if isinstance(country_info, dict):
                    cou_code = country_info.get('code') or country_info.get('Alpha2') or 'Unknown'
                    cou_name = country_info.get('name') or country_info.get('Name') or 'Unknown'
                else:
                    cou_code = res.get('Country', 'Unknown')
                    cou_name = res.get('CountryName', 'Unknown')
                
                if scheme != 'Unknown' or bank_name != 'Unknown':
                    return {
                        "bin": bin_num,
                        "scheme": scheme,
                        "bank": bank_name,
                        "country_code": cou_code,
                        "country_name": cou_name
                    }
    return None

@app.route('/')
def home():
    return "Advanced Interactive Bot is running successfully!"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not is_user_subscribed(message.from_user.id):
        send_subscription_prompt(message.chat.id)
        return

    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("⚡ Hunt Bins", callback_data="btn_hunt"), InlineKeyboardButton("💳 Generate Cards", callback_data="btn_gen"))
    markup.row(InlineKeyboardButton("🔍 Check Bin", callback_data="btn_check"))
    
    welcome_text = (
        "🔥 *Welcome to Advanced Tool Bot* 🔥\n\n"
        "You can use commands or click buttons below for interactive setup:\n"
        "• `/check <bin>` - Check bin info\n"
        "• `/hunt <prefix> <count> <country>` - Hunt valid bins\n"
        "• `/gen <bin> [mm] [yyyy] [cvv] [amount]` - Generate cards"
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
        bot.send_message(call.message.chat.id, "📥 *Hunt Setup*\n\nPlease send the **BIN Prefix** (e.g., `37` or `4751`):", parse_mode="Markdown")
        
    elif call.data == "btn_gen":
        USER_STATES[user_id] = {"action": "gen_bin"}
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "📥 *Card Generator Setup*\n\nPlease send the **BIN number** (e.g., `475126`):", parse_mode="Markdown")
        
    elif call.data == "btn_check":
        USER_STATES[user_id] = {"action": "check_bin"}
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "📥 *Bin Checker Setup*\n\nPlease send the **BIN** you want to check:", parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.from_user.id in USER_STATES)
def handle_interactive_steps(message):
    user_id = message.from_user.id
    state = USER_STATES.get(user_id)
    if not state:
        return
    
    action = state.get("action")
    text = message.text.strip()
    
    # --- HUNT FLOW ---
    if action == "hunt_prefix":
        state["prefix"] = text
        state["action"] = "hunt_count"
        bot.reply_to(message, "🔢 Now send how many bins you want to test (e.g., `10` or `20`):", parse_mode="Markdown")
        
    elif action == "hunt_count":
        if not text.isdigit():
            bot.reply_to(message, "⚠️ Please enter a valid number for count.")
            return
        state["count"] = int(text)
        state["action"] = "hunt_country"
        bot.reply_to(message, "🌍 Now send the **Country Code** (e.g., `US`, `BD`) or type `all` for any country:", parse_mode="Markdown")
        
    elif action == "hunt_country":
        prefix = state.get("prefix")
        count = state.get("count")
        country = None if text.lower() == "all" else text.upper()
        
        del USER_STATES[user_id] # Clear state
        
        msg = bot.reply_to(message, f"⚡ *Hunting {count} bins with prefix {prefix}... [░░░░░░░░░░] 0%*", parse_mode="Markdown")
        
        chars = '0987654321'
        length = 4 if prefix != '574' else 3
        generated_bins = [prefix + ''.join(random.choice(chars) for _ in range(length)) for _ in range(count)]
        
        async def run_batch():
            async with aiohttp.ClientSession() as session:
                tasks = [async_check_bin(b) for b in generated_bins]
                return await asyncio.gather(*tasks)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        all_results = loop.run_until_complete(run_batch())
        
        valid_records = []
        for res in all_results:
            if res:
                if country and res['country_code'].upper() != country:
                    continue
                valid_records.append(f"Bin: {res['bin']} | Scheme: {res['scheme']} | Country: {res['country_code']} ({res['country_name']}) | Bank: {res['bank']}")
                
        if valid_records:
            filename = f"valid_bins_{user_id}.txt"
            with open(filename, "w") as f:
                f.write("\n".join(valid_records))
            with open(filename, "rb") as f:
                bot.send_document(message.chat.id, f, caption=f"✅ *Hunt complete! Found {len(valid_records)} valid bins.*", parse_mode="Markdown")
            os.remove(filename)
        else:
            bot.send_message(message.chat.id, "❌ *No valid bins found matching criteria in this batch.*", parse_mode="Markdown")
        bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)

    # --- GENERATOR FLOW ---
    elif action == "gen_bin":
        state["bin"] = text
        state["action"] = "gen_amount"
        bot.reply_to(message, "💳 How many cards do you want to generate? (e.g., `10`, `20`):", parse_mode="Markdown")
        
    elif action == "gen_amount":
        if not text.isdigit():
            bot.reply_to(message, "⚠️ Please enter a valid number for amount.")
            return
        
        bin_input = state.get("bin")
        amount = int(text)
        del USER_STATES[user_id]
        
        animation_msg = bot.reply_to(message, "⚡ *Generating cards... [▒▒▒▒▒▒▒▒▒▒] 0%*", parse_mode="Markdown")
        time.sleep(0.5)
        bot.edit_message_text("⚡ *Generating cards... [█████▒▒▒▒▒] 50%*", chat_id=message.chat.id, message_id=animation_msg.message_id, parse_mode="Markdown")
        time.sleep(0.5)
        
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
        with open(filename, "w") as f:
            f.write("\n".join(generated_list))
        with open(filename, "rb") as f:
            bot.send_document(message.chat.id, f, caption=f"✅ *Successfully generated {amount} cards!*", parse_mode="Markdown")
        os.remove(filename)
        bot.delete_message(chat_id=message.chat.id, message_id=animation_msg.message_id)

    # --- CHECKER FLOW ---
    elif action == "check_bin":
        bin_num = text
        del USER_STATES[user_id]
        
        msg = bot.reply_to(message, "⏳ *Checking bin details...*", parse_mode="Markdown")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        res = loop.run_until_complete(async_check_bin(bin_num))
        
        if res:
            out = (f"✅ *Bin Info Found*\n"
                   f"━━━━━━━━━━━━━━━━━━━\n"
                   f"📌 *Bin:* `{res['bin']}`\n"
                   f"💳 *Scheme:* `{res['scheme']}`\n"
                   f"🌍 *Country:* `{res['country_code']}` ({res['country_name']})\n"
                   f"🏛 *Bank:* `{res['bank']}`\n"
                   f"━━━━━━━━━━━━━━━━━━━")
            bot.edit_message_text(out, chat_id=message.chat.id, message_id=msg.message_id, parse_mode="Markdown")
        else:
            bot.edit_message_text(f"❌ *Invalid or dead bin:* `{bin_num}`", chat_id=message.chat.id, message_id=msg.message_id, parse_mode="Markdown")

# Direct Command Handlers
@bot.message_handler(commands=['check'])
def check_single_bin(message):
    if not is_user_subscribed(message.from_user.id):
        send_subscription_prompt(message.chat.id)
        return
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "Usage: `/check 475126`", parse_mode="Markdown")
            return
        bin_num = parts[1]
        msg = bot.reply_to(message, "⏳ *Checking bin details...*", parse_mode="Markdown")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        res = loop.run_until_complete(async_check_bin(bin_num))
        if res:
            out = (f"✅ *Bin Info Found*\n"
                   f"━━━━━━━━━━━━━━━━━━━\n"
                   f"📌 *Bin:* `{res['bin']}`\n"
                   f"💳 *Scheme:* `{res['scheme']}`\n"
                   f"🌍 *Country:* `{res['country_code']}` ({res['country_name']})\n"
                   f"🏛 *Bank:* `{res['bank']}`\n"
                   f"━━━━━━━━━━━━━━━━━━━")
            bot.edit_message_text(out, chat_id=message.chat.id, message_id=msg.message_id, parse_mode="Markdown")
        else:
            bot.edit_message_text(f"❌ *Invalid or dead bin:* `{bin_num}`", chat_id=message.chat.id, message_id=msg.message_id, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

@bot.message_handler(commands=['gen'])
def generate_cards(message):
    if not is_user_subscribed(message.from_user.id):
        send_subscription_prompt(message.chat.id)
        return
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "Usage: `/gen <bin> [month] [year] [cvv] [amount]`\nExample: `/gen 475126 12 2028 456 10`", parse_mode="Markdown")
            return
        bin_input = parts[1]
        month = parts[2] if len(parts) > 2 and parts[2].isdigit() else None
        year = parts[3] if len(parts) > 3 and parts[3].isdigit() else None
        cvv = parts[4] if len(parts) > 4 and parts[4].isdigit() else None
        amount = int(parts[5]) if len(parts) > 5 and parts[5].isdigit() else 10
        
        animation_msg = bot.reply_to(message, "⚡ *Generating cards... [▒▒▒▒▒▒▒▒▒▒] 0%*", parse_mode="Markdown")
        time.sleep(0.5)
        bot.edit_message_text("⚡ *Generating cards... [█████▒▒▒▒▒] 50%*", chat_id=message.chat.id, message_id=animation_msg.message_id, parse_mode="Markdown")
        time.sleep(0.5)
        
        generated_list = []
        target_len = 16 if not bin_input.startswith("3") else 15
        rem_len = target_len - len(bin_input)
        for _ in range(amount):
            rand_digits = "".join([str(random.randint(0, 9)) for _ in range(rem_len)])
            card_num = bin_input + rand_digits
            c_month = month if month else str(random.randint(1, 12)).zfill(2)
            c_year = year if year else str(random.randint(2027, 2032))
            c_cvv = cvv if cvv else (str(random.randint(100, 9999)) if bin_input.startswith("3") else str(random.randint(100, 999)))
            generated_list.append(f"{card_num}|{c_month}|{c_year}|{c_cvv}")
            
        filename = f"generated_{message.from_user.id}.txt"
        with open(filename, "w") as f:
            f.write("\n".join(generated_list))
        with open(filename, "rb") as f:
            bot.send_document(message.chat.id, f, caption=f"✅ *Successfully generated {amount} cards!*", parse_mode="Markdown")
        os.remove(filename)
        bot.delete_message(chat_id=message.chat.id, message_id=animation_msg.message_id)
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

@bot.message_handler(commands=['hunt'])
def hunt_bins_command(message):
    if not is_user_subscribed(message.from_user.id):
        send_subscription_prompt(message.chat.id)
        return
    try:
        parts = message.text.split()
        prefix = parts[1] if len(parts) > 1 else "37"
        count = int(parts[2]) if len(parts) > 2 else 10
        target_country = parts[3].upper() if len(parts) > 3 else None
        
        msg = bot.reply_to(message, f"⚡ *Hunting {count} bins with prefix {prefix}... [░░░░░░░░░░] 0%*", parse_mode="Markdown")
        chars = '0987654321'
        length = 4 if prefix != '574' else 3
        generated_bins = [prefix + ''.join(random.choice(chars) for _ in range(length)) for _ in range(count)]
        
        async def run_batch():
            async with aiohttp.ClientSession() as session:
                tasks = [async_check_bin(b) for b in generated_bins]
                return await asyncio.gather(*tasks)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        all_results = loop.run_until_complete(run_batch())
        
        valid_records = []
        for res in all_results:
            if res:
                if target_country and res['country_code'].upper() != target_country:
                    continue
                valid_records.append(f"Bin: {res['bin']} | Scheme: {res['scheme']} | Country: {res['country_code']} ({res['country_name']}) | Bank: {res['bank']}")
                
        if valid_records:
            filename = f"valid_bins_{message.from_user.id}.txt"
            with open(filename, "w") as f:
                f.write("\n".join(valid_records))
            with open(filename, "rb") as f:
                bot.send_document(message.chat.id, f, caption=f"✅ *Hunt complete! Found {len(valid_records)} valid bins.*", parse_mode="Markdown")
            os.remove(filename)
        else:
            bot.send_message(message.chat.id, "❌ *No valid bins found matching criteria in this batch.*", parse_mode="Markdown")
        bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)
    except Exception as e:
        bot.send_message(message.chat.id, f"Error during hunt: {str(e)}")

def run_bot():
    bot.remove_webhook()
    bot.infinity_polling()

if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
