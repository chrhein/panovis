def pov_script(location_x, location_height, location_y,
        view_x, view_height, view_y,
        demfile):
    povfiletext = '''
    #include "colors.inc"
    #include "math.inc"

    global_settings {
        assumed_gamma 1
    }

    #declare CAMERALOOKAT = <%f, %f, %f>;
    #declare CAMERAPOS = <%f, %f, %f>;
    #declare FILENAME = "%s";

    #declare CAMERAFRONT  = vnormalize(CAMERALOOKAT - CAMERAPOS);
    #declare CAMERAFRONTX = CAMERAFRONT.x;
    #declare CAMERAFRONTY = CAMERAFRONT.y;
    #declare CAMERAFRONTZ = CAMERAFRONT.z;
    #declare DEPTHMIN = 0.01;
    #declare DEPTHMAX = 0.2;

    camera {
        cylinder 1
        location CAMERALOOKAT
        look_at  CAMERAPOS
        angle 160
    }

    #declare clipped_scaled_gradient =
        function(x, y, z, gradx, grady, gradz, gradmin, gradmax) {
            clip(
            ((x * gradx + y * grady + z * gradz) - gradmin) / (gradmax - gradmin),
            0,1)
        }
    #declare thetexture = texture {
        pigment {
            function {
            clipped_scaled_gradient(
                x, y, z, CAMERAFRONTX, CAMERAFRONTY, CAMERAFRONTZ, DEPTHMIN, DEPTHMAX)
            }
            color_map {
            [0 color rgb <0,0,0>]
            [1 color rgb <1,1,1>]

            }
            translate CAMERAPOS
        }
        finish { ambient 1 diffuse 0 specular 0 }
        }
    
    light_source { CAMERALOOKAT color White }
    
    union {
        height_field { 
            png FILENAME
        }
        texture { thetexture }
    }


    ''' % (location_x, location_height, location_y,
        view_x, view_height, view_y,
        demfile)
    return povfiletext
