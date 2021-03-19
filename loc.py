def getLocation(lat, lon, hgt):
    location_x = lat
    location_y = lon
    location_height = hgt
    view_x = 0.25
    view_y = 0.4
    view_height = 0.0
    return [[location_x, location_y, location_height], [view_x, view_y, view_height]]
