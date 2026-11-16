// Cartão de capítulo 3D do Ep. 11 (Escandinávia, 16/11) — mesma base do cena.js (three.js no Chromium, quadro a quadro,
// tudo função do tempo). Pacote: "cada cartão exibe uma runa nórdica sendo entalhada/queimada na madeira gelada ao som
// de vento cortante e tambor grave, revelando o título".
// Uma tábua grossa de pinho escuro com geada nas bordas, presa a um tronco; a LÂMINA entalha a runa traço a traço
// (0.1–1.4 s: o sulco afunda no relevo e lascas de madeira voam); no TAMBOR (1.6 s) a runa enche de vermelho-brasa
// (sangue/ocre aceso) que pulsa e fica; neve caindo o tempo todo, hálito de névoa no chão, luar azul de contraluz e a
// chama de uma tocha do lado. Título em português por cima (2D), frio.
// cfg: {numero, numero_pt, titulo, ano, runa: "othala"|"ansuz"|"algiz"|"ligada", dur}
import * as THREE from "three";
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { RenderPass } from "three/addons/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/addons/postprocessing/UnrealBloomPass.js";
import { BokehPass } from "three/addons/postprocessing/BokehPass.js";
import { ShaderPass } from "three/addons/postprocessing/ShaderPass.js";
import { OutputPass } from "three/addons/postprocessing/OutputPass.js";

const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lin = (t, t0, d) => clamp((t - t0) / d);
const easeOut = (x) => 1 - Math.pow(1 - clamp(x), 3);
const easeInOut = (x) => (x = clamp(x), x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
function semente(s) { let h = 2166136261; for (const ch of String(s)) h = Math.imul(h ^ ch.charCodeAt(0), 16777619);
  return () => { h += 0x6D2B79F5; let t = h; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
function ruido1(x) { const i = Math.floor(x), f = x - i, a = semente("n" + i)(), b = semente("n" + (i + 1))(); return a + (b - a) * f * f * (3 - 2 * f); }
const tremor = (t, s) => ruido1(t * 6 + s * 17) * 0.6 + ruido1(t * 13 + s * 31) * 0.4;
const TB = 1.6, ENT0 = 0.1, ENT1 = 1.4;   // entalhe de 0.1 a 1.4 s; tambor em 1.6 s
const BW = 1.55, BH = 2.3, BX = -1.25;     // tábua: largura, altura, posição x
const TX = 1024, TY = Math.round(1024 * BH / BW);
// as runas em coordenadas da tábua (0..1), traço a traço (cada traço = lista de pontos)
const RUNAS = {
  othala: [[[0.5, 0.18], [0.75, 0.42], [0.5, 0.66], [0.25, 0.42], [0.5, 0.18]], [[0.5, 0.66], [0.75, 0.86]], [[0.5, 0.66], [0.25, 0.86]]],
  ansuz: [[[0.36, 0.14], [0.36, 0.88]], [[0.36, 0.2], [0.66, 0.38]], [[0.36, 0.42], [0.66, 0.6]]],
  algiz: [[[0.5, 0.14], [0.5, 0.88]], [[0.5, 0.44], [0.24, 0.16]], [[0.5, 0.44], [0.76, 0.16]]],
  ligada: [[[0.5, 0.1], [0.5, 0.9]], [[0.5, 0.36], [0.25, 0.12]], [[0.5, 0.36], [0.75, 0.12]], [[0.5, 0.44], [0.72, 0.62], [0.5, 0.8], [0.28, 0.62], [0.5, 0.44]], [[0.5, 0.8], [0.72, 0.92]], [[0.5, 0.8], [0.28, 0.92]]],
};
let C, W, H, renderer, scene, camera, composer, bokeh, grain, tabua, texCan, texCtx, tex, hCan, hCtx, hTex, gCan, gCtx, gTex, mat;
let base, alturaBase, tocha, luzTocha, neve, lascas, nevoa = [], overlay, octx;

function canvas(w, h) { const c = document.createElement("canvas"); c.width = w; c.height = h; return c; }
function suave(cor0, cor1) { const c = canvas(64, 64), g = c.getContext("2d"), r = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  r.addColorStop(0, cor0); r.addColorStop(1, cor1); g.fillStyle = r; g.fillRect(0, 0, 64, 64); return new THREE.CanvasTexture(c); }

function madeira() {   // pinho escuro com veios, nós e geada nas bordas (cor) + a altura (relevo dos veios)
  const c = canvas(TX, TY), g = c.getContext("2d"), r = semente("pinho");
  g.fillStyle = "#3a2c22"; g.fillRect(0, 0, TX, TY);
  for (let i = 0; i < 260; i++) {   // veios verticais ondulados
    const x0 = r() * TX, lw = 1 + r() * 3.5, a = 0.05 + r() * 0.18;
    g.strokeStyle = r() < 0.55 ? `rgba(18,9,4,${a * 1.6})` : `rgba(150,105,65,${a})`; g.lineWidth = lw; g.beginPath();
    for (let y = 0; y <= TY; y += 20) g.lineTo(x0 + Math.sin(y / 140 + i) * 10 + Math.sin(y / 37 + i * 2) * 2, y); g.stroke();
  }
  for (let k = 0; k < 3; k++) {   // nós
    const x = TX * (0.15 + 0.7 * r()), y = TY * (0.1 + 0.8 * r());
    for (let j = 0; j < 9; j++) { g.strokeStyle = `rgba(10,5,2,${0.35 - j * 0.03})`; g.lineWidth = 3; g.beginPath(); g.ellipse(x, y, 14 + j * 9, 24 + j * 14, 0.2, 0, 6.3); g.stroke(); }
  }
  // geada: cristais brancos azulados que crescem das bordas para dentro
  const borda = (x, y) => Math.min(x, y, TX - x, TY - y);
  for (let i = 0; i < 22000; i++) { const x = r() * TX, y = r() * TY, d = borda(x, y); if (r() > Math.exp(-d / 110)) continue;
    g.fillStyle = `rgba(${215 + r() * 40},${232 + r() * 23},255,${0.35 + 0.55 * r()})`; const s = 1 + r() * 2.5; g.fillRect(x, y, s, s); }
  return c;
}

function tremido(pts, k) {   // a faca não é régua: o sulco treme um pouco (sempre igual para a mesma runa)
  const r = semente("faca" + k), out = [];
  for (let i = 0; i < pts.length - 1; i++) { const [x0, y0] = pts[i], [x1, y1] = pts[i + 1];
    for (let j = 0; j < 8; j++) { const q = j / 8; out.push([x0 + (x1 - x0) * q + (r() - 0.5) * 0.008, y0 + (y1 - y0) * q + (r() - 0.5) * 0.008]); } }
  out.push(pts[pts.length - 1]); return out;
}
function traco(g, pts, p) {   // desenha só a fração p da linha poligonal
  if (p <= 0) return; let tot = 0; const seg = [];
  for (let i = 1; i < pts.length; i++) { const d = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); seg.push(d); tot += d; }
  let resto = tot * Math.min(1, p); g.beginPath(); g.moveTo(pts[0][0] * TX, pts[0][1] * TY);
  for (let i = 1; i < pts.length && resto > 0; i++) { const q = Math.min(1, resto / seg[i - 1]);
    g.lineTo((pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * q) * TX, (pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * q) * TY); resto -= seg[i - 1]; }
  g.stroke();
}
// progresso de cada traço (os traços entalham um depois do outro) e a ponta da lâmina agora
function progresso(u) {
  const R = RUNAS[C.runa] || RUNAS.algiz, n = R.length, k = lin(u, ENT0, ENT1 - ENT0) * n;
  return R.map((_, i) => clamp(k - i));
}
function ponta(u) {
  const R = RUNAS[C.runa] || RUNAS.algiz, ps = progresso(u), i = ps.findIndex((p) => p < 1);
  if (i < 0 || u < ENT0) return null; const pts = R[i], p = ps[i];
  let tot = 0; const seg = []; for (let j = 1; j < pts.length; j++) { const d = Math.hypot(pts[j][0] - pts[j - 1][0], pts[j][1] - pts[j - 1][1]); seg.push(d); tot += d; }
  let resto = tot * p; for (let j = 1; j < pts.length; j++) { if (resto <= seg[j - 1]) { const q = resto / seg[j - 1];
    return [pts[j - 1][0] + (pts[j][0] - pts[j - 1][0]) * q, pts[j - 1][1] + (pts[j][1] - pts[j - 1][1]) * q]; } resto -= seg[j - 1]; }
  return pts[pts.length - 1];
}

function pintar(u) {
  const R = (RUNAS[C.runa] || RUNAS.algiz).map((pts, k) => tremido(pts, k)), ps = progresso(u), ub = u - TB, lw = TX * 0.075;
  // cor: o sulco escuro (madeira crua por dentro é mais clara nas paredes)
  texCtx.drawImage(base, 0, 0); texCtx.lineCap = "round"; texCtx.lineJoin = "round";
  R.forEach((pts, i) => { texCtx.strokeStyle = "#7a5636"; texCtx.lineWidth = lw * 1.08; traco(texCtx, pts, ps[i]);
    texCtx.strokeStyle = "#140a05"; texCtx.lineWidth = lw * 0.62; traco(texCtx, pts, ps[i]); });
  if (ub > 0) {   // a runa QUEIMA a madeira em volta (carvão) — é entalhe aceso, não neon
    const qa = easeOut(lin(ub, 0, 0.9)); texCtx.save(); texCtx.globalAlpha = 0.85 * qa; texCtx.filter = "blur(10px)";
    R.forEach((pts) => { texCtx.strokeStyle = "#0b0604"; texCtx.lineWidth = lw * 2.1; traco(texCtx, pts, 1); }); texCtx.restore();
    texCtx.strokeStyle = "#140a05"; texCtx.lineWidth = lw * 0.7; R.forEach((pts) => traco(texCtx, pts, 1));
  }
  if (ub > 0) {   // depois do tambor: o sulco enche de vermelho (sangue/ocre) que se espalha um pouco na fibra
    const a = easeOut(lin(ub, 0, 0.5)); texCtx.save(); texCtx.globalAlpha = a; texCtx.filter = "blur(3px)";
    R.forEach((pts) => { texCtx.strokeStyle = "#5a0605"; texCtx.lineWidth = lw * 0.9; traco(texCtx, pts, 1); }); texCtx.filter = "none";
    R.forEach((pts) => { texCtx.strokeStyle = "#a3120c"; texCtx.lineWidth = lw * 0.5; traco(texCtx, pts, 1); });
    // escorre: fios de sangue descendo da parte de baixo de cada traço, devagar
    const rd = semente("gota" + C.runa); texCtx.lineCap = "round";
    R.forEach((pts) => { for (let j = 0; j < 2; j++) { const q = pts[Math.floor(rd() * pts.length)], comp = (0.08 + 0.2 * rd()) * easeOut(lin(ub, 0.15 + rd() * 0.5, 3.0));
      texCtx.strokeStyle = "#7a0907"; texCtx.lineWidth = lw * (0.16 + 0.12 * rd()); texCtx.beginPath(); texCtx.moveTo(q[0] * TX, q[1] * TY);
      texCtx.lineTo((q[0] + (rd() - 0.5) * 0.01) * TX, (q[1] + comp) * TY); texCtx.stroke(); } });
    texCtx.restore();
  }
  tex.needsUpdate = true;
  // relevo: o sulco afunda (preto = fundo)
  hCtx.drawImage(alturaBase, 0, 0); hCtx.lineCap = "round"; hCtx.lineJoin = "round";
  R.forEach((pts, i) => { hCtx.save(); hCtx.filter = "blur(5px)"; hCtx.strokeStyle = "#000"; hCtx.lineWidth = lw; traco(hCtx, pts, ps[i]); hCtx.restore(); });
  hTex.needsUpdate = true;
  // brasa: a runa acende no tambor e fica pulsando (mapa emissivo)
  gCtx.fillStyle = "#000"; gCtx.fillRect(0, 0, TX, TY);
  if (ub > -0.05) { gCtx.save(); gCtx.filter = "blur(5px)"; gCtx.lineCap = "round"; gCtx.lineWidth = lw * 0.3;
    R.forEach((pts, k) => { for (let i = 1; i < pts.length; i++) { const v = 0.45 + 0.55 * ruido1(i * 0.7 + k * 9 + u * 1.3);
      gCtx.strokeStyle = `rgb(${Math.round(255 * v)},${Math.round(255 * v)},${Math.round(255 * v)})`; gCtx.beginPath();
      gCtx.moveTo(pts[i - 1][0] * TX, pts[i - 1][1] * TY); gCtx.lineTo(pts[i][0] * TX, pts[i][1] * TY); gCtx.stroke(); } }); gCtx.restore(); }
  gTex.needsUpdate = true;
  mat.emissiveIntensity = ub > 0 ? 2.4 * Math.exp(-ub / 0.4) + 0.5 * (1 - Math.exp(-ub / 0.3)) * (0.7 + 0.3 * ruido1(u * 2.2)) : 0;
}

window.preparar = async function (cfg) {
  C = cfg; W = cfg.W || 1920; H = cfg.H || 1080;
  await document.fonts.load('700 40px "Cinzel"'); await document.fonts.load('700 40px "Inter"');
  const gl = document.getElementById("gl"); gl.width = W; gl.height = H;
  renderer = new THREE.WebGLRenderer({ canvas: gl, antialias: true, preserveDrawingBuffer: true });
  renderer.setSize(W, H, false); renderer.setPixelRatio(1);
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.15; renderer.outputColorSpace = THREE.SRGBColorSpace;
  scene = new THREE.Scene(); scene.background = new THREE.Color(0x02040a); scene.fog = new THREE.FogExp2(0x050a14, 0.075);
  camera = new THREE.PerspectiveCamera(32, W / H, 0.1, 60);
  // floresta de pinheiros ao fundo (silhuetas escuras, cones) e o chão de neve
  const pinho = new THREE.MeshStandardMaterial({ color: 0x0a1410, roughness: 1 }), rr = semente("mata");
  for (let i = 0; i < 26; i++) { const h = 3 + rr() * 3, p = new THREE.Mesh(new THREE.ConeGeometry(0.5 + rr() * 0.5, h, 7), pinho);
    p.position.set(-7 + rr() * 14, -1.9 + h / 2, -3 - rr() * 6); scene.add(p); }
  const chao = new THREE.Mesh(new THREE.PlaneGeometry(30, 20), new THREE.MeshStandardMaterial({ color: 0x2a313c, roughness: 1 }));
  chao.rotation.x = -Math.PI / 2; chao.position.y = -2.3; chao.receiveShadow = true; scene.add(chao);
  // o tronco onde a tábua está presa
  const tronco = new THREE.Mesh(new THREE.CylinderGeometry(0.42, 0.5, 7, 24), new THREE.MeshStandardMaterial({ color: 0x1c120b, roughness: 0.95 }));
  tronco.position.set(BX, 0.4, -0.55); tronco.receiveShadow = true; scene.add(tronco);
  // a tábua: caixa grossa com a face de madeira pintada por quadro
  base = madeira();
  alturaBase = canvas(TX, TY); const ah = alturaBase.getContext("2d"); ah.fillStyle = "#888"; ah.fillRect(0, 0, TX, TY);
  ah.globalAlpha = 0.5; ah.filter = "grayscale(1) contrast(1.6)"; ah.drawImage(base, 0, 0); ah.filter = "none"; ah.globalAlpha = 1;
  texCan = canvas(TX, TY); texCtx = texCan.getContext("2d"); tex = new THREE.CanvasTexture(texCan); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8;
  hCan = canvas(TX, TY); hCtx = hCan.getContext("2d"); hTex = new THREE.CanvasTexture(hCan);
  gCan = canvas(TX, TY); gCtx = gCan.getContext("2d"); gTex = new THREE.CanvasTexture(gCan);
  mat = new THREE.MeshStandardMaterial({ map: tex, bumpMap: hTex, bumpScale: 2.2, roughness: 0.82, emissive: new THREE.Color(0xff3608), emissiveMap: gTex, emissiveIntensity: 0 });
  const lado = new THREE.MeshStandardMaterial({ color: 0x24170e, roughness: 0.9 });
  tabua = new THREE.Mesh(new THREE.BoxGeometry(BW, BH, 0.09), [lado, lado, lado, lado, mat, lado]);
  tabua.position.set(BX, 0.05, -0.05); tabua.rotation.z = -0.025; tabua.rotation.y = 0.16; tabua.castShadow = true; tabua.receiveShadow = true; scene.add(tabua);
  const ferro = new THREE.MeshStandardMaterial({ color: 0x3a3a3e, roughness: 0.5, metalness: 0.8 });
  for (const [x, y] of [[-0.62, 1.0], [0.62, 1.0], [-0.62, -1.0], [0.62, -1.0]]) {
    const c = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.03, 12), ferro); c.rotation.x = Math.PI / 2; c.position.set(BX + x, 0.05 + y, 0.01); scene.add(c); }
  // luzes: luar frio de contraluz, a tocha quente do lado, ambiente azul
  const lua = new THREE.DirectionalLight(0x9cbcff, 2.2); lua.position.set(3, 4, -3); scene.add(lua);
  luzTocha = new THREE.PointLight(0xffa868, 24, 10, 1.5); luzTocha.position.set(-3.2, 0.9, 1.6); luzTocha.castShadow = true;
  luzTocha.shadow.mapSize.set(1024, 1024); luzTocha.shadow.radius = 5; scene.add(luzTocha);
  scene.add(new THREE.HemisphereLight(0x3a5280, 0x0a0806, 0.6));
  const frente = new THREE.DirectionalLight(0xbcd0ff, 1.1); frente.position.set(-2.5, 1.2, 4); frente.target = tabua; scene.add(frente);   // luar rasante: mostra os veios e a geada
  tocha = new THREE.Sprite(new THREE.SpriteMaterial({ map: suave("rgba(255,220,150,1)", "rgba(255,90,10,0)"), blending: THREE.AdditiveBlending, depthWrite: false }));
  tocha.position.set(-9, 0, 0); tocha.visible = false;   // a chama fica fora de quadro: só a luz dela
  // neve caindo e lascas de madeira
  const N = 900, ng = new THREE.BufferGeometry(), np = new Float32Array(N * 3), rn = semente("neve");
  for (let i = 0; i < N; i++) { np[i * 3] = (rn() - 0.5) * 9; np[i * 3 + 1] = rn() * 6 - 2; np[i * 3 + 2] = rn() * 4 - 1.5; }
  ng.setAttribute("position", new THREE.BufferAttribute(np, 3)); ng.userData.base = np.slice();
  neve = new THREE.Points(ng, new THREE.PointsMaterial({ size: 0.028, map: suave("rgba(255,255,255,1)", "rgba(255,255,255,0)"), transparent: true, depthWrite: false, opacity: 0.85 }));
  scene.add(neve);
  const L = 70, lg = new THREE.BufferGeometry(); lg.setAttribute("position", new THREE.BufferAttribute(new Float32Array(L * 3), 3));
  lascas = new THREE.Points(lg, new THREE.PointsMaterial({ size: 0.022, color: 0xb88a5a, transparent: true, opacity: 0.95 })); scene.add(lascas);
  // névoa rasteira (planos aditivos)
  const nt = suave("rgba(170,190,220,0.55)", "rgba(170,190,220,0)");
  for (let i = 0; i < 5; i++) { const m = new THREE.Mesh(new THREE.PlaneGeometry(6, 1.6), new THREE.MeshBasicMaterial({ map: nt, transparent: true, depthWrite: false, opacity: 0.3 }));
    m.position.set(-3 + i * 1.6, -1.55, 0.6 - i * 0.5); scene.add(m); nevoa.push(m); }
  // pós
  composer = new EffectComposer(renderer); composer.setPixelRatio(1); composer.setSize(W, H);
  composer.addPass(new RenderPass(scene, camera));
  composer.addPass(new UnrealBloomPass(new THREE.Vector2(W, H), 0.55, 0.55, 0.75));
  bokeh = new BokehPass(scene, camera, { focus: 6.0, aperture: 0.0014, maxblur: 0.007 }); composer.addPass(bokeh);
  grain = new ShaderPass({ uniforms: { tDiffuse: { value: null }, t: { value: 0 } }, vertexShader: "varying vec2 vUv;void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}",
    fragmentShader: `uniform sampler2D tDiffuse;uniform float t;varying vec2 vUv;
      float h(vec2 p){return fract(sin(dot(p,vec2(12.9898,78.233))+t*61.7)*43758.5453);}
      void main(){vec2 d=vUv-.5;vec3 c=texture2D(tDiffuse,vUv).rgb;c*=1.-smoothstep(.38,.95,length(d*vec2(1.05,1.25)));
      c+=(h(vUv*vec2(1920.,1080.))-.5)*.05;gl_FragColor=vec4(c,1.);}` });
  composer.addPass(grain); composer.addPass(new OutputPass());
  overlay = document.getElementById("titulo"); overlay.width = W; overlay.height = H; octx = overlay.getContext("2d");
};

function titulo(u) {   // frio: letras de gelo, número do capítulo, ano em vermelho
  octx.clearRect(0, 0, W, H);
  const a2 = easeOut(lin(u, 2.5, 0.8)); if (a2 <= 0) return;
  const xt = W * 0.555; octx.save(); octx.textBaseline = "alphabetic";
  const fg = octx.createLinearGradient(0, H * 0.34, 0, H * 0.68); fg.addColorStop(0, "rgba(160,20,16,0)"); fg.addColorStop(0.15, "#a3120c"); fg.addColorStop(1, "rgba(160,20,16,.2)");
  octx.fillStyle = fg; octx.fillRect(xt, H * 0.34, W * 0.003, H * 0.34 * a2);
  octx.globalAlpha = a2; octx.font = `700 ${Math.round(H * 0.026)}px "Inter"`; octx.fillStyle = "#a9c3dc";
  octx.fillText((C.numero_pt || `CAPÍTULO ${C.numero}`).toUpperCase().split("").join(" "), xt + W * 0.022, H * 0.405);
  let fs = Math.round(H * 0.07); octx.font = `700 ${fs}px "Cinzel"`;
  const tit = C.titulo || "", maxW = W * 0.38; let ls = [tit];
  if (octx.measureText(tit).width > maxW) { const ps = tit.split(" "), mm = Math.ceil(ps.length / 2); ls = [ps.slice(0, mm).join(" "), ps.slice(mm).join(" ")]; }
  while (Math.max(...ls.map((l) => octx.measureText(l).width)) > maxW && fs > 20) { fs -= 2; octx.font = `700 ${fs}px "Cinzel"`; }
  let k0 = 0; ls.forEach((l, li) => { let x = xt + W * 0.022; const y = H * 0.5 + li * fs * 1.14;
    for (const ch of l) { const p = easeOut(lin(u, 2.65 + k0 * 0.028, 0.45)); k0++;
      if (p > 0) { octx.save(); octx.globalAlpha = p; octx.filter = `blur(${(1 - p) * 8}px)`; octx.shadowColor = "rgba(120,170,255,.35)"; octx.shadowBlur = 18;
        octx.fillStyle = "#eef4fb"; octx.fillText(ch, x, y + (1 - p) * fs * 0.15); octx.restore(); }
      x += octx.measureText(ch).width; } });
  octx.globalAlpha = easeOut(lin(u, 3.45, 0.6)); octx.font = `700 ${Math.round(H * 0.033)}px "Inter"`; octx.fillStyle = "#d8322a";
  octx.fillText(C.ano || "", xt + W * 0.022, H * 0.5 + ls.length * fs * 1.14 + H * 0.025);
  octx.restore();
}

window.tempos = {};
window.quadro = function (t) {
  const u = t, ub = t - TB;
  pintar(u);
  // tocha tremendo
  luzTocha.intensity = 24 * (0.8 + 0.35 * tremor(t, 4));
  // neve caindo (com vento) — e o tambor sacode os flocos perto da tábua
  const pa = neve.geometry.attributes.position, b = neve.geometry.userData.base;
  for (let i = 0; i < pa.count; i++) { const y = ((b[i * 3 + 1] + 2 - t * (0.35 + (i % 7) * 0.04)) % 6 + 6) % 6 - 2;
    let x = b[i * 3] + Math.sin(t * 0.7 + i) * 0.12 + t * 0.15, z = b[i * 3 + 2];
    if (ub > 0 && ub < 1.2) { const k = Math.exp(-ub * 3) * 0.25; x += (x - BX) * k; z += k; }
    pa.setXYZ(i, ((x + 4.5) % 9 + 9) % 9 - 4.5, y, z); }
  pa.needsUpdate = true;
  // lascas saindo da ponta da lâmina enquanto entalha
  const lp = lascas.geometry.attributes.position, pt = ponta(u), rs = semente("lasca");
  for (let i = 0; i < lp.count; i++) { const vx = rs() - 0.5, vy = rs(), vz = rs(), fase = rs();
    if (!pt) { lp.setXYZ(i, 0, -9, 0); continue; }
    const age = ((t * 3 + fase) % 1), x0 = BX + (pt[0] - 0.5) * BW, y0 = 0.05 + (0.5 - pt[1]) * BH;
    lp.setXYZ(i, x0 + vx * age * 0.6, y0 + vy * age * 0.5 - age * age * 0.9, 0.05 + vz * age * 0.6); }
  lp.needsUpdate = true; lascas.material.opacity = pt ? 0.95 : 0;
  nevoa.forEach((m, i) => { m.position.x = -3 + i * 1.6 + Math.sin(t * 0.25 + i) * 0.4; m.material.opacity = 0.22 + 0.08 * Math.sin(t * 0.5 + i); });
  // câmera: aproxima devagar; o tambor dá um tranco
  const k = easeInOut(lin(t, 0, C.dur || 7.6)), tr = ub > 0 && ub < 0.22 ? (1 - ub / 0.22) : 0;
  camera.position.set(-0.2 + 0.12 * k + (ruido1(t * 0.7) - 0.5) * 0.03 + (ruido1(t * 40) - 0.5) * 0.035 * tr,
    -0.02 + (ruido1(t * 0.6 + 9) - 0.5) * 0.025 + (ruido1(t * 43 + 3) - 0.5) * 0.035 * tr, 6.3 - 0.6 * k);
  camera.lookAt(-0.05 + 0.05 * k, 0.0, 0); bokeh.uniforms.focus.value = camera.position.z - 0.05;
  grain.uniforms.t.value = t;
  composer.render(); renderer.getContext().finish();
  titulo(u);
  const fade = Math.min(lin(t, 0, 0.35), 1 - lin(t, (C.dur || 7.6) - 0.4, 0.4));
  document.getElementById("veu").style.opacity = String(1 - fade);
  return true;
};
window.pronto = true;
