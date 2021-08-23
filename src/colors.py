import cv2
import numpy as np

from src.debug_tools import p_i


def get_image_rgb_list(image_path, m_factor=0.55, color_space=1):
    image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    height, width, _ = image.shape
    color = image[int(height * m_factor), int(width * 0.5)]
    color = np.array_split(color, 3)
    r, g, b = color
    return r[0] / color_space, g[0] / color_space, b[0] / color_space


def color_interpolator(from_color, to_color, size):
    color_gradient = []
    for i in range(size + 1):
        r = (to_color[0] - from_color[0]) * i / size + from_color[0]
        g = (to_color[1] - from_color[1]) * i / size + from_color[1]
        b = (to_color[2] - from_color[2]) * i / size + from_color[2]
        color_gradient.append([r, 0, 0])
    return color_gradient


def get_unique_colors_in_image(image):
    image = cv2.imread(image)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return set(tuple(v) for m2d in image for v in m2d)


def get_color_from_image(image):
    m_factor = 0.0
    while True:
        color = get_image_rgb_list(image, m_factor)
        if color[1] == 0.0 or color[2] == 0.0:
            break
        if m_factor >= 1.0:
            m_factor = 0.5
            break
        m_factor += 0.01
    p_i("m_factor used: %.2f" % m_factor)
    return color, m_factor


def get_color_index_in_image(color, from_color, to_color, step_size):
    colors = color_interpolator(from_color, to_color, step_size)
    o_r, o_g, o_b = color
    p_i("Searching for: %i, %i, %i" % (o_r, o_g, o_b))

    l_index = 0
    lowest = 1000
    for i in range(len(colors)):
        r, g, b = colors[i]
        new_low_r = abs(r - o_r)
        if new_low_r < lowest:
            lowest = new_low_r
            l_index = i

    p_i(l_index)
    p_i("Found nearest color: %i, %i, %i" % (
        round(colors[l_index][0]), round(colors[l_index][1]), round(colors[l_index][2])))
    return l_index
