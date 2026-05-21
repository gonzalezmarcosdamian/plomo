"""
Usa tu Chrome con sesión activa para interceptar la API de Muzpa.
Chrome debe estar cerrado antes de correr esto.
"""
import asyncio, os, sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")
from playwright.async_api import async_playwright

CHROME_PROFILE = r"C:\Users\gonza\AppData\Local\Google\Chrome\User Data"
API_CALLS = []


async def main():
    async with async_playwright() as p:
        # Lanzar Chrome con perfil existente (ya logueado en Muzpa)
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=CHROME_PROFILE,
            headless=False,
            channel="chrome",
            accept_downloads=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = browser.pages[0] if browser.pages else await browser.new_page()

        # Interceptar requests de API
        async def on_request(req):
            if 'muzpa.com' in req.url:
                API_CALLS.append({'method': req.method, 'url': req.url,
                                  'post': req.post_data, 'headers': dict(req.headers)})
                # Mostrar TODAS las llamadas que no sean imágenes
                if not any(x in req.url for x in ['.png', '.jpg', '.css', '.js', '.ico']):
                    print(f"REQ: {req.method} {req.url}")
                    if req.post_data:
                        print(f"  POST: {req.post_data[:300]}")

        async def on_response(resp):
            if 'muzpa.com' in resp.url:
                if not any(x in resp.url for x in ['.png', '.jpg', '.css', '.js', '.ico']):
                    print(f"RESP {resp.status}: {resp.url}")
                    try:
                        body = await resp.text()
                        if len(body) < 2000:
                            print(f"  BODY: {body[:500]}")
                    except:
                        pass

        page.on("request", on_request)
        page.on("response", on_response)

        print("Chrome abierto con tu perfil.")
        print(">>> Navegá a srv.muzpa.com y buscá 'maze 28' <<<")
        print(">>> También intentá descargar un track MP3 <<<")
        print("Esperando 45 segundos para que hagas las acciones...")
        await asyncio.sleep(45)

        # Guardar todas las llamadas
        with open("muzpa_api_calls.json", "w") as f:
            json.dump(API_CALLS, f, indent=2)
        print(f"\nGuardadas {len(API_CALLS)} llamadas en muzpa_api_calls.json")

        await browser.close()


asyncio.run(main())
