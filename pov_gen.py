from loc import getLocation
import sys, os, math
import subprocess
from datetime import datetime
from PIL import Image
import rasterio
import rasterio
import rasterio.features
import rasterio.warp
from osgeo import ogr, osr
from pov import pov_script

def panorama_creator(indem, lat, lon):
    demfile = 'tmp_geotiff.png'
    date = 1
    if indem.lower().endswith('.dem') or indem.lower().endswith('.tif'):
        subprocess.call(['gdal_translate', '-ot', 'UInt16', 
                    '-of', 'PNG', '%s' % indem, '%s' % demfile])
    elif indem.lower().endswith('.png'):
        demfile = indem
        dt = datetime.now()
        date = "%02d%02d_%02d%02d%02d" % (dt.date().month, dt.date().day, 
            dt.time().hour, dt.time().minute, dt.time().second)
    else:
        print('please provide .dem, .tif or .png')
        exit()
    
    ds_raster = rasterio.open(demfile)
    b = ds_raster.bounds
    min_x, min_y, max_x, max_y = b.left, b.bottom, b.right, b.top

    in_sr = osr.SpatialReference()
    in_sr.ImportFromEPSG(4326)       # WGS84/Geographic
    out_sr = osr.SpatialReference()
    out_sr.ImportFromEPSG(32633)     # WGS 84 / UTM zone 33N

    coordinate_pair = ogr.Geometry(ogr.wkbPoint)
    coordinate_pair.AddPoint(lat,lon)
    coordinate_pair.AssignSpatialReference(in_sr)    # tell the point what coordinates it's in
    coordinate_pair.TransformTo(out_sr)              # project it to the out spatial reference

    polar_lat = coordinate_pair.GetX()
    polar_lon = coordinate_pair.GetY()
    lat_scaled = (polar_lat-min_x)/(max_x-min_x)
    lon_scaled = (polar_lon-min_y)/(max_y-min_y)

    # settings for povfile
    outfilename = 'assets/rendered_dem_%s.png' % date
    outwidth = 2400
    outheight = 800

    loc_view = getLocation(lat_scaled, lon_scaled, 0.005681)
    location, view = loc_view[0], loc_view[1]
    location_x, location_y, location_height = location[0], location[1], location[2]
    view_x, view_y, view_height = view[0], view[1], view[2]
    povfilename = '/tmp/povfile.pov'
    
    with open(povfilename, 'w') as pf:
        pf.write(pov_script(location_x, location_height, location_y,
        view_x, view_height, view_y,
        demfile))

    print("Generating", outfilename)
    subprocess.call(['povray', '+A', '+W%d' % outwidth, '+H%d' % outheight,
                    'Antialias=off Output_File_Type=N Bits_Per_Color=16', 
                    '+I' + povfilename, '+O' + outfilename])

    print("Wrote", povfilename)

    try:
        im = Image.open(r"%s" % outfilename)
    except FileNotFoundError:
        print("There is probably an error in the .pov file")
        exit()
    im.show()

    print("Finished creating panorama for", indem)
    sys.exit(0)

def clear(clear_list):
    for item in clear_list:
        os.remove(item)
