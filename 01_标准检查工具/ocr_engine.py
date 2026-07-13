"""PaddleOCR封装：图片文本识别 + 文本行合并"""

from __future__ import annotations

import logging
from typing import Any

from config import MERGE_LINE_DISTANCE, OCR_CONFIDENCE_THRESHOLD, OCR_LANG
from models import MergedTextLine, OcrTextRegion

logger = logging.getLogger("standard_checker")

# 延迟导入 PaddleOCR，避免模块加载时就报错
_ocr_instance: Any = None  # type: ignore[no-any-expr] # PaddleOCR type unavailable at type-check time


def _get_ocr() -> Any:  # noqa: TYPE_UNKNOWN
    """懒加载 PaddleOCR 实例"""
    global _ocr_instance
    if _ocr_instance is None:
        try:
            from paddleocr import PaddleOCR
        except ImportError:
            logger.error("未安装 PaddleOCR，请运行: pip install paddlepaddle paddleocr")
            raise
        _ocr_instance = PaddleOCR(
            use_angle_cls=True,
            lang=OCR_LANG,
        )
        logger.info("PaddleOCR 初始化完成")
    return _ocr_instance


def extract_text(
    image_path: str, confidence_threshold: float = OCR_CONFIDENCE_THRESHOLD
) -> list[OcrTextRegion]:
    """对单张图片进行OCR识别，返回文本区域列表"""
    ocr = _get_ocr()
    try:
        result = ocr.ocr(image_path, cls=True)
    except Exception as e:  # noqa: BROAD_EXCEPT_OK
        logger.error(f"OCR处理失败 [{image_path}]: {e}")
        return []

    if not result or not result[0]:
        logger.warning(f"OCR未识别到文本: {image_path}")
        return []

    regions = []
    for item in result[0]:
        bbox = item[0]  # [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
        text = item[1][0]
        confidence = item[1][1]

        if confidence >= confidence_threshold:
            regions.append(
                OcrTextRegion(
                    bbox=bbox,
                    text=text,
                    confidence=confidence,
                )
            )
        else:
            logger.debug(f"低置信度过滤: '{text}' ({confidence:.2f})")

    logger.info(f"OCR识别 [{image_path}]: {len(regions)} 个文本区域")
    return regions


def merge_text_regions(regions: list[OcrTextRegion]) -> list[MergedTextLine]:
    """
    将零散的OCR文本区域合并为逻辑文本行。

    算法：
    1. 计算每个区域的Y中心坐标
    2. 按Y中心聚类，距离 < MERGE_LINE_DISTANCE 的归为同一行
    3. 行内按X坐标从左到右排序
    4. 拼接文本，计算平均置信度
    """
    if not regions:
        return []

    # 计算每个区域的Y中心和X起点
    items = []
    for r in regions:
        ys = [p[1] for p in r.bbox]
        xs = [p[0] for p in r.bbox]
        y_center = sum(ys) / len(ys)
        x_min = min(xs)
        items.append((r, y_center, x_min))

    # 按Y中心排序
    items.sort(key=lambda x: x[1])

    # 按Y中心聚类为行
    lines: list[list[tuple]] = []
    current_line: list[tuple] = [items[0]]

    for item in items[1:]:
        if abs(item[1] - current_line[0][1]) < MERGE_LINE_DISTANCE:
            current_line.append(item)
        else:
            lines.append(current_line)
            current_line = [item]
    lines.append(current_line)

    # 每行内按X排序，拼接文本
    merged = []
    for line in lines:
        line.sort(key=lambda x: x[2])  # 按X坐标排序
        texts = [item[0].text for item in line]
        confidences = [item[0].confidence for item in line]
        merged_text = " ".join(texts)
        avg_confidence = sum(confidences) / len(confidences)
        y_center = sum(item[1] for item in line) / len(line)

        merged.append(
            MergedTextLine(
                text=merged_text,
                confidence=avg_confidence,
                y_center=y_center,
            )
        )

    return merged


def process_image(
    image_path: str, confidence_threshold: float = OCR_CONFIDENCE_THRESHOLD
) -> list[MergedTextLine]:
    """处理单张图片：OCR识别 → 文本行合并"""
    regions = extract_text(image_path, confidence_threshold)
    lines = merge_text_regions(regions)
    logger.debug(f"合并后文本行数: {len(lines)}")
    for line in lines:
        logger.debug(f"  [{line.confidence:.2f}] {line.text}")
    return lines
