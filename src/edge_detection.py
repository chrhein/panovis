import cv2
import numpy as np

from src.debug_tools import p_i, nothing


def edge_detection(image, interactive_window, blur_factor):
    print("[INFO] Starting Canny Edge Detection...")
    # automatically set lb and ub values from the median color in the image
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    v = np.median(gray)
    sigma = 0.5
    lb = int(max(0, (1.0 - sigma) * v))
    ub = int(min(100, (1.0 + sigma) * v))

    blurred = cv2.medianBlur(gray, blur_factor)
    # blurred = cv2.GaussianBlur(image, (blur_factor, blur_factor), 0)
    # blurred = cv2.blur(image, (blur_factor, blur_factor), 0)
    # blurred = cv2.bilateralFilter(image, blur_factor, 75, 75)
    if not interactive_window:
        print("[INFO] Canny Edge Detection complete!")
        return cv2.Canny(blurred, lb, ub)

    p_i('Opening external window')
    n = 'Canny Edge Detection'
    cv2.namedWindow(n)
    switch = 'Show Contours'
    cv2.createTrackbar(switch, n, 1, 1, nothing)
    cv2.createTrackbar('Lower Bound', n, lb, 100, nothing)
    cv2.createTrackbar('Upper Bound', n, ub, 100, nothing)
    while True:
        s = cv2.getTrackbarPos(switch, n)
        lb = cv2.getTrackbarPos('Lower Bound', n)
        ub = cv2.getTrackbarPos('Upper Bound', n)
        if s == 0:
            edges = image
        else:
            edges = cv2.Canny(blurred, lb, ub)
        cv2.imshow(n, edges)
        k = cv2.waitKey(1) & 0xFF
        if k == 27:  # use escape for exiting window, auto save image
            cv2.destroyAllWindows()
            p_i("Canny Edge Detection complete!")
            return edges
