"""Repair taochong.docx: remove ALL references to word/NULL from every XML."""
import zipfile
import shutil
import os
import re

path = r"D:\qoderwork\可研初步设计电气文本TESTB\source\taochong.docx"
tmp = path + ".repaired2"

entries = {}

with zipfile.ZipFile(path, 'r') as z:
    for item in z.infolist():
        data = z.read(item.filename)
        if item.filename.endswith('.xml') or item.filename.endswith('.rels'):
            text = data.decode('utf-8')
            if 'word/NULL' in text or 'NULL' in text:
                # Remove Override entries for word/NULL
                text = re.sub(r'<Override\s+PartName="word/NULL"[^>]*/>', '', text)
                text = re.sub(r'<Override\s+PartName="/word/NULL"[^>]*/>', '', text)
                # Remove Relationship entries for word/NULL
                text = re.sub(r'<Relationship\s+[^>]*Target="word/NULL"[^>]*/>', '', text)
                text = re.sub(r'<Relationship\s+[^>]*Target="/word/NULL"[^>]*/>', '', text)
                # Remove any reference to NULL
                text = re.sub(r'[Tt]arget="[^"]*NULL[^"]*"', '', text)
                text = re.sub(r'PartName="[^"]*NULL[^"]*"', '', text)
                data = text.encode('utf-8')
                print(f"  Patched: {item.filename}")
        entries[item.filename] = data

with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
    for name, data in entries.items():
        zout.writestr(name, data)

shutil.move(tmp, path)
print(f"Done: {len(entries)} entries")

# Verify
with zipfile.ZipFile(path, 'r') as z:
    for name in z.namelist():
        if name.endswith('.xml') or name.endswith('.rels'):
            content = z.read(name).decode('utf-8', errors='ignore')
            if 'NULL' in content:
                print(f"  WARNING: still has NULL: {name}")
