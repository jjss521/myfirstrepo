"""
设备材料表生成器 — 从负荷计算数据生成设备材料清单

特性：
  * 独立模块，可被 docx_generator 和 GUI 共同调用
  * 按工程类型配置默认设备类型
  * 返回结构化数据（dict），支持预览和 docx 两种输出
"""
import math
from typing import Dict, Any, List, Tuple


# 各工程类型的默认设备类型
DEFAULT_EQUIPMENT_TYPES: Dict[str, List[Dict[str, Any]]] = {
    'water_supply': [
        {'name': '干式变压器', 'spec_pattern': 'SCB14-{tx_cap}/10±2×2.5%/0.4kV D,yn11', 'unit': '台',
         'qty_fn': 'tx_count', 'note': '含温控、风机，IP20'},
        {'name': '10kV 中置式开关柜', 'spec_pattern': 'KYN28A-12', 'unit': '台',
         'qty_fn': 'hv_count', 'note': '含微机综合保护装置'},
        {'name': '低压抽出式开关柜', 'spec_pattern': 'MNS 0.4kV', 'unit': '台',
         'qty_fn': 'lv_count', 'note': '含智能多功能仪表'},
        {'name': '电容补偿柜', 'spec_pattern': '{qc_comp:.0f}kvar 智能型', 'unit': '套',
         'qty_fn': 'cap_count', 'note': '自动投切，含谐波抑制'},
        {'name': '10kV 电力电缆', 'spec_pattern': 'YJV-8.7/15kV', 'unit': 'm',
         'qty_fn': 'cable_hv', 'note': '各规格，以施工图为准'},
        {'name': '低压电力电缆', 'spec_pattern': 'YJV-0.6/1kV', 'unit': 'm',
         'qty_fn': 'cable_lv', 'note': '各规格，以施工图为准'},
        {'name': '控制电缆', 'spec_pattern': 'KVVP-450/750V', 'unit': 'm',
         'qty_fn': 'cable_ctrl', 'note': '各芯数'},
        {'name': 'PLC 控制柜', 'spec_pattern': '含 CPU、I/O、触摸屏', 'unit': '套',
         'qty_fn': 'plc_count', 'note': '含控制程序编制'},
        {'name': '在线检测仪表', 'spec_pattern': '流量/液位/压力/水质分析', 'unit': '套',
         'qty_fn': 'inst_count', 'note': '按工艺要求配置'},
        {'name': '工业电视监控系统', 'spec_pattern': '200 万像素高清 IP 摄像机', 'unit': '套',
         'qty_fn': 'cctv_count', 'note': '含 NVR、交换机、线缆'},
    ],
    'drainage': [
        {'name': '干式变压器', 'spec_pattern': 'SCB14-{tx_cap}/10±2×2.5%/0.4kV D,yn11', 'unit': '台',
         'qty_fn': 'tx_count', 'note': '含温控、风机，IP20'},
        {'name': '10kV 中置式开关柜', 'spec_pattern': 'KYN28A-12', 'unit': '台',
         'qty_fn': 'hv_count', 'note': '含微机综合保护装置'},
        {'name': '低压抽出式开关柜', 'spec_pattern': 'MNS 0.4kV', 'unit': '台',
         'qty_fn': 'lv_count', 'note': '含智能多功能仪表'},
        {'name': '电容补偿柜', 'spec_pattern': '{qc_comp:.0f}kvar 智能型', 'unit': '套',
         'qty_fn': 'cap_count', 'note': '自动投切，含谐波抑制'},
        {'name': '10kV 电力电缆', 'spec_pattern': 'YJV-8.7/15kV', 'unit': 'm',
         'qty_fn': 'cable_hv', 'note': '各规格，以施工图为准'},
        {'name': '低压电力电缆', 'spec_pattern': 'YJV-0.6/1kV', 'unit': 'm',
         'qty_fn': 'cable_lv', 'note': '各规格，以施工图为准'},
        {'name': '控制电缆', 'spec_pattern': 'KVVP-450/750V', 'unit': 'm',
         'qty_fn': 'cable_ctrl', 'note': '各芯数'},
        {'name': 'PLC 控制柜', 'spec_pattern': '含 CPU、I/O、触摸屏', 'unit': '套',
         'qty_fn': 'plc_count', 'note': '含控制程序编制'},
        {'name': '在线检测仪表', 'spec_pattern': '流量/液位/压力/水质分析', 'unit': '套',
         'qty_fn': 'inst_count', 'note': '按工艺要求配置'},
        {'name': '工业电视监控系统', 'spec_pattern': '200 万像素高清 IP 摄像机', 'unit': '套',
         'qty_fn': 'cctv_count', 'note': '含 NVR、交换机、线缆'},
        {'name': '除臭设备配电箱', 'spec_pattern': '非标定制', 'unit': '台',
         'qty_fn': 'deodor_count', 'note': '按除臭工艺分区配置'},
    ],
    'road': [
        {'name': '照明配电箱', 'spec_pattern': 'XL-21 型', 'unit': '台',
         'qty_fn': 'road_lv_count', 'note': '含智能路灯控制器'},
        {'name': '路灯（LED）', 'spec_pattern': 'LED 100W, 9m 灯杆', 'unit': '套',
         'qty_fn': 'road_light_count', 'note': '含基础、接地'},
        {'name': '低压电力电缆', 'spec_pattern': 'YJV-0.6/1kV', 'unit': 'm',
         'qty_fn': 'cable_lv', 'note': '各规格，以施工图为准'},
        {'name': '交通信号控制机', 'spec_pattern': 'SAT-2000 型', 'unit': '台',
         'qty_fn': 'signal_count', 'note': '含无线通信模块'},
        {'name': '交通监控摄像机', 'spec_pattern': '200 万像素网络球机', 'unit': '套',
         'qty_fn': 'cctv_count', 'note': '含立杆、基础'},
        {'name': '通信光缆', 'spec_pattern': 'GYTA-24B1.3', 'unit': 'km',
         'qty_fn': 'fiber_count', 'note': '沿电缆沟敷设'},
    ],
    'sanitation': [
        {'name': '干式变压器', 'spec_pattern': 'SCB14-{tx_cap}/10±2×2.5%/0.4kV D,yn11', 'unit': '台',
         'qty_fn': 'tx_count', 'note': '含温控、风机，IP20'},
        {'name': '10kV 中置式开关柜', 'spec_pattern': 'KYN28A-12', 'unit': '台',
         'qty_fn': 'hv_count', 'note': '含微机综合保护装置'},
        {'name': '低压抽出式开关柜', 'spec_pattern': 'MNS 0.4kV', 'unit': '台',
         'qty_fn': 'lv_count', 'note': '含智能多功能仪表'},
        {'name': '电容补偿柜', 'spec_pattern': '{qc_comp:.0f}kvar 智能型', 'unit': '套',
         'qty_fn': 'cap_count', 'note': '自动投切，含谐波抑制'},
        {'name': '10kV 电力电缆', 'spec_pattern': 'YJV-8.7/15kV', 'unit': 'm',
         'qty_fn': 'cable_hv', 'note': '各规格，以施工图为准'},
        {'name': '低压电力电缆', 'spec_pattern': 'YJV-0.6/1kV', 'unit': 'm',
         'qty_fn': 'cable_lv', 'note': '各规格，以施工图为准'},
        {'name': '控制电缆', 'spec_pattern': 'KVVP-450/750V', 'unit': 'm',
         'qty_fn': 'cable_ctrl', 'note': '各芯数'},
        {'name': 'PLC 控制柜', 'spec_pattern': '含 CPU、I/O、触摸屏', 'unit': '套',
         'qty_fn': 'plc_count', 'note': '含控制程序编制，防爆型'},
        {'name': '在线检测仪表', 'spec_pattern': '流量/液位/压力/气体分析', 'unit': '套',
         'qty_fn': 'inst_count', 'note': '按工艺要求配置，含防爆型'},
        {'name': '工业电视监控系统', 'spec_pattern': '200 万像素高清 IP 摄像机', 'unit': '套',
         'qty_fn': 'cctv_count', 'note': '含 NVR、交换机、线缆，防爆型'},
        {'name': '除臭/气体检测系统', 'spec_pattern': '气体探测器+控制主机', 'unit': '套',
         'qty_fn': 'gas_detect_count', 'note': '按填埋气/焚烧工艺配置'},
    ],
}


class EquipmentTableGenerator:
    """设备材料表生成器"""

    def __init__(self):
        self._custom_types: Dict[str, List[Dict[str, Any]]] = {}

    def get_available_types(self, project_type: str) -> List[Dict[str, Any]]:
        """获取指定工程类型的可用设备类型列表"""
        if project_type in self._custom_types:
            return self._custom_types[project_type]
        return DEFAULT_EQUIPMENT_TYPES.get(project_type, DEFAULT_EQUIPMENT_TYPES.get('water_supply', []))

    def set_custom_types(self, project_type: str, types: List[Dict[str, Any]]) -> None:
        """设置自定义设备类型列表"""
        self._custom_types[project_type] = types

    def generate(self, project_type: str, summary: Dict[str, Any],
                 area_summaries: List[Dict[str, Any]] = None,
                 design_stage: str = "可行性研究",
                 selected_indices: List[int] = None) -> Dict[str, Any]:
        """生成设备材料表数据

        Returns:
            dict with keys:
                - headers: List[str] 表头
                - rows: List[List[str]] 数据行
                - raw_items: List[dict] 原始条目数据
                - has_data: bool 是否有数据
        """
        area_summaries = area_summaries or []
        tx_config = summary.get('recommended_transformer', '')
        qc_comp = summary.get('qc_compensation', 0)
        total_equip = summary.get('total_equip_power', 0)
        area_count = len(area_summaries) or summary.get('area_count', 2)

        # 计算数量
        is_feasibility = '可行' in design_stage
        tx_count, tx_cap = self._parse_tx_detail(tx_config)
        hv_count = 3 + min(area_count, 6) if is_feasibility else 5 + min(area_count, 8)
        lv_count = 2 + min(area_count, 6) if is_feasibility else 2 + min(area_count, 10)
        cap_count = max(1, math.ceil(qc_comp / 150))
        # 长度估算（初设更精确）
        length_factor = 1.0 if is_feasibility else 1.3
        cable_hv = max(100, int(total_equip * 0.8 * length_factor))
        cable_lv = max(200, int(total_equip * 2.0 * length_factor))
        cable_ctrl = max(150, int(total_equip * 1.0 * length_factor))
        plc_count = max(1, math.ceil(area_count / 2))
        inst_count = max(8, area_count * 4)
        cctv_count = max(3, area_count + 3)
        # 工程特定
        deodor_count = max(2, area_count)
        road_lv_count = max(2, area_count)
        road_light_count = max(10, area_count * 20)
        signal_count = max(2, area_count)
        fiber_count = max(1, area_count)
        gas_detect_count = max(4, area_count * 3)

        # 数量映射
        qty_map = {
            'tx_count': tx_count, 'hv_count': hv_count, 'lv_count': lv_count,
            'cap_count': cap_count, 'cable_hv': cable_hv, 'cable_lv': cable_lv,
            'cable_ctrl': cable_ctrl, 'plc_count': plc_count,
            'inst_count': inst_count, 'cctv_count': cctv_count,
            'deodor_count': deodor_count, 'road_lv_count': road_lv_count,
            'road_light_count': road_light_count, 'signal_count': signal_count,
            'fiber_count': fiber_count, 'gas_detect_count': gas_detect_count,
        }
        # spec 模板所需参数
        spec_params = {'tx_cap': tx_cap, 'qc_comp': qc_comp}

        equipment_types = self.get_available_types(project_type)
        if selected_indices:
            equipment_types = [equipment_types[i] for i in selected_indices if i < len(equipment_types)]

        headers = ['序号', '名称', '规格型号', '单位', '数量', '备注']
        raw_items = []
        rows = []

        for idx, eq in enumerate(equipment_types):
            qty = qty_map.get(eq['qty_fn'], 1)
            spec = eq['spec_pattern'].format(**spec_params) if '{' in eq['spec_pattern'] else eq['spec_pattern']
            raw_items.append({
                'name': eq['name'],
                'spec': spec,
                'unit': eq['unit'],
                'qty': qty,
                'note': eq['note'],
            })
            rows.append([
                str(idx + 1), eq['name'], spec, eq['unit'], str(qty), eq['note'],
            ])

        return {
            'headers': headers,
            'rows': rows,
            'raw_items': raw_items,
            'has_data': len(rows) > 0,
            'note': '注：以下设备材料根据负荷计算结果及类似工程经验估算，具体规格、数量以施工图为准。',
        }

    @staticmethod
    def _parse_tx_detail(tx_config: str) -> Tuple[int, int]:
        """从变压器配置字符串解析台数和容量"""
        if not tx_config:
            return 2, 800
        # 格式: "2×800kVA" 或 "2x800" 或 "800kVA"
        import re
        m = re.match(r'(\d+)\s*[×x]\s*(\d+)', str(tx_config))
        if m:
            return int(m.group(1)), int(m.group(2))
        m = re.match(r'(\d+)', str(tx_config))
        if m:
            return 2, int(m.group(1))
        return 2, 800

    def to_text(self, result: Dict[str, Any]) -> str:
        """将生成结果格式化为文本（用于GUI预览）"""
        lines = ['主要设备材料表', '─' * 60]
        lines.append(result.get('note', ''))
        lines.append('')
        headers = result['headers']
        lines.append(' | '.join(h.center(8) for h in headers))
        lines.append('─' * 60)
        for row in result['rows']:
            lines.append(' | '.join(cell.ljust(8) for cell in row))
        lines.append('─' * 60)
        return '\n'.join(lines)
