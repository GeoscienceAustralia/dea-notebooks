from pathlib import Path
from testbook import testbook

TEST_DIR = Path(__file__).parent.parent.resolve()
NB_DIR = TEST_DIR.parent
NB_PATH = NB_DIR / "Beginners_guide" / "04_Loading_data.ipynb"


@testbook(NB_PATH, execute=True)
def test_ok(tb):
    assert True  # ok
