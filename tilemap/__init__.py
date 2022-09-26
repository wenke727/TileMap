from .tile import TileMap, CACHE_FOLDER, set_logger
from ._providers import providers, TileProvider, Baidu, Amap, OpenStreetMap
from .plotting import add_basemap, plot_geodata

__version__ = "1.1.0"