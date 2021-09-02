#!/usr/bin/env python3

# Note: To use the 'upload' functionality of this file, you must:
#   $ pipenv install twine --dev

import io
import os
import sys
from shutil import rmtree
from pathlib import Path

from setuptools import find_packages, setup, Command
import setuptools_scm

# Package meta-data.
NAME = 'dea-tools'
DESCRIPTION = 'Functions and algorithms for analysing Digital Earth Australia data.'
URL = 'https://github.com/GeoscienceAustralia/dea-notebooks'
EMAIL = 'dea@ga.gov.au'
AUTHOR = 'Geoscience Australia'
REQUIRES_PYTHON = '>=3.6.0'

# Where are we?
IS_SANDBOX = os.getenv('JUPYTER_IMAGE', default='').startswith('geoscienceaustralia/sandbox')
IS_NCI = 'dea-env' in os.getenv('LOADEDMODULES_modshare', default='')
IS_DEA = IS_NCI or IS_SANDBOX

# What packages are required for this module to be executed?
# These are all on the Sandbox/NCI so shouldn't need installing on those platforms.
REQUIRED = [
    # bom
    'ciso8601',
    'pytz',
    'requests',
    'lxml',
    # classification
    'numpy',
    'xarray',
    'geopandas',
    'datacube',
    'tqdm',
    'dask',
    'rasterio',
    'scikit-learn',
    # coastal
    'matplotlib',
    'pandas',
    'scipy',
    # 'otps',  # Hard to install, but available on Sandbox and NCI
    # datahandling
    'GDAL',
    'odc-ui',
    'numexpr',
    # plotting
    'folium',
    'pyproj',
    'branca',
    'shapely',
    'scikit-image',
    # climate
    'python-dateutil',
    # waterbodies
    'OWSLib',
]

# What packages are optional?
EXTRAS = {
    'jupyter': ['IPython', 'ipywidgets', 'ipyleaflet'],
    'boto': ['boto3'],
}

# The rest you shouldn't have to touch too much :)
# ------------------------------------------------
# Except, perhaps the License and Trove Classifiers!
# If you do change the License, remember to change the Trove Classifier for that!

here = os.path.abspath(os.path.dirname(__file__))

# Import the README and use it as the long-description.
# Note: this will only work if 'README.md' is present in your MANIFEST.in file!
try:
    with io.open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
        long_description = '\n' + f.read()
except FileNotFoundError:
    long_description = DESCRIPTION

    
class UploadCommand(Command):
    """Support setup.py upload."""

    description = 'Build and publish the package.'
    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print('\033[1m{0}\033[0m'.format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status('Removing previous builds…')
            rmtree(os.path.join(here, 'dist'))
        except OSError:
            pass

        self.status('Building Source and Wheel (universal) distribution…')
        os.system('{0} setup.py sdist bdist_wheel --universal'.format(sys.executable))

        self.status('Uploading the package to PyPI via Twine…')
        os.system('twine upload dist/*')

        self.status('Pushing git tags…')
        os.system('git tag v{0}'.format(about['__version__']))
        os.system('git push --tags')

        sys.exit()


# Versioning magic.
VERSION_FILE_PATH = Path('dea_tools/__version__.py')
about = {}
try:
    version = setuptools_scm.get_version(
        root='..',
        write_to='Tools' / VERSION_FILE_PATH,
        relative_to=__file__,
        local_scheme=lambda _: '')
except (LookupError, FileNotFoundError):
    # python -m build will trip the FNFError
    try:
        # no .git folder, so read from __version__.py
        with open(VERSION_FILE_PATH) as f_version:
            exec(f_version.read(), about)
            version = about['version']
    except FileNotFoundError:
        # No __version__.py, yikes
        raise RuntimeError('Build in-place with --use-feature=in-tree-build.')

# Where the magic happens:
setup(
    name=NAME,
    version=version,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type='text/x-rst',
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),

    # entry_points={
    #     'console_scripts': ['mycli=mymodule:cli'],
    # },
    install_requires=REQUIRED if not IS_DEA else [],
    extras_require=EXTRAS if not IS_DEA else {k: [] for k in EXTRAS},
    include_package_data=True,
    license='Apache License 2.0',
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'License :: OSI Approved :: Apache Software License',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: GIS',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
    # $ setup.py publish support.
    cmdclass={
        'upload': UploadCommand,
    },
)
