import sys, os
import subprocess
from datetime import datetime
from PIL import Image


def panorama_creator(indem):
    demfile = 'tmp_geotiff.png'
    clear_after_run = False
    date = 1
    if indem.lower().endswith('.dem') or indem.lower().endswith('.tif'):
        subprocess.call(['gdal_translate', '-ot', 'UInt16', 
                    '-of', 'PNG', '%s' % indem, '%s' % demfile])
        clear_after_run = True
    elif indem.lower().endswith('.png'):
        demfile = indem
        date = "%02d%02d_%02d%02d%02d" % (datetime.now().date().month, 
            datetime.now().date().day, 
            datetime.now().time().hour, 
            datetime.now().time().minute, 
            datetime.now().time().second)
    else:
        exit()
    
    # settings for povfile
    outfilename = 'assets/rendered_dem_%s.png' % date
    outwidth = 2400
    outheight = 800
    location_x = 0.5
    location_y = 0.5
    location_height = 0.012620
    view_x = 1.0
    view_y = 0.5
    view_height = 0.010620
    mapcolor = '<0.5, 0.5, 0.5>'

    povfilename = '/tmp/povfile.pov'
    povfiletext = '''
    camera {
        cylinder 1

        // povray coordinates compared to the height field image are
        // < rightward, upward, forward >
        location <%f, %f, %f>
        look_at  <%f, %f, %f>

        // to get a panorama image
        angle 160
    }

    light_source { <%f, %f, %f> color <1,1,1> }

    height_field {
        png "%s"
        
        // smooth
        pigment {
            color %s
        }

        scale <1, 1, 1>
    }

    ''' % (location_x, location_height, location_y,
        view_x, view_height, view_y,
        location_x, location_height, location_y,
        demfile, mapcolor)

    with open(povfilename, 'w') as pf:
        pf.write(povfiletext)

    print("Generating", outfilename)
    subprocess.call(['povray', '+A', '+W%d' % outwidth, '+H%d' % outheight,
                    '+I' + povfilename, '+O' + outfilename])

    print("Wrote", povfilename)

    im = Image.open(r"%s" % outfilename)
    im.show()

    if clear_after_run:
        clear([demfile, "%s.aux.xml" % demfile, outfilename])
    else:
        clear(["%s.aux.xml" % demfile])

    sys.exit(0)

def clear(clear_list):
    for item in clear_list:
        os.remove(item)

if __name__ == '__main__':
    try:
        panorama_creator(sys.argv[1])
    except IndexError:
        print('Must provide DEM file as argument')
