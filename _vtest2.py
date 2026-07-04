import sys
sys.path.insert(0, r'd:\qoderwork\02_负荷计算系统_v4')

# Test 1: equipment_dialogs.py - KxReferenceEditorDialog has NO _edit_widget
from load_calc.pages.equipment_dialogs import KxReferenceEditorDialog, ValvePowerConfigDialog
import inspect

# Verify KxReferenceEditorDialog has no _edit_widget in _on_close
kx_src = inspect.getsource(KxReferenceEditorDialog._on_close)
assert '_edit_widget' not in kx_src, "BUG: KxReferenceEditorDialog._on_close still has _edit_widget!"
print("Test 1 PASSED: KxReferenceEditorDialog._on_close is clean")

# Verify ValvePowerConfigDialog._on_close HAS _edit_widget cleanup
vp_src = inspect.getsource(ValvePowerConfigDialog._on_close)
assert '_edit_widget' in vp_src and '_cancel_cell_edit' in vp_src, "BUG: ValvePowerConfigDialog._on_close missing _edit_widget cleanup!"
print("Test 2 PASSED: ValvePowerConfigDialog._on_close has _edit_widget cleanup")

# Test 3: page_equipment.py has inline edit methods
from load_calc.pages.page_equipment import EquipmentPage
assert hasattr(EquipmentPage, '_on_equip_double_click'), "Missing _on_equip_double_click"
assert hasattr(EquipmentPage, '_commit_equip_cell_edit'), "Missing _commit_equip_cell_edit"
assert hasattr(EquipmentPage, '_EDITABLE_EQUIP_COLS'), "Missing _EDITABLE_EQUIP_COLS"
assert EquipmentPage._EDITABLE_EQUIP_COLS == {2, 3, 4, 5, 6, 7, 12}, "Wrong editable cols"
print("Test 3 PASSED: EquipmentPage has all inline edit methods")

# Test 4: valve power inference still works
from load_calc.valve_power_map import infer_valve_power
assert infer_valve_power('电动闸阀', 'DN150') == 0.09, "电动闸阀 DN150 should be 0.09"
assert infer_valve_power('电动蝶阀', 'DN200') == 0.12, "电动蝶阀 DN200 should be 0.12"
print("Test 4 PASSED: valve power inference works")

print("\nALL TESTS PASSED")
