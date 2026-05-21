"""
Descarga tracks de Muzpa usando la API directamente.
Más confiable que browser automation.
"""
import sys, os, requests, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")
from plomo import config

BASE = "https://muzpa.com/api"
DOWNLOADS = config.DOWNLOADS_FOLDER


def login(session, user, pwd):
    # Intentar endpoints comunes de login
    endpoints = [
        ("POST", f"{BASE}/login", {"email": user, "password": pwd}),
        ("POST", f"{BASE}/auth", {"email": user, "password": pwd}),
        ("POST", f"{BASE}/auth/login", {"email": user, "password": pwd}),
        ("POST", f"{BASE}/user/login", {"login": user, "password": pwd}),
    ]
    for method, url, data in endpoints:
        try:
            r = session.post(url, json=data, timeout=10)
            print(f"  {r.status_code} {url}")
            if r.status_code == 200:
                try:
                    j = r.json()
                    print(f"  Response: {json.dumps(j)[:200]}")
                    return True
                except:
                    print(f"  Response: {r.text[:200]}")
            elif r.status_code not in [404, 405]:
                print(f"  Response: {r.text[:200]}")
        except Exception as e:
            print(f"  Error: {e}")
    return False


def search(session, query):
    endpoints = [
        f"{BASE}/search?text={query}&format=mp3&matchonly=true",
        f"{BASE}/tracks?search={query}&format=mp3",
        f"{BASE}/media/search?text={query}&format=mp3",
    ]
    for url in endpoints:
        try:
            r = session.get(url, timeout=10)
            print(f"  {r.status_code} {url}")
            if r.status_code == 200:
                print(f"  Response: {r.text[:300]}")
                return r.json() if r.headers.get('content-type', '').startswith('application/json') else None
        except Exception as e:
            print(f"  Error: {e}")
    return None


def main():
    user = os.getenv("MUZPA_USER")
    pwd = os.getenv("MUZPA_PASS")

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Origin": "https://srv.muzpa.com",
        "Referer": "https://srv.muzpa.com/",
    })

    print("=== Probando login ===")
    login(session, user, pwd)

    print("\n=== Probando search ===")
    search(session, "Guy J Sirens")

    # Ver si hay cookies
    print(f"\nCookies: {dict(session.cookies)}")


if __name__ == "__main__":
    main()
