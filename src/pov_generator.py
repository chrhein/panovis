import os
import subprocess
import sys
from datetime import datetime

import numpy as np
import rasterio
import rasterio.features
import rasterio.warp
from osgeo import gdal

from src.edge_detection import edge_detection
from src.location_handler import convert_coordinates, get_location

color_mode = True


def panorama_creator(in_dem, lat, lon, view_lat, view_lon):
    dem_file = 'exports/tmp_geotiff.png'
    date = 1

    debugger(in_dem, lat, lon, view_lat, view_lon)

    if in_dem.lower().endswith('.dem') or in_dem.lower().endswith('.tif'):
        subprocess.call(['gdal_translate', '-ot', 'UInt16',
                         '-of', 'PNG', '%s' % in_dem, '%s' % dem_file])
    elif in_dem.lower().endswith('.png'):
        dem_file = in_dem
        dt = datetime.now()
        date = "%02d%02d_%02d%02d%02d" % (dt.date().month, dt.date().day,
                                          dt.time().hour, dt.time().minute, dt.time().second)
    else:
        print('please provide .dem, .tif or .png')
        exit()

    ds_raster = rasterio.open(dem_file)

    crs = int(ds_raster.crs.to_authority()[1])
    lat_lon = convert_coordinates(ds_raster, crs, lat, lon)
    view_lat_lon = convert_coordinates(ds_raster, crs, view_lat, view_lon)

    out_filename = 'exports/rendered_dem_%s.png' % date
    out_width = 2400
    out_height = 800

    loc_view = get_location(lat_lon[0], lat_lon[1], lat_lon[2], view_lat_lon[0], view_lat_lon[1], view_lat_lon[2])
    location, view = loc_view[0], loc_view[1]
    location_x, location_y, location_height = location[0], location[1], location[2]
    view_x, view_y, view_height = view[0], view[1], view[2]
    pov_filename = '/tmp/pov_file.pov'

    with open(pov_filename, 'w') as pf:
        pov = color_pov(location_x, location_height, location_y,
                        view_x, view_height, view_y,
                        dem_file) if color_mode else pov_script(location_x, location_height, location_y,
                                                                view_x, view_height, view_y,
                                                                dem_file)
        pf.write(pov)

    print("Generating", out_filename)
    subprocess.call(['povray', '+W%d' % out_width, '+H%d' % out_height,
                     'Output_File_Type=N Bits_Per_Color=8 +Q4 +UR +A',
                     '+I' + pov_filename, '+O' + out_filename])

    print("Wrote", pov_filename)

    try:
        edge_detection(out_filename)
    except FileNotFoundError:
        print("There is probably an error in the .pov file")
        exit()
    clear([out_filename])
    print("Finished creating panorama for", in_dem)
    sys.exit(0)


def pov_script(location_x, location_height, location_y,
               view_x, view_height, view_y,
               dem_file):
    pov_text = '''
    #version 3.7;
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
    
    height_field { 
        png FILENAME
        texture { thetexture }
    }
    ''' % (location_x, location_height, location_y,
           view_x, view_height, view_y,
           dem_file)
    return pov_text


def color_pov(location_x, location_height, location_y,
              view_x, view_height, view_y,
              dem_file):
    pov_text = '''
    #version 3.7;
    #include "colors.inc"
    #include "math.inc"
    
    global_settings {
        assumed_gamma 1
    }

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
                [0.000000001 color BakersChoc]
                [0.02 color White]
                [1 color SlateBlue]
            }
        }
        finish { ambient 0.2 diffuse 1 specular 0.1 }
        scale <1, 1, 1>
    }
    plane {
          y, 0
          texture
          {
            pigment { color rgb < 0.3, 0.3, 0.7 > }
            normal { bumps 0.2 }
            finish { phong 1 reflection 1.0 ambient 0.2 diffuse 0.2 specular 1.0 }
          }
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
           dem_file)
    return pov_text


def debugger(in_dem, lat, lon, view_lat, view_lon):
    demdata = gdal.Open(in_dem)
    demarray = np.array(demdata.GetRasterBand(1).ReadAsArray())
    # print('Map coordinate for max height:', np.where(demarray == demarray.max()))
    # print('Map coordinate for min height:', np.where(demarray == demarray.min()))
    print('\nInput file:', in_dem)
    print('Camera position:', lat, lon)
    print('Look at position:', view_lat, view_lon)
    print('Color mode:', color_mode, '\n')


def clear(clear_list):
    for item in clear_list:
        os.remove(item)
    subprocess.call(['rm', '-r', 'src/__pycache__'])
