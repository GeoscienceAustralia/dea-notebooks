import cartopy.crs as ccrs

def plot_towns(ax, lats, lons, resolution='10m', transform=ccrs.PlateCarree(), zorder=3):
    """
    This function will download the 'populated_places' shapefile from
    NaturalEarth, trim the shapefile based on the limits of the provided
    lat & long coords, and then plot the locations and names of the towns
    on a given GeoAxes.
    
    ax = a pyplot axes object
    lats = latitudes, as an xarray object
    lons = longitudes, as an xarray object
    resolution= str. either high res:'10m' or low res: '50m'
    transform = a cartopy crs object
    """
    #get town locations
    shp_fn = shpreader.natural_earth(resolution=resolution, category='cultural', name='populated_places')
    shp = shpreader.Reader(shp_fn)
    xy = [pt.coords[0] for pt in shp.geometries()]
    x, y = list(zip(*xy))

    #get town names
    towns = shp.records()
    names_en = []
    for town in towns:
        names = town.attributes['name_en']
        names_en.append(names)

    #create data frame and index by the region of the plot
    all_towns = pd.DataFrame({'names_en': names_en, 'x':x, 'y':y})
    region_towns = all_towns[(all_towns.y<np.max(lats.values)) & (all_towns.y>np.min(lats.values))
                           & (all_towns.x>np.min(lons.values)) & (all_towns.x<np.max(lons.values))]

    #plot the locations and labels of the towns in the region
    ax.scatter(region_towns.x.values, region_towns.y.values, c ='black', marker= '.', transform=transform, zorder=zorder)
    transform_mpl = crs.PlateCarree()._as_mpl_transform(ax) #this is a work-around to transform xy coords in ax.annotate
    for i, txt in enumerate(region_towns.names_en):
         ax.annotate(txt[:3], (region_towns.x.values[i], region_towns.y.values[i]), xycoords=transform_mpl)