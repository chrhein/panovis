import cv2
import numpy as np
from hed import holistically_nested
from feature_matching import skeletonize
from tools.debug import p_i, nothing
from image_manipulations import resizer
from datetime import datetime
from pickle import load, dump


def edge_detection(image_path, algorithm, im_w=2400):
    panorama_filename = image_path.split("/")[-1].split(".")[0]
    folder = "exports/%s/" % panorama_filename
    if algorithm == "Canny":
        im_path = "%srender-depth.png" % folder
        image = cv2.imread(im_path)
        edge_detected_image = skeletonize(canny_edge_detection(image, True))
        if folder:
            cv2.imwrite("%sedge-detected-canny.png" % folder, edge_detected_image)
    elif algorithm == "HED":
        image = cv2.imread(image_path)
        t = datetime.now().strftime("%H%M%S")
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

        kernel = np.ones((5, 15), np.uint8)
        dilated_image = cv2.dilate(holistically_nested_image, kernel, iterations=1)
        skeletonized_image = skeletonize(dilated_image)

        _, thresh_binary = cv2.threshold(skeletonized_image, 50, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(
            image=thresh_binary, mode=cv2.RETR_CCOMP, method=cv2.CHAIN_APPROX_SIMPLE
        )
        mask = np.zeros(holistically_nested_image.shape[:2], dtype=np.uint8)
        [
            cv2.drawContours(mask, [cnt], 0, (255), -1)
            for cnt in contours
            if cv2.contourArea(cnt) > 100
        ]
        bitwise_and_image = cv2.bitwise_and(skeletonized_image, mask)
        # eroded_image = cv2.erode(bitwise_and_image, kernel, iterations=1)

        # eroded_image[eroded_image < 100] = 0

        # gaussian_blurred = cv2.GaussianBlur(eroded_image, (35, 3), 0)
        # median_blurred = cv2.medianBlur(gaussian_blurred, 3)

        # eroded_image = cv2.erode(bitwise_and_image, kernel, iterations=1)
        """
        skeletonized_image = skeletonize(bitwise_and_image)

        gaussian_blurred = cv2.GaussianBlur(skeletonized_image, (35, 7), 0)

        gaussian_blurred[gaussian_blurred > 25] = 255

        kernel = np.ones((7, 20), np.uint8)
        dilated_image = cv2.dilate(gaussian_blurred, kernel, iterations=1)
        eroded_image = cv2.erode(dilated_image, kernel, iterations=1)

        skeletonized_image = skeletonize(eroded_image) """

        cv2.imwrite("%sedge-detected-hed-%s.png" % (folder, t), bitwise_and_image)

    elif algorithm == "Horizon":
        edge_detected_image = find_horizon_edge(image_path)
        if folder:
            cv2.imwrite("%shighlighted_horizon.png" % folder, edge_detected_image)
    else:
        return


def harris_corner_detection(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = np.float32(gray)
    dst = cv2.cornerHarris(gray, 2, 3, 0.04)
    dst = cv2.dilate(dst, None)
    image[dst > 0.01 * dst.max()] = [0, 0, 255]
    return image


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

    p_i("Opening external window")
    n = "Canny Edge Detection"
    cv2.namedWindow(n)
    cv2.createTrackbar("Lower Bound", n, lb, 100, nothing)
    cv2.createTrackbar("Upper Bound", n, ub, 100, nothing)
    while True:
        lb = cv2.getTrackbarPos("Lower Bound", n)
        ub = cv2.getTrackbarPos("Upper Bound", n)
        edges = cv2.Canny(blurred, lb, ub)
        cv2.imshow(n, edges)
        k = cv2.waitKey(1) & 0xFF
        if k == 27:  # use escape for exiting window
            cv2.destroyAllWindows()
            p_i("Canny Edge Detection complete!")
            return edges


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
