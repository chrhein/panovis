import sys, os
import subprocess
import rasterio
import rasterio.features
import rasterio.warp
from datetime import datetime
from src.location_handler import convertCoordinates, getLocation
from src.edge_detection import edge_detection


def panorama_creator(indem, lat, lon, llat, llon):
    demfile = 'exports/tmp_geotiff.png'
    date = 1
    color_mode = False
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
    

    crs = int(ds_raster.crs.to_authority()[1])
    latlon = convertCoordinates(ds_raster, crs, lat, lon)
    llatllon = convertCoordinates(ds_raster, crs, llat, llon)

    outfilename = 'exports/rendered_dem_%s.png' % date
    outwidth = 2400
    outheight = 800

    loc_view = getLocation(latlon[0], latlon[1], latlon[2], llatllon[0], llatllon[1], llatllon[2])
    location, view = loc_view[0], loc_view[1]
    location_x, location_y, location_height = location[0], location[1], location[2]
    view_x, view_y, view_height = view[0], view[1], view[2]
    povfilename = '/tmp/povfile.pov'
    
    with open(povfilename, 'w') as pf:
        pov = color_pov(location_x, location_height, location_y,
        view_x, view_height, view_y,
        demfile) if color_mode else pov_script(location_x, location_height, location_y,
        view_x, view_height, view_y,
        demfile)
        pf.write(pov)

    print("Generating", outfilename)
    subprocess.call(['povray', '+A', '+W%d' % outwidth, '+H%d' % outheight,
                    '+A0.3 Output_File_Type=N Bits_Per_Color=16 +Q8', 
                    '+I' + povfilename, '+O' + outfilename])

    print("Wrote", povfilename)

    try:
        edge_detection(outfilename)
    except FileNotFoundError:
        print("There is probably an error in the .pov file")
        exit()
    clear([outfilename])
    print("Finished creating panorama for", indem)
    sys.exit(0)


def pov_script(location_x, location_height, location_y,
        view_x, view_height, view_y,
        demfile):
    povfiletext = '''
    #include "colors.inc"
    #include "math.inc"

    global_settings {
        assumed_gamma 1
    }

    #declare CAMERALOOKAT = <%f, %f, %f>;
    #declare CAMERAPOS = <%f, %f, %f>;
    #declare FILENAME = "%s";

    #declare CAMERAFRONT  = vnormalize(CAMERALOOKAT - CAMERAPOS);
    #declare CAMERAFRONTX = CAMERAFRONT.x;
    #declare CAMERAFRONTY = CAMERAFRONT.y;
    #declare CAMERAFRONTZ = CAMERAFRONT.z;
    #declare DEPTHMIN = -0.1;
    #declare DEPTHMAX = 0.2;

    camera {
        cylinder 1
        angle 150
        location CAMERALOOKAT
        look_at  CAMERAPOS
    }

    #declare clipped_scaled_gradient =
        function(x, y, z, gradx, grady, gradz, gradmin, gradmax) {
            clip(
            ((x * gradx + y * grady + z * gradz) - gradmin) / (gradmax - gradmin),
            0,1)
        }
    #declare thetexture = texture {
        pigment {
            function {
            clipped_scaled_gradient(
                x, y, z, CAMERAFRONTX, CAMERAFRONTY, CAMERAFRONTZ, DEPTHMIN, DEPTHMAX)
            }
            color_map {
            [0 color rgb <0,0,0>]
            [1 color rgb <1,1,1>]

            }
            translate CAMERAPOS
        }
        finish { ambient 1 diffuse 0 specular 0 }
        }
    
    light_source { CAMERALOOKAT color White }
    
    union {
        height_field { 
            png FILENAME
        }
        texture { thetexture }
    }
    ''' % (location_x, location_height, location_y,
        view_x, view_height, view_y,
        demfile)
    return povfiletext


def color_pov(location_x, location_height, location_y,
        view_x, view_height, view_y,
        demfile):
    povfiletext = '''
    #include "colors.inc"
    #include "math.inc"

    #declare CAMERALOOKAT = <%f, %f, %f>;
    #declare CAMERAPOS = <%f, %f, %f>;
    #declare FILENAME = "%s";

    camera {
        cylinder 1
        angle 150
        location CAMERALOOKAT
        look_at  CAMERAPOS
    }
    light_source { CAMERALOOKAT color White }
    height_field {
        png FILENAME
        pigment {
            gradient y
            color_map {
                [0.0 color SlateBlue]
                [0.000000001 color BakersChoc]
                [0.02 color White]
                [1 color SlateBlue]
            }
        }
        finish { ambient 0.2 diffuse 1 specular 0.1 }
        scale <1, 1, 1>
    }
    sky_sphere {
    pigment {
      gradient y
      color_map {
        [0.4 color rgb<1 1 1>]
        [0.8 color rgb<0.1,0.25,0.75>]
        [1 color rgb<0.1,0.25,0.75>]
      }
      scale 2
      translate -1
    }
  }
    
    ''' % (location_x, location_height, location_y,
        view_x, view_height, view_y,
        demfile)
    return povfiletext


def clear(clear_list):
    for item in clear_list:
        os.remove(item)
    subprocess.call(['rm','-r', 'src/__pycache__'])
