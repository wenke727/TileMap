import os
import math
import numpy as np
from PIL import Image
from scipy import ndimage
import matplotlib.pyplot as plt



def clip_background( img, bb, clip_bb, show = False ):
    """
    clip the tile accroding to the bbox
    @param
        bb: left, upper, right, lower;
        clip_bb: left, upper, right, lower
    @return: the clip image
    """
    x_range, y_range = img.size
    dx, dy = x_range / ( bb[2]-bb[0] ), y_range / ( bb[3]-bb[1] )
    
    [x0, y0, x1, y1] = clip_bb
    x0_pix = int((x0 - bb[0]) * dx)
    y0_pix = int((y0 - bb[1]) * dy)
    x1_pix = int((x1 - bb[0]) * dx)
    y1_pix = int((y1 - bb[1]) * dy)

    cropped = img.crop((x0_pix,y0_pix,x1_pix,y1_pix))  # (left, upper, right, lower)
    # cropped.save("pil_cut_thor.jpg")
    BB = [ clip_bb[0],clip_bb[2], clip_bb[3],clip_bb[1] ]
    if show:
        fig, ax = plt.subplots(1,1)
        ax.imshow( cropped, zorder=0, extent=clip_bb )
    return cropped, BB


def tile_gcj02_to_wgs84(tile_x, tile_y, zoom, origin_path ='/home/pcl/Data/tile/shenzhen/s/', des_path='/home/pcl/Data/tile/shenzhen/wgs'):
    """
    transfer the tile coordination systen from gcj02 to wgs84
    @para: tile_x, tile_y, zoom
    """
    bbox_wgs = [*tileXYToLnglat( tile_x, tile_y, zoom ), *tileXYToLnglat( tile_x+1, tile_y+1, zoom )]
    bbox_gcj = [*wgs84_to_gcj02( bbox_wgs[0], bbox_wgs[1] ), *wgs84_to_gcj02( bbox_wgs[2], bbox_wgs[3] )]

    min_x, min_y = lnglatToTileXY(*bbox_gcj[:2], zoom)
    max_x, max_y = lnglatToTileXY(*bbox_gcj[2:], zoom)
    bbox_img     = [*tileXYToLnglat(min_x, min_y, zoom), *tileXYToLnglat(max_x+1, max_y+1, zoom)]

    IMAGE_SIZE = 256
    IMAGE_COLUMN = max_x - min_x + 1
    IMAGE_ROW    = max_y - min_y + 1
    to_image = Image.new('RGB', (IMAGE_COLUMN * IMAGE_SIZE, IMAGE_ROW * IMAGE_SIZE))
    
    for x in range( min_x, max_x + 1):
        for y in range( min_y, max_y+1 ):
            path = os.path.join( origin_path, f'{zoom}/{x}/{y}.jpg')
            try:
                from_image = Image.open( path ).resize( (IMAGE_SIZE, IMAGE_SIZE), Image.ANTIALIAS)
                to_image.paste( from_image, ((x - min_x ) * IMAGE_SIZE, (y - min_y) * IMAGE_SIZE) )
            except:
                print(f"数据缺失: {path}")
                pass

    img, _ = clip_background(to_image, bbox_img, bbox_gcj)

    if des_path:
        file_dir = os.path.join( des_path, f'{zoom}/{tile_x}/' )
        if not os.path.isdir(file_dir):
            os.makedirs(file_dir)

        file_path = os.path.join( file_dir, f'{tile_y}.jpg' )
        # print(file_path)
        img.save(file_path)

    return img


def plain_PNG(file, image_size = 256 ):
    dataset = np.ndarray(shape=(image_size, image_size, 3), dtype=np.int8)
    try:
        image_data = ndimage.imread(file, mode='RGB').astype(int)
        dataset = image_data
        plain = False if 50135039-np.sum(dataset)>=0 else True     # 256*256*255*3 = 50135040
        return plain
    except:
        print('open images failed')


def tileXY_To_lnglat(tileX, tileY,ZOOM, in_sys = 'wgs', out_sys = 'wgs'):
    # 就算是Google地图，坐标也是GCJ02
    lng = tileX/pow(2,ZOOM)*360-180
    lat = math.atan( math.sinh( math.pi - 2*math.pi*( (tileY)/pow(2,ZOOM) ) ) )* 180/math.pi
    if in_sys == 'gcj' and out_sys == 'wgs':
        lng,lat = gcj02_to_wgs84(lng,lat)
    return "%.7f, %.7f"%(lng,lat)
    # return lng,lat

def tileXYToLnglat(x, y, zoom):
    lng = x/math.pow(2,zoom)*360-180
    lat = math.atan(math.sinh(math.pi-2*math.pi*y/math.pow(2,zoom))) * 180 /math.pi
    return round(lng, 6), round(lat, 6)


def lnglatToTileXY(lng,lat,zoom):
    tileX = math.floor((lng+180)/360 * pow(2,zoom))
    tileY = math.floor( (0.5 -( math.log( math.tan( lat * math.pi / 180) + ( 1/math.cos( lat*math.pi /180)) , math.e) /2/math.pi) )* pow(2,zoom))
    return tileX, tileY

