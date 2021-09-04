from src.debug_tools import p_e, p_i, p_line
from src.feature_matching import feature_matching
from src.edge_detection import edge_detection
from src.data_getters.mountains import get_mountain_data
from src.dem import get_date_time, render_dem
from tkinter.filedialog import askopenfile
import tkinter as tk


def get_input():
    p_i("Select one of these modes to continue:")
    information_text = [
        "1: create 3d depth pov-ray render from DEM",
        "2: render-to-coordinates",
        "3: edge detection in given image",
        "4: feature matching given two images",
        "0: exit program"
    ]
    p_line(information_text)

    while True:
        try:
            mode = int(input("[INPUT] Select mode: "))
        except ValueError:
            p_e('No valid mode given.')
            continue
        else:
            if mode == 0:
                exit()
            if mode < 1 or mode > len(information_text):
                p_e('No valid mode given.')
                continue
            return mode


def file_chooser(title):
    root = tk.Tk()
    root.withdraw()
    filename = askopenfile(title=title,
                           mode='r',
                           filetypes=[('PNGs', '*.png'),
                                      ('JPEGs', '*.jpeg'), ('JPGs', '*.jpg')])
    return filename.name


if __name__ == '__main__':
    mode = get_input()

    # save renders to export-folder
    persistent = True

    date = get_date_time()
    folder = '/tmp/'
    if persistent:
        folder = 'exports/'

    if mode == 1 or mode == 2:
        file, camera_lat, camera_lon, look_at_lat, look_at_lon = \
            get_mountain_data('data/dem-data.json')
        camera_lat, camera_lon = 60.340148, 5.47665
        look_at_lat, look_at_lon = 60.373084070631464, 5.580410727548175
        coordinates = [camera_lat, camera_lon, look_at_lat, look_at_lon]
        render_dem(file, coordinates, mode, folder, date)

    elif mode == 3:
        image = file_chooser('Select an image to detect edges on')
        edge_detection(image, folder, date)
    elif mode == 4:
        image1 = file_chooser('Select first image')

        feature_matching(image1)
