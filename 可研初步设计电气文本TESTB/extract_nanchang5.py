"""Extract nanchang.doc via Word COM - save as TXT (no encryption)."""
import os, ctypes

src = r"D:\qoderwork\可研初步设计电气文本TESTB\source\nanchang.doc"
out_txt = r"D:\temp_nanchang_out.txt"
out_md = r"D:\qoderwork\可研初步设计电气文本TESTB\output\extracted\南昌取水口优化调整可研报告2021.md"

# Cleanup stale
for p in [out_txt]:
    if os.path.exists(p):
        os.remove(p)

ole32 = ctypes.OleDLL('ole32')
ole32.CoInitialize(None)

word = None
try:
    import comtypes.client
    word = comtypes.client.CreateObject("Word.Application")
    word.Visible = False
    word.DisplayAlerts = False

    abs_src = os.path.abspath(src)
    print(f"Opening: {src} ({os.path.getsize(src)/1024/1024:.1f} MB)")
    doc = word.Documents.Open(abs_src)

    abs_out = os.path.abspath(out_txt)
    print(f"Saving as TXT: {abs_out}")
    # wdFormatText = 2
    doc.SaveAs(abs_out, FileFormat=2)
    doc.Close()
    print(f"Saved. File exists: {os.path.exists(out_txt)}")

    if os.path.exists(out_txt):
        sz = os.path.getsize(out_txt)
        print(f"TXT size: {sz} bytes ({sz/1024/1024:.1f} MB)")
        with open(out_txt, 'rb') as f:
            header = f.read(16)
        print(f"Header: {' '.join(f'{b:02x}' for b in header)}")
        print(f"Text: {header}")

        # Read the text file
        # Try utf-8 first, then gbk
        for enc in ['utf-8', 'gbk', 'gb2312', 'utf-16']:
            try:
                with open(out_txt, 'r', encoding=enc) as f:
                    content = f.read()
                print(f"Read OK with {enc}: {len(content)} chars")
                break
            except:
                continue

        # Convert to markdown - use blank lines between paragraphs
        paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
        md_content = '\n\n'.join(paragraphs)
        with open(out_md, 'w', encoding='utf-8') as f:
            f.write(md_content)
        print(f"Written to: {out_md}")
        print(f"Total paragraphs: {len(paragraphs)}")
        print(f"Preview: {md_content[:300]}...")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    if word:
        try: word.Quit()
        except: pass
    ole32.CoUninitialize()
    for p in [out_txt]:
        if os.path.exists(p):
            try: os.remove(p)
            except: pass
