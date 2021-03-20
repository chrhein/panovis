from osgeo import ogr, osr


def getLocation(lat, lon, hgt):
    location_x = lat
    location_y = lon
    location_height = hgt
    view_x = 0.25 # TODO: user selects lookat
    view_y = 0.4
    view_height = 0.0
    return [[location_x, location_y, location_height], [view_x, view_y, view_height]]


def convertCoordinates(raster, from_espg, to_espg, lat, lon):
    b = raster.bounds
    min_x, min_y, max_x, max_y = b.left, b.bottom, b.right, b.top

    in_sr = osr.SpatialReference()
    in_sr.ImportFromEPSG(from_espg)       # WGS84/Geographic
    out_sr = osr.SpatialReference()
    out_sr.ImportFromEPSG(to_espg)     # WGS 84 / UTM zone 33N

    coordinate_pair = ogr.Geometry(ogr.wkbPoint)
    coordinate_pair.AddPoint(lat,lon)
    coordinate_pair.AssignSpatialReference(in_sr)    # tell the point what coordinates it's in
    coordinate_pair.TransformTo(out_sr)              # project it to the out spatial reference

    polar_lat = coordinate_pair.GetX()
    polar_lon = coordinate_pair.GetY()
    lat_scaled = (polar_lat-min_x)/(max_x-min_x)
    lon_scaled = (polar_lon-min_y)/(max_y-min_y)
    return [lat_scaled, lon_scaled]