import asyncio  # @avoidogu
import base64  # @avoidogu
import ctypes  # @avoidogu
import json  # @avoidogu
import os  # @avoidogu
import random  # @avoidogu
import sys  # @avoidogu
import threading  # @avoidogu
import time  # @avoidogu
import urllib.request  # @avoidogu
import uuid  # @avoidogu
from dataclasses import dataclass, field  # @avoidogu
from datetime import datetime  # @avoidogu
from typing import Optional  # @avoidogu
import re  # @avoidogu
from urllib.parse import quote, urlparse  # @avoidogu
import requests  # @avoidogu
# @avoidogu
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # @avoidogu
from tls2 import Client  # @avoidogu
# @avoidogu
BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0])) if sys.argv else os.path.dirname(os.path.abspath(__file__))  # @avoidogu
# @avoidogu
API_BASE = "https://discord.com/api/v9"  # @avoidogu
HCAPTCHA_SITEKEY = "472b4c9f-f2b7-4382-8135-c983f5496eb9"  # @avoidogu
with open(os.path.join(BASE_DIR, "config.json"), "r", encoding="utf-8") as _cf:  # @avoidogu
    CONFIG = json.load(_cf)  # @avoidogu
# @avoidogu
MAX_THREADS = CONFIG.get("max_threads", 4)  # @avoidogu
MAX_RETRIES = CONFIG.get("max_retries", 2)  # @avoidogu
CAPTCHA_HEAVEN_API_KEY = CONFIG.get("captchaheaven_api_key", "")  # @avoidogu
CAPTCHA_TIMEOUT = CONFIG.get("captcha_timeout", 120)  # @avoidogu
SMS_TIMEOUT = CONFIG.get("sms_timeout", 90)  # @avoidogu
# @avoidogu
# --- Live Discord info (fetched at startup, like sexy v3) ---  # @avoidogu
def _fetch_discord_info() -> dict:  # @avoidogu
    """Fetch live Discord info from eintim API (same source as sexy v3)."""  # @avoidogu
    try:  # @avoidogu
        import urllib.request as _ur  # @avoidogu
        req = _ur.Request("https://discord.eintim.dev/discord_info")  # @avoidogu
        with _ur.urlopen(req, timeout=10) as resp:  # @avoidogu
            return json.loads(resp.read())  # @avoidogu
    except Exception:  # @avoidogu
        return None  # @avoidogu
# @avoidogu
_discord_info = _fetch_discord_info()  # @avoidogu
# @avoidogu
if _discord_info and "desktop" in _discord_info:  # @avoidogu
    _desktop = _discord_info["desktop"]  # @avoidogu
    SUPER_PROPERTIES_RAW = _desktop["decoded-x-super-properties"]  # @avoidogu
    CLIENT_BUILD = SUPER_PROPERTIES_RAW.get("client_build_number", 567923)  # @avoidogu
    DISCORD_USER_AGENT = _desktop.get("user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9243 Chrome/128.0.6613.186 Electron/32.2.7 Safari/537.36")  # @avoidogu
else:  # @avoidogu
    # Fallback if API is down — use desktop values from last known  # @avoidogu
    CLIENT_BUILD = 567923  # @avoidogu
    DISCORD_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9243 Chrome/128.0.6613.186 Electron/32.2.7 Safari/537.36"  # @avoidogu
    SUPER_PROPERTIES_RAW = {  # @avoidogu
        "os": "Windows",  # @avoidogu
        "browser": "Discord Client",  # @avoidogu
        "release_channel": "stable",  # @avoidogu
        "client_version": "1.0.9243",  # @avoidogu
        "os_version": "10.0.26100",  # @avoidogu
        "os_arch": "x64",  # @avoidogu
        "app_arch": "x64",  # @avoidogu
        "system_locale": "en-US",  # @avoidogu
        "has_client_mods": False,  # @avoidogu
        "browser_user_agent": DISCORD_USER_AGENT,  # @avoidogu
        "browser_version": "32.2.7",  # @avoidogu
        "os_sdk_version": "26100",  # @avoidogu
        "client_build_number": CLIENT_BUILD,  # @avoidogu
        "native_build_number": 84934,  # @avoidogu
        "client_event_source": None,  # @avoidogu
    }  # @avoidogu
# @avoidogu
SUPER_PROPERTIES = base64.b64encode(json.dumps(SUPER_PROPERTIES_RAW).encode()).decode()  # @avoidogu
# @avoidogu
P = "\033[38;2;180;130;255m"  # @avoidogu
W = "\033[97m"  # @avoidogu
G = "\033[90m"  # @avoidogu
R = "\033[0m"  # @avoidogu
# @avoidogu
# Logger — ported from Checkout V3's modules/utils/logger.py (Console class):  # @avoidogu
# same palette, same timestamp/icon/connector layout, same level-gating rules.  # @avoidogu
class Col:  # @avoidogu
    green  = "\033[38;2;100;255;100m"  # @avoidogu
    red    = "\033[38;2;255;0;0m"  # @avoidogu
    gray   = "\033[38;2;150;150;150m"  # @avoidogu
    yellow = "\033[38;2;255;255;0m"  # @avoidogu
    lblue  = "\033[38;2;100;100;255m"  # @avoidogu
    cyan   = "\033[38;2;0;255;255m"  # @avoidogu
    white  = "\033[38;2;255;255;255m"  # @avoidogu
    reset  = "\033[0m"  # @avoidogu
# @avoidogu
LOGGER_LEVEL    = 2       # 2 - most detailed, 1 - medium, 0 - least detailed (matches config.yaml)  # @avoidogu
SHOW_EXTRA_INFO = False   # granular 3DS/OTP step chatter — opt-in, off by default  # @avoidogu
CONNECTOR       = "-->"  # @avoidogu
BOUNDER         = ","  # @avoidogu
SPACER          = ": "  # @avoidogu
# @avoidogu
_LEVEL_ICON  = {"success": "$", "info": ">", "warn": "!", "error": "X", "extra_info": "*"}  # @avoidogu
_LEVEL_COLOR = {"success": Col.green, "info": Col.lblue, "warn": Col.yellow, "error": Col.red, "extra_info": Col.cyan}  # @avoidogu
# @avoidogu
OUT_DIR = os.path.join(BASE_DIR, "out")  # @avoidogu
os.makedirs(OUT_DIR, exist_ok=True)  # @avoidogu
# @avoidogu
print_lock = threading.Lock()  # @avoidogu
file_lock = threading.Lock()  # @avoidogu
promo_lock = threading.Lock()  # @avoidogu
three_ds_lock = threading.Lock()  # @avoidogu
used_promos = set()  # @avoidogu
# @avoidogu
stats = {"redeemed": 0, "failed": 0, "skipped": 0, "captcha": 0}  # @avoidogu
stats_lock = threading.Lock()  # @avoidogu
# @avoidogu
_tz_cache: dict[str, str] = {}   # proxy -> timezone  (thread-safe via GIL for reads)  # @avoidogu
_tz_lock = threading.Lock()  # @avoidogu
# @avoidogu
# @avoidogu
# @avoidogu

class ProxyPool:  # @avoidogu
    """Thread-safe proxy pool — each token reserves (pops) a unique proxy."""  # @avoidogu
    def __init__(self, proxies: list[str]):  # @avoidogu
        self._pool = list(proxies)  # @avoidogu
        self._lock = threading.Lock()  # @avoidogu
# @avoidogu
    def reserve(self) -> Optional[str]:  # @avoidogu
        """Pop a proxy from the pool. Returns None if empty."""  # @avoidogu
        with self._lock:  # @avoidogu
            if self._pool:  # @avoidogu
                return self._pool.pop(0)  # @avoidogu
        return None  # @avoidogu
# @avoidogu
    def remaining(self) -> int:  # @avoidogu
        with self._lock:  # @avoidogu
            return len(self._pool)  # @avoidogu
# @avoidogu
    @staticmethod  # @avoidogu
    def delete_from_file(proxy: str):  # @avoidogu
        """Remove used proxy from proxies.txt so it's never reused."""  # @avoidogu
        path = os.path.join(BASE_DIR, "in", "proxies.txt")  # @avoidogu
        # Strip scheme for matching  # @avoidogu
        clean = proxy.replace("http://", "").replace("https://", "").replace("socks5://", "").replace("socks5h://", "")  # @avoidogu
        with file_lock:  # @avoidogu
            try:  # @avoidogu
                with open(path, "r", encoding="utf-8") as f:  # @avoidogu
                    lines = f.readlines()  # @avoidogu
                with open(path, "w", encoding="utf-8") as f:  # @avoidogu
                    for line in lines:  # @avoidogu
                        if clean not in line.strip():  # @avoidogu
                            f.write(line)  # @avoidogu
            except FileNotFoundError:  # @avoidogu
                pass  # @avoidogu
# @avoidogu
# @avoidogu
def test_proxy(proxy: Optional[str], timeout: int = 10) -> bool:  # @avoidogu
    """Return True if proxy can reach the internet within timeout seconds."""  # @avoidogu
    if not proxy:  # @avoidogu
        return True   # proxyless — always OK  # @avoidogu
    try:  # @avoidogu
        proxy_handler = urllib.request.ProxyHandler({  # @avoidogu
            "http":  proxy if proxy.startswith("http") else f"http://{proxy}",  # @avoidogu
            "https": proxy if proxy.startswith("http") else f"http://{proxy}",  # @avoidogu
        })  # @avoidogu
        opener = urllib.request.build_opener(proxy_handler)  # @avoidogu
        req = urllib.request.Request(  # @avoidogu
            "https://api.ipify.org?format=json",  # @avoidogu
            headers={"User-Agent": "Mozilla/5.0"}  # @avoidogu
        )  # @avoidogu
        with opener.open(req, timeout=timeout) as resp:  # @avoidogu
            data = json.loads(resp.read())  # @avoidogu
            return bool(data.get("ip"))  # @avoidogu
    except Exception:  # @avoidogu
        return False  # @avoidogu
# @avoidogu
# @avoidogu
def scrape_timezone(proxy: Optional[str] = None) -> str:  # @avoidogu
    """Fetch real timezone for the proxy's IP (5s timeout, won't block)."""  # @avoidogu
    cache_key = proxy or "direct"  # @avoidogu
    with _tz_lock:  # @avoidogu
        if cache_key in _tz_cache:  # @avoidogu
            return _tz_cache[cache_key]  # @avoidogu
    try:  # @avoidogu
        if proxy:  # @avoidogu
            proxy_handler = urllib.request.ProxyHandler({  # @avoidogu
                "http": f"http://{proxy}",  # @avoidogu
                "https": f"http://{proxy}",  # @avoidogu
            })  # @avoidogu
            opener = urllib.request.build_opener(proxy_handler)  # @avoidogu
        else:  # @avoidogu
            opener = urllib.request.build_opener()  # @avoidogu
# @avoidogu
        req = urllib.request.Request("https://api.ipify.org?format=json")  # @avoidogu
        with opener.open(req, timeout=5) as resp:  # @avoidogu
            ip = json.loads(resp.read()).get("ip", "")  # @avoidogu
# @avoidogu
        if ip:  # @avoidogu
            req2 = urllib.request.Request(f"http://ip-api.com/json/{ip}?fields=timezone")  # @avoidogu
            with opener.open(req2, timeout=5) as resp2:  # @avoidogu
                data = json.loads(resp2.read())  # @avoidogu
                tz = data.get("timezone", "")  # @avoidogu
                if tz:  # @avoidogu
                    with _tz_lock:  # @avoidogu
                        _tz_cache[cache_key] = tz  # @avoidogu
                    return tz  # @avoidogu
    except Exception:  # @avoidogu
        pass  # @avoidogu
    return "America/New_York"  # @avoidogu
# @avoidogu
# @avoidogu
SESSION_START = time.time()   # reset at the start of each redeem session, see main()  # @avoidogu
# @avoidogu
# @avoidogu
def _format_elapsed(seconds: float) -> str:  # @avoidogu
    m, s = divmod(int(seconds), 60)  # @avoidogu
    h, m = divmod(m, 60)  # @avoidogu
    return f"{h:02d}:{m:02d}:{s:02d}"  # @avoidogu
# @avoidogu
# @avoidogu
def _update_title():  # @avoidogu
    with stats_lock:  # @avoidogu
        r, f, s, c = stats["redeemed"], stats["failed"], stats["skipped"], stats["captcha"]  # @avoidogu
    elapsed = _format_elapsed(time.time() - SESSION_START)  # @avoidogu
    title = f"@avoidogu | Discord Promo Redeemer - Redeemed: {r} | Failed: {f} | Skipped: {s} | Captcha: {c} | Time: {elapsed}"  # @avoidogu
    if os.name == "nt":  # @avoidogu
        try:  # @avoidogu
            ctypes.windll.kernel32.SetConsoleTitleW(title)  # @avoidogu
        except Exception:  # @avoidogu
            pass  # @avoidogu
    else:  # @avoidogu
        sys.stdout.write(f"\033]0;{title}\007")  # @avoidogu
        sys.stdout.flush()  # @avoidogu
# @avoidogu
# @avoidogu
def _title_thread():  # @avoidogu
    # continuously-updating title bar — ported from Checkout V3's Console.title_thread  # @avoidogu
    while True:  # @avoidogu
        _update_title()  # @avoidogu
        time.sleep(0.5)  # @avoidogu
# @avoidogu
# @avoidogu
def stat(key: str):  # @avoidogu
    with stats_lock:  # @avoidogu
        stats[key] += 1  # @avoidogu
# @avoidogu
# @avoidogu
def stats_line() -> str:  # @avoidogu
    with stats_lock:  # @avoidogu
        return f"{Col.lblue}{stats['redeemed']}{W} redeemed {G}|{W} {Col.lblue}{stats['failed']}{W} failed {G}|{W} {Col.lblue}{stats['skipped']}{W} skipped"  # @avoidogu
# @avoidogu
# @avoidogu
threading.Thread(target=_title_thread, daemon=True).start()  # @avoidogu
# @avoidogu
# @avoidogu
def save(filename: str, line: str):  # @avoidogu
    with file_lock:  # @avoidogu
        with open(os.path.join(OUT_DIR, filename), "a", encoding="utf-8") as f:  # @avoidogu
            f.write(line + "\n")  # @avoidogu
# @avoidogu
# @avoidogu
def remove_line(filename: str, target: str):  # @avoidogu
    path = os.path.join(BASE_DIR, "in", filename)  # @avoidogu
    with file_lock:  # @avoidogu
        try:  # @avoidogu
            with open(path, "r", encoding="utf-8") as f:  # @avoidogu
                lines = f.readlines()  # @avoidogu
            with open(path, "w", encoding="utf-8") as f:  # @avoidogu
                for line in lines:  # @avoidogu
                    if target not in line:  # @avoidogu
                        f.write(line)  # @avoidogu
        except FileNotFoundError:  # @avoidogu
            pass  # @avoidogu
# @avoidogu
# @avoidogu
def mask_token(token: str) -> str:  # @avoidogu
    """Never print the full account token — always show a truncated form."""  # @avoidogu
    return token[:18] + "…" if len(token) > 18 else token  # @avoidogu
# @avoidogu
# @avoidogu
def _timestamp() -> str:  # @avoidogu
    _ORANGE = "\033[38;2;255;165;0m"  # @avoidogu
    return f"{Col.white}[{Col.gray}{datetime.now().strftime('%H:%M:%S')}{Col.white}] {_ORANGE}[@avoidogu]{Col.white}"  # @avoidogu
# @avoidogu
# @avoidogu
def _extra(col: str, *args, **kwargs) -> str:  # @avoidogu
    formatted_args = [f"{col}{v}" for v in args if v not in (None, "")]  # @avoidogu
    formatted_kwargs = [f"{Col.gray}{k}{SPACER}{col}{v}" for k, v in kwargs.items()]  # @avoidogu
    values = formatted_args + formatted_kwargs  # @avoidogu
    if not values:  # @avoidogu
        return ""  # @avoidogu
    joined = f"{Col.white}{BOUNDER}{col} ".join(values)  # @avoidogu
    return f"{Col.white} {CONNECTOR} {joined}"  # @avoidogu
# @avoidogu
# @avoidogu
def _emit(level: str, msg: str, *args, **kwargs):  # @avoidogu
    col = _LEVEL_COLOR[level]  # @avoidogu
    icon = _LEVEL_ICON[level]  # @avoidogu
    line = f"{_timestamp()} [{col}{icon}{Col.white}]{Col.gray} - {Col.white}{msg}{_extra(col, *args, **kwargs)}{Col.reset}"  # @avoidogu
    with print_lock:  # @avoidogu
        print(line)  # @avoidogu
# @avoidogu
# @avoidogu
def success(msg: str, *args, **kwargs):  # @avoidogu
    _emit("success", msg, *args, **kwargs)  # @avoidogu
# @avoidogu
# @avoidogu
def info(msg: str, *args, **kwargs):  # @avoidogu
    if LOGGER_LEVEL > 1 or (not args and not kwargs):  # @avoidogu
        _emit("info", msg, *args, **kwargs)  # @avoidogu
# @avoidogu
# @avoidogu
def warn(msg: str, *args, **kwargs):  # @avoidogu
    if LOGGER_LEVEL > 0:  # @avoidogu
        _emit("warn", msg, *args, **kwargs)  # @avoidogu
# @avoidogu
# @avoidogu
def error(msg: str, *args, **kwargs):  # @avoidogu
    _emit("error", msg, *args, **kwargs)  # @avoidogu
# @avoidogu
# @avoidogu
def extra_info(msg: str, *args, **kwargs):  # @avoidogu
    if SHOW_EXTRA_INFO:  # @avoidogu
        _emit("extra_info", msg, *args, **kwargs)  # @avoidogu
# @avoidogu
# @avoidogu
@dataclass  # @avoidogu
class RedeemResult:  # @avoidogu
    success: bool  # @avoidogu
    error_code: Optional[int] = None  # @avoidogu
    error_message: Optional[str] = None  # @avoidogu
    captcha_required: bool = False  # @avoidogu
    captcha_sitekey: Optional[str] = None  # @avoidogu
    captcha_service: Optional[str] = None  # @avoidogu
    captcha_rqdata: Optional[str] = None  # @avoidogu
    captcha_rqtoken: Optional[str] = None  # @avoidogu
    raw: Optional[dict] = field(default=None, repr=False)  # @avoidogu
# @avoidogu
# @avoidogu
@dataclass  # @avoidogu
class GiftCode:  # @avoidogu
    code: str  # @avoidogu
    sku_id: str  # @avoidogu
    application_id: str  # @avoidogu
    redeemed: bool  # @avoidogu
    expires_at: str  # @avoidogu
    max_uses: int  # @avoidogu
    uses: int  # @avoidogu
    subscription_plan_id: Optional[str] = None  # @avoidogu
    promotion_id: Optional[str] = None  # @avoidogu
    partner_id: Optional[str] = None  # @avoidogu
    restricted_countries: list = field(default_factory=list)  # @avoidogu
    raw: Optional[dict] = field(default=None, repr=False)  # @avoidogu
# @avoidogu
# @avoidogu
def load_tokens() -> list[tuple[Optional[str], Optional[str], str, Optional[str]]]:  # @avoidogu
    path = os.path.join(BASE_DIR, "in", "tokens.txt")  # @avoidogu
    results = []  # @avoidogu
    try:  # @avoidogu
        f = open(path, "r", encoding="utf-8")  # @avoidogu
    except FileNotFoundError:  # @avoidogu
        return results  # @avoidogu
    with f:  # @avoidogu
        for line in f:  # @avoidogu
            line = line.strip()  # @avoidogu
            if not line:  # @avoidogu
                continue  # @avoidogu
            proxy = None  # @avoidogu
            if "|" in line:  # @avoidogu
                line, proxy = line.rsplit("|", 1)  # @avoidogu
                proxy = proxy.strip()  # @avoidogu
                if proxy and not proxy.startswith(("http://", "https://", "socks5://", "socks5h://")):  # @avoidogu
                    proxy = f"http://{proxy}"  # @avoidogu
                if not proxy:  # @avoidogu
                    proxy = None  # @avoidogu
            m = re.search(r"([\w-]{24,}\.[\w-]{6}\.[\w-]{27,})", line)  # @avoidogu
            if m:  # @avoidogu
                tok = m.group(1)  # @avoidogu
                prefix = line[:m.start()].rstrip(":").rstrip()  # @avoidogu
                if ";" in prefix:  # @avoidogu
                    email, password = prefix.split(";", 1)  # @avoidogu
                elif ":" in prefix:  # @avoidogu
                    email, password = prefix.split(":", 1)  # @avoidogu
                else:  # @avoidogu
                    email, password = None, None  # @avoidogu
                results.append((email, password, tok, proxy))  # @avoidogu
            else:  # @avoidogu
                results.append((None, None, line, proxy))  # @avoidogu
    return results  # @avoidogu
# @avoidogu
# @avoidogu
def load_promos() -> list[str]:  # @avoidogu
    path = os.path.join(BASE_DIR, "in", "promos.txt")  # @avoidogu
    codes = []  # @avoidogu
    try:  # @avoidogu
        f = open(path, "r", encoding="utf-8")  # @avoidogu
    except FileNotFoundError:  # @avoidogu
        return codes  # @avoidogu
    with f:  # @avoidogu
        for line in f:  # @avoidogu
            line = line.strip()  # @avoidogu
            if not line:  # @avoidogu
                continue  # @avoidogu
            code = line.split("/")[-1]  # @avoidogu
            codes.append(code)  # @avoidogu
    return codes  # @avoidogu
# @avoidogu
# @avoidogu
def load_proxies() -> list[str]:  # @avoidogu
    path = os.path.join(BASE_DIR, "in", "proxies.txt")  # @avoidogu
    proxies = []  # @avoidogu
    try:  # @avoidogu
        with open(path, "r", encoding="utf-8") as f:  # @avoidogu
            for line in f:  # @avoidogu
                line = line.strip()  # @avoidogu
                if not line:  # @avoidogu
                    continue  # @avoidogu
                if not line.startswith(("http://", "https://", "socks5://", "socks5h://")):  # @avoidogu
                    line = f"http://{line}"  # @avoidogu
                proxies.append(line)  # @avoidogu
    except FileNotFoundError:  # @avoidogu
        pass  # @avoidogu
    return proxies  # @avoidogu
# @avoidogu
# @avoidogu
# --- CaptchaHeaven solver (cap_client.py SDK) ---  # @avoidogu
import sys as _sys  # @avoidogu
_sys.path.insert(0, BASE_DIR)  # @avoidogu
from cap_client import CapClient, CapAPIError  # @avoidogu
# @avoidogu
_cap_client: CapClient | None = None  # @avoidogu
_cap_client_lock = threading.Lock()  # @avoidogu
# @avoidogu
def _get_cap_client() -> CapClient:  # @avoidogu
    """Return a shared CapClient instance, created once on first use."""  # @avoidogu
    global _cap_client  # @avoidogu
    with _cap_client_lock:  # @avoidogu
        if _cap_client is None:  # @avoidogu
            if not CAPTCHA_HEAVEN_API_KEY:  # @avoidogu
                raise RuntimeError("captchaheaven_api_key is not set in config.json")  # @avoidogu
            _cap_client = CapClient(api_key=CAPTCHA_HEAVEN_API_KEY, max_wait=float(CAPTCHA_TIMEOUT))  # @avoidogu
        return _cap_client  # @avoidogu
# @avoidogu
# @avoidogu
# @avoidogu

# @avoidogu
# @avoidogu
class DiscordRedeemer:  # @avoidogu
    def __init__(self, token: str, proxy: Optional[str] = None):  # @avoidogu
        self.token = token  # @avoidogu
        self.proxy = proxy  # @avoidogu
        self.payment_source_id: Optional[str] = None  # @avoidogu
        self.client = Client(proxy=proxy)  # @avoidogu
        # Per-session IDs — mirrors sexy v3's client_heartbeat_session_id / client_launch_id  # @avoidogu
        self._session_id = str(uuid.uuid4())  # @avoidogu
        self._launch_id  = str(uuid.uuid4())  # @avoidogu
        self._timezone   = "America/New_York"   # updated by setup_session()  # @avoidogu
        self._cookies: dict = {}  # @avoidogu
# @avoidogu
    def setup_session(self):  # @avoidogu
        """Fetch real timezone + warm up Discord session (non-blocking, safe)."""  # @avoidogu
        # Timezone — quick, has its own 5s timeout per request  # @avoidogu
        try:  # @avoidogu
            self._timezone = scrape_timezone(self.proxy)  # @avoidogu
        except Exception:  # @avoidogu
            self._timezone = "America/New_York"  # @avoidogu
# @avoidogu
        # Warm up session by hitting a harmless endpoint (gets cookies set)  # @avoidogu
        try:  # @avoidogu
            resp = self.client.get(  # @avoidogu
                f"{API_BASE}/users/@me/affinities/guilds",  # @avoidogu
                headers=self._headers(),  # @avoidogu
            )  # @avoidogu
            # tls2 Response may not have .cookies — guard it  # @avoidogu
            if resp.ok and hasattr(resp, 'cookies'):  # @avoidogu
                try:  # @avoidogu
                    for k, v in resp.cookies.items():  # @avoidogu
                        self._cookies[k] = v  # @avoidogu
                except Exception:  # @avoidogu
                    pass  # @avoidogu
        except Exception:  # @avoidogu
            pass  # @avoidogu
# @avoidogu
    def _super_properties(self) -> str:  # @avoidogu
        """Build enriched super-properties with live session IDs (sexy v3 style)."""  # @avoidogu
        props = dict(SUPER_PROPERTIES_RAW)  # @avoidogu
        props["client_app_state"]             = "focused"  # @avoidogu
        props["client_heartbeat_session_id"]  = self._session_id  # @avoidogu
        props["client_launch_id"]             = self._launch_id  # @avoidogu
        return base64.b64encode(json.dumps(props).encode()).decode()  # @avoidogu
# @avoidogu
    def _headers(self, extra: Optional[dict] = None, referer_code: Optional[str] = None) -> list[tuple[str, str]]:  # @avoidogu
        ref = f"https://discord.com/billing/promotions/{referer_code}" if referer_code else "https://discord.com/billing/promotions"  # @avoidogu
        h = [  # @avoidogu
            ("Accept", "*/*"),  # @avoidogu
            ("Accept-Encoding", "gzip, br"),  # @avoidogu
            ("Accept-Language", "en-US;q=0.9"),  # @avoidogu
            ("Authorization", self.token),  # @avoidogu
            ("Content-Type", "application/json"),  # @avoidogu
            ("Origin", "https://discord.com"),  # @avoidogu
            ("Referer", ref),  # @avoidogu
            ("Priority", "u=1, i"),  # @avoidogu
            ("Sec-Ch-Ua-Mobile", "?0"),  # @avoidogu
            ("Sec-Ch-Ua-Platform", '"Windows"'),  # @avoidogu
            ("Sec-Fetch-Dest", "empty"),  # @avoidogu
            ("Sec-Fetch-Mode", "cors"),  # @avoidogu
            ("Sec-Fetch-Site", "same-origin"),  # @avoidogu
            ("User-Agent", DISCORD_USER_AGENT),  # @avoidogu
            ("X-Debug-Options", "bugReporterEnabled"),  # @avoidogu
            ("X-Discord-Locale", "en-US"),  # @avoidogu
            ("X-Discord-Timezone", self._timezone),  # @avoidogu
            ("X-Super-Properties", self._super_properties()),  # @avoidogu
        ]  # @avoidogu
        if self._cookies:  # @avoidogu
            cookie_str = "; ".join(f"{k}={v}" for k, v in self._cookies.items())  # @avoidogu
            h.append(("Cookie", cookie_str))  # @avoidogu
        if extra:  # @avoidogu
            h.extend(extra.items())  # @avoidogu
        return h  # @avoidogu
# @avoidogu
    def close(self):  # @avoidogu
        self.client.close()  # @avoidogu
# @avoidogu
    def get_user(self) -> dict:  # @avoidogu
        resp = self.client.get(f"{API_BASE}/users/@me", headers=self._headers())  # @avoidogu
        if not resp.ok:  # @avoidogu
            raise RuntimeError(f"get_user: {resp.status} {resp.text}")  # @avoidogu
        return resp.json()  # @avoidogu
# @avoidogu
    def get_country_code(self) -> str:  # @avoidogu
        resp = self.client.get(f"{API_BASE}/users/@me/billing/country-code", headers=self._headers())  # @avoidogu
        if not resp.ok:  # @avoidogu
            raise RuntimeError(f"get_country_code: {resp.status} {resp.text}")  # @avoidogu
        return resp.json().get("country_code", "US")  # @avoidogu
# @avoidogu
    def get_payment_sources(self) -> list:  # @avoidogu
        resp = self.client.get(f"{API_BASE}/users/@me/billing/payment-sources", headers=self._headers())  # @avoidogu
        if not resp.ok:  # @avoidogu
            raise RuntimeError(f"get_payment_sources: {resp.status} {resp.text}")  # @avoidogu
        return resp.json()  # @avoidogu
# @avoidogu
    def has_active_subscription(self) -> bool:  # @avoidogu
        resp = self.client.get(f"{API_BASE}/users/@me/billing/subscriptions", headers=self._headers())  # @avoidogu
        if not resp.ok:  # @avoidogu
            return False  # @avoidogu
        subs = resp.json()  # @avoidogu
        return any(s.get("status") in (1, "active") for s in subs)  # @avoidogu
# @avoidogu
    def has_had_nitro(self) -> bool:  # @avoidogu
        resp = self.client.get(f"{API_BASE}/users/@me/billing/subscriptions?include_inactive=true", headers=self._headers())  # @avoidogu
        if not resp.ok:  # @avoidogu
            return False  # @avoidogu
        return len(resp.json()) > 0  # @avoidogu
# @avoidogu
    def resolve_gift_code(self, code: str, country_code: str = "US") -> GiftCode:  # @avoidogu
        params = f"country_code={country_code}&with_application=false&with_subscription_plan=true"  # @avoidogu
        if self.payment_source_id:  # @avoidogu
            params += f"&payment_source_id={self.payment_source_id}"  # @avoidogu
        resp = self.client.get(f"{API_BASE}/entitlements/gift-codes/{code}?{params}", headers=self._headers(referer_code=code))  # @avoidogu
        if not resp.ok:  # @avoidogu
            raise RuntimeError(f"resolve: {resp.status} {resp.text}")  # @avoidogu
        data = resp.json()  # @avoidogu
        promo = data.get("promotion") or {}  # @avoidogu
        return GiftCode(  # @avoidogu
            code=data["code"],  # @avoidogu
            sku_id=data["sku_id"],  # @avoidogu
            application_id=data["application_id"],  # @avoidogu
            redeemed=data.get("redeemed", False),  # @avoidogu
            expires_at=data.get("expires_at", ""),  # @avoidogu
            max_uses=data.get("max_uses", 0),  # @avoidogu
            uses=data.get("uses", 0),  # @avoidogu
            subscription_plan_id=data.get("subscription_plan_id"),  # @avoidogu
            promotion_id=promo.get("id"),  # @avoidogu
            partner_id=promo.get("partner_id"),  # @avoidogu
            restricted_countries=promo.get("inbound_restricted_countries", []),  # @avoidogu
            raw=data,  # @avoidogu
        )  # @avoidogu
# @avoidogu
    def redeem(self, code: str, captcha_key: Optional[str] = None, captcha_rqtoken: Optional[str] = None, captcha_session_id: Optional[str] = None) -> RedeemResult:  # @avoidogu
        body = json.dumps({  # @avoidogu
            "channel_id": None,  # @avoidogu
            "payment_source_id": self.payment_source_id,  # @avoidogu
            "gateway_checkout_context": None,  # @avoidogu
        })  # @avoidogu
        extra = {}  # @avoidogu
        if captcha_key:  # @avoidogu
            extra["X-Captcha-Key"] = captcha_key  # @avoidogu
        if captcha_rqtoken:  # @avoidogu
            extra["X-Captcha-Rqtoken"] = captcha_rqtoken  # @avoidogu
        if captcha_session_id:  # @avoidogu
            extra["X-Captcha-Session-Id"] = captcha_session_id  # @avoidogu
        resp = self.client.post(  # @avoidogu
            f"{API_BASE}/entitlements/gift-codes/{code}/redeem",  # @avoidogu
            body=body,  # @avoidogu
            headers=self._headers(extra if extra else None, referer_code=code),  # @avoidogu
        )  # @avoidogu
        if resp.ok:  # @avoidogu
            try:  # @avoidogu
                return RedeemResult(success=True, raw=resp.json())  # @avoidogu
            except Exception:  # @avoidogu
                return RedeemResult(success=True)  # @avoidogu
        try:  # @avoidogu
            data = resp.json()  # @avoidogu
        except Exception:  # @avoidogu
            return RedeemResult(success=False, error_code=resp.status, error_message="invalid response")  # @avoidogu
        if data.get("captcha_key"):  # @avoidogu
            return RedeemResult(  # @avoidogu
                success=False,  # @avoidogu
                captcha_required=True,  # @avoidogu
                captcha_sitekey=data.get("captcha_sitekey"),  # @avoidogu
                captcha_service=data.get("captcha_service"),  # @avoidogu
                captcha_rqdata=data.get("captcha_rqdata"),  # @avoidogu
                captcha_rqtoken=data.get("captcha_rqtoken"),  # @avoidogu
                raw=data,  # @avoidogu
            )  # @avoidogu
        return RedeemResult(success=False, error_code=data.get("code"), error_message=data.get("message"), raw=data)  # @avoidogu
# @avoidogu
    def get_stripe_payment_intent(self, payment_id: str) -> dict:  # @avoidogu
        resp = self.client.get(  # @avoidogu
            f"{API_BASE}/users/@me/billing/stripe/payment-intents/payments/{payment_id}",  # @avoidogu
            headers=self._headers(),  # @avoidogu
        )  # @avoidogu
        if not resp.ok:  # @avoidogu
            raise RuntimeError(f"stripe intent: {resp.status} {resp.text}")  # @avoidogu
        return resp.json()  # @avoidogu
# @avoidogu
    def poll_payment(self, payment_id: str) -> dict:  # @avoidogu
        resp = self.client.get(  # @avoidogu
            f"{API_BASE}/users/@me/billing/payments/{payment_id}",  # @avoidogu
            headers=self._headers(),  # @avoidogu
        )  # @avoidogu
        if not resp.ok:  # @avoidogu
            raise RuntimeError(f"poll payment: {resp.status} {resp.text}")  # @avoidogu
        return resp.json()  # @avoidogu
# @avoidogu
# @avoidogu
SMSBOT_KEY = CONFIG.get("smsbot_key", "")  # @avoidogu
SMSBOT_BASE = "https://cabinet.smsbot.cc/api/v1"  # @avoidogu
SMSBOT_RENTAL_ID = CONFIG.get("smsbot_rental_id", "")  # @avoidogu
# @avoidogu
_otp_channel_ids = CONFIG.get("otp_channel_ids", CONFIG.get("discord_otp_channel_ids", []))  # @avoidogu
DISCORD_OTP_CHANNEL_ID = (_otp_channel_ids[0] if isinstance(_otp_channel_ids, list) and _otp_channel_ids else str(_otp_channel_ids)) if _otp_channel_ids else CONFIG.get("discord_otp_channel_id", "")  # @avoidogu
DISCORD_OTP_TOKEN = CONFIG.get("otp_bot_token", CONFIG.get("discord_otp_token", ""))  # @avoidogu
DISCORD_OTP_TIMEOUT = CONFIG.get("discord_otp_timeout", SMS_TIMEOUT)  # @avoidogu
# @avoidogu
# @avoidogu
class SMSBot:  # @avoidogu
    def __init__(self):  # @avoidogu
        self.client = requests.Session()  # @avoidogu
# @avoidogu
    def _headers(self) -> dict:  # @avoidogu
        return {  # @avoidogu
            "Accept": "application/json",  # @avoidogu
            "Authorization": f"Bearer {SMSBOT_KEY}",  # @avoidogu
        }  # @avoidogu
# @avoidogu
    def close(self):  # @avoidogu
        self.client.close()  # @avoidogu
# @avoidogu
    def get_sms(self, rental_id: str) -> list:  # @avoidogu
        try:  # @avoidogu
            r = self.client.get(f"{SMSBOT_BASE}/rentals/{rental_id}", headers=self._headers(), timeout=15)  # @avoidogu
            if not r.ok:  # @avoidogu
                return []  # @avoidogu
            data = r.json().get("data", {})  # @avoidogu
            return data.get("smsMessages", [])  # @avoidogu
        except Exception:  # @avoidogu
            return []  # @avoidogu
# @avoidogu
    def poll_code(self, rental_id: str, timeout: int = 60, seen: Optional[set] = None) -> Optional[str]:  # @avoidogu
        seen = set(seen) if seen else set()  # @avoidogu
        deadline = time.time() + timeout  # @avoidogu
        while time.time() < deadline:  # @avoidogu
            for msg in self.get_sms(rental_id):  # @avoidogu
                if msg.get("id") in seen:  # @avoidogu
                    continue  # @avoidogu
                code = msg.get("extractedCode") or msg.get("code")  # @avoidogu
                if code:  # @avoidogu
                    return code  # @avoidogu
            time.sleep(0.2)  # @avoidogu
        return None  # @avoidogu
# @avoidogu
# @avoidogu
_OTP_RE = re.compile(r'(?:pin|otp)\s+is\s+(\d{4,8})', re.IGNORECASE)  # @avoidogu
_OTP_FALLBACK_RE = re.compile(r'\b(\d{6})\b')  # @avoidogu
# @avoidogu
# @avoidogu
def _extract_otp(text: str) -> Optional[str]:  # @avoidogu
    m = _OTP_RE.search(text)  # @avoidogu
    if m:  # @avoidogu
        return m.group(1)  # @avoidogu
    m = _OTP_FALLBACK_RE.search(text)  # @avoidogu
    return m.group(1) if m else None  # @avoidogu
# @avoidogu
# @avoidogu
class DiscordOTPPoller:  # @avoidogu
    def __init__(self):  # @avoidogu
        self.client = requests.Session()  # @avoidogu
# @avoidogu
    def _headers(self) -> dict:  # @avoidogu
        _tok = DISCORD_OTP_TOKEN  # @avoidogu
        if _tok and not _tok.startswith(("Bot ", "Bearer ")):  # @avoidogu
            _tok = f"Bot {_tok}"  # @avoidogu
        return {  # @avoidogu
            "Accept": "application/json",  # @avoidogu
            "Authorization": _tok,  # @avoidogu
        }  # @avoidogu
# @avoidogu
    def close(self):  # @avoidogu
        self.client.close()  # @avoidogu
# @avoidogu
    def get_messages(self, after: Optional[str] = None, limit: int = 50) -> list:  # @avoidogu
        if not DISCORD_OTP_CHANNEL_ID:  # @avoidogu
            return []  # @avoidogu
        url = f"{API_BASE}/channels/{DISCORD_OTP_CHANNEL_ID}/messages?limit={limit}"  # @avoidogu
        if after:  # @avoidogu
            url += f"&after={after}"  # @avoidogu
        try:  # @avoidogu
            r = self.client.get(url, headers=self._headers(), timeout=15)  # @avoidogu
            if not r.ok:  # @avoidogu
                error(f"Discord messages API error: {r.status_code} {r.text[:200]}")  # @avoidogu
                return []  # @avoidogu
            return r.json()  # @avoidogu
        except Exception as e:  # @avoidogu
            error(f"Discord messages fetch error: {e}")  # @avoidogu
            return []  # @avoidogu
# @avoidogu
    def snapshot_latest_id(self) -> Optional[str]:  # @avoidogu
        msgs = self.get_messages(limit=1)  # @avoidogu
        return msgs[0]["id"] if msgs else None  # @avoidogu
# @avoidogu
    def poll_otp(self, timeout: int = 60, after_id: Optional[str] = None) -> Optional[str]:  # @avoidogu
        deadline = time.time() + timeout  # @avoidogu
        while time.time() < deadline:  # @avoidogu
            msgs = self.get_messages(after=after_id)  # @avoidogu
            for msg in sorted(msgs, key=lambda m: int(m.get("id", "0"))):  # @avoidogu
                content = msg.get("content", "")  # @avoidogu
                for embed in msg.get("embeds", []):  # @avoidogu
                    content += " " + (embed.get("description") or "")  # @avoidogu
                    content += " " + (embed.get("title") or "")  # @avoidogu
                    for field in embed.get("fields", []):  # @avoidogu
                        content += " " + (field.get("value") or "")  # @avoidogu
                otp = _extract_otp(content)  # @avoidogu
                if otp:  # @avoidogu
                    return otp  # @avoidogu
                after_id = msg.get("id", after_id)  # @avoidogu
            time.sleep(2)  # @avoidogu
        return None  # @avoidogu
# @avoidogu
# @avoidogu
STRIPE_KEY = "pk_live_CUQtlpQUF0vufWpnpUmQvcdi"  # @avoidogu
STRIPE_VERSION = "2025-03-31.basil"  # @avoidogu
# @avoidogu
# @avoidogu
class StripeClient:  # @avoidogu
    def __init__(self, proxy: Optional[str] = None):  # @avoidogu
        self.client = Client(proxy=proxy)  # @avoidogu
# @avoidogu
    def _headers(self) -> list[tuple[str, str]]:  # @avoidogu
        return [  # @avoidogu
            ("Accept", "application/json"),  # @avoidogu
            ("Content-Type", "application/x-www-form-urlencoded"),  # @avoidogu
            ("Origin", "https://js.stripe.com"),  # @avoidogu
            ("Referer", "https://js.stripe.com/"),  # @avoidogu
            ("User-Agent", SUPER_PROPERTIES_RAW["browser_user_agent"]),  # @avoidogu
        ]  # @avoidogu
# @avoidogu
    def close(self):  # @avoidogu
        self.client.close()  # @avoidogu
# @avoidogu
    def get_payment_intent(self, pi_id: str, client_secret: str) -> dict:  # @avoidogu
        url = f"https://api.stripe.com/v1/payment_intents/{pi_id}?is_stripe_sdk=false&client_secret={client_secret}&key={STRIPE_KEY}"  # @avoidogu
        resp = self.client.get(url, headers=self._headers())  # @avoidogu
        if not resp.ok:  # @avoidogu
            raise RuntimeError(f"stripe get pi: {resp.status}")  # @avoidogu
        return resp.json()  # @avoidogu
# @avoidogu
    def confirm(self, pi_id: str, client_secret: str) -> dict:  # @avoidogu
        body = f"expected_payment_method_type=card&use_stripe_sdk=true&key={STRIPE_KEY}&_stripe_version={STRIPE_VERSION}&client_secret={client_secret}"  # @avoidogu
        resp = self.client.post(  # @avoidogu
            f"https://api.stripe.com/v1/payment_intents/{pi_id}/confirm",  # @avoidogu
            body=body,  # @avoidogu
            headers=self._headers(),  # @avoidogu
        )  # @avoidogu
        if not resp.ok:  # @avoidogu
            raise RuntimeError(f"stripe confirm: {resp.status} {resp.text[:300]}")  # @avoidogu
        return resp.json()  # @avoidogu
# @avoidogu
    def authenticate_3ds2(self, source: str) -> dict:  # @avoidogu
        browser_json = json.dumps({  # @avoidogu
            "fingerprintAttempted": False,  # @avoidogu
            "fingerprintData": None,  # @avoidogu
            "challengeWindowSize": None,  # @avoidogu
            "threeDSCompInd": "Y",  # @avoidogu
            "browserJavascriptEnabled": True,  # @avoidogu
            "browserJavaEnabled": False,  # @avoidogu
            "browserLanguage": "en-US",  # @avoidogu
            "browserColorDepth": "24",  # @avoidogu
            "browserScreenHeight": "1080",  # @avoidogu
            "browserScreenWidth": "1920",  # @avoidogu
            "browserTZ": "-180",  # @avoidogu
            "browserUserAgent": SUPER_PROPERTIES_RAW["browser_user_agent"],  # @avoidogu
        })  # @avoidogu
        body = (  # @avoidogu
            f"source={quote(source, safe='')}"  # @avoidogu
            f"&browser={quote(browser_json, safe='')}"  # @avoidogu
            f"&one_click_authn_device_support[hosted]=false"  # @avoidogu
            f"&one_click_authn_device_support[same_origin_frame]=false"  # @avoidogu
            f"&one_click_authn_device_support[spc_eligible]=false"  # @avoidogu
            f"&one_click_authn_device_support[webauthn_eligible]=false"  # @avoidogu
            f"&one_click_authn_device_support[publickey_credentials_get_allowed]=true"  # @avoidogu
            f"&key={STRIPE_KEY}"  # @avoidogu
        )  # @avoidogu
        resp = self.client.post(  # @avoidogu
            "https://api.stripe.com/v1/3ds2/authenticate",  # @avoidogu
            body=body,  # @avoidogu
            headers=self._headers(),  # @avoidogu
        )  # @avoidogu
        if not resp.ok:  # @avoidogu
            raise RuntimeError(f"stripe 3ds2 auth: {resp.status} {resp.text[:300]}")  # @avoidogu
        return resp.json()  # @avoidogu
# @avoidogu
    def challenge_complete(self, source: str, cres_json: str) -> dict:  # @avoidogu
        body = f"source={quote(source, safe='')}&final_cres={quote(cres_json, safe='')}&key={STRIPE_KEY}&_stripe_version={STRIPE_VERSION}"  # @avoidogu
        resp = self.client.post(  # @avoidogu
            "https://api.stripe.com/v1/3ds2/challenge_complete",  # @avoidogu
            body=body,  # @avoidogu
            headers=self._headers(),  # @avoidogu
        )  # @avoidogu
        if not resp.ok:  # @avoidogu
            raise RuntimeError(f"stripe challenge_complete: {resp.status}")  # @avoidogu
        return resp.json()  # @avoidogu
# @avoidogu
    def notify_3ds(self, notify_url: str, cres: str) -> bool:  # @avoidogu
        body = f"cres={quote(cres, safe='')}"  # @avoidogu
        resp = self.client.post(notify_url, body=body, headers=self._headers())  # @avoidogu
        return resp.ok  # @avoidogu
# @avoidogu
# @avoidogu
def complete_3ds_apata(acs_url: str, acs_trans_id: str, server_trans_id: str, proxy: Optional[str] = None, rental_id: Optional[str] = None, tag: str = "") -> str:  # @avoidogu
    c = Client(proxy=proxy)  # @avoidogu
    headers = [  # @avoidogu
        ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),  # @avoidogu
        ("Content-Type", "application/x-www-form-urlencoded"),  # @avoidogu
        ("Origin", "https://acs-challenge.apata.io"),  # @avoidogu
        ("Referer", acs_url),  # @avoidogu
        ("User-Agent", SUPER_PROPERTIES_RAW["browser_user_agent"]),  # @avoidogu
    ]  # @avoidogu
# @avoidogu
    try:  # @avoidogu
        creq_data = base64.b64encode(json.dumps({  # @avoidogu
            "threeDSServerTransID": server_trans_id,  # @avoidogu
            "acsTransID": acs_trans_id,  # @avoidogu
            "challengeWindowSize": "05",  # @avoidogu
            "messageType": "CReq",  # @avoidogu
            "messageVersion": "2.2.0",  # @avoidogu
        }).encode()).decode()  # @avoidogu
# @avoidogu
        creq_resp = c.post(acs_url, body=f"creq={quote(creq_data, safe='')}", headers=headers)  # @avoidogu
        if not creq_resp.ok:  # @avoidogu
            raise RuntimeError(f"creq POST failed: {creq_resp.status}")  # @avoidogu
# @avoidogu
        poll_token_match = re.search(r'pollToken\s*[=:]\s*["\']([^"\']+)["\']', creq_resp.text)  # @avoidogu
        poll_token = poll_token_match.group(1) if poll_token_match else None  # @avoidogu
# @avoidogu
        if poll_token:  # @avoidogu
            poll_headers = [  # @avoidogu
                ("Accept", "application/json"),  # @avoidogu
                ("Content-Type", "application/json; charset=UTF-8"),  # @avoidogu
                ("Origin", "https://acs-challenge.apata.io"),  # @avoidogu
                ("Referer", acs_url),  # @avoidogu
                ("User-Agent", SUPER_PROPERTIES_RAW["browser_user_agent"]),  # @avoidogu
            ]  # @avoidogu
            for _ in range(10):  # @avoidogu
                r = c.post(  # @avoidogu
                    "https://acs-challenge.apata.io/v1/PollTransaction",  # @avoidogu
                    body=json.dumps({"pollToken": poll_token}),  # @avoidogu
                    headers=poll_headers,  # @avoidogu
                )  # @avoidogu
                try:  # @avoidogu
                    d = r.json()  # @avoidogu
                    if d.get("state") != "PENDING":  # @avoidogu
                        break  # @avoidogu
                except Exception:  # @avoidogu
                    pass  # @avoidogu
                time.sleep(2)  # @avoidogu
        else:  # @avoidogu
            extra_info("no pollToken in creq response — skipping poll", tag)  # @avoidogu
# @avoidogu
        # Try SUBMIT (OOB "already confirmed") first  # @avoidogu
        r = c.post(  # @avoidogu
            "https://acs-challenge.apata.io/v1/BrowserCReqAction",  # @avoidogu
            body=f"transactionId={acs_trans_id}&answer=none&action=SUBMIT",  # @avoidogu
            headers=headers,  # @avoidogu
        )  # @avoidogu
        cres_match = re.search(r'name="cres" value="([^"]+)"', r.text)  # @avoidogu
# @avoidogu
        if not cres_match:  # @avoidogu
            tid_match = re.search(r'name="transactionId" value="([^"]+)"', r.text)  # @avoidogu
            page_tid = tid_match.group(1) if tid_match else acs_trans_id  # @avoidogu
            extra_info("OOB submit rejected, falling back to OTP", tag)  # @avoidogu
# @avoidogu
            # snapshot BEFORE triggering FALLBACK so delayed stale codes are excluded  # @avoidogu
            pre_fallback_seen: set = set()  # @avoidogu
            if rental_id:  # @avoidogu
                _snap = SMSBot()  # @avoidogu
                try:  # @avoidogu
                    for m in _snap.get_sms(rental_id):  # @avoidogu
                        if m.get("id"):  # @avoidogu
                            pre_fallback_seen.add(m["id"])  # @avoidogu
                except Exception:  # @avoidogu
                    pass  # @avoidogu
                finally:  # @avoidogu
                    _snap.close()  # @avoidogu
            discord_after_id: Optional[str] = None  # @avoidogu
            if DISCORD_OTP_CHANNEL_ID and DISCORD_OTP_TOKEN:  # @avoidogu
                _dsnap = DiscordOTPPoller()  # @avoidogu
                try:  # @avoidogu
                    discord_after_id = _dsnap.snapshot_latest_id()  # @avoidogu
                except Exception:  # @avoidogu
                    pass  # @avoidogu
                finally:  # @avoidogu
                    _dsnap.close()  # @avoidogu
# @avoidogu
            r = c.post(  # @avoidogu
                "https://acs-challenge.apata.io/v1/BrowserCReqAction",  # @avoidogu
                body=f"transactionId={page_tid}&acctId={page_tid}&action=FALLBACK&fallbackButton=Confirmar+por+SMS",  # @avoidogu
                headers=headers,  # @avoidogu
            )  # @avoidogu
            cres_match = re.search(r'name="cres" value="([^"]+)"', r.text)  # @avoidogu
# @avoidogu
        if not cres_match:  # @avoidogu
            save("apata_fallback.html", r.text)  # @avoidogu
            extra_info("saved fallback page to out/apata_fallback.html", tag)  # @avoidogu
            has_otp_form = "answer" in r.text and "SUBMIT" in r.text  # @avoidogu
            if has_otp_form and (bool(DISCORD_OTP_CHANNEL_ID and DISCORD_OTP_TOKEN) or rental_id):  # @avoidogu
                tid_match = re.search(r'name="transactionId" value="([^"]+)"', r.text)  # @avoidogu
                current_tid = tid_match.group(1) if tid_match else acs_trans_id  # @avoidogu
                # submit fingerprint data required by apata before OTP is accepted  # @avoidogu
                otp_pt_match = re.search(r'pollToken\s*[=:]\s*["\']([^"\']+)["\']', r.text)  # @avoidogu
                if otp_pt_match:  # @avoidogu
                    otp_poll_token = otp_pt_match.group(1)  # @avoidogu
                    fp_headers = [  # @avoidogu
                        ("Accept", "application/json"),  # @avoidogu
                        ("Content-Type", "application/json"),  # @avoidogu
                        ("Origin", "https://acs-challenge.apata.io"),  # @avoidogu
                        ("Referer", acs_url),  # @avoidogu
                        ("User-Agent", SUPER_PROPERTIES_RAW["browser_user_agent"]),  # @avoidogu
                    ]  # @avoidogu
                    try:  # @avoidogu
                        c.post(  # @avoidogu
                            "https://acs-challenge.apata.io/v1/submitBbioProfile",  # @avoidogu
                            body=json.dumps({"pollToken": otp_poll_token, "bbioData": base64.b64encode(b"{}").decode()}),  # @avoidogu
                            headers=fp_headers,  # @avoidogu
                        )  # @avoidogu
                    except Exception:  # @avoidogu
                        pass  # @avoidogu
                    try:  # @avoidogu
                        c.post(  # @avoidogu
                            "https://acs-challenge.apata.io/v2/submitBBioDeviceId",  # @avoidogu
                            body=json.dumps({"pollToken": otp_poll_token, "deviceId": "automated"}),  # @avoidogu
                            headers=fp_headers,  # @avoidogu
                        )  # @avoidogu
                    except Exception:  # @avoidogu
                        pass  # @avoidogu
                    extra_info("submitted fingerprint data", tag)  # @avoidogu
# @avoidogu
                _use_discord = bool(DISCORD_OTP_CHANNEL_ID and DISCORD_OTP_TOKEN)  # @avoidogu
                if _use_discord:  # @avoidogu
                    extra_info("OTP required — polling Discord channel…", tag)  # @avoidogu
                    disc = DiscordOTPPoller()  # @avoidogu
                    try:  # @avoidogu
                        for otp_attempt in range(3):  # @avoidogu
                            otp_code = disc.poll_otp(timeout=DISCORD_OTP_TIMEOUT, after_id=discord_after_id)  # @avoidogu
                            if not otp_code:  # @avoidogu
                                if otp_attempt < 2:  # @avoidogu
                                    warn("Discord OTP timed out, requesting resend…", tag)  # @avoidogu
                                    c.post(  # @avoidogu
                                        "https://acs-challenge.apata.io/v1/BrowserCReqAction",  # @avoidogu
                                        body=f"transactionId={current_tid}&action=RESEND",  # @avoidogu
                                        headers=headers,  # @avoidogu
                                    )  # @avoidogu
                                    continue  # @avoidogu
                                raise RuntimeError("Discord OTP timed out after retries")  # @avoidogu
                            extra_info(f"got OTP from Discord: {otp_code}", tag)  # @avoidogu
                            r = c.post(  # @avoidogu
                                "https://acs-challenge.apata.io/v1/BrowserCReqAction",  # @avoidogu
                                body=f"transactionId={current_tid}&answer={otp_code}&action=SUBMIT",  # @avoidogu
                                headers=headers,  # @avoidogu
                            )  # @avoidogu
                            cres_match = re.search(r'name="cres" value="([^"]+)"', r.text)  # @avoidogu
                            if cres_match:  # @avoidogu
                                break  # @avoidogu
                            if "answer" in r.text and "SUBMIT" in r.text:  # @avoidogu
                                tid_match2 = re.search(r'name="transactionId" value="([^"]+)"', r.text)  # @avoidogu
                                if tid_match2:  # @avoidogu
                                    current_tid = tid_match2.group(1)  # @avoidogu
                                err_match = re.search(r'class="error[^"]*"[^>]*>([^<]+)<', r.text)  # @avoidogu
                                err_hint = err_match.group(1).strip() if err_match else "no error text found"  # @avoidogu
                                warn(f"wrong OTP ({err_hint}), retrying…", tag)  # @avoidogu
                                save("apata_wrong_otp.html", r.text)  # @avoidogu
                                continue  # @avoidogu
                            save("apata_otp_response.html", r.text)  # @avoidogu
                            break  # @avoidogu
                    finally:  # @avoidogu
                        disc.close()  # @avoidogu
                else:  # @avoidogu
                    extra_info("OTP required — polling SMS…", tag)  # @avoidogu
                    sms = SMSBot()  # @avoidogu
                    sms_seen: set = set(pre_fallback_seen) if rental_id else set()  # @avoidogu
                    try:  # @avoidogu
                        for otp_attempt in range(3):  # @avoidogu
                            code = sms.poll_code(rental_id, timeout=SMS_TIMEOUT, seen=sms_seen)  # @avoidogu
                            if not code:  # @avoidogu
                                if otp_attempt < 2:  # @avoidogu
                                    warn("SMS timed out, requesting resend…", tag)  # @avoidogu
                                    c.post(  # @avoidogu
                                        "https://acs-challenge.apata.io/v1/BrowserCReqAction",  # @avoidogu
                                        body=f"transactionId={current_tid}&action=RESEND",  # @avoidogu
                                        headers=headers,  # @avoidogu
                                    )  # @avoidogu
                                    continue  # @avoidogu
                                raise RuntimeError("SMS OTP timed out after retries")  # @avoidogu
                            extra_info(f"got OTP: {code}", tag)  # @avoidogu
                            r = c.post(  # @avoidogu
                                "https://acs-challenge.apata.io/v1/BrowserCReqAction",  # @avoidogu
                                body=f"transactionId={current_tid}&answer={code}&action=SUBMIT",  # @avoidogu
                                headers=headers,  # @avoidogu
                            )  # @avoidogu
                            cres_match = re.search(r'name="cres" value="([^"]+)"', r.text)  # @avoidogu
                            if cres_match:  # @avoidogu
                                break  # @avoidogu
                            if "answer" in r.text and "SUBMIT" in r.text:  # @avoidogu
                                tid_match2 = re.search(r'name="transactionId" value="([^"]+)"', r.text)  # @avoidogu
                                if tid_match2:  # @avoidogu
                                    current_tid = tid_match2.group(1)  # @avoidogu
                                err_match = re.search(r'class="error[^"]*"[^>]*>([^<]+)<', r.text)  # @avoidogu
                                err_hint = err_match.group(1).strip() if err_match else "no error text found"  # @avoidogu
                                warn(f"wrong OTP ({err_hint}), retrying…", tag)  # @avoidogu
                                save("apata_wrong_otp.html", r.text)  # @avoidogu
                                continue  # @avoidogu
                            save("apata_otp_response.html", r.text)  # @avoidogu
                            break  # @avoidogu
                    finally:  # @avoidogu
                        sms.close()  # @avoidogu
            elif has_otp_form:  # @avoidogu
                raise RuntimeError("OTP required but no rental_id or Discord config")  # @avoidogu
# @avoidogu
        if not cres_match:  # @avoidogu
            raise RuntimeError(f"no cres from apata: {r.text[:300]}")  # @avoidogu
# @avoidogu
        cres_b64 = cres_match.group(1)  # @avoidogu
        padded = cres_b64 + "=" * (4 - len(cres_b64) % 4) if len(cres_b64) % 4 else cres_b64  # @avoidogu
        cres_json = base64.b64decode(padded).decode("utf-8")  # @avoidogu
# @avoidogu
        notify_match = re.search(r'<form[^>]+action="([^"]+)"', r.text)  # @avoidogu
        notify_url = notify_match.group(1) if notify_match else None  # @avoidogu
# @avoidogu
        return json.dumps({"cres_json": cres_json, "cres_b64": cres_b64, "notify_url": notify_url})  # @avoidogu
    finally:  # @avoidogu
        c.close()  # @avoidogu
# @avoidogu
# @avoidogu
def complete_3ds_entersekt(acs_url: str, acs_trans_id: str, server_trans_id: str, proxy: Optional[str] = None, tag: str = "") -> str:  # @avoidogu
    c = requests.Session()  # @avoidogu
    if proxy:  # @avoidogu
        c.proxies = {"http": proxy, "https": proxy}  # @avoidogu
    acs_origin = f"https://{urlparse(acs_url).netloc}"  # @avoidogu
    req_headers = {  # @avoidogu
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",  # @avoidogu
        "Content-Type": "application/x-www-form-urlencoded",  # @avoidogu
        "Origin": acs_origin,  # @avoidogu
        "Referer": acs_url,  # @avoidogu
        "User-Agent": SUPER_PROPERTIES_RAW["browser_user_agent"],  # @avoidogu
    }  # @avoidogu
# @avoidogu
    def _parse_form(html):  # @avoidogu
        form_match = re.search(r'<form[^>]+action=["\']([^"\']+)["\']', html, re.IGNORECASE)  # @avoidogu
        action = form_match.group(1) if form_match else None  # @avoidogu
        if action and action.startswith("/"):  # @avoidogu
            action = f"{acs_origin}{action}"  # @avoidogu
        hidden = {}  # @avoidogu
        submit_fields = {}  # @avoidogu
        otp_field = "challengeDataEntry"  # @avoidogu
        for inp in re.finditer(r'<input[^>]+>', html, re.IGNORECASE):  # @avoidogu
            h = inp.group(0)  # @avoidogu
            typ_m = re.search(r'type=["\']([^"\']+)["\']', h, re.IGNORECASE)  # @avoidogu
            nam_m = re.search(r'name=["\']([^"\']+)["\']', h)  # @avoidogu
            val_m = re.search(r'value=["\']([^"\']*)["\']', h)  # @avoidogu
            if not nam_m:  # @avoidogu
                continue  # @avoidogu
            typ = typ_m.group(1).lower() if typ_m else "text"  # @avoidogu
            if typ == "hidden":  # @avoidogu
                hidden[nam_m.group(1)] = val_m.group(1) if val_m else ""  # @avoidogu
            elif typ == "submit":  # @avoidogu
                submit_fields[nam_m.group(1)] = val_m.group(1) if val_m else ""  # @avoidogu
            elif typ in ("text", "tel", "number", "password") and otp_field == "challengeDataEntry":  # @avoidogu
                otp_field = nam_m.group(1)  # @avoidogu
        for btn in re.finditer(r'<button[^>]+>', html, re.IGNORECASE):  # @avoidogu
            h = btn.group(0)  # @avoidogu
            typ_m = re.search(r'type=["\']([^"\']+)["\']', h, re.IGNORECASE)  # @avoidogu
            nam_m = re.search(r'name=["\']([^"\']+)["\']', h)  # @avoidogu
            val_m = re.search(r'value=["\']([^"\']*)["\']', h)  # @avoidogu
            if typ_m and typ_m.group(1).lower() == "submit" and nam_m:  # @avoidogu
                submit_fields[nam_m.group(1)] = val_m.group(1) if val_m else ""  # @avoidogu
        return action, hidden, otp_field, submit_fields  # @avoidogu
# @avoidogu
    try:  # @avoidogu
        creq_data = base64.b64encode(json.dumps({  # @avoidogu
            "threeDSServerTransID": server_trans_id,  # @avoidogu
            "acsTransID": acs_trans_id,  # @avoidogu
            "challengeWindowSize": "05",  # @avoidogu
            "messageType": "CReq",  # @avoidogu
            "messageVersion": "2.2.0",  # @avoidogu
        }).encode()).decode()  # @avoidogu
# @avoidogu
        creq_resp = c.post(acs_url, data={"creq": creq_data}, headers=req_headers)  # @avoidogu
        if not creq_resp.ok:  # @avoidogu
            raise RuntimeError(f"entersekt creq POST failed: {creq_resp.status_code}")  # @avoidogu
# @avoidogu
        save("entersekt_challenge.html", creq_resp.text)  # @avoidogu
# @avoidogu
        form_action, hidden_fields, otp_field, submit_fields = _parse_form(creq_resp.text)  # @avoidogu
        if not form_action:  # @avoidogu
            raise RuntimeError(f"no form in entersekt challenge page: {creq_resp.text[:300]}")  # @avoidogu
# @avoidogu
        discord_after_id: Optional[str] = None  # @avoidogu
        if DISCORD_OTP_CHANNEL_ID and DISCORD_OTP_TOKEN:  # @avoidogu
            _dsnap = DiscordOTPPoller()  # @avoidogu
            try:  # @avoidogu
                discord_after_id = _dsnap.snapshot_latest_id()  # @avoidogu
            except Exception:  # @avoidogu
                pass  # @avoidogu
            finally:  # @avoidogu
                _dsnap.close()  # @avoidogu
# @avoidogu
        cres_match = None  # @avoidogu
        submit_resp = None  # @avoidogu
        for attempt in range(3):  # @avoidogu
            extra_info(f"entersekt OTP — polling Discord… (attempt {attempt + 1}/3)", tag)  # @avoidogu
            disc = DiscordOTPPoller()  # @avoidogu
            try:  # @avoidogu
                otp_code = disc.poll_otp(timeout=DISCORD_OTP_TIMEOUT, after_id=discord_after_id)  # @avoidogu
            finally:  # @avoidogu
                disc.close()  # @avoidogu
# @avoidogu
            if not otp_code:  # @avoidogu
                raise RuntimeError("Discord OTP timed out for entersekt 3DS")  # @avoidogu
# @avoidogu
            extra_info(f"got OTP from Discord: {otp_code}", tag)  # @avoidogu
# @avoidogu
            payload = {**hidden_fields, otp_field: otp_code, **submit_fields}  # @avoidogu
            submit_resp = c.post(form_action, data=payload, headers=req_headers)  # @avoidogu
            save("entersekt_submit.html", submit_resp.text)  # @avoidogu
# @avoidogu
            cres_match = re.search(r'name=["\']cres["\'][^>]*value=["\']([^"\']+)["\']', submit_resp.text, re.IGNORECASE)  # @avoidogu
            if not cres_match:  # @avoidogu
                cres_match = re.search(r'value=["\']([^"\']+)["\'][^>]*name=["\']cres["\']', submit_resp.text, re.IGNORECASE)  # @avoidogu
            if cres_match:  # @avoidogu
                break  # @avoidogu
# @avoidogu
            new_action, new_hidden, new_otp_field, new_submit_fields = _parse_form(submit_resp.text)  # @avoidogu
            if new_action and attempt < 2:  # @avoidogu
                err_m = re.search(r'class="[^"]*error[^"]*"[^>]*>([^<]+)<', submit_resp.text, re.IGNORECASE)  # @avoidogu
                err_hint = err_m.group(1).strip() if err_m else "wrong OTP"  # @avoidogu
                warn(f"wrong OTP ({err_hint}), retrying…", tag)  # @avoidogu
                save("entersekt_wrong_otp.html", submit_resp.text)  # @avoidogu
                form_action, hidden_fields, otp_field, submit_fields = new_action, new_hidden, new_otp_field, new_submit_fields  # @avoidogu
                continue  # @avoidogu
            raise RuntimeError(f"no cres from entersekt after OTP submit: {submit_resp.text[:300]}")  # @avoidogu
# @avoidogu
        if not cres_match:  # @avoidogu
            raise RuntimeError("entersekt: no cres after retries")  # @avoidogu
# @avoidogu
        cres_b64 = cres_match.group(1)  # @avoidogu
        padded = cres_b64 + "=" * (4 - len(cres_b64) % 4) if len(cres_b64) % 4 else cres_b64  # @avoidogu
        cres_json = base64.b64decode(padded).decode("utf-8")  # @avoidogu
# @avoidogu
        notify_match = re.search(r'<form[^>]+action=["\']([^"\']+)["\']', submit_resp.text, re.IGNORECASE)  # @avoidogu
        notify_url = notify_match.group(1) if notify_match else None  # @avoidogu
# @avoidogu
        return json.dumps({"cres_json": cres_json, "cres_b64": cres_b64, "notify_url": notify_url})  # @avoidogu
    finally:  # @avoidogu
        c.close()  # @avoidogu
# @avoidogu
# @avoidogu
def handle_3ds(redeemer, payment_id: str, proxy: Optional[str] = None, tag: str = "", rental_id: Optional[str] = None) -> bool:  # @avoidogu
    extra_info(f"3DS auth required (payment {payment_id})", tag)  # @avoidogu
# @avoidogu
    intent_data = redeemer.get_stripe_payment_intent(payment_id)  # @avoidogu
    client_secret = intent_data["stripe_payment_intent_client_secret"]  # @avoidogu
    pi_id = client_secret.split("_secret_")[0]  # @avoidogu
# @avoidogu
    def _run(use_proxy):  # @avoidogu
        stripe = StripeClient(proxy=use_proxy)  # @avoidogu
        try:  # @avoidogu
            confirm_pi = stripe.confirm(pi_id, client_secret)  # @avoidogu
            extra_info("confirmed payment intent", tag)  # @avoidogu
# @avoidogu
            # Frictionless — Stripe approved during confirm itself  # @avoidogu
            if confirm_pi.get("status") == "succeeded":  # @avoidogu
                extra_info("payment succeeded immediately after confirm (frictionless)", tag)  # @avoidogu
                for _ in range(15):  # @avoidogu
                    time.sleep(1)  # @avoidogu
                    payment = redeemer.poll_payment(payment_id)  # @avoidogu
                    if payment.get("status", 0) != 0:  # @avoidogu
                        extra_info(f"payment status: {payment.get('status')}", tag)  # @avoidogu
                        return True  # @avoidogu
                return True  # @avoidogu
# @avoidogu
            pi = stripe.get_payment_intent(pi_id, client_secret)  # @avoidogu
            pi_status = pi.get("status", "")  # @avoidogu
            sdk = pi.get("next_action", {}).get("use_stripe_sdk", {})  # @avoidogu
            source = sdk.get("three_d_secure_2_source")  # @avoidogu
            server_trans_id = sdk.get("server_transaction_id")  # @avoidogu
# @avoidogu
            extra_info(f"source={source} server_tx={server_trans_id} status={pi_status}", tag)  # @avoidogu
# @avoidogu
            # Already succeeded after re-fetch  # @avoidogu
            if pi_status == "succeeded":  # @avoidogu
                extra_info("payment intent already succeeded — no 3DS challenge needed", tag)  # @avoidogu
                for _ in range(15):  # @avoidogu
                    time.sleep(1)  # @avoidogu
                    payment = redeemer.poll_payment(payment_id)  # @avoidogu
                    if payment.get("status", 0) != 0:  # @avoidogu
                        extra_info(f"payment status: {payment.get('status')}", tag)  # @avoidogu
                        return True  # @avoidogu
                return True  # @avoidogu
# @avoidogu
            if not source:  # @avoidogu
                error("no 3ds2 source in payment intent", tag)  # @avoidogu
                return False  # @avoidogu
# @avoidogu
            auth = stripe.authenticate_3ds2(source)  # @avoidogu
            auth_state = auth.get("state", "")  # @avoidogu
            ares = auth.get("ares", {})  # @avoidogu
            acs_url = ares.get("acsURL", "") or auth.get("acs_url", "") or auth.get("acsURL", "")  # @avoidogu
            acs_trans_id = ares.get("acsTransID", "")  # @avoidogu
            trans_status = ares.get("transStatus", "")  # @avoidogu
# @avoidogu
            extra_info(f"3DS2 auth_state={auth_state} trans_status={trans_status} acs={acs_url[:40]}…", tag)  # @avoidogu
# @avoidogu
            # Frictionless — auth succeeded outright  # @avoidogu
            if auth_state == "succeeded":  # @avoidogu
                extra_info("3DS authenticate state=succeeded — frictionless approved", tag)  # @avoidogu
                for _ in range(15):  # @avoidogu
                    time.sleep(1)  # @avoidogu
                    payment = redeemer.poll_payment(payment_id)  # @avoidogu
                    if payment.get("status", 0) != 0:  # @avoidogu
                        extra_info(f"payment status: {payment.get('status')}", tag)  # @avoidogu
                        return True  # @avoidogu
                return True  # @avoidogu
# @avoidogu
            if trans_status == "Y":  # @avoidogu
                extra_info("3DS frictionless (Y) — approved without challenge", tag)  # @avoidogu
                for _ in range(15):  # @avoidogu
                    time.sleep(1)  # @avoidogu
                    payment = redeemer.poll_payment(payment_id)  # @avoidogu
                    if payment.get("status", 0) != 0:  # @avoidogu
                        extra_info(f"payment status: {payment.get('status')}", tag)  # @avoidogu
                        return True  # @avoidogu
                error("payment never settled after frictionless Y", tag)  # @avoidogu
                return False  # @avoidogu
# @avoidogu
            if trans_status == "A":  # @avoidogu
                extra_info("3DS attempted (A) — proceeding without challenge", tag)  # @avoidogu
                for _ in range(15):  # @avoidogu
                    time.sleep(1)  # @avoidogu
                    payment = redeemer.poll_payment(payment_id)  # @avoidogu
                    if payment.get("status", 0) != 0:  # @avoidogu
                        extra_info(f"payment status: {payment.get('status')}", tag)  # @avoidogu
                        return True  # @avoidogu
                error("payment never settled after attempted A", tag)  # @avoidogu
                return False  # @avoidogu
# @avoidogu
            # Challenge required (C) — try ACS flow  # @avoidogu
            if trans_status == "C" and acs_url:  # @avoidogu
                if "apata.io" in acs_url:  # @avoidogu
                    extra_info("apata ACS — auto-completing", tag)  # @avoidogu
                    result_json = complete_3ds_apata(acs_url, acs_trans_id, server_trans_id, proxy=use_proxy, rental_id=rental_id, tag=tag)  # @avoidogu
                elif "entersekt" in acs_url:  # @avoidogu
                    extra_info("entersekt ACS — auto-completing", tag)  # @avoidogu
                    result_json = complete_3ds_entersekt(acs_url, acs_trans_id, server_trans_id, proxy=use_proxy, tag=tag)  # @avoidogu
                else:  # @avoidogu
                    error(f"unsupported ACS: {acs_url}", tag)  # @avoidogu
                    result_json = None  # @avoidogu
# @avoidogu
                if result_json:  # @avoidogu
                    result = json.loads(result_json)  # @avoidogu
                    cres_json_val = result["cres_json"]  # @avoidogu
                    notify_url = result.get("notify_url")  # @avoidogu
                    if notify_url:  # @avoidogu
                        stripe.notify_3ds(notify_url, result["cres_b64"])  # @avoidogu
                    stripe.challenge_complete(source, cres_json_val)  # @avoidogu
                    extra_info("3DS challenge completed", tag)  # @avoidogu
                    for _ in range(15):  # @avoidogu
                        time.sleep(1)  # @avoidogu
                        payment = redeemer.poll_payment(payment_id)  # @avoidogu
                        if payment.get("status", 0) != 0:  # @avoidogu
                            extra_info(f"payment status: {payment.get('status')}", tag)  # @avoidogu
                            return True  # @avoidogu
                    error("payment never settled after challenge", tag)  # @avoidogu
                    return False  # @avoidogu
# @avoidogu
            # Fallback: redirect-confirm approach (sexy v3 strategy)  # @avoidogu
            extra_info("trying redirect-confirm fallback", tag)  # @avoidogu
            redirect_body = (  # @avoidogu
                f"expected_payment_method_type=card"  # @avoidogu
                f"&return_url={quote('https://discord.com/billing/premium', safe='')}"  # @avoidogu
                f"&key={STRIPE_KEY}"  # @avoidogu
                f"&client_secret={quote(client_secret, safe='')}"  # @avoidogu
            )  # @avoidogu
            redirect_resp = stripe.client.post(  # @avoidogu
                f"https://api.stripe.com/v1/payment_intents/{pi_id}/confirm",  # @avoidogu
                body=redirect_body,  # @avoidogu
                headers=stripe._headers(),  # @avoidogu
            )  # @avoidogu
            if redirect_resp.ok:  # @avoidogu
                rj = redirect_resp.json()  # @avoidogu
                if rj.get("status") == "succeeded":  # @avoidogu
                    extra_info("redirect-confirm succeeded", tag)  # @avoidogu
                    for _ in range(15):  # @avoidogu
                        time.sleep(1)  # @avoidogu
                        payment = redeemer.poll_payment(payment_id)  # @avoidogu
                        if payment.get("status", 0) != 0:  # @avoidogu
                            extra_info(f"payment status: {payment.get('status')}", tag)  # @avoidogu
                            return True  # @avoidogu
                    return True  # @avoidogu
# @avoidogu
            error(f"3DS rejected: state={auth_state} trans_status={trans_status}", tag)  # @avoidogu
            return False  # @avoidogu
        finally:  # @avoidogu
            stripe.close()  # @avoidogu
# @avoidogu
    try:  # @avoidogu
        return _run(proxy)  # @avoidogu
    except Exception as e:  # @avoidogu
        if proxy and ("403" in str(e) or "proxy" in str(e).lower()):  # @avoidogu
            warn("proxy blocked 3DS — retrying direct…", tag)  # @avoidogu
            return _run(None)  # @avoidogu
        raise  # @avoidogu
# @avoidogu
# @avoidogu
def solve_captcha(result, code, proxy, tag):  # @avoidogu
    """Solve hCaptcha via CaptchaHeaven API using type=redeem."""  # @avoidogu
    raw = result.raw or {}  # @avoidogu
    sitekey  = raw.get("captcha_sitekey") or HCAPTCHA_SITEKEY  # @avoidogu
    rqdata   = raw.get("captcha_rqdata")  or ""  # @avoidogu
    rqtoken  = raw.get("captcha_rqtoken") or ""  # @avoidogu
    info("solving captcha via CaptchaHeaven (redeem)…", tag)  # @avoidogu
    client = _get_cap_client()  # @avoidogu
    solved = client._run_task({  # @avoidogu
        "type": "redeem",  # @avoidogu
        "captcha_sitekey": sitekey,  # @avoidogu
        "captcha_rqdata": rqdata,  # @avoidogu
        "captcha_rqtoken": rqtoken,  # @avoidogu
        "proxy": proxy or "",  # @avoidogu
    })  # @avoidogu
    captcha_key         = solved.get("x-captcha-key", "")  # @avoidogu
    captcha_rqtoken_out = solved.get("x-captcha-rqtoken", rqtoken)  # @avoidogu
    info("captcha solved", tag)  # @avoidogu
    return captcha_key, captcha_rqtoken_out  # @avoidogu
# @avoidogu
# @avoidogu
def try_redeem(redeemer, code, proxy, tag, acct_line):  # @avoidogu
    for attempt in range(1, MAX_RETRIES + 1):  # @avoidogu
        result = redeemer.redeem(code)  # @avoidogu
# @avoidogu
        if result.success:  # @avoidogu
            return True, "direct"  # @avoidogu
# @avoidogu
        if result.error_code in (50097, 50050):  # @avoidogu
            return False, f"{result.error_code}: account not eligible (previous Nitro or ineligible payment method)"  # @avoidogu
# @avoidogu
        if result.captcha_required:  # @avoidogu
            info("captcha…", tag)  # @avoidogu
            stat("captcha")  # @avoidogu
            try:  # @avoidogu
                captcha_key, captcha_rqtoken = solve_captcha(result, code, proxy, tag)  # @avoidogu
            except Exception as e:  # @avoidogu
                error(f"captcha error: {e}", tag)  # @avoidogu
                if attempt < MAX_RETRIES:  # @avoidogu
                    time.sleep(random.uniform(1, 3))  # @avoidogu
                    continue  # @avoidogu
                return False, f"captcha: {e}"  # @avoidogu
# @avoidogu
            raw = result.raw or {}  # @avoidogu
            session_id = raw.get("captcha_session_id")  # @avoidogu
            result2 = redeemer.redeem(code, captcha_key=captcha_key, captcha_rqtoken=captcha_rqtoken, captcha_session_id=session_id)  # @avoidogu
# @avoidogu
            if result2.success:  # @avoidogu
                return True, "captcha"  # @avoidogu
# @avoidogu
            if result2.error_code == 100029:  # @avoidogu
                payment_id = result2.raw.get("payment_id") if result2.raw else None  # @avoidogu
                if not payment_id:  # @avoidogu
                    return False, "100029 no payment_id"  # @avoidogu
                try:  # @avoidogu
                    with three_ds_lock:  # @avoidogu
                        ok = handle_3ds(redeemer, payment_id, proxy=proxy, tag=tag, rental_id=SMSBOT_RENTAL_ID or None)  # @avoidogu
                except Exception as e:  # @avoidogu
                    error(f"3DS error: {e}", tag)  # @avoidogu
                    if attempt < MAX_RETRIES:  # @avoidogu
                        time.sleep(random.uniform(2, 4))  # @avoidogu
                        continue  # @avoidogu
                    return False, f"3DS: {e}"  # @avoidogu
                if not ok:  # @avoidogu
                    if attempt < MAX_RETRIES:  # @avoidogu
                        time.sleep(random.uniform(2, 4))  # @avoidogu
                        continue  # @avoidogu
                    return False, "3DS failed"  # @avoidogu
# @avoidogu
                for post_attempt in range(1, MAX_RETRIES + 1):  # @avoidogu
                    result3 = redeemer.redeem(code)  # @avoidogu
                    if result3.success:  # @avoidogu
                        return True, "3DS"  # @avoidogu
                    if result3.captcha_required:  # @avoidogu
                        info("captcha after 3DS…", tag)  # @avoidogu
                        stat("captcha")  # @avoidogu
                        try:  # @avoidogu
                            captcha_key3, captcha_rqtoken3 = solve_captcha(result3, code, proxy, tag)  # @avoidogu
                        except Exception as e:  # @avoidogu
                            error(f"post-3DS captcha error: {e}", tag)  # @avoidogu
                            if post_attempt < MAX_RETRIES:  # @avoidogu
                                time.sleep(random.uniform(1, 3))  # @avoidogu
                                continue  # @avoidogu
                            return False, f"post-3DS captcha: {e}"  # @avoidogu
                        sid3 = result3.raw.get("captcha_session_id") if result3.raw else None  # @avoidogu
                        result4 = redeemer.redeem(code, captcha_key=captcha_key3, captcha_rqtoken=captcha_rqtoken3, captcha_session_id=sid3)  # @avoidogu
                        if result4.success:  # @avoidogu
                            return True, "3DS+captcha"  # @avoidogu
                        if result4.error_code == 100029:  # @avoidogu
                            warn("another 3DS after captcha, retrying…", tag)  # @avoidogu
                            pid2 = result4.raw.get("payment_id") if result4.raw else None  # @avoidogu
                            if pid2:  # @avoidogu
                                try:  # @avoidogu
                                    with three_ds_lock:  # @avoidogu
                                        handle_3ds(redeemer, pid2, proxy=proxy, tag=tag, rental_id=SMSBOT_RENTAL_ID or None)  # @avoidogu
                                except Exception:  # @avoidogu
                                    pass  # @avoidogu
                            if post_attempt < MAX_RETRIES:  # @avoidogu
                                continue  # @avoidogu
                            return False, "3DS loop"  # @avoidogu
                        error(f"post-3DS redeem: [{result4.error_code}] {result4.error_message}", tag)  # @avoidogu
                        return False, f"{result4.error_code}: {result4.error_message}"  # @avoidogu
                    else:  # @avoidogu
                        error(f"post-3DS redeem: [{result3.error_code}] {result3.error_message}", tag)  # @avoidogu
                        return False, f"{result3.error_code}: {result3.error_message}"  # @avoidogu
                return False, "post-3DS retries exhausted"  # @avoidogu
# @avoidogu
            if result2.captcha_required and attempt < MAX_RETRIES:  # @avoidogu
                warn("captcha flagged, retrying…", tag)  # @avoidogu
                time.sleep(random.uniform(1, 3))  # @avoidogu
                continue  # @avoidogu
# @avoidogu
            if result2.error_code in (50097, 50050):  # @avoidogu
                return False, f"{result2.error_code}: account not eligible (previous Nitro or ineligible payment method)"  # @avoidogu
            return False, f"{result2.error_code}: {result2.error_message}"  # @avoidogu
# @avoidogu
        if result.error_code == 50050:  # @avoidogu
            return False, "50050: account not eligible (already subscribed or card not qualifying)"  # @avoidogu
# @avoidogu
        if result.error_code == 429 and attempt < MAX_RETRIES:  # @avoidogu
            warn("rate limited, waiting…", tag)  # @avoidogu
            time.sleep(random.uniform(5, 10))  # @avoidogu
            continue  # @avoidogu
# @avoidogu
        return False, f"{result.error_code}: {result.error_message}"  # @avoidogu
# @avoidogu
    return False, "retries exhausted"  # @avoidogu
# @avoidogu
# @avoidogu
def worker(email: Optional[str], password: Optional[str], token: str, promos: list[str], proxy: Optional[str], proxy_pool: Optional['ProxyPool'] = None):  # @avoidogu
    tag = mask_token(token)  # @avoidogu
    acct_line = f"{email};{password}:{token}" if email else token  # @avoidogu
    start_counter = time.perf_counter()  # @avoidogu
# @avoidogu
    # --- Proxy validation: test up to 5 proxies, 10s each ---  # @avoidogu
    # Test the assigned proxy; rotate if dead  # @avoidogu
    MAX_PROXY_TRIES = 5  # @avoidogu
    for _ptry in range(MAX_PROXY_TRIES):  # @avoidogu
        if test_proxy(proxy, timeout=10):  # @avoidogu
            break  # @avoidogu
        warn(f"dead proxy ({_ptry+1}/{MAX_PROXY_TRIES}), trying next…", tag)  # @avoidogu
        if proxy:  # @avoidogu
            ProxyPool.delete_from_file(proxy)  # @avoidogu
        if proxy_pool:  # @avoidogu
            proxy = proxy_pool.reserve()  # @avoidogu
        else:  # @avoidogu
            proxy = None  # @avoidogu
        if not proxy:  # @avoidogu
            error("no live proxies available — running proxyless", tag)  # @avoidogu
            break  # @avoidogu
# @avoidogu
    redeemer = DiscordRedeemer(token=token, proxy=proxy)  # @avoidogu
    try:  # @avoidogu
        # Setup session: real timezone + Discord cookies (mirrors sexy v3)  # @avoidogu
        redeemer.setup_session()  # @avoidogu
        # Retry get_user up to 3 times — Discord sometimes gives transient errors  # @avoidogu
        user = None  # @avoidogu
        for _attempt in range(3):  # @avoidogu
            try:  # @avoidogu
                user = redeemer.get_user()  # @avoidogu
                break  # @avoidogu
            except Exception:  # @avoidogu
                if _attempt < 2:  # @avoidogu
                    time.sleep(random.uniform(2, 4))  # @avoidogu
        if not user:  # @avoidogu
            error("invalid token (3 attempts)", tag)  # @avoidogu
            stat("skipped")  # @avoidogu
            save("failed.txt", f"{acct_line} | invalid_token")  # @avoidogu
            remove_line("tokens.txt", token)  # @avoidogu
            return  # @avoidogu
        info("logged in", tag)  # @avoidogu
# @avoidogu
        if redeemer.has_had_nitro():  # @avoidogu
            error("previously had Nitro — ineligible for promo", tag)  # @avoidogu
            stat("skipped")  # @avoidogu
            save("failed.txt", f"{acct_line} | previous_nitro")  # @avoidogu
            return  # @avoidogu
# @avoidogu
        country = redeemer.get_country_code()  # @avoidogu
        sources = redeemer.get_payment_sources()  # @avoidogu
        if sources:  # @avoidogu
            redeemer.payment_source_id = sources[0]["id"]  # @avoidogu
            extra_info(f"payment {sources[0].get('brand')} ****{sources[0].get('last_4')}", tag)  # @avoidogu
        else:  # @avoidogu
            error("no payment source — skipping", tag)  # @avoidogu
            stat("skipped")  # @avoidogu
            return  # @avoidogu
# @avoidogu
        code = None  # @avoidogu
        with promo_lock:  # @avoidogu
            for c in promos:  # @avoidogu
                if c in used_promos:  # @avoidogu
                    continue  # @avoidogu
                try:  # @avoidogu
                    gift = redeemer.resolve_gift_code(c, country_code=country)  # @avoidogu
                except Exception as e:  # @avoidogu
                    error(f"resolve failed for {c[:8]}…: {e}", tag)  # @avoidogu
                    continue  # @avoidogu
                if gift.redeemed or gift.uses >= gift.max_uses:  # @avoidogu
                    warn(f"promo {c[:8]}… already used/exhausted", tag)  # @avoidogu
                    used_promos.add(c)  # @avoidogu
                    continue  # @avoidogu
                if gift.restricted_countries and country in gift.restricted_countries:  # @avoidogu
                    warn(f"promo {c[:8]}… restricted in {country}", tag)  # @avoidogu
                    continue  # @avoidogu
                code = c  # @avoidogu
                used_promos.add(c)  # @avoidogu
                break  # @avoidogu
# @avoidogu
        if not code:  # @avoidogu
            warn("no available promo — keeping token for next run", tag)  # @avoidogu
            # Don't touch the token file — token stays for next session  # @avoidogu
            return  # @avoidogu
# @avoidogu
        info("using promo", tag, promo=code[:8])  # @avoidogu
# @avoidogu
        redeemed_ok, reason = try_redeem(redeemer, code, proxy, tag, acct_line)  # @avoidogu
        elapsed = f"{time.perf_counter() - start_counter:.2f}s"  # @avoidogu
# @avoidogu
        if redeemed_ok:  # @avoidogu
            success("redeemed", tag, promo=code[:8], reason=reason, t=elapsed)  # @avoidogu
            stat("redeemed")  # @avoidogu
            save("redeemed.txt", f"{acct_line} | {code}")  # @avoidogu
            remove_line("promos.txt", code)  # @avoidogu
            remove_line("tokens.txt", token)  # @avoidogu
        else:  # @avoidogu
            error("failed", tag, promo=code[:8], reason=reason, t=elapsed)  # @avoidogu
            stat("failed")  # @avoidogu
            save("failed.txt", f"{acct_line} | {code} | {reason}")  # @avoidogu
            # Release the promo so another token can try it  # @avoidogu
            with promo_lock:  # @avoidogu
                used_promos.discard(code)  # @avoidogu
# @avoidogu
    except Exception as e:  # @avoidogu
        error(f"error: {e}", tag)  # @avoidogu
    finally:  # @avoidogu
        redeemer.close()  # @avoidogu
        # Delete used proxy from file so it's never reused  # @avoidogu
        if proxy:  # @avoidogu
            ProxyPool.delete_from_file(proxy)  # @avoidogu
            extra_info("proxy removed from pool", tag)  # @avoidogu
# @avoidogu
# @avoidogu
def main():  # @avoidogu
    os.system("cls" if os.name == "nt" else "clear")  # @avoidogu
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":  # @avoidogu
        sys.stdout.reconfigure(encoding="utf-8")  # @avoidogu
    print(f"""
{P}  ╔══════════════════════════════════════════════════╗
  ║   ∫  Discord Promo Redeemer By @avoidogu  ∂        ║
  ╚══════════════════════════════════════════════════╝{R}
""")  # @avoidogu
# @avoidogu
    while True:  # @avoidogu
        # --- Reload files each session ---  # @avoidogu
        tokens = load_tokens()  # @avoidogu
        promos = load_promos()  # @avoidogu
        proxies = load_proxies()  # @avoidogu
# @avoidogu
        if not tokens:  # @avoidogu
            error("no tokens in in/tokens.txt")  # @avoidogu
            input(f"\n{W}[{P}>{W}] Press Enter to reload…{R}")  # @avoidogu
            continue  # @avoidogu
        if not promos:  # @avoidogu
            error("no promos in in/promos.txt")  # @avoidogu
            input(f"\n{W}[{P}>{W}] Press Enter to reload…{R}")  # @avoidogu
            continue  # @avoidogu
# @avoidogu
        tokens_with_proxy = sum(1 for _, _, _, p in tokens if p)  # @avoidogu
        info(f"loaded {P}{len(tokens)}{W} tokens ({P}{tokens_with_proxy}{W} with built-in proxy), {P}{len(promos)}{W} promos, {P}{len(proxies)}{W} proxies")  # @avoidogu
# @avoidogu
        # --- Ask for thread count ---  # @avoidogu
        while True:  # @avoidogu
            try:  # @avoidogu
                thread_input = input(f"{W}[{P}>{W}] Threads: {R}").strip()  # @avoidogu
                num_threads = int(thread_input)  # @avoidogu
                if num_threads < 1:  # @avoidogu
                    raise ValueError  # @avoidogu
                break  # @avoidogu
            except (ValueError, EOFError):  # @avoidogu
                error("Enter a valid number")  # @avoidogu
# @avoidogu
        info(f"starting with {P}{num_threads}{R} threads")  # @avoidogu
        print()  # @avoidogu
# @avoidogu
        # --- Reset session state ---  # @avoidogu
        used_promos.clear()  # @avoidogu
        with stats_lock:  # @avoidogu
            stats["redeemed"] = 0  # @avoidogu
            stats["failed"] = 0  # @avoidogu
            stats["skipped"] = 0  # @avoidogu
            stats["captcha"] = 0  # @avoidogu
        global SESSION_START  # @avoidogu
        SESSION_START = time.time()  # @avoidogu
# @avoidogu
        # --- Launch workers ---  # @avoidogu
        proxy_pool = ProxyPool(proxies)  # @avoidogu
        threads = []  # @avoidogu
        for i, (email, password, token, token_proxy) in enumerate(tokens):  # @avoidogu
            # Token with built-in proxy uses its own; otherwise reserve a unique one from pool  # @avoidogu
            if token_proxy:  # @avoidogu
                proxy = token_proxy  # @avoidogu
            else:  # @avoidogu
                proxy = proxy_pool.reserve()  # @avoidogu
                if not proxy:  # @avoidogu
                    error(f"no proxies left for token {i+1}")  # @avoidogu
# @avoidogu
            while len([t for t in threads if t.is_alive()]) >= num_threads:  # @avoidogu
                time.sleep(0.3)  # @avoidogu
# @avoidogu
            t = threading.Thread(target=worker, args=(email, password, token, promos, proxy, proxy_pool))  # @avoidogu
            t.start()  # @avoidogu
            threads.append(t)  # @avoidogu
            time.sleep(random.uniform(0.3, 0.8))  # @avoidogu
# @avoidogu
        for t in threads:  # @avoidogu
            t.join()  # @avoidogu
# @avoidogu
        print()  # @avoidogu
        info(f"done — {stats_line()}")  # @avoidogu
        input(f"\n{W}[{P}>{W}] Press Enter to restart…{R}")  # @avoidogu
        print()  # @avoidogu
# @avoidogu
# @avoidogu
if __name__ == "__main__":  # @avoidogu
    main()  # @avoidogu
