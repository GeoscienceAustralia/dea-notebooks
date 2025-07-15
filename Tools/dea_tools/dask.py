# dea_dask.py
"""
Tools for simplifying the creation of Dask clusters for parallelised computing.

License: The code in this notebook is licensed under the Apache License,
Version 2.0 (https://www.apache.org/licenses/LICENSE-2.0). Digital Earth
Australia data is licensed under the Creative Commons by Attribution 4.0
license (https://creativecommons.org/licenses/by/4.0/).

Contact: If you need assistance, please post a question on the Open Data
Cube Discord chat (https://discord.com/invite/4hhBQVas5U) or on the GIS Stack
Exchange (https://gis.stackexchange.com/questions/ask?tags=open-data-cube)
using the `open-data-cube` tag (you can view previously asked questions
here: https://gis.stackexchange.com/questions/tagged/open-data-cube).

If you would like to report an issue with this script, you can file one on
GitHub (https://github.com/GeoscienceAustralia/dea-notebooks/issues/new).

Last modified: June 2022

"""

import os
from importlib.util import find_spec

import dask
import dask.distributed
from aiohttp import ClientConnectionError
from odc.io.cgroups import get_cpu_quota
from odc.stac import configure_rio

_HAVE_PROXY = bool(find_spec("jupyter_server_proxy"))
_IS_AWS = "AWS_ACCESS_KEY_ID" in os.environ or "AWS_DEFAULT_REGION" in os.environ


def create_local_dask_cluster(
    display_client=True, return_client=False, n_workers=1, threads_per_worker=None, **kwargs
):
    """
    Using the datacube utils function `start_local_dask`, generate
    a local dask cluster. Automatically detects if on AWS or NCI.

    Example use :

        from dea_dask import create_local_dask_cluster
        create_local_dask_cluster()

    Parameters
    ----------
    display_client : Bool, optional
        An optional boolean indicating whether to display a summary of
        the dask client, including a link to monitor progress of the
        analysis. Set to False to hide this display.
    return_client : Bool, optional
        An optional boolean indicating whether to return the dask client
        object.
    n_workers : int, optional
        Number of workers to start, default is set to 1 which works well
        with loading ODC data.
    threads_per_worker: int, optional
        Number of threads per each worker, by default this will be set to
        the number of cpus on the machine.
    kwargs: int, optional
        Additional keyword arguments passed to `dask.distributed.Client`

    """

    if _HAVE_PROXY:
        # Configure dashboard link to go over proxy
        prefix = os.environ.get("JUPYTERHUB_SERVICE_PREFIX", "/")
        dask.config.set({"distributed.dashboard.link": prefix + "proxy/{port}/status"})

    # count cpus if threads_per_worker not provided
    if threads_per_worker is None:
        if get_cpu_quota() is not None:
            threads_per_worker = round(get_cpu_quota())
        else:
            threads_per_worker = os.cpu_count()

    # start client
    client = dask.distributed.Client(
        n_workers=n_workers, threads_per_worker=threads_per_worker, **kwargs
    )
    
    # configure aws access
    if _IS_AWS:
        configure_rio(cloud_defaults=True, aws={"aws_unsigned": True}, client=client)

    # Show the dask cluster settings
    if display_client:
        from IPython.display import display

        display(client)

    # return the client as an object
    if return_client:
        return client


def create_dask_gateway_cluster(profile="r5_L", workers=2):
    """
    Create a cluster in our internal dask cluster.

    Parameters
    ----------
    profile : str
        Possible values are:
            - r5_L (2 cores, 15GB memory)
            - r5_XL (4 cores, 31GB memory)
            - r5_2XL (8 cores, 63GB memory)
            - r5_4XL (16 cores, 127GB memory)

    workers : int
        Number of workers in the cluster.
    """

    # Attempt to import dask_gateway and raise an error if not available
    try:
        from dask_gateway import Gateway
    except ImportError as e:
        raise ImportError(
            "`dask_gateway` is required for `create_dask_gateway_cluster`. "
            "Please install DEA Tools with the `[dask_gateway]` extra, e.g.: "
            "`pip install dea-tools[dask_gateway]`"
        ) from e

    try:
        gateway = Gateway()

        # Close any existing clusters
        cluster_names = gateway.list_clusters()
        if len(cluster_names) > 0:
            print("Cluster(s) still running:", cluster_names)
            for n in cluster_names:
                cluster = gateway.connect(n.name)
                cluster.shutdown()

        options = gateway.cluster_options()
        options["profile"] = profile

        # limit username to alphanumeric characters
        # kubernetes pods won't launch if labels contain anything other than [a-Z, -, _]
        options["jupyterhub_user"] = "".join(
            c if c.isalnum() else "-" for c in os.getenv("JUPYTERHUB_USER")
        )

        cluster = gateway.new_cluster(options)
        cluster.scale(workers)
        return cluster
    except ClientConnectionError:
        raise ConnectionError("access to dask gateway cluster unauthorized")
