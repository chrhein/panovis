import cv2
import matplotlib.pyplot as plt

from src.edge_detection import edge_detection


def photo_filtering(input_photo):
    photo = cv2.imread(input_photo)
    smaller = cv2.resize(photo, (0, 0), fx=0.2, fy=0.2)
    dst = cv2.GaussianBlur(smaller, (3, 3), cv2.BORDER_DEFAULT)
    rgb = cv2.cvtColor(dst, cv2.COLOR_BGR2RGB)
    grayscale = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    ret, thresh = cv2.threshold(grayscale, 220, 255, cv2.THRESH_BINARY_INV)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    imageC = cv2.drawContours(smaller, contours, -1, (0, 0, 255), 2)
    plt.imshow(imageC)
    plt.show()
    '''
    cv2.imwrite('/tmp/grayscale.png', thresh)
    edge_detection('/tmp/grayscale.png')
    '''