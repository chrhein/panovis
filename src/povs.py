def depth_pov(dem_file, raster_data, pov_settings):
    coordinates = raster_data[0]
    location_x, location_height, location_y, \
        view_x, view_height, view_y = coordinates
    max_height = raster_data[1][3]
    panoramic_angle = pov_settings[0]
    height_field_scale_factor = pov_settings[1]

    pov_text = '''
    #version 3.8;
    #include "colors.inc"
    #include "math.inc"

    #declare CAMERAX = %f;
    #declare CAMERAHEIGHT = %f;
    #declare CAMERAY = %f;
    #declare VIEWX = %f;
    #declare VIEWHEIGHT = %f;
    #declare VIEWY = %f;

    #declare CAMERAPOS = <CAMERAX, CAMERAHEIGHT, CAMERAY>;
    #declare CAMERALOOKAT = <VIEWX, CAMERAHEIGHT, VIEWY>;
    #declare FILENAME = "%s";
    #declare MAXMOUNTAIN = %f;
    #declare PANOANGLE = %f;
    #declare SCALEFACTOR = %f;

    #declare CAMERAFRONT  = vnormalize(CAMERAPOS - CAMERALOOKAT);
    #declare CAMERAFRONTX = CAMERAFRONT.x;
    #declare CAMERAFRONTY = CAMERAFRONT.y;
    #declare CAMERAFRONTZ = CAMERAFRONT.z;
    #declare DEPTHMIN = -1;
    #declare DEPTHMAX = 0.15;

    camera {
        cylinder 1
        location CAMERAPOS
        look_at  CAMERALOOKAT
        angle PANOANGLE
    }

    #declare clipped_scaled_gradient =
        function(x, y, z, gradx, grady, gradz, gradmin, gradmax) {
            clip(
            ((x * gradx + y * grady + z * gradz)
             - gradmin) / (gradmax - gradmin),
            0,1)
        }

    #declare thetexture = texture {
        pigment {
            function {
                clipped_scaled_gradient(
                    x, y, z, CAMERAFRONTX, CAMERAFRONTY,
                    CAMERAFRONTZ, DEPTHMIN, DEPTHMAX)
            }
            color_map {
                [0.0 color rgb <0,0,0>]
                [1 color rgb <1,1,1>]
            }
            translate CAMERALOOKAT
            }
            finish {
                ambient 1 diffuse 0 specular 0
            }
        }

    light_source { <0, 3000, 0> color <1,1,1> }

    height_field {
        png FILENAME
        texture { thetexture }
        scale <1,SCALEFACTOR,1>
    }
    ''' % (location_x, location_height, location_y,
           view_x, view_height, view_y,
           dem_file, max_height, panoramic_angle, height_field_scale_factor)
    return pov_text


def texture_pov(dem_file, raster_data, pov_settings):
    coordinates = raster_data[0]
    location_x, location_height, location_y, \
        view_x, view_height, view_y = coordinates
    max_height = raster_data[1][3]
    panoramic_angle = pov_settings[0]
    height_field_scale_factor = pov_settings[1]
    texture_path = pov_settings[2]
    tex_bounds = pov_settings[3]
    scale_x = tex_bounds.min_y[0]
    scale_y = tex_bounds.min_x[1]
    x_l = tex_bounds.max_y[0] - tex_bounds.min_y[0]
    print(x_l)
    pov_text = '''
    #version 3.8;
    #include "colors.inc"
    #include "math.inc"

    global_settings {
        assumed_gamma 1
    }

    #declare CAMERAX = %f;
    #declare CAMERAHEIGHT = %f;
    #declare CAMERAY = %f;
    #declare VIEWX = %f;
    #declare VIEWHEIGHT = %f;
    #declare VIEWY = %f;

    #declare CAMERAPOS = <CAMERAX, CAMERAHEIGHT, CAMERAY>;
    #declare CAMERALOOKAT = <VIEWX, CAMERAHEIGHT, VIEWY>;
    #declare FILENAME = "%s";
    #declare MAXMOUNTAIN = %f;
    #declare PANOANGLE = %f;
    #declare SCALEFACTOR = %f;
    #declare TEXTURE = "%s";
    #declare SKEW = <%f, %f, 0.0>;
    #declare SCALE = <%f, %f, 0.0>;
    camera {
        perspective
        location <0.5, 0.6, 0.5>
        look_at  <0.5, 0, 0.5>
        angle 100
    }

    sky_sphere {
        pigment {
            gradient y
            color_map {
                [0.4 color rgb<1 1 1>]
                [0.8 color rgb<0.1,0.25,0.75>]
                [1 color rgb<0.1,0.25,0.75>]
            }
            scale 2
            translate -1
        }
    }

    object{
        height_field {
            png FILENAME
            pigment {
            gradient y
            color_map {
                [0 color NewTan]
                [0.001 color CadetBlue]
                [0.01 color SkyBlue]
                [0.02 color Silver]
            }
        }
        finish { ambient 0.25 diffuse 1 specular 0.25 }
        scale <1, SCALEFACTOR, 1>
        }
        texture{
            pigment {
                image_map {
                    png TEXTURE
                    once
                }
                scale SCALE
                translate SKEW
            }
            rotate <90, 0, 0>
        }
    }

    ''' % (location_x, location_height, location_y,
           view_x, view_height, view_y,
           dem_file, max_height, panoramic_angle,
           height_field_scale_factor, texture_path,
           scale_x, scale_y, x_l, x_l)
    return pov_text


def color_gradient_pov(dem_file, raster_data, pov_settings, axis):
    coordinates = raster_data[0]
    location_x, location_height, location_y, \
        view_x, view_height, view_y = coordinates
    max_height = raster_data[1][3]
    panoramic_angle = pov_settings[0]
    height_field_scale_factor = pov_settings[1]
    pov_text = '''
    #version 3.8;
    #include "colors.inc"
    #include "math.inc"

    global_settings {
        assumed_gamma 1
    }

    #declare CAMERAX = %f;
    #declare CAMERAHEIGHT = %f;
    #declare CAMERAY = %f;
    #declare VIEWX = %f;
    #declare VIEWHEIGHT = %f;
    #declare VIEWY = %f;

    #declare CAMERAPOS = <CAMERAX, CAMERAHEIGHT, CAMERAY>;
    #declare CAMERALOOKAT = <VIEWX, CAMERAHEIGHT, VIEWY>;
    #declare FILENAME = "%s";
    #declare MAXMOUNTAIN = %f;
    #declare PANOANGLE = %f;
    #declare SCALEFACTOR = %f;

    camera {
        cylinder 1
        location CAMERAPOS
        look_at  CAMERALOOKAT
        angle PANOANGLE
    }

    background { color rgb <1, 1, 1> }
    height_field {
        png FILENAME
        pigment {
            gradient %s
            color_map {
                blend_mode 0
                [0 color rgb <0,0,0>] // west if x, south if z
                [1 color rgb <1,0,0>] // east if x, north if z
            }
        }
        scale <1,SCALEFACTOR,1>
        finish {ambient 1 diffuse 0 specular 0}
    }

    ''' % (location_x, location_height, location_y,
           view_x, view_height, view_y,
           dem_file, max_height, panoramic_angle, height_field_scale_factor,
           axis)
    return pov_text


def height_pov(dem_file, raster_data, pov_settings):
    coordinates = raster_data[0]
    location_x, location_height, location_y, \
        view_x, view_height, view_y = coordinates
    max_height = raster_data[1][3]
    panoramic_angle = pov_settings[0]
    height_field_scale_factor = pov_settings[1]

    pov_text = '''
    #version 3.8;
    #include "colors.inc"
    #include "math.inc"

    global_settings {
        assumed_gamma 1
        ambient_light 1.5
    }

    #declare CAMERAX = %f;
    #declare CAMERAHEIGHT = %f;
    #declare CAMERAY = %f;
    #declare VIEWX = %f;
    #declare VIEWHEIGHT = %f;
    #declare VIEWY = %f;

    #declare CAMERAPOS = <CAMERAX, CAMERAHEIGHT, CAMERAY>;
    #declare CAMERALOOKAT = <VIEWX, CAMERAHEIGHT, VIEWY>;
    #declare FILENAME = "%s";
    #declare MAXMOUNTAIN = %f;
    #declare PANOANGLE = %f;
    #declare SCALEFACTOR = %f;


    camera {
        cylinder 1
        location CAMERAPOS
        look_at  CAMERALOOKAT
        angle PANOANGLE
    }

    light_source { CAMERAPOS color White }

    height_field {
        png FILENAME
        pigment {
            gradient y
            color_map {
                [0.000000001 color BakersChoc]
                [MAXMOUNTAIN color White]
            }
        }
        finish { ambient 0.25 diffuse 1 specular 0.25 }
        scale <1,SCALEFACTOR,1>
    }

    plane {
        y, 0
        texture {
            pigment { color rgb < 0.3, 0.3, 0.7 > }
            normal { bumps 0.2 }
            finish {
                phong 1 reflection 1.0 ambient 0.2 diffuse 0.2 specular 1.0
            }
        }
    }

    sky_sphere {
        pigment {
            gradient y
            color_map {
                [0.4 color rgb<1 1 1>]
                [0.8 color rgb<0.1,0.25,0.75>]
                [1 color rgb<0.1,0.25,0.75>]
            }
            scale 2
            translate -1
        }
    }

    ''' % (location_x, location_height, location_y,
           view_x, view_height, view_y,
           dem_file, max_height, panoramic_angle, height_field_scale_factor)
    return pov_text


def debug_pov(dem_file, texture_path):
    pov_text = '''
    #version 3.8;
    #include "colors.inc"
    #include "math.inc"

    global_settings {
        assumed_gamma 2.2
    }

    #declare CAMERAPOS = <0.5, 0.6, 0.5>;
    #declare CAMERALOOKAT = <0.5, 0.0, 0.5>;
    #declare FILENAME = "%s";
    #declare TEXTURE = "%s";
    #declare SKEW = <0, 0, 0>;
    camera {
        perspective
        location CAMERAPOS
        look_at  CAMERALOOKAT
    }

    sky_sphere {
        pigment {
            gradient y
            color_map {
                [0.4 color rgb<1 1 1>]
                [0.8 color rgb<0.1,0.25,0.75>]
                [1 color rgb<0.1,0.25,0.75>]
            }
            scale 2
            translate -1
        }
    }

    object{
        height_field {
            png FILENAME
            pigment {
            gradient y
            color_map {
                [0.00000000000001 color BakersChoc]
                [0.01 color White]
            }
        }
        finish { ambient 0.25 diffuse 1 specular 0.25 }
        scale <1, SCALEFACTOR, 1>
        }
        texture{
            pigment {
                image_map {
                    png TEXTURE
                    once
                }
                scale <0.1, 0.1, 0.0>
                translate <0.73, 0.27, 0.0>
            }
            rotate <90, 0, 0>
        }
    }
    ''' % (dem_file, texture_path)
    return pov_text
