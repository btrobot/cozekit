import pytest
from pathlib import Path

_DIR = Path(__file__).parent

def pytest_collection_modifyitems(items):
    for item in items:
        if _DIR in Path(item.fspath).parents:
            item.add_marker(pytest.mark.regression)
