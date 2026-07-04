import xlrd
import traceback

path = r"d:\qoderwork\load_calc.xls"
outfile = r"d:\qoderwork\excel_output.txt"

try:
    wb = xlrd.open_workbook(path, formatting_info=False)
    with open(outfile, 'w', encoding='utf-8') as f:
        f.write(f"Sheets: {wb.sheet_names()}\n\n")
        for sname in wb.sheet_names():
            f.write(f"\n=== Sheet: {sname} ===\n")
            sh = wb.sheet_by_name(sname)
            f.write(f"Rows: {sh.nrows}, Cols: {sh.ncols}\n")
            for r in range(min(sh.nrows, 100)):
                row = []
                for c in range(sh.ncols):
                    cell = sh.cell(r, c)
                    val = cell.value
                    ctype = cell.ctype
                    if val != '' and ctype != 0:  # not empty and not blank
                        row.append(f"[{c}](t{ctype}){val}")
                if row:
                    f.write(f"R{r}: {' | '.join(row)}\n")
    print("Done")
except Exception as e:
    with open(outfile, 'w', encoding='utf-8') as f:
        f.write(traceback.format_exc())
    print("Error:", e)
