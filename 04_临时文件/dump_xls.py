import xlrd
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

path = r"d:\qoderwork\load_calc.xls"
wb = xlrd.open_workbook(path)

for sname in wb.sheet_names():
    sh = wb.sheet_by_name(sname)
    print("=" * 60)
    print("SHEET:", sname, "Rows:", sh.nrows, "Cols:", sh.ncols)
    print("=" * 60)
    for r in range(sh.nrows):
        row_data = []
        for c in range(sh.ncols):
            val = sh.cell_value(r, c)
            if val != '':
                row_data.append("[" + str(c) + "]" + str(val))
        if row_data:
            print("R" + str(r) + ":", " | ".join(row_data))
    print()
