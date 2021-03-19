import math as m
import numpy as np


def LLHtoECEF(lat, lon, alt):
    # see http://www.mathworks.de/help/toolbox/aeroblks/llatoecefposition.html

    rad = np.float64(6378137.0)        # Radius of the Earth (in meters)
    f = np.float64(1.0/298.257223563)  # Flattening factor WGS84 Model
    cosLat = np.cos(lat)
    sinLat = np.sin(lat)
    FF     = (1.0-f)**2
    C      = 1/np.sqrt(cosLat**2 + FF * sinLat**2)
    S      = C * FF

    x = (rad * C + alt)*cosLat * np.cos(lon)
    y = (rad * C + alt)*cosLat * np.sin(lon)
    z = (rad * S + alt)*sinLat

    return (x, y, z)

pos = LLHtoECEF(60.3609, 5.3191, 0)
        # Radius of the Earth (in meters)
R = np.float64(6378137.0)
lat = 60.36458
lon = 5.32426


def get_cartesian(lat=None,lon=None):
    lat, lon = np.deg2rad(lat), np.deg2rad(lon)
    print('latlatlat:', lat, 'lonlon:', lon)
    R = 6371 # radius of the earth
    x = R * np.cos(lat) * np.cos(lon)
    y = R * np.cos(lat) * np.sin(lon)
    z = R *np.sin(lat)
    return x,y,z

print('cart:', get_cartesian(lat, lon))

x = R * m.cos(lat) * m.cos(lon)

y = R * m.cos(lat) * m.sin(lon)

z = R * m.sin(lat)

pos = get_cartesian(lat, lon)
x, y, z = pos[0], pos[1], pos[2]
length = m.sqrt(x**2+y**2+z**2)
v = (x/length, y/length, z/length)
print(v)

print('3270.5,-4593.9')
print()

normalized = (1/(61.07762884508124-60.06285261573484))
print(normalized)
'''
min_x = 60.06285261573484
max_x = 61.07762884508124
min_y = 4.8144238494077305
max_y = 6.8766610561377925
'''

min_x = -50205.0
max_x = 50205.0
min_y = 6699795.0
max_y = 6800205.0
print((((lat - min_x) * 100) / (max_x - min_x)))
print((((lon - min_x) * 100) / (max_x - min_x)))

print((lat * m.pi) / 180)





polar_lat = -32631
polar_lon = 6731207
lat_scaled = (polar_lat-min_x)/(max_x-min_x)
lon_scaled = (polar_lon-min_y)/(max_y-min_y)

print(lat_scaled)
print(lon_scaled)