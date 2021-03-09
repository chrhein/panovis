from osgeo import gdal
from mayavi import mlab
import numpy as np
import affine


ds = gdal.Open('assets/67M1_sub.dem')
data = ds.GetRasterBand(1).ReadAsArray()[:-1]
print(data)
print(data.min(), data.max())

indices = np.where(data == data.max())
ymax, xmax = indices[0][0], indices[1][0]
print("The highest point is", data[ymax][xmax])
print("  at pixel location", xmax, ymax)

'''
affine_transform = affine.Affine.from_gdal(*data.GetGeoTransform())
lon, lat = affine_transform * (xmax, ymax)
'''

mlab.figure(size=(800, 640), bgcolor=(0.4, 0.4, 0.4))
repres = ["surface", "wireframe", "points"]
mlab.surf(data, 
        colormap='terrain', 
        warp_scale=0.04, 
        vmin=0, 
        representation=repres[0], 
        line_width=1.0) 
f = mlab.gcf()
camera = f.scene.camera
mlab.show()
