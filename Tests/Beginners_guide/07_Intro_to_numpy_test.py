# import os
# import pytest
# from pathlib import Path
# from testbook import testbook

# TEST_DIR = Path(__file__).parent.parent.resolve()
# NB_DIR = TEST_DIR.parent
# NB_PATH = NB_DIR / "Beginners_guide" / "07_Intro_to_numpy.ipynb"


# @pytest.fixture(scope="module")
# def tb():

#     # Update working directory to ensure relative links in notebooks work
#     os.chdir(NB_DIR.parent)

#     with testbook(NB_PATH, execute=True) as tb:
#         yield tb


# def test_ok(tb):
#     assert True  # ok
