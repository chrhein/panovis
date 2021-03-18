from loc import getLocation
import sys, os, math
import subprocess
from datetime import datetime
from PIL import Image
import rasterio
import rasterio
import rasterio.features
import rasterio.warp
from osgeo import gdal
from mayavi import mlab
import numpy as np
from mayavi_vis import visualizeInMayavi
from pov import pov_script

def panorama_creator(indem):
    #  visualizeInMayavi(indem, 10)
    demfile = 'tmp_geotiff.png'
    clear_after_run = False
    date = 1
    if indem.lower().endswith('.dem') or indem.lower().endswith('.tif'):
        #  tmptiff = 'tmp_tiff.tif'
        #  subprocess.call(['gdalwarp', '-t_srs', "+proj=longlat +datum=WGS84 +no_defs" , indem, tmptiff])
        subprocess.call(['gdal_translate', '-ot', 'UInt16', 
                    '-of', 'PNG', '%s' % indem, '%s' % demfile])
        clear_after_run = True
    elif indem.lower().endswith('.png'):
        demfile = indem
        dt = datetime.now()
        date = "%02d%02d_%02d%02d%02d" % (dt.date().month, dt.date().day, 
            dt.time().hour, dt.time().minute, dt.time().second)
    else:
        print('please provide .dem, .tif or .png')
        exit()
    
    ds_raster = rasterio.open(demfile)
    bounds = ds_raster.bounds
    left= bounds.left
    bottom = bounds.bottom
    right = bounds.right
    top = bounds.top
    print(left, bottom, right, top)
    print(ds_raster.crs)

    # settings for povfile
    outfilename = 'assets/rendered_dem_%s.png' % date
    outwidth = 2400
    outheight = 800

    location_name = 'Løvstakken'
    loc_view = getLocation(location_name)
    location = loc_view[0]
    view = loc_view[1]
    location_x = location[0]
    location_y = location[1]
    location_height = location[2]
    view_x = view[0]
    view_y = view[1]
    view_height = view[2]

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
        clear(["%s.aux.xml" % demfile])
        print("There is probably an error in the .pov file")
        exit()
    im.show()

    if clear_after_run:
        clear(["%s.aux.xml" % demfile, outfilename, 
        #  tmptiff
        ])
    else:
         clear([
             # "%s.aux.xml" % demfile, 
             outfilename
             ])

    print("Finished creating panorama for", indem)
    sys.exit(0)

def clear(clear_list):
    for item in clear_list:
        os.remove(item)
