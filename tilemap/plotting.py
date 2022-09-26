from ast import arg
import matplotlib.pyplot as plt
from rasterio.enums import Resampling
from contextily.plotting import _reproj_bb, add_attribution
from contextily.tile import warp_tiles

from . import providers as PROVIDERS
from . import TileProvider
from .tile import TileMap, PROVIDERS, CACHE_FOLDER

ZOOM = "auto"
ATTRIBUTION_SIZE = 8
INTERPOLATION = "bilinear"

def add_basemap(
    ax,
    zoom=ZOOM,
    provider=None,
    interpolation=INTERPOLATION,
    attribution=None,
    attribution_size=ATTRIBUTION_SIZE,
    reset_extent=True,
    crs=None,
    resampling=Resampling.bilinear,
    cache_folder=None,
    **extra_imshow_args
):
    """
    Add a (web/local) basemap to `ax`.

    Parameters
    ----------
    ax : AxesSubplot
        Matplotlib axes object on which to add the basemap. The extent of the
        axes is assumed to be in Spherical Mercator (EPSG:3857), unless the `crs`
        keyword is specified.
    zoom : int or 'auto'
        [Optional. Default='auto'] Level of detail for the basemap. If 'auto',
        it is calculated automatically. Ignored if `source` is a local file.
    source : contextily.providers object or str
        [Optional. Default: Stamen Terrain web tiles]
        The tile source: web tile provider or path to local file. The web tile
        provider can be in the form of a `contextily.providers` object or a
        URL. The placeholders for the XYZ in the URL need to be `{x}`, `{y}`,
        `{z}`, respectively. For local file paths, the file is read with
        `rasterio` and all bands are loaded into the basemap.
        IMPORTANT: tiles are assumed to be in the Spherical Mercator
        projection (EPSG:3857), unless the `crs` keyword is specified.
    interpolation : str
        [Optional. Default='bilinear'] Interpolation algorithm to be passed
        to `imshow`. See `matplotlib.pyplot.imshow` for further details.
    attribution : str
        [Optional. Defaults to attribution specified by the source]
        Text to be added at the bottom of the axis. This
        defaults to the attribution of the provider specified
        in `source` if available. Specify False to not
        automatically add an attribution, or a string to pass
        a custom attribution.
    attribution_size : int
        [Optional. Defaults to `ATTRIBUTION_SIZE`].
        Font size to render attribution text with.
    reset_extent : bool
        [Optional. Default=True] If True, the extent of the
        basemap added is reset to the original extent (xlim,
        ylim) of `ax`
    crs : None or str or CRS
        [Optional. Default=None] coordinate reference system (CRS),
        expressed in any format permitted by rasterio, to use for the
        resulting basemap. If None (default), no warping is performed
        and the original Spherical Mercator (EPSG:3857) is used.
    resampling : <enum 'Resampling'>
        [Optional. Default=Resampling.bilinear] Resampling
        method for executing warping, expressed as a
        `rasterio.enums.Resampling` method
    url : str [DEPRECATED]
        [Optional. Default: 'http://tile.stamen.com/terrain/{z}/{x}/{y}.png']
        Source url for web tiles, or path to local file. If
        local, the file is read with `rasterio` and all
        bands are loaded into the basemap.
    **extra_imshow_args :
        Other parameters to be passed to `imshow`.

    Examples
    --------

    >>> import geopandas
    >>> import contextily as ctx
    >>> db = geopandas.read_file(ps.examples.get_path('virginia.shp'))

    Ensure the data is in Spherical Mercator:

    >>> db = db.to_crs(epsg=3857)

    Add a web basemap:

    >>> ax = db.plot(alpha=0.5, color='k', figsize=(6, 6))
    >>> ctx.add_basemap(ax, source=url)
    >>> plt.show()

    Or download a basemap to a local file and then plot it:

    >>> source = 'virginia.tiff'
    >>> _ = ctx.bounds2raster(*db.total_bounds, zoom=6, source=source)
    >>> ax = db.plot(alpha=0.5, color='k', figsize=(6, 6))
    >>> ctx.add_basemap(ax, source=source)
    >>> plt.show()

    """
    xmin, xmax, ymin, ymax = ax.axis()

    # If web source
    if provider is None:
        provider = PROVIDERS.Amap.Satellite
    assert isinstance(provider, (dict, TileProvider)), "Check provider info"

    # Extent
    left, right, bottom, top = xmin, xmax, ymin, ymax
    # Convert extent from `crs` into WM for tile query
    if crs is not None:
        left, right, bottom, top = _reproj_bb(
            left, right, bottom, top, crs, {"init": "epsg:3857"}
        )
    # Download image
    cfg = {"provider": provider, "cache_folder": cache_folder}
    tile_processor = TileMap(**cfg)
    
    image, extent = tile_processor.bounds2img(
        left, bottom, right, top, zoom=zoom, ll=True
    )
    # Warping
    if crs is not None:
        image, extent = warp_tiles(image, extent, t_crs=crs, resampling=resampling)
    # Check if overlay
    if _is_overlay(provider) and 'zorder' not in extra_imshow_args:
        # If zorder was not set then make it 9 otherwise leave it
        extra_imshow_args['zorder'] = 9

    # Plotting
    if image.shape[2] == 1:
        image = image[:, :, 0]
    img = ax.imshow(
        image, extent=extent, interpolation=interpolation, **extra_imshow_args
    )

    if reset_extent:
        ax.axis((xmin, xmax, ymin, ymax))
    else:
        max_bounds = (
            min(xmin, extent[0]),
            max(xmax, extent[1]),
            min(ymin, extent[2]),
            max(ymax, extent[3]),
        )
        ax.axis(max_bounds)

    # Add attribution text
    if provider is None:
        provider = PROVIDERS.Amap.Satellite
    if isinstance(provider, (dict, TileProvider)) and attribution is None:
        attribution = provider.get("attribution")
    if attribution:
        add_attribution(ax, attribution, font_size=attribution_size)

    return


def plot_geodata(
    gdf,
    figsize=(12,9),
    zoom=ZOOM,
    provider=None,
    interpolation=INTERPOLATION,
    attribution=False,
    attribution_size=ATTRIBUTION_SIZE,
    reset_extent=True,
    crs=None,
    resampling=Resampling.bilinear,
    cache_folder=None,
    fn=None,
    extra_imshow_args={},
    *args,
    **extra_plot_args
):
    """
    Visual geodataframe.

    Parameters
    ----------
    gdf : AxesSubplot
        Matplotlib axes object on which to add the basemap. The extent of the
        axes is assumed to be in Spherical Mercator (EPSG:3857), unless the `crs`
        keyword is specified.
    zoom : int or 'auto'
        [Optional. Default='auto'] Level of detail for the basemap. If 'auto',
        it is calculated automatically. Ignored if `source` is a local file.
    source : contextily.providers object or str
        [Optional. Default: Stamen Terrain web tiles]
        The tile source: web tile provider or path to local file. The web tile
        provider can be in the form of a `contextily.providers` object or a
        URL. The placeholders for the XYZ in the URL need to be `{x}`, `{y}`,
        `{z}`, respectively. For local file paths, the file is read with
        `rasterio` and all bands are loaded into the basemap.
        IMPORTANT: tiles are assumed to be in the Spherical Mercator
        projection (EPSG:3857), unless the `crs` keyword is specified.
    interpolation : str
        [Optional. Default='bilinear'] Interpolation algorithm to be passed
        to `imshow`. See `matplotlib.pyplot.imshow` for further details.
    attribution : str
        [Optional. Defaults to attribution specified by the source]
        Text to be added at the bottom of the axis. This
        defaults to the attribution of the provider specified
        in `source` if available. Specify False to not
        automatically add an attribution, or a string to pass
        a custom attribution.
    attribution_size : int
        [Optional. Defaults to `ATTRIBUTION_SIZE`].
        Font size to render attribution text with.
    reset_extent : bool
        [Optional. Default=True] If True, the extent of the
        basemap added is reset to the original extent (xlim,
        ylim) of `ax`
    crs : None or str or CRS
        [Optional. Default=None] coordinate reference system (CRS),
        expressed in any format permitted by rasterio, to use for the
        resulting basemap. If None (default), no warping is performed
        and the original Spherical Mercator (EPSG:3857) is used.
    resampling : <enum 'Resampling'>
        [Optional. Default=Resampling.bilinear] Resampling
        method for executing warping, expressed as a
        `rasterio.enums.Resampling` method
    url : str [DEPRECATED]
        [Optional. Default: 'http://tile.stamen.com/terrain/{z}/{x}/{y}.png']
        Source url for web tiles, or path to local file. If
        local, the file is read with `rasterio` and all
        bands are loaded into the basemap.
    **extra_imshow_args :
        Other parameters to be passed to `imshow`.

    Examples
    --------

    >>> import geopandas
    >>> import contextily as ctx
    >>> db = geopandas.read_file(ps.examples.get_path('virginia.shp'))

    Ensure the data is in Spherical Mercator:

    >>> db = db.to_crs(epsg=3857)

    Add a web basemap:

    >>> ax = db.plot(alpha=0.5, color='k', figsize=(6, 6))
    >>> ctx.add_basemap(ax, source=url)
    >>> plt.show()

    Or download a basemap to a local file and then plot it:

    >>> source = 'virginia.tiff'
    >>> _ = ctx.bounds2raster(*db.total_bounds, zoom=6, source=source)
    >>> ax = db.plot(alpha=0.5, color='k', figsize=(6, 6))
    >>> ctx.add_basemap(ax, source=source)
    >>> plt.show()
    """
    fig, ax = plt.subplots(1, 1, figsize=figsize)
    
    gdf.plot(ax=ax, *args, **extra_plot_args)
    add_basemap(ax, zoom, provider, interpolation, attribution, attribution_size, reset_extent, crs, resampling, cache_folder, **extra_imshow_args)
    
    # 去除科学记数法
    ax.get_xaxis().get_major_formatter().set_useOffset(False)
    ax.get_yaxis().get_major_formatter().set_useOffset(False)
    
    if fn is not None:
        fig.savefig(fn, dpi=300, bbox_inches='tight', pad_inches=0.1)
    
    return fig, ax


def _is_overlay(source):
    """
    Check if the identified source is an overlay (partially transparent) layer.
    Parameters
    ----------
    source : dict
        The tile source: web tile provider.  Must be preprocessed as
        into a dictionary, not just a string.
    Returns
    -------
    bool
    Notes
    -----
    This function is based on a very similar javascript version found in leaflet:
    https://github.com/leaflet-extras/leaflet-providers/blob/9eb968f8442ea492626c9c8f0dac8ede484e6905/preview/preview.js#L56-L70
    """
    if not isinstance(source, dict):
        return False
    if source.get('opacity', 1.0) < 1.0:
        return True
    overlayPatterns = [
        '^(OpenWeatherMap|OpenSeaMap)',
        'OpenMapSurfer.(Hybrid|AdminBounds|ContourLines|Hillshade|ElementsAtRisk)',
        'Stamen.Toner(Hybrid|Lines|Labels)',
        'CartoDB.(Positron|DarkMatter|Voyager)OnlyLabels',
        'Hydda.RoadsAndLabels',
        '^JusticeMap',
        'OpenPtMap',
        'OpenRailwayMap',
        'OpenFireMap',
        'SafeCast'
    ]
    import re
    return bool(re.match('(' + '|'.join(overlayPatterns) + ')', source.get('name', '')))

