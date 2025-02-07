import pandas as pd
import os
import geocoder as geo
import geocoder_input as gi
import geopandas as gpd
from shapely.geometry import Point

FILEPATH = os.path.join(os.pardir, os.pardir, 'seamo/data/')
DATADIR = os.path.join(os.pardir, os.pardir, 'seamo/data/raw/shapefiles/')
PROCESSED_DIR = os.path.join(os.pardir, os.pardir, 'seamo/data/processed/')

def get_latlon_csv(input_file):
    fp = FILEPATH + str(input_file) + '.csv'
    df = pd.read_csv(fp)
    lat = df['lat']
    lon = df ['lon']
    coords = pd.concat([lat, lon], axis=1)
    coords['geometry'] = coords.apply(lambda x: Point((float(x[1]), float(x[0]))), axis=1)
    coords = gpd.GeoDataFrame(coords, geometry='geometry')
    coords.crs = {'init': 'epsg:4326'}
    return df, coords

full, coords = get_latlon_csv('KCSales1')
blkgrp = gi.read_shapefile('blkgrp10_shore', 'GEO_ID_GRP', 'Block_Group', DATADIR).drop(columns='geography')
df = gpd.sjoin(coords, blkgrp, how = 'left')
df = df.drop(columns = ['index_right', 'geometry'], axis=1)
df = df.sort_values(by='key')
df = pd.DataFrame(df)
df = df.fillna('N/A')
df.columns = ['lat', 'lon', 'blkgrp']
df['lat'] = df['lat'].astype(float)
df['lon'] = df['lon'].astype(float)
final = pd.merge(full, df, how='inner', left_on=['lat', 'lon'], right_on=['lat', 'lon'])
final = final.drop_duplicates(keep='first')
final = final.reset_index()
final = final.drop(columns=['index', 'Unnamed: 0'], axis=1)
geo.write_to_csv(final, PROCESSED_DIR, 'KCSales1_blkgrps.csv')