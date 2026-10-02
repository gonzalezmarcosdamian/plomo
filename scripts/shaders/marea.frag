#version 330
// Marea: el mar de noche con la luna saliendo. El look de la Session 02.
// La luna arranca naranja sobre el horizonte (el naranja de la marca) y a lo largo del set
// sube y se pone plateada. El camino de luz en el agua es el bajo; su brillo, el cuerpo;
// los destellos, los hats. Nada de flashes: el bombo respira, no parpadea.
// No usa la paleta del telefono: la noche sobre el mar tiene sus propios colores.

uniform vec2 uRes;
uniform float uTime;
uniform float uProgreso;  // 0 al empezar el set, 1 al terminar
uniform float uBombo;
uniform float uBajo;
uniform float uCuerpo;
uniform float uAire;
uniform float uChispa;
uniform vec2 uDeriva;
uniform float uAngulo;
uniform sampler2D uTexto;
uniform float uTextoAlfa;

out vec4 fragColor;

const vec3 NARANJA = vec3(1.00, 0.50, 0.20);
const vec3 CREMA = vec3(1.00, 0.86, 0.66);   // de naranja a plata directo pasaba por rosado
const vec3 PLATA = vec3(0.90, 0.93, 1.00);
const vec3 NOCHE_ARRIBA = vec3(0.004, 0.008, 0.024);
const vec3 NOCHE_HORIZONTE = vec3(0.028, 0.046, 0.090);
const vec3 MAR = vec3(0.003, 0.010, 0.022);
const float HORIZONTE = 0.58;   // desde arriba, en alturas de pantalla

float hash(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

float ruido(vec2 p) {
    vec2 i = floor(p), f = fract(p);
    vec2 u = f * f * f * (f * (f * 6.0 - 15.0) + 10.0);
    float a = hash(i), b = hash(i + vec2(1, 0)), c = hash(i + vec2(0, 1)), d = hash(i + vec2(1, 1));
    return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

// las octavas altas se escalan con el aire: sin agudos, sin detalle fino
float fbm(vec2 p, float detalle, int octavas) {
    float v = 0.0, a = 0.5;
    mat2 r = mat2(0.8, 0.6, -0.6, 0.8);
    for (int i = 0; i < 6; i++) {
        if (i >= octavas) break;
        float w = i < 2 ? 1.0 : detalle;
        v += a * w * ruido(p);
        p = r * p * 2.02 + 17.0;
        a *= 0.5;
    }
    return v;
}

vec3 cielo(vec2 s, vec2 luna, float radio, vec3 colLuna, float energia, float respira, float detalle) {
    float alto = clamp((HORIZONTE - s.y) / HORIZONTE, 0.0, 1.0);   // 0 en el horizonte, 1 arriba
    vec3 col = mix(NOCHE_HORIZONTE, NOCHE_ARRIBA, pow(alto, 0.6));
    float d = length(s - luna);

    // halo: el bajo lo abre, el cuerpo lo enciende
    float halo = exp(-d / (0.09 + 0.04 * uBajo)) * 0.50 + exp(-d / 0.45) * 0.18;
    col += colLuna * halo * energia * respira * 0.55;

    // nubes finas y estiradas, que corren con el viento de cada tema
    vec2 viento = vec2(cos(uAngulo), sin(uAngulo));
    vec2 q = vec2(s.x * 0.8, s.y * 3.2) + uDeriva + viento * uTime * 0.006;
    vec2 w = vec2(fbm(q * 0.9 + 3.1, detalle, 4), fbm(q * 0.9 + 7.4, detalle, 4));
    float nube = smoothstep(0.42, 0.80, fbm(q * 1.4 + 0.7 * w, detalle, 5)) * (1.0 - 0.6 * alto);
    float cerca = exp(-d / 0.28);
    col = mix(col, col * 0.5 + colLuna * cerca * 0.30 * energia, nube * 0.8);

    // estrellas: pocas cerca de la luna y del horizonte; titilan con los hats
    float celda = 1.0 / 110.0;
    vec2 c = floor(s / celda);
    float r = hash(c + 3.7);
    float hay = step(0.965, r) * smoothstep(0.05, 0.35, alto) * smoothstep(0.10, 0.35, d) * (1.0 - nube);
    vec2 centro = (c + 0.5 + 0.35 * (vec2(hash(c + 9.1), hash(c + 2.3)) - 0.5)) * celda;
    float punto = exp(-dot(s - centro, s - centro) / (celda * celda * 0.012));
    float titila = 0.5 + 0.5 * mix(1.0, 0.5 + 0.5 * sin(uTime * (2.0 + 3.0 * r) + r * 40.0), uChispa);
    col += vec3(0.85, 0.90, 1.0) * hay * punto * titila * 0.7;

    // el disco, con manchas y borde suave; las nubes lo tapan a medias
    float disco = 1.0 - smoothstep(radio - 0.0025, radio + 0.0025, d);
    float manchas = 0.86 + 0.14 * fbm((s - luna) * 18.0 + 4.0, 1.0, 4);
    col = mix(col, colLuna * manchas * (1.25 + 0.15 * uCuerpo), disco * (1.0 - 0.7 * nube));
    return col;
}

vec3 mar(vec2 s, vec2 luna, float radio, vec3 colLuna, float energia, float respira, float detalle) {
    // perspectiva de un plano: a la distancia dy del horizonte le toca la profundidad 1/dy
    float dy = s.y - HORIZONTE;
    float z = 1.0 / (dy + 0.004);
    vec2 plano = vec2((s.x - luna.x) * z, z);
    float lejos = smoothstep(0.0, 0.06, dy);     // contra el horizonte el detalle se pierde
    vec2 viento = vec2(cos(uAngulo), sin(uAngulo));
    vec2 flujo = viento * uTime * 0.15 + 2.0 * uDeriva;

    // olas: crestas largas en horizontal, que vienen hacia uno (con menos frecuencia, cerca
    // de la camara quedaban tres franjas anchas en vez de un camino de reflejos)
    float olas = fbm(vec2(plano.x * 0.45, plano.y * 4.0) + flujo + vec2(0.0, uTime * 0.6),
                     detalle * lejos + 0.1, 5);
    vec3 col = mix(NOCHE_HORIZONTE * 0.8, MAR, smoothstep(0.0, 0.25, dy)) * (0.75 + 0.5 * olas);

    // el camino de la luna: angosto en el horizonte, ancho cerca; el bajo lo abre
    float ancho = 0.015 + radio * 0.6 + dy * (0.50 + 0.45 * uBajo);
    float columna = exp(-pow((s.x - luna.x) / ancho, 2.0));
    float cresta = smoothstep(0.52 - 0.08 * uBajo, 0.86, olas);
    col += colLuna * columna * cresta * (0.35 + 0.65 * smoothstep(0.0, 0.03, dy)) * energia * respira * 1.1;
    col += colLuna * columna * 0.06 * energia * (1.0 - smoothstep(0.0, 0.4, dy));

    // destellos sobre el camino: cada uno se enciende y se apaga a su ritmo, mas con los hats
    float celda = 1.0 / 170.0;
    vec2 c = floor(s / celda);
    float r = hash(c + 5.3);
    vec2 centro = (c + 0.5 + 0.3 * (vec2(hash(c + 1.7), hash(c + 8.2)) - 0.5)) * celda;
    float punto = exp(-dot(s - centro, s - centro) / (celda * celda * 0.03));
    float pulso = pow(max(0.0, sin(uTime * (1.5 + 3.5 * r) + r * 60.0)), 10.0);
    float hay = step(0.80, r) * columna * cresta * lejos;
    col += colLuna * hay * punto * pulso * (0.25 + 0.75 * uChispa) * energia * 1.6;
    return col;
}

void main() {
    // la fila 0 del framebuffer es la de ARRIBA del video (ver atardecer.frag): y crece hacia abajo
    vec2 frag = gl_FragCoord.xy;
    vec2 uv = frag / uRes;
    vec2 s = vec2(uv.x * uRes.x / uRes.y, uv.y);   // en alturas de pantalla
    vec2 p = (frag - 0.5 * uRes) / uRes.y;

    // la luna sube a lo largo del set y se le va el naranja
    float sube = smoothstep(0.0, 1.0, uProgreso);
    vec2 luna = vec2(0.60 * uRes.x / uRes.y, HORIZONTE - 0.035 - 0.26 * sube);
    float radio = 0.050 - 0.008 * sube;
    vec3 colLuna = mix(mix(NARANJA, CREMA, smoothstep(0.0, 0.45, sube)), PLATA, smoothstep(0.45, 0.9, sube));
    float energia = 0.35 + 0.65 * uCuerpo;
    float respira = 1.0 + 0.10 * uBombo;
    float detalle = mix(0.15, 1.0, uAire);

    vec3 col = s.y < HORIZONTE ? cielo(s, luna, radio, colLuna, energia, respira, detalle)
                               : mar(s, luna, radio, colLuna, energia, respira, detalle);

    // bruma sobre la linea del horizonte, teñida de luna cerca de ella
    float bruma = exp(-abs(s.y - HORIZONTE) / 0.010);
    col += (NOCHE_HORIZONTE * 1.5 + colLuna * 0.18 * exp(-pow((s.x - luna.x) / 0.5, 2.0))) * bruma * 0.5;

    col *= 1.0 + 0.03 * uBombo;
    // vineta
    col *= mix(0.70, 1.0, smoothstep(1.15, 0.30, length(p * vec2(0.85, 1.25))));
    // compresion suave de altas luces
    col = 1.0 - exp(-col * 1.25);

    // texto del tema (alfa recto)
    vec4 tx = texture(uTexto, uv);
    col = mix(col, tx.rgb, tx.a * uTextoAlfa);

    // grano: rompe los escalones que YouTube le hace a los degrades oscuros
    col += (hash(frag + fract(uTime * 7.13) * 91.0) - 0.5) * (2.0 / 255.0);
    fragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
}
