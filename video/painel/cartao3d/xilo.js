// Cartão de capítulo do Ep. 11 (Escandinávia) — "XILOGRAVURA VIVA" (16/11, refeito a pedido do usuário: "algo mais bem
// feito e marcante", no estilo xilogravura das cenas do episódio — referência: gravura em papel velho, rasgado e dobrado).
// Uma cena 3D de verdade (three.js): PEDRA RÚNICA alta numa clareira de neve, com a SERPENTE entalhada em volta da face
// (a faixa com runas, como nas pedras suecas) e a runa do capítulo no meio; pinheiros com neve, árvore seca em primeiro
// plano, lua entre nuvens, neve caindo. A imagem inteira é IMPRESSA como gravura: a luz vira hachura de tinta (linhas
// que engrossam no escuro, cruzadas nas sombras, contorno nas bordas) sobre papel velho com manchas, vincos e borda
// rasgada. A ÚNICA cor da tela é o vermelho: no tambor (1.6 s) a runa do meio acende como sangue, e o fogo CORRE pela
// serpente, da cauda até a cabeça (1.75–3.3 s); a luz vermelha tinge a neve e brasas sobem. O título entra numa cartela
// impressa (como legenda de livro antigo).
// cfg: {numero, numero_pt, titulo, ano, runa: "othala"|"ansuz"|"algiz"|"ligada", dur}
import * as THREE from "three";
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { RenderPass } from "three/addons/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/addons/postprocessing/UnrealBloomPass.js";
import { ShaderPass } from "three/addons/postprocessing/ShaderPass.js";
import { mergeGeometries } from "three/addons/utils/BufferGeometryUtils.js";

const PH = "/root/.cache/polyhaven/";   // texturas CC0 da Poly Haven (fora do repositório)
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lin = (t, t0, d) => clamp((t - t0) / d);
const easeOut = (x) => 1 - Math.pow(1 - clamp(x), 3);
const easeInOut = (x) => (x = clamp(x), x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
const sstep = (a, b, x) => { const t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t); };
function semente(s) { let h = 2166136261; for (const ch of String(s)) h = Math.imul(h ^ ch.charCodeAt(0), 16777619);
  return () => { h += 0x6D2B79F5; let t = h; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
function ruido1(x) { const i = Math.floor(x), f = x - i, a = semente("n" + i)(), b = semente("n" + (i + 1))(); return a + (b - a) * f * f * (3 - 2 * f); }
// ruído de valor 3D (para deformar a pedra, o chão e as árvores)
function h3(x, y, z) { let h = Math.imul(x | 0, 374761393) + Math.imul(y | 0, 668265263) + Math.imul(z | 0, 2147483647); h = Math.imul(h ^ (h >>> 13), 1274126177); return ((h ^ (h >>> 16)) >>> 0) / 4294967296; }
function vn3(x, y, z) { const xi = Math.floor(x), yi = Math.floor(y), zi = Math.floor(z), xf = x - xi, yf = y - yi, zf = z - zi;
  const u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf), w = zf * zf * (3 - 2 * zf); let s = 0;
  for (let k = 0; k < 8; k++) { const dx = k & 1, dy = (k >> 1) & 1, dz = (k >> 2) & 1;
    s += h3(xi + dx, yi + dy, zi + dz) * (dx ? u : 1 - u) * (dy ? v : 1 - v) * (dz ? w : 1 - w); } return s; }
const fbm3 = (x, y, z) => vn3(x, y, z) * 0.55 + vn3(x * 2.1, y * 2.1, z * 2.1) * 0.3 + vn3(x * 4.3, y * 4.3, z * 4.3) * 0.15;

const TB = 1.6, F0 = 1.75, F1 = 3.3;            // tambor; o fogo corre pela serpente de F0 a F1
const SX = 0.8, SY = 1.6, SZ = 0.3;             // meia-largura, meia-altura, meia-espessura da pedra
const CHAO = -2.2, PX = -1.5, PZ = 0;           // altura do chão; posição da pedra
const PY = CHAO + SY - 0.12;                    // a base fica enterrada na neve
const FW = 1024, FH = 2048;                     // textura da face entalhada
const EW = 512, EH = 1024;                      // mapa do brilho (vermelho)

// runa do capítulo (coordenadas 0..1 de um quadro em pé) — as mesmas do cartão anterior
const RUNAS = {
  othala: [[[0.5, 0.18], [0.75, 0.42], [0.5, 0.66], [0.25, 0.42], [0.5, 0.18]], [[0.5, 0.66], [0.75, 0.86]], [[0.5, 0.66], [0.25, 0.86]]],
  ansuz: [[[0.36, 0.14], [0.36, 0.88]], [[0.36, 0.2], [0.66, 0.38]], [[0.36, 0.42], [0.66, 0.6]]],
  algiz: [[[0.5, 0.14], [0.5, 0.88]], [[0.5, 0.44], [0.24, 0.16]], [[0.5, 0.44], [0.76, 0.16]]],
  ligada: [[[0.5, 0.1], [0.5, 0.9]], [[0.5, 0.36], [0.25, 0.12]], [[0.5, 0.36], [0.75, 0.12]], [[0.5, 0.44], [0.72, 0.62], [0.5, 0.8], [0.28, 0.62], [0.5, 0.44]], [[0.5, 0.8], [0.72, 0.92]], [[0.5, 0.8], [0.28, 0.92]]],
};
// runas do Futhark novo (x ao longo da faixa −.25...25, y atravessando −.5..+.5) para o texto dentro da serpente
const S = [[0, -0.5], [0, 0.5]];
const FUT = {
  i: [S], t: [S, [[-0.25, -0.22], [0, -0.5], [0.25, -0.22]]], s: [[[-0.2, -0.5], [-0.2, -0.05], [0.2, 0.05], [0.2, 0.5]]],
  f: [S, [[0, -0.18], [0.25, -0.45]], [[0, 0.05], [0.25, -0.22]]], u: [[[-0.2, 0.5], [-0.2, -0.5], [0.2, -0.2], [0.2, 0.5]]],
  o: [S, [[-0.22, -0.32], [0.22, -0.12]]], r: [[[-0.2, 0.5], [-0.2, -0.5], [0.2, -0.3], [-0.2, -0.05], [0.2, 0.5]]],
  k: [S, [[0, -0.1], [0.25, -0.4]]], h: [S, [[-0.25, -0.25], [0.25, 0.25]], [[0.25, -0.25], [-0.25, 0.25]]],
  n: [S, [[-0.22, 0.1], [0.22, -0.1]]], a: [S, [[-0.22, -0.1], [0.22, 0.1]]], m: [S, [[0, -0.25], [-0.22, -0.48]], [[0, -0.25], [0.22, -0.48]]],
  l: [S, [[0, -0.5], [0.25, -0.25]]], b: [[[-0.15, 0.5], [-0.15, -0.5], [0.2, -0.25], [-0.15, 0], [0.2, 0.25], [-0.15, 0.5]]],
  þ: [S, [[0, -0.25], [0.22, 0], [0, 0.25]]], R: [S, [[0, 0.25], [-0.22, 0.48]], [[0, 0.25], [0.22, 0.48]]],
};
// "Uppsala · sacrifício · nove noites · o vigia vê" em nórdico antigo, escrito como numa pedra (sem p: b)
const TEXTO = "ubsala:blut:niu:natr:o:uiki:sir:ubsala:blut:niu:natr:o:uiki:sir:ubsala:blut";

let C, W, H, renderer, scene, camera, composer, grava, faceMat, emCan, emCtx, emTex, luzRubra, brasas, neve;
let banda = [], bandaS = [], glifos = [], runaC = [], overlay, octx, papelCan, luaDir;

function canvas(w, h) { const c = document.createElement("canvas"); c.width = w; c.height = h; return c; }
function img(src) { return new Promise((ok, erro) => { const i = new Image(); i.onload = () => ok(i); i.onerror = erro; i.src = src; }); }
function suave(cor0, cor1) { const c = canvas(64, 64), g = c.getContext("2d"), r = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  r.addColorStop(0, cor0); r.addColorStop(1, cor1); g.fillStyle = r; g.fillRect(0, 0, 64, 64); return new THREE.CanvasTexture(c); }

// ---------- a serpente: curva em volta da face (u, v em 0..1; v = 0 no alto) ----------
function catmull(P, n) {
  const out = [];
  for (let i = 0; i < P.length - 1; i++) { const p0 = P[Math.max(0, i - 1)], p1 = P[i], p2 = P[i + 1], p3 = P[Math.min(P.length - 1, i + 2)];
    for (let j = 0; j < n; j++) { const t = j / n, t2 = t * t, t3 = t2 * t;
      out.push([0, 1].map((k) => 0.5 * (2 * p1[k] + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2 + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3))); } }
  out.push(P[P.length - 1]); return out;
}
function montarSerpente() {
  const P = [[0.36, 0.84], [0.25, 0.74], [0.18, 0.56], [0.175, 0.33], [0.235, 0.16], [0.36, 0.075], [0.5, 0.055], [0.64, 0.075],
    [0.765, 0.16], [0.825, 0.33], [0.82, 0.54], [0.78, 0.69], [0.69, 0.79], [0.56, 0.835]];
  const pts = catmull(P, 30).map(([u, v]) => [u * FW, v * FH]);
  const sl = [0]; for (let i = 1; i < pts.length; i++) sl.push(sl[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
  const L = sl[sl.length - 1]; bandaS = sl.map((s) => s / L); banda = pts;
  const bw = 0.085 * FW;
  const em = (s) => { let i = bandaS.findIndex((x) => x >= s); if (i <= 0) i = 1; const a = pts[i - 1], b = pts[i], q = (s - bandaS[i - 1]) / Math.max(1e-6, bandaS[i] - bandaS[i - 1]);
    const tx = b[0] - a[0], ty = b[1] - a[1], tl = Math.hypot(tx, ty) || 1; return { p: [a[0] + tx * q, a[1] + ty * q], T: [tx / tl, ty / tl], N: [-ty / tl, tx / tl] }; };
  // as bordas da faixa (a cauda afina até sumir) — cada uma é uma lista de [x, y, s]
  const larg = (s) => bw * 0.5 * sstep(0, 0.09, s);
  const borda = (sinal) => pts.map((p, i) => { const { N } = em(Math.min(0.9999, Math.max(0.0001, bandaS[i]))); const w = larg(bandaS[i]) * sinal; return [p[0] + N[0] * w, p[1] + N[1] * w, bandaS[i]]; });
  // cabeça: amêndoa na ponta, virada para a cauda, com o olho
  const fim = em(0.9999), cx = fim.p[0] + fim.T[0] * bw * 0.55, cy = fim.p[1] + fim.T[1] * bw * 0.55, ang = Math.atan2(fim.T[1], fim.T[0]);
  const cab = []; for (let k = 0; k <= 40; k++) { const a = (k / 40) * Math.PI * 2, rx = bw * 1.05 * (Math.cos(a) > 0 ? 1.0 : 0.7), ry = bw * 0.75 * (1 - 0.25 * Math.max(0, Math.cos(a)));
    const x = Math.cos(a) * rx, y = Math.sin(a) * ry; cab.push([cx + x * Math.cos(ang) - y * Math.sin(ang), cy + x * Math.sin(ang) + y * Math.cos(ang), 1]); }
  const olho = [cx + Math.cos(ang) * bw * 0.25 - Math.sin(ang) * bw * 0.18, cy + Math.sin(ang) * bw * 0.25 + Math.cos(ang) * bw * 0.18];
  // as runas dentro da faixa
  const sulcos = [{ pts: borda(1), w: 15 }, { pts: borda(-1), w: 15 }, { pts: cab, w: 14, cabeca: true }];
  const passo = (bw * 0.6) / (sl[sl.length - 1]); let s = 0.1;
  for (const ch of TEXTO) {
    if (s > 0.93) break;
    const { p, T, N } = em(s), h = bw * 0.62;
    if (ch === ":") { for (const d of [-0.16, 0.16]) glifos.push({ s, pontos: [[p[0] + N[0] * d * h, p[1] + N[1] * d * h]], w: 11 }); s += passo * 0.55; continue; }
    for (const tr of FUT[ch] || FUT.i) glifos.push({ s, pts: tr.map(([x, y]) => [p[0] + T[0] * x * h + N[0] * y * h, p[1] + T[1] * x * h + N[1] * y * h, s]), w: 10 });
    s += passo;
  }
  // a runa do capítulo no meio
  for (const tr of RUNAS[C.runa] || RUNAS.algiz) runaC.push({ pts: tr.map(([x, y]) => [(0.29 + x * 0.42) * FW, (0.2 + y * 0.6) * FH, 0]), w: 44 });
  return { sulcos, olho };
}
function linha(g, pts, ate = 2, esc = 1) {   // linha poligonal até o parâmetro s = ate
  g.beginPath(); let ok = false;
  for (let i = 0; i < pts.length; i++) { const [x, y, s] = pts[i]; if (s > ate) {
      if (i > 0) { const [x0, y0, s0] = pts[i - 1], q = (ate - s0) / Math.max(1e-6, s - s0); g.lineTo((x0 + (x - x0) * q) * esc, (y0 + (y - y0) * q) * esc); } break; }
    if (!ok) { g.moveTo(x * esc, y * esc); ok = true; } else g.lineTo(x * esc, y * esc); }
  g.stroke();
}

// ---------- a pedra ----------
async function montarPedra(serp) {
  const rocha = await img(PH + "lichen_rock/Diffuse.jpg"), desl = await img(PH + "lichen_rock/Displacement.jpg");
  // pedra cinza (granito com líquen): a textura dessaturada
  const lado = canvas(1024, 1024), lg = lado.getContext("2d"); lg.filter = "saturate(0.2) brightness(1.15) contrast(0.75) blur(1.5px)"; lg.drawImage(rocha, 0, 0, 1024, 1024); lg.filter = "none"; lg.globalAlpha = 0.35; lg.fillStyle = "#8d8d90"; lg.fillRect(0, 0, 1024, 1024); lg.globalAlpha = 1;
  const tLado = new THREE.CanvasTexture(lado); tLado.wrapS = tLado.wrapT = THREE.RepeatWrapping; tLado.repeat.set(1.4, 2.2); tLado.colorSpace = THREE.SRGBColorSpace;
  // a face: cor (com a tinta ocre gasta nos sulcos), altura (sulcos em V) → mapa de normais
  const cor = canvas(FW, FH), cg = cor.getContext("2d"), tile = FW / (SX * 2);
  for (let y = 0; y < FH; y += tile) for (let x = 0; x < FW; x += tile) cg.drawImage(lado, x, y, tile, tile);
  const alt = canvas(FW, FH), ag = alt.getContext("2d");
  ag.filter = "grayscale(1) contrast(0.9)"; for (let y = 0; y < FH; y += tile) for (let x = 0; x < FW; x += tile) ag.drawImage(desl, x, y, tile, tile);
  ag.filter = "none"; ag.globalAlpha = 0.5; ag.fillStyle = "#c8c8c8"; ag.fillRect(0, 0, FW, FH); ag.globalAlpha = 1;
  const todos = [...serp.sulcos, ...glifos.filter((g) => g.pts), ...runaC];
  ag.lineCap = cg.lineCap = "round"; ag.lineJoin = cg.lineJoin = "round";
  for (const sk of todos) { ag.save(); ag.filter = `blur(${sk.w * 0.35}px)`; ag.strokeStyle = "#202020"; ag.lineWidth = sk.w * 1.25; linha(ag, sk.pts); ag.restore();
    ag.save(); ag.filter = `blur(${sk.w * 0.12}px)`; ag.strokeStyle = "#000"; ag.lineWidth = sk.w * 0.55; linha(ag, sk.pts); ag.restore();
    cg.strokeStyle = "rgba(30,22,20,.75)"; cg.lineWidth = sk.w * 1.0; linha(cg, sk.pts); cg.strokeStyle = "rgba(118,34,22,.55)"; cg.lineWidth = sk.w * 0.55; linha(cg, sk.pts); }
  for (const g of glifos.filter((g) => g.pontos)) for (const [x, y] of g.pontos) { ag.fillStyle = "#000"; ag.beginPath(); ag.arc(x, y, 7, 0, 7); ag.fill(); cg.fillStyle = "rgba(30,22,20,.8)"; cg.beginPath(); cg.arc(x, y, 7, 0, 7); cg.fill(); }
  ag.fillStyle = "#000"; ag.beginPath(); ag.arc(serp.olho[0], serp.olho[1], 12, 0, 7); ag.fill();
  // normais a partir da altura
  const hd = ag.getImageData(0, 0, FW, FH).data, nor = canvas(FW, FH), ng = nor.getContext("2d"), nd = ng.createImageData(FW, FH), K = 5.0;
  const hh = (x, y) => hd[((Math.min(FH - 1, Math.max(0, y)) * FW) + Math.min(FW - 1, Math.max(0, x))) * 4] / 255;
  for (let y = 0; y < FH; y++) for (let x = 0; x < FW; x++) {
    const du = (hh(x + 1, y) - hh(x - 1, y)) * K, dv = (hh(x, y - 1) - hh(x, y + 1)) * K, l = Math.hypot(du, dv, 1), o = (y * FW + x) * 4;
    nd.data[o] = (-du / l * 0.5 + 0.5) * 255; nd.data[o + 1] = (-dv / l * 0.5 + 0.5) * 255; nd.data[o + 2] = (1 / l * 0.5 + 0.5) * 255; nd.data[o + 3] = 255; }
  ng.putImageData(nd, 0, 0);
  // altura suave (só os sulcos) para afundar a malha de verdade
  const sm = canvas(256, 512), sg = sm.getContext("2d"); sg.fillStyle = "#fff"; sg.fillRect(0, 0, 256, 512); sg.lineCap = "round"; sg.lineJoin = "round";
  for (const sk of todos) { sg.save(); sg.filter = "blur(1.5px)"; sg.strokeStyle = "#000"; sg.lineWidth = sk.w * 0.25 * 0.9; linha(sg, sk.pts, 2, 0.25); sg.restore(); }
  const smd = sg.getImageData(0, 0, 256, 512).data, sulco = (u, v) => { const x = Math.min(255, Math.max(0, Math.round(u * 255))), y = Math.min(511, Math.max(0, Math.round((1 - v) * 511))); return 1 - smd[(y * 256 + x) * 4] / 255; };

  const tCor = new THREE.CanvasTexture(cor); tCor.colorSpace = THREE.SRGBColorSpace; tCor.anisotropy = 8;
  const tNor = new THREE.CanvasTexture(nor); tNor.anisotropy = 8;
  emCan = canvas(EW, EH); emCtx = emCan.getContext("2d"); emTex = new THREE.CanvasTexture(emCan);
  faceMat = comNeve(new THREE.MeshStandardMaterial({ map: tCor, normalMap: tNor, normalScale: new THREE.Vector2(2.6, 2.6), roughness: 0.9, color: 0xa8a8ac,
    emissive: new THREE.Color(0xff2a12), emissiveMap: emTex, emissiveIntensity: 0 }));
  const ladoMat = comNeve(new THREE.MeshStandardMaterial({ map: tLado, roughness: 0.95, color: 0x9a9a9e }));

  // malha: caixa bem dividida → superelipsoide (bordas arredondadas), afina no alto, irregular, face entalhada
  const g = new THREE.BoxGeometry(2, 2, 2, 110, 200, 14), pos = g.attributes.position, uv = g.attributes.uv;
  const frente = new Set(); { const gr = g.groups[4]; for (let i = gr.start; i < gr.start + gr.count; i++) frente.add(g.index.array[i]); }
  for (let i = 0; i < pos.count; i++) {
    let a = pos.getX(i), b = pos.getY(i), c = pos.getZ(i);
    const n = 8 - 4.8 * sstep(-0.3, 0.7, b), nz = 5, m = Math.max(Math.abs(a), Math.abs(b), Math.abs(c));
    const sN = Math.pow(Math.pow(Math.abs(a), n) + Math.pow(Math.abs(b), n) + Math.pow(Math.abs(c), nz), 1 / Math.max(n, nz));
    const f = m / Math.max(1e-6, sN); a *= f; b *= f; c *= f;
    const yy = (b + 1) / 2, top = Math.max(0, b);
    let x = a * SX * (1 - 0.14 * yy), y = b * SY - 0.18 * top * top * (a > 0 ? 1.0 : 0.3) * Math.abs(a), z = c * SZ * (1 - 0.2 * yy);
    const nn = (fbm3(x * 1.4 + 3, y * 1.4, z * 1.4) - 0.5) * 0.12 + (fbm3(x * 6, y * 6, z * 6) - 0.5) * 0.025;
    x *= 1 + nn; z *= 1 + nn * 0.8; y += nn * 0.3 * Math.max(0, b);
    if (frente.has(i)) z -= 0.022 * sulco(uv.getX(i), uv.getY(i));
    pos.setXYZ(i, x, y, z);
  }
  g.computeVertexNormals(); suavizarCostura(g);
  // neve no topo e acumulada na base
  const nr = g.attributes.normal, nv = new Float32Array(pos.count);
  for (let i = 0; i < pos.count; i++) { const y = pos.getY(i), x = pos.getX(i), z = pos.getZ(i);
    nv[i] = clamp(sstep(0.45, 0.8, nr.getY(i)) * (0.55 + 0.6 * fbm3(x * 5, y * 5, z * 5)) + sstep(-SY + 0.75, -SY + 0.2, y) * (0.4 + 0.6 * fbm3(x * 4, 0, z * 4))); }
  g.setAttribute("neve", new THREE.BufferAttribute(nv, 1));
  const pedra = new THREE.Mesh(g, [ladoMat, ladoMat, ladoMat, ladoMat, faceMat, ladoMat]);
  pedra.position.set(PX, PY, PZ); pedra.rotation.y = 0.22; pedra.rotation.z = -0.03; pedra.castShadow = pedra.receiveShadow = true; scene.add(pedra);
  return pedra;
}
function suavizarCostura(g) {   // a caixa tem vértices repetidos nas arestas: média das normais por posição
  const p = g.attributes.position, n = g.attributes.normal, mapa = new Map();
  for (let i = 0; i < p.count; i++) { const k = `${p.getX(i).toFixed(4)},${p.getY(i).toFixed(4)},${p.getZ(i).toFixed(4)}`; (mapa.get(k) || mapa.set(k, []).get(k)).push(i); }
  for (const l of mapa.values()) { if (l.length < 2) continue; let x = 0, y = 0, z = 0; for (const i of l) { x += n.getX(i); y += n.getY(i); z += n.getZ(i); }
    const m = Math.hypot(x, y, z) || 1; for (const i of l) n.setXYZ(i, x / m, y / m, z / m); }
}
function comNeve(mat) {   // atributo "neve" (0..1): branqueia a superfície
  mat.onBeforeCompile = (sh) => {
    sh.vertexShader = "attribute float neve;\nvarying float vNeve;\n" + sh.vertexShader.replace("#include <begin_vertex>", "#include <begin_vertex>\nvNeve = neve;");
    sh.fragmentShader = "varying float vNeve;\n" + sh.fragmentShader.replace("#include <map_fragment>", "#include <map_fragment>\ndiffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.93,0.95,1.0), clamp(vNeve,0.,1.));");
  };
  return mat;
}
function poeNeve(geo, f) { const p = geo.attributes.position, n = geo.attributes.normal, v = new Float32Array(p.count);
  for (let i = 0; i < p.count; i++) v[i] = f(p.getX(i), p.getY(i), p.getZ(i), n.getY(i)); geo.setAttribute("neve", new THREE.BufferAttribute(v, 1)); return geo; }

// ---------- a mata ----------
function pinheiros() {   // abetos de verdade: cada andar é um leque de RAMOS serrilhados caídos (silhueta espinhosa da gravura)
  const r = semente("mata"), P = [], N = [], troncos = [];
  const tri = (a, b, c, nv) => { P.push(...a, ...b, ...c); N.push(nv, nv, nv); };
  for (let k = 0; k < 90; k++) {
    const x = -24 + r() * 48, z = -5 - r() * 26; if (Math.abs(x - PX) < 3.2 && z > -16) continue;
    const h = 5 + r() * 8, base = CHAO - 0.1, inc = (r() - 0.5) * 0.06;
    const tr = new THREE.CylinderGeometry(0.04 * h / 6, 0.13 * h / 6, h, 6, 1, true); tr.translate(x, base + h * 0.5, z); troncos.push(tr);
    const andares = 16 + Math.floor(r() * 6);
    for (let j = 0; j < andares; j++) {
      const q = j / andares, y0 = base + h * (0.12 + 0.86 * q), raio = Math.pow(1 - q, 0.95) * h * 0.24 + 0.08, nr = 9 + Math.floor(raio * 9);
      for (let b = 0; b < nr; b++) {
        const th = (b / nr) * Math.PI * 2 + r() * 0.5 + j * 0.9, dx = Math.cos(th), dz = Math.sin(th), L = raio * (0.75 + 0.45 * r());
        const queda = 0.35 + 0.35 * r(), wb = L * 0.32, sx = -dz, sz = dx, nv = r() < 0.5 ? 1 : 0;   // nv: o ramo pega neve?
        const ponto = (u, lado) => { const w = (wb * (1 - u) + 0.015) * (Math.floor(u * 7) % 2 ? 0.55 : 1) * lado;
          return [x + inc * (y0 - base) + dx * L * u + sx * w, y0 + L * (0.12 * u - queda * u * u), z + dz * L * u + sz * w]; };
        for (let m = 0; m < 7; m++) { const u0 = m / 7, u1 = (m + 1) / 7;
          const a = ponto(u0, 1), b2 = ponto(u0, -1), c = ponto(u1, 1), d = ponto(u1, -1), nn = nv * sstep(0.45, 0.7, fbm3(a[0] * 2, a[1] * 2, a[2] * 2)) * 0.85;
          tri(a, b2, c, nn); tri(b2, d, c, nn); }
      }
    }
  }
  const g = new THREE.BufferGeometry(); g.setAttribute("position", new THREE.Float32BufferAttribute(P, 3)); g.setAttribute("neve", new THREE.Float32BufferAttribute(N, 1)); g.computeVertexNormals();
  const m = new THREE.Mesh(g, comNeve(new THREE.MeshStandardMaterial({ color: 0x0a0d0b, roughness: 1, side: THREE.DoubleSide }))); m.receiveShadow = true; scene.add(m);
  const t = new THREE.Mesh(mergeGeometries(troncos.map((x) => poeNeve(x, () => 0))), comNeve(new THREE.MeshStandardMaterial({ color: 0x15100c, roughness: 1 }))); scene.add(t);
}
function arvoreSeca() {   // árvore retorcida em primeiro plano (esquerda), galhos por cima do quadro
  const r = semente("arvore"), gs = [];
  const galho = (a, d, len, rad, nivel) => {
    let p = a.clone(), dir = d.clone(), rr = rad;
    for (let k = 0; k < 3; k++) {   // cada galho em 3 trechos que entortam: madeira retorcida
      const l = len / 3, b = p.clone().addScaledVector(dir, l), r1 = rr * 0.86, geo = new THREE.CylinderGeometry(r1, rr, l * 1.04, nivel < 3 ? 9 : 5, 1, true);
      geo.translate(0, l / 2, 0); geo.applyQuaternion(new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir)); geo.translate(p.x, p.y, p.z);
      gs.push(poeNeve(geo, (X, Y, Z, ny) => sstep(0.35, 0.75, ny) * (0.4 + 0.7 * fbm3(X * 6, Y * 6, Z * 6))));
      p = b; rr = r1; dir.add(new THREE.Vector3((r() - 0.5) * 0.55, (r() - 0.5) * 0.4, (r() - 0.5) * 0.4)).normalize();
    }
    if (nivel >= 7 || rr < 0.006) return;
    const filhos = nivel < 2 ? 2 : 2 + (r() < 0.6 ? 1 : 0);
    for (let k = 0; k < filhos; k++) {
      const nd = dir.clone().add(new THREE.Vector3((r() - 0.35) * 1.2, (r() - 0.4) * 0.9, (r() - 0.5) * 0.8)).normalize();
      if (nivel < 3) nd.add(new THREE.Vector3(1.1, -0.15, 0.1)).normalize();   // o tronco tomba para a direita, por cima da pedra
      galho(p, nd, len * (0.6 + r() * 0.22), rr * 0.66, nivel + 1);
    }
  };
  galho(new THREE.Vector3(-4.9, CHAO - 0.2, 0.6), new THREE.Vector3(0.22, 1, 0.05).normalize(), 3.0, 0.26, 0);
  const m = new THREE.Mesh(mergeGeometries(gs), comNeve(new THREE.MeshStandardMaterial({ color: 0x241b14, roughness: 1 })));
  m.castShadow = true; scene.add(m);
}
function chao() {
  const tx = new THREE.TextureLoader();
  const dif = tx.load(PH + "snow_02/Diffuse.jpg"), nor = tx.load(PH + "snow_02/nor_gl.jpg");
  for (const t of [dif, nor]) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(14, 10); } dif.colorSpace = THREE.SRGBColorSpace;
  const g = new THREE.PlaneGeometry(70, 50, 240, 170); g.rotateX(-Math.PI / 2); const p = g.attributes.position;
  for (let i = 0; i < p.count; i++) { const x = p.getX(i), z = p.getZ(i), d = Math.hypot(x - PX, z - PZ);
    p.setY(i, CHAO + (fbm3(x * 0.35, 0, z * 0.35) - 0.5) * 0.5 + 0.16 * Math.exp(-d * d / 0.9) + (fbm3(x * 2, 1, z * 2) - 0.5) * 0.06); }
  g.computeVertexNormals();
  const m = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ map: dif, normalMap: nor, roughness: 0.85, color: 0xb4b9c2 })); m.receiveShadow = true; scene.add(m);
  // pedras com neve em primeiro plano (como na gravura)
  const rr = semente("pedrinhas"), gs = [];
  for (const [x, z, s] of [[-2.6, 3.4, 0.55], [1.0, 3.9, 0.4], [2.6, 2.8, 0.5], [-0.6, 4.6, 0.3], [3.8, 4.2, 0.6]]) {
    const geo = new THREE.SphereGeometry(s, 28, 18), q = geo.attributes.position;
    for (let i = 0; i < q.count; i++) { const X = q.getX(i), Y = q.getY(i), Z = q.getZ(i), k = 1 + (fbm3(X * 3 + x, Y * 3, Z * 3) - 0.5) * 0.5; q.setXYZ(i, X * k * 1.4, Y * k * 0.55, Z * k); }
    geo.computeVertexNormals(); geo.translate(x, CHAO + 0.02, z); gs.push(poeNeve(geo, (X, Y, Z, ny) => sstep(0.2, 0.6, ny) * (0.6 + 0.5 * fbm3(X * 5, Y * 5, Z * 5)) + rr() * 0));
  }
  const pm = new THREE.Mesh(mergeGeometries(gs), comNeve(new THREE.MeshStandardMaterial({ color: 0x2b2b2e, roughness: 1 }))); pm.receiveShadow = pm.castShadow = true; scene.add(pm);
  // morros ao longe
  const mo = new THREE.MeshStandardMaterial({ color: 0x5a6068, roughness: 1 });
  for (const [x, z, sx, sy] of []) { const s = new THREE.Mesh(new THREE.SphereGeometry(1, 32, 16), mo); s.scale.set(sx, sy, 10); s.position.set(x, CHAO - 1, z); scene.add(s); }
}
function encapuzados() {   // vultos de manto e capuz na beira da mata — SEM rosto (o capuz é um buraco escuro)
  const gs = [], escuros = [], r = semente("vultos");
  const perfil = [[0, 0], [0.46, 0], [0.44, 0.06], [0.36, 0.35], [0.28, 0.75], [0.26, 1.05], [0.25, 1.22], [0.2, 1.36], [0.11, 1.44], [0, 1.47]].map(([a, b]) => new THREE.Vector2(a, b));
  for (const [x, z, s, lanca] of [[-4.4, -4.2, 1.0, 1], [-3.1, -5.6, 0.95, 0], [0.3, -5.2, 1.0, 0], [1.6, -4.0, 1.05, 1]]) {
    const manto = new THREE.LatheGeometry(perfil, 22), q = manto.attributes.position;
    for (let i = 0; i < q.count; i++) { const X = q.getX(i), Y = q.getY(i), Z = q.getZ(i), k = (1 + (fbm3(X * 5 + x, Y * 3, Z * 5) - 0.5) * 0.3 * (1 - Y / 1.5)) * (1 + 0.09 * Math.sin(Math.atan2(Z, X) * 7) * (1 - Y / 1.6)); q.setXYZ(i, X * k, Y, Z * k * 0.75); }
    manto.computeVertexNormals();
    const capuz = new THREE.SphereGeometry(0.2, 18, 14); capuz.scale(1, 1.25, 1.2); capuz.rotateX(0.25); capuz.translate(0, 1.55, 0.05);
    const ponta = new THREE.ConeGeometry(0.13, 0.3, 10); ponta.rotateX(-0.7); ponta.translate(0, 1.78, -0.12);
    const ext = (g) => { g.scale(s, s, s); g.rotateY((r() - 0.5) * 0.3); g.translate(x, CHAO - 0.05, z); gs.push(poeNeve(g, (X, Y, Z, ny) => sstep(0.6, 0.9, ny) * 0.6)); };
    ext(manto); ext(capuz); ext(ponta);
    if (lanca) { const l = new THREE.CylinderGeometry(0.018, 0.022, 2.6, 6, 1, true), c = new THREE.ConeGeometry(0.05, 0.28, 6); l.translate(0.36, 1.3, 0.08); c.translate(0.36, 2.72, 0.08); ext(l); ext(c); }
    const vazio = new THREE.SphereGeometry(0.12, 12, 10); vazio.scale(0.85, 1.05, 0.5); vazio.rotateX(0.25); vazio.translate(0, 1.52, 0.22); vazio.scale(s, s, s); vazio.translate(x, CHAO - 0.05, z); escuros.push(poeNeve(vazio, () => 0));
  }
  const m = new THREE.Mesh(mergeGeometries(gs), comNeve(new THREE.MeshStandardMaterial({ color: 0x1a1612, roughness: 1 }))); m.castShadow = true; scene.add(m);
  scene.add(new THREE.Mesh(mergeGeometries(escuros), new THREE.MeshBasicMaterial({ color: 0x000000 })));
}
function capim() {   // tufos de capim seco furando a neve (traços de tinta no chão, como na gravura)
  const r = semente("capim"), P = [];
  for (let k = 0; k < 140; k++) {
    const x = -6 + r() * 11.5, z = -3 + r() * 8; if (Math.hypot(x - PX, z - PZ) < 0.9) continue;
    const y0 = CHAO + (fbm3(x * 0.35, 0, z * 0.35) - 0.5) * 0.5 - 0.02, n = 5 + Math.floor(r() * 9), alto = 0.12 + r() * 0.3;
    for (let b = 0; b < n; b++) { const a = r() * 6.28, inc = 0.2 + r() * 0.6, hh = alto * (0.5 + r() * 0.6), w = 0.006 + r() * 0.006;
      const tx = x + Math.cos(a) * hh * inc, tz = z + Math.sin(a) * hh * inc, bx = x + (r() - 0.5) * 0.08, bz = z + (r() - 0.5) * 0.08;
      P.push(bx - w, y0, bz, bx + w, y0, bz, tx, y0 + hh, tz, bx, y0, bz - w, bx, y0, bz + w, tx, y0 + hh, tz); }
  }
  const g = new THREE.BufferGeometry(); g.setAttribute("position", new THREE.Float32BufferAttribute(P, 3)); g.computeVertexNormals();
  scene.add(new THREE.Mesh(g, new THREE.MeshStandardMaterial({ color: 0x1b140d, roughness: 1, side: THREE.DoubleSide })));
}
function ceu() {
  const mat = new THREE.ShaderMaterial({ side: THREE.BackSide, depthWrite: false, fog: false,
    uniforms: { lua: { value: luaDir }, t: { value: 0 } },
    vertexShader: "varying vec3 vP;void main(){vP=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}",
    fragmentShader: `uniform vec3 lua;uniform float t;varying vec3 vP;
      float h(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
      float vn(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(h(i),h(i+vec2(1,0)),f.x),mix(h(i+vec2(0,1)),h(i+vec2(1,1)),f.x),f.y);}
      float fbm(vec2 p){float s=0.,a=.5;for(int i=0;i<5;i++){s+=a*vn(p);p*=2.03;a*=.5;}return s;}
      void main(){vec3 d=normalize(vP);float y=max(d.y,0.);
        vec3 c=mix(vec3(.10,.105,.12),vec3(.012,.014,.02),smoothstep(0.,.5,y));
        vec2 q=d.xz/(y+.18);float nu=fbm(vec2(q.x*.55+t*.03,q.y*1.9));nu=smoothstep(.42,.78,nu);
        float m=dot(d,normalize(lua));float ang=acos(clamp(m,-1.,1.));
        float halo=exp(-ang*12.)*.18+exp(-ang*40.)*.5;
        c=mix(c,vec3(.16,.17,.19)*(.4+halo*2.2),nu*.9);
        c+=vec3(.75,.78,.85)*halo*.22*(1.-nu*.6);
        float disco=1.-smoothstep(.047,.052,ang);float cr=fbm(vec2(d.x,d.y)*28.+3.);
        float anel=smoothstep(.044,.049,ang)*(1.-smoothstep(.052,.057,ang));c=mix(c,vec3(1.25,1.22,1.15)*(.2+.8*smoothstep(.38,.62,cr)),disco*(1.-nu*.45));c*=1.-anel*.9;
        gl_FragColor=vec4(c,1.);}` });
  const s = new THREE.Mesh(new THREE.SphereGeometry(90, 48, 24), mat); scene.add(s); return mat;
}

// ---------- o papel (fundo da gravura) ----------
function papel() {
  const c = canvas(W, H), g = c.getContext("2d"), r = semente("papel");
  g.fillStyle = "#dcc59a"; g.fillRect(0, 0, W, H);
  const pq = canvas(160, 90), pg = pq.getContext("2d"), id = pg.createImageData(160, 90);
  for (let i = 0; i < id.data.length; i += 4) { const v = 150 + r() * 105; id.data[i] = v; id.data[i + 1] = v * 0.93; id.data[i + 2] = v * 0.8; id.data[i + 3] = 255; }
  pg.putImageData(id, 0, 0); g.save(); g.globalCompositeOperation = "multiply"; g.globalAlpha = 0.35; g.imageSmoothingEnabled = true; g.filter = "blur(6px)"; g.drawImage(pq, 0, 0, W, H); g.restore();
  for (let i = 0; i < 46; i++) { const x = r() * W, y = r() * H, rad = 40 + r() * 260, gr = g.createRadialGradient(x, y, 0, x, y, rad);
    gr.addColorStop(0, `rgba(${110 + r() * 40},${70 + r() * 30},30,${0.04 + r() * 0.1})`); gr.addColorStop(1, "rgba(120,80,30,0)"); g.fillStyle = gr; g.fillRect(x - rad, y - rad, rad * 2, rad * 2); }
  for (let i = 0; i < 260; i++) { g.fillStyle = `rgba(110,65,25,${0.08 + r() * 0.25})`; g.beginPath(); g.arc(r() * W, r() * H, 0.6 + r() * 2.6, 0, 7); g.fill(); }
  for (let i = 0; i < 4000; i++) { const x = r() * W, y = r() * H, a = r() * 6.3, l = 3 + r() * 10; g.strokeStyle = `rgba(90,60,30,${0.05 + r() * 0.07})`; g.lineWidth = 0.6;
    g.beginPath(); g.moveTo(x, y); g.lineTo(x + Math.cos(a) * l, y + Math.sin(a) * l); g.stroke(); }
  // vincos (dobras do papel)
  const vinco = (x0, y0, x1, y1) => { g.save(); g.filter = "blur(6px)"; g.strokeStyle = "rgba(90,58,25,.28)"; g.lineWidth = 12; g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1, y1); g.stroke(); g.restore();
    g.strokeStyle = "rgba(70,45,20,.45)"; g.lineWidth = 1.6; g.beginPath(); g.moveTo(x0, y0); for (let k = 1; k <= 30; k++) g.lineTo(x0 + (x1 - x0) * k / 30 + (r() - 0.5) * 2, y0 + (y1 - y0) * k / 30 + (r() - 0.5) * 2); g.stroke();
    g.strokeStyle = "rgba(255,240,210,.35)"; g.lineWidth = 1.4; g.beginPath(); g.moveTo(x0 + 2.5, y0 + 2.5); g.lineTo(x1 + 2.5, y1 + 2.5); g.stroke(); };
  vinco(W * 0.698, 0, W * 0.703, H); vinco(0, H * 0.455, W, H * 0.462);
  // bordas queimadas e rasgadas
  for (const [x0, y0, x1, y1] of [[0, 0, 110, 0], [W, 0, W - 110, 0], [0, 0, 0, 110], [0, H, 0, H - 110]]) {
    const gr = g.createLinearGradient(x0, y0, x1, y1); gr.addColorStop(0, "rgba(80,45,15,.6)"); gr.addColorStop(1, "rgba(80,45,15,0)"); g.fillStyle = gr; g.fillRect(0, 0, W, H); }
  const pts = [], m = 16, rb = semente("rasgo"), jag = (k) => 7 * (ruido1(k * 0.09) - 0.5) + 4 * (rb() - 0.5);
  const canto = (x, y) => { const d = Math.min(Math.hypot(x, y), Math.hypot(W - x, y), Math.hypot(x, H - y), Math.hypot(W - x, H - y)); return 26 * Math.exp(-d / 40); };
  for (let x = 0; x <= W; x += 6) pts.push([x, m + jag(x) + canto(x, 0)]);
  for (let y = 0; y <= H; y += 6) pts.push([W - m - jag(y + 999) - canto(W, y), y]);
  for (let x = W; x >= 0; x -= 6) pts.push([x, H - m - jag(x + 3333) - canto(x, H)]);
  for (let y = H; y >= 0; y -= 6) pts.push([m + jag(y + 7777) + canto(0, y), y]);
  g.save(); g.beginPath(); g.rect(0, 0, W, H); g.moveTo(pts[0][0], pts[0][1]); for (const [x, y] of pts) g.lineTo(x, y); g.closePath();
  g.fillStyle = "#0b0806"; g.fill("evenodd"); g.restore();
  g.save(); g.beginPath(); g.moveTo(pts[0][0], pts[0][1]); for (const [x, y] of pts) g.lineTo(x, y); g.closePath(); g.strokeStyle = "rgba(60,32,10,.7)"; g.lineWidth = 3; g.filter = "blur(2px)"; g.stroke(); g.restore();
  return c;
}

// ---------- a impressão: luz → hachura de tinta sobre o papel; vermelho fica vermelho ----------
function passeGravura(tPapel) {
  return new ShaderPass({
    uniforms: { tDiffuse: { value: null }, tPapel: { value: tPapel }, res: { value: new THREE.Vector2(W, H) }, t: { value: 0 }, expo: { value: 1.0 }, cru: { value: 0 }, tremido: { value: new THREE.Vector2() } },
    vertexShader: "varying vec2 vUv;void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}",
    fragmentShader: `uniform sampler2D tDiffuse,tPapel;uniform vec2 res,tremido;uniform float t,expo,cru;varying vec2 vUv;
      float h(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
      float vn(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(h(i),h(i+vec2(1,0)),f.x),mix(h(i+vec2(0,1)),h(i+vec2(1,1)),f.x),f.y);}
      vec3 aces(vec3 x){return clamp((x*(2.51*x+.03))/(x*(2.43*x+.59)+.14),0.,1.);}
      vec3 cor(vec2 uv){return pow(aces(texture2D(tDiffuse,uv).rgb*expo),vec3(1./2.2));}
      float lum(vec3 c){return dot(c,vec3(.3,.59,.11));}
      float hach(vec2 q,float a,float s,float d,float semente){
        if(d<=0.)return 0.;vec2 dir=vec2(cos(a),sin(a));
        float k=dot(q,dir)/s;float v=abs(fract(k)-.5)*2.;
        float corte=vn(vec2(floor(k)*3.1+semente,dot(q,vec2(-dir.y,dir.x))*.045));   // a goiva falha às vezes
        float w=clamp(d,0.,1.)*(.75+.5*corte);
        return 1.-smoothstep(w-.28,w+.08,v);}
      void main(){
        vec2 px=gl_FragCoord.xy, uv=vUv;
        vec3 c=cor(uv);float l=lum(c);
        float rubro=clamp((c.r-max(c.g,c.b)*1.15)*2.4,0.,1.)*smoothstep(.3,.65,c.r);
        float L=smoothstep(.07,.56,l);
        vec2 w=vec2(vn(px*.006+tremido),vn(px*.006+17.+tremido))*9.;   // linhas levemente onduladas (talho à mão)
        vec2 q=px+w+tremido;
        // a goiva segue a forma: as linhas correm ao longo dos contornos de luz (gradiente borrado), senão a 24°
        vec2 E=18./res;vec2 gdir=vec2(0.);
        for(int i=-1;i<=1;i++)for(int j=-1;j<=1;j++){vec2 o=uv+vec2(float(i),float(j))*14./res;
          gdir+=vec2(lum(cor(o+vec2(E.x,0)))-lum(cor(o-vec2(E.x,0))),lum(cor(o+vec2(0,E.y)))-lum(cor(o-vec2(0,E.y))));}
        gdir/=9.;float gm=length(gdir);
        float a0=.42;
        if(gm>.05){vec2 tg=normalize(vec2(-gdir.y,gdir.x));if(tg.x<0.)tg=-tg;float ac=atan(tg.y,tg.x)+1.5708;a0=mix(a0,ac,smoothstep(.05,.2,gm)*.7);}
        float tinta=hach(q,a0,4.6,min((1.-L)*.95,.8),0.);
        tinta=max(tinta,hach(q,a0-1.05,5.6,min((.38-L)*1.6,.55),7.));
        tinta=max(tinta,1.-smoothstep(.0,.07,L));
        vec2 e=2.2/res;
        float gx=lum(cor(uv+vec2(e.x,0)))-lum(cor(uv-vec2(e.x,0)));
        float gy=lum(cor(uv+vec2(0,e.y)))-lum(cor(uv-vec2(0,e.y)));
        tinta=max(tinta,smoothstep(.12,.26,length(vec2(gx,gy)))*.95);
        tinta=max(tinta,1.-smoothstep(.0,.06,l));
        tinta*=.9+.1*vn(px*.35);                                      // tinta que pegou mais/menos no papel
        vec3 pap=texture2D(tPapel,vec2(uv.x,1.-uv.y)).rgb;
        float borda=step(.12,pap.r);                                    // fora do papel rasgado: fundo preto
        vec3 tintaCor=vec3(.15,.095,.055);
        vec3 o=mix(pap,tintaCor*(.85+.3*pap),tinta*.94);
        vec3 sangue=mix(vec3(.42,.03,.02),vec3(1.,.36,.18),smoothstep(.45,1.,l));
        o=mix(o,sangue*(.75+.25*pap.r),smoothstep(.0,.55,rubro));
        gl_FragColor=vec4(mix(pap,o,borda),1.);if(cru>.5)gl_FragColor=vec4(c,1.);
      }` });
}

window.preparar = async function (cfg) {
  C = cfg; W = cfg.W || 1920; H = cfg.H || 1080;
  await document.fonts.load('400 40px "IM Fell English SC"'); await document.fonts.load('italic 400 40px "IM Fell English"'); await document.fonts.load('700 40px "Cinzel"'); await document.fonts.load('500 40px "Inter"'); await document.fonts.load('700 40px "Inter"');
  const gl = document.getElementById("gl"); gl.width = W; gl.height = H;
  renderer = new THREE.WebGLRenderer({ canvas: gl, antialias: false, preserveDrawingBuffer: true });
  renderer.setSize(W, H, false); renderer.setPixelRatio(1);
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  scene = new THREE.Scene(); scene.fog = new THREE.FogExp2(0x2a2f36, 0.035);
  camera = new THREE.PerspectiveCamera(36, W / H, 0.1, 200);
  posCamera(0); camera.updateMatrixWorld();
  luaDir = new THREE.Vector3(-0.02, 0.62, 0.5).unproject(camera).sub(camera.position).normalize();
  const ceuMat = ceu(); scene.userData.ceu = ceuMat;
  pinheiros(); arvoreSeca(); chao(); encapuzados(); capim();
  const serp = montarSerpente(); await montarPedra(serp); scene.userData.olho = serp.olho; scene.userData.sulcos = serp.sulcos;
  // luzes: a lua atrás (contraluz e sombras longas vindo para a câmera), luar rasante pela esquerda (mostra os sulcos)
  const lua = new THREE.DirectionalLight(0xc8d6ff, 1.8); lua.position.copy(luaDir).multiplyScalar(25).add(new THREE.Vector3(PX, 0, 0));
  lua.target.position.set(PX, CHAO, 2); scene.add(lua.target); lua.castShadow = true; lua.shadow.mapSize.set(2048, 2048);
  Object.assign(lua.shadow.camera, { left: -9, right: 9, top: 9, bottom: -9, near: 1, far: 60 }); lua.shadow.bias = -0.0008; scene.add(lua);
  const rasante = new THREE.DirectionalLight(0xbfcfff, 3.6); rasante.position.set(PX - 5, 2.5, 3.5); rasante.target.position.set(PX, PY, 0); scene.add(rasante.target); scene.add(rasante);
  scene.add(new THREE.HemisphereLight(0x8090a8, 0x30302c, 0.3));
  luzRubra = new THREE.PointLight(0xff2a10, 0, 7, 1.6); luzRubra.position.set(PX + 0.25, PY - 0.2, 1.0); scene.add(luzRubra);
  // neve caindo e brasas subindo
  const N = 1500, ng = new THREE.BufferGeometry(), np = new Float32Array(N * 3), rn = semente("neve");
  for (let i = 0; i < N; i++) { np[i * 3] = (rn() - 0.5) * 14; np[i * 3 + 1] = rn() * 8 - 2.5; np[i * 3 + 2] = rn() * 7 - 3; }
  ng.setAttribute("position", new THREE.BufferAttribute(np, 3)); ng.userData.base = np.slice();
  neve = new THREE.Points(ng, new THREE.PointsMaterial({ size: 0.045, map: suave("rgba(255,255,255,1)", "rgba(255,255,255,0)"), transparent: true, depthWrite: false, color: 0xffffff }));
  neve.material.color.setScalar(2.2); scene.add(neve);
  const B = 140, bg = new THREE.BufferGeometry(); bg.setAttribute("position", new THREE.BufferAttribute(new Float32Array(B * 3), 3));
  brasas = new THREE.Points(bg, new THREE.PointsMaterial({ size: 0.05, map: suave("rgba(255,80,40,1)", "rgba(255,30,10,0)"), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, color: 0xff3010 }));
  brasas.material.color.multiplyScalar(4); scene.add(brasas);
  // pós: bloom (lua e sangue) → gravura
  papelCan = papel(); const tPapel = new THREE.CanvasTexture(papelCan);
  composer = new EffectComposer(renderer); composer.setPixelRatio(1); composer.setSize(W, H);
  composer.addPass(new RenderPass(scene, camera));
  composer.addPass(new UnrealBloomPass(new THREE.Vector2(W, H), 0.45, 0.4, 1.2));
  grava = passeGravura(tPapel); grava.uniforms.cru.value = cfg.cru ? 1 : 0; composer.addPass(grava);
  overlay = document.getElementById("titulo"); overlay.width = W; overlay.height = H; octx = overlay.getContext("2d");
};

function posCamera(t) {
  const dur = (C && C.dur) || 7.6, k = easeInOut(lin(t, 0, dur)), ub = t - TB, tr = ub > 0 && ub < 0.3 ? (1 - ub / 0.3) : 0;
  camera.position.set(0.55 - 0.45 * k + (ruido1(t * 0.6) - 0.5) * 0.04 + (ruido1(t * 40) - 0.5) * 0.06 * tr,
    -1.05 - 0.15 * k + (ruido1(t * 0.5 + 9) - 0.5) * 0.03 + (ruido1(t * 43 + 3) - 0.5) * 0.06 * tr, 8.4 - 1.3 * k);
  camera.lookAt(-0.35 - 0.2 * k, -0.15 - 0.1 * k, 0);
}

function brilho(t) {   // o mapa emissivo: o sangue nos sulcos
  const ub = t - TB, f = easeInOut(lin(t, F0, F1 - F0)), e = EW / FW;
  emCtx.fillStyle = "#000"; emCtx.fillRect(0, 0, EW, EH); if (ub < 0) return 0;
  emCtx.lineCap = "round"; emCtx.lineJoin = "round";
  const tom = (v) => `rgb(${Math.round(255 * v)},${Math.round(255 * v)},${Math.round(255 * v)})`;
  // a runa do meio: clarão no tambor, depois pulsa
  const vr = clamp(0.75 + 0.25 * ruido1(t * 3)) * (1 + 0.6 * Math.exp(-ub / 0.25));
  emCtx.save(); emCtx.filter = "blur(2px)"; for (const sk of runaC) { emCtx.strokeStyle = tom(Math.min(1, vr)); emCtx.lineWidth = sk.w * 0.5 * e; linha(emCtx, sk.pts, 2, e); } emCtx.restore();
  // a serpente: o fogo corre da cauda à cabeça
  if (f > 0) {
    emCtx.save(); emCtx.filter = "blur(1.5px)";
    const [b1, b2, cab] = [0, 1, 2].map((i) => scene.userData.sulcos[i]);
    for (const b of [b1, b2]) { emCtx.strokeStyle = tom(0.85 + 0.15 * ruido1(t * 4)); emCtx.lineWidth = b.w * 0.45 * e; linha(emCtx, b.pts, f, e); }
    for (const g of glifos) { if (g.s > f) continue; const v = 0.6 + 0.4 * ruido1(g.s * 40 + t * 2.5) + 0.6 * Math.exp(-(f - g.s) * 25);
      emCtx.strokeStyle = emCtx.fillStyle = tom(Math.min(1, v));
      if (g.pts) { emCtx.lineWidth = g.w * 0.5 * e; linha(emCtx, g.pts, 2, e); } else for (const [x, y] of g.pontos) { emCtx.beginPath(); emCtx.arc(x * e, y * e, 3.5 * e * 2, 0, 7); emCtx.fill(); } }
    if (f >= 0.985) { const fl = Math.exp(-(t - F1) / 0.35); emCtx.strokeStyle = tom(1); emCtx.lineWidth = cab.w * 0.5 * e; linha(emCtx, cab.pts, 2, e);
      emCtx.fillStyle = tom(1); emCtx.beginPath(); emCtx.arc(scene.userData.olho[0] * e, scene.userData.olho[1] * e, 7 + 6 * fl, 0, 7); emCtx.fill(); }
    // a frente do fogo: brasa forte
    if (f < 1) { let i = bandaS.findIndex((s) => s >= f); if (i < 0) i = banda.length - 1; const [x, y] = banda[i];
      emCtx.filter = "blur(8px)"; emCtx.fillStyle = "#fff"; emCtx.beginPath(); emCtx.arc(x * e, y * e, 22, 0, 7); emCtx.fill(); }
    emCtx.restore();
  }
  emTex.needsUpdate = true;
  return Math.exp(-ub / 0.3);
}

function cartela(t) {   // a legenda impressa: caixa de papel limpo com fio duplo, letras entintadas
  octx.clearRect(0, 0, W, H);
  const a = easeOut(lin(t, 2.45, 0.6)); if (a <= 0) return;
  const x0 = W * 0.585, y0 = H * 0.285, cw = W * 0.345, ch = H * 0.36;
  octx.save(); octx.globalAlpha = a;
  // fundo: o próprio papel (cobre a gravura), com uma sombra de tinta em volta
  octx.drawImage(papelCan, x0, y0, cw, ch, x0, y0, cw, ch);
  const fio = easeInOut(lin(t, 2.5, 0.7)), per = 2 * (cw + ch);
  octx.strokeStyle = "#2a190c"; octx.setLineDash([per * fio, per]); octx.lineWidth = 3; octx.strokeRect(x0 + 10, y0 + 10, cw - 20, ch - 20);
  octx.lineWidth = 1.2; octx.strokeRect(x0 + 18, y0 + 18, cw - 36, ch - 36); octx.setLineDash([]);
  // cantos com losango
  if (fio > 0.95) for (const [x, y] of [[x0 + 10, y0 + 10], [x0 + cw - 10, y0 + 10], [x0 + 10, y0 + ch - 10], [x0 + cw - 10, y0 + ch - 10]]) {
    octx.fillStyle = "#2a190c"; octx.beginPath(); octx.moveTo(x, y - 7); octx.lineTo(x + 7, y); octx.lineTo(x, y + 7); octx.lineTo(x - 7, y); octx.closePath(); octx.fill(); }
  octx.textAlign = "center"; const xc = x0 + cw / 2;
  const cap = easeOut(lin(t, 2.75, 0.5)); octx.globalAlpha = a * cap; octx.fillStyle = "#8e1a10"; octx.font = `400 ${Math.round(H * 0.034)}px "IM Fell English SC"`;
  octx.fillText((C.numero_pt || `Capítulo ${C.numero}`).toUpperCase().split("").join(" "), xc, y0 + ch * 0.2);
  // divisor
  const dv = easeInOut(lin(t, 2.85, 0.5)) * cw * 0.22; octx.globalAlpha = a; octx.strokeStyle = "#2a190c"; octx.lineWidth = 1.5;
  octx.beginPath(); octx.moveTo(xc - dv, y0 + ch * 0.27); octx.lineTo(xc + dv, y0 + ch * 0.27); octx.stroke();
  if (dv > 1) { octx.fillStyle = "#8e1a10"; octx.beginPath(); octx.moveTo(xc, y0 + ch * 0.27 - 6); octx.lineTo(xc + 6, y0 + ch * 0.27); octx.lineTo(xc, y0 + ch * 0.27 + 6); octx.lineTo(xc - 6, y0 + ch * 0.27); octx.closePath(); octx.fill(); }
  // título em Cinzel, letra a letra
  let fs = Math.round(H * 0.07); octx.font = `400 ${fs}px "IM Fell English SC"`;
  const tit = C.titulo || "", maxW = cw * 0.84; let ls = [tit];
  if (octx.measureText(tit).width > maxW) { const ps = tit.split(" "); let best = null;
    for (let k = 1; k < ps.length; k++) { const l2 = [ps.slice(0, k).join(" "), ps.slice(k).join(" ")], m = Math.max(...l2.map((l) => octx.measureText(l).width)); if (!best || m < best[0]) best = [m, l2]; }
    ls = best[1]; }
  while (Math.max(...ls.map((l) => octx.measureText(l).width)) > maxW && fs > 20) { fs -= 2; octx.font = `400 ${fs}px "IM Fell English SC"`; }
  octx.textAlign = "left"; let k0 = 0; const yT = Math.max(y0 + ch * 0.47 - (ls.length - 1) * fs * 0.55, y0 + ch * 0.27 + fs * 1.05);   // a 1ª linha nunca encosta no divisor
  ls.forEach((l, li) => { let x = xc - octx.measureText(l).width / 2; const y = yT + li * fs * 1.12;
    for (const chh of l) { const p = easeOut(lin(t, 2.95 + k0 * 0.022, 0.35)); k0++;
      if (p > 0) { octx.globalAlpha = a * p; octx.fillStyle = "#24160c"; octx.fillText(chh, x, y + (1 - p) * 3); }
      x += octx.measureText(chh).width; } });
  // ano / fonte
  octx.textAlign = "center"; octx.globalAlpha = a * easeOut(lin(t, 3.6, 0.6)); octx.fillStyle = "#4a3220"; octx.font = `italic 400 ${Math.round(H * 0.036)}px "IM Fell English"`;
  octx.fillText(C.ano || "", xc, y0 + ch * 0.86);
  // tinta irregular: falhas de impressão nas letras
  octx.globalCompositeOperation = "destination-out"; const rf = semente("falha");
  for (let i = 0; i < 900; i++) { octx.globalAlpha = 0.35 * rf(); octx.beginPath(); octx.arc(x0 + rf() * cw, y0 + rf() * ch, 0.5 + rf() * 1.4, 0, 7); octx.fill(); }
  octx.restore();
}

window.tempos = {};
window.quadro = function (t) {
  const ub = t - TB;
  const flash = brilho(t);
  const aceso = ub > 0 ? 1 : 0;
  faceMat.emissiveIntensity = aceso * (2.2 + 3.5 * flash);
  luzRubra.intensity = aceso * (0.6 + 3 * flash + 0.6 * easeOut(lin(t, F0, F1 - F0))) * (0.85 + 0.25 * ruido1(t * 5));
  // neve com vento (o tambor sopra uma rajada)
  const pa = neve.geometry.attributes.position, b = neve.geometry.userData.base;
  for (let i = 0; i < pa.count; i++) { const y = ((b[i * 3 + 1] + 2.5 - t * (0.45 + (i % 7) * 0.05)) % 8 + 8) % 8 - 2.5;
    let x = b[i * 3] + Math.sin(t * 0.8 + i) * 0.15 + t * 0.35, z = b[i * 3 + 2];
    if (ub > 0) x += 0.9 * easeOut(lin(ub, 0, 1.2));
    pa.setXYZ(i, ((x + 7) % 14 + 14) % 14 - 7, y, z); }
  pa.needsUpdate = true;
  // brasas saindo dos sulcos acesos
  const bp = brasas.geometry.attributes.position, rs = semente("brasa");
  for (let i = 0; i < bp.count; i++) { const u0 = 0.25 + rs() * 0.5, v0 = 0.15 + rs() * 0.75, fase = rs(), vel = 0.35 + rs() * 0.5, dx = (rs() - 0.5) * 0.6;
    if (ub < 0) { bp.setXYZ(i, 0, -50, 0); continue; }
    const age = ((ub * vel + fase) % 1.6);
    bp.setXYZ(i, PX + (u0 - 0.5) * SX * 2 + dx * age + Math.sin(age * 6 + i) * 0.05, PY + (0.5 - v0) * SY * 2 + age * 1.2, PZ + SZ + 0.08 + age * 0.3); }
  bp.needsUpdate = true; brasas.material.opacity = clamp(ub * 3);
  scene.userData.ceu.uniforms.t.value = t;
  posCamera(t);
  grava.uniforms.t.value = t; { const rq = semente("tr" + Math.floor(t * 12)); grava.uniforms.tremido.value.set((rq() - 0.5) * 2.4, (rq() - 0.5) * 2.4); }
  composer.render(); renderer.getContext().finish();
  cartela(t);
  const dur = C.dur || 7.6, fade = Math.min(lin(t, 0, 0.35), 1 - lin(t, dur - 0.4, 0.4));
  document.getElementById("veu").style.opacity = String(1 - fade);
  return true;
};
window.pronto = true;
