from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(
        bypass_csp=True,
        ignore_https_errors=True
    )
    page = browser.new_page()
    page.goto("https://www.google.com")
    print("Success!")
    browser.close()