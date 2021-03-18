from osgeo import gdal
from mayavi import mlab
from mpl_toolkits.mplot3d import axes3d

def visualizeInMayavi(indem, quality):
    ds = gdal.Open(indem)
    
    data = ds.ReadAsArray()
    ans = []
    for i in range(0, len(data), quality):
        arr = []
        for j in range(0, len(data[i]), quality):
            arr.append(data[i][j])
        ans.append(arr)

    f = quality*100
    mlab.figure(size=(640, 800), bgcolor=(0.16, 0.28, 0.46))
    mlab.contour_surf(ans, warp_scale=quality/f)
    mlab.surf(ans, warp_scale=quality/f) 
    mlab.axes(xlabel='X', ylabel='Y', zlabel='Z')
    mlab.show()