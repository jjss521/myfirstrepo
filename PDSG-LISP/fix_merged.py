import os

src = r"D:\qoderwork\PDSG-LISP\PDSG.lsp"

with open(src, "r", encoding="utf-8") as f:
    content = f.read()

# Remove the init code at the end
marker = "(pdsg-init-default-catalog)"
idx = content.find(marker)
if idx > 0:
    content = content[:idx].rstrip()

# Add simple loading message
content += "\n\n(princ)\n"
content += '(princ "\\n[PDSG-LISP v1.0.0] 输入 PDSG_UI 打开界面")\n'
content += "(princ)\n"

with open(src, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Done. Size: {len(content)} bytes")

# Verify balance
opens = content.count("(")
closes = content.count(")")
print(f"Parens: {opens} open, {closes} close, balance={opens-closes}")
