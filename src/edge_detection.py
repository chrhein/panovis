import cv2
import numpy as np

from src.debug_tools import p_i, nothing


def edge_detection(image_path, folder, date):
    image = cv2.imread(image_path)
    edge_detected_image = canny_edge_detection(image)
    out_filename = '%s/edge_detected_image%s.png' % (folder, date)
    cv2.imwrite(out_filename, edge_detected_image)


def harris_corner_detection(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = np.float32(gray)
    dst = cv2.cornerHarris(gray, 2, 3, 0.04)
    dst = cv2.dilate(dst, None)
    image[dst > 0.01 * dst.max()] = [0, 0, 255]
    return image


def sift(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    s = cv2.SIFT_create()
    key_points, descriptors = s.detectAndCompute(gray, None)
    return [key_points, descriptors]


def canny_edge_detection(image, interactive_window=True, blur_factor=5):
    print("[INFO] Starting Canny Edge Detection...")
    # automatically set lb and ub values from the median color in the image
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    v = np.median(gray)
    sigma = 0.5
    lb = int(max(0, (1.0 - sigma) * v))
    ub = int(min(100, (1.0 + sigma) * v))

    blurred = cv2.medianBlur(gray, blur_factor)
    if not interactive_window:
        print("[INFO] Canny Edge Detection complete!")
        return cv2.Canny(blurred, lb, ub)

    p_i('Opening external window')
    n = 'Canny Edge Detection'
    cv2.namedWindow(n)
    switch = 'Show Contours'
    cv2.createTrackbar(switch, n, 1, 1, nothing)
    cv2.createTrackbar('Lower Bound', n, lb, 100, nothing)
    cv2.createTrackbar('Upper Bound', n, 25, 100, nothing)
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
        if k == 27:  # use escape for exiting window
            cv2.destroyAllWindows()
            p_i("Canny Edge Detection complete!")
            return edges
