#version 330
// Dos almas: una historia de amor abstracta (el DJ, 2026-10-27). Se conocen, vuelan juntas, se
// separan, una se apaga y se aleja, la otra la cura, y al final se separan brillando las dos.
// La historia la mueve Python (posicion, luz y velocidad de cada alma); aca solo se dibuja.
// uLook: 0 = dos luces sobre el mar de noche (gramatica de marea), 1 = en el cielo con nubes y
// estela, 2 = nubes de particulas sobre negro.

uniform vec2 uRes;
uniform float uTime;
uniform int uLook;
uniform vec2 uPosA;   // en unidades de alto de pantalla, (0,0) al centro
uniform vec2 uPosB;
uniform vec2 uVelA;   // hacia donde vuela: la estela sale para el otro lado
uniform vec2 uVelB;
uniform float uLuzA;  // 0 apagada, 1 plena
uniform float uLuzB;
uniform vec2 uCam;    // cuanto se corrio el cielo: las almas quedan en cuadro y el fondo pasa

out vec4 fragColor;

const vec3 CALIDA = vec3(1.00, 0.56, 0.22);   // el naranja de la marca
const vec3 FRIA = vec3(0.78, 0.86, 1.00);
const float HORIZONTE = -0.14;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float hash1(float n) { return fract(sin(n * 91.345) * 47453.5453); }

float ruido(vec2 p) {
    vec2 i = floor(p), f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

float fbm(vec2 p) {
    float v = 0.0, a = 0.5;
    for (int i = 0; i < 5; i++) { v += a * ruido(p); p *= 2.03; a *= 0.5; }
    return v;
}

// el alma: un nucleo blanco chico y un halo de su color. Apagada queda un punto gris tenue.
vec3 alma(vec2 p, vec2 c, vec3 col, float luz) {
    float d = length(p - c);
    float nucleo = exp(-d * d * 2600.0);
    float halo = exp(-d * d * 160.0) * 0.30 + 0.004 / (d + 0.02) * 0.25;
    vec3 gris = vec3(0.35, 0.36, 0.40);
    return mix(gris * 0.25, col, luz) * halo * (0.25 + luz) + mix(gris, vec3(1.0), luz) * nucleo * (0.35 + 0.65 * luz);
}

// estela detras del alma, mas larga cuanto mas rapido vuela
vec3 estela(vec2 p, vec2 c, vec2 vel, vec3 col, float luz) {
    float v = length(vel);
    if (v < 1e-4) return vec3(0.0);
    vec2 dir = -vel / v;
    float largo = clamp(v * 1.6, 0.0, 0.45);
    float t = clamp(dot(p - c, dir) / max(largo, 1e-4), 0.0, 1.0);
    vec2 q = c + dir * t * largo;
    float d = length(p - q);
    float ancho = mix(0.006, 0.0015, t);
    return col * luz * exp(-d * d / (ancho * ancho)) * (1.0 - t) * 0.55;
}

vec3 cielo_noche(vec2 p) {
    vec3 c = mix(vec3(0.050, 0.060, 0.120), vec3(0.012, 0.016, 0.040), smoothstep(HORIZONTE, 0.5, p.y));
    c += CALIDA * 0.05 * exp(-abs(p.y - HORIZONTE) * 14.0);    // el ultimo resto del atardecer
    vec2 g = floor(p * 260.0);
    float e = step(0.9965, hash(g)) * (0.5 + 0.5 * sin(uTime * 1.3 + hash(g + 3.0) * 6.28));
    return c + vec3(e) * 0.55 * smoothstep(HORIZONTE, 0.1, p.y);
}

vec3 luces(vec2 p) {
    return alma(p, uPosA, CALIDA, uLuzA) + alma(p, uPosB, FRIA, uLuzB);
}

vec3 look_mar(vec2 p) {
    if (p.y > HORIZONTE) return cielo_noche(p) + luces(p);
    // el agua: ondas que se mueven lento y el reflejo de las dos luces, partido por las ondas
    float prof = HORIZONTE - p.y;
    float onda = fbm(vec2(p.x * 6.0, p.y * 38.0 / (prof + 0.05)) + vec2(uTime * 0.05, uTime * 0.12));
    vec2 r = vec2(p.x + (onda - 0.5) * 0.05 * (prof * 4.0 + 0.2), 2.0 * HORIZONTE - p.y);
    vec3 reflejo = luces(r) * 0.55 * smoothstep(0.35, 0.75, onda);
    vec3 agua = vec3(0.010, 0.016, 0.034) + vec3(0.03, 0.04, 0.07) * onda * exp(-prof * 3.0);
    return agua + reflejo + cielo_noche(r) * 0.18;
}

vec3 look_cielo(vec2 p) {
    vec3 c = cielo_noche(p + uCam * 0.35 + vec2(0.0, 0.3)) * 0.8;      // las estrellas, lejos, pasan lento
    float nube = smoothstep(0.42, 0.85, fbm((p + uCam) * 2.4 + vec2(uTime * 0.01, 0.0)));
    // las nubes se encienden con la luz de las almas que pasan cerca
    vec3 ilum = CALIDA * uLuzA * exp(-length(p - uPosA) * 3.5) + FRIA * uLuzB * exp(-length(p - uPosB) * 3.5);
    c = mix(c, vec3(0.05, 0.06, 0.10) + ilum * 0.9, nube * 0.85);
    return c + estela(p, uPosA, uVelA, CALIDA, uLuzA) + estela(p, uPosB, uVelB, FRIA, uLuzB) + luces(p);
}

vec3 particulas(vec2 p, vec2 c, vec3 col, float luz, float semilla) {
    vec3 s = vec3(0.0);
    for (int i = 0; i < 70; i++) {
        float k = float(i) + semilla;
        float ang = hash1(k) * 6.2832 + uTime * (0.15 + hash1(k + 1.0) * 0.45);
        float rad = (0.012 + pow(hash1(k + 2.0), 1.6) * 0.09) * (0.45 + 0.75 * luz);
        vec2 q = c + rad * vec2(cos(ang), sin(ang) * 0.8);
        float d2 = dot(p - q, p - q);
        s += col * (exp(-d2 * 12000.0) * 0.9 + exp(-d2 * 700.0) * 0.04);
    }
    return s * (0.15 + 0.85 * luz);
}

vec3 look_particulas(vec2 p) {
    vec3 c = vec3(0.004, 0.004, 0.008);
    c += particulas(p, uPosA, CALIDA, uLuzA, 0.0) + particulas(p, uPosB, FRIA, uLuzB, 500.0);
    return c + luces(p) * 0.6;
}

void main() {
    vec2 p = (gl_FragCoord.xy - 0.5 * uRes) / uRes.y;
    vec3 c = uLook == 0 ? look_mar(p) : (uLook == 1 ? look_cielo(p) : look_particulas(p));
    // los colores ya estan pensados en pantalla: sin gamma, que levantaba la noche a gris
    c = 1.0 - exp(-c * 1.6);                      // sin quemar: las luces llegan a blanco suave
    c *= 1.0 - 0.35 * dot(p * 0.9, p * 0.9);      // vineta leve
    fragColor = vec4(c, 1.0);
}
