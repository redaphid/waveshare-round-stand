// Desk stands for Waveshare round display boards.
// Set `variant` below, then render. Mirrors build_stands.py exactly.
//
// Print flat on the base. No supports, no overhangs.
// Dimensions come from Waveshare's own outline drawings -- see reference/.

variant = "1.46-glass";   // "1.28" | "1.46-glass" | "1.46-bare"

//    board_d  thick   gap   lean depth base_d base_h fh bh  rh  W   slot_y nw  nf
P =
  variant=="1.28"      ? [36.50, 1.60, 2.40,20, 5.0, 27.0, 12.0, 3, 4, 2.0, 26, 12.0, 13, 2.0] :
  variant=="1.46-glass"? [44.77,12.30,13.10,20, 8.0, 36.0, 16.0, 4, 5, 2.5, 30, 16.0, 14, 2.0] :
  variant=="1.46-bare" ? [42.58,10.65,11.45,20, 8.0, 35.0, 16.0, 4, 5, 2.5, 29, 15.5, 14, 2.0] :
  undef;

board_d = P[0];  thick   = P[1];  gap        = P[2];  lean   = P[3];
depth   = P[4];  base_d  = P[5];  base_h     = P[6];  front_h= P[7];
back_h  = P[8];  ridge_half=P[9]; width      = P[10]; slot_y = P[11];
notch_w = P[12]; notch_floor = P[13];

eps = 0.01;

// horizontal offset from the groove centreline to a wall at z = base_h
wall_off = sin(lean)*(gap/2)*tan(lean) + cos(lean)*(gap/2);

module wedge() {
    rotate([90, 0, 90])
    linear_extrude(height = width)
        polygon([
            [0, 0], [base_d, 0], [base_d, back_h],
            [slot_y + wall_off + ridge_half, base_h],
            [slot_y - wall_off - ridge_half, base_h],
            [0, front_h]
        ]);
}

// the groove the board sits in
module groove() {
    translate([-eps, slot_y, base_h])
        rotate([-lean, 0, 0])
            translate([0, -gap/2, -depth])
                cube([width + 2*eps, gap, depth + base_h]);
}

// cable notch: straight through the ridge, front to back, so a USB-C lead
// can run through the stand instead of over it
module notch() {
    translate([(width - notch_w)/2, -eps, notch_floor])
        cube([notch_w, base_d + 2*eps, base_h - notch_floor + eps]);
}

difference() {
    wedge();
    groove();
    notch();
}

// Reference only -- the board in place. Uncomment to check clearances.
// %translate([width/2, slot_y - sin(lean)*depth, base_h - cos(lean)*depth])
//     rotate([-lean, 0, 0])
//         translate([0, 0, board_d/2])
//             rotate([0, 90, 0])
//                 cylinder(h = thick, d = board_d, center = true, $fn = 160);
