import sys

from src.photo_filtering import photo_filtering
from src.pov_generator import panorama_creator

dem_mode = False

if __name__ == '__main__':
    if dem_mode:
        blåmanen = 60.4014, 5.3633
        damsgårdsfjellet = 60.3774, 5.2914
        fløyen = 60.3944, 5.3432
        gulfjellet = 60.3731, 5.5804
        løvstakken = 60.3609, 5.3191
        lyderhorn = 60.3739, 5.2419
        rundemanen = 60.4112, 5.3613
        sandviksfjellet = 60.4094, 5.3402
        strandafjellet = 60.37214161757205, 5.3226537916231305
        ulriken = 60.4014, 5.3633

        camera_lat, camera_lon = strandafjellet
        look_at_lat, look_at_lon = ulriken

        try:
            panorama_creator(sys.argv[1], camera_lat, camera_lon, look_at_lat, look_at_lon)
        except IndexError:
            print('Must provide .png, .dem or .tif file as argument')
    else:
        try:
            photo_filtering('assets/panorama3.jpg')
        except IndexError:
            print('Must provide .png or .jpeg file as argument')
