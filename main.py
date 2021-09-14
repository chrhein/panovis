from src.debug_tools import p_e, p_i, p_in, p_line
from src.feature_matching import feature_matching
from src.edge_detection import edge_detection
from src.data_getters.mountains import get_mountain_data
from src.dem import get_date_time, render_dem
from tkinter.filedialog import askopenfile
import tkinter as tk
import os


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
            mode = int(p_in("Select mode: "))
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


def edge_detection_type():
    p_i("Select one of these algorithms to continue:")
    information_text = [
        "1: Canny",
        "2: Holistically-Nested (HED)",
        "3: Horizon Highlighting",
        "0: exit program"
    ]
    p_line(information_text)

    while True:
        try:
            mode = int(p_in("Select algorithm: "))
        except ValueError:
            p_e('No valid algorithm given.')
            continue
        else:
            if mode == 0:
                exit()
            if mode < 1 or mode > len(information_text):
                p_e('No valid algorithm given.')
                continue
            return mode


def file_chooser(title):
    # Set environment variable
    os.environ['TK_SILENCE_DEPRECATION'] = "1"
    root = tk.Tk()
    root.withdraw()
    p_i("Opening File Explorer")
    filename = askopenfile(title=title,
                           mode='r',
                           filetypes=[('PNGs', '*.png'),
                                      ('JPEGs', '*.jpeg'),
                                      ('JPGs', '*.jpg')])
    try:
        p_i("%s was selected" % filename.name.split('/')[-1])
        return filename.name
    except AttributeError:
        p_i("Exiting...")
        exit()


if __name__ == '__main__':
    mode = get_input()

    # save renders to export-folder
    persistent = True

    date = get_date_time()
    folder = '/tmp/'
    if persistent:
        folder = 'exports/'

    if mode == 1 or mode == 2:
        pano = file_chooser('Select an image to detect edges on')
        file, camera_lat, camera_lon, look_at_lat, look_at_lon = \
            get_mountain_data('data/dem-data.json', pano)
        coordinates = [camera_lat, camera_lon, look_at_lat, look_at_lon]
        render_dem(file, coordinates, mode, folder, date)

    elif mode == 3:
        kind = edge_detection_type()
        image = file_chooser('Select an image to detect edges on')
        if kind == 1:
            edge_detection(image, "Canny")
        elif kind == 2:
            edge_detection(image, "HED")
        elif kind == 3:
            edge_detection(image, "Horizon")
    elif mode == 4:
        image1 = file_chooser('Select render')
        image2 = file_chooser('Select image')

        feature_matching(image1, image2)
