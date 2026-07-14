"""Extract nanchang.doc text directly via Word COM, no intermediate file."""
import os, ctypes

src = r"D:\qoderwork\可研初步设计电气文本TESTB\source\nanchang.doc"
out_md = r"D:\qoderwork\可研初步设计电气文本TESTB\output\extracted\南昌取水口优化调整可研报告2021.md"

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

    # Get total paragraphs
    total = doc.Paragraphs.Count
    print(f"Total paragraphs: {total}")

    lines = []
    for i in range(1, total + 1):
        para = doc.Paragraphs(i)
        text = para.Range.Text.strip()
        if not text:
            continue
        # Check if bold
        is_bold = False
        try:
            if para.Range.Bold:
                is_bold = True
        except:
            pass
        # Check style
        if not is_bold:
            try:
                style_name = para.Style.NameLocal
                if style_name and style_name.startswith("heading"):
                    is_bold = True
            except:
                pass
        prefix = "## " if is_bold else ""
        lines.append(prefix + text)

        if i % 500 == 0:
            print(f"  Progress: {i}/{total} paragraphs...")

    doc.Close()

    out_text = "\n\n".join(lines)
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(out_text)

    print(f"\nOutput: {out_md}")
    print(f"Paragraphs: {len(lines)}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    if word:
        try: word.Quit()
        except: pass
    ole32.CoUninitialize()
