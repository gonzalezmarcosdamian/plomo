#version 330
// Fiesta: una fiesta en la playa, del atardecer a la noche. El look de la Session 04.
// "Busca mejores ideas de visuales, podes hacer como que fuera una fiesta? que es lo que mas
// reproducciones tiene? revisa en youtube" (el DJ, 2026-10-20). Lo que mas se ve en YouTube de
// este genero son sets filmados en un lugar lindo, al atardecer y con gente (Cercle, Miss
// Monique, Mayan Warrior, la playa). Aca es eso de espaldas y a contraluz: el sol se mete en el
// mar detras de la cabina, se hace de noche y la luz pasa a ser la del escenario.
//
// La gramatica de marea sigue: plano FIJO y nada de flashes. La gente se mueve a tiempo con el
// beat (uFase), levanta los brazos con la euforia (el groove de a poco, el drop de golpe) y saca
// el telefono en el breakdown. Los dos drops mas grandes del set tiran papelitos; si ya es de
// noche, tambien fuegos artificiales sobre el mar.

uniform vec2 uRes;
uniform float uTime;
uniform float uProgreso;   // 0 al empezar el set, 1 al terminar: es la hora del dia
uniform float uAltura;     // 1 en el breakdown
uniform float uEuforia;    // 0 a 1: cuantos brazos arriba
uniform float uFase;       // en que parte del beat estamos (0 en el golpe)
uniform float uDistancia;  // crece mas rapido en el groove: mueve las luces sin saltos
uniform vec3 uLuces;       // el color del escenario, uno por tema
uniform float uBombo;
uniform float uBajo;
uniform float uCuerpo;
uniform float uChispa;
uniform float uEtapaEdad;  // segundos desde uno de los dos drops grandes (-1: ninguno en el ultimo minuto)
uniform sampler2D uTexto;
uniform float uTextoAlfa;

out vec4 fragColor;

const float PI2 = 6.28318;
const vec3 NARANJA = vec3(1.00, 0.50, 0.20);
const vec3 CREMA = vec3(1.00, 0.86, 0.66);
const vec3 NOCHE_ARRIBA = vec3(0.004, 0.008, 0.024);
const vec3 NOCHE_HORIZONTE = vec3(0.028, 0.046, 0.090);
const vec3 SILUETA = vec3(0.010, 0.009, 0.013);
const vec3 FOCO = vec3(1.00, 0.70, 0.40);
const vec3 PANTALLA = vec3(0.75, 0.86, 1.00);
const float HY = -0.005;     // el horizonte (en p, con y hacia arriba)
const float ORILLA = -0.105;
const float PISO = -0.125;   // el piso de la tarima
const float SOL_X = 0.12;
const float FILAS = 9.0;

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

// ---- formas: distancias con signo, negativas adentro ----

vec2 segmentoH(vec2 q, vec2 a, vec2 b) {
    vec2 pa = q - a, ba = b - a;
    float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
    return vec2(length(pa - ba * h), h);
}

float segmento(vec2 q, vec2 a, vec2 b) {
    return segmentoH(q, a, b).x;
}

float caja(vec2 q, vec2 c, vec2 b, float r) {
    vec2 d = abs(q - c) - b + r;
    return length(max(d, 0.0)) + min(max(d.x, d.y), 0.0) - r;
}

float elipse(vec2 q, vec2 r) {
    float k0 = length(q / r), k1 = length(q / (r * r));
    return k0 * (k0 - 1.0) / k1;
}

float smin(float a, float b, float k) {
    float h = max(k - abs(a - b), 0.0) / k;
    return min(a, b) - h * h * k * 0.25;
}

float cubre(float d, float px) {
    return 1.0 - smoothstep(-px, px, d);
}

// ---- el fondo ----

vec3 cielo(vec2 p, vec2 sol, float radio, vec3 colSol, float solVis, vec3 hz, vec3 md, vec3 ar, float noche) {
    float alto = clamp((p.y - HY) / (0.5 - HY), 0.0, 1.0);
    vec3 col = mix(hz, md, smoothstep(0.0, 0.30, alto));
    col = mix(col, ar, smoothstep(0.25, 1.0, alto));
    float d = length(p - sol);
    col += colSol * (exp(-d / 0.07) * 0.8 + exp(-d / 0.40) * 0.25) * solVis;

    // nubes finas y estiradas, encendidas desde abajo por el sol; de noche las tine el escenario
    vec2 q = vec2(p.x * 1.1, p.y * 5.0) + vec2(uTime * 0.004, 0.0);
    float nube = smoothstep(0.48, 0.82, fbm(q * 1.3 + 0.6 * vec2(fbm(q + 3.1), fbm(q + 7.4))))
               * smoothstep(0.02, 0.15, alto) * (1.0 - 0.5 * alto);
    vec3 luzNube = mix(colSol * (0.5 + 0.9 * exp(-d / 0.35)) * (0.3 + 0.7 * solVis) + md * 0.5,
                       md * 0.7 + uLuces * 0.05 * exp(-abs(p.x) / 0.5), noche);
    col = mix(col, luzNube, nube * 0.75);

    // estrellas: solo de noche, titilan con los hats
    float celda = 1.0 / 110.0;
    vec2 c = floor(p / celda);
    float r = hash(c + 3.7);
    vec2 centro = (c + 0.5 + 0.35 * (vec2(hash(c + 9.1), hash(c + 2.3)) - 0.5)) * celda;
    float punto = exp(-dot(p - centro, p - centro) / (celda * celda * 0.012));
    float titila = 0.5 + 0.5 * mix(1.0, 0.5 + 0.5 * sin(uTime * (2.0 + 3.0 * r) + r * 40.0), uChispa);
    col += vec3(0.85, 0.90, 1.0) * step(0.965, r) * punto * titila * smoothstep(0.08, 0.4, alto)
         * (1.0 - nube) * smoothstep(0.55, 0.9, noche) * 0.7;

    // el disco; las nubes lo tapan a medias
    float disco = 1.0 - smoothstep(radio - 0.002, radio + 0.002, d);
    col = mix(col, colSol * 1.7, disco * (1.0 - 0.6 * nube));
    return col;
}

vec3 mar(vec2 p, vec3 hz, vec3 colSol, float solVis, float noche) {
    // perspectiva de un plano: a la distancia dy del horizonte le toca la profundidad 1/dy
    float dy = HY - p.y;
    float z = 1.0 / (dy + 0.004);
    vec2 plano = vec2(p.x * z, z);
    float lejos = smoothstep(0.0, 0.04, dy);
    float olas = fbm(vec2(plano.x * 0.45, plano.y * 4.0) + vec2(uTime * 0.05, uTime * 0.6), lejos + 0.1, 5);
    vec3 hondo = mix(vec3(0.06, 0.04, 0.08), vec3(0.003, 0.008, 0.018), noche);
    vec3 col = mix(hz * 0.55, hondo, smoothstep(0.0, 0.10, dy)) * (0.75 + 0.5 * olas);
    float cresta = smoothstep(0.50 - 0.08 * uBajo, 0.86, olas);
    // el camino del sol; de noche, el del escenario
    float ancho = 0.010 + dy * (0.55 + 0.40 * uBajo);
    col += colSol * exp(-pow((p.x - SOL_X) / ancho, 2.0)) * cresta * solVis * 1.2;
    col += uLuces * exp(-pow(p.x / (0.03 + dy * 0.9), 2.0)) * cresta * noche * (0.15 + 0.35 * uCuerpo);
    return col;
}

vec3 arena(vec2 p, vec3 hz, float noche) {
    vec3 col = mix(hz * 0.16 + vec3(0.05, 0.035, 0.03), vec3(0.012, 0.012, 0.018), noche);
    col *= mix(1.0, 0.2, smoothstep(ORILLA, ORILLA - 0.05, p.y));   // la sombra de la gente
    float espuma = exp(-abs(p.y - ORILLA - 0.003 * sin(p.x * 18.0 + uTime * 0.7)) / 0.0025);
    return col + mix(hz * 0.5, vec3(0.04), noche) * espuma * 0.5;
}

// ---- luces del escenario ----

float haz(vec2 p, vec2 o, float ang, float abre) {
    vec2 dir = vec2(sin(ang), cos(ang));
    vec2 v = p - o;
    float a = dot(v, dir);
    if (a <= 0.0) return 0.0;
    float perp = abs(v.x * dir.y - v.y * dir.x);
    return exp(-pow(perp / (0.003 + a * abre), 2.0)) * smoothstep(0.0, 0.03, a) * exp(-a * 0.9);
}

// seis haces: dos por torre y dos desde la cabina. Barren con uDistancia, que corre rapido en el
// groove y despacio en el breakdown; en el breakdown ademas se juntan hacia arriba
vec3 haces(vec2 p, float noche) {
    float junta = 1.0 - 0.6 * uAltura;
    float b = uDistancia * 0.35;
    float h = 0.0;
    for (int i = 0; i < 2; i++) {
        float sg = i == 0 ? -1.0 : 1.0;
        vec2 torre = vec2(sg * 0.30, 0.128);
        h += haz(p, torre, sg * junta * (0.30 + 0.30 * sin(b + 1.3 * float(i))), 0.05);
        h += haz(p, torre, sg * junta * (0.70 + 0.30 * sin(b * 0.8 + 2.0 + float(i))), 0.05);
        h += haz(p, vec2(sg * 0.06, PISO + 0.066), sg * junta * (0.18 + 0.22 * sin(b * 1.2 + 3.1 * float(i))), 0.03);
    }
    float humo = 0.6 + 0.4 * fbm(p * vec2(4.0, 2.0) + vec2(uTime * 0.03, -uTime * 0.01));
    float fuerza = (0.12 + 0.88 * noche) * (0.25 + 0.55 * uCuerpo * (1.0 - 0.4 * uAltura) + 0.3 * uEuforia);
    return mix(uLuces, vec3(1.0), 0.15) * h * humo * fuerza * 0.55;
}

// laseres: un abanico de nueve desde la cabina, solo de noche y con la euforia arriba
vec3 laseres(vec2 p, float px, float noche) {
    float on = noche * smoothstep(0.50, 0.85, uEuforia);
    vec2 v = p - vec2(0.0, PISO + 0.07);
    if (on <= 0.0 || v.y <= 0.0) return vec3(0.0);
    float ang = atan(v.x, v.y);
    float r = length(v);
    float abre = 0.13 + 0.04 * sin(uDistancia * 0.21);
    float centro = 0.25 * sin(uDistancia * 0.13);
    float k = clamp(floor((ang - centro) / abre + 0.5), -4.0, 4.0);
    float perp = r * abs(sin(ang - centro - k * abre));
    float linea = exp(-pow(perp / (0.9 * px), 2.0)) + 0.25 * exp(-perp / (5.0 * px));
    return mix(uLuces, vec3(1.0), 0.3) * linea * on * exp(-r * 0.8) * smoothstep(0.0, 0.05, r) * 0.8;
}

// fuegos artificiales sobre el mar: cinco estallidos en los primeros 15 s de un drop grande
vec3 fuegos(vec2 p, float noche) {
    float edad = uEtapaEdad;
    if (edad < 0.0 || noche < 0.5 || p.y < HY) return vec3(0.0);
    vec3 col = vec3(0.0);
    for (int k = 0; k < 5; k++) {
        float fk = float(k);
        float a = edad - fk * 2.7 - 0.8 * hash(vec2(fk, 1.7));
        if (a < 0.0 || a > 2.6) continue;
        vec2 o = vec2(mix(-0.55, 0.55, hash(vec2(fk, 4.4))), 0.16 + 0.17 * hash(vec2(fk, 8.8)));
        vec2 v = p - o;
        v.y += 0.018 * a * a;   // caen
        float r = length(v);
        float radio = 0.13 * (1.0 - exp(-a * 2.4));
        if (r > radio + 0.03) continue;
        float rayos = 36.0;
        float cual = floor(atan(v.y, v.x) / PI2 * rayos + 0.5);
        float ang = cual / rayos * PI2;
        vec2 chispa = vec2(cos(ang), sin(ang)) * radio * (0.85 + 0.15 * hash(vec2(cual, fk)));
        float dd = length(v - chispa);
        float estela = segmento(v, chispa * 0.75, chispa);
        float apaga = pow(1.0 - a / 2.6, 2.0);
        vec3 tinte = k % 2 == 0 ? mix(uLuces, vec3(1.0), 0.35) : mix(NARANJA, CREMA, 0.4);
        col += tinte * (exp(-dd / 0.003) * 1.3 + exp(-estela / 0.0015) * 0.5) * apaga;
    }
    return col * noche;
}

// ---- siluetas ----

float palmera(vec2 p, vec2 pie, vec2 copa, float tam, float sem, float px) {
    float d = 1e9;
    // el tronco: una curva que sale derecha del piso y se va inclinando hacia la copa
    if (p.x > min(pie.x, copa.x) - 0.05 && p.x < max(pie.x, copa.x) + 0.05 && p.y < copa.y) {
        vec2 ctrl = vec2(pie.x, mix(pie.y, copa.y, 0.55));
        vec2 a = pie;
        for (int i = 1; i <= 6; i++) {
            float t = float(i) / 6.0;
            vec2 b = mix(mix(pie, ctrl, t), mix(ctrl, copa, t), t);
            d = min(d, segmento(p, a, b) - tam * mix(0.020, 0.011, t));
            a = b;
        }
    }
    vec2 v = p - copa;
    if (abs(v.x) > 0.45 * tam || v.y > 0.36 * tam || v.y < -0.36 * tam) return d;
    float espacio = max(0.0065 * tam, 3.0 * px);
    for (int k = 0; k < 9; k++) {
        float fk = float(k);
        float ang = -2.5 + 5.0 * (fk + 0.5) / 9.0 + 0.25 * (hash(vec2(fk, sem)) - 0.5);
        ang += 0.05 * sin(uTime * 0.5 + fk * 1.3 + sem) + 0.02 * sin(uTime * 1.3 + fk);
        float L = tam * (0.26 + 0.10 * hash(vec2(sem, fk)));
        vec2 dir = vec2(sin(ang), cos(ang));
        float cae = L * (0.35 + 0.45 * abs(dir.x));
        vec2 a = copa;
        for (int n = 1; n <= 5; n++) {
            float t = float(n) / 5.0;
            vec2 b = copa + dir * L * t - vec2(0.0, cae * t * t);
            vec2 sh = segmentoH(p, a, b);
            float tt = (float(n - 1) + sh.y) / 5.0;
            // una hoja de palmera a contraluz es un nervio con un fleco de hojitas colgando:
            // rayas finas que bajan del nervio y se van hacia la punta (el primer intento fue un
            // borde serruchado, y parecian orugas)
            vec2 ab = b - a;
            vec2 abajo = normalize(vec2(-ab.y, ab.x));
            if (abajo.y > 0.0) abajo = -abajo;
            float o = dot(p - (a + ab * sh.y), abajo);   // > 0 colgando abajo del nervio
            float largo = tam * 0.060 * pow(sin(3.14159 * min(tt * 1.08, 1.0)), 0.6);
            float banda = max(-o - 0.35 * largo, o - largo);
            float raya = (abs(fract((tt * L + 0.55 * abs(o)) / espacio) - 0.5) - 0.17) * espacio;
            // acotado al tramo: sin el sh.x, la banda seguia de largo por la recta del tramo
            d = min(d, min(sh.x - 0.0025 * tam, max(max(banda, raya), sh.x - largo)));
            a = b;
        }
    }
    return min(d, length(v) - 0.022 * tam);   // los cocos
}

// la cabina: tarima, mesa, equipos, el DJ y las dos torres de luces. En el drop levanta una mano
float cabina(vec2 p, out float led, out float cabezal) {
    float y0 = PISO;
    float d = caja(p, vec2(0.0, y0 - 0.02), vec2(0.34, 0.02), 0.002);
    d = min(d, caja(p, vec2(0.0, y0 + 0.032), vec2(0.075, 0.032), 0.003));
    d = min(d, caja(p, vec2(-0.045, y0 + 0.067), vec2(0.022, 0.004), 0.002));
    d = min(d, caja(p, vec2(0.045, y0 + 0.067), vec2(0.022, 0.004), 0.002));
    led = caja(p, vec2(0.0, y0 + 0.058), vec2(0.072, 0.0014), 0.0);

    float cabeceo = 0.0035 * (0.5 + 0.5 * cos(PI2 * uFase)) * (0.3 + 0.7 * uCuerpo);
    float dj = caja(p, vec2(0.0, y0 + 0.078 - cabeceo * 0.5), vec2(0.021, 0.034), 0.012);
    dj = smin(dj, elipse(p - vec2(0.002, y0 + 0.124 - cabeceo), vec2(0.0115, 0.0135)), 0.004);
    float arriba = smoothstep(0.58, 0.75, uEuforia);
    for (int i = 0; i < 2; i++) {
        float sg = i == 0 ? -1.0 : 1.0;
        vec2 hombro = vec2(sg * 0.018, y0 + 0.102 - cabeceo * 0.5);
        vec2 mano = vec2(sg * 0.040, y0 + 0.071 + 0.002 * sin(uTime * (1.1 + 0.4 * sg)));
        if (i == 1) mano = mix(mano, vec2(0.046, y0 + 0.19 - 0.006 * (0.5 + 0.5 * cos(PI2 * uFase))), arriba);
        vec2 codo = mix(hombro, mano, 0.5) + vec2(sg * 0.010, -0.006);
        dj = min(dj, min(segmento(p, hombro, codo), segmento(p, codo, mano)) - 0.0042);
    }
    d = min(d, dj);

    cabezal = 1e9;
    for (int i = 0; i < 2; i++) {
        float x = i == 0 ? -0.30 : 0.30;
        d = min(d, caja(p, vec2(x, (y0 + 0.12) * 0.5), vec2(0.0025, (0.12 - y0) * 0.5), 0.0));
        cabezal = min(cabezal, caja(p, vec2(x, 0.126), vec2(0.009, 0.006), 0.003));
    }
    return min(d, cabezal);
}

// una persona de espaldas, en unidades de su alto: los pies en 0, la coronilla en ~2.25.
// aI, aD: cuanto sube cada brazo; tel: el telefono en la mano derecha
float persona(vec2 q, float h, float aI, float aD, float tel, float pulso, out float pantalla) {
    float ancho = 0.40 + 0.10 * h;
    float d = caja(q, vec2(0.0, -0.60), vec2(ancho, 2.20), 0.30);
    d = smin(d, caja(q, vec2(0.0, 1.70), vec2(0.09, 0.12), 0.05), 0.08);
    d = smin(d, elipse(q - vec2(0.02 * (h - 0.5), 1.98), vec2(0.21, 0.25)), 0.06);
    float pelo = fract(h * 13.7);
    if (pelo < 0.18) d = min(d, length(q - vec2(0.0, 2.22)) - 0.10);                        // rodete
    else if (pelo < 0.40) d = smin(d, caja(q, vec2(0.0, 1.72), vec2(0.20, 0.30), 0.12), 0.04);  // pelo largo
    else if (pelo < 0.46) d = min(d, elipse(q - vec2(0.0, 2.10), vec2(0.34, 0.045)));        // sombrero
    vec2 conTel = vec2(0.30, 2.55);
    for (int lado = 0; lado < 2; lado++) {
        float sg = lado == 0 ? -1.0 : 1.0;
        float a = lado == 0 ? aI : aD;
        vec2 hombro = vec2(sg * (ancho - 0.04), 1.48);
        vec2 mano = mix(vec2(sg * (ancho + 0.06), 0.55), vec2(sg * (0.55 + 0.10 * h), 2.95 - 0.16 * pulso), a);
        if (lado == 1) mano = mix(mano, conTel, tel);
        vec2 codo = mix(hombro, mano, 0.5) + vec2(sg * (0.06 + 0.10 * sin(3.14159 * max(a, tel))), -0.04);
        d = min(d, min(segmento(q, hombro, codo) - 0.085, segmento(q, codo, mano) - 0.075));
    }
    pantalla = caja(q, conTel + vec2(0.0, 0.17), vec2(0.075, 0.13), 0.02) + 2.0 * (1.0 - smoothstep(0.75, 1.0, tel));
    return min(d, pantalla);
}

// la fila j de gente (0 la del fondo): la distancia en unidades de pantalla
float fila(vec2 p, float j, out float pantalla) {
    float t = j / (FILAS - 1.0);
    float yb = mix(-0.135, -0.74, pow(t, 1.15));
    float S = mix(0.021, 0.125, pow(t, 1.6));
    pantalla = 1e9;
    if (p.y > yb + 3.3 * S || p.y < yb - 2.9 * S) return 1e9;
    float paso = 0.92 * S;
    float corrida = j * 0.37 + 0.5;
    float i0 = floor(p.x / paso + corrida);
    float energia = (0.25 + 0.75 * uCuerpo) * (1.0 - 0.7 * uAltura);
    float conTelefono = 0.004 + 0.07 * uAltura * (1.0 - uEuforia);
    float d = 1e9;
    for (int k = -1; k <= 1; k++) {
        float i = i0 + float(k);
        vec2 sem = vec2(i, j * 7.13 + 1.0);
        float h = hash(sem), h2 = hash(sem + 3.1), h3 = hash(sem + 5.7), h4 = hash(sem + 9.3);
        float h5 = hash(sem + 11.9), h6 = hash(sem + 13.3), h7 = hash(sem + 17.1);
        if (h < 0.05) continue;   // un hueco
        float s = S * (0.82 + 0.32 * h2);
        // todos al beat, cada uno un poquito corrido y con su propia fuerza
        float pulso = 0.5 + 0.5 * cos(PI2 * (uFase + 0.08 * (h3 - 0.5)));
        float rebote = 0.06 * energia * (0.5 + h4) * pulso;
        float vaiven = 0.05 * sin(uTime * (0.45 + 0.4 * h5) + h * 40.0) * (0.3 + 0.7 * uCuerpo);
        float umbral = 0.45 + 0.9 * h6;
        float aI = smoothstep(umbral - 0.1, umbral + 0.1, uEuforia);
        float aD = smoothstep(umbral + 0.15 * h7 - 0.1, umbral + 0.15 * h7 + 0.1, uEuforia);
        float tel = smoothstep(h7 - 0.02, h7 + 0.02, conTelefono);
        float xc = (i - corrida + 0.5 + 0.34 * (h3 - 0.5)) * paso;
        vec2 q = (p - vec2(xc, yb + S * 0.30 * (h5 - 0.5))) / s - vec2(vaiven, -rebote);
        float pt;
        d = min(d, persona(q, h, aI, aD, tel, pulso, pt) * s);
        pantalla = min(pantalla, pt * s);
    }
    return d;
}

// guirnalda de focos colgando entre a y b
vec3 guirnalda(vec3 col, vec2 p, vec2 a, vec2 b, float caida, float px, float prende) {
    float t = clamp((p.x - a.x) / (b.x - a.x), 0.0, 1.0);
    float y = mix(a.y, b.y, t) - caida * 4.0 * t * (1.0 - t);
    col = mix(col, SILUETA, (1.0 - smoothstep(0.6 * px, 1.6 * px, abs(p.y - y))) * 0.9);
    float paso = 0.042;
    float i0 = floor((p.x - a.x) / paso);
    for (int k = -1; k <= 1; k++) {
        float i = i0 + float(k);
        float x = a.x + (i + 0.5) * paso;
        float tf = clamp((x - a.x) / (b.x - a.x), 0.0, 1.0);
        vec2 foco = vec2(x, mix(a.y, b.y, tf) - caida * 4.0 * tf * (1.0 - tf) - 0.006);
        float d = length(p - foco);
        float fuerza = prende * (0.7 + 0.3 * hash(vec2(i, a.y))) * (1.0 + 0.12 * uBajo);
        col += FOCO * (exp(-d * d / (0.0032 * 0.0032)) * 1.3 + exp(-d / 0.018) * 0.10) * fuerza;
    }
    return col;
}

// papelitos: tres capas que caen y se dan vuelta, en el minuto despues de un drop grande
vec3 papelitos(vec3 col, vec2 p, float px) {
    float edad = uEtapaEdad;
    if (edad < 0.0) return col;
    float cantidad = smoothstep(0.0, 1.5, edad) * (1.0 - smoothstep(20.0, 58.0, edad));
    for (int capa = 0; capa < 3; capa++) {
        float fc = float(capa);
        if (p.y < 0.55 - edad * (0.35 + 0.15 * fc)) continue;   // el frente de la lluvia
        float celda = 0.022 + 0.018 * fc;
        vec2 q = vec2(p.x + 0.3 * fc, p.y + edad * (0.06 + 0.05 * fc));
        vec2 c = floor(q / celda);
        float h = hash(c + 17.0 * fc);
        if (h > 0.30 * cantidad) continue;
        vec2 centro = (c + 0.5 + vec2(0.25 * sin(edad * (1.0 + 2.0 * h) + h * 30.0), 0.0)) * celda;
        float giro = edad * (2.0 + 4.0 * hash(c + 3.3)) + h * 20.0;
        float ca = cos(giro * 0.7), sa = sin(giro * 0.7);
        vec2 v = mat2(ca, -sa, sa, ca) * (q - centro);
        float voltea = abs(cos(giro));   // se da vuelta mientras cae
        float tam = celda * 0.16;
        float d = caja(v, vec2(0.0), vec2(tam, tam * 0.55 * max(voltea, 0.08)), 0.0);
        float cual = hash(c + 5.5);
        vec3 tinte = cual < 0.3 ? uLuces : cual < 0.5 ? NARANJA : cual < 0.7 ? CREMA
                   : cual < 0.85 ? vec3(1.0, 0.45, 0.65) : vec3(0.45, 0.80, 1.0);
        col = mix(col, tinte * (0.45 + 0.55 * pow(voltea, 6.0)), cubre(d, px) * 0.9);
    }
    return col;
}

void main() {
    // la fila 0 del framebuffer es la de ARRIBA del video (ver atardecer.frag): se da vuelta y
    vec2 frag = gl_FragCoord.xy;
    vec2 uv = frag / uRes;
    vec2 p = (vec2(frag.x, uRes.y - frag.y) - 0.5 * uRes) / uRes.y;
    float px = 1.0 / uRes.y;

    // la hora: el sol se mete en el mar a un tercio del set y a los dos tercios ya es de noche
    float tarde = smoothstep(0.12, 0.45, uProgreso);
    float noche = smoothstep(0.38, 0.72, uProgreso);
    float radio = 0.045;
    vec2 sol = vec2(SOL_X, mix(HY + 0.22, HY - 0.07, smoothstep(0.0, 0.45, uProgreso)));
    float solVis = smoothstep(HY - radio, HY + 0.06, sol.y);
    vec3 colSol = mix(vec3(1.00, 0.80, 0.48), vec3(1.00, 0.42, 0.18), smoothstep(HY + 0.20, HY, sol.y));
    vec3 hz = mix(mix(vec3(1.00, 0.55, 0.28), vec3(0.55, 0.22, 0.22), tarde), NOCHE_HORIZONTE, noche);
    vec3 md = mix(mix(vec3(0.78, 0.36, 0.38), vec3(0.22, 0.10, 0.24), tarde), vec3(0.012, 0.020, 0.050), noche);
    vec3 ar = mix(mix(vec3(0.16, 0.16, 0.36), vec3(0.04, 0.05, 0.13), tarde), NOCHE_ARRIBA, noche);

    vec3 col = p.y > HY ? cielo(p, sol, radio, colSol, solVis, hz, md, ar, noche)
             : p.y > ORILLA ? mar(p, hz, colSol, solVis, noche) : arena(p, hz, noche);
    col += (hz * 1.2 + colSol * 0.25 * solVis) * exp(-abs(p.y - HY) / 0.008) * 0.35;   // bruma del horizonte

    // el humo del escenario, iluminado; los haces, los laseres y los fuegos
    float lavado = exp(-length((p - vec2(0.0, PISO + 0.05)) * vec2(0.7, 1.6)) / 0.15);
    col += uLuces * lavado * (0.05 + 0.40 * noche) * (0.5 + 0.5 * uCuerpo);
    col += haces(p, noche) + laseres(p, px, noche) + fuegos(p, noche);

    // a contraluz: las siluetas del fondo se pierden en la bruma; el borde de arriba agarra la luz
    vec3 bruma = mix(hz * 0.30 + colSol * 0.08 * solVis, NOCHE_HORIZONTE * 0.8 + uLuces * 0.06, noche);
    vec3 contraluz = mix(colSol * 0.9 * solVis + hz * 0.45, uLuces * 0.8, noche);

    col = mix(col, mix(bruma, SILUETA, 0.55), cubre(min(palmera(p, vec2(-0.52, -0.115), vec2(-0.55, 0.10), 0.5, 3.0, px),
                                                     palmera(p, vec2(0.50, -0.115), vec2(0.52, 0.075), 0.42, 7.0, px)), px));
    float led, cabezal;
    float dc = cabina(p, led, cabezal);
    col = mix(col, mix(bruma, SILUETA, 0.8), cubre(dc, px));
    col = mix(col, uLuces * (0.6 + 0.4 * uCuerpo), cubre(led, px) * (0.3 + 0.7 * noche));
    col = mix(col, mix(uLuces, vec3(1.0), 0.5), cubre(cabezal, px) * noche * 0.8);

    for (int j = 0; j < int(FILAS); j++) {
        float fj = float(j);
        float pantalla;
        float d = fila(p, fj, pantalla);
        float c = cubre(d, px);
        if (c > 0.0) {
            float S = mix(0.021, 0.125, pow(fj / (FILAS - 1.0), 1.6));
            float pa;
            float borde = smoothstep(-0.3, 0.6, fila(p + vec2(0.0, 0.045 * S), fj, pa) / (0.045 * S));
            float lejos = 1.0 - fj / (FILAS - 1.0);
            // el borde de luz solo en los de adelante: en los chiquitos del fondo los iluminaba enteros
            vec3 sil = mix(SILUETA, bruma, 0.25 * lejos * lejos)
                     + contraluz * borde * (0.22 + 0.15 * noche) * smoothstep(0.015, 0.06, S);
            col = mix(col, sil, c);
            col = mix(col, PANTALLA * 0.9, cubre(pantalla, px));
        }
        col += PANTALLA * exp(-max(pantalla, 0.0) / (0.003 + 0.012 * fj / FILAS)) * 0.10;
    }

    float prende = 0.35 + 0.65 * noche;
    col = mix(col, SILUETA, cubre(min(palmera(p, vec2(-0.70, -0.55), vec2(-0.80, 0.30), 1.0, 1.0, px),
                                      palmera(p, vec2(0.70, -0.55), vec2(0.82, 0.22), 0.95, 5.0, px)), px));
    col = guirnalda(col, p, vec2(-0.80, 0.30), vec2(0.82, 0.22), 0.10, px, prende);
    col = guirnalda(col, p, vec2(-0.95, 0.47), vec2(0.95, 0.50), 0.07, px, prende);
    col = papelitos(col, p, px);

    col *= 1.0 + 0.03 * uBombo;
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
