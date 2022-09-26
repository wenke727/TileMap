class Bunch(dict):
    """A dict with attribute-access"""

    def __getattr__(self, key):
        try:
            return self.__getitem__(key)
        except KeyError:
            raise AttributeError(key)

    def __dir__(self):
        return self.keys()


class TileProvider(Bunch):
    """
    A dict with attribute-access and that
    can be called to update keys
    """

    def __call__(self, **kwargs):
        new = TileProvider(self)  # takes a copy preserving the class
        new.update(kwargs)
        return new


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
            url = 'http://webst0{s}.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}', # &size=1&scale=1
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
        
    ),
    Baidu = Bunch(
        Satellite = TileProvider(
            url = "https://maponline{s}.bdimg.com/starpic/?qt=satepc&u=x={x};y={y};z={z};v=009;type=sate",
            sys='bd',
            max_zoom = 19,
            subdomains = '0123',
            attribution = '(C) Baidu contributors',
            name = 'Baidu.Satellite'
        ),
        Tile = TileProvider(
            url = "https://mapsv{s}.bdimg.com/tile/?qt=tile&styles=pl&x={x}&y={y}&z={z}",
            sys='bd',
            max_zoom = 19,
            subdomains = '01',
            attribution = '(C) Baidu contributors',
            name = 'Baidu.Tile'
        )
    ),
    Google = Bunch(
        Mapnik = TileProvider(
            url = "http://mt{s}.google.cn/vt/lyrs={lyr}@258000000&hl=zh-CN&gl=CN&src=app&s=Ga&x={x}&y={y}&z={z}",
            sys='wgs', # FIXME
            subdomains = '0123',
            max_zoom = 19,
            lyrs='mtpsyh', #Google style m：路线图 t：地形图 p：带标签的地形图 s：卫星图 y：带标签的卫星图 h：标签层（路名、地名等）
            attribution = '(C) Google contributors',
            name = 'Google.Base'
        )
    ),
)


Amap = providers.Amap
Baidu = providers.Baidu
Google = providers.Google
OpenStreetMap = providers.OpenStreetMap