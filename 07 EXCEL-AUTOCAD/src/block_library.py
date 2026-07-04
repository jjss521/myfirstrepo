"""PDSG 图块库管理

从 block_catalog.yaml 加载图块目录，并提供查询和校验功能。
"""
import logging
import os
from typing import Dict, List, Optional

import yaml

from .data_model import BlockCatalog, BlockDefinition
from .errors import BlockLibraryError

logger = logging.getLogger(__name__)


def load_catalog(catalog_path: str) -> BlockCatalog:
    """从 YAML 文件加载图块目录

    Args:
        catalog_path: block_catalog.yaml 路径

    Returns:
        BlockCatalog 实例

    Raises:
        BlockLibraryError: 文件不存在或解析失败
    """
    if not os.path.isfile(catalog_path):
        raise BlockLibraryError(f"图块目录文件不存在: {catalog_path}")

    try:
        with open(catalog_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise BlockLibraryError(f"图块目录解析失败: {e}")

    if not raw or "blocks" not in raw:
        raise BlockLibraryError("图块目录文件缺少 'blocks' 字段")

    blocks = []
    for item in raw["blocks"]:
        blocks.append(BlockDefinition(
            name=item.get("name", ""),
            description=item.get("description", ""),
            applicable=item.get("applicable", {}),
            attributes=item.get("attributes", []),
        ))

    catalog = BlockCatalog(blocks)
    logger.info("加载图块目录: %d 个图块", len(blocks))
    return catalog


def validate_catalog(
    catalog: BlockCatalog,
    block_library_dwg_path: str,
) -> List[str]:
    """校验图块目录中的图块是否在 DWG 中存在

    注意: 此函数需要 AutoCAD 连接才能真正校验。
    这里仅做基本文件存在性检查。

    Args:
        catalog: 图块目录
        block_library_dwg_path: 图块库 DWG 文件路径

    Returns:
        缺失图块名列表（空列表表示全部存在）
    """
    if not os.path.isfile(block_library_dwg_path):
        raise BlockLibraryError(f"图块库 DWG 不存在: {block_library_dwg_path}")

    # 实际 DWG 内图块校验需要在 cad_drawer 中进行
    logger.debug("图块库 DWG 文件存在: %s", block_library_dwg_path)
    return []


def get_block_definition(
    block_name: str,
    catalog: BlockCatalog,
) -> Optional[BlockDefinition]:
    """根据名称查询图块定义"""
    return catalog.find(block_name)


def create_sample_catalog(output_path: str) -> None:
    """生成示例图块目录文件

    用于首次初始化项目时创建模板。
    """
    sample = {
        "blocks": [
            {
                "name": "LOOP_POWER_A",
                "description": "400A及以下断路器回路",
                "applicable": {"breaker_max_current": 400},
                "attributes": [],
            },
            {
                "name": "LOOP_POWER_B",
                "description": "400A以上断路器回路",
                "applicable": {"breaker_min_current": 401},
                "attributes": [],
            },
        ]
    }

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(sample, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    logger.info("生成示例图块目录: %s", output_path)
