import cv2
import numpy as np
from src.debug_tools import nothing, p_line
from src.edge_detection import sift
from src.im import custom_imshow


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


def flip(image, direction=0):
    image = cv2.transpose(image)
    return cv2.flip(image, flipCode=direction)


def thin(image, lb, ub):
    img1 = image.copy()
    ret, img1 = cv2.threshold(image, lb, ub, 0)
    kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    thin = np.zeros(image.shape, dtype='uint8')
    while (cv2.countNonZero(img1) != 0):
        eroded = cv2.erode(img1, kernel)
        opening = cv2.morphologyEx(eroded, cv2.MORPH_OPEN, kernel)
        closing = cv2.morphologyEx(eroded, cv2.MORPH_CLOSE, kernel)
        subset = eroded - opening + closing
        thin = cv2.bitwise_or(subset, thin)
        img1 = eroded.copy()
    return thin


def skeletonize(image):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    lb = 0
    ub = 255

    n = 'Skeletonizing'
    cv2.namedWindow(n)
    switch = 'Skeletonize'
    cv2.createTrackbar(switch, n, 1, 1, nothing)
    cv2.createTrackbar('Lower Bound', n, 55, 255, nothing)
    cv2.createTrackbar('Upper Bound', n, 255, 255, nothing)
    while True:
        s = cv2.getTrackbarPos(switch, n)
        lb = cv2.getTrackbarPos('Lower Bound', n)
        ub = cv2.getTrackbarPos('Upper Bound', n)
        if s == 0:
            thinned = image
        else:
            thinned = thin(image, lb, ub)
        cv2.imshow(n, thinned)
        k = cv2.waitKey(1) & 0xFF
        if k == 27:  # use escape for exiting window
            cv2.destroyAllWindows()
            p_line(["lb: %i" % lb, "ub: %i" % ub])
            return thinned


def feature_matching(image1, image2):
    image1 = flip(cv2.imread(image1))
    image2 = flip(cv2.imread(image2))

    key_points_1, descriptors_1 = sift(image1)
    key_points_2, descriptors_2 = sift(image2)

    bf = cv2.BFMatcher(cv2.NORM_L1, crossCheck=True)
    matches = bf.match(descriptors_1, descriptors_2)
    matches = sorted(matches, key=lambda x: x.distance)
    image3 = flip(cv2.drawMatches(image1, key_points_1, image2,
                                  key_points_2, matches[:20],
                                  image2, flags=2), 1)
    custom_imshow(image3, "FM"), cv2.waitKey(0)
    save_image(image3, "matched")
