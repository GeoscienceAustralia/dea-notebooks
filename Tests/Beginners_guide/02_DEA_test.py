from pathlib import Path

from testbook import testbook

TEST_DIR = Path(__file__).parent.parent.resolve()
NB_DIR = TEST_DIR.parent


@testbook(NB_DIR / 'Beginners_guide' / '02_DEA.ipynb', execute=True)
def test_ok(tb):
    assert True  # ok
