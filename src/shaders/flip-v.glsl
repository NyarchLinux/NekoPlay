//!HOOK MAIN
//!BIND HOOKED
//!DESC Vertical Flip

vec4 hook() {
    return HOOKED_tex(vec2(HOOKED_pos.x, 1.0 - HOOKED_pos.y));
}