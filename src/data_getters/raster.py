import os
import subprocess
from datetime import datetime

from src.colors import *
from src.debug_tools import *
from src.edge_detection import *
from src.location_handler import *
from src.photo_filtering import *
from src.povs import *

def get_raster_data(dem_file, coordinates):
    ds_raster = rasterio.open(dem_file)
    tpx = ds_raster.transform
    tpx_x, tpx_y = tpx[0], -tpx[4]
    crs = int(ds_raster.crs.to_authority()[1])
    lat_lon = convert_coordinates(ds_raster, crs, coordinates[0], coordinates[1])
    view_lat_lon = convert_coordinates(ds_raster, crs, coordinates[2], coordinates[3])
    raster_left, raster_bottom, raster_right, raster_top = ds_raster.bounds
    p_line([raster_left, raster_right, raster_top, raster_bottom])
    bounds = crs_to_wgs84(ds_raster, raster_left, raster_bottom), \
             crs_to_wgs84(ds_raster, raster_right, raster_top)
    lb_lat = bounds[0][0][0]
    lb_lon = bounds[0][1][0]
    ub_lat = bounds[1][0][0]
    yb_lon = bounds[1][1][0]
    p_i("Lower left coordinates:  (%f, %f)" % (lb_lat, lb_lon))
    p_i("Upper right coordinates: (%f, %f)" % (ub_lat, yb_lon))

    total_distance_e_w = abs(raster_left) + abs(raster_right)
    total_distance_n_s = abs(raster_left) + abs(raster_right)
    loc_view = get_location(*lat_lon, *view_lat_lon)
    location, view = loc_view[0], loc_view[1]
    location_x, location_y, location_height = location[0], location[1], location[2]
    view_x, view_y, view_height = view[0], view[1], view[2]

    a_l = [location_x, location_height, location_y,
               view_x, view_height, view_y, dem_file]

    return [a_l, ds_raster, total_distance_n_s, total_distance_e_w, tpx_x, tpx_y]

    ds_raster, total_distance_n_s, total_distance_e_w, tpx_x, tpx_y,

    return [location_x, location_height, location_y,
               view_x, view_height, view_y, 
               tpx_x, tpx_y, 
               total_distance_n_s, total_distance_e_w, 
               ds_raster]