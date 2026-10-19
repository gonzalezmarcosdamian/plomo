// El terreno de vuelo.frag, sin uniforms: lo usan la render y vuelo_suelo.frag, que mide
// la altura del suelo para que la camara se calcule antes y vuele suave (video_animar.suelos).
// Si se toca un paisaje aca, la camara lo sigue sola.

const mat2 GIRO = mat2(1.6, -1.2, 1.2, 1.6);

float hash(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

// ruido de valor con sus derivadas: las derivadas son las que dan la erosion de las montanas
vec3 ruidoD(vec2 x) {
    vec2 i = floor(x), f = fract(x);
    vec2 u = f * f * f * (f * (f * 6.0 - 15.0) + 10.0);
    vec2 du = 30.0 * f * f * (f * (f - 2.0) + 1.0);
    float a = hash(i), b = hash(i + vec2(1, 0)), c = hash(i + vec2(0, 1)), d = hash(i + vec2(1, 1));
    float k1 = b - a, k2 = c - a, k3 = a - b - c + d;
    return vec3(a + k1 * u.x + k2 * u.y + k3 * u.x * u.y, du * (vec2(k1, k2) + k3 * u.yx));
}

float montana(vec2 p, int oct) {
    float a = 0.0, b = 1.0;
    vec2 d = vec2(0.0);
    for (int i = 0; i < 9; i++) {
        if (i >= oct) break;
        vec3 n = ruidoD(p);
        d += n.yz;
        a += b * n.x / (1.0 + dot(d, d));
        b *= 0.5;
        p = GIRO * p;
    }
    return a;
}

float dunas(vec2 p, int oct) {
    float h = 0.0, a = 0.55;
    for (int i = 0; i < 6; i++) {
        if (i >= oct) break;
        float n = 1.0 - abs(2.0 * ruidoD(p).x - 1.0);
        h += a * n * n;
        a *= 0.42;
        p = GIRO * p + 11.0;
    }
    return h;
}

// canon: mesetas de roca con paredes a pique. Las terrazas salen de cortar la montana en
// escalones que suben rapido y despues quedan planos
float meseta(vec2 p, int oct) {
    float s = 7.0 * montana(p, oct) * 1.2;
    return (floor(s) + smoothstep(0.0, 0.18, fract(s))) / 1.2;
}

float crudo(int b, vec2 q, int oct) {
    if (b == 0) return 10.0 * montana(q * 0.022, oct) - 1.5;
    if (b == 1) return 6.0 * montana(q * 0.03 + 3.7, oct) - 4.0;
    if (b == 2) return 2.4 * dunas(q * 0.13, oct);
    return meseta(q * 0.02 + 9.1, oct) - 1.0;
}

// en la costa el mar es el piso, en 0
float altura(int b, vec2 q, int oct) {
    float h = crudo(b, q, oct);
    return b == 1 ? max(h, 0.0) : h;
}
