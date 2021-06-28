# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.5.2
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %%
import os

import dask
import dask.array as da
from dask.distributed import wait as dask_wait
from dask_gateway import Gateway
from datacube.utils.rio import configure_s3_access


def gw_options(gateway, **overrides):
    opts = gateway.cluster_options()
    opts["image"] = os.getenv("JUPYTER_IMAGE")
    opts["jupyterhub_user"] = os.getenv("JUPYTERHUB_USER")
    opts.update(**overrides)
    return opts


def connect_to_cluster(gateway=None):
    gateway = gateway or Gateway()
    for cluster in gateway.list_clusters():
        return gateway.connect(cluster.name).get_client()
    return None


gateway = Gateway()
gateway.list_clusters()

# %% [markdown]
# ### Launch Cluster
#
# This can take several minutes to complete

# %%
client = connect_to_cluster(gateway)

if client is None:
    cluster = gateway.new_cluster(gw_options(gateway, profile="r5_4XL"))
    cluster.scale(1)
    client = cluster.get_client()

if client is not None:
    display(client.cluster)
    display(client)

# %% [markdown]
# ### Configure S3 access on the cluster

# %%
configure_s3_access(aws_unsigned=True, cloud_defaults=True, client=client)

# %% [markdown]
# ### Leave this running
#
# When done with the cluster, run 
# ```python
# cluster.shutdown()
# ```
#
# To check it did shutdown, make sure that
# ```python
# gateway.list_clusters() == []
# ```
