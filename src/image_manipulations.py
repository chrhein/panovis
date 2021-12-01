import cv2
import numpy as np
from tools.debug import p_i


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
    # kernel = np.ones((3, 3), np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_DILATE, (3, 3))
    while True:
        opening = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
        temp = cv2.subtract(img, opening)
        img = cv2.erode(img, kernel)
        skeleton_image = cv2.bitwise_or(skeleton_image, temp)
        if cv2.countNonZero(img) == 0:
            break
    # dilated_image = cv2.dilate(skeleton_image, np.ones((1, 2), np.uint8), iterations=1)
    return skeleton_image


def flip(image, direction=0):
    image = cv2.transpose(image)
    return cv2.flip(image, flipCode=direction)


def trim_edges(image):
    vertical_effect = 1
    horizontal_effect = 4

    kernel = np.ones((vertical_effect, horizontal_effect), np.uint8)
    dilated_image = cv2.dilate(image, kernel, iterations=6)
    eroded_image = cv2.erode(dilated_image, kernel, iterations=7)

    _, thresh_binary = cv2.threshold(eroded_image, 40, 255, cv2.THRESH_BINARY)
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    contours, _ = cv2.findContours(
        image=thresh_binary, mode=cv2.RETR_CCOMP, method=cv2.CHAIN_APPROX_SIMPLE
    )

    if len(contours) != 0:
        [
            cv2.drawContours(mask, [cnt], 0, (255), -1)
            for cnt in contours
            if cv2.contourArea(cnt) > 10000
        ]

    masked_image = cv2.bitwise_and(eroded_image, mask)

    return skeletonize(masked_image)
