from playwright.sync_api import sync_playwright
import json, time, sys

sys.stdout.reconfigure(encoding='utf-8')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    api_data = []
    def on_resp(response):
        if "api" in response.url or "skill" in response.url:
            try:
                data = response.json()
                api_data.append({"url": response.url, "data": data})
            except:
                pass
    
    page.on("response", on_resp)
    
    page.goto("https://skillhub.cn", wait_until="networkidle", timeout=30000)
    time.sleep(5)
    
    text = page.inner_text("body")
    print("=== PAGE TEXT ===")
    print(text[:5000])
    
    print("\n=== API RESPONSES ===")
    for r in api_data:
        url = r["url"]
        if "skill" in url.lower() or "list" in url.lower() or "hot" in url.lower():
            print(f"\nURL: {url}")
            print(json.dumps(r["data"], ensure_ascii=False)[:2000])
    
    page.screenshot(path="D:/qoderwork/skillhub.png", full_page=True)
    print("\nScreenshot saved to D:/qoderwork/skillhub.png")
    
    browser.close()
