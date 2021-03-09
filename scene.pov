camera {
    cylinder 1

    location <0.344444, 0.010620, 0.5>
    look_at  <0.344444, 0.010620, 0.2>

    angle 360
}

light_source { <0.344444, 0.010620, 0.5> color <1,1,1> }

height_field {
    png "assets/demfile2.png"


    pigment {
        gradient x
        color_map {
            [ 0.5 color <1 1 1> ]
            [ 1 color <1 0.5 0.5> ]
        }
    }

    scale <1, 1, 1>
}