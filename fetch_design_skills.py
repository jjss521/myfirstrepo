from playwright.sync_api import sync_playwright
import json, time, sys

sys.stdout.reconfigure(encoding='utf-8')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    api_data = []
    def on_resp(response):
        if "skill" in response.url:
            try:
                data = response.json()
                api_data.append({"url": response.url, "data": data})
            except:
                pass
    
    page.on("response", on_resp)
    
    # Go to design-media category
    page.goto("https://skillhub.cn/category/design-media", wait_until="networkidle", timeout=30000)
    time.sleep(5)
    
    print("=== API RESPONSES ===")
    for r in api_data:
        url = r["url"]
        if "skill" in url.lower():
            print(f"\nURL: {url}")
            data = r["data"]
            if isinstance(data, dict) and "data" in data:
                skills = data["data"].get("skills", []) if isinstance(data["data"], dict) else []
                for s in skills[:20]:
                    print(f"  Name: {s.get('name')}")
                    print(f"  Downloads: {s.get('downloads', 0)}")
                    print(f"  Stars: {s.get('stars', 0)}")
                    print(f"  SubCategories: {[c.get('name') for c in s.get('subCategories', [])]}")
                    print(f"  Description: {s.get('description', '')[:80]}")
                    print()
    
    browser.close()
