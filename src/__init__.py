import cv2
from main import main
from tools.color_map import color_gradient_to_index, create_color_gradient_image, load_gradient

if __name__ == '__main__':
    main()
    # color_gradient_to_index()
    # p = load_gradient()
    exit()
    im = cv2.imread('data/bergen.png')
    for key, val in p.items():
        b, g, r = [int(i) for i in key.strip('[]').split()]
        for v in val:
            im[v[0], v[1]] = (b, g, r)
    cv2.imwrite('data/color_gradient2.png', im)
