import math
import numpy as np
import mercantile as mt
from mercantile import tile, Sequence, LL_EPSILON

from .coordTransform_bd import bd_mc_to_coord, bd_coord_to_mc
from .coordTransform_py import bd09_to_gcj02, bd09_to_wgs84


def merge_tiles_bd(tiles, arrays):
    """
    Merge a set of tiles into a single array.

    Parameters
    ---------
    tiles : list of mercantile.Tile objects
        The tiles to merge.
    arrays : list of numpy arrays
        The corresponding arrays (image pixels) of the tiles. This list
        has the same length and order as the `tiles` argument.

    Returns
    -------
    img : np.ndarray
        Merged arrays.
    extent : tuple
        Bounding box [west, south, east, north] of the returned image
        in long/lat.
    """
    # create (n_tiles x 2) array with column for x and y coordinates
    tile_xys = np.array([(t.x, t.y) for t in tiles])
    # print(tile_xys)

    # get indices starting at zero
    indices = tile_xys - tile_xys.min(axis=0)

    # the shape of individual tile images
    h, w, d = arrays[0].shape

    # number of rows and columns in the merged tile
    n_x, n_y = (indices + 1).max(axis=0)

    # empty merged tiles array to be filled in
    img = np.zeros((h * n_y, w * n_x, d), dtype=np.uint8)

    for ind, arr in zip(indices, arrays):
        x, y = ind
        img[(n_y - y - 1) * h : (n_y - y) * h, x * w : (x + 1) * w, :] = arr

    bounds = np.array([bounds_bd(t) for t in tiles])
    west, south, east, north = (
        min(bounds[:, 0]),
        min(bounds[:, 1]),
        max(bounds[:, 2]),
        max(bounds[:, 3]),
    )

    return img, (west, south, east, north)


def tile_bd(lng, lat, zoom):
    """Get the tile by (lng, lat, zoom)

    Args:
        lng (_type_): _description_
        lat (_type_): _description_
        zoom (_type_): _description_

    Returns:
        Tile: tile index
    """
    Z2 = math.pow(2, 18 - zoom) * 256
    xtile, ytile = bd_coord_to_mc(lng, lat)
    xtile = math.floor(xtile / Z2)
    ytile = math.floor(ytile / Z2) 
    
    return mt.Tile(xtile, ytile, zoom)


def tiles_bd(west, south, east, north, zooms, truncate=False):
    """Get the tiles overlapped by a geographic bounding box

    Parameters
    ----------
    west, south, east, north : sequence of float
        Bounding values in decimal degrees.
    zooms : int or sequence of int
        One or more zoom levels.
    truncate : bool, optional
        Whether or not to truncate inputs to web mercator limits.

    Yields
    ------
    Tile

    Notes
    -----
    A small epsilon is used on the south and east parameters so that this
    function yields exactly one tile when given the bounds of that same tile.

    """
    if truncate:
        west, south = mt.truncate_lnglat(west, south)
        east, north = mt.truncate_lnglat(east, north)
    if west > east:
        bbox_west = (-180.0, south, east, north)
        bbox_east = (west, south, 180.0, north)
        bboxes = [bbox_west, bbox_east]
    else:
        bboxes = [(west, south, east, north)]

    for w, s, e, n in bboxes:
        # Clamp bounding values.
        w = max(-180.0, w)
        s = max(-85.051129, s)
        e = min(180.0, e)
        n = min(85.051129, n)

        w, s = bd_coord_to_mc(w, s)
        e, n = bd_coord_to_mc(e, n)

        if not isinstance(zooms, Sequence):
            zooms = [zooms]

        for z in zooms:
            f = math.pow(2, 18 - z) * 256
            w_, s_ = math.floor(w / f), math.floor(s / f) 
            e_, n_ = math.ceil(e / f), math.ceil(n / f)
                        
            for i in range(w_, e_ + 1):
                for j in range(s_, n_ + 1):
                    yield mt.Tile(i, j, z)


def bounds_bd(tile:mt.Tile, sys='bd'):
    """Returns the bounding box of a tile

    Parameters
    ----------
    tile : Tile
        May be be either an instance of Tile or 3 ints (X, Y, Z).

    Returns
    -------
    LngLatBbox

    """
    assert sys in ['gcj', 'wgs', 'bd']
    tile = mt._parse_tile_arg(*tile)
    xtile, ytile, zoom = tile
    f = 256 * math.pow(2, 18 - zoom)
    
    xtile *= f
    ytile *= f
    
    ul_lon_deg, lr_lat_deg = bd_mc_to_coord(xtile, ytile)
    lr_lon_deg, ul_lat_deg = bd_mc_to_coord(xtile + f, ytile + f)
    
    if sys == 'gcj':
        ul_lon_deg, lr_lat_deg = bd09_to_gcj02(ul_lon_deg, lr_lat_deg)
        lr_lon_deg, ul_lat_deg = bd09_to_gcj02(lr_lon_deg, ul_lat_deg)
    elif sys == 'wgs':
        ul_lon_deg, lr_lat_deg = bd09_to_wgs84(ul_lon_deg, lr_lat_deg)
        lr_lon_deg, ul_lat_deg = bd09_to_wgs84(lr_lon_deg, ul_lat_deg)
    
    return mt.LngLatBbox(ul_lon_deg, lr_lat_deg, lr_lon_deg, ul_lat_deg)

