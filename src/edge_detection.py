import cv2
import numpy as np


def nothing(x):
    pass


def edge_detection(image):
    print('Opening external window')
    n = 'Canny Edge Detection'
    cv2.namedWindow(n)
    switch = 'Show Contours'

    # automatically set lb and ub values from the median color in the image
    v = np.median(image)
    sigma = 0.33
    lb = int(max(0, (1.0 - sigma) * v))
    ub = int(min(100, (1.0 + sigma) * v))

    blurred = cv2.medianBlur(image, 3)
    # gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)

    cv2.createTrackbar(switch, n, 1, 1, nothing)
    cv2.createTrackbar('Lower Bound', n, lb, 100, nothing)
    cv2.createTrackbar('Upper Bound', n, ub, 100, nothing)
    while True:
        s = cv2.getTrackbarPos(switch, n)
        lb = cv2.getTrackbarPos('Lower Bound', n)
        ub = cv2.getTrackbarPos('Upper Bound', n)
        if s == 0:
            edges = blurred
        else:
            edges = cv2.Canny(blurred, lb, ub)
        cv2.imshow(n, edges)
        k = cv2.waitKey(1) & 0xFF
        if k == 27:  # use escape for exiting window, auto save image
            cv2.destroyAllWindows()
            return edges
