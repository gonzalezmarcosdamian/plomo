#version 330
// Vuelo: la camara vuela sobre paisajes hacia el sol bajo. El look de la Session 03.
// "Me encanto el concepto" / "podemos darle mas realismo, no solo las arenas" (el DJ, 2026-10-19).
// Cada tema es un paisaje --montanas con nieve, costa con islas, dunas, mar de nubes-- y una hora
// del dia; en el blend un paisaje se funde en el otro. La forma de cada tema la sabe
// video_animar.camara mirando 1.2 s adelante: en el breakdown la camara sube, frena y se abre el
// cielo; en el drop baja en picada, acelera y el sol se enciende. Nada de flashes.
// La luz se calcula en lineal --sol con sombra, cielo, rebote, bruma que agarra el color del sol--
// y se lleva a pantalla con una curva filmica.

uniform vec2 uRes;
uniform float uTime;
uniform float uAltura;      // 1 en el breakdown, 0 en el groove
uniform float uDistancia;   // la integral de la velocidad: mueve las nubes altas
uniform float uImpacto;     // el golpe del drop, que se apaga en unos segundos
uniform float uBombo;
uniform float uCuerpo;
uniform float uChispa;
uniform vec3 uCieloAlto;    // cenit
uniform vec3 uHorizonte;
uniform vec3 uAcento;       // el sol
uniform float uBiomaA;      // 0 montanas, 1 costa, 2 dunas, 3 mar de nubes
uniform float uBiomaB;
uniform float uSemillaA;    // el tema: dos temas con el mismo paisaje no son el mismo lugar
uniform float uSemillaB;
uniform float uLocalA;      // cuanto se volo desde que empezo a sonar cada tema
uniform float uLocalB;
uniform float uMezclaBioma;
uniform sampler2D uTexto;
uniform float uTextoAlfa;

out vec4 fragColor;

const vec3 SOL = normalize(vec3(0.12, 0.09, 1.0));   // bajo y adelante: siempre se vuela hacia el
const mat2 GIRO = mat2(1.6, -1.2, 1.2, 1.6);

vec3 lin(vec3 c) { return pow(c, vec3(2.2)); }

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

float cumulos(vec2 p, int oct) {
    float h = 0.0, a = 0.6;
    for (int i = 0; i < 6; i++) {
        if (i >= oct) break;
        h += a * ruidoD(p).x;
        a *= 0.48;
        p = GIRO * p + 5.3;
    }
    return smoothstep(0.35, 1.0, h);
}

float crudo(int b, vec2 q, int oct) {
    if (b == 0) return 10.0 * montana(q * 0.022, oct) - 1.5;
    if (b == 1) return 6.0 * montana(q * 0.03 + 3.7, oct) - 4.0;
    if (b == 2) return 2.4 * dunas(q * 0.13, oct);
    return 2.6 * cumulos(q * 0.06, oct);
}

// en la costa el mar es el piso, en 0
float altura(int b, vec2 q, int oct) {
    float h = crudo(b, q, oct);
    return b == 1 ? max(h, 0.0) : h;
}

vec3 cielo(vec3 rd) {
    float y = max(rd.y, 0.0);
    vec3 c = mix(lin(uHorizonte) * 0.8, lin(uCieloAlto), pow(y, 0.40));
    float s = max(dot(rd, SOL), 0.0);
    vec3 sol = lin(uAcento);
    float fuerza = 1.0 + 1.4 * uImpacto + 0.4 * uCuerpo;
    c += sol * (0.20 * pow(s, 3.0) + 0.6 * pow(s, 14.0)) * fuerza;
    c += sol * 14.0 * smoothstep(0.99985, 0.99993, s);
    // nubes altas: una capa lejana que agarra el sol de costado
    if (rd.y > 0.01) {
        vec2 cp = rd.xz / rd.y * 0.012 + vec2(0.0, uDistancia * 0.004);
        float n = 0.0, a = 0.5;
        for (int i = 0; i < 5; i++) {
            n += a * ruidoD(cp).x;
            cp = GIRO * cp;
            a *= 0.5;
        }
        float dens = smoothstep(0.50, 0.85, n) * smoothstep(0.01, 0.12, rd.y);
        vec3 nube = mix(lin(uHorizonte) * 0.7, sol * 1.4, pow(s, 4.0)) + lin(uCieloAlto) * 0.2;
        c = mix(c, nube, dens * 0.85);
    }
    // estrellas: solo con cielo de noche, mas cuando la camara sube en el breakdown
    float noche = 1.0 - smoothstep(0.02, 0.10, dot(uCieloAlto, vec3(0.333)));
    vec2 e = vec2(atan(rd.x, rd.z), rd.y) * 140.0;
    vec2 c0 = floor(e);
    float r = hash(c0 + 4.3);
    float punto = pow(exp(-dot(e - c0 - 0.5, e - c0 - 0.5) * 9.0), 2.5);
    c += vec3(0.8) * step(0.982, r) * punto * smoothstep(0.06, 0.3, rd.y) * noche * (0.3 + 0.7 * uAltura)
         * (0.6 + 0.4 * uChispa);
    return c;
}

float sombraSuave(int b, vec2 sem, vec3 ro) {
    float res = 1.0, t = 0.2;
    for (int i = 0; i < 28; i++) {
        vec3 q = ro + SOL * t;
        float h = q.y - altura(b, q.xz + sem, 4);
        res = min(res, 10.0 * h / t);
        t += clamp(h, 0.3, 4.0);
        if (res < 0.01 || t > 60.0) break;
    }
    return clamp(res, 0.0, 1.0);
}

vec3 escena(int b, float semilla, float local, vec2 p) {
    vec2 sem = vec2(mod(semilla * 137.13, 997.0), mod(semilla * 71.37, 991.0));
    float z = local * 5.0;
    vec2 piso = vec2(sin(z * 0.009) * 6.0, z);
    // la camara pasa por encima de lo que viene adelante, no de lo que tiene abajo
    float suelo = 0.0;
    for (int k = 0; k < 8; k++) suelo = max(suelo, altura(b, piso + sem + vec2(0.0, float(k) * 5.0), 3));
    float escala = b == 0 ? 2.2 : (b == 1 ? 1.6 : 1.0);
    vec3 ro = vec3(piso.x, suelo + escala * mix(1.3, 4.5, uAltura) - 0.04 * uBombo, piso.y);
    float giro = cos(z * 0.009) * 0.054;
    vec3 rd = normalize(vec3(p.x, p.y + mix(-0.30, 0.02, uAltura), 1.35));
    rd.xz = mat2(cos(giro), -sin(giro), sin(giro), cos(giro)) * rd.xz;

    float t = 0.1;
    bool toco = true;   // si se acaban los pasos sin llegar lejos, es suelo: si no, quedan huecos
    for (int i = 0; i < 200; i++) {
        vec3 q = ro + rd * t;
        float h = q.y - altura(b, q.xz + sem, 5);
        if (h < 0.0015 * t) break;
        t += 0.4 * h;
        if (t > 260.0) { toco = false; break; }
    }
    if (!toco) return cielo(rd);

    vec3 pos = ro + rd * t;
    vec2 w = pos.xz + sem;
    float e = 0.002 * t + 0.01;
    float h0 = altura(b, w, 8);
    vec3 n = normalize(vec3(altura(b, w - vec2(e, 0.0), 8) - altura(b, w + vec2(e, 0.0), 8), 2.0 * e,
                            altura(b, w - vec2(0.0, e), 8) - altura(b, w + vec2(0.0, e), 8)));
    vec3 sol = lin(uAcento) * (1.8 + 1.4 * uImpacto + 0.4 * uCuerpo);
    // la sombra es azulada: la llena el cielo de arriba, no el horizonte
    vec3 amb = lin(uCieloAlto) * 1.2 + lin(uHorizonte) * 0.15;
    float sombra = sombraSuave(b, sem, pos + n * 0.05);
    vec3 col;

    if (b == 1 && crudo(b, w, 5) <= 0.0) {
        // el mar: refleja el cielo y hace un camino de destellos hacia el sol
        // olas finas: con manchas de un metro el agua parecia una meseta de barro
        vec2 ol = ruidoD(w * 3.0 + vec2(0.0, uTime * 0.6)).yz * 0.05 + ruidoD(w * 9.0 - uTime * 0.4).yz * 0.025;
        vec3 nw = normalize(vec3(-ol.x, 1.0, -ol.y));
        vec3 rr = reflect(rd, nw);
        float fres = 0.02 + 0.98 * pow(1.0 - max(dot(nw, -rd), 0.0), 5.0);
        col = lin(vec3(0.01, 0.03, 0.05)) * amb + cielo(rr) * fres
              + sol * pow(max(dot(rr, SOL), 0.0), 300.0) * 4.0 * sombra;
    } else {
        vec3 mat;
        float vario = ruidoD(w * 0.7).x;
        if (b == 0) {
            mat = vec3(0.16, 0.14, 0.12) * (0.8 + 0.4 * vario);
            mat = mix(mat, vec3(0.06, 0.09, 0.04), smoothstep(0.80, 0.90, n.y) * (1.0 - smoothstep(2.5, 4.5, h0)));
            mat = mix(mat, vec3(0.82, 0.85, 0.90), smoothstep(5.0, 5.6, h0 + 1.5 * vario) * smoothstep(0.55, 0.70, n.y));
        } else if (b == 1) {
            mat = vec3(0.18, 0.16, 0.14) * (0.8 + 0.4 * vario);
            mat = mix(mat, vec3(0.07, 0.11, 0.05), smoothstep(0.72, 0.85, n.y));
            mat = mix(mat, vec3(0.50, 0.44, 0.32), 1.0 - smoothstep(0.15, 0.45, h0));
        } else if (b == 2) {
            mat = vec3(0.58, 0.42, 0.27) * (0.88 + 0.12 * vario);
        } else {
            mat = vec3(0.80, 0.82, 0.86);
        }
        float dif = clamp(dot(n, SOL), 0.0, 1.0);
        float rebote = clamp(dot(n, normalize(vec3(-SOL.x, 0.0, -SOL.z))), 0.0, 1.0);
        vec3 luz = sol * dif * sombra + amb * (0.5 + 0.5 * n.y) * 0.45 + sol * rebote * 0.06;
        // el mar de nubes deja pasar la luz por los bordes
        if (b == 3) luz += sol * 0.25 * pow(clamp(dot(rd, SOL), 0.0, 1.0), 4.0);
        col = mat * luz;
    }
    // bruma: lo lejano toma el color del horizonte, y del sol si se mira hacia el
    float densidad = b == 0 ? 0.007 : (b == 1 ? 0.010 : (b == 2 ? 0.012 : 0.008));
    vec3 bruma = lin(mix(uCieloAlto, uHorizonte, 0.6)) * 0.7 + sol * 0.25 * pow(max(dot(rd, SOL), 0.0), 8.0);
    return mix(col, bruma, 1.0 - exp(-t * densidad));
}

void main() {
    // la fila 0 del framebuffer es la de ARRIBA del video (ver atardecer.frag): se da vuelta y
    vec2 frag = gl_FragCoord.xy;
    vec2 uv = frag / uRes;
    vec2 p = (vec2(frag.x, uRes.y - frag.y) - 0.5 * uRes) / uRes.y;

    vec3 col = escena(int(uBiomaA + 0.5), uSemillaA, uLocalA, p);
    if (uMezclaBioma > 0.002) col = mix(col, escena(int(uBiomaB + 0.5), uSemillaB, uLocalB, p), uMezclaBioma);
    col *= 0.85 * (1.0 + 0.04 * uBombo);
    // vineta
    col *= mix(0.72, 1.0, smoothstep(1.15, 0.30, length(p * vec2(0.85, 1.25))));
    // curva filmica y a pantalla
    col = clamp((col * (2.51 * col + 0.03)) / (col * (2.43 * col + 0.59) + 0.14), 0.0, 1.0);
    col = pow(col, vec3(1.0 / 2.2));

    // texto del tema (alfa recto)
    vec4 tx = texture(uTexto, uv);
    col = mix(col, tx.rgb, tx.a * uTextoAlfa);

    // grano: rompe los escalones que YouTube le hace a los degrades oscuros
    col += (hash(frag + fract(uTime * 7.13) * 91.0) - 0.5) * (2.0 / 255.0);
    fragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
}
