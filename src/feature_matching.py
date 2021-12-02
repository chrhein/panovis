import cv2
from image_manipulations import flip, trim_edges


def sift(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    s = cv2.SIFT_create()
    key_points, descriptors = s.detectAndCompute(gray, None)
    return [key_points, descriptors]


def feature_matching(pano, render):
    def get_key_points(image):
        trimmed = trim_edges(flip(cv2.imread(image)))
        key_points, descriptors = sift(trimmed)
        return [trimmed, key_points, descriptors]

    pano, kp_pano, d_pano = get_key_points(pano)
    render, kp_render, d_render = get_key_points(render)

    FLANN_INDEX_KDTREE = 1
    flann_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=7)
    matcher = cv2.FlannBasedMatcher(flann_params, {})
    matches = matcher.knnMatch(d_pano, d_render, 2)
    mask = [[0, 0] for _ in range(len(matches))]

    for i, (m1, m2) in enumerate(matches):
        if m1.distance < 0.7 * m2.distance:
            mask[i] = [1, 0]
            pt1 = kp_pano[m1.queryIdx].pt
            pt2 = kp_render[m1.trainIdx].pt
            if i % 2 == 0:
                cv2.circle(pano, (int(pt1[0]), int(pt1[1])), 7, (255, 0, 255), -1)
                cv2.circle(render, (int(pt2[0]), int(pt2[1])), 7, (255, 0, 255), -1)
    draw_params = dict(
        matchColor=(0, 255, 0),
        singlePointColor=(0, 0, 255),
        matchesMask=mask,
        flags=0,
    )
    res = cv2.drawMatchesKnn(
        pano, kp_pano, render, kp_render, matches, None, **draw_params
    )
    return flip(res, 1)
