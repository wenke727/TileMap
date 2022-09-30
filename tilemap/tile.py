#%%
import io
import os
import sys
import time
import random
import numpy as np
from PIL import Image
import mercantile as mt
from pathlib import Path
from loguru import logger
import matplotlib.pyplot as plt

from contextily.tile import _sm2ll, _validate_zoom, _merge_tiles


from .misc import get_proxy, http_retryer
from .parallel import parallel_process
from ._providers import providers as PROVIDERS
from .coordtransform import wgs84_to_gcj02, gcj02_to_wgs84
from .coordtransform import wgs84_to_bd09, bd09_to_wgs84
# merge_tiles_bd, tiles_bd

logger.remove()
CACHE_FOLDER = "/home/pcl/minio/tile"


#%%
def set_logger(stderr=True, folder=None, level="INFO"):
    logger.remove()
    cfg = {"enqueue": True, "backtrace": True, "diagnose": True, "level": level}
    
    if stderr:
        logger.add(sys.stderr, **cfg)
    if folder is not None:
        fn = os.path.join(folder, f"{time.strftime('%Y-%m-%d', time.localtime())}.log")
        logger.add(fn, **cfg)
    
    return logger


def set_tile_cache_floder(folder):
    global CACHE_FOLDER
    CACHE_FOLDER = folder


class TileMap():
    def __init__(self, provider=None, cache_folder=CACHE_FOLDER, proxy_pool_api=None):
        self.provider = provider
        if provider is None:
            self.provider = PROVIDERS.Amap.Satellite 

        if cache_folder is None:
            cache_folder = CACHE_FOLDER
        self.cache_folder = Path(cache_folder) / self.provider.name
        self.cache_folder.mkdir(exist_ok=True)
        
        self.logger = logger
        self.tile_coord_sys = self.provider.get('sys', 'wgs')
        self.proxy_pool_api = proxy_pool_api
        
        assert self.tile_coord_sys in ['wgs', 'gcj', 'bd'], \
            f"Check {self.provider}'s tile coordination system is within ['wgs', 'gcj', 'bd']."
        self._cfg_transform_funs()
    

    def _fetch_tile(self, tile:mt.Tile, wait=.5, max_retries=2):
        x, y, z = tile.x, tile.y, tile.z
        url = self._construct_tile_url(x, y, z)
        _validate_zoom(z, self.provider, auto='auto')
        fn = self.cache_folder/ str(z) / str(x) / f"{y}.png"
        
        if fn.exists():
            self.logger.trace(f"Using cache file: {'/'.join(fn.parts[-4:])}")
            array = np.array(Image.open(fn).convert("RGBA"))
            return tile, array
        
        proxy = get_proxy(self.proxy_pool_api)
        self.logger.debug(f"Fetching tile: {url}, {proxy}")
        request = http_retryer(url, wait, max_retries, proxy)

        fn.parent.mkdir(parents=True, exist_ok=True)
        with io.BytesIO(request.content) as image_stream:
            image = Image.open(image_stream)
            image.save(fn)
            image = image.convert("RGBA")
            array = np.asarray(image)
            image.close()
        
        return tile, array


    def fetch_tile_xyz(self, x, y, z, wait=.5, max_retries=2):
        tile = mt.Tile(x, y, z)
        return self._fetch_tile(tile, wait, max_retries)
        

    def fetch_tile_ll(self, lng, lat, zoom, wait=.5, max_retries=2):
        tile = self.ll_2_tile(lng, lat, zoom)
        return self._fetch_tile(tile, wait, max_retries)


    def fetch_tiles(self, w, s, e, n, geofence=None, ll=True, zoom="auto", n_jobs=-1, wait=0.5, max_retries=2):
        # TODO 增加 filter 机制 -> gpd.sjoin
        if self.proxy_pool_api is None:
            n_jobs = 1

        if self.tile_coord_sys in ['gcj', 'bd']:
            w, s = self.from_wgs(w, s)
            e, n = self.from_wgs(e, n)
        
        # calculate and validate zoom level
        auto_zoom = zoom == "auto"
        if auto_zoom:
            zoom = self._calculate_zoom(w, s, e, n)
        zoom = _validate_zoom(zoom, self.provider, auto=auto_zoom)

        # download and merge tiles
        tiles_lst = [(i, wait, max_retries) for i in self.iter_tiles(w, s, e, n, [zoom])]
        res = parallel_process(self._fetch_tile, tiles_lst, pbar_switch=True, n_jobs=n_jobs)
        tiles = [r[0] for r in res]
        arrays = [r[1] for r in res]

        return tiles, arrays


    def bounds2img(self, w, s, e, n, zoom="auto", ll=True, wait=0, max_retries=2):
        """
        Take bounding box and zoom and return an image with all the tiles
        that compose the map and its Spherical Mercator extent.

        Parameters
        ----------
        w : float
            West edge
        s : float
            South edge
        e : float
            East edge
        n : float
            North edge
        zoom : int
            Level of detail
        source : contextily.providers object or str
            [Optional. Default: Stamen Terrain web tiles]
            The tile source: web tile provider or path to local file. The web tile
            provider can be in the form of a `contextily.providers` object or a
            URL. The placeholders for the XYZ in the URL need to be `{x}`, `{y}`,
            `{z}`, respectively. For local file paths, the file is read with
            `rasterio` and all bands are loaded into the basemap.
            IMPORTANT: tiles are assumed to be in the Spherical Mercator
            projection (EPSG:3857), unless the `crs` keyword is specified.
        ll : Boolean
            [Optional. Default: False] If True, `w`, `s`, `e`, `n` are
            assumed to be lon/lat as opposed to Spherical Mercator.
        wait : int
            [Optional. Default: 0]
            if the tile API is rate-limited, the number of seconds to wait
            between a failed request and the next try
        max_retries: int
            [Optional. Default: 2]
            total number of rejected requests allowed before contextily
            will stop trying to fetch more tiles from a rate-limited API.
        url : str [DEPRECATED]
            [Optional. Default: 'http://tile.stamen.com/terrain/{z}/{x}/{y}.png']
            URL for tile provider. The placeholders for the XYZ need to be
            `{x}`, `{y}`, `{z}`, respectively. IMPORTANT: tiles are
            assumed to be in the Spherical Mercator projection (EPSG:3857).

        Returns
        -------
        img : ndarray
            Image as a 3D array of RGB values
        extent : tuple
            Bounding box [minX, maxX, minY, maxY] of the returned image
        """
        if not ll:
            # Convert w, s, e, n into lon/lat
            w, s = _sm2ll(w, s)
            e, n = _sm2ll(e, n)
            ll = True
        
        if self.tile_coord_sys in ['gcj', 'bd']:
            w, s = self.from_wgs(w, s)
            e, n = self.from_wgs(e, n)
        
        merged, extent = self._bounds2img_wgs(w, s, e, n, zoom, ll, wait, max_retries)

        if ll and self.tile_coord_sys in ['gcj', 'bd']:
            west, east, south, north = extent
            west, south = self.to_wgs(west, south) 
            east, north = self.to_wgs(east, north)
            extent = west, east, south, north
        
        return merged, extent
        
        
    def _bounds2img_wgs(self, w, s, e, n, zoom="auto", ll=False, wait=0.5, max_retries=2):
        # TODO 增加 抓取进度条的问题，通过日志体现
        # TODO 多进程获取数据 

        # calculate and validate zoom level
        auto_zoom = zoom == "auto"
        if auto_zoom:
            zoom = self._calculate_zoom(w, s, e, n)
        zoom = _validate_zoom(zoom, self.provider, auto=auto_zoom)

        # download and merge tiles
        tiles = []
        arrays = []
        # tiles_lst = list(self.tiles_func(w, s, e, n, [zoom]))
        for t in self.iter_tiles(w, s, e, n, [zoom]):
            _, image = self._fetch_tile(t, wait, max_retries)
            
            tiles.append(t)
            arrays.append(image)

        merged, extent = self.merge_tile(tiles, arrays)
        
        west, south, east, north = extent
        if ll:
            extent = west, east, south, north
        else:
            # lon/lat extent --> Spheric Mercator
            left, bottom = mt.xy(west, south)
            right, top = mt.xy(east, north)
            extent = left, right, bottom, top
        
        return merged, extent


    def howmany(self, w, s, e, n, zoom, verbose=True, ll=False):
        """
        Number of tiles required for a given bounding box and a zoom level

        Parameters
        ----------
        w : float
            West edge
        s : float
            South edge
        e : float
            East edge
        n : float
            North edge
        zoom : int
            Level of detail
        verbose : Boolean
            [Optional. Default=True] If True, print short message with
            number of tiles and zoom.
        ll : Boolean
            [Optional. Default: False] If True, `w`, `s`, `e`, `n` are
            assumed to be lon/lat as opposed to Spherical Mercator.
        """
        if not ll:
            # Convert w, s, e, n into lon/lat
            w, s = _sm2ll(w, s)
            e, n = _sm2ll(e, n)
        if zoom == "auto":
            zoom = self._calculate_zoom(w, s, e, n)
        tiles = len(list(mt.tiles(w, s, e, n, [zoom])))
        if verbose:
            print("Using zoom level %i, this will download %i tiles" % (zoom, tiles))
        return tiles


    def _calculate_zoom(self, w, s, e, n):
        """Automatically choose a zoom level given a desired number of tiles.

        .. note:: all values are interpreted as latitude / longitutde.

        Parameters
        ----------
        w : float
            The western bbox edge.
        s : float
            The southern bbox edge.
        e : float
            The eastern bbox edge.
        n : float
            The northern bbox edge.

        Returns
        -------
        zoom : int
            The zoom level to use in order to download this number of tiles.
        """
        # Calculate bounds of the bbox
        lon_range = np.sort([e, w])[::-1]
        lat_range = np.sort([s, n])[::-1]

        lon_length = np.subtract(*lon_range)
        lat_length = np.subtract(*lat_range)

        # Calculate the zoom
        zoom_lon = np.ceil(np.log2(360 * 2.0 / lon_length))
        zoom_lat = np.ceil(np.log2(360 * 2.0 / lat_length))
        zoom = np.max([zoom_lon, zoom_lat])
        
        if 'max_zoom' in self.provider:
            zoom = min(zoom, self.provider.max_zoom)
        
        return int(zoom)


    def _construct_tile_url(self, x, y, z, provider=None):
        if provider is None:
            provider = self.provider
        
        provider = provider.copy()
        tile_url = provider.pop("url")
        subdomains = provider.pop("subdomains", None)
        r = provider.pop("r", "")
        if subdomains is not None:
            subdomains = subdomains[random.randint(0, len(subdomains)-1)]
        tile_url = tile_url.format(x=x, y=y, z=z, s=subdomains, r=r, **provider)

        return tile_url

    
    def _cfg_transform_funs(self):
        if self.tile_coord_sys in ['wgs', 'gcj']:
            self.iter_tiles  = mt.tiles
            self.ll_2_tile   = mt.tile
            self.tile_bounds = mt.bounds
            self.merge_tile  = _merge_tiles
            if self.tile_coord_sys in ['gcj']:
                self.to_wgs = gcj02_to_wgs84
                self.from_wgs = wgs84_to_gcj02
        elif self.tile_coord_sys in ['bd']:
            # 百度瓦片的编号和常规编号不一致
            from .coordtransform import baidutile
            self.iter_tiles  = baidutile.tiles_bd
            self.ll_2_tile   = baidutile.tile
            self.tile_bounds = baidutile.bounds_bd
            self.merge_tile  = baidutile.merge_tiles_bd
            self.to_wgs = bd09_to_wgs84
            self.from_wgs = wgs84_to_bd09
        


#%%
if __name__ == "__main__":
    west, south, east, north = (
        113.93329,22.57102,
        113.94413,22.58131
    )
    # 百度街景瓦片
    tile = TileMap(provider=PROVIDERS.Baidu.Tile)
    ghent_img, ghent_ext = tile.bounds2img(west, south, east, north, zoom=18, ll=True)

    # OSM 基础瓦片
    tile = TileMap(provider=PROVIDERS.OpenStreetMap.Mapnik)
    ghent_img_, ghent_ext_ = tile.bounds2img(west, south, east, north, zoom=17, ll=True)

    fig, ax = plt.subplots(1, figsize=(18, 18))
    ax.imshow(ghent_img_, extent=ghent_ext_)
    ax.imshow(ghent_img, extent=ghent_ext)
    ax.axis('off')

    # 获取单张 tile
    tile = TileMap(provider=PROVIDERS.Baidu.Tile)
    tile._fetch_tile(49543, 10089, 18)

# %%
