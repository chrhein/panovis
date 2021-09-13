import cv2
import numpy as np
from src.image_manipulations import resizer


def custom_imshow(image, title, from_left=100, from_top=400):
    cv2.namedWindow(title)
    cv2.moveWindow(title, from_left, from_top)
    cv2.imshow(title, image)
    cv2.setWindowProperty(title, cv2.WND_PROP_TOPMOST, 1)
    cv2.waitKey(0)


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
    custom_imshow(stack, title)
