import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

import requests
import re
import time
import base64
import json
from urllib.parse import unquote


def start_keepalive():
    port = os.getenv("PORT")
    if not port:
        print("[*] No PORT env var, skipping keep-alive server")
        return
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"zefoy running")
        def do_HEAD(self):
            self.send_response(200)
            self.end_headers()
        def log_message(self, format, *args):
            pass
    httpd = HTTPServer(("0.0.0.0", int(port)), Handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    print(f"[*] Keep-alive server on port {port}")


class Zefoy:
    def __init__(self):
        self.base_url = "https://zefoy.com"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        self.session = requests.Session()
        self.proxy = None
        self.success = 0
        self.start_time = None
        # ---- Render env vars ----
        self.link = os.getenv("TIKTOK_URL", "").strip()
        if not self.link:
            raise SystemExit("TIKTOK_URL env var missing")
        self.service = os.getenv("SERVICE", "views").strip().lower()
        try:
            self.run_hours = float(os.getenv("RUN_HOURS", "0"))
        except Exception:
            self.run_hours = 0
        # -------------------------
        self.session.headers.update({
            "host": "zefoy.com",
            "x-requested-with": "XMLHttpRequest",
            "user-agent": self.user_agent,
            "accept": "*/*",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "origin": "https://zefoy.com"
        })

    def time_up(self):
        if self.run_hours <= 0:
            return False
        elapsed = time.time() - self.start_time
        return elapsed >= self.run_hours * 3600

    def decode_response(self, text):
        try:
            return base64.b64decode(unquote(text[::-1])).decode()
        except:
            return text

    def refresh_session(self):
        try:
            self.session.get(self.base_url, timeout=20)
        except:
            pass

    def login_web(self):
        response = self.session.get(self.base_url, timeout=20)
        if "captchatoken" not in response.text:
            return None, None
        captcha_token = re.search(r'id="captchatoken"\s+name="([^"]+)"', response.text).group(1)
        phpsessid = response.cookies.get("PHPSESSID")
        return captcha_token, phpsessid

    def get_captcha(self, phpsessid):
        self.session.cookies.update({"PHPSESSID": phpsessid})
        params = {"getcapthca": int(time.time())}
        response = self.session.get(self.base_url, params=params, timeout=20)
        encoded = response.text.split(":")[1].strip('"}')
        decoded = base64.b64decode(encoded)
        decoded = base64.b64decode(decoded)
        captcha_path = decoded.decode()
        captcha_url = f"{self.base_url}/{captcha_path}"
        image_response = self.session.get(captcha_url, timeout=20)
        return base64.b64encode(image_response.content).decode()

    def solve_captcha(self, image_base64):
        while True:
            if self.time_up():
                return ""
            try:
                image_bytes = base64.b64decode(image_base64)
                files = {"file": ("captcha.png", image_bytes, "image/png")}
                data = {"apikey": "helloworld", "language": "eng", "OCREngine": 2}
                headers = {"user-agent": self.user_agent}
                response = requests.post(
                    "https://api.ocr.space/parse/image",
                    files=files,
                    data=data,
                    headers=headers,
                    proxies=self.proxy,
                    timeout=30,
                    verify=False
                )
                result = response.json()
                if "ParsedResults" not in result:
                    continue
                answer = result["ParsedResults"][0]["ParsedText"].replace("\n", "").replace(" ", "").strip()
                print(f"[+] Captcha: {answer}")
                return answer
            except Exception as e:
                print(f"[-] Vpn ")
                print(e)
                continue

    def check_captcha(self, answer, phpsessid, captcha_token):
        self.session.cookies.update({"PHPSESSID": phpsessid})
        data = {captcha_token: answer, "captcha_encoded": ""}
        response = self.session.post(self.base_url, data=data, timeout=20)
        if "success" in response.text:
            print("[+] Captcha Solved")
            return True
        print("[-] Failed Captcha")
        return False

    def login_panel(self, phpsessid):
        self.session.cookies.update({"PHPSESSID": phpsessid})
        response = self.session.get(self.base_url, timeout=20)
        if "Enter Video URL" not in response.text:
            return None
        video_form = re.search(r'name="(.*?)"\s+placeholder="Enter Video URL"', response.text).group(1)
        print(f"[+] Video Form: {video_form}")
        return video_form

    def get_google_tokens(self):
        while True:
            if self.time_up():
                return None, None
            try:
                headers = {
                    "host": "partner.googleadservices.com",
                    "user-agent": self.user_agent
                }
                params = {
                    "domain": "zefoy.com",
                    "callback": "_gfp_s_",
                    "client": "ca-pub-3192305768699763",
                    "gpid_exp": 1
                }
                response = self.session.get(
                    "https://partner.googleadservices.com/gampad/cookie.js",
                    headers=headers,
                    params=params,
                    timeout=20
                )
                match = re.findall(r'_gfp_s_\((.*)\);', response.text)
                data = json.loads(match[0])
                gads = data["_cookies_"][0]["_value_"]
                gpi = data["_cookies_"][1]["_value_"]
                self.session.cookies.set("__gads", gads, domain="zefoy.com")
                self.session.cookies.set("__gpi", gpi, domain="zefoy.com")
                return gads, gpi
            except Exception:
                continue

    def get_wait_time(self, text):
        match = re.search(r"var ltm=(\d+)", text)
        if match:
            return int(match.group(1))
        return 30

    def send_like(self, html, link, phpsessid, video_form, gads, gpi, url):
        inputs = re.findall(r'<input[^>]*name="([^"]+)"[^>]*value="([^"]*)"', html)
        if len(inputs) < 3:
            return False
        payload = {}
        for kk, zv in inputs[:3]:
            payload[kk] = zv
        endpoint = url
        for pp in range(1000):
            if self.time_up():
                return False
            response = self.session.post(endpoint, data=payload, timeout=50)
            decoded = self.decode_response(response.text)
            if "10+ Hearts successfully sent." in decoded:
                self.success += 1
                print(f"[+] Success! Total: {self.success}")
                return True
            elif "Please wait, hearts are sendin" in decoded:
                print("wait sending")
                continue
            elif "Checking Timer" in decoded or "views-countdown" in decoded:
                wait_time = self.get_wait_time(decoded)
                print(f"[â³] Timer detected, waiting {wait_time} seconds...")
                for op in range(wait_time, 0, -1):
                    if self.time_up():
                        return False
                    print(f"\r[â³] Wait: {op}s ", end="", flush=True)
                    time.sleep(1)
                print()
                continue

    def send_views(self, html, link, phpsessid, video_form, gads, gpi, url):
        inputs = re.findall(r'<input[^>]*name="([^"]+)"[^>]*value="([^"]*)"', html)
        if len(inputs) < 3:
            return False
        payload = {}
        for d, o in inputs[:3]:
            payload[d] = o
        endpoint = url
        for xxw in range(1000):
            if self.time_up():
                return False
            response = self.session.post(endpoint, data=payload, timeout=20)
            decoded = self.decode_response(response.text)
            if "Successfully" in decoded and "views sent" in decoded:
                self.success += 1
                print(f"[+] Success! Total: {self.success}")
                return True
            elif "Checking Timer" in decoded or "views-countdown" in decoded:
                wait_time = self.get_wait_time(decoded)
                print(f"[â³] Timer detected, waiting {wait_time} seconds...")
                for oi in range(wait_time, 0, -1):
                    if self.time_up():
                        return False
                    print(f"\r[â³] Wait: {oi}s ", end="", flush=True)
                    time.sleep(1)
                print()
                continue
            elif "Please wait" in decoded:
                wait_match = re.search(r"Please wait (\d+)", decoded)
                if wait_match:
                    seconds = int(wait_match.group(1))
                    print(seconds)
                    for kk in range(seconds, 0, -1):
                        if self.time_up():
                            return False
                        print(f"\r[â³] Wait: {kk}s ", end="", flush=True)
                        time.sleep(1)
                    print()
                    continue
                else:
                    wait_time = self.get_wait_time(decoded)
                    for kk in range(wait_time, 0, -1):
                        if self.time_up():
                            return False
                        print(f"\r[â³] Wait: {kk}s ", end="", flush=True)
                        time.sleep(1)
                    print()
                    continue
            elif "Cloudflare" in decoded:
                print("[!] Cloudflare detected, waiting 10 seconds...")
                for kk in range(10, 0, -1):
                    if self.time_up():
                        return False
                    print(f"\r[â³] Waiting Cloudflare: {kk}s ", end="", flush=True)
                    time.sleep(1)
                print()
                continue
            else:
                print(f"[-] wait {xxw + 1} failed, retrying...")
                print(decoded)
                time.sleep(2)
        return False

    def start_service(self, phpsessid, video_form, gads, gpi, link, url):
        endpoint = url
        self.session.cookies.update({
            "PHPSESSID": phpsessid,
            "__gads": gads,
            "__gpi": gpi
        })
        while True:
            if self.time_up():
                return False
            self.refresh_session()
            payload = {video_form: link}
            response = self.session.post(endpoint, data=payload, timeout=20)
            decoded = self.decode_response(response.text)
            if "Checking Timer" in decoded or "views-countdown" in decoded:
                wait_time = self.get_wait_time(decoded)
                print(f"[â³] Timer detected, waiting {wait_time} seconds...")
                for pp in range(wait_time, 0, -1):
                    if self.time_up():
                        return False
                    print(f"\r[â³] Wait: {pp}s ", end="", flush=True)
                    time.sleep(1)
                print()
                continue
            if "Please wait" in decoded:
                wait_match = re.search(r"Please wait (\d+)", decoded)
                if wait_match:
                    seconds = int(wait_match.group(1))
                    for pp in range(seconds, 0, -1):
                        if self.time_up():
                            return False
                        print(f"\r[â³] Wait: {pp}s ", end="", flush=True)
                        time.sleep(1)
                    print()
                    continue
                else:
                    wait_time = self.get_wait_time(decoded)
                    for pp in range(wait_time, 0, -1):
                        if self.time_up():
                            return False
                        print(f"\r[â³] Wait: {pp}s ", end="", flush=True)
                        time.sleep(1)
                    print()
                    continue
            if "Session expired" in decoded:
                print("[!] Session Expired, restarting...")
                return False
            if "Cloudflare" in decoded:
                print("[!] Cloudflare detected, waiting 10 seconds...")
                for pp in range(10, 0, -1):
                    if self.time_up():
                        return False
                    print(f"\r[â³] Waiting Cloudflare: {pp}s ", end="", flush=True)
                    time.sleep(1)
                print()
                continue
            if 'name=' in decoded:
                if url == "https://zefoy.com/c2VuZC9mb2xeb3dlcnNfdGlrdG9V":
                    result = self.send_views(decoded, link, phpsessid, video_form, gads, gpi, url)
                    if result:
                        return True
                    else:
                        return False
                elif url == "https://zefoy.com/c2VuZF9mb2xsb3dlcnNfdGlrdG9L":
                    pass
                elif url == "https://zefoy.com/c2VuZE9nb2xsb3dlcnNfdGlrdG9r":
                    result = self.send_like(decoded, link, phpsessid, video_form, gads, gpi, url)
                    if result:
                        return True
                    else:
                        return False
            print("[-] Unknown response, retrying...")
            print(decoded)
            time.sleep(2)

    def run(self, url):
        self.start_time = time.time()
        print(f"[*] Service: {self.service}")
        print(f"[*] Link: {self.link}")
        print(f"[*] Auto stop after: {self.run_hours} hour(s) (0 = never)")
        while True:
            if self.time_up():
                print(f"\n[â] Auto stop: {self.run_hours} hour(s) completed. Total success: {self.success}")
                break

            print("\n[!] Starting new session...")
            self.session.cookies.clear()

            captcha_token, phpsessid = self.login_web()
            if captcha_token is None:
                print("[-] Failed to get captcha token, retrying...")
                time.sleep(2)
                continue

            captcha_image = self.get_captcha(phpsessid)
            captcha_answer = self.solve_captcha(captcha_image)
            if captcha_answer == "":
                print(f"\n[â] Auto stop reached during captcha. Total success: {self.success}")
                break

            if not self.check_captcha(captcha_answer, phpsessid, captcha_token):
                print("[-] Failed to solve captcha, retrying...")
                time.sleep(2)
                continue

            video_form = self.login_panel(phpsessid)
            if video_form is None:
                print("[-] Failed to get video form, retrying...")
                time.sleep(2)
                continue

            gads, gpi = self.get_google_tokens()
            if gads is None:
                print(f"\n[â] Auto stop reached during token fetch. Total success: {self.success}")
                break

            result = self.start_service(phpsessid, video_form, gads, gpi, self.link, url)
            if result:
                print(f"\n[â] Sent successfully! Total success: {self.success}")
                print("[*] Continuing to next round...")
                time.sleep(1)
                continue
            else:
                if self.time_up():
                    print(f"\n[â] Auto stop: {self.run_hours} hour(s) completed. Total success: {self.success}")
                    break
                print("[!] Service failed, restarting session...")
                time.sleep(2)
                continue


if __name__ == "__main__":
    start_keepalive()
    bot = Zefoy()
    if bot.service == "views":
        url = "https://zefoy.com/c2VuZC9mb2xeb3dlcnNfdGlrdG9V"
    elif bot.service == "likes":
        url = "https://zefoy.com/c2VuZE9nb2xsb3dlcnNfdGlrdG9r"
    else:
        exit("SERVICE must be views or likes")
    bot.run(url)
