import cv2

def nothing(x):
    pass

def edge_detection(image):
    print('Opening external window')
    n = 'Canny Edge Detection'
    img = cv2.imread(image)
    cv2.namedWindow(n)
    switch = 'Show Contours'
    cv2.createTrackbar(switch, n, 0, 1, nothing)
    cv2.createTrackbar('Lower Bound', n, 0, 100, nothing)
    cv2.createTrackbar('Upper Bound', n, 0, 100, nothing)
    while(True):
        s = cv2.getTrackbarPos(switch, n)
        lb = cv2.getTrackbarPos('Lower Bound', n)
        ub = cv2.getTrackbarPos('Upper Bound', n)
        if s == 0:
            edges = img
        else:
            edges = cv2.Canny(img, lb, ub)
        cv2.imshow(n, edges)
        k = cv2.waitKey(1) & 0xFF
        if k == 27:  # use escape for exiting window, autosave image
            cv2.imwrite('canny.png', edges)
            print('Created image using Canny Edge Detection')
            break
    cv2.destroyAllWindows
    