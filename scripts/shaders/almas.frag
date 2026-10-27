#version 330
// Dos almas: una historia de amor abstracta (el DJ, 2026-10-27). Se conocen, vuelan juntas, se
// separan, una se apaga y se aleja, vuelve y la otra la cura, vuelan otra vez, se alejan, y al
// final se separan brillando las dos.
//
// 2a version (tras "la idea esta pero esta mal lograda"). La coreografia la hace scripts/almas.py;
// aca se dibuja, con tres ideas:
//  - el alma es una luz con cuerpo: nucleo, halo que respira con borde vivo, y aura que tine el aire;
//  - la luz es la emocion: cada alma enciende las nubes que tiene cerca, el cielo pierde el color
//    cuando una se apaga (uFrio) y lo recupera con la onda de la cura;
//  - la estela queda en el cielo (puntos de la trayectoria, no una raya recta): juntas trenzan dos
//    hilos, separadas dibujan dos caminos.

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
uniform float uCalorB;        // cuanto de la luz calida de A lleva B
uniform float uGolpe;         // el bombo, 0 a 1, ya atenuado por la historia
uniform float uFondo;         // el grave lento: el cielo respira con la musica
uniform float uFrio;          // el cielo pierde el color cuando una se apaga
uniform float uAlba;          // el horizonte naranja del final
uniform vec3 uOnda;           // la cura: xy centro en pantalla, z segundos desde (negativo = todavia no)
uniform vec3 uToque;          // el primer encuentro: idem
uniform float uPuente;        // la luz que A le pasa a B en el hueco del drop, 0 a 1
uniform vec3 uEstelaA[NT];    // xy en pantalla, z la luz que tenia; [0] es el presente
uniform vec3 uEstelaB[NT];

out vec4 fragColor;

const vec3 CALIDA = vec3(1.00, 0.52, 0.18);   // el naranja de la marca
const vec3 FRIA = vec3(0.62, 0.80, 1.00);
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

// la luz que cada alma le tira al entorno en el punto p (inversa del cuadrado, ablandada)
vec3 luzEntorno(vec2 p, float blando) {
    vec2 da = p - uPosA, db = p - uPosB;
    float la = uLuzA * uTamA * uTamA / (dot(da, da) * 20.0 + blando);
    float lb = uLuzB * uTamB * uTamB / (dot(db, db) * 20.0 + blando);
    return CALIDA * la + mix(GRIS * 0.4, colorB(), smoothstep(0.05, 0.6, uLuzB)) * lb;
}

// la onda de la cura: un anillo que sale de las dos y enciende las nubes que cruza
float onda(vec2 p, vec3 o, float velocidad, float vida) {
    if (o.z < 0.0) return 0.0;
    float r = o.z * velocidad;
    float ancho = 0.04 + 0.10 * o.z;
    float d = (length(p - o.xy) - r) / ancho;
    return exp(-d * d) * exp(-o.z / vida);
}

vec3 cielo(vec2 p) {
    // el aire: azul de noche, mas claro abajo
    vec3 c = mix(vec3(0.036, 0.046, 0.096), vec3(0.008, 0.012, 0.032), smoothstep(-0.55, 0.55, p.y));
    // estrellas, lejos: casi no se mueven
    vec2 qe = p / mix(1.0, uZoom, 0.1) + uCam * 0.06;
    vec2 g = floor(qe * 210.0);
    float est = step(0.9972, hash(g)) * (0.55 + 0.45 * sin(uTime * 0.9 + hash(g + 3.0) * 6.28));
    c += vec3(0.75, 0.8, 1.0) * est * 0.32 * smoothstep(-0.3, 0.2, p.y);

    vec3 luzLejos = luzEntorno(p, 0.60) * 0.12;
    vec3 luzCerca = luzEntorno(p, 0.25) * 0.30;
    float o = onda(p, uOnda, 0.55, 2.2);
    float t = onda(p, uToque, 0.30, 0.9) * 0.45;
    vec3 luzOnda = mix(CALIDA, FRIA, 0.45) * (o + t);

    // tres capas de nubes, cada una con su paralaje: lejos, a la altura de las almas, y delante
    float zl = mix(1.0, uZoom, 0.35), zm = uZoom, zc = mix(1.0, uZoom, 1.4);
    float lejos = nube((p / zl + uCam * 0.30) * vec2(1.8, 2.6) + vec2(uTime * 0.008, 0.0), 0.42);
    vec2 qm = (p / zm + uCam) * vec2(2.2, 3.4) + vec2(uTime * 0.015, 4.0);
    float medio = nube(qm, 0.45);
    float arriba = medio - nube(qm + vec2(0.0, 0.10), 0.45);   // el borde de arriba, mas claro
    float cerca = nube((p / zc + uCam * 1.7) * vec2(1.1, 2.4) + vec2(uTime * 0.02, 11.0), 0.55);

    vec3 base = vec3(0.060, 0.075, 0.130) * uFondo;
    c = mix(c, base * 0.7 + luzLejos + luzOnda * 0.35, lejos * 0.60);
    c = mix(c, base * (0.85 + 0.6 * max(arriba, 0.0)) + luzCerca * (1.0 + max(arriba, 0.0)) + luzOnda * 0.75, medio * 0.85);
    c = mix(c, vec3(0.014, 0.018, 0.036) + luzCerca * 0.25, cerca * 0.50);
    c += luzOnda * 0.08;                                    // el anillo, apenas, en el aire

    // el alba del final: el horizonte naranja de la marca, abajo del cuadro
    float h = p.y + 0.62;
    c += uAlba * (CALIDA * 0.38 * exp(-max(h, 0.0) * 5.5) + vec3(0.10, 0.06, 0.10) * exp(-max(h, 0.0) * 2.0) * 0.5);

    // cuando una se apaga el cielo pierde el color y baja
    float gris = dot(c, vec3(0.30, 0.55, 0.15));
    return mix(c, vec3(gris) * vec3(0.80, 0.86, 1.0) * 0.80, uFrio * 0.9);
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

vec3 alma(vec2 p, vec2 c, vec3 col, float luz, float tam, float resp, float semilla) {
    vec2 d = (p - c) / tam;
    float r = length(d);
    float s = 1.0 + 0.10 * resp + 0.06 * uGolpe;
    // el borde del halo se mueve, apenas: esta vivo
    float borde = 1.0 + 0.22 * (ruido(d / max(r, 1e-4) * 1.4 + vec2(uTime * 0.35, semilla)) - 0.5);
    float rh = r / (s * borde);
    float nucleo = exp(-r * r * 7000.0 / (s * s));
    float halo = exp(-rh * rh * 500.0);
    float aura = 0.0028 / (r + 0.014);
    float viva = smoothstep(0.04, 0.6, luz);
    vec3 tinte = mix(GRIS, col, viva);
    return vec3(1.0, 0.97, 0.94) * nucleo * mix(0.45, 1.7, luz)
         + tinte * halo * mix(0.16, 0.95, luz)
         + tinte * aura * luz * 0.55;
}

void main() {
    vec2 p = (gl_FragCoord.xy - 0.5 * uRes) / uRes.y;
    vec3 c = cielo(p);
    c += estela(p, 0, CALIDA, uTamA) + estela(p, 1, mix(GRIS, colorB(), smoothstep(0.05, 0.6, uLuzB)), uTamB);
    c += puente(p);
    c += alma(p, uPosA, CALIDA, uLuzA, uTamA, uRespA, 0.0) + alma(p, uPosB, colorB(), uLuzB, uTamB, uRespB, 17.0);
    c = 1.0 - exp(-c * 1.5);                       // sin quemar: las luces llegan a blanco suave
    c *= 1.0 - 0.38 * dot(p * 0.9, p * 0.9);       // vineta: el ojo va al centro
    c += (hash(gl_FragCoord.xy + fract(uTime) * 91.0) - 0.5) / 255.0;   // sin escalones en el negro
    fragColor = vec4(c, 1.0);
}
