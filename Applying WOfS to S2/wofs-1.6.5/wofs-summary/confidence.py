import datacube
import geopandas
import rasterio
import rasterio.features
import matplotlib.pyplot as plt
import xarray
import numpy as np
import scipy
import scipy.ndimage
import glob
import sklearn.linear_model
import pickle

"""
# These weights are specified in the WOfS journal paper.
wofl_wet_freq = 0.1703
MrVBF = 0.1671
MODIS_OWL = 0.0336
slope = -0.2522
geofabric_foreshore = 4.2062
geofabric_pondage = -5.4692
geofabric_reservoir = 0.6574
geofabric_flat = 0.7700
geofabric_lake = 1.9992
geofabric_swamp = 1.3231
geofabric_watercourse = 1.9206
urban_areas = -4.9358

threshold = 0.05 # also by WOfS journal paper. Actually, maybe 0.01 (or 0.02)
"""


# --------------- Utilities ---------------


def numpy_to_xarray(array, geobox, name=None):
    """Utility to convert ndarray to DataArray, using a datacube.model.GeoBox"""
    coords = [xarray.IndexVariable(x, geobox.coords[x].values, attrs=dict(units=geobox.coords[x].units))
              for x in geobox.dims]
    return xarray.DataArray(array, coords=coords, attrs=dict(crs=geobox.crs), name=name)


def geopandas_to_xarray(table, geobox, name=None):
    """Rasterise (with reprojection)"""
    array = rasterio.features.rasterize(shapes=table.to_crs(geobox.crs._crs.ExportToProj4()).geometry,
                                        out_shape=(geobox.height, geobox.width),
                                        transform=geobox.affine)
    return numpy_to_xarray(array, geobox, name)


# Note on dimensions:
#   Rasterio has named height and width parameters,
#   referring to the first and second index of the raster array respectively.
#   ODC GeoBox names width and height (reverse order) in its constructor,
#   however height is associated with the "y" axis internally, which
#   still becomes the first of the two axes in the xarray.
def rasterfile_to_xarray(file, geobox=None, name=None, nodata=None):
    """Blit like"""
    with rasterio.open(file) as src:
        assert src.indexes == (1,)  # assume single band
        if geobox is None:
            from datacube.utils.geometry import GeoBox, CRS

            # TODO: fix this heinousness
            global crs
            global affine
            crs = src.crs
            affine = src.transform

            geobox = GeoBox(width=src.width,
                            height=src.height,
                            affine=src.affine,  # .transform is a list, .affine is an object
                            crs=CRS(src.crs.wkt))
            array = src.read(1)
        else:
            band = rasterio.band(src, 1)  # do not attempt to read entire extent into memory
            array = np.empty((geobox.height, geobox.width), dtype=band.dtype)
            rasterio.warp.reproject(source=band,
                                    destination=array,
                                    dst_crs=geobox.crs.crs_str,
                                    dst_transform=geobox.affine,
                                    dst_nodata=nodata)
    return numpy_to_xarray(array, geobox, name)


def write(filename, data, nodata=None):
    """ Output raster to filesystem """
    # TODO: eliminate globals (crs,affine) and magic constants (dimensions)
    import rasterio
    with rasterio.open(filename,
                       mode='w',
                       width=4000,
                       height=4000,
                       count=1,
                       dtype=data.dtype.name,
                       driver='GTIFF',
                       nodata=nodata,
                       tiled=True,
                       compress='LZW',  # balance IO volume and CPU speed
                       affine=affine,
                       crs=crs) as destination:
        destination.write(data.data, 1)


# ------------------ Ancilliaries ------------------
def urban(geobox):
    ucl_path = "/g/data/v10/wofs/ancillary/ucl/UCL_2011_AUST.shp"
    u = geopandas.read_file(ucl_path)  # load shapes table
    u = u[u['SOS_NAME11'] == 'Major Urban']  # filter out <100k
    u = u.to_crs(geobox.crs._crs.ExportToProj4())  # reproject
    array = rasterio.features.rasterize(shapes=u.geometry,
                                        out_shape=(geobox.height, geobox.width),
                                        transform=geobox.affine)
    return numpy_to_xarray(array, geobox, 'urban')


"""
Geofabric structure:

SrcFCName, SrcFType, AHGFFType

AHGFWaterbody
    Flats ['Swamp'] [27]
    Lakes ['Lake'] [26]
    Reservoirs ['Town Rural Storage', 'Flood Irrigation Storage'] [25]

AHGFHydroArea
    CanalAreas ['Canal Area'] [55]
    Flats ['Land Subject To Inundation', 'Saline Coastal Flat', 'Marine Swamp'] [56]
    ForeshoreFlats ['Foreshore Flat'] [59]
    PondageAreas ['Settling Pond', 'Aquaculture Area', 'Salt Evaporator'] [57]
    RapidAreas ['Rapid Area'] [58]
    WatercourseAreas ['Watercourse Area'] [54]
"""


def geofabric_parts(geobox):
    geofabric_path = "/g/data/v10/wofs/ancillary/geofabric/SH_Cartography_GDB/SH_Cartography.gdb"
    # fiona.listlayers(geofabric_path)
    for layer in ['AHGFHydroArea', 'AHGFWaterbody']:  # consider these two layers
        table = geopandas.read_file(geofabric_path, layer=layer)[['AHGFFType', 'SrcFCName', 'SrcFType', 'geometry']]
        for fc, df in table.groupby('SrcFCName'):
            if fc not in ['CanalAreas', 'RapidAreas']:  # exclude these two feature classes
                name = layer + fc
                yield geopandas_to_xarray(df, geobox, name=name)


# def geofabric(geobox):
#    geofabric_weights = {'AHGFHydroAreaFlats': geofabric_flat, # includes marine swamp
#                         'AHGFHydroAreaForeshoreFlats': geofabric_foreshore,
#                         'AHGFHydroAreaPondageAreas': geofabric_pondage,
#                         'AHGFHydroAreaWatercourseAreas': geofabric_watercourse,
#                         'AHGFWaterbodyFlats': geofabric_swamp, # type 27
#                         'AHGFWaterbodyLakes': geofabric_lake,
#                         'AHGFWaterbodyReservoirs': geofabric_reservoir}
#    return sum(array*geofabric_weights[array.name] for array in geofabric_parts(geobox))
datacube.config.LocalConfig.db_database = 'wofstest'
datacube.config.LocalConfig.db_hostname = 'agdcstaging-db.nci.org.au'
dc = datacube.Datacube()  # only used for elevation


def slope_degrees(geobox):
    pad = 5  # pixels of margin buffering
    padded = geobox[-pad:(geobox.height + pad), -pad:(geobox.width + pad)]

    # dem = dc.load(product='dsm1sv10', # ? 'srtm_dem1sv1_0'
    #              geopolygon=geobox[-pad:geobox.height+pad, -pad:geobox.width+pad].extent,
    #              output_crs=geobox.crs.crs_str, # force target gridspec, address weird bug
    #              resolution=geobox.resolution).isel(time=0)
    class likely:
        geobox = padded

    likely.extent = likely.geobox.extent
    likely.coords = likely.geobox.coords
    dem = dc.load(product='dsm1sv10',  # ? 'srtm_dem1sv1_0'
                  like=likely()).isel(time=0)

    # Sobel is prefered gradient method from DEM-grid literature.
    xgrad = scipy.ndimage.sobel(dem.elevation, axis=1) / abs(8 * dem.affine.a)  # i.e. dz/dx
    ygrad = scipy.ndimage.sobel(dem.elevation, axis=0) / abs(8 * dem.affine.e)
    # Here, assuming orthogonal grid. Probably shouldn't.

    # slope = numpy.degrees(numpy.arctan(numpy.hypot(xgrad, ygrad)))
    slope = np.degrees(np.arccos(1.0 / np.sqrt(xgrad ** 2 + ygrad ** 2 + 1.0)))
    # Tangential vectors have basis x+dz/dx z, y+dz/dy z.
    # Perpendicularity implies normal is colinear with z - dz/dx x - dz/dy y.
    # The slope cosine is given by the dot product of the normal with vertical
    # (i.e. by the vertical component of the normal, after magnitude normalisation).
    # Note, an alternative approach is to project the normal into the horizontal plane
    # (delaying magnitude normalisation until afterward),
    # and consider the rise in this direction of steepest ascent (seems like fewer operations).

    return numpy_to_xarray(slope[pad:-pad, pad:-pad], geobox, 'slope')  # strip padding


mrvbf_path = "/g/data/v10/wofs/ancillary/mrvbf/mrvbf_int.tif"
modis_path = "/g/data/v10/wofs/ancillary/modis/MOD09A1.aust.005.OWL.0.2.4.2001.2010.GE.20.tif"


# def synthesis(frequency_raster_path):
#
#    freq = rasterfile_to_xarray(frequency_raster_path)
#    geobox = freq.geobox
#
#    ucl = urban(geobox)
#    g = geofabric(geobox)
#    slant = slope_degrees(geobox)
#    vbf = rasterfile_to_xarray(mrvbf_path, geobox) # let nodata remain at 255
#    owl = rasterfile_to_xarray(modis_path, geobox)
#
#    ancillary = g + slope*slant + MODIS_OWL*owl + MrVBF*vbf + urban_areas*ucl
#
#    freq.data = np.nan_to_num(freq.data) # NaN -> 0
#    confidence = scipy.special.expit(ancillary + wofl_wet_freq*freq)
#
#    # filtered summary
#    filtered = freq*(confidence>threshold)
#
#    return confidence, filtered
def ancilliary_experts(geobox):
    ucl = urban(geobox)
    slant = slope_degrees(geobox)
    vbf = rasterfile_to_xarray(mrvbf_path, geobox, 'MrVBF')  # let nodata remain at 255
    owl = rasterfile_to_xarray(modis_path, geobox, 'MODIS-OWL')
    g = list(geofabric_parts(geobox))

    full_set = g + [ucl, slant, vbf, owl]

    # should sort this, say by name?
    # option to concat into a single xarray
    return full_set


def synthesis(frequency_raster_path=None, geobox=None, return_freq=False):
    """Return collection of all input datasets"""
    if frequency_raster_path is None:
        frequency_raster_path = '/g/data/v10/testing_ground/wofs_summary/frequency.vrt'
        assert geobox is not None

    raw_freq = rasterfile_to_xarray(frequency_raster_path, geobox=geobox, name='freq')

    if geobox is None:
        geobox = raw_freq.geobox

    everything = ancilliary_experts(geobox) + [raw_freq]

    result = xarray.concat(everything, dim='variable')
    return result if not return_freq else (result, raw_freq)


def training_data(max_tiles=None):
    """
    This gets the synthesis of data over the training areas,
    and unmasked subset (e.g. clear count must also be nonzero)
    """

    def generate_parts():
        for area in glob.glob('/g/data/u46/wofs/confidence/Training/*.tif')[:max_tiles]:
            training = rasterfile_to_xarray(area, name='training')

            clear_path = '/g/data/v10/testing_ground/wofs_summary/clear.vrt'
            clear = rasterfile_to_xarray(clear_path, geobox=training.geobox, name='clear_counts')

            mask = (clear.data > 0) & (training.data != 0)
            # del clear

            data = synthesis(geobox=training.geobox)

            Y_subset = (training.data[mask] == 2)
            T_subset = data.data[np.broadcast_to(mask, data.shape)].reshape((len(data), len(Y_subset)))

            yield Y_subset, T_subset

    Ys, Ts = map(np.hstack, zip(*generate_parts()))

    return Ys, Ts


model_path = '/g/data/v10/testing_ground/wofs_summary/logistic_model.pkl'


def train():
    print('Loading..')

    Ys, Ts = training_data()  # 8 works, 10 the kernel dies.

    model = sklearn.linear_model.LogisticRegression(tol=1e-7, class_weight='balanced')

    print('Fitting..')

    model.fit(Ts.T, Ys)

    print('Coefficients:')
    print(model.coef_)
    print('Intercept:')
    print(model.intercept_)

    with open(model_path, 'wb') as f:
        pickle.dump(model, f)

    return model


def process(filename, model, threshold=0.5):
    assert "frequency" in filename
    out1 = filename.replace("frequency", "confidence")
    out2 = filename.replace("frequency", "filtered")
    import os.path
    assert not os.path.isfile(out1)
    assert not os.path.isfile(out2)
    factors, freq = synthesis(filename, return_freq=True)
    X = factors.data.reshape((len(factors), -1)).T
    X = np.nan_to_num(X)  # NaN -> zero
    P = model.predict_proba(X)
    conf = P[:, 1].reshape(freq.shape)
    conf = numpy_to_xarray(conf, freq.geobox)

    write(out1, conf.astype(np.float32))

    freq.data[conf.data <= threshold] = np.nan
    filt = freq

    write(out2, filt.astype(np.float32), nodata=np.nan)


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python confidence.py *frequency*.tif")
        print("Example: /usr/bin/time find /g/data/v10/testing_ground/wofs_summary/ -maxdepth 1 "
              "-name */*frequency.tif | xargs -n 10 -P8 python confidence.py")
        raise SystemExit
    elif len(sys.argv) == 2 and sys.argv[1] == '--retrain':
        model = train()
        print('Done.')
    else:
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        for filename in sys.argv[1:]:
            process(filename, model)
