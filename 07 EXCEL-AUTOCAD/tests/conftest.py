"""pytest 公共 fixtures"""
import os
import sys

# 确保 src 在 sys.path 中
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


def sample_valid_path():
    return os.path.join(FIXTURES_DIR, "sample_valid.xlsx")


def sample_errors_path():
    return os.path.join(FIXTURES_DIR, "sample_with_errors.xlsx")


def sample_edge_path():
    return os.path.join(FIXTURES_DIR, "sample_edge_cases.xlsx")


def sample_transposed_path():
    return os.path.join(FIXTURES_DIR, "sample_transposed.xlsx")


def sample_transposed_errors_path():
    return os.path.join(FIXTURES_DIR, "sample_transposed_errors.xlsx")


def default_config_path():
    return os.path.join(PROJECT_ROOT, "config.yaml")
