from osgeo import gdal
from mayavi import mlab

ds = gdal.Open('assets/67M1_sub.dem')
data = ds.GetRasterBand(1).ReadAsArray()[:-1]
print(data)

mlab.figure(size=(800, 640), bgcolor=(0.5, 0.5, 0.5))
repres = ["surface", "wireframe", "points"]
mlab.surf(data, 
        colormap='terrain', 
        warp_scale=0.04, 
        vmin=0, 
        representation=repres[2], 
        line_width=1.0) 
f = mlab.gcf()
camera = f.scene.camera
mlab.show()
