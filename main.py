import sys
from src.pov_generator import panorama_creator


if __name__ == '__main__':
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
    lookat_lat, lookat_lon = ulriken

    try:
        panorama_creator(sys.argv[1], camera_lat, camera_lon, lookat_lat, lookat_lon)
    except IndexError:
        print('Must provide .png, .dem or .tif file as argument')
