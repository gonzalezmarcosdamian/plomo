#version 330
// Vuelo: la camara vuela de noche sobre dunas hacia un horizonte encendido. El look de la Session 03.
// No reacciona al volumen: sabe la forma de cada tema (video_animar.camara mira 1.2 s adelante).
// En el breakdown sube, frena y se abre el cielo; en el drop baja en picada, acelera y el
// horizonte se enciende. El bombo hace latir las curvas de nivel. Nada de flashes.

uniform vec2 uRes;
uniform float uTime;
uniform float uAltura;     // 1 en el breakdown, 0 en el groove
uniform float uDistancia;  // cuanto se avanzo: la integral de la velocidad
uniform float uImpacto;    // el golpe del drop, que se apaga en unos segundos
uniform float uBombo;
uniform float uBajo;
uniform float uCuerpo;
uniform float uAire;
uniform float uChispa;
uniform vec3 uCieloAlto;
uniform vec3 uHorizonte;
uniform vec3 uAcento;
uniform vec2 uDeriva;
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

// dunas: crestas suaves, mas finas cuanto mas agudos tiene el tema
float terreno(vec2 p) {
    float h = 0.0, a = 0.55;
    vec2 q = p * 0.16 + uDeriva * 3.0;
    mat2 r = mat2(0.8, 0.6, -0.6, 0.8);
    for (int i = 0; i < 4; i++) {
        float n = 1.0 - abs(2.0 * ruido(q) - 1.0);
        h += a * n * n * (i < 2 ? 1.0 : 0.4 + 0.6 * uAire);
        q = r * q * 2.03 + 11.0;
        a *= 0.42;
    }
    return h * 1.5;
}

vec3 cielo(vec3 rd) {
    float y = rd.y;
    vec3 c = mix(uHorizonte * 0.30, uCieloAlto, smoothstep(-0.02, 0.40, y));
    // el sol bajo del horizonte: se agranda con el bajo y se enciende en el drop
    float sol = exp(-length(vec2(rd.x, (y - 0.015) * 2.6)) / (0.09 + 0.05 * uBajo + 0.10 * uImpacto));
    c += uHorizonte * sol * (0.55 + 0.35 * uCuerpo + 1.3 * uImpacto);
    c += uHorizonte * exp(-abs(y) / 0.045) * (0.25 + 0.25 * uCuerpo + 0.7 * uImpacto);
    // estrellas: aparecen cuando la camara sube en el breakdown, titilan con los hats
    vec2 e = vec2(atan(rd.x, rd.z), y) * 140.0;
    vec2 c0 = floor(e);
    float r = hash(c0 + 4.3);
    float punto = exp(-dot(e - c0 - 0.5, e - c0 - 0.5) * 9.0);
    float hay = step(0.982, r) * smoothstep(0.06, 0.30, y);
    punto = pow(punto, 2.5);
    c += vec3(0.85, 0.9, 1.0) * hay * punto * (0.10 + 0.80 * uAltura) * (0.6 + 0.4 * uChispa);
    return c;
}

void main() {
    // la fila 0 del framebuffer es la de ARRIBA del video (ver atardecer.frag): se da vuelta y
    vec2 frag = gl_FragCoord.xy;
    vec2 uv = frag / uRes;
    vec2 p = (vec2(frag.x, uRes.y - frag.y) - 0.5 * uRes) / uRes.y;

    // la camara: alta y mirando al horizonte en el breakdown, a ras y mirando abajo en el drop
    float alto = mix(1.55, 3.6, uAltura);
    float inclina = 0.025 * sin(uDistancia * 0.11);
    p = mat2(cos(inclina), -sin(inclina), sin(inclina), cos(inclina)) * p;
    vec3 ro = vec3(sin(uDistancia * 0.045) * 4.0, alto, uDistancia * 5.0);
    vec3 rd = normalize(vec3(p.x, p.y + mix(-0.26, 0.03, uAltura), 1.35));

    float t = 0.2;
    float golpe = 1.0;   // si se acaban los pasos sin llegar al cielo, es suelo: si no, quedan huecos lejos
    // hasta 150: a 70 el terreno terminaba en una linea dura bajo el horizonte; a 150 la niebla ya lo borro
    for (int i = 0; i < 180; i++) {
        vec3 q = ro + rd * t;
        float d = q.y - terreno(q.xz);
        if (d < 0.002 * t) break;
        t += max(0.012, d * 0.5);
        if (t > 150.0) { golpe = 0.0; break; }
    }
    vec3 pos = ro + rd * t;
    float h = terreno(pos.xz);
    float e = 0.05;
    vec3 n = normalize(vec3(terreno(pos.xz - vec2(e, 0.0)) - terreno(pos.xz + vec2(e, 0.0)), 2.0 * e,
                            terreno(pos.xz - vec2(0.0, e)) - terreno(pos.xz + vec2(0.0, e))));

    // las dunas: oscuras, iluminadas de frente por el horizonte, con el borde encendido
    vec3 luz = normalize(vec3(0.0, 0.22, 1.0));
    float dif = clamp(dot(n, luz), 0.0, 1.0);
    float borde = pow(1.0 - clamp(dot(n, -rd), 0.0, 1.0), 4.0);
    vec3 suelo = uCieloAlto * 0.3 + uHorizonte * (0.05 + 0.34 * dif * dif + 0.10 * borde) * (0.45 + 0.55 * uCuerpo);
    // curvas de nivel: laten con el bombo y se apagan con la distancia. Sobre una silueta
    // fwidth se dispara y dibujaba un borde blanco ruidoso: ahi no se dibujan.
    float k = h * 7.0;
    float w = fwidth(k) + 1e-4;
    float linea = (1.0 - clamp(abs(fract(k) - 0.5) / w - 0.5, 0.0, 1.0)) * (1.0 - smoothstep(0.08, 0.3, w));
    suelo += uAcento * linea * (0.06 + 0.50 * uBombo) * exp(-t * 0.06);
    // niebla hacia el color del horizonte
    vec3 lejos = cielo(normalize(vec3(rd.x, 0.0, rd.z)));
    suelo = mix(suelo, lejos, 1.0 - exp(-t * 0.05));

    vec3 col = mix(cielo(rd), suelo, golpe);
    col *= 1.0 + 0.04 * uBombo;
    // vineta
    col *= mix(0.70, 1.0, smoothstep(1.15, 0.30, length(p * vec2(0.85, 1.25))));
    // compresion suave de altas luces
    col = 1.0 - exp(-col * 1.3);

    // texto del tema (alfa recto)
    vec4 tx = texture(uTexto, uv);
    col = mix(col, tx.rgb, tx.a * uTextoAlfa);

    // grano: rompe los escalones que YouTube le hace a los degrades oscuros
    col += (hash(frag + fract(uTime * 7.13) * 91.0) - 0.5) * (2.0 / 255.0);
    fragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
}
