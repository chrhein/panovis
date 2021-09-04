import cv2


from src.photo_filtering import resizer
from src.hed import holistically_nested


def save_image(image, filename):
    cv2.imwrite("./feature_matching/fm_%s.png" % filename, image)


'''

PIPELINE:

Photo:
- HED + skeletonizing + trimming
- Photo Edges
- SIFT
- Photo Edges - pt! ??

Render:
- Canny Edge Detection
- Render Edges
- SIFT
- Render Edges - p ??

Photo + Render = Match

'''


def feature_matching(image2):

    # RENDER
    '''
    render = cv2.imread(image1)
    canny = canny_edge_detection(render, interactive_window=False)
    save_image(canny, "canny")
    canny = cv2.imread("./feature_matching/fm_canny.png")
    render_keypoints, render_descriptors = sift(resizer(canny))
    '''

    # PHOTO
    photo = cv2.imread(image2)
    heded = holistically_nested(resizer(photo))
    save_image(heded, "hed")
