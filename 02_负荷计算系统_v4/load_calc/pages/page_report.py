# -*- coding: utf-8 -*-
"""报表导出页面 - Apple 简约优雅风格"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import datetime

from ..calc_engine import calc_subsystem_summary, calc_hv_system_summary, format_number
from ..widgets import CardFrame
from ..config import APP_NAME, THEME, blend_color, FONT_UI, FONT_DISPLAY, FONT_MONO, FS
from ..excel_exporter import export_to_excel


class ReportPage(ttk.Frame):
    """报表导出页面"""
    def __init__(self, master, hv_system=None, **kwargs):
        super().__init__(master, **kwargs)
        self.hv_system = hv_system
        self._create_widgets()

    def set_hv_system(self, hv_system):
        self.hv_system = hv_system
        self.refresh()

    def _create_widgets(self):
        # 标题
        title_frame = tk.Frame(self, bg=THEME["BG_MAIN"])
        title_frame.pack(fill="x", padx=20, pady=(15, 10))
        accent = tk.Frame(title_frame, bg=THEME["ACCENT_PURPLE"], width=4, height=24)
        accent.pack(side="left", padx=(0, 10))
        tk.Label(title_frame, text="报表生成与导出",
                 font=(FONT_DISPLAY, FS[18], "bold"),
                 fg=THEME["ACCENT_PURPLE"], bg=THEME["BG_MAIN"]).pack(side="left")

        # 按钮区域
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=20, pady=(0, 15))

        ttk.Button(btn_frame, text="📋 生成计算报告",
                   command=self._generate_report,
                   width=20).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="💾 导出为TXT",
                   command=self._export_txt,
                   width=20).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="📊 生成设备清单",
                   command=self._generate_equipment_list,
                   width=20).pack(side="left", padx=5)
        # 导出格式选择
        ttk.Label(btn_frame, text="导出格式:",
                  font=(FONT_UI, FS[9])).pack(side="left", padx=(20, 2))
        self._export_mode_var = tk.StringVar(value="详细表（含设备明细）")
        self._export_mode_combo = ttk.Combobox(btn_frame,
            textvariable=self._export_mode_var,
            values=["详细表（含设备明细）", "一览表（仅汇总）"],
            font=(FONT_UI, FS[9]), state="readonly", width=22)
        self._export_mode_combo.pack(side="left", padx=2)

        ttk.Button(btn_frame, text="📗 导出为Excel",
                   command=self._export_excel,
                   width=16).pack(side="left", padx=5)

        # 预览区域
        preview_frame = CardFrame(self, "报表预览", padding=10)
        preview_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        self.preview = tk.Text(preview_frame, font=(FONT_MONO, FS[9]),
                               bg=THEME["BG_CARD"], fg=THEME["FG_PRIMARY"],
                               insertbackground=THEME["ACCENT_BLUE"],
                               selectbackground=THEME["BG_ACTIVE"],
                               wrap="word", relief="flat", padx=10, pady=10,
                               highlightbackground=THEME["BORDER"],
                               highlightthickness=1)
        self.preview.pack(fill="both", expand=True)

        # 滚动条
        scrollbar = ttk.Scrollbar(self.preview, orient="vertical",
                                  command=self.preview.yview)
        self.preview.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

    def _generate_report(self):
        if not self.hv_system:
            messagebox.showwarning("提示", "请先加载数据")
            return
        report = self._build_report_text()
        self.preview.delete("1.0", "end")
        self.preview.insert("1.0", report)

    def _build_report_text(self) -> str:
        hv = self.hv_system
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        summary = calc_hv_system_summary(hv)

        lines = []
        lines.append("=" * 70)
        lines.append(f"  {APP_NAME}")
        lines.append(f"  报告生成时间: {now}")
        lines.append("=" * 70)
        lines.append("")

        lines.append("一、10kV高压系统总负荷")
        lines.append("-" * 50)
        lines.append(f"  总有功功率 Pc     = {hv.total_pc:>10.2f} kW")
        lines.append(f"  总无功功率 Qc     = {hv.total_qc:>10.2f} kvar")
        lines.append(f"  总视在功率 Sc     = {hv.total_sc:>10.2f} kVA")
        lines.append(f"  功率因数 cosφ     = {hv.power_factor:>10.4f}")
        lines.append("")

        for i, sub in enumerate(hv.subsystems):
            sm = summary["subsystems"][i]["summary"]
            lines.append(f"\n二、{sub.name}")
            lines.append("-" * 50)

            lines.append(f"\n  【补偿前】")
            lines.append(f"    有功功率 Pc   = {sm['pc']:>10.2f} kW")
            lines.append(f"    无功功率 Qc   = {sm['qc']:>10.2f} kvar")
            lines.append(f"    视在功率 Sc   = {sm['sc']:>10.2f} kVA")
            lines.append(f"    功率因数      = {sm['pf_before']:>10.4f}")

            lines.append(f"\n  【无功补偿】")
            lines.append(f"    需要补偿容量  = {sm['required_qc']:>10.2f} kvar")
            lines.append(f"    实际补偿容量  = {sm['actual_qc']:>10.0f} kvar")
            lines.append(f"    补偿后功率因数 = {sm['pf_after']:>10.4f}")

            lines.append(f"\n  【变压器】")
            lines.append(f"    变压器配置    = {int(sub.transformer_rating)}kVA × {sub.transformer_count}")
            lines.append(f"    变压器总容量  = {sm['transformer_capacity']:>10.0f} kVA")
            lines.append(f"    变压器负载率  = {sm['load_rate']*100:>10.2f}%")
            lines.append(f"    有功损耗 ΔP   = {sm['transformer_loss_p']:>10.2f} kW")
            lines.append(f"    无功损耗 ΔQ   = {sm['transformer_loss_q']:>10.2f} kvar")

            lines.append(f"\n  【10kV侧负荷】")
            lines.append(f"    有功功率 Pc   = {sm['hv_pc']:>10.2f} kW")
            lines.append(f"    无功功率 Qc   = {sm['hv_qc']:>10.2f} kvar")
            lines.append(f"    视在功率 Sc   = {sm['hv_sc']:>10.2f} kVA")
            lines.append(f"    功率因数      = {sm['hv_pf']:>10.4f}")
            lines.append("")

            lines.append(f"\n  【设备组明细】")
            for g in sub.groups:
                lines.append(f"    {g.name}:")
                lines.append(f"      Pe={g.total_device_power:.1f}kW  "
                            f"∑Pc={g.subtotal_pc:.2f}kW  "
                            f"Pc={g.computed_pc:.2f}kW  "
                            f"Qc={g.computed_qc:.2f}kvar  "
                            f"Sc={g.computed_sc:.2f}kVA  "
                            f"cosφ={g.power_factor:.3f}")

        lines.append("\n" + "=" * 70)
        lines.append("  【计算说明】")
        lines.append("  • 采用需要系数法（Kx法）计算")
        lines.append("  • 380V侧功率因数补偿至0.95以上")
        lines.append("  • 变压器损耗按有功1%、无功5%估算")
        lines.append("=" * 70)

        return "\n".join(lines)

    def _export_txt(self):
        if not self.hv_system:
            messagebox.showwarning("提示", "请先加载数据")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="导出计算报告"
        )
        if not file_path:
            return
        try:
            report = self._build_report_text()
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(report)
            messagebox.showinfo("成功", f"报告已导出到:\n{file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")

    def _generate_equipment_list(self):
        if not self.hv_system:
            messagebox.showwarning("提示", "请先加载数据")
            return
        lines = []
        lines.append("=" * 80)
        lines.append(f"  设备清单 - {datetime.datetime.now().strftime('%Y-%m-%d')}")
        lines.append("=" * 80)
        lines.append(f"{'系统':<20} {'设备组':<16} {'设备名称':<20} {'Pe(kW)':<10} {'Kx':<6} {'Pc(kW)':<10}")
        lines.append("-" * 80)

        for sub in self.hv_system.subsystems:
            for g in sub.groups:
                for eq in g.equipment_list:
                    if eq.is_subtotal:
                        continue
                    lines.append(f"{sub.name[:18]:<20} {g.name[:14]:<16} "
                                f"{eq.name[:18]:<20} {eq.rated_power:<8.1f}  "
                                f"{eq.kx:<.2f}    {eq.pc:<8.2f}")

        text = "\n".join(lines)
        self.preview.delete("1.0", "end")
        self.preview.insert("1.0", text)

    def refresh(self):
        pass  # 报表页面不自动刷新

    def _export_excel(self):
        """导出为格式化的Excel文件"""
        if not self.hv_system:
            messagebox.showwarning("提示", "请先加载数据")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")],
            title="导出负荷计算Excel报表",
            initialfile="负荷计算表.xlsx",
        )
        if not file_path:
            return

        # 确定导出模式
        mode_map = {
            "详细表（含设备明细）": "detailed",
            "一览表（仅汇总）": "summary",
        }
        mode = mode_map.get(self._export_mode_var.get(), "detailed")

        try:
            export_to_excel(self.hv_system, file_path, mode=mode)
            messagebox.showinfo("导出成功",
                               f"Excel报表已导出到:\n{file_path}")
            # 在预览中显示提示
            self.preview.delete("1.0", "end")
            if mode == "summary":
                self.preview.insert("1.0",
                    f"✅ 一览表已成功导出\n\n"
                    f"文件路径: {file_path}\n\n"
                    f"包含工作表:\n"
                    f"  · 各系统汇总\n"
                    f"  · 总10kV负荷计算表\n")
            else:
                self.preview.insert("1.0",
                    f"✅ 详细表已成功导出\n\n"
                    f"文件路径: {file_path}\n\n"
                    f"包含工作表:\n")
                for sub in self.hv_system.subsystems:
                    self.preview.insert("end",
                        f"  · {sub.name} — 0.4kV负荷计算表\n")
                self.preview.insert("end",
                    "  · 设备明细清单\n"
                    "  · 总10kV负荷计算表\n")
        except ImportError:
            messagebox.showerror("导出失败",
                               "请先安装 openpyxl 库:\n"
                               "pip install openpyxl")
        except Exception as e:
            messagebox.showerror("导出失败", f"{str(e)}")
