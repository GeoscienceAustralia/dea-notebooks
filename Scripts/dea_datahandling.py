# Functions in this script have been moved to a new location to allow them to be imported into notebooks as a Python package: ../Tools/

import pathlib
import warnings

warnings.warn("Scripts/dea_* scripts have been deprecated in favour of the dea-tools module. Please import dea_tools.datahandling instead.", DeprecationWarning)

current_dir = pathlib.Path(__file__).parent.absolute()

import sys
sys.path.insert(1, str(current_dir.parent.absolute() / 'Tools'))

from dea_tools.datahandling import *