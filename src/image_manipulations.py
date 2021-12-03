import cv2
import numpy as np
from tools.debug import p_i


def change_brightness(img, value=30):
    channels = img.ndim
    if channels == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    else:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(img)
    v = cv2.add(v, value)
    v[v > 255] = 255
    if channels == 2:
        v[v <= value] = 0
    else:
        v[v < 0] = 0
    final_hsv = cv2.merge((h, s, v))
    img = cv2.cvtColor(final_hsv, cv2.COLOR_HSV2BGR)
    if channels == 2:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img


def structured_forest(image):
    p_i("Starting Structured Forest Edge Detection...")
    sf = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    sf = sf.astype(np.float32) / 512.0
    edge_detector = cv2.ximgproc.createStructuredEdgeDetection("assets/model.yml")
    edges = edge_detector.detectEdges(sf) * 512.0
    p_i("Structured Forest Edge Detection complete!")
    return edges


def resizer(image, im_width=1200):
    n_size = (1 / image.shape[1]) * im_width
    return cv2.resize(image, (0, 0), fx=n_size, fy=n_size)


def annotate_image(image, text):
    header = np.zeros((75, image.shape[1], 3), np.uint8)
    header[:] = (0, 0, 0)
    out_im = cv2.vconcat((header, image))
    font = cv2.FONT_HERSHEY_COMPLEX
    cv2.putText(out_im, text, (10, 53), font, 2, (255, 255, 255), 3, 0)
    return out_im


def skeletonize(image):
    image[image != 0] = 255
    _, img = cv2.threshold(image, 1, 255, 0)
    skeleton_image = np.zeros(img.shape, np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    while True:
        opening = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
        temp = cv2.subtract(img, opening)
        img = cv2.erode(img, kernel)
        skeleton_image = cv2.bitwise_or(skeleton_image, temp)
        if cv2.countNonZero(img) == 0:
            break
    return skeleton_image


def flip(image, direction=0):
    image = cv2.transpose(image)
    return cv2.flip(image, flipCode=direction)


def remove_contours(image, min_area=100, lb=40, ub=255):
    _, thresh_binary = cv2.threshold(image, lb, ub, cv2.THRESH_BINARY)
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    contours, _ = cv2.findContours(
        image=thresh_binary, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_NONE
    )
    [
        cv2.drawContours(mask, [cnt], 0, (255), -1)
        for cnt in contours
        if cv2.contourArea(cnt) > min_area
    ]
    masked_image = cv2.bitwise_and(image, mask)
    return masked_image


def trim_edges(image):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 2))
    trimmed = cv2.dilate(image, kernel, iterations=3)
    for i in [35, 70]:
        trimmed = change_brightness(trimmed, 25)
        trimmed = remove_contours(trimmed, 50000, i, 255)
        trimmed = cv2.dilate(trimmed, kernel, iterations=1)
    trimmed = skeletonize(trimmed)
    trimmed = cv2.GaussianBlur(trimmed, (3, 3), 0)
    trimmed = remove_contours(trimmed, min_area=500, lb=1)

    return trimmed
