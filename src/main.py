from feature_matching import feature_matching
from edge_detection import edge_detection
from dem import render_dem
from data_getters.mountains import get_mountains
from im import custom_imshow
from tools.file_handling import select_file, tui_select, file_chooser


def main():
    render_dem('data/panoramas/panorama4.jpg', 2, '')
    custom_imshow('exports/panorama4/render-height.png', 'Preview')
    exit()
    info_title = 'Select one of these modes to continue:'
    main_modes = [
        'DEM Rendering',
        'Edge Detection',
        'Feature Matching'
    ]
    input_text = 'Select mode: '
    error_text = 'No valid mode given.'

    mode = tui_select(main_modes, info_title, input_text, error_text)
    if mode == 1:
        info_title = 'Select one of these modes to continue:'
        dem_modes = [
            'Render DEM with Depth Map Texture',
            'Render DEM with Height Coloring',
            'Render DEM with Hike Route Texture',
            'Mountains In-Sight Lookup',
        ]
        input_text = 'Select mode: '
        error_text = 'No valid mode given.'
        dem_mode_selected = tui_select(dem_modes, info_title, input_text, error_text, True)
        pano_folder = 'data/panoramas/'
        panos = select_file(pano_folder)
        if dem_mode_selected == 4:
            mountains = get_mountains('data/mountains/')
        else:
            mountains = ''
        for pano in panos:
            render_dem(pano, dem_mode_selected, mountains)
    elif mode == 2:
        info_title = 'Select one of these algorithms to continue:'
        mode_types = [
            'Canny',
            'Holistically-Nested (HED)',
            'Horizon Highlighting'
        ]
        input_text = 'Select algorithm: '
        error_text = 'No valid algorithm given.'
        kind = tui_select(mode_types, info_title, input_text, error_text)
        image = file_chooser('Select an image to detect edges on')
        if kind == 1:
            edge_detection(image, 'Canny')
        elif kind == 2:
            edge_detection(image, 'HED')
        elif kind == 3:
            edge_detection(image, 'Horizon')
    elif mode == 3:
        image1 = file_chooser('Select render')
        image2 = file_chooser('Select image')
        feature_matching(image1, image2)
