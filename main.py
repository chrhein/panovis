from src.debug_tools import p_e, p_i, p_in, p_line
from src.feature_matching import feature_matching
from src.edge_detection import edge_detection
from src.dem import render_dem
from tkinter.filedialog import askopenfile
import tkinter as tk
import os


def get_input():
    p_i("Select one of these modes to continue:")
    information_text = [
        "1: run through modes 2-5",
        "1: create 3d depth pov-ray render from DEM",
        "2: render-to-coordinates",
        "3: create a 3d height pov-ray render from DEM",
        "4: edge detection in given image",
        "5: feature matching given two images",
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

    if 0 < mode < 5:
        pano = file_chooser('Select an image to detect edges on')
        render_dem(pano, mode)
    elif mode == 5:
        kind = edge_detection_type()
        image = file_chooser('Select an image to detect edges on')
        if kind == 1:
            edge_detection(image, "Canny")
        elif kind == 2:
            edge_detection(image, "HED")
        elif kind == 3:
            edge_detection(image, "Horizon")
    elif mode == 6:
        image1 = file_chooser('Select render')
        image2 = file_chooser('Select image')

        feature_matching(image1, image2)
