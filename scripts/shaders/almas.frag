#version 330
// Dos almas: una historia de amor abstracta (el DJ, 2026-10-27). Se conocen, vuelan juntas, se
// separan, una se apaga y se aleja, vuelve y la otra la cura, vuelan otra vez, se alejan, y al
// final se separan brillando las dos.
//
// La coreografia la hace scripts/almas.py; aca se dibuja, con cuatro ideas:
//  - el alma es una luz con cuerpo y vida adentro: nucleo, halo que respira con borde vivo, aura,
//    y un brillo que se mueve por dentro (la calida: corrientes lentas; la fria: destellos finos);
//  - la luz es la emocion: cada alma tine las nubes hasta lejos, el cielo pierde el color cuando una
//    se apaga (uFrio) y lo recupera con la onda de la cura, que se abre y las deja en el centro;
//  - la estela queda en el cielo: juntas trenzan dos hilos, separadas dibujan dos caminos;
//  - el cielo es azul de noche en tres capas con paralaje, la del medio con relieve (borde de
//    arriba claro, de abajo en sombra). Todo es suave por construccion: anda igual en 4K.
// "me encanto" (el DJ, 2026-10-27, sobre la 2a version); esta es la vuelta de pulido. Y "es una
// historia de amor representada": sin simbolos, se cuenta con como se mueven, como se miran
// (uMira) y que le hace la luz de una a la otra.

#define NT 40

uniform vec2 uRes;
uniform float uTime;
uniform vec2 uCam;            // donde mira la camara, en coordenadas del cielo
uniform float uZoom;          // 1 normal, mas = mas cerca, menos = el cielo se abre
uniform vec2 uPosA;           // en pantalla, unidades de alto, (0,0) al centro
uniform vec2 uPosB;
uniform float uLuzA;          // 0 apagada, 1 plena (puede pasar de 1 en la cura)
uniform float uLuzB;
uniform float uTamA;          // escala por profundidad: chica = lejos
uniform float uTamB;
uniform float uRespA;         // respiracion, -1 a 1
uniform float uRespB;
uniform float uVidaA;         // el brillo de adentro; en la apagada, sus intentos de encenderse
uniform float uVidaB;
uniform float uMiraA;         // cuanto se inclina cada una hacia la otra: se miran
uniform float uMiraB;
uniform float uCalorB;        // cuanto de la luz calida de A lleva B
uniform float uGolpe;         // el bombo, 0 a 1, ya atenuado por la historia
uniform float uFondo;         // el grave lento: el cielo respira con la musica
uniform float uFrio;          // el cielo pierde el color cuando una se apaga
uniform float uAlba;          // el horizonte naranja del final
uniform vec3 uOnda;           // la cura: xy centro en pantalla, z segundos desde (negativo = todavia no)
uniform vec3 uToque;          // el primer encuentro: idem
uniform float uDetrasB;       // B esta detras de la capa cercana (0 a 1): la tapa y le enciende el borde
uniform vec3 uBanco;          // el banco de nubes donde B se esconde: centro en pantalla y radio
uniform float uPuente;        // la luz que A le pasa a B en el hueco del drop, 0 a 1
uniform vec3 uEstelaA[NT];    // xy en pantalla, z la luz que tenia; [0] es el presente
uniform vec3 uEstelaB[NT];

out vec4 fragColor;

const vec3 CALIDA = vec3(1.00, 0.52, 0.18);   // el naranja de la marca
const vec3 FRIA = vec3(0.62, 0.80, 1.00);
const vec3 FRIA_LUZ = vec3(0.40, 0.64, 1.00); // lo que la fria le tine a las nubes: azul, no gris
const vec3 GRIS = vec3(0.50, 0.53, 0.60);

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

float ruido(vec2 p) {
    vec2 i = floor(p), f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

float fbm(vec2 p) {
    float v = 0.0, a = 0.5;
    for (int i = 0; i < 5; i++) { v += a * ruido(p); p = p * 2.03 + vec2(1.7, 9.2); a *= 0.5; }
    return v;
}

// nubes blandas: fbm con el dominio torcido, para que no parezcan manchas de ruido
float nube(vec2 q, float cobertura) {
    vec2 w = vec2(fbm(q * 0.6 + 3.1), fbm(q * 0.6 + 7.7));
    return smoothstep(cobertura, cobertura + 0.30, fbm(q + 1.2 * w));
}

vec3 colorB() { return mix(FRIA, CALIDA, uCalorB); }

// cuanto llega a p la luz de cada alma (x: A, y: B): llega lejos y cerca no quema
vec2 alcance(vec2 p, float caida) {
    vec2 da = p - uPosA, db = p - uPosB;
    return vec2(uLuzA * uTamA * uTamA / (dot(da, da) * caida + 0.5),
                uLuzB * uTamB * uTamB / (dot(db, db) * caida + 0.5));
}

vec3 colorLuzB() { return mix(GRIS * 0.4, mix(FRIA_LUZ, CALIDA, uCalorB), smoothstep(0.05, 0.6, uLuzB)); }

vec3 luzEntorno(vec2 p, float caida) {
    vec2 l = alcance(p, caida);
    return CALIDA * l.x + colorLuzB() * l.y;
}

// la capa de nubes de adelante (x: densidad, y: cuanto tapa). Lleva el banco donde se esconde B,
// fijo en esta capa: pasa con su paralaje como cualquier nube
vec2 capaCerca(vec2 p) {
    float zc = mix(1.0, uZoom, 1.4);
    vec2 w = p / zc + uCam * 1.7;
    // el banco no es una forma aparte: es la misma nube, mas espesa alrededor de ese lugar
    float banco = smoothstep(1.0, 0.2, length((p - uBanco.xy) / uBanco.z * vec2(0.8, 1.6)));
    float n = nube(w * vec2(1.1, 2.4) + vec2(uTime * 0.02, 11.0), 0.55 - 0.30 * banco);
    return vec2(n, n * mix(0.5, 0.8, banco));
}

// una onda que se abre desde las dos: nace sin fogonazo y enciende solo lo que va cruzando
float onda(vec2 p, vec3 o, float velocidad, float vida) {
    if (o.z < 0.0) return 0.0;
    float r = 0.06 + o.z * velocidad;
    float ancho = 0.03 + 0.07 * o.z;
    float d = (length(p - o.xy) - r) / ancho;
    return exp(-d * d) * exp(-o.z / vida) * smoothstep(0.0, 0.25, o.z);
}

// recien abierta la onda, adentro la luz de las nubes baja: la onda se lleva el brillo hacia afuera
// y las deja a ellas dos solas en el centro, sin fogonazo
float hueco(vec2 p) {
    if (uOnda.z < 0.0) return 0.0;
    float r = 0.06 + uOnda.z * 0.70;
    return smoothstep(r, r * 0.4, length(p - uOnda.xy)) * exp(-uOnda.z / 1.2);
}

vec3 cielo(vec2 p, vec2 capa) {
    // el aire: azul de noche, mas claro abajo
    vec3 c = mix(vec3(0.030, 0.050, 0.125), vec3(0.006, 0.011, 0.038), smoothstep(-0.55, 0.55, p.y));
    // estrellas, lejos: puntos blandos en su celda (en 4K los cuadraditos se veian)
    vec2 qe = (p / mix(1.0, uZoom, 0.1) + uCam * 0.06) * 210.0;
    vec2 g = floor(qe);
    vec2 de = qe - g - 0.25 - 0.5 * vec2(hash(g + 7.0), hash(g + 13.0));
    float est = step(0.9972, hash(g)) * (0.55 + 0.45 * sin(uTime * 0.9 + hash(g + 3.0) * 6.28));
    c += vec3(0.75, 0.82, 1.0) * est * exp(-dot(de, de) * 25.0) * 0.45 * smoothstep(-0.3, 0.2, p.y);

    float queda = 1.0 - 0.75 * hueco(p);
    vec3 luzLejos = luzEntorno(p, 3.0) * 0.10 * queda;
    vec3 luzCerca = luzEntorno(p, 8.0) * 0.30 * queda;
    float o = onda(p, uOnda, 0.70, 1.6);
    float t = onda(p, uToque, 0.30, 0.9) * 0.45;
    vec3 luzOnda = mix(CALIDA, FRIA_LUZ, 0.4) * (o + t);

    // tres capas de nubes, cada una con su paralaje: lejos, a la altura de las almas, y delante
    float zl = mix(1.0, uZoom, 0.35), zm = uZoom;
    float lejos = nube((p / zl + uCam * 0.30) * vec2(1.8, 2.6) + vec2(uTime * 0.008, 0.0), 0.42);
    vec2 qm = (p / zm + uCam) * vec2(2.2, 3.4) + vec2(uTime * 0.015, 4.0);
    float medio = nube(qm, 0.45);
    // la luz desde cada alma (Quilez, derivada direccional): la densidad aca contra la de un paso
    // hacia el alma. Si hacia ella hay menos nube, este borde la mira y se enciende; el borde
    // encendido gira cuando el alma pasa
    vec2 escala = vec2(2.2, 3.4) / zm;
    float difA = clamp((medio - nube(qm + normalize(uPosA - p + 1e-4) * 0.05 * escala, 0.45)) * 3.0, 0.0, 1.0);
    float difB = clamp((medio - nube(qm + normalize(uPosB - p + 1e-4) * 0.05 * escala, 0.45)) * 3.0, 0.0, 1.0);
    vec2 llega = alcance(p, 8.0) * 0.30 * queda;
    vec3 luzMedio = CALIDA * llega.x * (0.35 + 1.5 * difA) + colorLuzB() * llega.y * (0.35 + 1.5 * difB);

    vec3 azul = vec3(0.045, 0.070, 0.160) * uFondo;              // nube de noche: azul, no gris
    // lejos: mas clara, mas azul y sin contraste, como con aire de por medio
    c = mix(c, vec3(0.050, 0.078, 0.170) * 0.85 * uFondo + luzLejos + luzOnda * 0.35, lejos * 0.55);
    float masa = mix(1.05, 0.70, smoothstep(0.5, 1.0, medio));   // el centro denso, mas oscuro
    c = mix(c, azul * masa + luzMedio + luzOnda * 0.9, medio * 0.85);
    c = mix(c, vec3(0.010, 0.016, 0.040) + luzCerca * 0.40, capa.y);
    c += luzOnda * 0.08;                                    // el anillo, apenas, en el aire

    // el alba del final: el horizonte naranja de la marca, abajo del cuadro
    float h = p.y + 0.62;
    c += uAlba * (CALIDA * 0.38 * exp(-max(h, 0.0) * 5.5) + vec3(0.10, 0.06, 0.10) * exp(-max(h, 0.0) * 2.0) * 0.5);

    // cuando una se apaga el cielo pierde el color y baja
    float gris = dot(c, vec3(0.30, 0.55, 0.15));
    return mix(c, vec3(gris) * vec3(0.80, 0.86, 1.0) * 0.80, uFrio * 0.9);
}

// el borde plateado: con la luz detras, lo fino de la nube se enciende (como Henyey-Greenstein
// hacia adelante). Solo alrededor de B, cuando esta detras de la capa cercana
vec3 plateado(vec2 p, float n) {
    if (uDetrasB <= 0.0) return vec3(0.0);
    vec2 d = (p - uPosB) / max(uTamB, 0.3);
    float junto = exp(-dot(d, d) * 30.0);
    float fino = smoothstep(0.05, 0.30, n) * (1.0 - smoothstep(0.35, 0.85, n));
    vec3 col = mix(GRIS, colorB(), smoothstep(0.05, 0.6, uLuzB));
    return col * uLuzB * uDetrasB * junto * fino * 2.5;
}

// la estela: el camino que hizo en los ultimos segundos, fino y vivo cerca, ancho y tenue lejos
vec3 estela(vec2 p, int cual, vec3 col, float tam) {
    float mejor = 0.0;
    for (int i = 0; i < NT - 1; i++) {
        vec3 e0 = cual == 0 ? uEstelaA[i] : uEstelaB[i];
        vec3 e1 = cual == 0 ? uEstelaA[i + 1] : uEstelaB[i + 1];
        vec2 pa = p - e0.xy, ba = e1.xy - e0.xy;
        float h = clamp(dot(pa, ba) / max(dot(ba, ba), 1e-8), 0.0, 1.0);
        float d = length(pa - ba * h);
        float edad = (float(i) + h) / float(NT - 1);
        float ancho = mix(0.0030, 0.0140, edad) * tam;
        float luz = mix(e0.z, e1.z, h);
        float v = exp(-d * d / (ancho * ancho)) * pow(1.0 - edad, 1.6) * luz * (0.0035 / ancho);
        mejor = max(mejor, v);
    }
    return col * mejor * 0.75 + vec3(1.0) * mejor * mejor * 0.12;
}

// el puente: un hilo de luz de A a B, con pulsos que viajan hacia B
vec3 puente(vec2 p) {
    if (uPuente <= 0.0) return vec3(0.0);
    vec2 ba = uPosB - uPosA, pa = p - uPosA;
    float h = clamp(dot(pa, ba) / max(dot(ba, ba), 1e-8), 0.0, 1.0);
    float d = length(pa - ba * h);
    float flujo = 0.55 + 0.45 * sin(h * 18.0 - uTime * 14.0);
    float ancho = 0.0040;
    return mix(CALIDA, vec3(1.0), 0.3) * exp(-d * d / (ancho * ancho)) * flujo * uPuente
         + CALIDA * exp(-d * d / (16.0 * ancho * ancho)) * uPuente * 0.12;
}

// adentro: un brillo que se mueve. giro = vueltas y sentido, grano = tamano de las corrientes,
// titila = cuanto parpadea la chispa (la fria titila, la calida no)
vec3 adentro(vec2 d, float r, vec3 col, float vida, float giro, float grano, float titila, float semilla) {
    if (r > 0.07 || vida <= 0.01) return vec3(0.0);
    float a = uTime * giro;
    vec2 q = mat2(cos(a), -sin(a), sin(a), cos(a)) * d / 0.032;
    float f = fbm(q * grano + vec2(semilla, -uTime * 0.7 * abs(giro)));
    float corriente = smoothstep(0.48, 0.85, f) * exp(-r * r / (0.030 * 0.030));
    vec2 c1 = 0.014 * vec2(cos(uTime * giro * 1.7 + semilla), sin(uTime * giro * 1.3 + semilla * 2.0));
    float chispa = exp(-dot(d - c1, d - c1) * 9000.0) * (1.0 - titila + titila * (0.5 + 0.5 * sin(uTime * 7.0 + semilla)));
    return (mix(col, vec3(1.0), 0.4) * corriente * 0.9 + vec3(1.0) * chispa * 0.55) * vida;
}

// otra, colOtra, luzOtra: la otra alma. mira: cuanto se inclina hacia ella (0 a 1); su halo se corre
// y su aura se estira de ese lado. Y la luz de la otra le tine el borde que la enfrenta, mas cuanto
// mas cerca estan: es lo que una le hace a la otra (en la cura, la calida entibia a la apagada)
vec3 alma(vec2 p, vec2 c, vec3 col, float luz, float tam, float resp, float vida,
          float giro, float grano, float titila, float semilla,
          vec2 otra, vec3 colOtra, float luzOtra, float mira) {
    vec2 hacia = otra - c;
    float dist = length(hacia);
    hacia /= max(dist, 1e-4);
    vec2 d = (p - c) / tam;
    float r = length(d);
    float frente = max(dot(d / max(r, 1e-4), hacia), 0.0);
    float s = 1.0 + 0.10 * resp + 0.06 * uGolpe;
    // el borde del halo se mueve, apenas: esta vivo
    float borde = 1.0 + 0.22 * (ruido(d / max(r, 1e-4) * 1.4 + vec2(uTime * 0.35, semilla)) - 0.5);
    float rh = length(d - hacia * 0.010 * mira) / (s * borde * (1.0 + 0.12 * mira * frente));
    float nucleo = exp(-r * r * 12000.0 / (s * s));
    float halo = exp(-rh * rh * 500.0);
    float aura = 0.0028 / (r + 0.014) * (1.0 + 0.6 * mira * frente);
    float toca = luzOtra / (1.0 + dist * dist * 25.0) * frente;
    vec3 tinte = mix(GRIS, col, smoothstep(0.04, 0.6, luz));
    return vec3(1.0, 0.97, 0.94) * nucleo * mix(0.45, 1.7, luz)
         + tinte * halo * mix(0.16, 0.95, luz)
         + tinte * aura * luz * 0.55
         + colOtra * toca * exp(-r * r * 300.0) * 0.6
         + adentro(d, r, col, vida, giro, grano, titila, semilla);   // su color, aunque este gris
}

void main() {
    vec2 p = (gl_FragCoord.xy - 0.5 * uRes) / uRes.y;
    vec2 capa = capaCerca(p);
    vec3 c = cielo(p, capa);
    // B detras de la capa cercana: la nube la tapa (Beer) y le enciende el borde
    float pasa = mix(1.0, exp(-3.0 * capa.x), uDetrasB);
    vec3 a = estela(p, 0, CALIDA, uTamA)
           + alma(p, uPosA, CALIDA, uLuzA, uTamA, uRespA, uVidaA, -0.35, 1.6, 0.0, 0.0, uPosB, colorB(), uLuzB, uMiraA);
    vec3 b = estela(p, 1, mix(GRIS, colorB(), smoothstep(0.05, 0.6, uLuzB)), uTamB)
           + alma(p, uPosB, colorB(), uLuzB, uTamB, uRespB, uVidaB, 0.9, 3.0, 1.0, 17.0, uPosA, CALIDA, uLuzA, uMiraB);
    c += a + b * pasa + puente(p) + plateado(p, capa.x);
    c = 1.0 - exp(-c * 1.5);                       // sin quemar: las luces llegan a blanco suave
    c *= 1.0 - 0.38 * dot(p * 0.9, p * 0.9);       // vineta: el ojo va al centro
    c += (hash(gl_FragCoord.xy + fract(uTime) * 91.0) - 0.5) / 255.0;   // sin escalones en el negro
    fragColor = vec4(c, 1.0);
}
