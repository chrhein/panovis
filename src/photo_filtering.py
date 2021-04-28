import cv2
import numpy as np

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
    return [original_image, np.repeat(edge_detected_image[..., np.newaxis], 3, axis=2), contoured_image]
    pass


def dilate_and_erode(image):
    kernel = np.ones((3, 3), 'uint8')
    dilated = cv2.dilate(image.copy(), kernel, iterations=1)
    eroded = cv2.erode(dilated, kernel)
    return eroded


def structured_forest(image):
    sf = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    sf = sf.astype(np.float32) / 512.0
    edge_detector = cv2.ximgproc.createStructuredEdgeDetection('assets/model.yml')
    edges = edge_detector.detectEdges(sf) * 512.0
    return edges


def photo_filtering(input_photo):
    im = cv2.imread(input_photo)
    # model and how its used found here:
    # https://www.pyimagesearch.com/2019/03/04/holistically-nested-edge-detection-with-opencv-and-deep-learning/
    net = cv2.dnn.readNetFromCaffe("assets/hed_model/deploy.prototxt",
                                   "assets/hed_model/hed_pretrained_bsds.caffemodel")

    image = cv2.resize(im, (0, 0), fx=0.1, fy=0.1)
    height, width = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    auto_detected = edge_detection(gray, False, 3)
    cv2.dnn_registerLayer("Crop", CropLayer)
    blob = cv2.dnn.blobFromImage(image, size=(width, height))
    net.setInput(blob)
    hed = (255 * cv2.resize(net.forward()[0, 0], (width, height))).astype("uint8")
    hed_list = [image,
                np.repeat(auto_detected[..., np.newaxis], 3, axis=2),
                np.repeat(hed[..., np.newaxis], 3, axis=2)]
    cv2.imshow("Comparing Edge Detected Images", np.vstack(hed_list))
    cv2.waitKey(0)
    cv2.destroyAllWindows()


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
