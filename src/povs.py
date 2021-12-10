def primary_pov(
    dem_file,
    raster_data,
    texture_path="",
    tex_bounds=None,
    mode="height",
):
    coordinates = raster_data[0]
    location_x, location_height, location_y, view_x, _, view_y = coordinates
    ds_raster, _, max_height = raster_data[1]
    y_axis_scaling = ds_raster.width / ds_raster.height

    if mode == "texture" or mode == "route" or mode == "gradient":
        if mode == "gradient":
            skew_x, skew_y, x_l, y_l = 0, 0, 0, 0
        else:
            if not tex_bounds:
                raise Exception("No texture bounds given")
            skew_y = tex_bounds.min_x[1]
            skew_x = tex_bounds.min_y[0]
            x_l = tex_bounds.max_x[1] - tex_bounds.min_x[1]
            y_l = tex_bounds.max_y[0] - tex_bounds.min_y[0]
    else:
        texture_path = ""
        skew_x, skew_y, x_l, y_l = 0, 0, 0, 0

    pov_text = """
    #version 3.8;
    #include "colors.inc"
    #include "math.inc"

    #declare CAMERAX = %f;
    #declare CAMERAHEIGHT = %f;
    #declare CAMERAY = %f;
    #declare VIEWX = %f;
    #declare VIEWY = %f;

    #declare FILENAME = "%s";
    #declare YSCALE = %f;
    #declare MAXMOUNTAIN = %f;
    #declare TEXTURE = "%s";
    #declare SKEW = <%f, %f, 0.0>;
    #declare SCALE = <%f, %f, 0.0>;
    #declare MODE = "%s";

    #declare HEIGHT = CAMERAHEIGHT;

    #declare CAMERAPOS = <CAMERAX, HEIGHT, CAMERAY>;
    #declare CAMERALOOKAT = <VIEWX, HEIGHT, VIEWY>;

    #if (MODE="depth")
    #declare CAMERAFRONT  = vnormalize(CAMERAPOS - CAMERALOOKAT);
    #declare CAMERAFRONTX = CAMERAFRONT.x;
    #declare CAMERAFRONTY = CAMERAFRONT.y;
    #declare CAMERAFRONTZ = CAMERAFRONT.z;
    #declare DEPTHMIN = -1;
    #declare DEPTHMAX = 0;

    #declare clipped_scaled_gradient =
        function(x, y, z, gradx, grady, gradz, gradmin, gradmax) {
            clip(
            ((x * gradx + y * grady + z * gradz)
             - gradmin) / (gradmax - gradmin),
            0,1)
        }

    #declare DEPTHTEXTURE = texture {
            pigment {
                function {
                    clipped_scaled_gradient(
                        x, y, z, CAMERAFRONTX, CAMERAFRONTY,
                        CAMERAFRONTZ, DEPTHMIN, DEPTHMAX)
                }
                color_map {
                    [0 color Black]
                    [1 color rgb White]
                }
            }
            finish {
                ambient 0 diffuse 0 specular 0 emission 1
            }
        }
    #end

    #if (MODE="gradient")
    global_settings {
        assumed_gamma 1
    }
    #else
    global_settings {
        assumed_gamma 1
        ambient_light 1.5
    }
    #end

    camera {
        cylinder 1
        location CAMERAPOS
        look_at CAMERALOOKAT
        angle 360
    }

    light_source { CAMERAPOS color White }

    #if (MODE="texture" | MODE="height")
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
    #end
    merge {
        object{
            height_field {
                png FILENAME
                #if (MODE="texture" | MODE="height")
                pigment {
                    gradient y
                    color_map {
                        [0.0000000000000000000001 color BakersChoc]
                        [MAXMOUNTAIN color White]
                    }
                }
                #else
                pigment { color rgb<0, 0, 0> }
                #end
                finish { ambient 0.2 diffuse 0.55 specular 0.15 }
            }
            #if (MODE="texture" | MODE="route")
                texture{
                    pigment {
                        image_map {
                            png TEXTURE
                            once
                        }
                        scale SCALE
                        translate SKEW
                    }
                    finish { ambient 1 diffuse 0 specular 0 }
                    rotate <90, 0, 0>
                }
            #end
            #if (MODE="depth")
                texture {
                    DEPTHTEXTURE
                    translate CAMERAPOS
                }
            #end
            #if (MODE="gradient")
                texture{
                    pigment {
                        image_map {
                            png TEXTURE
                            once
                        }
                    }
                    finish { ambient 1 diffuse 0 specular 0 }
                    rotate <90, 0, 0>
                }
            #end
        }
        #if (MODE="texture" | MODE="height")
        plane {
            y, 0.00000000000001
            texture {
                #if (MODE="no-going-to-use-this")
                DEPTHTEXTURE
                translate CAMERAPOS
                #else
                pigment { color rgb<0.1,0.25,0.75> }
                finish {
                    reflection 0 ambient 1 diffuse 0 specular 0
                }
                #end
            }
        }
        #end
        scale <1, YSCALE + 0.075, 1>
    }
    """ % (
        location_x,
        location_height,
        location_y,
        view_x,
        view_y,
        dem_file,
        y_axis_scaling,
        max_height,
        texture_path,
        skew_x,
        skew_y,
        y_l,
        x_l,
        mode,
    )
    return pov_text


def color_gradient_pov(dem_file, raster_data, pov_settings, axis):
    coordinates = raster_data[0]
    location_x, location_height, location_y, view_x, view_height, view_y = coordinates
    max_height = raster_data[1][3]
    panoramic_angle = pov_settings[0]
    height_field_scale_factor = pov_settings[1]
    pov_text = """
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

    """ % (
        location_x,
        location_height,
        location_y,
        view_x,
        view_height,
        view_y,
        dem_file,
        max_height,
        panoramic_angle,
        height_field_scale_factor,
        axis,
    )
    return pov_text


def debug_pov(dem_file, texture_path, tex_bounds, mh):
    scale_y = tex_bounds.min_x[1]
    scale_x = tex_bounds.min_y[0]
    x_l = tex_bounds.max_x[1] - tex_bounds.min_x[1]
    y_l = tex_bounds.max_y[0] - tex_bounds.min_y[0]

    pov_text = """
    #version 3.8;
    #include "colors.inc"
    #include "math.inc"

    global_settings {
        assumed_gamma 2.2
        hf_gray_16
    }

    #declare CAMERAPOS = <0.5, 1.25, 0.5>;
    #declare CAMERALOOKAT = <0.5, 0.0, 0.5>;
    #declare FILENAME = "%s";
    #declare TEXTURE = "%s";
    #declare SKEW = <%f, %f, 0.0>;
    #declare SCALE = <%f, %f, 0.0>;
    #declare MAXMOUNTAIN = %f;

    camera {
        perspective
        location CAMERAPOS
        look_at  CAMERALOOKAT
        angle 45
    }

    light_source {
        <-2, 100, 0.5> color rgb<1, 1, 1>
        spotlight
        falloff 0
        point_at <2, 0, 0.5>
    }

    object{
        height_field {
            png FILENAME
            pigment {
                gradient y
                color_map {
                    [MAXMOUNTAIN/1000 color rgb<0.62, 0.66, 0.46>]
                    [MAXMOUNTAIN/100 color rgb<0.79, 0.63, 0.48>]
                    [MAXMOUNTAIN/50 color rgb<0.74, 0.69, 0.62>]
                    [MAXMOUNTAIN/25 color rgb<0.678, 0.616, 0.643>]
                    [MAXMOUNTAIN/12.5 color rgb<0.851, 0.773, 0.804>]
                    [MAXMOUNTAIN/5 color rgb<1, 1, 1>]
                }
            }
            finish { reflection 0 ambient 0.35 diffuse 0.5 specular 0.25 }
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
            finish { ambient 0.75 diffuse 0.1 specular 0.1 }
        }
    }

    plane {
        y, 0.000000001
        texture {
            pigment { color rgb<0.74, 0.69, 0.62> }
            finish {
                reflection 0 ambient 1 diffuse 0 specular 0
            }
        }
    }


    """ % (
        dem_file,
        texture_path,
        scale_x,
        scale_y,
        y_l,
        x_l,
        mh,
    )
    return pov_text
