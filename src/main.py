from debug_tools import p_e, p_i, p_in, p_line
from feature_matching import feature_matching
from edge_detection import edge_detection
from dem import render_dem
from tkinter.filedialog import askopenfile, askopenfilenames
from tools.file_handling import select_file
import tkinter as tk
import os


def get_input():
    p_i("Select one of these modes to continue:")
    information_text = [
        "1: autopilot",
        "2: create 3d depth pov-ray render from DEM",
        "3: create a 3d height pov-ray render from DEM",
        "4: render-to-coordinates",
        "5: show geolocations in image",
        "6: edge detection in given image",
        "7: feature matching given two images",
        "8: render with hike-paths visible",
        "0: exit program"
    ]
    p_line(information_text)

    while True:
        try:
            mode = p_in("Select mode: ")
            if mode == 'debug':
                return mode
            mode = int(mode)
        except ValueError:
            p_e('No valid mode given.')
            continue
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


def file_chooser(title, multiple=False):
    # Set environment variable
    os.environ['TK_SILENCE_DEPRECATION'] = "1"
    root = tk.Tk()
    root.withdraw()
    p_i("Opening File Explorer")
    if multiple:
        files = askopenfilenames(title=title,
                                 filetypes=[('PNGs', '*.png'),
                                            ('JPEGs', '*.jpeg'),
                                            ('JPGs', '*.jpg')])
    else:
        filename = askopenfile(title=title,
                               mode='r',
                               filetypes=[('PNGs', '*.png'),
                                          ('JPEGs', '*.jpeg'),
                                          ('JPGs', '*.jpg')])
    try:
        if multiple:
            p_i("%s was selected" % [i.split('/')[-1] for i in files])
            return files
        else:
            p_i("%s was selected" % filename.name.split('/')[-1])
            return filename.name
    except AttributeError:
        p_i("Exiting...")
        exit()


def main():
    mode = 'debug'
    multiselect = False
    if mode == 'debug':
        panos = file_chooser('Select an image to detect edges on', True)
        for pano in panos:
            render_dem(pano, mode)
        exit()
    if 0 < mode < 6 or mode >= 8:
        pano_folder = 'data/panoramas/'
        panos = file_chooser('Select one or more panoramas') \
            if multiselect else [select_file(pano_folder)]
        for pano in panos:
            render_dem(pano, mode)
    elif mode == 6:
        kind = edge_detection_type()
        image = file_chooser('Select an image to detect edges on')
        if kind == 1:
            edge_detection(image, "Canny")
        elif kind == 2:
            edge_detection(image, "HED")
        elif kind == 3:
            edge_detection(image, "Horizon")
    elif mode == 7:
        image1 = file_chooser('Select render')
        image2 = file_chooser('Select image')
        feature_matching(image1, image2)
