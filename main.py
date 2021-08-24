import sys
import cv2
from src.data_getters.mountains import get_mountain_data

from src.debug_tools import p_a, p_i
from src.feature_matching import feature_matching
from src.location_handler import look_at_location
from src.photo_filtering import photo_filtering, resizer
from src.dem import render_dem


if __name__ == '__main__':
    render_dem(*get_mountain_data('data/dem-data.json'))

    exit()
    try:
        mode = int(sys.argv[1])
        index = 2
    except ValueError or IndexError:
        mode = 1
        p_a('No mode selected, using mode 1 as default.')
        index = 1
    if mode == 0:
        p_i("Running the program in DEM mode")
        blåmanen = 60.4014, 5.3633
         
        fløyen = 60.3944, 5.3432
        gulfjellet = 60.3731, 5.5804
        løvstakken = 60.3609, 5.3191
        lyderhorn = 60.3739, 5.2419
        rundemanen = 60.4112, 5.3613
        sandviksfjellet = 60.4094, 5.3402
        strandafjellet = 60.37214161757205, 5.3226537916231305
        ulriken = 60.3772347916171, 5.381081749383611

        lb = 60.062891, 5.092038
        ub = 61.077628, 6.647520

        camera_lat, camera_lon = strandafjellet
        look_at_lat, look_at_lon = ulriken

        """ 
        try:
            data = gpsphoto.getGPSData(sys.argv[index + 1])
            p_i("Image Lat/Lon: %f, %f" % (data['Latitude'], data['Longitude']))
            p_i("Image Lat/Lon: %f, %f" % (data['Latitude'], data['Longitude']))
            print(data)
            camera_lat, camera_lon = data['Latitude'], data['Longitude']
            print(camera_lat, camera_lon)
            try:
                heading = int(sys.argv[index + 2])
            except ValueError or IndexError:
                heading = 0
            look_at_lat, look_at_lon = look_at_location(camera_lat, camera_lon, 5, heading)
        except IndexError:
            pass 
        """

        try:
            file_handler(sys.argv[index], camera_lat, camera_lon, look_at_lat, look_at_lon)
        except IndexError:
            print('Must provide .png, .dem or .tif file as argument')
    elif mode == 1:
        p_i("Running the program in Photo Filtering mode")
        try:
            photo_filtering(sys.argv[index])
        except IndexError:
            print('Must provide .png or .jpeg file as argument')
    elif mode == 2:
        p_i("Running the program in Feature Matching mode")
        try:
            im1, im2 = cv2.imread(sys.argv[index]), cv2.imread(sys.argv[index + 1])
            feature_matching(resizer(im1), resizer(im2))
        except IndexError:
            print('Must provide two .pngs or .jpegs as arguments')
