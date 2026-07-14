"""Repair taochong.docx: remove word/NULL reference from Content_Types."""
import zipfile
import shutil
import os
import re

path = r"D:\qoderwork\可研初步设计电气文本TESTB\source\taochong.docx"
tmp = path + ".repaired"

# Read all entries, patch Content_Types.xml
entries = {}
content_types_xml = None

with zipfile.ZipFile(path, 'r') as z:
    for item in z.infolist():
        if item.filename.startswith('word/NULL'):
            print(f"Skipping corrupt entry: {item.filename}")
            continue
        data = z.read(item.filename)
        if item.filename == '[Content_Types].xml':
            content_types_xml = data.decode('utf-8')
            # Remove any reference to word/NULL
            content_types_xml = re.sub(r'<Override PartName="/word/NULL"[^>]*/>', '', content_types_xml)
            content_types_xml = re.sub(r'<Override PartName="word/NULL"[^>]*/>', '', content_types_xml)
            data = content_types_xml.encode('utf-8')
        entries[item.filename] = data

with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
    for name, data in entries.items():
        zout.writestr(name, data)

shutil.move(tmp, path)
print(f"Repaired: {len(entries)} entries kept")
