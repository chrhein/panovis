from loc import getLocation
import sys, os, math
import subprocess
from datetime import datetime
from PIL import Image
import rasterio


def panorama_creator(indem):
    demfile = 'tmp_geotiff.png'
    clear_after_run = False
    date = 1
    if indem.lower().endswith('.dem') or indem.lower().endswith('.tif'):
        tmptiff = 'tmp_tiff.tif'
        subprocess.call(['gdalwarp', '-t_srs', "+proj=longlat +datum=WGS84 +no_defs" , indem, tmptiff])
        subprocess.call(['gdal_translate', '-ot', 'UInt16', 
                    '-of', 'PNG', '%s' % tmptiff, '%s' % demfile])
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

    
    # settings for povfile
    outfilename = 'assets/rendered_dem_%s.png' % date
    outwidth = 2400
    outheight = 800

    location_name = 'Løvstakken'
    #  location_x = (lat * math.pi) / 180
    #  location_y = abs(math.cos(lat) * math.sin(lon))
    loc_view = getLocation(location_name)
    location = loc_view[0]
    view = loc_view[1]
    location_x = location[0]
    location_y = location[1]
    location_height = location[2]
    view_x = view[0]
    view_y = view[1]
    view_height = view[2]
    mapcolor = 'BakersChoc'

    sky = True
    skycolor_ground = '<0.9 0.9 0.9>' if sky else '<0 0 0>'
    skycolor_mid = '<0.1,0.25,0.75>' if sky else '<0 0 0>'
    skycolor_top = '<0.1,0.25,0.75>' if sky else '<0 0 0>'

    povfilename = '/tmp/povfile.pov'
    povfiletext = '''
    #include "colors.inc"

    camera {
        cylinder 1
        // panoramic
        // povray coordinates compared to the height field image are
        // < rightward, upward, forward >
        location <%f, %f, %f>
        look_at  <%f, %f, %f>

        // to get a panorama image
        angle 160
    }

    light_source { <%f, %f, %f> color White }

    height_field {
        png "%s"
        
        // smooth
        pigment { color %s }
        /*
        pigment {
            gradient y
            color_map {
                [0.0 color SlateBlue]
                [0.0000001 color BakersChoc]
                [0.1 color White]
                [1 color SlateBlue]
            }
        }
        */
        scale <1, 1, 1>
    }

    // sky ------------------------------------
    sphere{<0,0,0>,1 hollow
    texture{
    pigment{gradient <0,1,0>
            color_map{
            [0.0 color rgb%s]
            [0.4 color rgb%s]
            [1.0 color rgb%s] }
            } // end pigment
    finish {ambient 1 diffuse 0}
    } // end of texture
    scale 10000
    } // end of sphere -----------------------

    ''' % (location_x, location_height, location_y,
        view_x, view_height, view_y,
        location_x, location_height, location_y,
        demfile, mapcolor, 
        skycolor_ground, skycolor_mid, skycolor_top)

    
    with open(povfilename, 'w') as pf:
        pf.write(povfiletext)
    

    print("Generating", outfilename)
    subprocess.call(['povray', '+A', '+W%d' % outwidth, '+H%d' % outheight,
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
        clear(["%s.aux.xml" % demfile, outfilename, tmptiff])
    # else:
         # clear(["%s.aux.xml" % demfile])

    print("Finished creating panorama for", indem)
    sys.exit(0)

def clear(clear_list):
    for item in clear_list:
        os.remove(item)
