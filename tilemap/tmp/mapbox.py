#%%
import os
import time
import math
import urllib
import requests
import pandas as pd
from tqdm import tqdm
import geopandas as gpd
from vt2geojson.tools import vt_bytes_to_geojson

#%%
def lnglatToTileXY(lng,lat,zoom):
    tileX = math.floor((lng+180)/360 * pow(2,zoom))
    tileY = math.floor( (0.5 -( math.log( math.tan( lat * math.pi / 180) + ( 1/math.cos( lat*math.pi /180)) , math.e) /2/math.pi) )* pow(2,zoom))
    return tileX, tileY

def save_pbf_2():
    MAPBOX_ACCESS_TOKEN = "pk.eyJ1IjoiZ2FuamluZyIsImEiOiJja2F3NXZ3aGQxOXY2MzBwaGczaHg2dTJhIn0.rm_hFeTmW-jpjItvpJUd8Q"
    x = 3344
    y = 1786
    z = 12

    url = f'https://api.mapbox.com/v4/mapbox.mapbox-terrain-v2,mapbox.mapbox-streets-v7/{z}/{x}/{y}.vector.pbf?access_token={MAPBOX_ACCESS_TOKEN}'
    r = requests.get(url)
    assert r.status_code == 200, r.content
    vt_content = r.content
    with open('tile.pbf', 'wb') as f:
        f.write(vt_content)
    pass

def save_pbf( zoom, x, y, path = None ):
    access_token = 'pk.eyJ1IjoiZ2FuamluZyIsImEiOiJja2F3NXZ3aGQxOXY2MzBwaGczaHg2dTJhIn0.rm_hFeTmW-jpjItvpJUd8Q'
    url = f'https://api.mapbox.com/v4/mapbox.mapbox-terrain-v2,mapbox.mapbox-streets-v7/{zoom}/{x}/{y}.vector.pbf?access_token={access_token}'
    # headers= send_headers[random.randint(0,len(send_headers)-1)]
    request = urllib.request.Request(url=url, method='GET')
    res = urllib.request.urlopen(request)
    if path:
        f = open(path, 'wb')
        f.write(res.read());  # write并不是直接将数据写入文件，而是先写入内存中特定的缓冲区
    # https://api.mapbox.com/v4/mapbox.mapbox-terrain-v2,mapbox.mapbox-streets-v7/13/6690/3568.vector.pbf?access_token=pk.eyJ1IjoiZ2FuamluZyIsImEiOiJja2F3NXZ3aGQxOXY2MzBwaGczaHg2dTJhIn0.rm_hFeTmW-jpjItvpJUd8Q
    pass

def crawl_by_area( fn = './input/深圳.geojson', zoom = 16, DIR_TILE = './tile/' ):
    area = gpd.read_file(fn)
    bbox = area.envelope[0].bounds

    point0, point1 = (bbox[0], bbox[1]), (bbox[2], bbox[3]) 
    tileX0, tileY0 = lnglatToTileXY(point0[0],point1[1],zoom)
    tileX1, tileY1 = lnglatToTileXY(point1[0],point0[1],zoom)

    # zoom = 12
    # tileX0,tileX1, tileY0,tileY1 = [3340, 3348, 2308, 2315]
    for x in tqdm(range( tileX0, tileX1+1 )):
        dir_x = os.path.join( DIR_TILE, f'{zoom}/{x}' )
        if not os.path.exists(dir_x):
            os.makedirs(dir_x)
        for y in range( tileY0, tileY1+1 ):
            file_fn = f'{dir_x}/{y}.pbf'
            if os.path.exists(file_fn):
                continue
            save_pbf( zoom, x , y, file_fn )
        time.sleep(1)


#%%
if __name__ == "__main__":
    crawl_by_area( )
    pass



# %%

    # pbf parser 解析

    with open('tile.pbf', 'rb') as f:
        vt_content = f.read()
    features = vt_bytes_to_geojson(vt_content, x, y, z)
    gdf = gpd.GeoDataFrame.from_features(features)

    layers = gdf.name.unique()
    item = 'road'
    gdf.query( f"name == '{item}'" ).dropna(axis=1).plot()
    gdf.query( f"name == '{item}'" ).dropna(axis=1)

    gdf.query( f"name == '{item}'" ).dropna(axis=1)['class'].unique()

