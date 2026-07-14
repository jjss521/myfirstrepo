"""Check if nanchang_converted.docx is valid."""
import os, zipfile

path = r"D:\qoderwork\可研初步设计电气文本TESTB\source\nanchang_converted.docx"
print(f"Path: {path}")
print(f"Exists: {os.path.exists(path)}")
print(f"Size: {os.path.getsize(path)}")

try:
    with zipfile.ZipFile(path, 'r') as z:
        names = z.namelist()
        print(f"Valid ZIP: {len(names)} entries")
        print(f"Has document.xml: {'word/document.xml' in names}")
        # Check for NULL entries
        nulls = [n for n in names if 'NULL' in n]
        print(f"NULL entries: {nulls}")
except Exception as e:
    print(f"Not a valid ZIP: {e}")

# Also test with python-docx
from docx import Document
try:
    doc = Document(path)
    print(f"python-docx OK: {len(doc.paragraphs)} paragraphs")
except Exception as e:
    print(f"python-docx FAIL: {e}")
