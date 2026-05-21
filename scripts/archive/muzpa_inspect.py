"""
Intercepta las llamadas API de Muzpa para encontrar los endpoints de búsqueda y descarga.
Corre con headless=False para hacer login y buscar un track manualmente.
"""
import asyncio, os, sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")
from playwright.async_api import async_playwright

API_CALLS = []

async def main():
    user = os.getenv("MUZPA_USER")
    pwd = os.getenv("MUZPA_PASS")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        ctx = await browser.new_context(accept_downloads=True)
        page = await ctx.new_page()

        # Interceptar todas las llamadas de red
        async def on_request(request):
            url = request.url
            if any(x in url for x in ['/api/', '/search', '/download', '/track', '/media']):
                API_CALLS.append({
                    'method': request.method,
                    'url': url,
                    'headers': dict(request.headers),
                })

        async def on_response(response):
            url = response.url
            if any(x in url for x in ['/api/', '/search', '/download', '/track', '/media']):
                try:
                    body = await response.text()
                    if len(body) < 5000:
                        print(f"\nRESPONSE {response.status} {url[:80]}")
                        print(body[:500])
                except:
                    pass

        page.on("request", on_request)
        page.on("response", on_response)

        print("Abriendo Muzpa (visual)...")
        await page.goto('https://srv.muzpa.com', wait_until='domcontentloaded')
        await asyncio.sleep(2)

        # Login
        try:
            await page.fill('input[type="email"]', user, timeout=5000)
            await page.fill('input[type="password"]', pwd)
            await page.click('button[type="submit"]')
            await asyncio.sleep(3)
            print("Login OK")
        except:
            print("Login manual necesario - logueate en el browser que se abrió")

        print("\n=== Buscá 'maze 28' en la barra de búsqueda del browser ===")
        print("Esperando 20 segundos para que hagas la búsqueda...")
        await asyncio.sleep(20)

        # Guardar todas las llamadas interceptadas
        with open("muzpa_api_calls.json", "w") as f:
            json.dump(API_CALLS, f, indent=2)

        print(f"\nAPI calls interceptadas: {len(API_CALLS)}")
        for call in API_CALLS[:20]:
            print(f"  {call['method']} {call['url'][:100]}")

        await browser.close()

asyncio.run(main())
