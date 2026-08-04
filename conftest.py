import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_app(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def create_app():
    return load_app("create_order_app", "src/create_order/app.py")


@pytest.fixture
def get_app():
    return load_app("get_order_app", "src/get_order/app.py")


@pytest.fixture
def process_app():
    return load_app("process_order_app", "src/process_order/app.py")

