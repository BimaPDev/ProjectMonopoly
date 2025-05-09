from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=100)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://www.instagram.com/accounts/login/")

    input("🔐 Log in manually, then press ENTER to save session...")

    context.storage_state(path="auth.json")
    browser.close()
    print("✅ Session saved to auth.json")
