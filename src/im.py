from datetime import datetime
import cv2
import numpy as np
from tools.debug import custom_imshow, p_i, p_in
from image_manipulations import resizer
from tkinter.filedialog import askdirectory


def vertical_stack_imshow_divider(im1, im2, title="Preview", div_thickness=3):
    try:
        _, im1_w, _ = im1.shape
    except ValueError:
        im1 = cv2.cvtColor(im1, cv2.COLOR_GRAY2BGR)
        _, im1_w, _ = im1.shape
    try:
        _, im2_w, _ = im2.shape
    except ValueError:
        im2 = cv2.cvtColor(im2, cv2.COLOR_GRAY2BGR)
        _, im2_w, _ = im2.shape
    m = min(im1_w, im2_w)
    if im1_w != im2_w:
        im1 = resizer(im1, im_width=m)
        im2 = resizer(im2, im_width=m)
    divider = np.zeros((div_thickness, m, 3), np.uint8)
    divider[:, 0:m] = (255, 255, 255)
    stack = np.vstack((im1, divider, im2))
    to_save = custom_imshow(stack, title)
    if to_save:
        path = askdirectory(title="Select Folder")
        if path:
            filename = p_in("Filename: ")
            save_image(im2, filename, path)
            p_i("File was saved")


def get_image_shape(img, new_width=2800):
    im_height, im_width, _ = img.shape
    new_height = int(new_width * im_height / im_width)
    return new_width, new_height


def save_image(image, filename, folder=None, unique=False):
    filename = filename.lower()
    un = f"-{datetime.now().strftime('%Y%m%d%H%M%S')}" if unique else ""
    if folder:
        cv2.imwrite(f"{folder}/{filename}{un}.png", image)
    else:
        cv2.imwrite(f"{filename}{un}.png", image)


def open_image(path):
    return cv2.imread(path)


def f_print(image, n=3, m=2):
    return np.repeat(image[..., np.newaxis], n, axis=m)
