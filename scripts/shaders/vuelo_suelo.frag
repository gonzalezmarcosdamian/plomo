#version 330
// La altura del suelo en cada punto que va a recorrer la camara de vuelo.frag, con el MISMO
// terreno (vuelo_terreno.glsl) y las mismas octavas con que se dibuja. Cada texel de uPuntos es
// un punto: (x, z, paisaje), con la semilla del tema ya sumada.

#include "vuelo_terreno.glsl"

uniform sampler2D uPuntos;
out float alto;

void main() {
    vec4 d = texelFetch(uPuntos, ivec2(gl_FragCoord.xy), 0);
    alto = altura(int(d.z + 0.5), d.xy, 5);
}
