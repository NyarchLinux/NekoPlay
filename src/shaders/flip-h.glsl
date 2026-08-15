//!HOOK MAIN
//!BIND HOOKED
//!DESC Horizontal Flip

vec4 hook() {
    return HOOKED_tex(vec2(1.0 - HOOKED_pos.x, HOOKED_pos.y));
}