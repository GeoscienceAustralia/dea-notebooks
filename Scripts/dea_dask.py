## dea_dask.py
'''
Description: A set of python functions for simplifying the creation of a
local dask cluster.

License: The code in this notebook is licensed under the Apache License,
Version 2.0 (https://www.apache.org/licenses/LICENSE-2.0). Digital Earth
Australia data is licensed under the Creative Commons by Attribution 4.0
license (https://creativecommons.org/licenses/by/4.0/).

Contact: If you need assistance, please post a question on the Open Data
Cube Slack channel (http://slack.opendatacube.org/) or on the GIS Stack
Exchange (https://gis.stackexchange.com/questions/ask?tags=open-data-cube)
using the `open-data-cube` tag (you can view previously asked questions
here: https://gis.stackexchange.com/questions/tagged/open-data-cube).

If you would like to report an issue with this script, you can file one on
Github (https://github.com/GeoscienceAustralia/dea-notebooks/issues/new).

Functions included:
    create_local_dask_cluster

Last modified: March 2020

'''


from importlib.util import find_spec
import os
import dask
from IPython.display import display
from datacube.utils.dask import start_local_dask
from datacube.utils.rio import configure_s3_access

_HAVE_PROXY = bool(find_spec('jupyter_server_proxy'))
_IS_AWS = ('AWS_ACCESS_KEY_ID' in os.environ or
           'AWS_DEFAULT_REGION' in os.environ)


def create_local_dask_cluster(spare_mem='3Gb', display_client=True):
    """
    Using the datacube utils function `start_local_dask`, generate
    a local dask cluster. Automatically detects if on AWS or NCI.

    Example use :

        import sys
        sys.path.append("../Scripts")
        from dea_dask import create_local_dask_cluster

        create_local_dask_cluster(spare_mem='4Gb')

    Parameters
    ----------
    spare_mem : String, optional
        The amount of memory, in Gb, to leave for the notebook to run.
        This memory will not be used by the cluster. e.g '3Gb'
    display_client : Bool, optional
        An optional boolean indicating whether to display a summary of
        the dask client, including a link to monitor progress of the
        analysis. Set to False to hide this display.

    """

    if _HAVE_PROXY:
        # Configure dashboard link to go over proxy
        prefix = os.environ.get('JUPYTERHUB_SERVICE_PREFIX', '/')
        dask.config.set({"distributed.dashboard.link":
                         prefix + "proxy/{port}/status"})

    # Start up a local cluster
    client = start_local_dask(mem_safety_margin=spare_mem)

    if _IS_AWS:
        # Configure GDAL for s3 access
        configure_s3_access(aws_unsigned=True,
                            client=client)

    # Show the dask cluster settings
    if display_client:
        display(client)
