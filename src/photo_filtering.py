import cv2
import matplotlib.pyplot as plt


def photo_filtering(input_photo):
    photo = cv2.imread(input_photo)
    smaller = cv2.resize(photo, (0, 0), fx=0.2, fy=0.2)

    darkened = change_brightness(smaller, value=-50)
    dst = cv2.GaussianBlur(darkened, (3, 3), cv2.BORDER_DEFAULT)

    rgb = cv2.cvtColor(dst, cv2.COLOR_BGR2RGB)
    grayscale = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(grayscale, threshold1=200, threshold2=70)
    cv2.imshow("Canny Image", edges)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def change_brightness(img, value=30):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    v = cv2.add(v, value)
    v[v > 255] = 255
    v[v < 0] = 0
    final_hsv = cv2.merge((h, s, v))
    img = cv2.cvtColor(final_hsv, cv2.COLOR_HSV2BGR)
    return img
