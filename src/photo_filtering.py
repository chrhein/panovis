import cv2
import numpy as np

from src.edge_detection import edge_detection


def auto_canny(image, sigma=0.33):
    v = np.median(image)
    lb = int(max(0, (1.0 - sigma) * v))
    ub = int(min(255, (1.0 + sigma) * v))
    edge_detected_image = cv2.Canny(image, lb, ub)
    return edge_detected_image


def photo_filtering(input_photo):
    photo = cv2.imread(input_photo)
    out_list = []
    smaller = cv2.resize(photo, (0, 0), fx=0.2, fy=0.2)
    structured_forest = cv2.cvtColor(smaller, cv2.COLOR_BGR2RGB)
    structured_forest = structured_forest.astype(np.float32) / 255.0

    kernel = np.ones((3, 3), 'uint8')
    dilated = cv2.dilate(smaller, kernel, iterations=1)
    eroded = cv2.erode(dilated, kernel)

    edge_detector = cv2.ximgproc.createStructuredEdgeDetection('assets/model.yml')
    # detect the edges
    edges = edge_detector.detectEdges(structured_forest)

    auto = edge_detection(eroded)
    image = auto.copy()
    auto = np.repeat(auto[..., np.newaxis], 3, axis=2)

    edges = edges.astype(np.uint8)
    contours, hierarchy = cv2.findContours(image, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    forest_contours, forest_hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    contoured = cv2.drawContours(smaller.copy(), contours, -1, (0, 0, 255), thickness=3)
    contoured2 = cv2.drawContours(smaller.copy(), forest_contours, -1, (0, 255, 0), thickness=3)

    '''
    for cnt in contours:
        hull = cv2.convexHull(cnt)
        cv2.drawContours(image, [hull], 0, (0, 255, 0), 2)
        cv2.imshow('Convex Hull', image)
    for c in contours:
        accuracy = 0.1 * cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, accuracy, True)
        contoured = cv2.drawContours(smaller, [approx], 0, (0, 0, 255), 3) 
    '''

    out_list.append(auto)
    out_list.append(dilated)
    out_list.append(eroded)
    out_list.append(contoured)
    out_list.append(contoured2)

    cv2.imshow("Edges", np.vstack(out_list))
    print("Opened image in new Python window.")
    cv2.waitKey(0)


def change_brightness(img, value=30):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    v = cv2.add(v, value)
    v[v > 255] = 255
    v[v < 0] = 0
    final_hsv = cv2.merge((h, s, v))
    img = cv2.cvtColor(final_hsv, cv2.COLOR_HSV2BGR)
    return img
