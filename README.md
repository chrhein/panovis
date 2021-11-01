# E2

E2 is a program for rendering digital elevations models, overlaying `gpx` on top of the rendered landscape and finding the corresponding edges in a real-world panorama. The goal with this project is to automate the whole process so that the user only needs to choose which panorama to use and then E2 will do the rest.

As of now, E2 can be used to render landscapes from the DEM file provided given a hardcoded set of `LatLon` coordinates, field of view and viewing direction. Using the following parameters,

```json
"camera_location": {
    "latitude": 60.36423590473352,
    "longitude": 5.382310057603189,
    "panoramic_angle": 210,
    "view_direction": 280
}
```

E2 computes a `pov` file which is used to render the following panoramic render:

![](preview/preview-height.png)

Using a `gpx` file with coordinates that should be in sight in the render, a route texture is computed looking like this:

![](preview/preview-hike-route.png)

To visually see where in the DEM we are going to place the route texture, E2 includes a birds eye view rendering mode. This mode can be used to overlay the `gpx` on the DEM while looking high above the center of the map.

![](preview/preview-hike-birds-eye.png)

Finally, using the same parameters as in the first render we can paint the route texture into the landscape, which results in a render like the following image:

![](preview/preview-hike.png)
