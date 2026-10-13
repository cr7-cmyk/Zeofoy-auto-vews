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

USER_STATES = {}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0"
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

async def async_check_bin(bin_num):
    headers = get_random_headers()
    urls = [
        f"https://lookup.binlist.net/{bin_num}",
        f"https://data.handyapi.com/bin/{bin_num}"
    ]
    
    async with aiohttp.ClientSession() as session:
        for url in urls:
            try:
                async with session.get(url, headers=headers, timeout=4) as response:
                    if response.status == 200:
                        res = await response.json()
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
            except:
                pass
    return None

@app.route('/')
def home():
    return "Advanced Bin Hunter Bot is running!"

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
        bot.send_message(call.message.chat.id, "📥 *Hunt Setup*\n\nSend **BIN Prefix** (e.g., `37`, `47`, `574`):", parse_mode="Markdown")
        
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
        bot.reply_to(message, "🔢 Send how many bins to scan (e.g., `10`, `20`):", parse_mode="Markdown")
        
    elif action == "hunt_count":
        if not text.isdigit():
            bot.reply_to(message, "⚠️ Enter a valid number.")
            return
        state["count"] = int(text)
        state["action"] = "hunt_country"
        bot.reply_to(message, "🌍 Send **Country Code** (e.g., `US`, `BR`) or type `all`:", parse_mode="Markdown")
        
    elif action == "hunt_country":
        prefix = state.get("prefix")
        count = state.get("count")
        country = None if text.lower() == "all" else text.upper()
        
        del USER_STATES[user_id]
        
        msg = bot.reply_to(message, f"⚡ *Hunting bins with prefix {prefix}... Please wait.*", parse_mode="Markdown")
        
        length = 4 if prefix != '574' else 3
        chars = '0987654321'
        
        generated_bins = []
        for _ in range(count * 3):
            us = "".join(random.choice(chars) for _ in range(length))
            u1 = prefix + us
            if len(u1) >= 6:
                generated_bins.append(u1[:6])
        generated_bins = list(set(generated_bins))[:count]
        
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
            bot.send_message(message.chat.id, "❌ *No valid live bins found in this batch. Try prefix like 37, 47, or 574.*", parse_mode="Markdown")
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
        with open(filename, "w") as f:
            f.write("\n".join(generated_list))
        with open(filename, "rb") as f:
            bot.send_document(message.chat.id, f, caption=f"✅ *Successfully generated {amount} cards!*", parse_mode="Markdown")
        os.remove(filename)

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
        msg = bot.reply_to(message, "⏳ *Checking...*", parse_mode="Markdown")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        res = loop.run_until_complete(async_check_bin(bin_num))
        if res:
            out = f"✅ Bin: {res['bin']} | Scheme: {res['scheme']} | Country: {res['country_code']} | Bank: {res['bank']}"
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
