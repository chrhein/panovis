from renderer import render_height
from tools.types import ImageData


def main():
    pano = 'src/static/images/2021-04-17--pic03--Lyderhorn-fac51126/2021-04-17--pic03--Lyderhorn-fac51126.jpg'
    render_height(ImageData(pano))
    pass


main()
