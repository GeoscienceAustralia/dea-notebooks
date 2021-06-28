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
from tqdm.auto import tqdm


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
plugin = resolve("wofs-summary")("bilinear", dilation=3)

rdr = TaskReader(
    "ga_ls_wo_3_all-28-05-2021.db", plugin.product(location="file:///tmp/wofs/")
)

display(rdr)
display(rdr.all_tiles[0], "...", rdr.all_tiles[-1])

# %%
tidx = (40, 43)  # Tas: (41, 8)
tasks = [rdr.load_task(_tidx) for _tidx in rdr.all_tiles if _tidx[-2:] == tidx]
len(tasks)

# %%
# %%time
rr = [plugin.reduce(plugin.input_data(task)).compute() for task in tqdm(tasks)]

# %%
from odc.algo import apply_numexpr

cw = apply_numexpr(
    "where(count_wet == -999, 0, count_wet)", rr[0], dtype="int16", casting="unsafe"
)
cc = apply_numexpr(
    "where(count_clear == -999, 0, count_clear)", rr[0], dtype="int16", casting="unsafe"
)

for r in rr[1:]:
    cw += apply_numexpr("where(count_wet == -999, 0, count_wet)", r, dtype="int16", casting="unsafe")
    cc += apply_numexpr("where(count_clear == -999, 0, count_clear)", r, dtype="int16", casting="unsafe")

# %%
cw.plot.imshow(size=8)

# %%
cc.plot.imshow(size=8)

# %%
from odc.algo import safe_div

frequency = safe_div(cw, cc)

# %%
frequency.plot.imshow(size=8);

# %%
from datacube.utils.cog import write_cog

out_path = tasks[0].paths()["frequency"].replace("--P1Y", "--P36Y")
print(out_path)
write_cog(frequency, out_path, overview_resampling="average", overwrite=True)

# %%
out_path = tasks[0].paths()["count_clear"].replace("--P1Y", "--P36Y")
print(out_path)
write_cog(cc, out_path, overview_resampling="average", overwrite=True)

# %%
out_path = tasks[0].paths()["count_wet"].replace("--P1Y", "--P36Y")
print(out_path)
write_cog(cw, out_path, overview_resampling="average", overwrite=True)

# %%

# %%

# %%

# %%
from datacube import Datacube

region_code=f"x{tidx[0]}y{tidx[1]}"
dc = Datacube()

xx_orig = dc.load(product="ga_ls_wo_fq_myear_3", region_code=region_code).isel(time=0)

# %%
xx_orig.frequency.plot.imshow(size=8);

# %%
((xx_orig.frequency - frequency)).plot.imshow(size=8);

# %%
((to_float(xx_orig.count_clear) - to_float(cc)) < 0).sum()

# %%
to_float(xx_orig.count_clear).sum() - to_float(cc).sum()

# %%
plt.rcParams["axes.facecolor"] = "white"  # make it white again
xdiff = (to_float(xx_orig.count_clear) - to_float(cc)).data.ravel()
# plt.hist(xdiff, 100);

# %%
import seaborn

seaborn.kdeplot(xdiff, clip=(0, 200))

# %%
f0 = xx_orig.frequency.data.ravel()
f3 = frequency.data.ravel()

# %%
f0 = f0[np.isfinite(f0)]
f3 = f3[np.isfinite(f3)]

# %%
seaborn.kdeplot(f0, clip=(0, 0.05), color="C0")
seaborn.kdeplot(f3, clip=(0, 0.05), color="C1");

# %%
seaborn.kdeplot(f0, clip=(0.8, 1), color="C0")
seaborn.kdeplot(f3, clip=(0.8, 1), color="C1");

# %%
