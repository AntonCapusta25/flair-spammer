"""Manual browser-based captcha solver with local HTTP bridge."""

import asyncio
import logging
import webbrowser

import discord
from aiohttp import web

log = logging.getLogger(__name__)

_SOLVER_JS = """(async function(){const s=document.createElement('style');s.innerHTML=`#karuma-solver-overlay{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.85);z-index:999999;display:flex;justify-content:center;align-items:center;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;color:#fff}.karuma-solver-box{background:#2f3136;padding:40px;border-radius:12px;box-shadow:0 8px 24px rgba(0,0,0,0.5);text-align:center;max-width:400px;width:90%}.karuma-solver-box h2{margin-top:0;margin-bottom:10px;font-size:22px}.karuma-solver-box p{color:#b9bbbe;font-size:14px;margin-bottom:25px}.karuma-solver-status{margin-top:25px;color:#00b0f4;font-weight:bold}`;document.head.appendChild(s);if(!window.hcaptcha&&!document.querySelector('script[src*="hcaptcha.com"]')){const hc=document.createElement('script');hc.src='https://js.hcaptcha.com/1/api.js';hc.async=true;hc.defer=true;document.head.appendChild(hc)}if(!window.grecaptcha&&!document.querySelector('script[src*="recaptcha"]')){const rc=document.createElement('script');rc.src='https://www.google.com/recaptcha/api.js';rc.async=true;rc.defer=true;document.head.appendChild(rc)}let active=null;async function poll(){try{const r=await fetch('http://127.0.0.1:{{port}}/poll');if(!r.ok)return;const d=await r.json();if(d.status==='need_solve'&&!active){active=d;const o=document.createElement('div');o.id='karuma-solver-overlay';o.innerHTML=`<div class="karuma-solver-box"><h2>Karuma Captcha Required</h2><p>Please solve the verification below to continue messaging.</p><div id="karuma-captcha-container"></div><div class="karuma-solver-status" id="karuma-status">Waiting for verification...</div></div>`;document.body.appendChild(o);function solve(t){document.getElementById('karuma-status').innerText="Submitting token...";document.getElementById('karuma-status').style.color='#43b581';fetch('http://127.0.0.1:{{port}}/submit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token:t})}).then(res=>{if(res.ok){document.getElementById('karuma-status').innerText="Solved! Closing overlay...";setTimeout(()=>{o.remove();active=null},1500)}else{document.getElementById('karuma-status').innerText="Submission failed. Try again.";document.getElementById('karuma-status').style.color='#f04747';active=null}}).catch(err=>{document.getElementById('karuma-status').innerText="Connection error.";document.getElementById('karuma-status').style.color='#f04747';active=null})}setTimeout(()=>{if(d.service==='hcaptcha'){if(window.hcaptcha){var opts={sitekey:d.sitekey,theme:'dark',callback:solve};if(d.rqdata)opts.data=d.rqdata;hcaptcha.render('karuma-captcha-container',opts)}else{o.remove();active=null}}else{if(window.grecaptcha){grecaptcha.render('karuma-captcha-container',{sitekey:d.sitekey,theme:'dark',callback:solve})}else{o.remove();active=null}}window.focus()},1000)}}catch(e){}}setInterval(poll,2000);console.log("Karuma Solver active!");})();"""


class ManualCaptchaServer:
    """Local aiohttp server that receives captcha tokens from the browser."""

    def __init__(self) -> None:
        self.port = 5050
        self._requests: dict[str, dict] = {}
        self._futures: dict[str, asyncio.Future[str]] = {}
        self._runner: web.AppRunner | None = None
        self._site: web.TCPSite | None = None

    async def start(self) -> None:
        for port in range(5050, 5100):
            try:
                app = web.Application()
                app.router.add_route("*", "/poll", self._handle_poll)
                app.router.add_route("*", "/submit", self._handle_submit)

                self._runner = web.AppRunner(app)
                await self._runner.setup()
                self._site = web.TCPSite(self._runner, "127.0.0.1", port)
                await self._site.start()
                self.port = port
                log.info("Manual captcha server listening on http://127.0.0.1:%s", port)
                return
            except OSError:
                continue
        log.error("Failed to bind manual captcha server on ports 5050-5099")

    def print_instructions(self) -> None:
        js_code = _SOLVER_JS.replace("{{port}}", str(self.port))
        log.info("Manual captcha setup:")
        log.info("1. Open https://discord.com/channels/@me in your browser")
        log.info("2. Open DevTools console (F12) and paste the solver script")
        print("\n--- Karuma browser solver script ---\n")
        print(js_code)
        print("\n--- end script ---\n")

    async def _cors_headers(self) -> dict[str, str]:
        return {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }

    async def _handle_poll(self, request: web.Request) -> web.Response:
        headers = await self._cors_headers()
        if request.method == "OPTIONS":
            return web.Response(headers=headers)
        username = request.query.get("user")
        if username and username in self._requests:
            return web.json_response(self._requests[username], headers=headers)
        if self._requests:
            _, payload = next(iter(self._requests.items()))
            return web.json_response(payload, headers=headers)
        return web.json_response({"status": "idle"}, headers=headers)

    async def _handle_submit(self, request: web.Request) -> web.Response:
        headers = await self._cors_headers()
        if request.method == "OPTIONS":
            return web.Response(headers=headers)
        try:
            data = await request.json()
            token = data.get("token")
            username = data.get("username")
            if not token:
                return web.Response(text="Missing token", status=400, headers=headers)

            if username and username in self._futures:
                future = self._futures.pop(username, None)
                self._requests.pop(username, None)
            else:
                future = next((f for f in self._futures.values() if not f.done()), None)
                if self._futures:
                    self._requests.clear()
                    self._futures.clear()

            if future and not future.done():
                future.set_result(token)
            return web.Response(text="OK", headers=headers)
        except Exception as exc:
            return web.Response(text=str(exc), status=400, headers=headers)

    async def solve(self, exception: discord.CaptchaRequired, client_username: str) -> str:
        loop = asyncio.get_running_loop()
        future: asyncio.Future[str] = loop.create_future()
        self._futures[client_username] = future
        self._requests[client_username] = {
            "status": "need_solve",
            "service": exception.service.lower(),
            "sitekey": exception.sitekey,
            "rqdata": getattr(exception, "rqdata", "") or "",
            "username": client_username,
        }

        log.warning("Manual captcha required for %s (%s)", client_username, exception.service)
        try:
            webbrowser.open("https://discord.com/channels/@me")
        except OSError:
            pass

        try:
            return await asyncio.wait_for(future, timeout=300)
        except asyncio.TimeoutError as exc:
            self._futures.pop(client_username, None)
            self._requests.pop(client_username, None)
            raise RuntimeError("Manual captcha solve timed out after 300s") from exc
        finally:
            log.info("Captcha solved via browser for %s", client_username)


manual_captcha_server = ManualCaptchaServer()
