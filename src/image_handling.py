import ast
from base64 import b64encode
import io
import os
from PIL import Image
import cv2
import numpy as np
from location_handler import get_bearing, get_field_of_view
from renderer import render_height
from tools.converters import dms_to_decimal_degrees
from tools.debug import custom_imshow, p_i, p_in
from datetime import datetime
from tkinter.filedialog import askdirectory
from exifread import process_file
from tools.types import Location
from piexif import transplant


def get_exif_data(file_path):
    with open(file_path, "rb") as f:
        tags = process_file(f)
        f.close()
        has_gps_exif = [
            i in tags.keys()
            for i in [
                "GPS GPSLatitude",
                "GPS GPSLatitudeRef",
                "GPS GPSLongitude",
                "GPS GPSLongitudeRef",
            ]
        ]
        if not all(has_gps_exif):
            return None
        lat = tags["GPS GPSLatitude"]
        lon = tags["GPS GPSLongitude"]
        lat_ref = tags["GPS GPSLatitudeRef"]
        lon_ref = tags["GPS GPSLongitudeRef"]
        if lat_ref.printable == "S":
            lat = -lat
        if lon_ref.printable == "W":
            lon = -lon
    return Location(dms_to_decimal_degrees(lat), dms_to_decimal_degrees(lon))


def vertical_stack_imshow_divider(im1, im2, title="Preview", div_thickness=3):
    try:
        _, im1_w, _ = im1.shape
    except ValueError:
        im1 = cv2.cvtColor(im1, cv2.COLOR_GRAY2BGR)
        _, im1_w, _ = im1.shape
    try:
        _, im2_w, _ = im2.shape
    except ValueError:
        im2 = cv2.cvtColor(im2, cv2.COLOR_GRAY2BGR)
        _, im2_w, _ = im2.shape
    m = min(im1_w, im2_w)
    if im1_w != im2_w:
        im1 = resizer(im1, im_width=m)
        im2 = resizer(im2, im_width=m)
    divider = np.zeros((div_thickness, m, 3), np.uint8)
    divider[:, 0:m] = (255, 255, 255)
    stack = np.vstack((im1, divider, im2))
    to_save = custom_imshow(stack, title)
    if to_save:
        path = askdirectory(title="Select Folder")
        if path:
            filename = p_in("Filename: ")
            save_image(im2, filename, path)
            p_i("File was saved")


def get_image_shape(img, new_width=2800):
    im_height, im_width, _ = img.shape
    new_height = int(new_width * im_height / im_width)
    return new_width, new_height


def save_image(image, filename, folder=None, unique=False):
    filename = filename.lower()
    un = f"-{datetime.now().strftime('%Y%m%d%H%M%S')}" if unique else ""
    if folder:
        cv2.imwrite(f"{folder}/{filename}{un}.png", image)
    else:
        cv2.imwrite(f"{filename}{un}.png", image)


def open_image(path):
    return cv2.imread(path)


def f_print(image, n=3, m=2):
    return np.repeat(image[..., np.newaxis], n, axis=m)


def change_brightness(img, value=30):
    channels = img.ndim
    if channels == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    else:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(img)
    v = cv2.add(v, value)
    v[v > 255] = 255
    if channels == 2:
        v[v <= value] = 0
    else:
        v[v < 0] = 0
    final_hsv = cv2.merge((h, s, v))
    img = cv2.cvtColor(final_hsv, cv2.COLOR_HSV2BGR)
    if channels == 2:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img


def rotate_image_on_map(image, coor1, coor2):
    angle = get_bearing(*coor1, *coor2)

    height, width, _ = image.shape
    image_center = (width / 2, height / 2)

    rotation_mat = cv2.getRotationMatrix2D(image_center, angle, 1.0)

    abs_cos = abs(rotation_mat[0, 0])
    abs_sin = abs(rotation_mat[0, 1])

    bound_w = int(height * abs_sin + width * abs_cos)
    bound_h = int(height * abs_cos + width * abs_sin)

    rotation_mat[0, 2] += bound_w / 2 - image_center[0]
    rotation_mat[1, 2] += bound_h / 2 - image_center[1]

    rotated_mat = cv2.warpAffine(
        image,
        rotation_mat,
        (bound_w, bound_h),
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(255, 255, 255, 0),
    )

    whites = np.all(rotated_mat == 255, axis=-1)
    alpha = np.uint8(np.logical_not(whites)) * 255
    bgra = np.dstack((rotated_mat, alpha))
    im = cv2.cvtColor(bgra, cv2.COLOR_BGRA2RGBA)
    return im


def structured_forest(image):
    p_i("Starting Structured Forest Edge Detection...")
    sf = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    sf = sf.astype(np.float32) / 512.0
    edge_detector = cv2.ximgproc.createStructuredEdgeDetection("assets/model.yml")
    edges = edge_detector.detectEdges(sf) * 512.0
    p_i("Structured Forest Edge Detection complete!")
    return edges


def resizer(image, im_width=1200):
    n_size = (1 / image.shape[1]) * im_width
    return cv2.resize(image, (0, 0), fx=n_size, fy=n_size)


def annotate_image(image, text):
    header = np.zeros((75, image.shape[1], 3), np.uint8)
    header[:] = (0, 0, 0)
    out_im = cv2.vconcat((header, image))
    font = cv2.FONT_HERSHEY_COMPLEX
    cv2.putText(out_im, text, (10, 53), font, 2, (255, 255, 255), 3, 0)
    return out_im


def skeletonize(image):
    image[image != 0] = 255
    _, img = cv2.threshold(image, 1, 255, 0)
    skeleton_image = np.zeros(img.shape, np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    while True:
        opening = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
        temp = cv2.subtract(img, opening)
        img = cv2.erode(img, kernel)
        skeleton_image = cv2.bitwise_or(skeleton_image, temp)
        if cv2.countNonZero(img) == 0:
            break
    return skeleton_image


def flip(image, direction=0):
    image = cv2.transpose(image)
    return cv2.flip(image, flipCode=direction)


def remove_contours(image, min_area=100, lb=40, ub=255):
    _, thresh_binary = cv2.threshold(image, lb, ub, cv2.THRESH_BINARY)
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    contours, _ = cv2.findContours(
        image=thresh_binary, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_NONE
    )
    [
        cv2.drawContours(mask, [cnt], 0, (255), -1)
        for cnt in contours
        if cv2.contourArea(cnt) > min_area
    ]
    masked_image = cv2.bitwise_and(image, mask)
    return masked_image


def trim_edges(image):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 2))
    trimmed = cv2.dilate(image, kernel, iterations=3)
    for i in [35, 70]:
        trimmed = change_brightness(trimmed, 25)
        trimmed = remove_contours(trimmed, 50000, i, 255)
        trimmed = cv2.dilate(trimmed, kernel, iterations=1)
    trimmed = skeletonize(trimmed)
    trimmed = cv2.GaussianBlur(trimmed, (3, 3), 0)
    trimmed = remove_contours(trimmed, min_area=1250, lb=1)

    return trimmed


def reduce_filesize(image_path, image_quality=50):
    im = Image.open(image_path)
    resized_pano = f"/tmp/resized.jpg"
    im.save(resized_pano, quality=image_quality, optimize=True)
    transplant(image_path, resized_pano)
    os.remove(image_path)
    os.rename(resized_pano, image_path)


def transform_panorama(pano_path, render_path, pano_coords, render_coords):
    print(f"Pano:          {pano_path}")
    print(f"Render:        {render_path}")
    print(f"Pano coords:   {pano_coords}")
    print(f"Render coords: {render_coords}")

    pano_coords = {
        k: v
        for k, v in sorted(
            ast.literal_eval(pano_coords).items(), key=lambda x: int(x[0])
        )
    }
    render_coords = {
        k: v
        for k, v in sorted(
            ast.literal_eval(render_coords).items(), key=lambda x: int(x[0])
        )
    }

    pts_panorama = np.float32([[x, y] for x, y in pano_coords.values()])
    panorama_image = cv2.imread(pano_path)
    pts_render = np.float32([[x, y] for x, y in render_coords.values()])
    render_image = cv2.imread(render_path)
    render_width = render_image.shape[1]

    prev_x_coord = 0
    for i in range(len(pts_render)):
        x = pts_render[i][0]
        if x < prev_x_coord:
            pts_render[i][0] = x + render_width
        prev_x_coord = x

    render_image = cv2.hconcat([render_image, render_image])

    if len(pts_render) == len(pts_panorama) == 3:

        TRANSFORM_MATRIX = cv2.getAffineTransform(pts_panorama, pts_render)

        warped_panorama = cv2.warpAffine(
            panorama_image,
            TRANSFORM_MATRIX,
            (render_image.shape[1], render_image.shape[0]),
            flags=cv2.INTER_AREA,
        )

    else:

        TRANSFORM_MATRIX, _ = cv2.findHomography(pts_panorama, pts_render)

        warped_panorama = cv2.warpPerspective(
            panorama_image,
            TRANSFORM_MATRIX,
            (render_image.shape[1], render_image.shape[0]),
            flags=cv2.INTER_AREA,
            borderMode=cv2.BORDER_TRANSPARENT,
        )

    mask = np.where((warped_panorama == (0, 0, 0)).all(axis=2), 0, 255).astype(np.uint8)
    warped_panorama = cv2.cvtColor(warped_panorama, cv2.COLOR_BGR2BGRA)

    warped_panorama[:, :, 3] = mask
    render_image = cv2.cvtColor(render_image, cv2.COLOR_BGR2BGRA)
    bg_render = cv2.bitwise_and(render_image, render_image, mask=cv2.bitwise_not(mask))
    fg_panorama = cv2.bitwise_and(warped_panorama, warped_panorama, mask=mask)

    im_overlay = cv2.add(bg_render, fg_panorama)

    _, x = fg_panorama[:, :, 3].nonzero()
    minx = np.min(x)
    maxx = np.max(x)

    min_heading, max_heading = get_field_of_view(render_image.shape[1], minx, maxx)

    print(f"Min heading: {min_heading}")
    print(f"Max heading: {max_heading}")
    print(f"FOV:         {(max_heading-min_heading) % 360}")

    pano_filename = pano_path.split("/")[-1].split(".")[0]
    overlay_path = f"src/static/{pano_filename}-overlay.jpg"
    ultrawide_render_path = f"src/static/{pano_filename}-ultrawide.jpg"

    overlay_crop = im_overlay[0 : im_overlay.shape[0], minx:maxx]
    ultrawide_render_crop = render_image[0 : im_overlay.shape[0], minx:maxx]

    cv2.imwrite(overlay_path, overlay_crop)
    cv2.imwrite(ultrawide_render_path, ultrawide_render_crop)

    c_h, c_w = ultrawide_render_crop.shape[:2]

    render_height(
        pano_path,
        f"src/static/{pano_filename}-dem.png",
        imdims=[c_w, c_h],
        fov=get_field_of_view(render_image.shape[1], minx, maxx),
    )

    return overlay_path, ultrawide_render_path


def image_array_to_flask(im):
    file_object = io.BytesIO()
    img = Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGR2RGB).astype("uint8"))
    img.save(file_object, "PNG")
    base64img = "data:image/png;base64," + b64encode(file_object.getvalue()).decode(
        "ascii"
    )
    return base64img
