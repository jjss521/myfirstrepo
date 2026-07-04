# -*- coding: utf-8 -*-
"""预设数据加载器 - 从Excel提取的数据"""

from .models import (
    Equipment, EquipmentGroup, Subsystem, HVSystem, VoltageLevel
)


def build_project_data() -> HVSystem:
    """构建完整的项目数据"""
    hv = HVSystem("二期全厂10KV负荷")

    # ===== 1#配电系统 380V =====
    dist1 = Subsystem("水厂二期1#配电系统380V负荷", voltage=VoltageLevel.LV_380V)
    dist1.transformer_rating = 1250
    dist1.transformer_count = 2
    dist1.target_power_factor = 0.95
    _build_dist1(dist1)
    hv.add_subsystem(dist1)

    # ===== 2#配电系统(蒸发系统) 380V =====
    dist2 = Subsystem("水厂二期2#配电系统(蒸发系统)380V负荷", voltage=VoltageLevel.LV_380V)
    dist2.transformer_rating = 2000
    dist2.transformer_count = 2
    dist2.target_power_factor = 0.95
    _build_dist2(dist2)
    hv.add_subsystem(dist2)

    return hv


def _build_dist1(sys: Subsystem):
    """构建1#配电系统数据"""

    # -- 一体化进水泵站 --
    g1 = EquipmentGroup("一体化进水泵站")
    g1.kp = 0.9
    g1.kq = 0.95
    g1.add_equipment(Equipment("进水泵", 37, 3, 2, 0.9, 0.8, 0.75))
    g1.add_equipment(Equipment("粉碎格栅", 3.7, 1, 1, 0.9, 0.8, 0.75))
    g1.add_equipment(Equipment("自控仪表", 1.0, 1, 1, 0.8, 0.7, 1.02))
    g1.add_equipment(Equipment("用电设备组计算负荷", is_subtotal=True,
                                rated_power=78.7, kx=1, cos_phi=0.8, tan_phi=0.75))
    sys.add_group(g1)

    # -- 三组生化池 --
    g2 = EquipmentGroup("三组生化池")
    g2.kp = 0.9
    g2.kq = 0.95
    for i in range(1, 4):
        g2.add_equipment(Equipment(f"{i}#生物池-回流泵", 6.0, 4, 3, 0.8, 0.8, 0.75))
        g2.add_equipment(Equipment(f"{i}#生物池-搅拌器", 2.75, 6, 6, 0.8, 0.8, 0.75))
        g2.add_equipment(Equipment(f"{i}#生物池-搅拌机", 1.5, 4, 4, 0.8, 0.8, 0.75))
        g2.add_equipment(Equipment(f"{i}#生物池-电动蝴蝶", 0.75, 6, 6, 0.5, 0.8, 0.75))
        g2.add_equipment(Equipment(f"{i}#生物池-电动闸门_small", 0.55, 6, 6, 0.2, 0.8, 0.75))
        g2.add_equipment(Equipment(f"{i}#生物池-电动闸门_large", 1.5, 2, 2, 0.2, 0.8, 0.75))
    sys.add_group(g2)

    # -- MBR膜池 --
    g3 = EquipmentGroup("三组MBR膜池")
    g3.kp = 0.9
    g3.kq = 0.95
    for i in range(1, 4):
        g3.add_equipment(Equipment(f"{i}#MBR膜池-产水泵", 4.0, 5, 4, 0.8, 0.8, 0.75))
        g3.add_equipment(Equipment(f"{i}#MBR膜池-CIP泵", 5.5, 2, 1, 0.8, 0.8, 0.75))
        g3.add_equipment(Equipment(f"{i}#MBR膜池-剩余污泥泵", 4.0, 2, 1, 0.8, 0.8, 0.75))
        g3.add_equipment(Equipment(f"{i}#MBR膜池-排空泵", 7.5, 2, 1, 0.8, 0.8, 0.75))
        g3.add_equipment(Equipment(f"{i}#MBR膜池-调节闸门", 0.75, 4, 4, 0.2, 0.8, 0.75))
        g3.add_equipment(Equipment(f"{i}#MBR膜池-方闸门", 0.75, 4, 4, 0.2, 0.8, 0.75))
        g3.add_equipment(Equipment(f"{i}#MBR膜池-电动葫芦_large", 12.0, 1, 1, 0.2, 0.8, 0.75))
        g3.add_equipment(Equipment(f"{i}#MBR膜池-电动葫芦_small", 5.0, 1, 1, 0.2, 0.8, 0.75))
        g3.add_equipment(Equipment(f"{i}#MBR膜池-潜水泵", 0.55, 2, 1, 0.2, 0.8, 0.75))
        g3.add_equipment(Equipment(f"{i}#MBR膜池-液环真空泵", 1.5, 2, 1, 0.5, 0.8, 0.75))
        g3.add_equipment(Equipment(f"{i}#MBR膜池-照明", 5.0, 1, 1, 0.2, 0.7, 1.02))
    sys.add_group(g3)

    # -- 常规水调节池及事故池 --
    g4 = EquipmentGroup("常规水调节池及事故池")
    g4.kp = 0.9
    g4.kq = 0.95
    g4.add_equipment(Equipment("耐腐蚀泵", 15.0, 5, 4, 0.9, 0.9, 0.4843))
    g4.add_equipment(Equipment("双曲面搅拌器", 4.0, 12, 12, 0.9, 0.8, 0.75))
    g4.add_equipment(Equipment("潜污泵", 0.75, 1, 1, 0.3, 0.8, 0.75))
    g4.add_equipment(Equipment("轴流风机", 0.18, 2, 2, 0.7, 0.8, 0.75))
    g4.add_equipment(Equipment("电动闸门", 0.55, 2, 2, 0.2, 0.8, 0.75))
    g4.add_equipment(Equipment("电动葫芦", 1.7, 1, 1, 0.2, 0.5, 1.732))
    g4.add_equipment(Equipment("照明", 2.5, 1, 1, 0.8, 0.9, 0.4843))
    g4.add_equipment(Equipment("自控仪表", 5.0, 1, 1, 0.9, 0.7, 1.02))
    sys.add_group(g4)

    # -- 常规水混凝沉淀池 --
    g5 = EquipmentGroup("常规水混凝沉淀池")
    g5.kp = 0.9
    g5.kq = 0.95
    g5.add_equipment(Equipment("机械搅拌混合器_4kW", 4.0, 4, 4, 0.8, 0.9, 0.4843))
    g5.add_equipment(Equipment("机械搅拌混合器_3kW", 3.0, 4, 4, 0.8, 0.9, 0.4843))
    g5.add_equipment(Equipment("反应搅拌器_0.2kW", 0.2, 4, 4, 0.8, 0.9, 0.4843))
    g5.add_equipment(Equipment("反应搅拌器_0.1kW", 0.1, 4, 4, 0.8, 0.9, 0.4843))
    g5.add_equipment(Equipment("刮泥机", 0.37, 4, 4, 0.8, 0.8, 0.75))
    g5.add_equipment(Equipment("潜污泵", 2.2, 16, 16, 0.8, 0.9, 0.4843))
    g5.add_equipment(Equipment("电动闸门", 0.55, 20, 20, 0.2, 0.8, 0.75))
    g5.add_equipment(Equipment("照明", 6.0, 1, 1, 0.8, 0.9, 0.4843))
    g5.add_equipment(Equipment("自控仪表", 5.0, 1, 1, 0.9, 0.7, 1.02))
    sys.add_group(g5)

    # -- 高盐水调节池及事故池 --
    g6 = EquipmentGroup("高盐水调节池及事故池")
    g6.kp = 0.9
    g6.kq = 0.95
    g6.add_equipment(Equipment("耐腐蚀泵", 11.0, 5, 4, 0.9, 0.9, 0.4843))
    g6.add_equipment(Equipment("双曲面搅拌器", 4.0, 6, 6, 0.9, 0.8, 0.75))
    g6.add_equipment(Equipment("潜污泵", 0.75, 1, 1, 0.3, 0.8, 0.75))
    g6.add_equipment(Equipment("轴流风机", 0.18, 2, 2, 0.7, 0.8, 0.75))
    g6.add_equipment(Equipment("电动闸门", 0.55, 2, 2, 0.2, 0.8, 0.75))
    g6.add_equipment(Equipment("电动葫芦", 1.7, 1, 1, 0.2, 0.5, 1.732))
    g6.add_equipment(Equipment("照明", 2.5, 1, 1, 0.8, 0.9, 0.4843))
    g6.add_equipment(Equipment("自控仪表", 5.0, 1, 1, 0.9, 0.7, 1.02))
    sys.add_group(g6)

    # -- 高盐水中和池及混凝沉淀池 --
    g7 = EquipmentGroup("高盐水中和池及混凝沉淀池")
    g7.kp = 0.9
    g7.kq = 0.95
    g7.add_equipment(Equipment("机械搅拌混合器_4kW", 4.0, 4, 4, 0.8, 0.9, 0.4843))
    g7.add_equipment(Equipment("机械搅拌混合器_3kW", 3.0, 2, 2, 0.8, 0.9, 0.4843))
    g7.add_equipment(Equipment("反应搅拌器_0.2kW", 0.2, 2, 2, 0.8, 0.9, 0.4843))
    g7.add_equipment(Equipment("反应搅拌器_0.1kW", 0.1, 2, 2, 0.8, 0.9, 0.4843))
    g7.add_equipment(Equipment("刮泥机", 0.37, 2, 2, 0.8, 0.8, 0.75))
    g7.add_equipment(Equipment("潜污泵", 2.2, 8, 8, 0.8, 0.9, 0.4843))
    g7.add_equipment(Equipment("电动闸门", 0.55, 10, 10, 0.2, 0.8, 0.75))
    g7.add_equipment(Equipment("照明", 6.0, 1, 1, 0.8, 0.9, 0.4843))
    g7.add_equipment(Equipment("自控仪表", 5.0, 1, 1, 0.9, 0.7, 1.02))
    sys.add_group(g7)

    # -- 综合水池 --
    g8 = EquipmentGroup("综合水池")
    g8.kp = 0.9
    g8.kq = 0.95
    g8.add_equipment(Equipment("高级氧化调节池搅拌器", 1.5, 1, 1, 0.9, 0.85, 0.62))
    g8.add_equipment(Equipment("高级氧化调节池离心泵", 4.0, 2, 1, 0.9, 0.85, 0.62))
    g8.add_equipment(Equipment("出水调节池离心泵", 22.0, 3, 2, 0.9, 0.85, 0.62))
    g8.add_equipment(Equipment("蒸发水池离心泵", 7.5, 2, 1, 0.9, 0.85, 0.62))
    g8.add_equipment(Equipment("中间水池离心泵", 7.5, 2, 1, 0.9, 0.85, 0.62))
    g8.add_equipment(Equipment("氢氧化钠池离心泵", 4.0, 3, 2, 0.9, 0.8, 0.75))
    g8.add_equipment(Equipment("氢氧化钠池计量泵", 0.37, 3, 2, 0.9, 0.8, 0.75))
    g8.add_equipment(Equipment("硫酸池离心泵", 4.0, 2, 1, 0.9, 0.8, 0.75))
    g8.add_equipment(Equipment("高压反渗透清洗泵", 30.0, 2, 2, 0.9, 0.85, 0.62))
    g8.add_equipment(Equipment("潜污泵", 0.75, 4, 3, 0.2, 0.85, 0.62))
    g8.add_equipment(Equipment("电动葫芦", 1.7, 2, 2, 0.2, 0.85, 0.62))
    g8.add_equipment(Equipment("取样泵", 0.75, 1, 1, 0.5, 0.85, 0.62))
    g8.add_equipment(Equipment("其他(含阀门、预留等)", 10.0, 1, 1, 0.9, 0.85, 0.62))
    sys.add_group(g8)

    # -- 加药间 --
    g9 = EquipmentGroup("加药间")
    g9.kp = 0.9
    g9.kq = 0.95
    g9.add_equipment(Equipment("碳酸钠投加系统", 24.0, 1, 1, 0.8, 0.8, 0.75))
    g9.add_equipment(Equipment("PAC加药系统", 7.0, 1, 1, 0.8, 0.8, 0.75))
    g9.add_equipment(Equipment("PAM投加系统", 16.0, 1, 1, 0.8, 0.8, 0.75))
    g9.add_equipment(Equipment("NaClO加药系统", 10.0, 1, 1, 0.8, 0.8, 0.75))
    g9.add_equipment(Equipment("NaOH加药系统", 7.0, 1, 1, 0.8, 0.8, 0.75))
    g9.add_equipment(Equipment("柠檬酸投加系统", 10.0, 1, 1, 0.8, 0.8, 0.75))
    g9.add_equipment(Equipment("轴流风机", 1.0, 1, 1, 0.7, 0.8, 0.75))
    g9.add_equipment(Equipment("增压泵", 3.0, 2, 1, 0.8, 0.8, 0.75))
    g9.add_equipment(Equipment("照明", 2.0, 1, 1, 0.8, 0.8, 0.75))
    sys.add_group(g9)

    # -- 鼓风机房风机 --
    g10 = EquipmentGroup("鼓风机房风机")
    g10.kp = 0.9
    g10.kq = 0.95
    g10.add_equipment(Equipment("鼓风机_37kW", 37.0, 8, 8, 0.8, 0.8, 0.75))
    g10.add_equipment(Equipment("鼓风机_44kW", 44.0, 8, 6, 0.8, 0.8, 0.75))
    sys.add_group(g10)

    # -- 排水池及鼓风机房辅助负荷 --
    g11 = EquipmentGroup("排水池及鼓风机房辅助负荷")
    g11.kp = 0.9
    g11.kq = 0.95
    g11.add_equipment(Equipment("排水池潜污泵", 7.5, 4, 4, 0.8, 0.8, 0.75))
    g11.add_equipment(Equipment("排水池潜水搅拌器", 5.5, 2, 2, 0.8, 0.8, 0.75))
    g11.add_equipment(Equipment("轴流风机", 1.0, 1, 1, 0.7, 0.8, 0.75))
    g11.add_equipment(Equipment("卷帘过滤器", 0.37, 2, 2, 0.8, 0.8, 0.75))
    g11.add_equipment(Equipment("照明", 3.0, 1, 1, 0.8, 0.7, 1.02))
    g11.add_equipment(Equipment("自控仪表", 4.0, 1, 1, 0.8, 0.7, 1.02))
    sys.add_group(g11)

    # -- MCR及芬顿系统 --
    g12 = EquipmentGroup("MCR及芬顿系统")
    g12.kp = 0.9
    g12.kq = 0.95
    # MCR系统
    g12.add_equipment(Equipment("MCR-反洗泵", 3.7, 2, 1, 0.5, 0.95, 0.3287))
    g12.add_equipment(Equipment("MCR-产水泵", 3.7, 2, 1, 0.8, 0.85, 0.6197))
    g12.add_equipment(Equipment("MCR-框式搅拌机", 3.0, 2, 2, 0.8, 0.85, 0.6197))
    g12.add_equipment(Equipment("MCR-排空泵", 15.0, 2, 1, 0.8, 0.85, 0.6197))
    g12.add_equipment(Equipment("MCR-电动起重机", 6.0, 1, 1, 0.3, 0.85, 0.6197))
    g12.add_equipment(Equipment("MCR-真空发生器", 4.0, 1, 1, 0.8, 0.85, 0.6197))
    g12.add_equipment(Equipment("MCR-PLC系统", 3.0, 1, 1, 0.8, 0.85, 0.6197))
    g12.add_equipment(Equipment("MCR-辅助设备", 5.0, 1, 1, 0.7, 0.85, 0.6197))
    g12.add_equipment(Equipment("MCR-风机", 1.5, 2, 2, 0.7, 0.85, 0.6197))
    # Fenton-FD系统
    g12.add_equipment(Equipment("Fenton-循环泵", 5.5, 3, 2, 0.8, 0.95, 0.3287))
    g12.add_equipment(Equipment("Fenton-污泥泵", 2.2, 2, 1, 0.8, 0.85, 0.6197))
    g12.add_equipment(Equipment("Fenton-框式搅拌机", 1.1, 1, 1, 0.8, 0.85, 0.6197))
    g12.add_equipment(Equipment("Fenton-PLC系统", 3.0, 1, 1, 0.8, 0.85, 0.6197))
    g12.add_equipment(Equipment("Fenton-辅助设备", 6.0, 1, 1, 0.7, 0.85, 0.6197))
    # Fenton-MCC2系统
    g12.add_equipment(Equipment("Fenton2-双氧水投加泵", 0.18, 2, 1, 0.8, 0.95, 0.3287))
    g12.add_equipment(Equipment("Fenton2-卸料泵", 1.5, 1, 1, 0.8, 0.85, 0.6197))
    g12.add_equipment(Equipment("Fenton2-硫酸亚铁投加泵", 2.2, 3, 2, 0.8, 0.85, 0.6197))
    g12.add_equipment(Equipment("Fenton2-PLC系统", 3.0, 2, 2, 0.8, 0.85, 0.6197))
    g12.add_equipment(Equipment("Fenton2-辅助设备", 10.0, 1, 1, 0.7, 0.85, 0.6197))
    sys.add_group(g12)

    # -- 机修、仓库、化验室 --
    g13 = EquipmentGroup("机修、仓库、化验室")
    g13.kp = 0.9
    g13.kq = 0.95
    g13.add_equipment(Equipment("机修、仓库、化验室", 50.0, 1, 1, 0.5, 0.8, 0.75))
    sys.add_group(g13)

    # -- 脱水车间 --
    g14 = EquipmentGroup("脱水车间")
    g14.kp = 0.9
    g14.kq = 0.95
    g14.add_equipment(Equipment("框式搅拌机", 4.0, 4, 4, 0.7, 0.8, 0.75))
    g14.add_equipment(Equipment("叠螺机进料螺杆泵", 4.0, 4, 4, 0.7, 0.8, 0.75))
    g14.add_equipment(Equipment("叠螺式污泥浓缩机", 2.6, 4, 4, 0.7, 0.8, 0.75))
    g14.add_equipment(Equipment("压滤机", 13.0, 4, 4, 0.7, 0.8, 0.75))
    g14.add_equipment(Equipment("陶柱塞泵", 11.0, 4, 4, 0.7, 0.8, 0.75))
    g14.add_equipment(Equipment("压榨泵", 15.0, 4, 4, 0.7, 0.8, 0.75))
    g14.add_equipment(Equipment("清洗泵", 15.0, 2, 1, 0.7, 0.8, 0.75))
    g14.add_equipment(Equipment("空压机", 30.0, 2, 1, 0.7, 0.8, 0.75))
    g14.add_equipment(Equipment("冷干机", 1.0, 1, 1, 0.7, 0.8, 0.75))
    g14.add_equipment(Equipment("PAM制备装置(浓缩)", 1.95, 1, 1, 0.7, 0.8, 0.75))
    g14.add_equipment(Equipment("PAM投加螺杆泵(浓缩)", 1.1, 4, 4, 0.7, 0.8, 0.75))
    g14.add_equipment(Equipment("FeCl3加药泵", 1.1, 2, 2, 0.7, 0.8, 0.75))
    g14.add_equipment(Equipment("FeCl3卸料泵", 4.0, 1, 1, 0.7, 0.8, 0.75))
    g14.add_equipment(Equipment("PAM泡药机(脱水)", 2.02, 1, 1, 0.7, 0.8, 0.75))
    g14.add_equipment(Equipment("PAM加药螺杆泵", 1.1, 2, 2, 0.7, 0.8, 0.75))
    g14.add_equipment(Equipment("轴流风机", 0.25, 14, 14, 0.7, 0.8, 0.75))
    g14.add_equipment(Equipment("照明", 15.0, 1, 1, 0.8, 0.9, 0.48))
    g14.add_equipment(Equipment("自控仪表", 5.0, 1, 1, 0.8, 0.7, 1.02))
    sys.add_group(g14)

    # -- 全厂照明及自控 --
    g15 = EquipmentGroup("全厂照明及自控")
    g15.kp = 0.9
    g15.kq = 0.95
    g15.add_equipment(Equipment("全院照明及自控", 10.0, 1, 1, 0.8, 0.8, 0.75))
    sys.add_group(g15)

    # -- 全厂空调及暖通 --
    g16 = EquipmentGroup("全厂空调及暖通")
    g16.kp = 0.9
    g16.kq = 0.95
    g16.add_equipment(Equipment("全厂空调及暖通", 100.0, 1, 1, 0.7, 0.8, 0.75))
    sys.add_group(g16)

    # 全厂除臭系统
    g17 = EquipmentGroup("全厂除臭系统")
    g17.kp = 0.9
    g17.kq = 0.95
    g17.add_equipment(Equipment("全厂除臭系统", 170.0, 1, 1, 0.7, 0.8, 0.75))
    sys.add_group(g17)


def _build_dist2(sys: Subsystem):
    """构建2#配电系统(蒸发系统)数据 - 按建/构筑物分组"""

    # -- 蒸发结晶主体厂房 --
    g1 = EquipmentGroup("蒸发结晶主体", kp=0.9, kq=0.95)
    for name, rated, installed, working, kx, cos_phi, tan_phi in [
        ("硝循环泵", 160.0, 2, 2, 1.0, 0.8, 0.75),
        ("磁悬浮压缩机", 400.0, 2, 2, 1.0, 0.8, 0.75),
        ("硝冷凝泵", 4.0, 2, 2, 1.0, 0.8, 0.75),
        ("降温水泵", 1.5, 2, 2, 1.0, 0.8, 0.75),
        ("硝出料泵", 3.0, 2, 2, 1.0, 0.8, 0.75),
        ("硝母液罐搅拌", 5.5, 2, 2, 1.0, 0.8, 0.75),
        ("硝母液泵", 5.5, 2, 2, 1.0, 0.8, 0.75),
        ("蒸发进料泵", 5.5, 1, 1, 1.0, 0.8, 0.75),
        ("蒸发结晶检修池提升泵", 5.5, 1, 1, 1.0, 0.8, 0.75),
        ("机封水泵", 4.0, 1, 1, 1.0, 0.8, 0.75),
    ]:
        g1.add_equipment(Equipment(name, rated, installed, working, kx, cos_phi, tan_phi))
    sys.add_group(g1)

    # -- 干燥包装车间 --
    g2 = EquipmentGroup("干燥包装车间", kp=0.9, kq=0.95)
    for name, rated, installed, working, kx, cos_phi, tan_phi in [
        ("元明粉离心机", 30.0, 2, 2, 0.8, 0.8, 0.75),
        ("硝输送机", 4.0, 2, 2, 0.7, 0.8, 0.75),
        ("振动干燥机", 65.0, 1, 1, 0.8, 0.8, 0.75),
        ("硝吨袋包装机", 3.0, 1, 1, 0.6, 0.8, 0.75),
        ("元明粉溶解罐搅拌", 4.0, 1, 1, 0.8, 0.8, 0.75),
        ("芒硝离心机", 55.0, 1, 1, 0.8, 0.8, 0.75),
        ("芒硝输送机", 3.0, 1, 1, 0.7, 0.8, 0.75),
    ]:
        g2.add_equipment(Equipment(name, rated, installed, working, kx, cos_phi, tan_phi))
    sys.add_group(g2)

    # -- 冷冻结晶车间 --
    g3 = EquipmentGroup("冷冻结晶车间", kp=0.9, kq=0.95)
    for name, rated, installed, working, kx, cos_phi, tan_phi in [
        ("冷冻机组", 300.0, 1, 1, 0.9, 0.8, 0.75),
        ("冷冻内循环泵", 37.0, 1, 1, 0.9, 0.8, 0.75),
        ("冷冻外循环泵", 37.0, 1, 1, 0.9, 0.8, 0.75),
        ("冷冻循环泵", 55.0, 2, 2, 0.9, 0.8, 0.75),
        ("冷媒循环泵", 22.0, 2, 2, 0.9, 0.8, 0.75),
        ("冷冻进料泵", 4.0, 1, 1, 0.9, 0.8, 0.75),
        ("冷冻出料泵", 7.5, 1, 1, 0.9, 0.8, 0.75),
        ("预冷母液循环泵", 7.5, 1, 1, 0.9, 0.8, 0.75),
        ("预冷原料循环泵", 11.0, 1, 1, 0.9, 0.8, 0.75),
        ("冷冻母液罐搅拌", 4.0, 1, 1, 0.8, 0.8, 0.75),
        ("冷冻母液泵", 15.0, 1, 1, 0.9, 0.8, 0.75),
        ("冷冻结晶检修池提升泵", 5.5, 1, 1, 0.5, 0.8, 0.75),
    ]:
        g3.add_equipment(Equipment(name, rated, installed, working, kx, cos_phi, tan_phi))
    sys.add_group(g3)

    # -- 杂盐干化及辅助系统 --
    g4 = EquipmentGroup("杂盐干化及辅助系统", kp=0.8, kq=0.85)
    for name, rated, installed, working, kx, cos_phi, tan_phi in [
        ("杂盐进料泵", 3.0, 1, 1, 0.8, 0.8, 0.75),
        ("杂盐母液干化机", 16.0, 3, 3, 0.8, 0.8, 0.75),
        ("消泡剂加药装置", 1.5, 1, 1, 0.7, 0.8, 0.75),
        ("阻垢剂加药装置", 1.5, 1, 1, 0.7, 0.8, 0.75),
        ("冷却风扇", 15.0, 1, 1, 0.8, 0.8, 0.75),
        ("冷却循环泵", 110.0, 1, 1, 0.9, 0.8, 0.75),
        ("备用回路1", 5.5, 1, 1, 0.8, 0.8, 0.75),
        ("备用回路2", 7.5, 1, 1, 0.8, 0.8, 0.75),
        ("备用回路3", 7.5, 1, 1, 0.8, 0.8, 0.75),
    ]:
        g4.add_equipment(Equipment(name, rated, installed, working, kx, cos_phi, tan_phi))
    sys.add_group(g4)
