import cv2
import numpy as np
from hed import holistically_nested
from im import save_image
from tools.debug import p_i, nothing
from image_manipulations import resizer, skeletonize
from pickle import load, dump


def edge_detection(image_path, algorithm, im_w=2800):
    panorama_filename = image_path.split("/")[-1].split(".")[0]
    folder = f"exports/{panorama_filename}/"
    if algorithm == "Canny":
        im_path = "%srender-depth.png" % folder
        image = cv2.imread(im_path)
        edge_detected_image = skeletonize(canny_edge_detection(image, True))
    elif algorithm == "HED":
        image = cv2.imread(image_path)
        height, width, _ = image.shape
        max_length = max(height, width)

        if max_length > im_w:
            image = resizer(image, im_width=im_w)
        try:
            holistically_nested_image = load(
                open("%sedge-detected-hed.pkl" % folder, "rb")
            )
        except (OSError, IOError):
            holistically_nested_image = holistically_nested(image)
            dump(
                holistically_nested_image,
                open("%sedge-detected-hed.pkl" % folder, "wb"),
            )

        edge_detected_image = holistically_nested_image
    elif algorithm == "Horizon":
        edge_detected_image = find_horizon_edge(image_path)
    else:
        return
    save_image(
        edge_detected_image,
        f"edge-detected-{algorithm}",
        folder,
    )


def harris_corner_detection(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = np.float32(gray)
    dst = cv2.cornerHarris(gray, 2, 3, 0.04)
    dst = cv2.dilate(dst, None)
    image[dst > 0.01 * dst.max()] = [0, 0, 255]
    return image


def canny_edge_detection(image, interactive_window=True, blur_factor=5):
    p_i("Starting Canny Edge Detection...")
    # automatically set lb and ub values from the median color in the image
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    v = np.median(gray)
    sigma = 0.5
    lb = int(max(0, (1.0 - sigma) * v))
    ub = int(min(100, (1.0 + sigma) * v))

    blurred = cv2.medianBlur(gray, blur_factor)
    if not interactive_window:
        p_i("Canny Edge Detection complete!")
        return cv2.Canny(blurred, lb, ub, apertureSize=5)

    p_i("Opening external window")
    n = "Canny Edge Detection"
    cv2.namedWindow(n)
    cv2.createTrackbar("Lower Bound", n, lb, 100, nothing)
    cv2.createTrackbar("Upper Bound", n, ub, 100, nothing)
    cv2.createTrackbar("Dilate Horizontal", n, 1, 20, nothing)
    cv2.createTrackbar("Dilate Vertical", n, 1, 20, nothing)
    while True:
        lb = cv2.getTrackbarPos("Lower Bound", n)
        ub = cv2.getTrackbarPos("Upper Bound", n)
        d_h = cv2.getTrackbarPos("Dilate Horizontal", n)
        d_v = cv2.getTrackbarPos("Dilate Vertical", n)
        edges = cv2.Canny(blurred, lb, ub)
        kernel = np.ones((d_v, d_h), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=1)
        cv2.imshow(n, dilated)
        k = cv2.waitKey(1) & 0xFF
        if k == 27:  # use escape for exiting window
            cv2.destroyAllWindows()
            p_i("Canny Edge Detection complete!")
            return dilated


def remove_pixels(image, thresh=100):
    rows, cols, _ = image.shape
    for row in range(rows):
        for col in range(cols):
            k = image[row, col]
            r, g, b = k
            if r < thresh or g < thresh or b < thresh:
                image[row, col] = [0, 0, 0]
    return image


def find_horizon_edge(image):
    image_path = image
    image = cv2.imread(image_path)
    image = remove_pixels(image, 10)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    kernel = np.ones((1, 20), np.uint8)
    d_im = cv2.dilate(gray, kernel, iterations=1)
    gray = cv2.erode(d_im, kernel, iterations=1)
    rows, cols = gray.shape
    brightest_pixels = []
    search_area = 2
    for col in range(search_area, cols - search_area):
        edge_center = gray[search_area, col]
        backtrack = False
        for row in range(search_area, int(rows * 0.75)):
            k = gray[row, col]
            if k > edge_center and not backtrack:
                edge_center = k
            elif k < edge_center and not backtrack:
                brightest_pixels.append((row, col))
                break
    for px in brightest_pixels:
        x, y = px
        color_specific_pixel(image, x, y, [0, 0, 255], search_area)
    return image


def color_specific_pixel(image, pixel_x, pixel_y, color, size):
    for y in range(-size, size):
        for x in range(-size, size):
            try:
                image[pixel_x + x, pixel_y + y] = color
            except IndexError:
                continue


def pixel_eigenvalue(image, pixel_x, pixel_y, size):
    sum = 0
    index = 0
    for y in range(-size, size):
        for x in range(-size, size):
            try:
                sum += image[pixel_x + x, pixel_y + y]
                index += 1
            except IndexError:
                continue
    return sum / index
