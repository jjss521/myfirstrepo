"""工具模块：日志、限速器、重试逻辑"""
import logging
import os
import random
import time
from typing import Optional

import requests

from config import (
    MAX_RETRIES, RETRY_BACKOFF_FACTOR, REQUEST_TIMEOUT,
    USER_AGENT, REQUEST_DELAY_MIN, REQUEST_DELAY_MAX,
)


def setup_logging(output_dir: str, debug: bool = False) -> logging.Logger:
    """配置日志：同时输出到控制台和文件"""
    os.makedirs(output_dir, exist_ok=True)
    log_file = os.path.join(output_dir, "log.txt")

    logger = logging.getLogger("standard_checker")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.handlers.clear()

    # 控制台 Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    console_format = logging.Formatter("[%(levelname)s] %(message)s")
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # 文件 Handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    return logger


class RateLimiter:
    """请求限速器"""

    def __init__(self, min_delay: float = REQUEST_DELAY_MIN,
                 max_delay: float = REQUEST_DELAY_MAX):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_request_time: float = 0

    def wait(self):
        """等待直到可以发起下一次请求"""
        now = time.time()
        elapsed = now - self.last_request_time
        delay = random.uniform(self.min_delay, self.max_delay)
        if elapsed < delay:
            sleep_time = delay - elapsed
            time.sleep(sleep_time)
        self.last_request_time = time.time()


def retry_request(
    url: str,
    session: requests.Session,
    rate_limiter: RateLimiter,
    max_retries: int = MAX_RETRIES,
    logger: Optional[logging.Logger] = None,
) -> Optional[requests.Response]:
    """带重试和限速的HTTP GET请求"""
    if logger is None:
        logger = logging.getLogger("standard_checker")

    headers = {"User-Agent": USER_AGENT}

    for attempt in range(max_retries):
        rate_limiter.wait()
        try:
            logger.debug(f"请求: {url} (第{attempt + 1}次)")
            resp = session.get(url, headers=headers, timeout=REQUEST_TIMEOUT)

            if resp.status_code == 429:
                wait_time = 30
                logger.warning(f"HTTP 429 限速，等待{wait_time}秒...")
                time.sleep(wait_time)
                continue

            resp.raise_for_status()
            return resp

        except requests.exceptions.Timeout:
            backoff = REQUEST_DELAY_MIN * (RETRY_BACKOFF_FACTOR ** attempt)
            logger.warning(f"请求超时，{backoff:.1f}秒后重试: {url}")
            time.sleep(backoff)

        except requests.exceptions.ConnectionError as e:
            backoff = REQUEST_DELAY_MIN * (RETRY_BACKOFF_FACTOR ** attempt)
            logger.warning(f"连接错误: {e}，{backoff:.1f}秒后重试")
            time.sleep(backoff)

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP错误: {e}，URL: {url}")
            if attempt < max_retries - 1:
                backoff = REQUEST_DELAY_MIN * (RETRY_BACKOFF_FACTOR ** attempt)
                time.sleep(backoff)
            else:
                return None

    logger.error(f"请求失败，已重试{max_retries}次: {url}")
    return None


def find_screenshots(input_dir: str) -> list:
    """扫描输入目录，返回所有截图文件路径"""
    if not os.path.isdir(input_dir):
        return []

    extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    files = []
    for name in sorted(os.listdir(input_dir)):
        ext = os.path.splitext(name)[1].lower()
        if ext in extensions:
            files.append(os.path.join(input_dir, name))
    return files


def normalize_whitespace(text: str) -> str:
    """压缩多余空白为单个空格"""
    import re
    return re.sub(r'\s+', ' ', text).strip()
