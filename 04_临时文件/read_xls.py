import xlrd

path = r"d:\qoderwork\load_calc.xls"
outfile = r"d:\qoderwork\excel_data.txt"

wb = xlrd.open_workbook(path)

with open(outfile, 'w', encoding='utf-8') as f:
    f.write("Sheets: " + str(wb.sheet_names()) + "\n\n")
    for sname in wb.sheet_names():
        sh = wb.sheet_by_name(sname)
        f.write("\n" + "="*80 + "\n")
        f.write("=== Sheet: " + sname + " === (Rows:" + str(sh.nrows) + ", Cols:" + str(sh.ncols) + ")\n")
        f.write("="*80 + "\n")
        for r in range(sh.nrows):
            row_data = []
            for c in range(sh.ncols):
                val = sh.cell_value(r, c)
                if val != '':
                    row_data.append("[" + str(c) + "]" + str(val))
            if row_data:
                f.write("R" + str(r) + ": " + " | ".join(row_data) + "\n")
            else:
                f.write("R" + str(r) + ": (empty)\n")

print("Done. Output written to " + outfile)
