from exifread import process_file
from tools.types import Location


def get_exif_data(file_path):
    with open(file_path, 'rb') as f:
        tags = process_file(f)
        f.close()
        has_gps_exif = [i in tags.keys() for i in [
                        'GPS GPSLatitude',
                        'GPS GPSLatitudeRef',
                        'GPS GPSLongitude',
                        'GPS GPSLongitudeRef']]
        if not all(has_gps_exif):
            return None
        lat = tags['GPS GPSLatitude']
        lon = tags['GPS GPSLongitude']
        lat_ref = tags['GPS GPSLatitudeRef']
        lon_ref = tags['GPS GPSLongitudeRef']
        if lat_ref.printable == 'S':
            lat = -lat
        if lon_ref.printable == 'W':
            lon = -lon
    return Location(convert_to_degress(lat),
                    convert_to_degress(lon))


def convert_to_degress(coordinate):
    c = coordinate.values
    d = c[0].num/c[0].den
    m = c[1].num/c[1].den
    s = c[2].num/c[2].den
    return d + (m / 60.0) + (s / 3600.0)
