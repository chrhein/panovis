import cv2
from src.debug_tools import p_i


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
        (input_shape, target_shape) = (inputs[0], inputs[1])
        (batch_size, num_channels) = (input_shape[0], input_shape[1])
        (H, W) = (target_shape[2], target_shape[3])
        # compute the starting and ending crop coordinates
        self.startX = int((input_shape[3] - target_shape[3]) / 2)
        self.startY = int((input_shape[2] - target_shape[2]) / 2)
        self.endX = self.startX + W
        self.endY = self.startY + H
        # return the shape of the volume (we'll perform the actual
        # crop during the forward pass
        return [[batch_size, num_channels, H, W]]

    def forward(self, inputs):
        # use the derived (x, y)-coordinates to perform the crop
        return [inputs[0][:, :, self.startY:self.endY,
                self.startX:self.endX]]


def holistically_nested(image):
    p_i("Starting Holistically-Nested Edge Detection...")
    net = cv2.dnn.readNetFromCaffe("assets/hed_model/deploy.prototxt",
                                   "assets/hed_model/"
                                   + "hed_pretrained_bsds.caffemodel")
    height, width = image.shape[:2]
    cv2.dnn_registerLayer("Crop", CropLayer)
    blob = cv2.dnn.blobFromImage(image, size=(width, height))
    net.setInput(blob)
    hed = (255 * cv2.resize(net.forward()[0, 0], (width, height)))\
        .astype("uint8")
    p_i("Holistically-Nested Edge Detection complete!")
    return hed
