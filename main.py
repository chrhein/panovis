import sys
import cv2
from src.data_getters.mountains import get_mountain_data

from src.debug_tools import p_a, p_i
from src.feature_matching import feature_matching
from src.location_handler import look_at_location
from src.photo_filtering import photo_filtering, resizer
from src.dem import render_dem


if __name__ == '__main__':
    render_dem(*get_mountain_data('data/dem-data.json'))
    