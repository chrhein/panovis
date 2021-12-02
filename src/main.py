import os
from feature_matching import feature_matching
from edge_detection import edge_detection
from dem import render_dem
from data_getters.mountains import get_mountains, compare_two_mountain_lists
from im import save_image
from tools.file_handling import select_file, tui_select


def main():
    info_title = "Select one of these modes to continue:"
    main_modes = [
        "DEM Rendering",
        "Edge Detection",
        "Feature Matching",
        "Compare Datasets",
        "Previous Choices",
    ]
    input_text = "Select mode: "
    error_text = "No valid mode given."

    mode = tui_select(main_modes, info_title, input_text, error_text)
    if mode == 1:
        info_title = "Select one of these modes to continue:"
        dem_modes = [
            "Render DEM with Depth Map Texture",
            "Render DEM with Height Coloring",
            "Render DEM with Hike Route Texture",
            "Mountains in-sight Lookup",
        ]
        input_text = "Select mode: "
        error_text = "No valid mode given."
        dem_mode_selected = tui_select(
            dem_modes, info_title, input_text, error_text, True
        )
        pano_folder = "data/panoramas/"
        panos = select_file(pano_folder)
        if dem_mode_selected == 4:
            mountains = list(get_mountains("data/mountains/").values())[0]["mountains"]
        else:
            mountains = ""
        for pano in panos:
            render_dem(pano, dem_mode_selected, mountains)
        os.makedirs("dev/", exist_ok=True)
        f = open("dev/mode.txt", "w+")
        f.write(f"{mode}::{dem_mode_selected}::{panos}")
    elif mode == 2:
        info_title = "Select one of these algorithms to continue:"
        mode_types = ["Canny", "Holistically-Nested (HED)", "Horizon Highlighting"]
        input_text = "Select algorithm: "
        error_text = "No valid algorithm given."
        kind = tui_select(mode_types, info_title, input_text, error_text)
        pano_folder = "data/panoramas/"
        panos = select_file(pano_folder)
        for pano in panos:
            if kind == 1:
                algo = "Canny"
            elif kind == 2:
                algo = "HED"
            elif kind == 3:
                algo = "Horizon"
            else:
                algo = ""
            edge_detection(pano, algo)
        os.makedirs("dev/", exist_ok=True)
        f = open("dev/mode.txt", "w+")
        f.write(f"{mode}::{algo}::{panos}")
    elif mode == 3:
        pano_folder = "data/panoramas/"
        exports_folder = "exports/"
        panos = select_file(pano_folder)
        pano_filename = panos[0].split("/")[-1].split(".")[0]
        im_path = f"{exports_folder}{pano_filename}"
        im1 = select_file(im_path)[0]
        im2 = select_file(im_path)[0]
        save_image(feature_matching(im1, im2), "fm", im_path)
        os.makedirs("dev/", exist_ok=True)
        f = open("dev/mode.txt", "w+")
        f.write(f"{mode}::{im_path}::{im1}::{im2}")
    elif mode == 4:
        compare_two_mountain_lists()
    elif mode == 5:
        f = open("dev/mode.txt", "r")
        prev = f.readline().split("::")
        prev_mode = int(prev[0])
        if prev_mode == 1:
            dem_mode_selected = int(prev[1])
            panos = prev[2].strip("[]").split("', '")
            if dem_mode_selected == 4:
                mountains = list(get_mountains("data/mountains/").values())[0][
                    "mountains"
                ]
            else:
                mountains = ""
            for pano in panos:
                render_dem(str(pano).strip("'"), dem_mode_selected, mountains)
        elif prev_mode == 2:
            algo = prev[1]
            panos = prev[2].strip("[]").split("', '")
            for pano in panos:
                edge_detection(str(pano).strip("'"), algo)
        elif prev_mode == 3:
            im_path = prev[1]
            im1 = prev[2]
            im2 = prev[3]
            save_image(feature_matching(im1, im2), "fm", im_path, True)
