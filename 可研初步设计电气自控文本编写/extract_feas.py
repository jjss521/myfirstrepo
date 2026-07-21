# -*- coding: utf-8 -*-
import pdfplumber, re, traceback, sys

fn = r'D:/D盘/360安全浏览器下载/《市政公用工程设计文件编制深度规定》（2025年版）.pdf'
TYPE_MAP = {'给水工程': 'water_supply', '排水工程': 'drainage',
            '道路工程': 'road', '环境卫生工程': 'sanitation'}

cur_type = None
cur_stage = None
results = {}

def classify_page(t):
    global cur_type, cur_stage
    m = re.search(r'第[一二三四五六七八九十]+篇\s*([一-龥]+工程)', t)
    if m and m.group(1) in TYPE_MAP:
        cur_type = TYPE_MAP[m.group(1)]
    # 可研章标题： "第一章 XXX工程可行性研究报告文件编制深度"
    for cn, en in TYPE_MAP.items():
        if re.search(r'第[一二三四五六七八九十]+章\s*' + re.escape(cn) + r'.{0,6}可行性研究', t):
            cur_type = en
            cur_stage = 'feasibility'
            return
    # 初步设计章
    for cn, en in TYPE_MAP.items():
        if re.search(r'第[一二三四五六七八九十]+章\s*' + re.escape(cn) + r'.{0,6}初步设计', t):
            cur_type = en
            cur_stage = 'preliminary'
            return

SUBSECTIONS = [
    ('供配电设计', '电气设计'),
    ('自动控制及通信设计', '仪表自控弱电设计'),
    ('仪表、自动控制及通信设计', '仪表自控弱电设计'),
    ('仪表自控及通信设计', '仪表自控弱电设计'),
    ('电气设计', '电气设计'),
]

try:
    with pdfplumber.open(fn) as pdf:
        for i, page in enumerate(pdf.pages):
            t = page.extract_text() or ''
            classify_page(t)
            if cur_stage != 'feasibility':
                continue
            for key, label in SUBSECTIONS:
                # 匹配 "5.4.4 供配电设计" 或 "5.4 供配电设计" 等
                for mm in re.finditer(r'\d+\.\d+(?:\.\d+)?\s*' + re.escape(key), t):
                    idx = t.find(mm.group(0))
                    after = t[idx + len(mm.group(0)):]
                    # 截到下一个编号子节（同层级或更高）之前
                    nxt = re.search(r'\n\d+\.\d+(?:\.\d+)?\s', after)
                    seg = after[:nxt.start()] if nxt else after
                    seg = seg.strip()
                    if not seg:
                        continue
                    results.setdefault(cur_type, {}).setdefault('feasibility', {}).setdefault(label, [])
                    if seg not in results[cur_type]['feasibility'][label]:
                        results[cur_type]['feasibility'][label].append(seg)
except Exception:
    traceback.print_exc()
    sys.exit(1)

with open('feas_extract.txt', 'w', encoding='utf-8') as f:
    for typ in ['water_supply', 'drainage', 'road', 'sanitation']:
        f.write('################ %s ################\n' % typ)
        d = results.get(typ, {}).get('feasibility')
        if not d:
            f.write('  (无)\n')
            continue
        for lab, segs in d.items():
            f.write('----- %s -----\n' % lab)
            for s in segs[:3]:
                f.write(s + '\n\n')
print('OK pages scanned, types found:', list(results.keys()))
