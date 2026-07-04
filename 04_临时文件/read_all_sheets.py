import xlrd

path = r"d:\qoderwork\load_calc.xls"
outfile = r"d:\qoderwork\excel_full.txt"

wb = xlrd.open_workbook(path)
with open(outfile, 'w', encoding='utf-8') as f:
    f.write(f"Sheets: {wb.sheet_names()}\n\n")
    for sname in wb.sheet_names():
        sh = wb.sheet_by_name(sname)
        f.write(f"\n{'='*80}\n=== Sheet: {sname} === (Rows:{sh.nrows}, Cols:{sh.ncols})\n{'='*80}\n")
        for r in range(sh.nrows):
            row = []
            for c in range(sh.ncols):
                val = sh.cell_value(r, c)
                if val != '':
                    row.append(f"[{c}]{val}")
            if row:
                f.write(f"R{r}: {' | '.join(row)}\n")
            else:
                f.write(f"R{r}: (empty)\n")
print("Done")
