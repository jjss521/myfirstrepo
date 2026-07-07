#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 文件读取工具 - 提取文本内容供 AI 学习使用
用法: python read_pdf.py "文件路径.pdf" "输出路径.txt"
"""
import sys
import pdfplumber

def extract_pdf(pdf_path, output_path=None):
    """从 PDF 提取全部文本"""
    if output_path is None:
        output_path = pdf_path.rsplit('.', 1)[0] + '.txt'
    
    full_text = []
    with pdfplumber.open(pdf_path) as pdf:
        print(f"共 {len(pdf.pages)} 页")
        for i, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            if text.strip():
                full_text.append(f"\n=== 第 {i} 页 ===\n")
                full_text.append(text)
            print(f"  已处理第 {i} 页, 提取 {len(text)} 字符")
    
    result = "".join(full_text)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result)
    
    print(f"\n完成! 共提取 {len(result)} 字符")
    print(f"已保存到: {output_path}")
    return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python read_pdf.py <pdf文件路径> [输出txt路径]")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    extract_pdf(pdf_path, output_path)
