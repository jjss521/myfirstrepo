import zipfile, shutil, re

path = r"D:\qoderwork\可研初步设计电气文本TESTB\source\taochong.docx"
tmp = path + ".repaired3"
entries = {}

with zipfile.ZipFile(path, 'r') as z:
    for item in z.infolist():
        data = z.read(item.filename)
        if item.filename == 'word/_rels/document.xml.rels':
            text = data.decode('utf-8')
            # Remove the relationship with Target="NULL"
            text = re.sub(r'<Relationship\s+Id="[^"]*"\s+Type="[^"]*"\s+Target="NULL"\s*/>', '', text)
            if 'NULL' in text:
                print(f"  WARNING: NULL still in {item.filename}")
            else:
                print(f"  OK: NULL removed from {item.filename}")
            data = text.encode('utf-8')
        entries[item.filename] = data

with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
    for name, data in entries.items():
        zout.writestr(name, data)

shutil.move(tmp, path)
print("Saved. Verifying...")

with zipfile.ZipFile(path, 'r') as z:
    for name in z.namelist():
        if name.endswith('.xml') or name.endswith('.rels'):
            content = z.read(name).decode('utf-8', errors='ignore')
            m = re.findall(r'[Tt]arget="[^"]*NULL[^"]*"', content)
            if m:
                for x in m:
                    print(f"  STILL HAS: {x} in {name}")
print("Verify done")
