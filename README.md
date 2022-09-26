# TileMap

TileMap can `crawl tiles based on bbox` and add those tiles as `basemap` to matplotlib figures or write tile maps to disk into geospatial raster files. Bounding boxes can be passed in both GCJ02/WGS84 (EPSG:4326) and Spheric Mercator (EPSG:3857).

![地图样式](https://contextily.readthedocs.io/en/latest/_images/tiles.png)

## 安装

```bash
sh install.sh
```

## 调用说明

### 下载瓦片

```python
from tilemap import TileMap, providers

# 定义瓦片提供服务商信息，以及瓦片存储位置
tile = TileMap(provider=providers.Amap.Normal, cache_folder='./tiles)

# 需要获取瓦片额范围
west, south, east, north = (
    113.93329,22.57102,
    113.94413,22.58131
)

# zoom 下载瓦片的级别，ll 表示 [west, south, east, north] 输入为经纬度
tile.bounds2img(west, south, east, north, zoom=18, ll=True)
```

### 背景瓦片绘制

- 单通道

```python
from tilemap import vis_geodata, providers

_, ax = vis_geodata(gdf, df, figsize=(6,6), alpha=.4, color='red', attribution=False, reset_extent=False)
ax.axis('off')

```

- 双通道：高德卫星影像 + 高德地图标识

```python
fig, ax = vis_geodata(df, figsize=(6,6), alpha=.4, color='red', attribution=False, reset_extent=False)
add_basemap(ax, provider=providers.Amap.Normal, attribution=False)
ax.axis('off')
```

### 瓦片定义

定义文件 `./tilemap/_providers.py`, 目前配置了三个瓦片源: OpenStreetMap, 高德卫星瓦片，高德基础地图

```python
providers = Bunch(
    OpenStreetMap = Bunch(
        Mapnik = TileProvider(
            url = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
            sys='wgs',
            subdomains = 'abc',
            max_zoom = 18,
            attribution = '(C) OpenStreetMap contributors',
            name = 'OpenStreetMap.Mapnik'
        )
    ),
    Amap = Bunch(
        Satellite = TileProvider(
            # &size=1&scale=1
            url = 'http://webst0{s}.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}',
            sys='gcj',
            max_zoom = 18,
            subdomains = '1234',
            attribution = '(C) AutoNavi',
            describe='style=6为影像图, style=7为矢量路网, style=8为影像路网',
            name = 'Amap.Satellite'
        ),
        Normal = TileProvider(
            url = 'http://webst0{s}.is.autonavi.com/appmaptile?style=8&x={x}&y={y}&z={z}',
            sys='gcj',
            max_zoom = 18,
            subdomains = '1234',
            attribution = '(C) AutoNavi',
            describe='style=6为影像图, style=7为矢量路网, style=8为影像路网',
            name = 'Amap.Normal'
        )
        
    )
)
```
