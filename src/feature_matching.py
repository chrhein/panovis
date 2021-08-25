import cv2

from src.debug_tools import custom_imshow
from src.edge_detection import sift


def feature_matching(image1, image2, title="Feature Matched Images"):
    image1 = cv2.imread(image1)
    image2 = cv2.imread(image2)
    key_points_1, descriptors_1 = sift(image1)
    key_points_2, descriptors_2 = sift(image2)
    bf = cv2.BFMatcher(cv2.NORM_L1, crossCheck=True)
    matches = bf.match(descriptors_1, descriptors_2)
    matches = sorted(matches, key=lambda x: x.distance)
    image3 = cv2.drawMatches(image1, key_points_1, image2, key_points_2, matches[:50], image2, flags=2)
    custom_imshow(image3, title), cv2.waitKey(0)