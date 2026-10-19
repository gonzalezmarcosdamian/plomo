#version 330
// Ascenso: un cohete que sube durante todo el set. El look de la Session 03.
// "Mas abstracto ahora ... como la luna, pero un avion que va subiendo, un cohete solamente"
// (el DJ, 2026-10-19). Como la luna de marea: una sola cosa en la imagen, que se mueve a lo
// largo de toda la hora y media. La camara acompana al cohete: el horizonte se va quedando
// abajo, el cielo pasa del atardecer al negro y al final se ve la curva de la Tierra.
// Sube mas rapido en el groove y planea en el breakdown (video_animar.camara). El bajo es el
// largo de la llama; en el drop el motor se enciende de golpe y la estela florece, como los
// cohetes que se ven al atardecer. Nada salta: lo que se mueve viene suavizado.

uniform vec2 uRes;
uniform float uTime;
uniform float uAltitud;    // 0 en la plataforma, 1 al final del set
uniform float uAltura;     // 1 en el breakdown: el motor afloja y aparecen las estrellas
uniform float uImpacto;    // el golpe del drop, que se apaga en unos segundos
uniform float uDistancia;  // lo que se subio: hace correr el humo hacia abajo
uniform float uBajo;
uniform float uCuerpo;
uniform float uChispa;
uniform sampler2D uTexto;
uniform float uTextoAlfa;

out vec4 fragColor;

float hash(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

float ruido(vec2 p) {
    vec2 i = floor(p), f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    float a = hash(i), b = hash(i + vec2(1, 0)), c = hash(i + vec2(0, 1)), d = hash(i + vec2(1, 1));
    return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

float fbm(vec2 p) {
    float v = 0.0, a = 0.5;
    for (int i = 0; i < 4; i++) {
        v += a * ruido(p);
        p = mat2(1.6, -1.2, 1.2, 1.6) * p + 7.3;
        a *= 0.5;
    }
    return v;
}

// el cohete casi quieto en la pantalla, con una deriva lenta para que no parezca pegado
vec2 cohete() {
    return vec2(0.10 + 0.012 * sin(uTime * 0.11), 0.10 + 0.008 * sin(uTime * 0.07 + 1.3));
}

vec3 cielo(vec2 p, float espacio, out float suelo) {
    // el horizonte baja hasta irse de cuadro (solo cielo) y, ya en el espacio, vuelve desde abajo
    // como la curva de la Tierra: un circulo cada vez mas chico, o sea cada vez mas curvo
    float vuelve = smoothstep(0.55, 1.0, uAltitud);
    float hy = mix(-0.30, -0.78, smoothstep(0.0, 0.45, uAltitud)) + 0.40 * vuelve;
    float R = mix(60.0, 1.6, vuelve);
    float alto = p.y - (hy - R + sqrt(max(R * R - p.x * p.x, 0.0)));
    vec3 horiz = mix(vec3(1.00, 0.55, 0.24), vec3(1.00, 0.50, 0.30), espacio);
    vec3 cenit = mix(vec3(0.06, 0.11, 0.26), vec3(0.004, 0.006, 0.018), espacio);
    vec3 c = mix(horiz, cenit, smoothstep(-0.02, mix(0.75, 0.10, espacio), alto));
    // la atmosfera vista desde arriba: una linea fina sobre la curva, naranja abajo y azul arriba
    float capa = exp(-max(alto, 0.0) / mix(0.20, 0.014, espacio)) * step(0.0, alto);
    // naranja pegada a la Tierra, azul arriba: la atmosfera vista desde el espacio
    vec3 aire = mix(vec3(1.0, 0.55, 0.25), vec3(0.30, 0.55, 1.0), smoothstep(0.0, 0.010, alto) * espacio);
    c += aire * capa * mix(0.25, 0.9, espacio);
    // abajo, la tierra ya de noche
    suelo = smoothstep(0.0, -0.008, alto);
    return mix(c, vec3(0.010, 0.011, 0.018), suelo);
}

float estrellas(vec2 p) {
    vec2 q = p * 85.0;
    vec2 c0 = floor(q);
    float r = hash(c0);
    vec2 centro = vec2(hash(c0 + 1.3), hash(c0 + 7.1)) * 0.6 + 0.2;
    float titila = 1.0 - 0.5 * uChispa * (0.5 + 0.5 * sin(uTime * (2.0 + 4.0 * r) + r * 60.0));
    return step(0.972, r) * smoothstep(0.10, 0.0, length(fract(q) - centro)) * titila;
}

// la estela: el humo viejo queda abajo, se curva y se abre; corre hacia abajo mientras el cohete sube
vec3 estela(vec2 p, vec2 c0, float espacio, float motor) {
    float s = c0.y - p.y;
    if (s <= 0.0) return vec3(0.0);
    float sube = uDistancia * 2.0;
    float x = c0.x - 0.07 * pow(s, 1.5) + 0.03 * s * (fbm(vec2(s * 1.5 - sube * 0.2, 4.0)) - 0.5);
    float ancho = 0.003 + 0.045 * s * (0.8 + 0.5 * uAltura) + 0.004 * motor;
    float d = (p.x - x) / ancho;
    float humo = fbm(vec2(d * 0.8, s * 7.0 - sube));
    float i = exp(-d * d) * (0.45 + 0.55 * humo) * exp(-s * mix(1.3, 2.4, espacio));
    vec3 lejos = mix(vec3(0.95, 0.62, 0.50), vec3(0.55, 0.70, 1.0), espacio);
    return mix(vec3(1.0, 0.80, 0.55), lejos, smoothstep(0.0, 0.15, s)) * i * (0.6 + 0.4 * motor);
}

// ya alto, el escape se abre en una campana de luz pastel alrededor del cohete
vec3 campana(vec2 p, vec2 c0, float espacio, float motor) {
    vec2 d = p - c0;
    float r = length(d);
    float ang = abs(atan(d.x, -d.y));   // 0 hacia abajo
    float R = mix(0.15, 0.55, smoothstep(0.35, 0.9, uAltitud)) * (1.0 + 0.35 * uImpacto);
    // el borde ondula con la distancia y el tiempo: un recorte recto parecia un faro
    float apertura = mix(0.55, 0.95, uImpacto) + 0.18 * (fbm(vec2(r * 5.0 - uDistancia * 0.6, 2.0)) - 0.5);
    float adentro = smoothstep(apertura, apertura * 0.45, ang) * exp(-r / R);
    float borde = exp(-pow((ang - apertura * 0.85) / (0.06 + 0.25 * r), 2.0)) * exp(-r / (R * 1.3));
    float filamentos = 0.5 + 0.5 * fbm(vec2(ang * 9.0, r * 3.0 - uDistancia * 1.2));
    float textura = 0.45 + 0.55 * filamentos * filamentos;
    vec3 c = mix(vec3(0.95, 0.55, 0.65), vec3(0.45, 0.70, 1.0), clamp(r / R, 0.0, 1.0));
    return c * (0.30 * adentro + 0.30 * borde) * textura * smoothstep(0.30, 0.55, uAltitud) * (0.5 + 0.5 * motor);
}

void main() {
    // la fila 0 del framebuffer es la de ARRIBA del video (ver atardecer.frag): se da vuelta y
    vec2 frag = gl_FragCoord.xy;
    vec2 uv = frag / uRes;
    vec2 p = (vec2(frag.x, uRes.y - frag.y) - 0.5 * uRes) / uRes.y;

    float espacio = smoothstep(0.25, 0.85, uAltitud);
    // el motor: afloja en el breakdown, se enciende de golpe en el drop
    float motor = clamp(0.35 + 0.45 * uCuerpo * (1.0 - 0.6 * uAltura) + 0.9 * uImpacto, 0.0, 1.6);
    vec2 c0 = cohete();

    float suelo;
    vec3 col = cielo(p, espacio, suelo);
    float oscuro = 1.0 - smoothstep(0.05, 0.35, dot(col, vec3(0.333)));
    col += vec3(0.85, 0.9, 1.0) * estrellas(p) * oscuro * (1.0 - suelo) * (0.25 + 0.75 * espacio) * (0.5 + 0.5 * uAltura);
    col += estela(p, c0, espacio, motor) * (1.0 - suelo) * (1.0 - 0.7 * smoothstep(0.4, 0.9, uAltitud));
    col += campana(p, c0, espacio, motor);

    // la llama: el bajo es su largo, el drop la estira
    vec2 d = p - c0;
    // el drop: un anillo que se abre desde el cohete mientras el golpe se apaga, sin flash
    float radio = (1.0 - uImpacto) * 0.7;
    col += mix(vec3(1.0, 0.70, 0.55), vec3(0.55, 0.75, 1.0), espacio)
           * uImpacto * smoothstep(0.15, 0.35, uImpacto + 0.2 * (1.0 - radio))
           * exp(-pow((length(d) - radio) / (0.012 + 0.05 * radio), 2.0)) * 0.6;
    float largo = 0.03 + 0.06 * uBajo * motor + 0.08 * uImpacto;
    float llama = exp(-abs(d.x) / (0.004 + 0.003 * motor)) * exp(-max(-d.y, 0.0) / largo) * step(d.y, 0.002);
    col += vec3(1.0, 0.92, 0.75) * exp(-length(d) / 0.0035) * 1.8;
    col += vec3(1.0, 0.62, 0.30) * llama * motor * 1.4;
    col += vec3(1.0, 0.55, 0.30) * exp(-length(d) / (0.05 + 0.04 * uImpacto)) * 0.35 * motor;

    // el cohete: una silueta chica y oscura arriba de la llama, con el borde que agarra el sol
    vec2 q = d - vec2(0.0, 0.016);
    float forma = length(max(abs(q) - vec2(0.0016, 0.012), 0.0)) - 0.0012;
    float cuerpo = smoothstep(0.0008, 0.0, forma);
    vec3 tono = vec3(0.08, 0.08, 0.10) + vec3(1.0, 0.6, 0.35) * smoothstep(0.0, -0.0015, q.x) * 0.5 * (1.0 - espacio * 0.6);
    col = mix(col, tono, cuerpo);

    // vineta y compresion suave de altas luces
    col *= mix(0.75, 1.0, smoothstep(1.15, 0.30, length(p * vec2(0.85, 1.25))));
    col = 1.0 - exp(-col * 1.15);

    // texto del tema (alfa recto)
    vec4 tx = texture(uTexto, uv);
    col = mix(col, tx.rgb, tx.a * uTextoAlfa);

    // grano: rompe los escalones que YouTube le hace a los degrades oscuros
    col += (hash(frag + fract(uTime * 7.13) * 91.0) - 0.5) * (2.0 / 255.0);
    fragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
}
