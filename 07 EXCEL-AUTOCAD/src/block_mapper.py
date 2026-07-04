"""PDSG 图块映射器

按 负荷类型 + 极数 组合匹配回路图块。
无法匹配时使用默认图块并记录警告。
"""
import logging
from typing import List, Optional

from .data_model import (
    BlockCatalog,
    BlockMappingConfig,
    BlockMappingRule,
    CircuitRecord,
    CircuitWithBlock,
    ErrorRecord,
)

logger = logging.getLogger(__name__)


def map_circuits(
    circuits: List[CircuitRecord],
    cfg: BlockMappingConfig,
    catalog: Optional[BlockCatalog] = None,
) -> tuple:
    """将回路列表映射为带图块的回路

    Args:
        circuits: 有效回路记录列表
        cfg: 图块映射配置
        catalog: 图块目录（可选，用于验证图块是否存在）

    Returns:
        (List[CircuitWithBlock], List[ErrorRecord]) 映射结果和警告
    """
    mapped: List[CircuitWithBlock] = []
    warnings: List[ErrorRecord] = []

    for circuit in circuits:
        block_name = _find_block(circuit, cfg.rules)

        if block_name is None:
            # 使用默认图块
            block_name = cfg.default_block
            warnings.append(ErrorRecord(
                row_number=circuit.row_number,
                circuit_id=circuit.circuit_id,
                error_type="图块映射警告",
                error_message=(
                    f"回路 {circuit.circuit_id}: 负荷类型={circuit.load_type.value} "
                    f"极数={circuit.breaker_poles} 无匹配规则，使用默认图块 {block_name}"
                ),
            ))
            logger.warning(
                "回路 %s: 无匹配规则，使用默认图块 %s",
                circuit.circuit_id,
                block_name,
            )

        # 验证图块是否存在于目录中
        if catalog and not catalog.find(block_name):
            warnings.append(ErrorRecord(
                row_number=circuit.row_number,
                circuit_id=circuit.circuit_id,
                error_type="图块目录警告",
                error_message=(
                    f"回路 {circuit.circuit_id}: 图块 \"{block_name}\" "
                    f"在图块目录中不存在"
                ),
            ))
            logger.warning("图块 \"%s\" 不在图块目录中", block_name)

        mapped.append(CircuitWithBlock(
            record=circuit,
            block_name=block_name,
        ))

    logger.info("图块映射完成: %d/%d", len(mapped), len(circuits))
    return mapped, warnings


def _find_block(
    circuit: CircuitRecord,
    rules: List[BlockMappingRule],
) -> Optional[str]:
    """为单个回路查找匹配图块

    按规则列表顺序（优先级从前到后）匹配。
    匹配条件: load_type + poles
    """
    for rule in rules:
        if _rule_matches(circuit, rule):
            return rule.block
    return None


def _rule_matches(circuit: CircuitRecord, rule: BlockMappingRule) -> bool:
    """检查规则是否匹配回路

    支持的匹配条件:
    - load_type: 负荷类型
    - poles: 断路器极数
    - breaker_max_current: 脱扣器电流 ≤ 此值
    - breaker_min_current: 脱扣器电流 > 此值 (不含等于)
    """
    match = rule.match

    # 负荷类型匹配
    if "load_type" in match:
        rule_load_type = match["load_type"]
        if circuit.load_type.value != rule_load_type:
            return False

    # 极数匹配
    if "poles" in match:
        rule_poles = int(match["poles"])
        if circuit.breaker_poles != rule_poles:
            return False

    # 断路器电流上限匹配 (≤ 阈值)
    if "breaker_max_current" in match:
        threshold = float(match["breaker_max_current"])
        if circuit.breaker_trip_current_a > threshold:
            return False

    # 断路器电流下限匹配 (> 阈值，不含等于)
    if "breaker_min_current" in match:
        threshold = float(match["breaker_min_current"]) - 1
        if circuit.breaker_trip_current_a <= threshold:
            return False

    return True
