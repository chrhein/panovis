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

ds = gdal.Open('assets/subset_DEM3.dem')
data = ds.ReadAsArray()
data = data[:1000, 900:1900]
data[data <= 0] = data[data > 0].min()
'''
for i in range(len(data)):
    print(data[i])
    for j in range(len(data[i])):
        if data[i][j] < 0:
            data[i][j] = 0
'''

print(data)

mlab.figure(size=(800, 640), bgcolor=(0.5, 0.5, 0.5))

repres = ["surface", "wireframe", "points"]

mlab.surf(data, colormap='gist_earth', warp_scale=0.5, vmin=100, vmax=250, representation=repres[0], line_width=3.0) 

f = mlab.gcf()
camera = f.scene.camera
#  camera.yaw(45)

mlab.show()
