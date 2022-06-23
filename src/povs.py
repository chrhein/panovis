def primary_pov(
    dem_file,
    raster_data,
    texture_path="",
    tex_bounds=None,
    mode="height",
    fov=None,
):
    coordinates = raster_data[0]
    location_x, location_height, location_y, view_x, _, view_y = coordinates
    _, max_height = raster_data[1]
    y_axis_scaling = 2.0

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

    """ if dem_file.endswith(".tif"):
        tmp_dem = '/tmp/dem.png'
        call(['gdal_translate', '-ot', 'UInt16',
              '-of', 'PNG', dem_file, tmp_dem])
        dem_file = tmp_dem """

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
        max_trace_level 1
    }
    #else
    global_settings {
        assumed_gamma 1
        ambient_light 1.5
        max_trace_level 1
    }
    #end

    camera {
        spherical
        angle 360 180
        location CAMERAPOS
        look_at CAMERALOOKAT
    }

    background { rgb <0, 0, 0> }


    #if (MODE="gradient")
    light_source { <0.5, 1, 0.5> color White }
    #else
    light_source { CAMERAPOS color White }
    #end


    #if (MODE="texture" | MODE="height")
        sky_sphere {
            pigment {
                gradient y
                color_map {
                    [0.25 color rgb<0.95, 0.98, 0.99>]
                    [0.7 color rgb<0.54, 0.76, 0.85>]
                    [1 color rgb<0.23,0.60,0.74>]
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
                water_level 0
                #if (MODE="texture" | MODE="height")
                pigment {
                    gradient y
                    color_map {
                        [0.0001 color rgb<0.01, 0.40, 0.26>] // darthmouth green
                        [0.0035 color rgb<0.89, 0.79, 0.45>] // chenin
                        [0.0070 color rgb<0.78, 0.58, 0.27>] // tussock
                        [0.0105 color rgb<0.62, 0.16, 0.00>] // totem pole
                        [0.0140 color rgb<0.60, 0.60, 0.60>] // aluminum
                        [0.0200 color rgb<0.78, 0.58, 0.27>] // tussock
                        [0.0235 color rgb<0.62, 0.16, 0.00>] // totem pole
                        [0.0270 color rgb<0.60, 0.60, 0.60>] // aluminum
                        [MAXMOUNTAIN color White]
                    }
                }
                #else
                pigment { color rgb<0, 0, 0> }
                #end
                translate <0, 0.00025, 0>
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
            y, 0.0002525
            texture {
                pigment { color rgb<0.16, 0.41, 0.52> }

                finish {
                    reflection 0 ambient 1 diffuse 0 specular 0
                }
            }
        }
        #end
        scale <1, YSCALE, 1>
    }
    """ % (
        location_x,
        location_height,
        location_y,
        view_x,
        view_y,
        dem_file.replace('.tif', '.png'),
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


def debug_pov(dem_file, texture_path, tex_bounds, mh):
    with_route_texture = bool(texture_path and tex_bounds)
    if with_route_texture:
        scale_y = tex_bounds.min_x[1]
        scale_x = tex_bounds.min_y[0]
        x_l = tex_bounds.max_x[1] - tex_bounds.min_x[1]
        y_l = tex_bounds.max_y[0] - tex_bounds.min_y[0]
    else:
        scale_y = 0
        scale_x = 0
        x_l = 0
        y_l = 0

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
        #if (TEXTURE!="")
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
        #end
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
