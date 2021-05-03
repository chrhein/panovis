import cv2
import numpy as np

from src.debug_tools import p_i
from src.edge_detection import edge_detection


def change_brightness(img, value=30):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    v = cv2.add(v, value)
    v[v > 255] = 255
    v[v < 0] = 0
    final_hsv = cv2.merge((h, s, v))
    img = cv2.cvtColor(final_hsv, cv2.COLOR_HSV2BGR)
    return img


def image_contouring(original_image, edge_detected_image):
    contours, hierarchy = cv2.findContours(edge_detected_image.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contoured_image = cv2.drawContours(original_image.copy(), contours, -1, (0, 0, 255), thickness=3)
    return [original_image, f_print(edge_detected_image), contoured_image]
    pass


def dilate_and_erode(image):
    kernel = np.ones((3, 3), 'uint8')
    dilated = cv2.dilate(image.copy(), kernel, iterations=1)
    eroded = cv2.erode(dilated, kernel)
    return eroded


def structured_forest(image):
    p_i("Starting Structured Forest Edge Detection...")
    sf = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    sf = sf.astype(np.float32) / 512.0
    edge_detector = cv2.ximgproc.createStructuredEdgeDetection('assets/model.yml')
    edges = edge_detector.detectEdges(sf) * 512.0
    p_i("Structured Forest Edge Detection complete!")
    return edges


def holistically_nested(image):
    p_i("Starting Holistically-Nested Edge Detection...")
    # model and how its used found here:
    # https://www.pyimagesearch.com/2019/03/04/holistically-nested-edge-detection-with-opencv-and-deep-learning/
    net = cv2.dnn.readNetFromCaffe("assets/hed_model/deploy.prototxt",
                                   "assets/hed_model/hed_pretrained_bsds.caffemodel")
    height, width = image.shape[:2]
    cv2.dnn_registerLayer("Crop", CropLayer)
    blob = cv2.dnn.blobFromImage(image, size=(width, height))
    net.setInput(blob)
    hed = (255 * cv2.resize(net.forward()[0, 0], (width, height))).astype("uint8")
    p_i("Holistically-Nested Edge Detection complete!")
    return hed


def f_print(image, n=3, m=2):
    # force image to be the same dimensions as the other images it will be shown with
    return np.repeat(image[..., np.newaxis], n, axis=m)


def resizer(image, width=0.1, height=0.1):
    return cv2.resize(image, (0, 0), fx=width, fy=height)


def annotate_image(image, text):
    header = np.zeros((75, image.shape[1], 3), np.uint8)
    header[:] = (0, 0, 0)
    out_im = cv2.vconcat((header, image))
    font = cv2.FONT_HERSHEY_COMPLEX
    cv2.putText(out_im, text, (10, 53), font, 2, (255, 255, 255), 3, 0)
    return out_im


def photo_filtering(input_photo):
    p_i("Detecting edges in '%s'...\n" % input_photo)
    filename = input_photo.split("/")[1].split(".")[0]
    image = cv2.imread(input_photo)
    image = resizer(image)
    auto_canny_detected = edge_detection(image, False, 7)
    hed = holistically_nested(image)
    sf = structured_forest(image)

    p_i("Exporting edge detected images...")
    cv2.imwrite(filename="exports/edge_detections/canny_%s.png" % filename,
                img=annotate_image(np.concatenate([image, f_print(auto_canny_detected)]), "Canny"))
    cv2.imwrite(filename="exports/edge_detections/hed_%s.png" % filename,
                img=annotate_image(np.concatenate([image, f_print(hed)]), "Holistically-Nested"))
    cv2.imwrite(filename="exports/edge_detections/sf_%s.png" % filename, img=sf)
    nsf = cv2.imread("exports/edge_detections/sf_%s.png" % filename)
    cv2.imwrite(filename="exports/edge_detections/sf_%s.png" % filename,
                img=annotate_image(np.concatenate([image, nsf]), "Structured Forest"))
    p_i("Exporting complete!")


# also from the link above
class CropLayer(object):
    def __init__(self, params, blobs):
        # initialize our starting and ending (x, y)-coordinates of
        # the crop
        self.startX = 0
        self.startY = 0
        self.endX = 0
        self.endY = 0

    def getMemoryShapes(self, inputs):
        # the crop layer will receive two inputs -- we need to crop
        # the first input blob to match the shape of the second one,
        # keeping the batch size and number of channels
        (inputShape, targetShape) = (inputs[0], inputs[1])
        (batchSize, numChannels) = (inputShape[0], inputShape[1])
        (H, W) = (targetShape[2], targetShape[3])

        # compute the starting and ending crop coordinates
        self.startX = int((inputShape[3] - targetShape[3]) / 2)
        self.startY = int((inputShape[2] - targetShape[2]) / 2)
        self.endX = self.startX + W
        self.endY = self.startY + H

        # return the shape of the volume (we'll perform the actual
        # crop during the forward pass
        return [[batchSize, numChannels, H, W]]

    def forward(self, inputs):
        # use the derived (x, y)-coordinates to perform the crop
        return [inputs[0][:, :, self.startY:self.endY,
                self.startX:self.endX]]
