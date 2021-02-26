import matplotlib.pyplot as plt
from osgeo import gdal
from mayavi import mlab

'''

src = gdal.Open('assets/cropped10.tif')
dst = 'assets/mgddem.tif'
t = 'hillshade'
slope = gdal.DEMProcessing(dst, src, t, computeEdges = True)


rb = slope.GetRasterBand(1).ReadAsArray()
plt.figure()
plt.imshow(rb, cmap="gray")
plt.colorbar()
plt.show()

'''


from osgeo import gdal
from mayavi import mlab

ds = gdal.Open('assets/slope.dem')
data = ds.ReadAsArray()

mlab.figure(size=(640, 800), bgcolor=(0.16, 0.28, 0.46))

mlab.surf(data, warp_scale=0.2) 

f = mlab.gcf()
camera = f.scene.camera
camera.yaw(45)

mlab.show()

