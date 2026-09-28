#version 330
// Atardecer: un cielo abstracto que escucha el set.
// La paleta sale del video del telefono de esa misma tarde (video_rasgos.py);
// el movimiento, del audio del master. Nada de flashes: el bombo respira, no parpadea.

uniform vec2 uRes;
uniform float uTime;
uniform vec3 uFondo;
uniform vec3 uCielo;
uniform vec3 uResplandor;
uniform vec3 uBrillo;
uniform float uBombo;     // pulso en la grilla del beat, 0 en los breakdowns
uniform float uBajo;
uniform float uCuerpo;    // loudness de corto plazo: la forma del set
uniform float uAire;      // > 6 kHz: cuando el DJ cierra el filtro, la imagen se ablanda
uniform float uChispa;    // hats y platillos
uniform float uNoche;     // 0 con sol, 1 cuando en el video ya es de noche
uniform vec2 uDeriva;     // el "viento" de cada tema, fundido en los blends
uniform float uAngulo;
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
    vec2 u = f * f * f * (f * (f * 6.0 - 15.0) + 10.0);
    float a = hash(i), b = hash(i + vec2(1, 0)), c = hash(i + vec2(0, 1)), d = hash(i + vec2(1, 1));
    return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

// las octavas altas se escalan con el aire: sin agudos, sin detalle fino
float fbm(vec2 p, float detalle) {
    float v = 0.0, a = 0.5;
    mat2 r = mat2(0.8, 0.6, -0.6, 0.8);
    for (int i = 0; i < 7; i++) {
        float w = i < 3 ? 1.0 : detalle;
        v += a * w * ruido(p);
        p = r * p * 2.02 + 17.0;
        a *= 0.5;
    }
    return v;
}

void main() {
    // la fila 0 del framebuffer es la primera que se lee y la primera que recibe ffmpeg:
    // o sea, la de ARRIBA del video. Con gl_FragCoord tal cual, y crece hacia abajo.
    vec2 frag = gl_FragCoord.xy;
    vec2 uv = frag / uRes;
    vec2 p = (frag - 0.5 * uRes) / uRes.y;
    float t = uTime * 0.035;

    // capas estiradas en horizontal, como el cielo por la ventana
    vec2 q = vec2(p.x * 0.9, p.y * 2.2) * (1.0 + 0.012 * uBombo);
    vec2 flujo = vec2(cos(uAngulo), sin(uAngulo)) * t;
    float detalle = mix(0.12, 1.0, uAire);
    vec2 w1 = vec2(fbm(q * 1.3 + flujo + uDeriva, detalle),
                   fbm(q * 1.3 - flujo + uDeriva + 5.2, detalle));
    vec2 w2 = vec2(fbm(q * 1.1 + 3.0 * w1 + vec2(1.7, 9.2) + 0.6 * t, detalle),
                   fbm(q * 1.1 + 3.0 * w1 + vec2(8.3, 2.8) - 0.4 * t, detalle));
    float f = fbm(q + 2.6 * w2 + uDeriva, detalle);

    // el horizonte sube un poco con la energia, y las nubes lo deforman
    float hy = 0.60 - 0.05 * uCuerpo;
    float y = uv.y + 0.10 * (f - 0.5) + 0.04 * (w2.y - 0.5);

    // cielo: oscuro arriba, el color del cielo cerca del horizonte, modulado por las nubes
    vec3 cielo = mix(uFondo, uCielo, smoothstep(-0.05, hy, y)) * (0.65 + 0.7 * f);
    // abajo: la ciudad en penumbra
    vec3 suelo = uFondo * (0.55 + 0.3 * f);
    vec3 col = mix(cielo, suelo, smoothstep(hy - 0.03, hy + 0.09, y));

    // resplandor del horizonte: ancho con el bajo, intensidad con el cuerpo, respira con el bombo
    float ancho = 0.045 + 0.05 * uBajo + 0.008 * uBombo;
    float g = exp(-pow((y - hy) / ancho, 2.0));
    float fuerza = (0.30 + 0.70 * uCuerpo) * (1.0 + 0.10 * uBombo);
    col += uResplandor * g * fuerza * (0.45 + 0.75 * f);
    // las nubes cerca del horizonte agarran el color del resplandor
    // (un corte de 0.02 aca dibujaba una linea dentada y dura bajo el horizonte)
    float tinte = smoothstep(hy - 0.35, hy, y) * (1.0 - smoothstep(hy - 0.01, hy + 0.09, y));
    col = mix(col, col + uResplandor * 0.35 * f, tinte * (0.4 + 0.6 * uCuerpo));

    // filamentos finos: solo existen si hay agudos
    float hilo = pow(smoothstep(0.55, 0.92, f), 3.0) * uAire * (1.0 - smoothstep(hy - 0.02, hy + 0.06, y));
    col += uBrillo * hilo * 0.30;

    // reflejo del resplandor en la ciudad, continuo a traves del horizonte
    float bajoHorizonte = smoothstep(hy - 0.02, hy + 0.06, y);
    col += uResplandor * g * 0.25 * bajoHorizonte * (1.0 - smoothstep(hy + 0.02, hy + 0.35, y));

    // luces de la ciudad: mas cuanto mas de noche, titilan con los hats
    if (y > hy + 0.02) {
        float celda = uRes.y / 95.0;
        vec2 c = floor(frag / celda);
        float r = hash(c + 3.1);
        float hay = step(1.0 - mix(0.03, 0.10, uNoche), r);
        vec2 centro = (c + 0.5 + 0.3 * (vec2(hash(c + 7.7), hash(c + 1.9)) - 0.5)) * celda;
        float punto = exp(-dot(frag - centro, frag - centro) / (celda * celda * 0.018));
        float titila = 0.35 + 0.65 * uChispa * step(0.5, fract(r * 17.0 + floor(uTime * 4.0) * 0.37));
        float lejos = smoothstep(hy + 0.02, hy + 0.35, y);
        col += uBrillo * hay * punto * titila * (0.35 + 0.65 * lejos) * (0.4 + 0.6 * uNoche);
    }

    col *= 1.0 + 0.04 * uBombo;
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
