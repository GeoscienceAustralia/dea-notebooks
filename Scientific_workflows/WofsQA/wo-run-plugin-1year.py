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
#     name: local
# ---

# %% [markdown]
# ## Preparation Instructions
#
# - get db file
#   - `wget https://dea-dev-stats-processing.s3.ap-southeast-2.amazonaws.com/dbs/ga_ls_wo_3_all-28-05-2021.db`
# - install more recent odc-tools
#   - `python -m pip install -U odc-stats odc-algo --extra-index-url=https://packages.dea.ga.gov.au/`
# - Launch gateway in other notebook to avoid restarting it all the time

# %%
# #!wget https://dea-dev-stats-processing.s3.ap-southeast-2.amazonaws.com/dbs/ga_ls_wo_3_all-28-05-2021.db
# #!python -m pip install -U odc-stats odc-algo --extra-index-url=https://packages.dea.ga.gov.au/

# %%
# %matplotlib inline
import matplotlib.pyplot as plt
from IPython.display import Image, display

plt.rcParams["axes.facecolor"] = "magenta"  # makes transparent pixels obvious
import numpy as np
import xarray as xr
from odc.algo import colorize, to_float, to_rgba
from odc.ui import to_jpeg_data


def show_im(data, transparent=(255, 0, 255), q=99):
    display(Image(data=to_jpeg_data(data, transparent=transparent, quality=q)))


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

# %%
client = connect_to_cluster(gateway)

if client is None:
    raise ValueError("Dask gateway is not running")

if client is not None:
    display(client.cluster)
    display(client)

# %% [markdown]
# ```bash
# wget https://dea-dev-stats-processing.s3.ap-southeast-2.amazonaws.com/dbs/ga_ls_wo_3_all-28-05-2021.db
# ```

# %%
from odc.stats._plugins import import_all, resolve
from odc.stats.tasks import OutputProduct, TaskReader

import_all()
plugin0 = resolve("wofs-summary")("bilinear", dilation=0)
plugin3 = resolve("wofs-summary")("bilinear", dilation=3)

rdr = TaskReader(
    "ga_ls_wo_3_all-28-05-2021.db", plugin0.product(location="file:///tmp/wofs/")
)

display(rdr)
display(rdr.all_tiles[0], "...", rdr.all_tiles[-1])

# %%
tidx = ("1990--P1Y", 41, 8)
task = rdr.load_task(tidx)

# %%
rr0 = plugin0.reduce(plugin0.input_data(task))
rr3 = plugin3.reduce(plugin3.input_data(task))

display(rr0)
display(rr3)

# %%
# %%time

_rr0, _rr3 = client.compute([rr0, rr3])
dask_wait([_rr0, _rr3])
_rr0, _rr3 = _rr0.result(), _rr3.result()

# %%
_rr0.frequency.plot.imshow(size=8);

# %%
_rr3.frequency.plot.imshow(size=8);

# %%
(_rr3.count_wet - _rr0.count_wet).plot.imshow(size=8);

# %%
(_rr3.count_clear - _rr0.count_clear).plot.imshow(size=8);

# %%
(_rr3.frequency - _rr0.frequency).plot.imshow(size=8);

# %%

# %%
(
    np.nanmean(to_float(_rr3.count_wet) - to_float(_rr0.count_wet)),
    np.nanmean(to_float(_rr3.count_clear) - to_float(_rr0.count_clear)),
    np.nanmean(_rr3.frequency - _rr0.frequency),
)

# %%
_df = (_rr3.frequency - _rr0.frequency).data.ravel()

# %%
fig, ax = plt.subplots(1, figsize=(12, 3))

ax.plot(_df, ".", markersize=0.1)
ax.set_facecolor("white")

# %%
