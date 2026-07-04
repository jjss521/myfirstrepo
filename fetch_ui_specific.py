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
    for pg in range(1, 15):
        page.goto(f"https://skillhub.cn/?page={pg}", wait_until="networkidle", timeout=30000)
        time.sleep(1)
    
    # Filter UI/design specific skills
    ui_keywords = ["ui", "ux", "界面", "原型", "figma", "sketch", "adobe", "photoshop", 
                   "illustrator", "xd", "设计稿", "切图", "标注", "高保真", "低保真",
                   "wireframe", "mockup", "design system", "组件库", "design token",
                   "视觉设计", "交互设计", "用户体验", "user interface"]
    
    ui_skills = []
    seen = set()
    for s in all_skills:
        name = s.get("name", "").lower()
        desc = s.get("description", "").lower()
        cats = " ".join([c.get("name", "").lower() for c in s.get("subCategories", [])])
        slug = s.get("slug", "")
        
        if slug in seen:
            continue
        seen.add(slug)
        
        if any(kw in name or kw in desc or kw in cats for kw in ui_keywords):
            ui_skills.append(s)
    
    ui_skills.sort(key=lambda x: x.get("downloads", 0), reverse=True)
    
    print("=== UI Design Specific Skills ===\n")
    for s in ui_skills[:15]:
        print(f"Name: {s.get('name')}")
        print(f"Downloads: {s.get('downloads', 0)}")
        print(f"Stars: {s.get('stars', 0)}")
        print(f"Score: {round(s.get('score', 0), 1)}")
        print(f"SubCategories: {[c.get('name') for c in s.get('subCategories', [])]}")
        print(f"Description: {s.get('description', '')[:150]}")
        print(f"URL: https://skillhub.cn/skills/{s.get('slug')}")
        print()
    
    # Also get design-media category specifically
    print("\n=== Design & Media Category (all) ===\n")
    design_media = [s for s in all_skills if s.get("category") == "design-media"]
    design_media.sort(key=lambda x: x.get("downloads", 0), reverse=True)
    for s in design_media[:10]:
        print(f"Name: {s.get('name')}")
        print(f"Downloads: {s.get('downloads', 0)}")
        print(f"Stars: {s.get('stars', 0)}")
        print(f"SubCategories: {[c.get('name') for c in s.get('subCategories', [])]}")
        print(f"Description: {s.get('description', '')[:100]}")
        print()
    
    browser.close()
