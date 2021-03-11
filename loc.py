def getLocation(location_name):
    if location_name.lower() == 'løvstakken':
        location_x = 0.175
        location_y = 0.31
        location_height = 0.007020
        view_x = 0.25
        view_y = 0.4
        view_height = 0.0
        return [[location_x, location_y, location_height], [view_x, view_y, view_height]]
    else:
        return [[0.5, 0.5, 0.05], [0.3, 0.3, 0.005]]
