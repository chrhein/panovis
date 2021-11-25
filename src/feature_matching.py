import cv2
import numpy as np
from im import custom_imshow


def save_image(image, filename):
    cv2.imwrite("./feature_matching/fm_%s.png" % filename, image)


def open_image(filename):
    return cv2.imread("./feature_matching/fm_%s.png" % filename)


'''

PIPELINE:

Photo:
- HED + skeletonizing + trimming
- Photo Edges
- SIFT
- Photo Edges - pt! ??

Render:
- Canny Edge Detection
- Render Edges
- SIFT
- Render Edges - p ??

Photo + Render = Match

'''


def sift(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    s = cv2.SIFT_create()
    key_points, descriptors = s.detectAndCompute(gray, None)
    return [key_points, descriptors]


def flip(image, direction=0):
    image = cv2.transpose(image)
    return cv2.flip(image, flipCode=direction)


def skeletonize(image):
    img1 = image.copy()
    _, img = cv2.threshold(img1, 50, 255, 0)
    skel = np.zeros(img.shape, np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (5, 5))
    while True:
        opening = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
        temp = cv2.subtract(img, opening)
        eroded = cv2.erode(img, kernel)
        skel = cv2.bitwise_or(skel, temp)
        img = eroded.copy()
        if cv2.countNonZero(img) == 0:
            break
    return skel


def feature_matching(image1, image2, folder="", im_orig="", im_rendr=""):
    im1 = flip(cv2.imread(image1))
    im2 = flip(cv2.imread(image2))

    key_points_1, descriptors_1 = sift(im1)
    key_points_2, descriptors_2 = sift(im2)

    bf = cv2.BFMatcher(cv2.NORM_L1, crossCheck=True)
    matches = bf.match(descriptors_1, descriptors_2)
    matches = sorted(matches, key=lambda x: x.distance)
    image3 = flip(cv2.drawMatches(im1, key_points_1, im2,
                                  key_points_2, matches[:50],
                                  im2, flags=2), 1)
    if im_orig and im_rendr:
        im1 = flip(cv2.imread(im_rendr))
        im2 = flip(cv2.imread(im_orig))
        image4 = flip(cv2.drawMatches(im1, key_points_1, im2,
                                      key_points_2, matches[:50],
                                      im2, flags=2), 1)
    if folder:
        cv2.imwrite("%sfeature_matched.png" % folder, image3)
        if im_orig and im_rendr:
            cv2.imwrite("%sfeature_matched_color.png" % folder, image4)
    else:
        custom_imshow(image3, "FM"), cv2.waitKey(0)
