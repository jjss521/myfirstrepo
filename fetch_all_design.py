from playwright.sync_api import sync_playwright
import json, time, sys

sys.stdout.reconfigure(encoding='utf-8')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    all_skills = []
    def on_resp(response):
        if "api.skillhub.cn" in response.url and "skill" in response.url:
            try:
                data = response.json()
                if isinstance(data, dict) and "data" in data:
                    skills = data["data"].get("skills", []) if isinstance(data["data"], dict) else []
                    all_skills.extend(skills)
            except:
                pass
    
    page.on("response", on_resp)
    
    # Browse all pages
    for pg in range(1, 10):
        page.goto(f"https://skillhub.cn/?page={pg}", wait_until="networkidle", timeout=30000)
        time.sleep(2)
    
    # Filter design-related skills
    design_keywords = ["ui", "设计", "design", "界面", "figma", "sketch", "原型", "视觉", "图片", "海报", "logo", "icon", "图标", "排版", "平面"]
    
    design_skills = []
    seen = set()
    for s in all_skills:
        name = s.get("name", "").lower()
        desc = s.get("description", "").lower()
        cats = " ".join([c.get("name", "").lower() for c in s.get("subCategories", [])])
        slug = s.get("slug", "")
        
        if slug in seen:
            continue
        seen.add(slug)
        
        if any(kw in name or kw in desc or kw in cats for kw in design_keywords):
            design_skills.append(s)
    
    design_skills.sort(key=lambda x: x.get("downloads", 0), reverse=True)
    
    print("=== Design Related Skills (sorted by downloads) ===\n")
    for s in design_skills[:20]:
        print(f"Name: {s.get('name')}")
        print(f"Downloads: {s.get('downloads', 0)}")
        print(f"Stars: {s.get('stars', 0)}")
        print(f"Score: {round(s.get('score', 0), 1)}")
        print(f"Category: {s.get('category')}")
        print(f"SubCategories: {[c.get('name') for c in s.get('subCategories', [])]}")
        print(f"Description: {s.get('description', '')[:120]}")
        print(f"Slug: {s.get('slug')}")
        print(f"URL: https://skillhub.cn/skills/{s.get('slug')}")
        print()
    
    browser.close()
