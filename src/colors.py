import cv2
import numpy as np

from tools.debug import p_i


def get_image_hsv_list(image, m_factor=0.55, color_space=1):
    height, width, _ = image.shape
    color = image[int(height * m_factor), int(width * 0.5)]
    color = np.array_split(color, 3)
    h, s, v = color
    return h[0] / color_space, s[0] / color_space, v[0] / color_space


def color_interpolator(from_color, to_color, size):
    color_gradient = []
    for i in range(size + 1):
        r = (to_color - from_color) * i / size + from_color
        color_gradient.append(int(r))
    return color_gradient


def get_unique_colors_in_image(image):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return set(tuple(v) for m2d in image for v in m2d)


def get_color_from_image(image_path):
    image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    m_factor = 0.0
    while True:
        color = get_image_hsv_list(image, m_factor)
        if color[1] == 0.0 or color[2] == 0.0:
            break
        if m_factor >= 1.0:
            m_factor = 0.5
            break
        m_factor += 0.01
    p_i("m_factor used: %.2f" % m_factor)
    return color, m_factor


def get_color_index_in_image(color, colors):
    o_r, _, _ = color
    l_index = 0
    lowest = 1000
    for i in range(1000, len(colors), 5):
        r, _, _ = colors[i]
        new_low_r = abs(r - o_r)
        if new_low_r < lowest:
            lowest = new_low_r
            l_index = i
    return l_index
