import cv2


def photo_filtering(input_photo):
    photo = cv2.imread(input_photo)
    smaller = cv2.resize(photo, (0, 0), fx=0.2, fy=0.2)
    dst = cv2.GaussianBlur(smaller, (3, 3), 0)
    # darkened = change_brightness(dst, value=-50)

    image = cv2.cvtColor(dst, cv2.COLOR_BGR2RGB)
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 200, 255)

    _, binary = cv2.threshold(edges, 200, 255, cv2.THRESH_BINARY)

    contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    filtered_contours = [x for x in contours if (cv2.contourArea(x) > 5) and (cv2.contourArea(x) < 1000)]
    image = cv2.drawContours(smaller, filtered_contours, -1, (0, 0, 255), thickness=3)
    cv2.imshow("contour_detected_image", image)
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
