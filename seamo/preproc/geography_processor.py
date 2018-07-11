import os
import pandas as pd
import geopandas as gpd
from fiona.crs import from_epsg
from shapely.geometry import Polygon
from shapely.ops import cascaded_union
from geopandas.tools import sjoin
import spatial_overlays as sp
# import matplotlib.pyplot as plt


# plt.rcParams["figure.figsize"] = [16, 9] #optional

def read_file_into_dataframe(desired_geometry, name, crs):
    # shapefile filepath
    desired_geometry = str(desired_geometry) + '.shp'
    FP = os.path.join(os.pardir, os.pardir,
        'seamo/data/raw/shapefiles/', desired_geometry)

    # read filepath into dataframe
    df = gpd.read_file(FP)

    # convert stateplane to lat/long
    df = df.to_crs({'init': 'epsg:4326'})

    # select desired columns and convert into geodataframe
    if desired_geometry == 'blkgrp10_shore' + '.shp':
        gdf = gpd.GeoDataFrame(df.loc[:, (name, 'Shape_area', 'geometry')],
            crs=crs, geometry='geometry')

        # process columns from geodataframe
        tract_blkgrp = gdf.loc[:, 'GEO_ID_GRP'].str[6:].astype(str)
        geometry = gdf.loc[:, 'geometry']
        area = gdf.loc[:, 'Shape_area']

        # convert series back to dataframe
        tract_blkgrp.to_frame(name='tract_blkgrp')
        geometry.to_frame(name='geometry')
        area.to_frame(name='area')
        gdf = pd.concat([tract_blkgrp, geometry, area],axis=1)
        gdf.columns = ['tract_blkgrp', 'geometry', 'area']
    else:
        gdf = gpd.GeoDataFrame(df.loc[:, (name, 'geometry')],
            crs=crs, geometry='geometry')
        gdf.columns = ['key', 'geometry']
    return gdf


def process_data(desired_geometry, name, crs, outline, rectangle):
    gdf = read_file_into_dataframe(desired_geometry, name, crs)
    seattle = sp.spatial_overlays(outline, rectangle, how='intersection')
    seattle = seattle.drop(['idx1', 'idx2'], axis=1)
    seattle.crs = from_epsg(4326)
    seattle.crs = gdf.crs

    # spatial join between king county and seattle
    data = sjoin(gdf, seattle, op='intersects')
    data = data[['key', 'geometry']]
    mask = data.key.duplicated(keep='first')
    data = data[~mask]

    # plot map
    # data.plot(cmap="tab20b")
    return data


def seattle_outline(df, crs):
    blkgrps = df.geometry
    polygons = blkgrps
    boundary = gpd.GeoSeries(cascaded_union(polygons))
    # boundary.plot(color = 'red')
    # plt.show()
    boundary.crs = from_epsg(4326)
    outline = gpd.GeoDataFrame(boundary, crs=crs)
    outline.columns = ['geometry']
    return outline


def write_to_csv(desired_output, data):
    desired_output = str(desired_output) + '.csv'
    PRCOESSED_FP = os.path.join(os.pardir, os.pardir,
        'seamo/data/processed/csv_files/', desired_output)
    data.to_csv(PRCOESSED_FP)


def main():
    # create boundary for seattle
    crs = {'init': 'epsg:4326'}
    rectangle = gpd.GeoDataFrame([Polygon([(-122.435896, 47.734000),
        (-122.285766, 47.734000),
        (-122.285766, 47.735004),
        (-122.246627, 47.683255),
        (-122.245314, 47.495860),
        (-122.435896, 47.495860)])],
        columns=['geometry'], geometry='geometry')
    rectangle.crs = from_epsg(4326)

    # Block Group
    # shape file and correlation csv filepaths
    SEATTLE_FP = 'seamo/data/raw/SeattleCensusBlocksandNeighborhoodCorrelationFile.xlsx'
    SEATTLE_FP = os.path.join(os.pardir, os.pardir, SEATTLE_FP)

    # read filepath into dataframe
    seattle_data = pd.read_excel(SEATTLE_FP)

    # select desired columns
    s_data = seattle_data.loc[:, 'GEOID10'].astype(str).str[6:12].unique()

    # process Seattle correlation dataframe
    s = pd.DataFrame(s_data.astype(str))
    s.columns = ['tract_blkgrp']

    # process King County correlation dataframe
    gdf = read_file_into_dataframe('blkgrp10_shore', 'GEO_ID_GRP', crs)

    # inner join on Seattle census tract/block groups
    gdf = pd.merge(s, gdf, left_on='tract_blkgrp',
        right_on='tract_blkgrp', how='inner')

    # convert pandas dataframe to geopandas dataframe
    gdf = gpd.GeoDataFrame(gdf, crs=crs, geometry='geometry')
    gdf.crs = from_epsg(4326)

    # overlay boundary of seattle with current outline to remove noise
    data = sp.spatial_overlays(gdf, rectangle, how='intersection')
    data = data[['tract_blkgrp', 'area', 'geometry']]

    # plot map
    # data.plot(cmap="tab20b")

    # calculate centroids
    centroids = data.geometry.centroid
    data['tract_blkgrp'] = '530330' + data['tract_blkgrp'].astype(str)
    blkgrps = pd.concat([data, centroids.y, centroids.x], axis=1)
    blkgrps.columns = ['geoid', 'area', 'geometry', 'lat', 'long']

    # outline of seattle used for overlay intersection
    outline = seattle_outline(blkgrps, crs)

    # Short Neighborhood
    short_nbhd = process_data('Neighborhoods', 'S_Hood',
        crs, outline, rectangle)

    # Long Neighborhood
    long_nbhd = process_data('Neighborhoods', 'N_Hood',
        crs, outline, rectangle)

    # Council District
    coucil_districts = process_data('sccdst', 'NAME',
        crs, outline, rectangle)

    # Zipcode
    zipcodes = process_data('zipcode', 'ZIPCODE',
        crs, outline, rectangle)

    # Urban Village
    urban_villages = process_data('DPD_uvmfg_polygon', 'UV_NAME',
        crs, outline, rectangle)

    # write to csv file
    write_to_csv('SeattleShortNeighborhoods', short_nbhd)
    write_to_csv('SeattleLongNeighborhoods', long_nbhd)
    write_to_csv('SeattleCouncilDistricts', coucil_districts)
    write_to_csv('SeattleZipcodes', zipcodes)
    write_to_csv('SeattleUrbanVillages', urban_villages)
    write_to_csv('SeattleCensusBlockGroups', blkgrps)


if __name__ == "__main__":
    main()