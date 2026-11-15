// Cartão de capítulo em 3D (Ep. 10, 16/11) — three.js (MIT) no Chromium sem tela, quadro a quadro.
// Pedido do usuário: "fazer melhor ainda esses cartões… um motor diferente com qualidade ainda maior".
// O pano Pha Yant é uma malha de tecido de verdade (material físico com brilho de tecido, trama em relevo), pendurado numa
// vara diante de uma parede de tábuas de teca; ele DESENROLA (o rolo desce girando), ondula, e o golpe do tambor
// (1.6 s) manda uma onda pelo tecido de cima a baixo. A tinta do yantra é traçada na textura enquanto o vídeo roda e,
// depois do tambor, as linhas acendem como brasa e esfriam. Luz de velas tremendo (sombras na parede), luar frio de
// contraluz, fumaça de incenso, poeira, profundidade de campo, bloom, grão e vinheta. Tudo é função do tempo (sem estado),
// então os quadros podem ser renderizados em paralelo.
// API: await window.preparar(cfg) · window.quadro(t) → dataURL JPEG do quadro t (s)
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
  return () => ((h = Math.imul(h ^ (h >>> 15), 2246822507) ^ Math.imul(h ^ (h >>> 13), 3266489909)) >>> 0) / 4294967296; }
function ruido1(x) { const i = Math.floor(x), f = x - i, a = semente("n" + i)(), b = semente("n" + (i + 1))(); return a + (b - a) * f * f * (3 - 2 * f); }
const tremor = (t, s) => ruido1(t * 6 + s * 17) * 0.6 + ruido1(t * 13 + s * 31) * 0.4;   // chama de vela

const KHOM = ["ន", "មោ", "ពុ", "ទ្ធា", "យ", "ម", "អ", "ឥ", "ស", "វា", "សុ", "ជា", "នា", "ក", "ត", "ឧ", "អ៊ុ"];
const TB = 1.6;   // o golpe do tambor (a música do capítulo bate aqui)
let C, W, H, renderer, scene, camera, composer, bokeh, pano, geo, base, texCan, texCtx, tex, glowCan, glowCtx, glowTex, mat;
let vara, velas = [], luzes = [], fumacas = [], poeira, overlay, octx, final, fctx, grain;
const PW = 1.5, PH = 2.65, TOPO = 1.42, PX = -1.25;   // pano: largura, altura, topo, posição x

// ------------------------------------------------------------ texturas procedurais
function canvas(w, h) { const c = document.createElement("canvas"); c.width = w; c.height = h; return c; }
function tabuas() {   // parede de tábuas de teca escurecida (casa de madeira de Isan)
  const c = canvas(1024, 1024), g = c.getContext("2d"), r = semente("teca");
  for (let i = 0; i < 8; i++) {
    const x = i * 128, tom = 38 + r() * 18;
    g.fillStyle = `rgb(${tom + 14},${tom * 0.62},${tom * 0.36})`; g.fillRect(x, 0, 128, 1024);
    for (let k = 0; k < 140; k++) {   // veios
      g.strokeStyle = `rgba(${10 + r() * 30},${6 + r() * 14},${2},${0.12 + r() * 0.2})`; g.lineWidth = 0.6 + r() * 2.2;
      const xx = x + r() * 128; g.beginPath(); g.moveTo(xx, 0);
      for (let y = 0; y <= 1024; y += 64) g.lineTo(xx + Math.sin(y * 0.01 + k) * (2 + r() * 5), y); g.stroke();
    }
    g.fillStyle = "rgba(0,0,0,.75)"; g.fillRect(x, 0, 3, 1024);   // fresta entre as tábuas
  }
  const v = g.createRadialGradient(512, 450, 120, 512, 512, 760); v.addColorStop(0, "rgba(0,0,0,0)"); v.addColorStop(1, "rgba(0,0,0,.6)"); g.fillStyle = v; g.fillRect(0, 0, 1024, 1024);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping; t.anisotropy = 4; return t;
}
function trama() {   // relevo da trama do tecido (mapa de normais a partir de uma altura)
  const n = 512, hgt = new Float32Array(n * n), r = semente("trama");
  for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) {
    const fio = Math.sin(x * Math.PI / 2) ** 2 * 0.5 + Math.sin(y * Math.PI / 2 + (Math.floor(x / 2) % 2) * Math.PI / 2) ** 2 * 0.5;
    hgt[y * n + x] = fio + (r() - 0.5) * 0.25;
  }
  const c = canvas(n, n), g = c.getContext("2d"), im = g.createImageData(n, n);
  for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) {
    const dx = hgt[y * n + (x + 1) % n] - hgt[y * n + (x - 1 + n) % n], dy = hgt[((y + 1) % n) * n + x] - hgt[((y - 1 + n) % n) * n + x];
    const nx = -dx * 1.4, ny = -dy * 1.4, nz = 1, L = Math.hypot(nx, ny, nz), i = (y * n + x) * 4;
    im.data[i] = (nx / L * 0.5 + 0.5) * 255; im.data[i + 1] = (ny / L * 0.5 + 0.5) * 255; im.data[i + 2] = (nz / L * 0.5 + 0.5) * 255; im.data[i + 3] = 255;
  }
  g.putImageData(im, 0, 0);
  const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(26, 46); return t;
}
function suave(cor0, cor1) {   // sprite redondo e macio (chama, fumaça, poeira)
  const c = canvas(128, 128), g = c.getContext("2d"), gr = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  gr.addColorStop(0, cor0); gr.addColorStop(1, cor1); g.fillStyle = gr; g.fillRect(0, 0, 128, 128);
  return new THREE.CanvasTexture(c);
}
function texFumaca() {
  const c = canvas(256, 512), g = c.getContext("2d"), r = semente("fum");
  for (let i = 0; i < 90; i++) { const y = 512 - i * 5.5, x = 128 + Math.sin(i * 0.17) * 30 * (i / 90) + (r() - 0.5) * 10, rad = 10 + i * 0.6;
    const gr = g.createRadialGradient(x, y, 0, x, y, rad); gr.addColorStop(0, `rgba(220,215,205,${0.05 * (1 - i / 110)})`); gr.addColorStop(1, "rgba(220,215,205,0)");
    g.fillStyle = gr; g.fillRect(x - rad, y - rad, rad * 2, rad * 2); }
  return new THREE.CanvasTexture(c);
}

// ------------------------------------------------------------ o pano: base (tecido) + tinta traçada por quadro
const TX = 1024, TY = Math.round(1024 * PH / PW);
function baseTecido(cor) {
  const c = canvas(TX, TY), g = c.getContext("2d"), r = semente("pano" + cor);
  const [R, G, B] = cor === "branco" ? [214, 204, 184] : [128, 18, 16];
  g.fillStyle = `rgb(${R},${G},${B})`; g.fillRect(0, 0, TX, TY);
  for (let i = 0; i < 2600; i++) {   // irregularidade do tingimento e manchas de anos de incenso
    const x = r() * TX, y = r() * TY, rad = 6 + r() * 60, a = r() * 0.03;
    g.fillStyle = r() < 0.5 ? `rgba(0,0,0,${a})` : `rgba(255,${cor === "branco" ? 250 : 120},${cor === "branco" ? 230 : 90},${a * 0.6})`;
    g.beginPath(); g.arc(x, y, rad, 0, 6.29); g.fill();
  }
  const v = g.createRadialGradient(TX / 2, TY / 2, TX * 0.3, TX / 2, TY / 2, TY * 0.62); v.addColorStop(0, "rgba(0,0,0,0)"); v.addColorStop(1, "rgba(25,6,0,.55)");
  g.fillStyle = v; g.fillRect(0, 0, TX, TY);
  for (let i = 0; i < 260; i++) { g.fillStyle = `rgba(20,5,0,${0.15 + r() * 0.3})`; g.fillRect(r() * TX, TY - r() * 12, 2, 12); }   // barra puída
  return c;
}
function traco(g, pts, p, fechado) {
  if (p <= 0) return; const P = fechado ? pts.concat([pts[0]]) : pts; let tot = 0; const seg = [];
  for (let i = 1; i < P.length; i++) { const d = Math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]); seg.push(d); tot += d; }
  let resto = tot * Math.min(1, p); g.beginPath(); g.moveTo(P[0][0], P[0][1]);
  for (let i = 1; i < P.length && resto > 0; i++) { const d = seg[i - 1], q = Math.min(1, resto / d);
    g.lineTo(P[i - 1][0] + (P[i][0] - P[i - 1][0]) * q, P[i - 1][1] + (P[i][1] - P[i - 1][1]) * q); resto -= d; }
  g.stroke();
}
function circulo(cx, cy, R, ry = 1, a0 = -Math.PI / 2) { const p = []; for (let a = 0; a <= 6.30; a += 0.06) p.push([cx + Math.cos(a + a0) * R, cy + Math.sin(a + a0) * R * ry]); return p; }
// desenha o yantra até o instante u em g (cor da tinta); usado duas vezes: tinta (cor) e brasa (emissivo)
function yantra(g, u, tinta, lw) {
  g.save(); g.lineCap = "round"; g.lineJoin = "round"; g.strokeStyle = tinta; g.fillStyle = tinta;
  const m = TX * 0.07, x0 = m, x1 = TX - m, y0 = m, y1 = TY - m * 1.8;
  g.lineWidth = lw * 9; traco(g, [[x0, y0], [x1, y0], [x1, y1], [x0, y1]], lin(u, 0.9, 0.75), true);
  g.lineWidth = lw * 4; traco(g, [[x0 + m * 0.45, y0 + m * 0.45], [x1 - m * 0.45, y0 + m * 0.45], [x1 - m * 0.45, y1 - m * 0.45], [x0 + m * 0.45, y1 - m * 0.45]], lin(u, 1.0, 0.75), true);
  // unalom: espiral sagrada que sobe
  const pu = lin(u, 1.15, 0.6), ux = TX / 2, uy = y0 + TY * 0.11, esp = [];
  for (let a = 0; a <= 6.28 * 2.3; a += 0.1) esp.push([ux + Math.cos(a) * a * TX * 0.0062, uy + Math.sin(a) * a * TX * 0.0062]);
  esp.push([ux, uy - TY * 0.07]); g.lineWidth = lw * 6; traco(g, esp, pu);
  // motivo do capítulo (entra no tambor)
  const pm = easeOut(lin(u, TB, 0.85)), my = y0 + TY * 0.33, R = TX * 0.24; g.lineWidth = lw * 7;
  const mot = C.motivo || ["sol", "presas", "aneis", "olho"][((C.numero || 1) - 1) % 4];
  if (mot === "sol") { traco(g, circulo(TX / 2, my, R * 0.55), pm);
    for (let i = 0; i < 12; i++) { const a = i / 12 * 6.28; traco(g, [[TX / 2 + Math.cos(a) * R * 0.7, my + Math.sin(a) * R * 0.7], [TX / 2 + Math.cos(a) * R, my + Math.sin(a) * R]], clamp(pm * 12 - i)); } }
  else if (mot === "presas") { traco(g, [[TX / 2 - R, my - R * 0.6], [TX / 2, my + R], [TX / 2 + R, my - R * 0.6]], pm, true);
    traco(g, [[TX / 2 - R * 0.55, my + R * 0.72], [TX / 2, my - R * 0.95], [TX / 2 + R * 0.55, my + R * 0.72]], clamp(pm * 1.4 - 0.4), true);
    traco(g, circulo(TX / 2, my + R * 0.08, R * 0.16), clamp(pm * 2 - 1)); }
  else if (mot === "aneis") { for (let k = 0; k < 3; k++) traco(g, circulo(TX / 2, my, R * (0.32 + k * 0.3)), clamp(pm * 3 - k));
    for (let k = 0; k < 8; k++) { const a = k / 8 * 6.28; traco(g, [[TX / 2 + Math.cos(a) * R * 0.92, my + Math.sin(a) * R * 0.92], [TX / 2 + Math.cos(a) * R * 1.12, my + Math.sin(a) * R * 1.12]], clamp(pm * 3 - 2)); } }
  else { const ol = []; for (let a = 0; a <= 6.30; a += 0.05) ol.push([TX / 2 + Math.cos(a) * R, my + Math.sin(a) * R * 0.48 * (Math.abs(Math.cos(a / 2)) * 0.6 + 0.4)]);
    traco(g, ol, pm); traco(g, circulo(TX / 2, my, R * 0.22), clamp(pm * 2 - 0.8)); traco(g, circulo(TX / 2, my, R * 0.09), clamp(pm * 2 - 1)); }
  // grade 3×3 e as sílabas khom
  const gs = TX * 0.52, cel = gs / 3, gx = (TX - gs) / 2, gy = y0 + TY * 0.5, pg = lin(u, 1.85, 0.65); g.lineWidth = lw * 5;
  for (let k = 0; k <= 3; k++) { traco(g, [[gx, gy + k * cel], [gx + gs, gy + k * cel]], clamp(pg * 2 - k * 0.25)); traco(g, [[gx + k * cel, gy], [gx + k * cel, gy + gs]], clamp(pg * 2 - 0.5 - k * 0.25)); }
  const rk = semente("khom" + (C.numero || 1)), sil = Array.from({ length: 9 }, () => KHOM[Math.floor(rk() * KHOM.length)]);
  g.textAlign = "center"; g.textBaseline = "middle"; g.font = `400 ${Math.round(cel * 0.64)}px "Moul", "Noto Serif Khmer"`;
  sil.forEach((s, i) => { const p = clamp(lin(u, 2.1, 1.0) * 9 - i); if (p <= 0) return; g.globalAlpha = p; g.fillText(s, gx + (i % 3 + 0.5) * cel, gy + (Math.floor(i / 3) + 0.5) * cel); });
  g.globalAlpha = 1; g.font = `400 ${Math.round(TX * 0.05)}px "Moul", "Noto Serif Khmer"`; g.textAlign = "left";
  for (let L = 0; L < 3; L++) { const yy = gy + gs + TY * 0.04 + L * TX * 0.062, p = lin(u, 2.5 + L * 0.25, 0.6); if (p <= 0) continue;
    const txt = Array.from({ length: 12 }, () => KHOM[Math.floor(rk() * KHOM.length)]).join("");
    g.save(); g.beginPath(); g.rect(x0 + m * 0.7, yy - TX * 0.05, (x1 - x0 - m * 1.4) * p, TX * 0.1); g.clip(); g.fillText(txt, x0 + m * 0.8, yy, x1 - x0 - m * 1.6); g.restore(); }
  // pontos rituais nos cantos
  const pp = lin(u, 2.3, 0.4); for (const [a, b] of [[0, 0], [3, 0], [0, 3], [3, 3]]) { g.globalAlpha = pp; g.beginPath(); g.arc(gx + a * cel, gy + b * cel, lw * 9, 0, 6.29); g.fill(); }
  g.restore();
}
function pintarPano(u) {
  const tinta = C.cor === "branco" ? "#7a0906" : "#e7bd5a";   // 16/11: tinta dourada no vermelho (a escrita é a marca do episódio)
  texCtx.drawImage(base, 0, 0);
  texCtx.save(); texCtx.filter = "blur(7px)"; texCtx.globalAlpha = 0.5; yantra(texCtx, u, C.cor === "branco" ? "#3a0302" : "#2a0602", 3.6); texCtx.restore();   // sombra/sangrado escuro por baixo: o ouro salta   // a tinta que espalha na fibra
  texCtx.globalAlpha = 1; yantra(texCtx, u, tinta, 2.8);
  tex.needsUpdate = true;
  // brasa: depois do tambor as linhas acendem e esfriam devagar (mapa emissivo)
  glowCtx.fillStyle = "#000"; glowCtx.fillRect(0, 0, TX, TY);
  glowCtx.save(); glowCtx.filter = "blur(4px)"; yantra(glowCtx, u, "#fff", 2.6); glowCtx.restore(); yantra(glowCtx, u, "#fff", 2.2); glowTex.needsUpdate = true;
  const ub = u - TB; mat.emissiveIntensity = ub > 0 ? 1.4 * Math.exp(-ub / 0.8) + 0.32 * (1 - Math.exp(-ub / 0.4)) * (0.9 + 0.1 * Math.sin(u * 5.3)) : 0.18;   // acende no tambor e fica aceso (brasa viva)
}

// ------------------------------------------------------------ o pano desenrolando (geometria por quadro)
function moldarPano(u, t) {
  const e = easeInOut(lin(u, 0.1, 1.45)), frente = PH * e, pos = geo.attributes.position, uv = geo.attributes.uv;
  const ub = u - TB, esp = 0.0045;
  for (let i = 0; i < pos.count; i++) {
    const s = uv.getX(i), v = 1 - uv.getY(i), y = v * PH, x = (s - 0.5) * PW;
    let px = x, py, pz;
    const solto = clamp(1 - frente / PH) ;
    const onda = (0.034 * Math.sin(s * 5.5 + t * 1.25 + v * 2.6) + 0.022 * Math.sin(v * 7 - t * 1.9 + s * 2) * v + 0.012 * Math.sin(s * 13 + v * 5 + t * 0.8)) * (0.35 + 0.65 * v) + 0.028 * Math.sin(s * 3.1 * Math.PI + 0.7) * Math.min(1, v * 3) + 0.012 * Math.sin(s * 8.3 * Math.PI) * v;
    let pulso = 0; if (ub > 0) { const fr = ub * 2.4; pulso = 0.09 * Math.exp(-ub / 0.55) * Math.sin(14 * (v - fr)) * clamp((fr - v) * 6) * (0.3 + v); }
    if (y <= frente) { py = TOPO - y; pz = onda + pulso + (1 - e) * 0.02 * Math.sin(u * 9 + v * 4); }
    else {   // enrolado: espiral em volta do eixo que desce com a frente
      const sArc = y - frente, Rr = 0.085 * solto + 0.012, rr = Math.max(0.006, Rr - (sArc / (2 * Math.PI * Rr)) * esp), a = sArc / rr;
      py = TOPO - frente - Math.sin(a) * rr; pz = (Rr - Math.cos(a) * rr) + 0.004;
    }
    pos.setXYZ(i, px, py, pz);
  }
  pos.needsUpdate = true; geo.computeVertexNormals();
  pano.rotation.z = 0.01 * Math.sin(t * 0.9) + (1 - e) * 0.025 * Math.sin(u * 7);
}

// ------------------------------------------------------------ montar a cena
window.preparar = async function (cfg) {
  C = cfg; W = cfg.W || 1920; H = cfg.H || 1080;
  await document.fonts.load('400 40px "Moul"'); await document.fonts.load('700 40px "Cinzel"'); await document.fonts.load('700 40px "Inter"');
  const gl = document.getElementById("gl"); gl.width = W; gl.height = H;
  renderer = new THREE.WebGLRenderer({ canvas: gl, antialias: !cfg.sem_aa, preserveDrawingBuffer: true });
  renderer.setSize(W, H, false); renderer.setPixelRatio(1);
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05; renderer.outputColorSpace = THREE.SRGBColorSpace;
  scene = new THREE.Scene(); scene.background = new THREE.Color(0x030202); scene.fog = new THREE.FogExp2(0x060403, 0.06);
  camera = new THREE.PerspectiveCamera(32, W / H, 0.1, 60);
  // parede
  const tTab = tabuas(); tTab.repeat.set(2.2, 1.3);
  const parede = new THREE.Mesh(new THREE.PlaneGeometry(16, 9), new THREE.MeshStandardMaterial({ map: tTab, roughness: 0.92, bumpMap: tTab, bumpScale: 0.04 }));
  parede.position.set(0, 0, -0.55); parede.receiveShadow = true; scene.add(parede);
  // pano
  base = baseTecido(C.cor); texCan = canvas(TX, TY); texCtx = texCan.getContext("2d"); tex = new THREE.CanvasTexture(texCan); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8;
  glowCan = canvas(TX, TY); glowCtx = glowCan.getContext("2d"); glowTex = new THREE.CanvasTexture(glowCan);
  mat = new THREE.MeshPhysicalMaterial({ map: tex, normalMap: trama(), normalScale: new THREE.Vector2(0.55, 0.55), roughness: 0.88,
    sheen: 1.0, sheenRoughness: 0.55, sheenColor: new THREE.Color(C.cor === "branco" ? 0xfff4e0 : 0xff5a40),
    emissive: new THREE.Color(C.cor === "branco" ? 0xd0200c : 0xffa53a), emissiveMap: glowTex, emissiveIntensity: 0, side: THREE.DoubleSide });
  geo = new THREE.PlaneGeometry(PW, PH, 60, 110); pano = new THREE.Mesh(geo, mat); pano.castShadow = true; pano.receiveShadow = true;
  pano.position.set(PX, 0, 0); scene.add(pano);
  // vara de madeira, ponteiras de latão e o cordão
  const madeira = new THREE.MeshStandardMaterial({ color: 0x4a2c16, roughness: 0.55, metalness: 0.05 });
  vara = new THREE.Group();
  const cil = new THREE.Mesh(new THREE.CylinderGeometry(0.028, 0.028, PW + 0.26, 24), madeira); cil.rotation.z = Math.PI / 2; cil.castShadow = true; vara.add(cil);
  const latao = new THREE.MeshStandardMaterial({ color: 0xb08a3c, roughness: 0.3, metalness: 0.9 });
  for (const lado of [-1, 1]) { const p = new THREE.Mesh(new THREE.SphereGeometry(0.042, 20, 16), latao); p.position.x = lado * (PW / 2 + 0.13); vara.add(p); }
  const cordao = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3([new THREE.Vector3(-PW * 0.42, 0, 0), new THREE.Vector3(0, 0.3, -0.05), new THREE.Vector3(PW * 0.42, 0, 0)]), 40, 0.006, 6),
    new THREE.MeshStandardMaterial({ color: 0xe8e2d2, roughness: 0.9 })); vara.add(cordao);
  const prego = new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.012, 0.1, 8), latao); prego.rotation.x = Math.PI / 2; prego.position.set(0, 0.3, -0.08); vara.add(prego);
  vara.position.set(PX, TOPO + 0.02, 0.02); scene.add(vara);
  // velas no primeiro plano (fora de foco) e a luz delas
  const cera = new THREE.MeshStandardMaterial({ color: 0xe9dfc8, roughness: 0.6 });
  const chamaTex = suave("rgba(255,230,170,1)", "rgba(255,120,20,0)");
  for (const [x, y, z, h] of [[-2.55, -1.55, 1.25, 0.32], [-2.3, -1.6, 1.45, 0.22], [0.55, -1.62, 1.35, 0.27], [-0.35, -1.7, 1.8, 0.18]]) {
    const v = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.05, h, 20), cera); v.position.set(x, y + h / 2, z); scene.add(v);
    const ch = new THREE.Sprite(new THREE.SpriteMaterial({ map: chamaTex, blending: THREE.AdditiveBlending, depthWrite: false, color: 0xffd9a0 }));
    ch.position.set(x, y + h + 0.06, z); ch.scale.set(0.06, 0.15, 1); scene.add(ch); velas.push(ch);
  }
  const vela = new THREE.PointLight(0xff9a48, 34, 10, 1.5); vela.position.set(-2.9, -1.0, 0.55); vela.castShadow = !cfg.sem_sombra; vela.shadow.mapSize.set(1024, 1024); vela.shadow.radius = 6; vela.shadow.bias = -0.002; scene.add(vela); luzes.push(vela);
  const vela2 = new THREE.PointLight(0xff8a38, 6, 8, 1.5); vela2.position.set(0.6, -1.3, 1.0); scene.add(vela2); luzes.push(vela2);
  const lua = new THREE.DirectionalLight(0x7d9cff, 0.35); lua.position.set(3, 3, -2); scene.add(lua);
  const amb = new THREE.HemisphereLight(0x5a4030, 0x080504, 0.45); scene.add(amb);
  // fumaça de incenso (planos que sobem e giram) e poeira no ar
  const ftex = texFumaca();
  for (let i = 0; i < 4; i++) { const f = new THREE.Mesh(new THREE.PlaneGeometry(1.2, 2.4), new THREE.MeshBasicMaterial({ map: ftex, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, opacity: 0.55 }));
    f.position.set(-2.35 + i * 0.12, -0.4, 0.9 + i * 0.08); f.scale.set(0.6, 0.75, 1); scene.add(f); fumacas.push(f); }
  const N = 500, pg = new THREE.BufferGeometry(), pp = new Float32Array(N * 3), r = semente("poeira");
  for (let i = 0; i < N; i++) { pp[i * 3] = (r() - 0.5) * 6; pp[i * 3 + 1] = (r() - 0.5) * 3.6; pp[i * 3 + 2] = r() * 2.2 - 0.2; }
  pg.setAttribute("position", new THREE.BufferAttribute(pp, 3)); pg.userData.base = pp.slice();
  poeira = new THREE.Points(pg, new THREE.PointsMaterial({ size: 0.012, map: suave("rgba(255,235,200,1)", "rgba(255,235,200,0)"), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, opacity: 0.55 }));
  scene.add(poeira);
  // pós: render → bloom (chamas e brasa) → profundidade de campo → grão + vinheta + aberração → saída
  composer = new EffectComposer(renderer); composer.setPixelRatio(1); composer.setSize(W, H);
  composer.addPass(new RenderPass(scene, camera));
  if (!cfg.sem_bloom) composer.addPass(new UnrealBloomPass(new THREE.Vector2(W, H), 0.55, 0.65, 0.72));
  bokeh = new BokehPass(scene, camera, { focus: 5.6, aperture: 0.0016, maxblur: 0.008 }); if (!cfg.sem_bokeh) composer.addPass(bokeh);
  grain = new ShaderPass({ uniforms: { tDiffuse: { value: null }, t: { value: 0 } }, vertexShader: "varying vec2 vUv;void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}",
    fragmentShader: `uniform sampler2D tDiffuse;uniform float t;varying vec2 vUv;
      float h(vec2 p){return fract(sin(dot(p,vec2(12.9898,78.233))+t*61.7)*43758.5453);}
      void main(){vec2 d=vUv-.5;float ab=.0016*length(d);vec3 c=vec3(texture2D(tDiffuse,vUv+d*ab).r,texture2D(tDiffuse,vUv).g,texture2D(tDiffuse,vUv-d*ab).b);
      c*=1.-smoothstep(.35,.95,length(d*vec2(1.05,1.25)));c+=(h(vUv*vec2(1920.,1080.))-.5)*.05;gl_FragColor=vec4(c,1.);}` });
  composer.addPass(grain); composer.addPass(new OutputPass());
  // composição final: o quadro 3D + o título em 2D por cima
  // 16/11: o título vai num canvas 2D POR CIMA do WebGL e o quadro é capturado pela tela (page.screenshot): copiar o
  // WebGL para um canvas 2D e gerar o JPEG no navegador custava ~13 s por quadro no SwiftShader
  overlay = document.getElementById("titulo"); overlay.width = W; overlay.height = H; octx = overlay.getContext("2d");
};

// ------------------------------------------------------------ título em português (2D, nítido)
function titulo(u) {
  octx.clearRect(0, 0, W, H);
  const a2 = easeOut(lin(u, 2.55, 0.8)); if (a2 <= 0) return;
  const xt = W * 0.565; octx.save(); octx.textAlign = "left"; octx.textBaseline = "alphabetic";
  // pincelada vermelha (fio) que desce
  const fg = octx.createLinearGradient(0, H * 0.34, 0, H * 0.68); fg.addColorStop(0, "rgba(190,22,28,0)"); fg.addColorStop(0.15, "#be161c"); fg.addColorStop(1, "rgba(190,22,28,.2)");
  octx.fillStyle = fg; octx.fillRect(xt, H * 0.34, W * 0.003, H * 0.34 * a2);
  octx.globalAlpha = a2; octx.font = `700 ${Math.round(H * 0.026)}px "Inter"`; octx.fillStyle = "#cdb991";
  octx.fillText((C.numero_pt || `CAPÍTULO ${C.numero}`).toUpperCase().split("").join(" "), xt + W * 0.022, H * 0.405);
  let fs = Math.round(H * 0.074); octx.font = `700 ${fs}px "Cinzel"`;
  const tit = C.titulo || "", maxW = W * 0.37; let ls = [tit];
  if (octx.measureText(tit).width > maxW) { const ps = tit.split(" "), mm = Math.ceil(ps.length / 2); ls = [ps.slice(0, mm).join(" "), ps.slice(mm).join(" ")]; }
  while (Math.max(...ls.map((l) => octx.measureText(l).width)) > maxW && fs > 20) { fs -= 2; octx.font = `700 ${fs}px "Cinzel"`; }
  // cada letra chega desfocada e assenta (tinta que seca), da esquerda para a direita
  let k0 = 0; ls.forEach((l, li) => { let x = xt + W * 0.022; const y = H * 0.5 + li * fs * 1.14;
    for (const ch of l) { const p = easeOut(lin(u, 2.7 + k0 * 0.028, 0.45)); k0++;
      if (p > 0) { octx.save(); octx.globalAlpha = p; octx.filter = `blur(${(1 - p) * 8}px)`; octx.shadowColor = "rgba(0,0,0,.95)"; octx.shadowBlur = 22;
        octx.fillStyle = "#f2e8d2"; octx.fillText(ch, x, y + (1 - p) * fs * 0.15); octx.restore(); }
      x += octx.measureText(ch).width; } });
  octx.globalAlpha = easeOut(lin(u, 3.5, 0.6)); octx.font = `700 ${Math.round(H * 0.033)}px "Inter"`; octx.fillStyle = "#d8322a";
  octx.fillText(C.ano || "", xt + W * 0.022, H * 0.5 + ls.length * fs * 1.14 + H * 0.025);
  octx.restore();
}

window.tempos = {};
const _m = (k, f) => { const a = performance.now(); f(); window.tempos[k] = (window.tempos[k] || 0) + performance.now() - a; };
window.quadro = function (t) {
  const u = t;
  _m("pintar", () => pintarPano(u)); _m("moldar", () => moldarPano(u, t));
  // velas: chama e luz tremendo juntas
  velas.forEach((v, i) => { const f = tremor(t, i); v.scale.set(0.05 + 0.02 * f, 0.12 + 0.06 * f, 1); v.material.opacity = 0.75 + 0.25 * f; });
  luzes.forEach((l, i) => { l.intensity = (i ? 6 : 34) * (0.8 + 0.3 * tremor(t, i + 7)); });
  // fumaça e poeira
  fumacas.forEach((f, i) => { const k = (t * 0.06 + i * 0.25) % 1; f.position.y = -0.7 + k * 1.6; f.material.opacity = 0.32 * Math.sin(Math.PI * k); f.rotation.z = Math.sin(t * 0.3 + i) * 0.25; });
  const pa = poeira.geometry.attributes.position, b = poeira.geometry.userData.base, ub = t - TB;
  for (let i = 0; i < pa.count; i++) { let x = b[i * 3] + Math.sin(t * 0.2 + i) * 0.05, y = b[i * 3 + 1] + ((t * 0.03 + i * 0.37) % 1) * 0.3, z = b[i * 3 + 2];
    if (ub > 0 && Math.abs(x - PX) < PW * 0.7 && z < 0.6) { const k = (1 - Math.exp(-ub * 2)) * 0.25; x += (x - PX) * k * 0.4; z += k * 0.5; y += k * 0.2; }
    pa.setXYZ(i, x, y, z); }
  pa.needsUpdate = true;
  // câmera: aproxima devagar, mão leve; o tambor dá um tranco
  const k = easeInOut(lin(t, 0, C.dur || 7.6)), tr = ub > 0 && ub < 0.22 ? (1 - ub / 0.22) : 0;
  camera.position.set(-0.15 + 0.12 * k + (ruido1(t * 0.7) - 0.5) * 0.03 + (ruido1(t * 40) - 0.5) * 0.03 * tr,
    -0.05 + (ruido1(t * 0.6 + 9) - 0.5) * 0.025 + (ruido1(t * 43 + 3) - 0.5) * 0.03 * tr, 6.2 - 0.6 * k);
  camera.lookAt(-0.05 + 0.05 * k, 0.0, 0); bokeh.uniforms.focus.value = camera.position.z - 0.02;
  grain.uniforms.t.value = t;
  _m("render", () => { composer.render(); renderer.getContext().finish(); });
  _m("titulo", () => titulo(u));
  const fade = Math.min(lin(t, 0, 0.35), 1 - lin(t, (C.dur || 7.6) - 0.4, 0.4));
  document.getElementById("veu").style.opacity = String(1 - fade);
  return true;
};
window.pronto = true;
