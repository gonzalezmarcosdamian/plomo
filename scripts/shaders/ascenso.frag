#version 330
// Ascenso: un cohete que sube durante todo el set. El look de la Session 03.
// "Mas abstracto ahora ... como la luna, pero un avion que va subiendo, un cohete solamente"
// (el DJ, 2026-10-19). Con la gramatica de marea, que es la que le gusto: plano FIJO sobre el
// mismo mar de la Session 02 y una sola cosa que se mueve casi sin que se note. El cohete sale
// del agua a la izquierda y cruza el cuadro en un arco que se va acostando (el giro por
// gravedad) a lo largo de la hora y media: la foto de exposicion larga de un lanzamiento al
// atardecer, armada durante el set. La estela es humo que TAPA, y solo brilla lo que todavia
// agarra el sol; la sombra de la Tierra va subiendo por ella. Ya alto, el escape se abre en la
// "medusa" de los lanzamientos al atardecer: una cascara curva, borde brillante, centro
// transparente. El audio mueve luz, nunca la camara: el bajo es el largo de la llama y en el
// drop un golpe de escape denso baja por la estela.
//
// La primera version seguia al cohete con la camara: el cohete quedaba quieto en pantalla, el
// mundo cambiaba por actos y el DJ dijo "esta raro". El rediseno sale de tres agentes (critica
// visual, como se ve un lanzamiento real, y retencion en YouTube), 2026-10-19.

uniform vec2 uRes;
uniform float uTime;
uniform float uAltitud;    // 0 en el agua, 1 al final del set: el punto del arco donde va el cohete
uniform float uAltura;     // 1 en el breakdown: el motor afloja y se ven mas estrellas
uniform float uImpacto;    // el golpe del drop, que se apaga en unos segundos
uniform float uDistancia;  // hace fluir el escape fresco (via fluir(): en float32 no se usa directo)
uniform float uBajo;
uniform float uCuerpo;
uniform float uChispa;
uniform float uEtapaEdad;  // segundos desde la ultima separacion de etapa (-1: ninguna en el ultimo minuto)
uniform float uEtapaA;     // en que punto del arco fue
uniform sampler2D uTexto;
uniform float uTextoAlfa;

out vec4 fragColor;

const vec3 NARANJA = vec3(1.00, 0.50, 0.20);
const vec3 CREMA = vec3(1.00, 0.86, 0.66);
const vec3 PLATA = vec3(0.90, 0.93, 1.00);
const vec3 NOCHE_ARRIBA = vec3(0.004, 0.008, 0.024);
const vec3 NOCHE_HORIZONTE = vec3(0.028, 0.046, 0.090);
const vec3 MAR = vec3(0.003, 0.010, 0.022);
const float HY = -0.28;          // el horizonte, fijo todo el set (en p, con y hacia arriba)
const float HORIZONTE = 0.78;    // el mismo, en las coordenadas de marea (desde arriba)

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

float fbm(vec2 p) {
    float v = 0.0, a = 0.5;
    for (int i = 0; i < 4; i++) {
        v += a * ruido(p);
        p = mat2(1.6, -1.2, 1.2, 1.6) * p + 7.3;
        a *= 0.5;
    }
    return v;
}

// la de marea: las octavas altas se escalan con el detalle
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

// fluir sin perder precision: uDistancia llega a miles y en float32 el ruido se volvia
// escalones a la hora de set. Dos capas periodicas que se turnan sin costura.
float fluir(vec2 base, float v) {
    const float P = 64.0;
    float f0 = fract(v / P), f1 = fract(v / P + 0.5);
    return mix(fbm(base + vec2(f1 * P, 31.0)), fbm(base + vec2(f0 * P, 0.0)), 1.0 - abs(2.0 * f0 - 1.0));
}

// el arco: sale vertical del agua a la izquierda y se acuesta hacia la derecha
vec2 ruta(float t) { return vec2(-0.45 + 0.85 * t * t, HY + 0.60 * t - 0.08 * t * t); }
vec2 rumbo(float t) { return normalize(vec2(1.70 * t, 0.60 - 0.16 * t)); }

// distancia con signo a la estela ya recorrida (0..hasta) y el t del punto mas cercano
vec2 aLaEstela(vec2 p, float hasta) {
    const int N = 48;
    float mejor = 1e9, tm = 0.0, lado = 1.0;
    vec2 a = ruta(0.0);
    for (int i = 1; i <= N; i++) {
        float tb = hasta * float(i) / float(N);
        vec2 b = ruta(tb), ab = b - a, ap = p - a;
        float h = clamp(dot(ap, ab) / max(dot(ab, ab), 1e-10), 0.0, 1.0);
        float d = length(ap - ab * h);
        if (d < mejor) {
            mejor = d;
            tm = tb - hasta / float(N) * (1.0 - h);
            lado = sign(ab.x * ap.y - ab.y * ap.x + 1e-9);
        }
        a = b;
    }
    return vec2(mejor * lado, tm);
}

// el drop: un golpe de escape denso que baja por la estela mientras uImpacto se apaga
float golpe(float atras) {
    float viaje = 0.35 * (1.0 - uImpacto);
    return uImpacto * smoothstep(0.0, 0.03, atras) * exp(-pow((atras - viaje) / (0.03 + 0.08 * viaje), 2.0));
}

// del atardecer a la noche de marea, nunca negro; la linea naranja se afina pero no se va
vec3 cielo(vec2 p, float A) {
    float alto = p.y - HY, tarde = 1.0 - smoothstep(0.0, 0.55, A);
    vec3 c = mix(mix(NOCHE_HORIZONTE, vec3(0.60, 0.33, 0.18), tarde),
                 mix(NOCHE_ARRIBA, vec3(0.05, 0.09, 0.22), tarde), pow(clamp(alto / 0.75, 0.0, 1.0), 0.55));
    return c + NARANJA * exp(-max(alto, 0.0) / mix(0.12, 0.02, smoothstep(0.0, 0.7, A))) * mix(0.8, 0.4, A);
}

float estrellas(vec2 p) {
    vec2 q = p * 85.0;
    vec2 c0 = floor(q);
    float r = hash(c0);
    vec2 centro = vec2(hash(c0 + 1.3), hash(c0 + 7.1)) * 0.6 + 0.2;
    float titila = 1.0 - 0.5 * uChispa * (0.5 + 0.5 * sin(uTime * (2.0 + 4.0 * r) + r * 60.0));
    return step(0.972, r) * smoothstep(0.12, 0.0, length(fract(q) - centro)) * titila;
}

// el humo se MEZCLA (tapa), se abre con la edad, lo tuerce el viento en minutos, y solo brilla
// lo que esta arriba de la sombra de la Tierra, que sube a medida que cae la noche
vec3 humo(vec3 col, vec2 p, float A, vec3 luz) {
    float lejos = smoothstep(0.0, 0.6, length(p - ruta(A)));
    p.x += 0.05 * lejos * (fbm(vec2(p.y * 2.5, uTime * 0.012)) - 0.5);
    vec2 e = aLaEstela(p, A);
    float edad = A - e.y, x = e.x / (0.002 + 0.06 * edad);
    // el escape fresco corre con el cohete; el humo viejo no se queda quieto: se arremolina
    // despacio ("dale mas animacion")
    float tex = fluir(vec2(e.y * 60.0, x * 0.8 + 5.0), uDistancia * 2.0 * exp(-edad * 40.0) + uTime * 0.12);
    float g = golpe(edad * length(vec2(1.70 * A, 0.60 - 0.16 * A)));
    float dens = exp(-x * x) * (0.55 + 0.45 * tex) * mix(0.9, 0.35, smoothstep(0.0, 0.8, edad)) * (1.0 + g);
    float sol = smoothstep(-0.04, 0.06, p.y - mix(-0.40, 0.05, uAltitud));
    float cara = 0.75 + 0.25 * clamp(-x, -1.0, 1.0);   // el lado de abajo mira al sol
    vec3 tono = mix(vec3(0.05, 0.06, 0.09), luz * cara * (1.0 + 0.5 * g), sol);
    return mix(col, tono, clamp(dens * 0.85, 0.0, 1.0));
}

// la medusa: un paraboloide que envuelve al cohete; borde brillante, centro transparente
vec3 medusa(vec2 p, float A, vec3 luz) {
    vec2 q = p - ruta(A), f = rumbo(A);
    float u = -dot(q, f), v = dot(q, vec2(-f.y, f.x));
    float k = mix(0.10, 0.30, smoothstep(0.45, 1.0, A)) * (1.0 + 0.25 * uImpacto);
    float pared = k * sqrt(max(u + 0.004, 0.0));
    float borde = exp(-pow((abs(v) - pared) / (0.004 + 0.05 * max(u, 0.0)), 2.0));
    // ondas que viajan hacia atras por la cascara, y filamentos que fluyen
    borde *= 0.65 + 0.35 * sin(u * 45.0 - uTime * 2.2);
    float velo = exp(-pow(v / max(pared, 1e-3), 2.0)) * 0.25;
    float tex = 0.6 + 0.4 * fluir(vec2(u * 8.0, v * 6.0), -uDistancia * 0.5 - uTime * 0.3);
    float hay = smoothstep(0.45, 0.85, A) * smoothstep(-0.01, 0.01, u + 0.004);
    // brazos cortos: largos, la cascara se leia como un bumeran
    return luz * (0.45 * borde + velo) * exp(-max(u, 0.0) / mix(0.10, 0.26, A)) * tex * hay;
}

// el cohete es un punto de luz con el halo de la luna; la llama sigue el rumbo
vec3 luzCohete(vec2 p, float A, vec3 luz, float motor) {
    vec2 q = p - ruta(A), f = rumbo(A);
    float d = length(q), atras = -dot(q, f), lat = dot(q, vec2(-f.y, f.x));
    float largo = 0.02 + 0.04 * uBajo * motor + 0.06 * uImpacto;
    float llama = exp(-abs(lat) / (0.0025 + 0.002 * motor)) * exp(-max(atras, 0.0) / largo)
                * smoothstep(-0.002, 0.002, atras);
    llama *= 0.9 + 0.1 * ruido(vec2(uTime * 9.0, 1.3));   // titila apenas, como un motor
    // los nudos brillantes del escape (diamantes de choque): solo abajo, donde el aire es denso
    float diamantes = 0.0;
    for (int k = 1; k <= 4; k++) {
        diamantes += exp(-pow((atras - float(k) * 0.006) / 0.0015, 2.0)) * exp(-float(k) * 0.35);
    }
    diamantes *= exp(-abs(lat) / 0.0018) * (1.0 - smoothstep(0.08, 0.35, A)) * motor;
    return vec3(1.0, 0.93, 0.80) * exp(-d / 0.003) * 1.8
         + vec3(1.0, 0.60, 0.28) * llama * motor * 1.2
         + vec3(1.0, 0.85, 0.60) * diamantes * 0.9
         + luz * exp(-d / (0.07 + 0.03 * uBajo)) * 0.22 * (0.6 + 0.4 * motor);
}

// nubes altas que cruzan despacio: encendidas por el atardecer al principio, grises de noche
vec3 nubes(vec3 col, vec2 p, float A) {
    float alto = p.y - HY;
    float n = fbm(vec2(p.x * 1.2 + uTime * 0.007, alto * 7.0) + vec2(0.0, 1.7));
    float banda = smoothstep(0.04, 0.20, alto) * (1.0 - smoothstep(0.35, 0.65, alto));
    float d = smoothstep(0.56, 0.80, n) * banda;
    vec3 tono = mix(vec3(1.0, 0.58, 0.32) * 0.85, vec3(0.13, 0.16, 0.26), smoothstep(0.08, 0.55, A));
    return mix(col, tono, d * 0.55);
}

// una estrella fugaz de vez en cuando, mas seguido en el breakdown; solo con el cielo oscuro
vec3 fugaz(vec2 p) {
    const float CICLO = 37.0, DURA = 0.9;
    float n = floor(uTime / CICLO), fase = fract(uTime / CICLO) * CICLO;
    if (fase > DURA || hash(vec2(n, 3.7)) > 0.25 + 0.45 * uAltura) return vec3(0.0);
    vec2 inicio = vec2(mix(-0.8, 0.8, hash(vec2(n, 1.1))), mix(0.05, 0.42, hash(vec2(n, 2.2))));
    vec2 dir = normalize(vec2(mix(-1.0, 1.0, hash(vec2(n, 5.5))), -0.6));
    vec2 cabeza = inicio + dir * fase * 0.5, cola = cabeza - dir * 0.12;
    vec2 ab = cabeza - cola, ap = p - cola;
    float h = clamp(dot(ap, ab) / dot(ab, ab), 0.0, 1.0);
    float brillo = exp(-length(ap - ab * h) / 0.0012) * h * h * sin(3.14159 * fase / DURA);
    return vec3(0.9, 0.92, 1.0) * brillo * 0.9 * smoothstep(0.25, 0.6, uAltitud);
}

// la separacion de etapa: la pluma vieja se desprende y se va hacia atras por la estela y
// hacia abajo, abriendose mientras se apaga; la primera etapa cae como una chispa. La primera
// version era una burbuja que se inflaba donde fue la separacion, pero el cohete se mueve tan
// despacio que en 35 s seguia ahi: quedaba un aro alrededor del cohete, el anillo de lente
vec3 etapa(vec2 p, vec3 luz) {
    if (uEtapaEdad < 0.0) return vec3(0.0);
    float e = uEtapaEdad;
    vec2 f = rumbo(uEtapaA);
    vec2 c = ruta(uEtapaA) - f * (0.012 + 0.006 * e) - vec2(0.0, 0.0012 * e);
    vec2 q = p - c;
    float u = dot(q, f), v = dot(q, vec2(-f.y, f.x));
    float largo = 0.03 + 0.006 * e, ancho = 0.012 + 0.003 * e;
    float nube = exp(-(u * u) / (largo * largo) - (v * v) / (ancho * ancho));
    float tex = 0.5 + 0.5 * fbm(vec2(u * 30.0 - e * 0.2, v * 30.0) + 3.0);
    float sale = smoothstep(0.0, 1.5, e) * exp(-e / 14.0);
    vec2 cae = ruta(uEtapaA) - f * 0.010 * e - vec2(0.0, 0.0010 * e * e);
    float chispa = exp(-length(p - cae) / 0.0022) * exp(-e / 7.0) * 1.4;
    return luz * nube * tex * sale * 0.9 + vec3(1.0, 0.70, 0.40) * chispa;
}

// el mar de marea: refleja al cohete como reflejaba a la luna
vec3 mar(vec2 s, vec2 luna, float radio, vec3 colLuna, float energia) {
    float dy = s.y - HORIZONTE;
    float z = 1.0 / (dy + 0.004);
    vec2 plano = vec2((s.x - luna.x) * z, z);
    float lejos = smoothstep(0.0, 0.06, dy);
    vec2 flujo = vec2(cos(0.3), sin(0.3)) * uTime * 0.15;
    float olas = fbm(vec2(plano.x * 0.45, plano.y * 4.0) + flujo + vec2(0.0, uTime * 0.6), lejos + 0.1, 5);
    vec3 col = mix(NOCHE_HORIZONTE * 0.8, MAR, smoothstep(0.0, 0.25, dy)) * (0.75 + 0.5 * olas);
    float ancho = 0.015 + radio * 0.6 + dy * (0.50 + 0.45 * uBajo);
    float columna = exp(-pow((s.x - luna.x) / ancho, 2.0));
    float cresta = smoothstep(0.52 - 0.08 * uBajo, 0.86, olas);
    col += colLuna * columna * cresta * (0.35 + 0.65 * smoothstep(0.0, 0.03, dy)) * energia * 1.1;
    col += colLuna * columna * 0.06 * energia * (1.0 - smoothstep(0.0, 0.4, dy));
    float celda = 1.0 / 170.0;
    vec2 c = floor(s / celda);
    float r = hash(c + 5.3);
    vec2 centro = (c + 0.5 + 0.3 * (vec2(hash(c + 1.7), hash(c + 8.2)) - 0.5)) * celda;
    float punto = exp(-dot(s - centro, s - centro) / (celda * celda * 0.03));
    float pulso = pow(max(0.0, sin(uTime * (1.5 + 3.5 * r) + r * 60.0)), 10.0);
    col += colLuna * step(0.80, r) * columna * cresta * lejos * punto * pulso * (0.25 + 0.75 * uChispa) * energia * 1.6;
    return col;
}

void main() {
    // la fila 0 del framebuffer es la de ARRIBA del video (ver atardecer.frag): se da vuelta y
    vec2 frag = gl_FragCoord.xy;
    vec2 uv = frag / uRes;
    vec2 p = (vec2(frag.x, uRes.y - frag.y) - 0.5 * uRes) / uRes.y;
    float W = uRes.x / uRes.y;

    float A = max(uAltitud, 0.003);
    vec2 c0 = ruta(A);
    // un solo arco de color, que es el reloj del set: naranja, crema, plata (el de la luna)
    vec3 luz = mix(mix(NARANJA, CREMA, smoothstep(0.0, 0.45, A)), PLATA, smoothstep(0.45, 0.9, A));
    // el motor: afloja en el breakdown, se enciende de golpe en el drop
    float motor = clamp(0.35 + 0.45 * uCuerpo * (1.0 - 0.6 * uAltura) + 0.9 * uImpacto, 0.0, 1.6);

    vec3 col;
    if (p.y > HY) {
        col = cielo(p, A);
        col += vec3(0.85, 0.9, 1.0) * estrellas(p) * smoothstep(0.25, 0.7, A)
             * smoothstep(0.05, 0.3, p.y - HY) * (0.5 + 0.5 * uAltura);
        col += fugaz(p);
        col = nubes(col, p, A);
        col = humo(col, p, A, mix(CREMA, PLATA, smoothstep(0.3, 0.9, A)));
        col += medusa(p, A, luz);
        col += etapa(p, luz);
    } else {
        col = mar(vec2(p.x + 0.5 * W, 0.5 - p.y), vec2(c0.x + 0.5 * W, 0.5 - c0.y), 0.004, luz,
                  (0.35 + 0.65 * uCuerpo) * 0.6 * mix(1.0, 0.5, A));
    }
    col += luzCohete(p, A, luz, motor);
    // la bruma sobre el horizonte, tenida del cohete cerca de el (la de marea)
    col += (NOCHE_HORIZONTE * 1.5 + luz * 0.18 * exp(-pow((p.x - c0.x) / 0.5, 2.0))) * exp(-abs(p.y - HY) / 0.010) * 0.5;

    // vineta y compresion suave de altas luces
    col *= mix(0.70, 1.0, smoothstep(1.15, 0.30, length(p * vec2(0.85, 1.25))));
    col = 1.0 - exp(-col * 1.25);

    // texto del tema (alfa recto)
    vec4 tx = texture(uTexto, uv);
    col = mix(col, tx.rgb, tx.a * uTextoAlfa);

    // grano: rompe los escalones que YouTube le hace a los degrades oscuros
    col += (hash(frag + fract(uTime * 7.13) * 91.0) - 0.5) * (2.0 / 255.0);
    fragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
}
