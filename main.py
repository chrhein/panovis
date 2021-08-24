from src.data_getters.mountains import get_mountain_data
from src.dem import render_dem


if __name__ == '__main__':
    file, camera_lat, camera_lon, look_at_lat, look_at_lon =  \
        get_mountain_data('data/dem-data.json')
    coordinates = [camera_lat, camera_lon, look_at_lat, look_at_lon]

    # modes:
    # 1: create 3d depth pov-ray render from DEM
    # 2: render-to-coordinates
    mode = 1

    # save renders to export-folder
    persistent = False

    render_dem(file, coordinates, mode, persistent)
