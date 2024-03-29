import cv2
from image_handling import flip, trim_edges


def sift(image, detector):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    key_points, descriptors = detector.detectAndCompute(gray, None)
    return [key_points, descriptors]


def feature_matching(pano, render):
    detector = cv2.SIFT_create(nOctaveLayers=3)

    def get_key_points(image):
        im = cv2.imread(image)
        flipped = flip(im)
        flipped = cv2.GaussianBlur(flipped, (3, 5), 0)
        trimmed = trim_edges(flipped)
        trimmed = trimmed if cv2.countNonZero(trimmed) != 0 else flipped
        key_points, descriptors = sift(trimmed, detector)
        return [trimmed, key_points, descriptors]

    pano, kp_pano, d_pano = get_key_points(pano)
    render, kp_render, d_render = get_key_points(render)

    FLANN_INDEX_KDTREE = 1
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=2)
    search_params = dict(checks=100)

    flann = cv2.FlannBasedMatcher(index_params, search_params)

    matches = flann.knnMatch(d_pano, d_render, k=2)
    matchesMask = [[0, 0] for _ in range(len(matches))]

    # ratio test as per Lowe's paper
    for i, (m, n) in enumerate(matches):
        if m.distance < 1 * n.distance:
            matchesMask[i] = [1, 0]

    draw_params = dict(
        matchColor=(0, 255, 0),
        singlePointColor=(255, 0, 0),
        matchesMask=matchesMask,
        flags=0,
    )

    result = cv2.drawMatchesKnn(
        pano, kp_pano, render, kp_render, matches, None, **draw_params
    )
    return flip(result, 1)
