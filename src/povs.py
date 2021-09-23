def depth_pov(location_x, location_height, location_y,
              view_x, view_height, view_y,
              dem_file):
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
    #declare CAMERALOOKAT = <VIEWX, VIEWHEIGHT, VIEWY>;
    #declare FILENAME = "%s";

    #declare CAMERAFRONT  = vnormalize(CAMERAPOS - CAMERALOOKAT);
    #declare CAMERAFRONTX = CAMERAFRONT.x;
    #declare CAMERAFRONTY = CAMERAFRONT.y;
    #declare CAMERAFRONTZ = CAMERAFRONT.z;
    #declare DEPTHMIN = -1;
    #declare DEPTHMAX = 0.15;

    camera {
        cylinder 1
        angle 220
        location CAMERAPOS
        look_at  CAMERALOOKAT
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

    light_source { CAMERAPOS color White }

    height_field {
        png FILENAME
        texture { thetexture }

    }
    ''' % (location_x, location_height, location_y,
           view_x, view_height, view_y,
           dem_file)
    return pov_text


def color_gradient_pov(location_x, location_height, location_y,
                       view_x, view_height, view_y,
                       dem_file, axis):
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
    #declare CAMERALOOKAT = <VIEWX, VIEWHEIGHT, VIEWY>;
    #declare FILENAME = "%s";

    camera {
        cylinder 1
        angle 220
        location CAMERAPOS
        look_at  CAMERALOOKAT
    }
    background { color rgb <1, 1, 1> }
    height_field {
        png FILENAME
        pigment {
            gradient %s
            color_map {
                [0 color rgb <0,0,0>] // west if x, south if z
                [1 color rgb <1,0,0>] // east if x, north if z
              }
        }
        finish {ambient 1 diffuse 0 specular 0}

    }
    ''' % (location_x, location_height, location_y,
           view_x, view_height, view_y,
           dem_file, axis)
    return pov_text


def height_pov(location_x, location_height, location_y,
               view_x, view_height, view_y,
               dem_file, max_height, panoramic_angle,
               height_field_scale_factor):
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
