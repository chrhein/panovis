import sys, os
import subprocess
from datetime import datetime
from PIL import Image


def panorama_creator(indem):
    demfile = 'tmp_geotiff.png'
    subprocess.call(['gdal_translate', '-ot', 'UInt16', 
                    '-of', 'PNG', '%s' % indem, '%s' % demfile])

    date = "%02d%02d_%02d%02d%02d" % (datetime.now().date().month, 
            datetime.now().date().day, 
            datetime.now().time().hour, 
            datetime.now().time().minute, 
            datetime.now().time().second)
    
    outfilename = 'exports/rendered_dem_%s.png' % date
    outwidth = 2400
    outheight = 800

    povfilename = '/tmp/povfile.pov'
    povfiletext = '''
    camera {
        // "perspective" is the default camera, which warps images
        // so they're hard to stitch together.
        // "cylinder 1" uses a vertical cylinder.
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
            gradient x
            color_map {
                [ 0.4 color <1 1 1> ]
                [ 0.6 color <0 0 1> ]
                [ 0.8 color <0 1 0> ]
                [ 1 color <1 0 0> ]
            }
        }

        scale <1, 1, 1>
    }

    ''' % (0.5, 0.015620, 0.5,
        1, 0.010620, 0.5,
        0.5, 0.015620, 0.5,
        demfile)

    with open(povfilename, 'w') as pf:
        pf.write(povfiletext)

    print("Generating", outfilename)
    subprocess.call(['povray', '+A', '+W%d' % outwidth, '+H%d' % outheight,
                    '+I' + povfilename, '+O' + outfilename])

    print("Wrote", povfilename)

    im = Image.open(r"%s" % outfilename)
    im.show()

    clear([demfile, "%s.aux.xml" % demfile, outfilename])

    sys.exit(0)

def clear(clear_list):
    for item in clear_list:
        os.remove(item)

if __name__ == '__main__':
    try:
        panorama_creator(sys.argv[1])
    except IndexError:
        print('Must provide DEM file as argument')
