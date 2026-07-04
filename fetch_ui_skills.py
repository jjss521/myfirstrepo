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
    
    # Search for UI design skills
    page.goto("https://skillhub.cn/search?keyword=UI%E8%AE%BE%E8%AE%A1", wait_until="networkidle", timeout=30000)
    time.sleep(5)
    
    print("=== UI Design Search Results ===\n")
    for r in api_data:
        url = r["url"]
        if "skill" in url.lower() and "search" in url.lower():
            print(f"URL: {url}")
            data = r["data"]
            if isinstance(data, dict) and "data" in data:
                skills = data["data"].get("skills", []) if isinstance(data["data"], dict) else []
                for s in skills[:10]:
                    print(f"  Name: {s.get('name')}")
                    print(f"  Downloads: {s.get('downloads', 0)}")
                    print(f"  Stars: {s.get('stars', 0)}")
                    print(f"  SubCategories: {[c.get('name') for c in s.get('subCategories', [])]}")
                    print(f"  Description: {s.get('description', '')[:100]}")
                    print(f"  Slug: {s.get('slug')}")
                    print()
    
    # Also try "界面" search
    page.goto("https://skillhub.cn/search?keyword=%E7%95%8C%E9%9D%A2", wait_until="networkidle", timeout=30000)
    time.sleep(3)
    
    print("\n=== Interface Search Results ===\n")
    for r in api_data[-5:]:
        url = r["url"]
        if "skill" in url.lower():
            data = r["data"]
            if isinstance(data, dict) and "data" in data:
                skills = data["data"].get("skills", []) if isinstance(data["data"], dict) else []
                for s in skills[:5]:
                    print(f"  Name: {s.get('name')}")
                    print(f"  Downloads: {s.get('downloads', 0)}")
                    print(f"  Stars: {s.get('stars', 0)}")
                    print(f"  SubCategories: {[c.get('name') for c in s.get('subCategories', [])]}")
                    print()
    
    browser.close()
