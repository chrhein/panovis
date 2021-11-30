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


def skeletonize(image, lb_threshold=50):
    _, img = cv2.threshold(image, lb_threshold, 255, 0)
    skeleton_image = np.zeros(img.shape, np.uint8)
    vertical_effect = 3
    horizontal_effect = 3
    kernel = np.ones((vertical_effect, horizontal_effect), np.uint8)
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


def trim_edges(image):
    vertical_effect = 2
    horizontal_effect = 6
    kernel = np.ones((vertical_effect, horizontal_effect), np.uint8)
    dilated_image = cv2.dilate(image, kernel, iterations=5)
    eroded_image = cv2.erode(dilated_image, kernel, iterations=6)

    _, thresh_binary = cv2.threshold(eroded_image, 1, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(
        image=thresh_binary, mode=cv2.RETR_CCOMP, method=cv2.CHAIN_APPROX_NONE
    )
    mask = np.zeros(image.shape[:2], dtype=np.uint8)

    if len(contours) != 0:
        cv2.drawContours(mask, contours, -1, 255, 5)

    masked_image = cv2.bitwise_and(eroded_image, mask)

    median_blur = cv2.medianBlur(masked_image, 3)

    _, thresh_binary = cv2.threshold(median_blur, 25, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(
        image=thresh_binary, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_SIMPLE
    )
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    [
        cv2.drawContours(mask, [cnt], 0, (255), -1)
        for cnt in contours
        if cv2.contourArea(cnt) > 100
    ]

    masked_image = cv2.bitwise_and(median_blur, mask)
    skeletonized_image = skeletonize(masked_image, 10)

    vertical_effect = 2
    horizontal_effect = 3
    kernel = np.ones((vertical_effect, horizontal_effect), np.uint8)
    dilated_image = cv2.dilate(skeletonized_image, kernel, iterations=2)
    eroded_image = cv2.erode(dilated_image, kernel, iterations=1)

    _, thresh_binary = cv2.threshold(eroded_image, 1, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(
        image=thresh_binary, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_SIMPLE
    )
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    [
        cv2.drawContours(mask, [cnt], 0, (255), -1)
        for cnt in contours
        if cv2.contourArea(cnt) > 100
    ]

    masked_image = cv2.bitwise_and(eroded_image, mask)
    # eroded_image = cv2.erode(masked_image, kernel, iterations=1)

    return masked_image
