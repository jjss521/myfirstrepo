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
    for pg in range(1, 20):
        page.goto(f"https://skillhub.cn/?page={pg}", wait_until="networkidle", timeout=30000)
        time.sleep(1)
    
    # Get unique skills
    seen = set()
    unique_skills = []
    for s in all_skills:
        slug = s.get("slug", "")
        if slug and slug not in seen:
            seen.add(slug)
            unique_skills.append(s)
    
    # Filter design-related skills with broader keywords
    design_keywords = ["设计", "design", "ui", "ux", "界面", "原型", "figma", "sketch", 
                       "adobe", "photoshop", "illustrator", "xd", "视觉", "交互",
                       "体验", "wireframe", "mockup", "组件", "token", "排版",
                       "海报", "logo", "图标", "icon", "图片", "图像", "渲染",
                       "3d", "blender", "模型", "动画", "视频", "音频", "音效",
                       "图表", "diagram", "mermaid", "ppt", "powerpoint", "cad"]
    
    design_skills = []
    for s in unique_skills:
        name = s.get("name", "").lower()
        desc = s.get("description", "").lower()
        cats = " ".join([c.get("name", "").lower() for c in s.get("subCategories", [])])
        
        if any(kw in name or kw in desc or kw in cats for kw in design_keywords):
            design_skills.append(s)
    
    design_skills.sort(key=lambda x: x.get("downloads", 0), reverse=True)
    
    print(f"Total unique skills: {len(unique_skills)}")
    print(f"Design-related skills: {len(design_skills)}\n")
    
    print("=== Top 20 Design Skills (by downloads) ===\n")
    for i, s in enumerate(design_skills[:20], 1):
        print(f"{i}. {s.get('name')}")
        print(f"   Downloads: {s.get('downloads', 0)} | Stars: {s.get('stars', 0)} | Score: {round(s.get('score', 0), 1)}")
        print(f"   Category: {s.get('category')} | Sub: {[c.get('name') for c in s.get('subCategories', [])]}")
        print(f"   URL: https://skillhub.cn/skills/{s.get('slug')}")
        print()
    
    browser.close()
