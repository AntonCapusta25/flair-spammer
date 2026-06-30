#!/usr/bin/python
# -*- coding: UTF-8 -*-
import subprocess
try:
    from os import system, name
    import sys, os, json, random, time, asyncio, pyfade, discord, aiohttp, webbrowser, socket
    from aiohttp import web
    from datetime import datetime
    from discord.ext import commands
    from colorama import Fore, init, Style; init()
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", '-r', 'requirements.txt'])
    from os import system, name
    import sys, os, json, random, time, asyncio, pyfade, discord, aiohttp, webbrowser, socket
    from aiohttp import web
    from datetime import datetime
    from discord.ext import commands
    from colorama import Fore, init, Style; init()

sys.tracebacklimit = 0

class Config:
    def __init__(self):
        self.load_config()
        
    def load_config(self):
        try:
            with open("./config.json", "r") as f:
                config = json.load(f)
                self.minimum_dm = config.get("minimum_dm_delay", 1)
                self.maximum_dm = config.get("maximum_dm_delay", 3)
                # Token loaded from config as fallback, but tokens.txt preferred now
                self.token = config.get("token", "")
                self.skip_booting = config.get("skip_booting", False)
                self.skip_disclaimer = config.get("skip_disclaimer", False)
                self.min_ban = config.get("minimum_ban_delay", 1)
                self.max_ban = config.get("maximum_ban_delay", 3)
                self.min_general = config.get("minimum_general_delay", 0.5)
                self.max_general = config.get("maximum_general_delay", 1.5)
                self.captcha_api_key = config.get("captcha_api_key", "")
                self.captcha_service = config.get("captcha_service", "2captcha" if self.captcha_api_key else "manual")
                self.x_super_properties = config.get("x_super_properties", "")
        except Exception as e:
            print(f"{Fore.RED}Error loading config: {e}")
            sys.exit(1)

config = Config()

def random_cooldown(minimum, maximum):
    return random.uniform(minimum, maximum)

async def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

async def show_disclaimer():
    if not config.skip_disclaimer:
        messages = [
            f"{Fore.LIGHTWHITE_EX}{Style.BRIGHT}DISCLAIMER:",
            f"{Style.RESET_ALL}{Fore.LIGHTWHITE_EX}User automation and spamming are {Fore.LIGHTYELLOW_EX}{Style.BRIGHT}against Discord's TOS!!{Style.RESET_ALL}{Fore.RESET}",
            f"{Fore.LIGHTWHITE_EX}Use this tool only for educational purposes and at your own risk",
            f"{Fore.LIGHTWHITE_EX}Ask the server owner if you're allowed to use this tool",
            f"{Fore.LIGHTGREEN_EX}{Style.BRIGHT}Mass Dm {Style.RESET_ALL}{Fore.RESET}{Fore.LIGHTWHITE_EX}requires {Fore.LIGHTGREEN_EX}{Style.BRIGHT}Privileged Member Intents{Style.RESET_ALL}",
            f"{Fore.LIGHTWHITE_EX}This tool may get your account banned if used improperly"
        ]
        
        for idx, msg in enumerate(messages):
            print(msg)
            await asyncio.sleep(0.8 if idx < len(messages) - 1 else 0)

async def show_boot_animation():
    if not config.skip_booting:
        stages = [
            f"{Style.BRIGHT}{Fore.LIGHTWHITE_EX}Booting {Fore.RED}Karuma {Fore.RESET}{Fore.LIGHTWHITE_EX}Tool",
            f"{Fore.RED}25%",
            f"{Fore.YELLOW}50%",
            f"{Fore.LIGHTYELLOW_EX}75%",
            f"{Fore.LIGHTGREEN_EX}99%",
            f"{Fore.LIGHTBLUE_EX}Karuma Tool ready"
        ]
        
        delays = [0.3, 0.5, 0.6, 0.7, 1, 1]
        
        for stage, delay in zip(stages, delays):
            print(stage)
            await asyncio.sleep(delay)

class KarumaBot(discord.Client):
    def __init__(self, proxy=None, *args, **kwargs):
        super().__init__(proxy=proxy, *args, **kwargs)
        
    async def login(self, token: str) -> None:
        await super().login(token)
        if config.x_super_properties:
            import base64
            try:
                decoded = base64.b64decode(config.x_super_properties).decode('utf-8')
                props = json.loads(decoded)
                self.http.headers.super_properties.update(props)
                self.http.headers.encoded_super_properties = config.x_super_properties
                if 'user_agent' in self.http.headers.__dict__:
                    del self.http.headers.__dict__['user_agent']
                if 'client_hints' in self.http.headers.__dict__:
                    del self.http.headers.__dict__['client_hints']
                if 'os' in props:
                    self.http.headers.platform = props['os']
                if 'browser_version' in props:
                    try:
                        self.http.headers.major_version = int(props['browser_version'].split('.')[0])
                    except:
                        pass
                print(f"{Fore.LIGHTGREEN_EX}Successfully applied custom X-Super-Properties from config.json")
            except Exception as e:
                print(f"{Fore.RED}Failed to apply custom X-Super-Properties: {e}")

        
    async def on_ready(self):
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="github.com/hoemotion"
            ),
            status=discord.Status.idle
        )
        print(f"{Fore.LIGHTGREEN_EX}Ready: {self.user}")

    async def get_guild_by_id(self, guild_id):
        return discord.utils.get(self.guilds, id=guild_id)

    async def handle_captcha(self, exception: discord.CaptchaRequired) -> str:
        # Calls the standalone captcha solver to return the solution string.
        # This allows discord.py-self to internally retry standard requests with headers.
        try:
            if config.captcha_service == "manual":
                return await captcha_server.solve(exception, str(self.user))
            elif config.captcha_service == "nopecha":
                return await solve_captcha_nopecha(self, exception)
            else:
                return await solve_captcha_2captcha(self, exception)
        except Exception as e:
            print(f"{Fore.RED}Internal Captcha solve failed: {e}")
            raise exception

class GlobalCaptchaServer:
    def __init__(self):
        self.port = 5050
        self.captcha_req = None
        self.token_future = None
        self.runner = None
        self.site = None

    async def start(self):
        # Find a free port starting at 5050
        for p in range(5050, 5100):
            try:
                app = web.Application()
                app.router.add_options('/poll', self.handle_options)
                app.router.add_get('/poll', self.handle_poll)
                app.router.add_options('/submit', self.handle_options)
                app.router.add_post('/submit', self.handle_submit)
                
                self.runner = web.AppRunner(app)
                await self.runner.setup()
                self.site = web.TCPSite(self.runner, '127.0.0.1', p)
                await self.site.start()
                self.port = p
                print(f"{Fore.LIGHTGREEN_EX}[*] Background Captcha Server started on http://127.0.0.1:{self.port}")
                break
            except Exception:
                continue
        else:
            print(f"{Fore.RED}[!] Failed to start background captcha server.")

    async def handle_options(self, request):
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        }
        return web.Response(headers=headers)

    async def handle_poll(self, request):
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        }
        if self.captcha_req:
            return web.json_response(self.captcha_req, headers=headers)
        return web.json_response({"status": "idle"}, headers=headers)

    async def handle_submit(self, request):
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        }
        try:
            data = await request.json()
            token = data.get("token")
            if token:
                if self.token_future and not self.token_future.done():
                    self.token_future.set_result(token)
                self.captcha_req = None
                return web.Response(text="OK", headers=headers)
            return web.Response(text="Missing token", status=400, headers=headers)
        except Exception as e:
            return web.Response(text=str(e), status=400, headers=headers)

    async def solve(self, exception: discord.CaptchaRequired, client_username: str) -> str:
        self.token_future = asyncio.get_running_loop().create_future()
        self.captcha_req = {
            "status": "need_solve",
            "service": exception.service.lower(),
            "sitekey": exception.sitekey,
            "rqdata": getattr(exception, 'rqdata', '') or '',
            "username": client_username
        }
        
        print(f"\n{Fore.LIGHTRED_EX}[!] Captcha Required for {client_username}! Service: {exception.service}")
        print(f"{Fore.LIGHTYELLOW_EX}Please solve it in your browser tab connected to the Karuma Solver.")
        
        # Open Discord automatically
        try:
            webbrowser.open("https://discord.com/channels/@me")
        except:
            pass
            
        try:
            # Wait up to 5 minutes
            token = await asyncio.wait_for(self.token_future, timeout=300)
            print(f"{Fore.LIGHTGREEN_EX}Captcha solved successfully via browser!")
            return token
        except asyncio.TimeoutError:
            self.captcha_req = None
            raise Exception("Captcha manual solve timed out")

captcha_server = GlobalCaptchaServer()

def print_manual_instructions(port):
    js_code = """(async function(){const s=document.createElement('style');s.innerHTML=`#karuma-solver-overlay{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.85);z-index:999999;display:flex;justify-content:center;align-items:center;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;color:#fff}.karuma-solver-box{background:#2f3136;padding:40px;border-radius:12px;box-shadow:0 8px 24px rgba(0,0,0,0.5);text-align:center;max-width:400px;width:90%}.karuma-solver-box h2{margin-top:0;margin-bottom:10px;font-size:22px}.karuma-solver-box p{color:#b9bbbe;font-size:14px;margin-bottom:25px}.karuma-solver-status{margin-top:25px;color:#00b0f4;font-weight:bold}`;document.head.appendChild(s);if(!window.hcaptcha&&!document.querySelector('script[src*="hcaptcha.com"]')){const hc=document.createElement('script');hc.src='https://js.hcaptcha.com/1/api.js';hc.async=true;hc.defer=true;document.head.appendChild(hc)}if(!window.grecaptcha&&!document.querySelector('script[src*="recaptcha"]')){const rc=document.createElement('script');rc.src='https://www.google.com/recaptcha/api.js';rc.async=true;rc.defer=true;document.head.appendChild(rc)}let active=null;async function poll(){try{const r=await fetch('http://127.0.0.1:{{port}}/poll');if(!r.ok)return;const d=await r.json();if(d.status==='need_solve'&&!active){active=d;const o=document.createElement('div');o.id='karuma-solver-overlay';o.innerHTML=`<div class="karuma-solver-box"><h2>Karuma Captcha Required</h2><p>Please solve the verification below to continue messaging.</p><div id="karuma-captcha-container"></div><div class="karuma-solver-status" id="karuma-status">Waiting for verification...</div></div>`;document.body.appendChild(o);function solve(t){document.getElementById('karuma-status').innerText="Submitting token...";document.getElementById('karuma-status').style.color='#43b581';fetch('http://127.0.0.1:{{port}}/submit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token:t})}).then(res=>{if(res.ok){document.getElementById('karuma-status').innerText="Solved! Closing overlay...";setTimeout(()=>{o.remove();active=null},1500)}else{document.getElementById('karuma-status').innerText="Submission failed. Try again.";document.getElementById('karuma-status').style.color='#f04747';active=null}}).catch(err=>{document.getElementById('karuma-status').innerText="Connection error.";document.getElementById('karuma-status').style.color='#f04747';active=null})}setTimeout(()=>{if(d.service==='hcaptcha'){if(window.hcaptcha){var opts={sitekey:d.sitekey,theme:'dark',callback:solve};if(d.rqdata)opts.data=d.rqdata;hcaptcha.render('karuma-captcha-container',opts)}else{o.remove();active=null}}else{if(window.grecaptcha){grecaptcha.render('karuma-captcha-container',{sitekey:d.sitekey,theme:'dark',callback:solve})}else{o.remove();active=null}}window.focus()},1000)}}catch(e){}}setInterval(poll,2000);console.log("Karuma Solver active!");})();""".replace("{{port}}", str(port))

    print(f"\n{Fore.LIGHTCYAN_EX}==================================================================")
    print(f"{Fore.LIGHTWHITE_EX}{Style.BRIGHT}MANUAL CAPTCHA SOLVER SETUP (NON-HEADLESS)")
    print(f"{Fore.LIGHTCYAN_EX}==================================================================")
    print(f"{Fore.LIGHTWHITE_EX}To solve captchas, please link your web browser:")
    print(f"1. Open your browser and log into: {Fore.LIGHTBLUE_EX}https://discord.com/channels/@me")
    print(f"{Fore.LIGHTWHITE_EX}2. Open Developer Console ({Fore.YELLOW}F12{Fore.LIGHTWHITE_EX} or {Fore.YELLOW}Cmd+Option+I{Fore.LIGHTWHITE_EX} -> Console tab)")
    print(f"{Fore.LIGHTWHITE_EX}3. Paste the following JavaScript code and press Enter:")
    print(f"\n{Fore.YELLOW}{js_code}\n")
    print(f"{Fore.LIGHTCYAN_EX}==================================================================\n")

async def solve_captcha_2captcha(client: 'KarumaBot', exception: discord.CaptchaRequired) -> str:
    """Standalone captcha solver called directly by the DM loop."""
    print(f"{Fore.LIGHTRED_EX}[!] Captcha Required for {client.user}! Service: {exception.service}")
    
    if not config.captcha_api_key:
        raise Exception("No captcha_api_key set in config.json!")
    
    method = exception.service.lower()
    if "hcaptcha" in method:
        method = "hcaptcha"
    elif "recaptcha" in method:
        method = "userrecaptcha"
    else:
        raise Exception(f"Unsupported captcha service: {exception.service}")
        
    print(f"{Fore.LIGHTYELLOW_EX}Sending Captcha to 2Captcha...")
    async with aiohttp.ClientSession() as session:
        in_url = "https://2captcha.com/in.php"
        payload = {
            "key": config.captcha_api_key,
            "method": method,
            "pageurl": "https://discord.com/channels/@me",
            "json": 1
        }
        
        if method == "hcaptcha":
            payload["sitekey"] = exception.sitekey
        else:
            payload["googlekey"] = exception.sitekey
        
        try:
            payload["useragent"] = client.http.user_agent
            payload["userAgent"] = client.http.user_agent
        except:
            pass
        
        rqdata = getattr(exception, 'rqdata', None)
        if rqdata:
            payload["data"] = rqdata
            payload["enterprise"] = 1
        
        if getattr(exception, 'should_serve_invisible', False):
            payload["invisible"] = 1
        else:
            payload["invisible"] = 0
        
        # Extract proxy configuration from the client if configured
        bot_proxy = getattr(client.http, 'proxy', None)
        if bot_proxy and isinstance(bot_proxy, str):
            from urllib.parse import urlparse
            try:
                parsed = urlparse(bot_proxy)
                # Parse proxyType
                ptype = parsed.scheme if parsed.scheme in ["http", "https", "socks4", "socks5"] else "http"
                payload["proxyType"] = ptype.upper()
                payload["proxytype"] = ptype.upper()
                
                # Format proxy string for 2Captcha: login:password@IP:port
                proxy_str = ""
                if parsed.username and parsed.password:
                    proxy_str += f"{parsed.username}:{parsed.password}@"
                if parsed.hostname:
                    proxy_str += parsed.hostname
                if parsed.port:
                    proxy_str += f":{parsed.port}"
                payload["proxy"] = proxy_str
                print(f"{Fore.LIGHTYELLOW_EX}Passing proxy configuration to 2Captcha: {proxy_str} (Type: {ptype.upper()})")
            except Exception as pe:
                print(f"{Fore.RED}Failed to parse proxy details for 2Captcha: {pe}")
        else:
            print(f"{Fore.RED}[WARNING] No proxy configured for this bot client!")
            print(f"{Fore.RED}[WARNING] hCaptcha Enterprise often enforces IP matching. Without proxies, solving via 2Captcha may result in an infinite loop.")
            print(f"{Fore.RED}[WARNING] We highly recommend configuring residential proxies in proxies.txt.")
            
        async with session.post(in_url, data=payload) as resp:
            try:
                res = await resp.json(content_type=None)
            except Exception as je:
                raw_text = await resp.text()
                raise Exception(f"Failed to parse 2Captcha response as JSON: {raw_text[:200]} (error: {je})")
            if res.get("status") != 1:
                raise Exception(f"2Captcha API error: {res.get('request')}")
            req_id = res["request"]
        
        print(f"{Fore.LIGHTYELLOW_EX}Captcha task ID {req_id} queued. Waiting for solution...")
        
        res_url = "https://2captcha.com/res.php"
        for i in range(60):
            await asyncio.sleep(5)
            params = {"key": config.captcha_api_key, "action": "get", "id": req_id, "json": 1}
            async with session.get(res_url, params=params) as resp:
                try:
                    result = await resp.json(content_type=None)
                except Exception as je:
                    raw_text = await resp.text()
                    # Handle case where json=1 is ignored or transient server HTML error
                    if "CAPCHA_NOT_READY" in raw_text:
                        if i % 3 == 0:
                            print(f"{Fore.YELLOW}Still solving... elapsed {i*5}s")
                        continue
                    if "OK|" in raw_text:
                        print(f"{Fore.LIGHTGREEN_EX}Captcha solved successfully (plaintext fallback)!")
                        return raw_text.split("|")[1]
                    print(f"{Fore.YELLOW}Warning: 2Captcha returned non-JSON response: {raw_text[:100]}... (error: {je})")
                    continue
                
                if result.get("status") == 1:
                    print(f"{Fore.LIGHTGREEN_EX}Captcha solved successfully!")
                    return result["request"]
                if result.get("request") != "CAPCHA_NOT_READY":
                    raise Exception(f"2Captcha solve error: {result.get('request')}")
                if i % 3 == 0:
                    print(f"{Fore.YELLOW}Still solving... elapsed {i*5}s")
        
        raise Exception("Captcha solving timed out after 300 seconds")

async def solve_captcha_nopecha(client: 'KarumaBot', exception: discord.CaptchaRequired) -> str:
    """Standalone captcha solver using Nopecha Token API."""
    print(f"{Fore.LIGHTRED_EX}[!] Captcha Required for {client.user}! Service: {exception.service}")
    
    if not config.captcha_api_key:
        raise Exception("No captcha_api_key set in config.json!")
        
    print(f"{Fore.LIGHTYELLOW_EX}Sending Captcha to Nopecha...")
    async with aiohttp.ClientSession() as session:
        url = "https://api.nopecha.com/token/"
        payload = {
            "key": config.captcha_api_key,
            "type": "hcaptcha" if exception.service.lower() == "hcaptcha" else exception.service.lower(),
            "sitekey": exception.sitekey,
            "url": "https://discord.com/channels/@me"
        }
        
        # Pass useragent/userAgent if available
        try:
            user_agent = getattr(client.http, 'user_agent', None)
            if user_agent:
                payload["useragent"] = user_agent
                payload["userAgent"] = user_agent
        except:
            pass
            
        # Pass rqdata if available
        rqdata = getattr(exception, 'rqdata', None)
        if rqdata:
            payload["data"] = {
                "rqdata": rqdata
            }
            
        # Extract proxy configuration from the client if configured
        bot_proxy = getattr(client.http, 'proxy', None)
        if bot_proxy and isinstance(bot_proxy, str):
            from urllib.parse import urlparse
            try:
                parsed = urlparse(bot_proxy)
                scheme = parsed.scheme.lower() if parsed.scheme in ["http", "https", "socks4", "socks5"] else "http"
                proxy_obj = {
                    "scheme": scheme,
                    "address": parsed.hostname or "",
                    "port": int(parsed.port) if parsed.port else (80 if scheme in ["http", "https"] else 1080)
                }
                if parsed.username:
                    proxy_obj["username"] = parsed.username
                if parsed.password:
                    proxy_obj["password"] = parsed.password
                payload["proxy"] = proxy_obj
                print(f"{Fore.LIGHTYELLOW_EX}Passing proxy configuration to Nopecha: {parsed.hostname}:{parsed.port or (80 if scheme in ['http', 'https'] else 1080)}")
            except Exception as pe:
                print(f"{Fore.RED}Failed to parse proxy details for Nopecha: {pe}")
        else:
            print(f"{Fore.RED}[WARNING] No proxy configured for this bot client!")
            print(f"{Fore.RED}[WARNING] hCaptcha Enterprise often enforces IP matching. Without proxies, solving via Nopecha may result in an infinite loop.")
            print(f"{Fore.RED}[WARNING] We highly recommend configuring residential proxies in proxies.txt.")
            
        async with session.post(url, json=payload) as resp:
            try:
                res = await resp.json()
            except Exception as je:
                raw_text = await resp.text()
                raise Exception(f"Failed to parse Nopecha response as JSON: {raw_text[:200]} (error: {je})")
            
            if "error" in res:
                raise Exception(f"Nopecha API error: {res.get('error')}")
            
            job_id = res.get("data")
            if not job_id:
                raise Exception(f"Nopecha response missing job ID: {res}")
                
        print(f"{Fore.LIGHTYELLOW_EX}Nopecha task ID {job_id} queued. Waiting for solution...")
        
        for i in range(60):
            await asyncio.sleep(2)
            poll_url = f"https://api.nopecha.com/token/?key={config.captcha_api_key}&id={job_id}"
            async with session.get(poll_url) as resp:
                try:
                    result = await resp.json()
                except Exception as je:
                    raw_text = await resp.text()
                    continue
                
                if "data" in result:
                    print(f"{Fore.LIGHTGREEN_EX}Captcha solved successfully via Nopecha!")
                    return result["data"]
                
                if result.get("code") == 14: # Incomplete job
                    if i % 5 == 0:
                        print(f"{Fore.YELLOW}Still solving via Nopecha... elapsed {i*2}s")
                    continue
                else:
                    raise Exception(f"Nopecha solve error: {result.get('message', result)}")
                    
        raise Exception("Captcha solving via Nopecha timed out after 120 seconds")

async def check_permissions_and_confirm(client, guild, required_perms, action_name):
    bot_member = guild.get_member(client.user.id)
    missing_perms = [perm for perm, value in required_perms.items() if not getattr(bot_member.guild_permissions, perm)]
    
    if missing_perms:
        print(f"{Fore.YELLOW}Warning: Missing permissions for {action_name} on client {client.user}:")
        for perm in missing_perms:
            print(f"- {perm.replace('_', ' ').title()}")
        
        confirm = input(f"{Fore.LIGHTYELLOW_EX}Continue without {action_name}? (yes/no): ").lower()
        if confirm != "yes":
            return False, missing_perms
        return True, missing_perms
    return True, []

async def nuke_server(client, guild_id=None):
    if not guild_id:
        while True:
            try:
                guild_id = int(input(f'{Fore.LIGHTYELLOW_EX}Enter server ID: '))
                break
            except ValueError:
                print(f'{Fore.RED}Invalid ID')
                
    guild = await client.get_guild_by_id(guild_id)
    if not guild:
        print(f"{Fore.RED}Server not found")
        return
        
    bot_member = guild.get_member(client.user.id)
    reason = input("Ban reason (optional): ")
    
    action_groups = {
        "ban_members": {"name": "banning members", "perms": {"ban_members": True}, "func": ban_members, "args": (client, guild, bot_member, reason)},
        "manage_channels": {"name": "deleting channels", "perms": {"manage_channels": True}, "func": delete_channels, "args": (guild,)},
        "manage_roles": {"name": "deleting roles", "perms": {"manage_roles": True}, "func": delete_roles, "args": (guild, bot_member)},
        "manage_emojis": {"name": "deleting emojis", "perms": {"manage_emojis": True}, "func": delete_emojis, "args": (guild,)},
        "manage_emojis_and_stickers": {"name": "deleting stickers", "perms": {"manage_emojis": True}, "func": delete_stickers, "args": (guild,)}
    }
    
    for action in action_groups.values():
        proceed, missing = await check_permissions_and_confirm(client, guild, action["perms"], action["name"])
        if proceed and not missing:
            await action["func"](*action["args"])
    
    print(f"{Fore.LIGHTGREEN_EX}Nuke operations completed")
    input("Press Enter to continue")

async def ban_members(client, guild, bot_member, reason):
    members = [m for m in guild.members if m != client.user and m.top_role < bot_member.top_role]
    total = len(members)
    for idx, member in enumerate(members, 1):
        try:
            await member.ban(reason=reason, delete_message_days=7)
            print(f"{Fore.LIGHTGREEN_EX}[{idx}/{total}] Banned {Fore.YELLOW}{member}")
        except Exception as e:
            print(f"{Fore.RED}[{idx}/{total}] Failed to ban {Fore.YELLOW}{member}: {e}")
        if idx < total:
            await asyncio.sleep(random_cooldown(config.min_ban, config.max_ban))

async def delete_channels(guild):
    for channel in guild.channels:
        try:
            await channel.delete()
            print(f"{Fore.LIGHTGREEN_EX}Deleted channel: {Fore.YELLOW}{channel.name}")
        except Exception as e:
            print(f"{Fore.RED}Failed to delete channel {Fore.YELLOW}{channel.name}: {e}")
        await asyncio.sleep(random_cooldown(config.min_general, config.max_general))

async def delete_roles(guild, bot_member):
    for role in guild.roles:
        if role.name != "@everyone" and role.position < bot_member.top_role.position:
            try:
                await role.delete()
                print(f"{Fore.LIGHTGREEN_EX}Deleted role: {Fore.YELLOW}{role.name}")
            except Exception as e:
                print(f"{Fore.RED}Failed to delete role {Fore.YELLOW}{role.name}: {e}")
            await asyncio.sleep(random_cooldown(config.min_general, config.max_general))

async def delete_emojis(guild):
    emojis = await guild.fetch_emojis()
    if not emojis: return
    for emoji in emojis:
        try:
            await emoji.delete()
            print(f"{Fore.LIGHTGREEN_EX}Deleted emoji: {Fore.YELLOW}{emoji.name}")
        except Exception as e:
            print(f"{Fore.RED}Failed to delete emoji {Fore.YELLOW}{emoji.name}: {e}")
        await asyncio.sleep(random_cooldown(config.min_general, config.max_general))

async def delete_stickers(guild):
    stickers = await guild.fetch_stickers()
    if not stickers: return
    for sticker in stickers:
        try:
            await sticker.delete()
            print(f"{Fore.LIGHTGREEN_EX}Deleted sticker: {Fore.YELLOW}{sticker.name}")
        except Exception as e:
            print(f"{Fore.RED}Failed to delete sticker {Fore.YELLOW}{sticker.name}: {e}")
        await asyncio.sleep(random_cooldown(config.min_general, config.max_general))

async def raid_server(client, guild_id=None):
    if not guild_id:
        while True:
            try:
                guild_id = int(input(f'{Fore.LIGHTYELLOW_EX}Enter server ID: '))
                break
            except ValueError:
                print(f'{Fore.RED}Invalid ID')
                
    guild = await client.get_guild_by_id(guild_id)
    if not guild:
        print(f"{Fore.RED}Server not found")
        return
        
    bot_member = guild.get_member(client.user.id)
    
    action_groups = {
        "rename_server": {"name": "renaming server", "perms": {"manage_guild": True}, "func": rename_server, "args": (guild,)},
        "create_channels": {"name": "creating channels", "perms": {"manage_channels": True}, "func": create_channels, "args": (guild,)},
        "create_roles": {"name": "creating roles", "perms": {"manage_roles": True}, "func": create_roles, "args": (guild,)},
        "change_nicks": {"name": "changing nicknames", "perms": {"manage_nicknames": True}, "func": change_nicknames, "args": (client, guild, bot_member)}
    }
    
    new_name = input("New server name (leave blank to skip): ")
    channel_name = input("Channel name to spam: ")
    channel_count = int(input("Number of channels to create (0 to skip): "))
    role_name = input("Role name to spam: ")
    role_count = int(input("Number of roles to create (0 to skip): "))
    nickname = input("Nickname to set (leave blank to skip): ")
    
    action_groups["rename_server"]["args"] = (guild, new_name) if new_name else None
    action_groups["create_channels"]["args"] = (guild, channel_name, channel_count) if channel_count > 0 else None
    action_groups["create_roles"]["args"] = (guild, role_name, role_count) if role_count > 0 else None
    action_groups["change_nicks"]["args"] = (client, guild, bot_member, nickname) if nickname else None
    
    for action in action_groups.values():
        if action["args"] is None: continue
        proceed, missing = await check_permissions_and_confirm(client, guild, action["perms"], action["name"])
        if proceed and not missing:
            await action["func"](*action["args"])
    
    print(f"{Fore.LIGHTGREEN_EX}Raid operations completed")
    input("Press Enter to continue")

async def rename_server(guild, new_name):
    try:
        await guild.edit(name=new_name)
        print(f"{Fore.LIGHTGREEN_EX}Server renamed to {Fore.YELLOW}{new_name}")
    except Exception as e:
        print(f"{Fore.RED}Failed to rename server: {e}")

async def create_channels(guild, channel_name, count):
    for i in range(count):
        try:
            await guild.create_text_channel(f"{channel_name}-{i+1}")
            print(f"{Fore.LIGHTGREEN_EX}Created channel {Fore.YELLOW}{channel_name}-{i+1}")
        except Exception as e:
            print(f"{Fore.RED}Failed to create channel: {e}")
        await asyncio.sleep(random_cooldown(config.min_general, config.max_general))

async def create_roles(guild, role_name, count):
    for i in range(count):
        try:
            await guild.create_role(name=f"{role_name}-{i+1}")
            print(f"{Fore.LIGHTGREEN_EX}Created role {Fore.YELLOW}{role_name}-{i+1}")
        except Exception as e:
            print(f"{Fore.RED}Failed to create role: {e}")
        await asyncio.sleep(random_cooldown(config.min_general, config.max_general))

async def change_nicknames(client, guild, bot_member, nickname):
    members = [m for m in guild.members if m != client.user and m.top_role < bot_member.top_role]
    for member in members:
        try:
            await member.edit(nick=nickname)
            print(f"{Fore.LIGHTGREEN_EX}Changed nickname for {Fore.YELLOW}{member}")
        except Exception as e:
            print(f"{Fore.RED}Failed to change nickname for {Fore.YELLOW}{member}: {e}")
        await asyncio.sleep(random_cooldown(config.min_general, config.max_general))

async def create_embed():
    embed = discord.Embed()
    title = input(f"{Fore.LIGHTGREEN_EX}Embed title (leave blank for none): ")
    if title: embed.title = title
    description = input(f"{Fore.LIGHTGREEN_EX}Embed description (leave blank for none): ")
    if description: embed.description = description
    color = input(f"{Fore.LIGHTGREEN_EX}Embed color (hex without #, e.g., FF0000 for red): ")
    if color:
        try: embed.color = int(color, 16)
        except: embed.color = discord.Color.random()
    while True:
        field_name = input(f"{Fore.LIGHTGREEN_EX}Add field? Enter name (leave blank to stop): ")
        if not field_name: break
        field_value = input(f"{Fore.LIGHTGREEN_EX}Field value: ")
        inline = input(f"{Fore.LIGHTGREEN_EX}Inline field? (y/n): ").lower() == 'y'
        embed.add_field(name=field_name, value=field_value, inline=inline)
    author_name = input(f"{Fore.LIGHTGREEN_EX}Author name (leave blank for none): ")
    if author_name:
        author_icon = input(f"{Fore.LIGHTGREEN_EX}Author icon URL (leave blank for none): ")
        embed.set_author(name=author_name, icon_url=author_icon if author_icon else None)
    footer_text = input(f"{Fore.LIGHTGREEN_EX}Footer text (leave blank for none): ")
    if footer_text:
        footer_icon = input(f"{Fore.LIGHTGREEN_EX}Footer icon URL (leave blank for none): ")
        embed.set_footer(text=footer_text, icon_url=footer_icon if footer_icon else None)
    thumbnail = input(f"{Fore.LIGHTGREEN_EX}Thumbnail URL (leave blank for none): ")
    if thumbnail: embed.set_thumbnail(url=thumbnail)
    image = input(f"{Fore.LIGHTGREEN_EX}Image URL (leave blank for none): ")
    if image: embed.set_image(url=image)
    return embed

async def mass_dm_users(clients, user_ids):
    message_type = input(f"{Fore.LIGHTGREEN_EX}Message type (text/embed/both): ").lower()
    text_content = None
    embed_content = None
    
    if message_type in ['text', 'both']:
        text_content = input(f"{Fore.LIGHTGREEN_EX}Enter text message: ")
    if message_type in ['embed', 'both']:
        embed_content = await create_embed()
    
    if not text_content and not embed_content:
        print(f"{Fore.RED}No message content provided")
        return
    
    total = len(user_ids)
    for idx, uid in enumerate(user_ids, 1):
        current_client = clients[(idx - 1) % len(clients)]
        try:
            target = current_client.get_user(int(uid))
            if not target:
                try: target = await current_client.fetch_user(int(uid))
                except: pass
            
            if not target or target.bot or target.id == current_client.user.id:
                continue
            
            # Open DM channel first (rarely triggers captcha)
            try:
                dm_channel = await target.create_dm()
            except Exception as dm_err:
                print(f"{Fore.RED}[{idx}/{total}] Could not open DM with {uid}: {dm_err}")
                continue
            
            # Send message natively using discord.py-self
            sent = False
            try:
                if message_type == 'text':
                    await dm_channel.send(content=text_content)
                elif message_type == 'embed':
                    await dm_channel.send(embed=embed_content)
                else:
                    await dm_channel.send(content=text_content, embed=embed_content)
                sent = True
            except Exception as e:
                print(f"{Fore.RED}[{idx}/{total}] Failed to send: {e}")
            
            if sent:
                print(f"{Fore.LIGHTGREEN_EX}[{idx}/{total}] Sent to {Fore.YELLOW}{target} {Fore.CYAN}(via {current_client.user})")
            else:
                print(f"{Fore.RED}[{idx}/{total}] Failed to send to {Fore.YELLOW}{uid}")
                
        except Exception as e:
            print(f"{Fore.RED}[{idx}/{total}] Failed to send to {Fore.YELLOW}{uid}: {e}")
        
        if idx < total:
            await asyncio.sleep(random_cooldown(config.minimum_dm, config.maximum_dm))


async def mass_dm_server(clients, guild_id=None):
    client = clients[0]
    if not guild_id:
        while True:
            try:
                guild_id = int(input(f'{Fore.LIGHTYELLOW_EX}Enter server ID: '))
                break
            except ValueError:
                print(f'{Fore.RED}Invalid ID')
                
    guild = await client.get_guild_by_id(guild_id)
    if not guild:
        print(f"{Fore.RED}Server not found by primary client.")
        return
        
    print(f'Target: {Fore.YELLOW}{guild.name}')
    member_ids = [m.id for m in guild.members if not m.bot]
    await mass_dm_users(clients, member_ids)

async def mass_dm_all_users(clients):
    all_users = set()
    for c in clients:
        for u in c.users:
            if not u.bot: all_users.add(u.id)
    await mass_dm_users(clients, list(all_users))

async def mass_dm_from_file(clients):
    try:
        with open("members.txt", "r") as f:
            user_ids = [int(line.strip()) for line in f.readlines() if line.strip().isdigit()]
    except FileNotFoundError:
        print(f"{Fore.RED}members.txt not found.")
        return
    except Exception as e:
        print(f"{Fore.RED}Failed to read members.txt: {e}")
        return

    print(f"{Fore.LIGHTGREEN_EX}Loaded {len(user_ids)} IDs from members.txt.")
    
    limit_input = input(f"{Fore.LIGHTYELLOW_EX}Limit the number of users to DM? (Enter a number, or leave blank to DM all): ")
    if limit_input.isdigit():
        limit = int(limit_input)
        # Reverse the list so we start from the absolute bottom and move up
        user_ids = list(reversed(user_ids))[:limit]
        print(f"{Fore.LIGHTGREEN_EX}Limiting to {len(user_ids)} users, starting from the BOTTOM of the list and moving up.")
    
    await mass_dm_users(clients, user_ids)

async def scrape_members(client):
    invite_link = input(f"{Fore.LIGHTYELLOW_EX}Enter server invite link: ")
    try:
        invite = await client.fetch_invite(invite_link)
        guild = invite.guild
        if not guild:
            print(f"{Fore.RED}Invalid invite or could not find server.")
            return

        joined_guild = client.get_guild(guild.id)
        if not joined_guild:
            print(f"{Fore.LIGHTYELLOW_EX}Joining server {guild.name}...")
            await client.accept_invite(invite_link)
            await asyncio.sleep(3)
            joined_guild = client.get_guild(guild.id)
            
        if not joined_guild:
            print(f"{Fore.RED}Failed to join or fetch server details.")
            return

        print(f"{Fore.LIGHTGREEN_EX}Fetching members for {joined_guild.name} (this may take a moment)...")
        
        # In discord.py-self, very large guilds cannot be chunked.
        # We must use fetch_members() instead.
        members = []
        try:
            members = await joined_guild.fetch_members()
        except Exception as e:
            print(f"{Fore.RED}Failed to fetch members: {e}")
            return

        member_ids = [str(m.id) for m in members if not m.bot and m.id != client.user.id]
        if not member_ids:
            print(f"{Fore.RED}No members found or failed to fetch member list.")
            return
            
        with open("members.txt", "a") as f:
            for uid in set(member_ids): # Use set to remove duplicates
                f.write(uid + "\n")
                
        print(f"{Fore.LIGHTGREEN_EX}Successfully scraped {len(set(member_ids))} members and saved to members.txt!")

    except discord.Forbidden:
        print(f"{Fore.RED}Permission denied. You might be banned or the invite is invalid.")
    except Exception as e:
        print(f"{Fore.RED}Error scraping server: {e}")

async def deep_scrape_members(client):
    invite_link = input(f"{Fore.LIGHTYELLOW_EX}Enter server invite link: ")
    try:
        invite = await client.fetch_invite(invite_link)
        guild = invite.guild
        if not guild:
            print(f"{Fore.RED}Invalid invite or could not find server.")
            return

        joined_guild = client.get_guild(guild.id)
        if not joined_guild:
            print(f"{Fore.LIGHTYELLOW_EX}Joining server {guild.name}...")
            await client.accept_invite(invite_link)
            await asyncio.sleep(3)
            joined_guild = client.get_guild(guild.id)
            
        if not joined_guild:
            print(f"{Fore.RED}Failed to join or fetch server details.")
            return

        limit = input(f"{Fore.LIGHTYELLOW_EX}How many messages to read per channel? (e.g. 1000): ")
        try:
            limit = int(limit)
        except:
            limit = 1000

        print(f"{Fore.LIGHTGREEN_EX}Deep Scraping {joined_guild.name}... (This will take time)")
        
        member_ids = set()
        channels = [c for c in joined_guild.text_channels if c.permissions_for(joined_guild.me).read_message_history]
        total = len(channels)
        
        for idx, channel in enumerate(channels, 1):
            try:
                count = 0
                async for message in channel.history(limit=limit):
                    if not message.author.bot and message.author.id != client.user.id:
                        member_ids.add(str(message.author.id))
                    count += 1
                print(f"{Fore.LIGHTGREEN_EX}[{idx}/{total}] {Fore.YELLOW}#{channel.name}{Fore.LIGHTGREEN_EX}: Scanned {count} messages. Total unique active users so far: {len(member_ids)}")
            except discord.Forbidden:
                print(f"{Fore.RED}[{idx}/{total}] #{channel.name}: Missing access")
            except Exception as e:
                print(f"{Fore.RED}[{idx}/{total}] #{channel.name}: Error - {e}")
            await asyncio.sleep(0.5)
            
        if not member_ids:
            print(f"{Fore.RED}No members found during deep scrape.")
            return
            
        with open("members.txt", "a") as f:
            for uid in member_ids:
                f.write(uid + "\n")
                
        print(f"{Fore.LIGHTGREEN_EX}Successfully scraped {len(member_ids)} highly active members and saved to members.txt!")

    except discord.Forbidden:
        print(f"{Fore.RED}Permission denied. You might be banned or the invite is invalid.")
    except Exception as e:
        print(f"{Fore.RED}Error deep scraping server: {e}")

async def list_servers(client):
    print(f"{Fore.LIGHTGREEN_EX}Connected servers (Primary Account):")
    for guild in client.guilds:
        bot_member = guild.get_member(client.user.id)
        perms = []
        if bot_member.guild_permissions.ban_members: perms.append("Ban")
        if bot_member.guild_permissions.manage_channels: perms.append("Channels")
        if bot_member.guild_permissions.manage_roles: perms.append("Roles")
        if bot_member.guild_permissions.manage_nicknames: perms.append("Nicks")
        if bot_member.guild_permissions.manage_emojis: perms.append("Emojis")
        if bot_member.guild_permissions.manage_guild: perms.append("Server")
        if bot_member.guild_permissions.create_instant_invite: perms.append("Invites")

        perm_status = f"{Fore.LIGHTGREEN_EX}Perms: {', '.join(perms)}" if perms else f"{Fore.RED}No key perms"
        print(f"\n{Fore.YELLOW}{guild.name} {Fore.LIGHTGREEN_EX}(ID: {guild.id}, Members: {guild.member_count}) {perm_status}")
        
        if bot_member.guild_permissions.manage_guild:
            try:
                invites = await guild.invites()
                permanent_invites = [inv for inv in invites if inv.max_age == 0]
                if permanent_invites:
                    print(f"{Fore.CYAN}  Permanent Invites:")
                    for invite in permanent_invites:
                        print(f"  - {Fore.LIGHTBLUE_EX}{invite.url} (Uses: {invite.uses}, Created by: {invite.inviter})")
                else:
                    print(f"{Fore.RED}  No permanent invites found.")
            except discord.Forbidden:
                print(f"{Fore.RED}  No invite access (missing 'Manage Server' permission)")
            except Exception as e:
                print(f"{Fore.RED}  Failed to fetch invites: {e}")
    input("\nPress Enter to continue...")

async def leave_all_servers(client):
    confirm = input(f"{Fore.RED}Are you sure? This uses the primary account. (yes/no): ").lower()
    if confirm != "yes": return
    for guild in client.guilds:
        try:
            await guild.leave()
            print(f"{Fore.LIGHTGREEN_EX}Left {Fore.YELLOW}{guild.name}")
        except Exception as e:
            print(f"{Fore.RED}Failed to leave {Fore.YELLOW}{guild.name}: {e}")
        await asyncio.sleep(1)
    print(f"{Fore.LIGHTGREEN_EX}Left all servers")
    input("Press Enter to continue")

async def main_menu(clients):
    primary = clients[0]
    while True:
        await clear_console()
        print(pyfade.Fade.Horizontal(pyfade.Colors.yellow_to_red, '''
██╗  ██╗ █████╗ ██████╗ ██╗   ██╗███╗   ███╗ █████╗ 
██║ ██╔╝██╔══██╗██╔══██╗██║   ██║████╗ ████║██╔══██╗
█████═╝ ███████║██████╔╝██║   ██║██╔████╔██║███████║
██╔═██╗ ██╔══██║██╔══██╗██║   ██║██║╚██╔╝██║██╔══██║
██║ ╚██╗██║  ██║██║  ██║╚██████╔╝██║ ╚═╝ ██║██║  ██║
╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝'''))
        
        print(f'''{Fore.LIGHTWHITE_EX}                                   Made by {Fore.YELLOW}hoemotion

{Fore.LIGHTWHITE_EX}GitHub: {Fore.LIGHTBLUE_EX}https://github.com/hoemotion/Karuma
{Fore.LIGHTGREEN_EX}Active Accounts: {Fore.YELLOW}{len(clients)}
{Fore.LIGHTGREEN_EX}Primary Account: {Fore.YELLOW}{primary.user}

{Fore.LIGHTGREEN_EX}[1] Nuke Server (Ban members, delete channels/roles/emojis/stickers)
{Fore.LIGHTGREEN_EX}[2] Raid Server (Spam channels/roles, change nicks)
{Fore.LIGHTGREEN_EX}[3] Mass DM Server (Distributed with embed support)
{Fore.LIGHTGREEN_EX}[4] Mass DM All Users (Distributed with embed support)
{Fore.LIGHTGREEN_EX}[5] Mass DM from members.txt (Distributed)
{Fore.LIGHTGREEN_EX}[6] Fast Scrape Members (via Invite Link)
{Fore.LIGHTGREEN_EX}[7] Deep Scrape Members (Message History)
{Fore.LIGHTGREEN_EX}[8] List Servers (Primary Account)
{Fore.LIGHTGREEN_EX}[9] Leave All Servers (Primary Account)
{Fore.LIGHTGREEN_EX}[10] Exit
''')
        
        choice = input(f"{Fore.LIGHTGREEN_EX}Select>> ").lower()
        
        if choice == '1':
            await nuke_server(primary)
        elif choice == '2':
            await raid_server(primary)
        elif choice == '3':
            await mass_dm_server(clients)
        elif choice == '4':
            await mass_dm_all_users(clients)
        elif choice == '5':
            await mass_dm_from_file(clients)
        elif choice == '6':
            await scrape_members(primary)
        elif choice == '7':
            await deep_scrape_members(primary)
        elif choice == '8':
            await list_servers(primary)
        elif choice == '9':
            await leave_all_servers(primary)
        elif choice in ['10', 'quit', 'exit']:
            print(f"{Fore.LIGHTGREEN_EX}Goodbye!")
            for c in clients: await c.close()
            sys.exit(0)
        else:
            print(f"{Fore.RED}Invalid choice")
            await asyncio.sleep(1)

async def main():
    import discord.http
    print(f"{Fore.LIGHTCYAN_EX}[DEBUG] Loaded discord.http from: {discord.http.__file__}")
    await show_disclaimer()
    await show_boot_animation()
    
    # Initialize background captcha server if manual solving is enabled
    if config.captcha_service == "manual":
        await captcha_server.start()
        print_manual_instructions(captcha_server.port)
        await asyncio.sleep(1)
    tokens = []
    if os.path.exists("tokens.txt"):
        with open("tokens.txt", "r") as f:
            tokens = [line.strip() for line in f if line.strip()]
    if not tokens and config.token:
        tokens = [config.token]
        
    if not tokens:
        print(f"{Fore.RED}No tokens found in tokens.txt or config.json.")
        sys.exit(1)

    # Load proxies
    proxies = []
    if os.path.exists("proxies.txt"):
        with open("proxies.txt", "r") as f:
            for line in f:
                p = line.strip()
                if p and not p.startswith("#"):
                    if not p.startswith("http"):
                        p = f"http://{p}"
                    proxies.append(p)

    clients = []
    for i, token in enumerate(tokens):
        proxy = proxies[i % len(proxies)] if proxies else None
        client = KarumaBot(proxy=proxy)
        clients.append((client, token))
    
    print(f"{Fore.LIGHTYELLOW_EX}Starting {len(clients)} client(s)...")
    
    async def start_client(c, t):
        try:
            await c.start(t)
        except discord.LoginFailure:
            print(f"{Fore.RED}Invalid token: {t[:10]}...")
        except Exception as e:
            print(f"{Fore.RED}Failed to start client {t[:10]}... : {e}")

    # Start all clients in the background
    for c, t in clients:
        asyncio.create_task(start_client(c, t))
    
    # Wait for clients to connect
    print(f"{Fore.LIGHTYELLOW_EX}Waiting for connections (this may take up to 15s with proxies)...")
    await asyncio.sleep(15)
    
    active_clients = [c for c, t in clients if c.is_ready()]
    if not active_clients:
        print(f"{Fore.RED}No clients successfully connected. Check your tokens.")
        sys.exit(1)
        
    print(f"{Fore.LIGHTGREEN_EX}Successfully connected {len(active_clients)} account(s)!")
    await asyncio.sleep(2)
    
    await clear_console()
    await main_menu(active_clients)

if __name__ == "__main__":
    asyncio.run(main())
