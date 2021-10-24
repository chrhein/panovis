import rasterio
from location_handler import convert_coordinates
from debug_tools import p_e


def get_raster_data(dem_file, coordinates, height_field_scale_factor):
    # load raster data
    ds_raster = rasterio.open(dem_file)
    # get resolution (points per square meter)
    resolution = ds_raster.transform[0]
    # get coordinate reference system
    crs = int(ds_raster.crs.to_authority()[1])
    # convert lat_lon to grid coordinates in the interval [0, 1]
    camera_lat_lon = convert_coordinates(ds_raster, crs,
                                         coordinates[0], coordinates[1],
                                         True, height_field_scale_factor)
    if not camera_lat_lon:
        p_e('Camera location is out of bounds')
        return
    look_at_lat_lon = convert_coordinates(ds_raster, crs,
                                          coordinates[2], coordinates[3],
                                          False, height_field_scale_factor)
    if not look_at_lat_lon:
        p_e('Viewpoint location is out of bounds')
        return
    raster_left, raster_bottom, raster_right, raster_top = ds_raster.bounds
    # get total sample points across x and y axis
    total_distance_e_w = raster_right - raster_left
    total_distance_n_s = raster_top - raster_bottom
    distances = [total_distance_n_s, total_distance_e_w]
    try:
        max_height = camera_lat_lon[-1]
    except TypeError:
        pass

    normalized_coordinates = [*camera_lat_lon[:3], *look_at_lat_lon[:3]]
    raster_metadata = [ds_raster, distances, resolution, max_height]
    return [normalized_coordinates, raster_metadata]
