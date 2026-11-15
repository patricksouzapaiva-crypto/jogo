// Identidade tailandesa (Ep. 10, 15/11) — Isan / Loei. Marca: o PHA YANT (ผ้ายันต์), pano sagrado vermelho (ou branco)
// com o diagrama geométrico (yantra) e a escrita KHOM; o tambor ritual; a câmera de segurança (CCTV) do Mateus.
// Usa os ganchos do coreia.js (carregado antes): KR.cenas / KR.efeitos / KR.trans.
//   KR.cenas.pha_yant(c, t)          — cartão de capítulo: o pano desenrola, o yantra é traçado, o tambor bate
//   KR.efeitos.cctv(c, t, cfg)       — por cima de qualquer cena: visão noturna, CAM + ● REC + relógio correndo
//   KR.trans.obturador(A, B, k, t)   — corte seco de dossiê: lâminas de obturador fecham e abrem num flash
"use strict";
const TH = { _c: {} };
const PANO = { vermelho: [150, 22, 20], branco: [214, 206, 186] };
// "Khom" = escrita khmer antiga; sílabas de katha (fórmulas) que aparecem em pha yant reais (na-mo-bud-dha-ya…)
const KHOM = ["ន", "មោ", "ពុ", "ទ្ធា", "យ", "ម", "អ", "ឥ", "ស", "វា", "សុ", "ជា", "នា", "ក", "ត", "ឧ", "អ៊ុ"].filter((s) => !/[Ⴀ-ჿ]/.test(s));

function thPano(w, h, cor, chave) {   // tecido: trama fina (fios horizontais e verticais), manchas, borda puída
  const k = `pano${chave}${w}x${h}`;
  if (TH._c[k]) return TH._c[k];
  const oc = document.createElement("canvas"); oc.width = w; oc.height = h;
  const g = oc.getContext("2d"), r = _semente(chave), f = _fbm(0, Math.ceil(w / 6), Math.ceil(h / 6), chave, 5), fw = Math.ceil(w / 6);
  const im = g.createImageData(w, h);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const v = f[Math.floor(y / 6) * fw + Math.floor(x / 6)], tr = ((x % 3 === 0) ? -14 : 0) + ((y % 3 === 1) ? 10 : 0);
    const m = 0.72 + v * 0.42, n = (r() - 0.5) * 14, i = (y * w + x) * 4;
    im.data[i] = cor[0] * m + tr + n; im.data[i + 1] = cor[1] * m + tr * 0.5 + n; im.data[i + 2] = cor[2] * m + tr * 0.5 + n; im.data[i + 3] = 255;
  }
  g.putImageData(im, 0, 0);
  const v = g.createRadialGradient(w / 2, h / 2, w * 0.25, w / 2, h / 2, h * 0.62);   // escurece nas bordas (anos de fumaça de incenso)
  v.addColorStop(0, "rgba(0,0,0,0)"); v.addColorStop(1, "rgba(30,8,0,.55)"); g.fillStyle = v; g.fillRect(0, 0, w, h);
  TH._c[k] = oc; return oc;
}

function thTraco(pts, p, fechado) {   // desenha só a fração p (0..1) de uma linha poligonal — o "pincel" traçando
  if (p <= 0) return;
  const seg = []; let tot = 0;
  const P = fechado ? pts.concat([pts[0]]) : pts;
  for (let i = 1; i < P.length; i++) { const d = Math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]); seg.push(d); tot += d; }
  let resto = tot * Math.min(1, p);
  ctx.beginPath(); ctx.moveTo(P[0][0], P[0][1]);
  for (let i = 1; i < P.length && resto > 0; i++) {
    const d = seg[i - 1], q = Math.min(1, resto / d);
    ctx.lineTo(P[i - 1][0] + (P[i][0] - P[i - 1][0]) * q, P[i - 1][1] + (P[i][1] - P[i - 1][1]) * q); resto -= d;
  }
  ctx.stroke();
}

// ---------------------------------------------------------------- 1) CARTÃO DE CAPÍTULO: o pano Pha Yant
// c: {tipo:"pha_yant", numero:1, numero_pt:"CAPÍTULO 1", titulo:"O aluguel da terra e os famintos", ano:"séc. XIX → hoje",
//     cor:"vermelho"|"branco", motivo:"sol"|"presas"|"aneis"|"olho", imagem (fundo)}
// Tempo (o som do capítulo — ep10_cap<N> — segue isto): 0–1.1 o pano desenrola · 0.9–1.6 a moldura · 1.6 o TAMBOR
// (tranco + pó) · 1.6–2.5 o yantra (motivo + grade) · 2.0–3.0 a escrita Khom cela a cela · 2.6–3.8 o título.
KR.cenas.pha_yant = function (c, t) {
  const { W, H } = D, u = t - c.t0;
  krFundo(krImg(c), t, c, "blur(8px) brightness(0.26) saturate(0.6)", [1.08, 1.0]);
  // luz de vela + fumaça de incenso subindo atrás do pano
  const resp = 0.85 + 0.15 * Math.sin(t * 6.1) * Math.sin(t * 2.7 + 1);
  const lg = ctx.createRadialGradient(W * 0.33, H * 0.55, 0, W * 0.33, H * 0.55, H * 0.8);
  lg.addColorStop(0, `rgba(255,140,50,${0.2 * resp})`); lg.addColorStop(1, "rgba(0,0,0,0)"); ctx.fillStyle = lg; ctx.fillRect(0, 0, W, H);
  ctx.save(); ctx.strokeStyle = "rgba(210,205,195,.10)"; ctx.lineCap = "round";
  for (let i = 0; i < 3; i++) { ctx.lineWidth = H * (0.006 + i * 0.004); ctx.filter = `blur(${5 + i * 4}px)`; ctx.beginPath();
    for (let s = 0; s <= 30; s++) { const q = s / 30, y = H * (1 - q), x = W * (0.2 + i * 0.12) + Math.sin(q * 5 + t * 0.9 + i * 2) * W * 0.025 * q; s ? ctx.lineTo(x, y) : ctx.moveTo(x, y); }
    ctx.stroke(); }
  ctx.restore();
  // tranco do tambor (1.6 s): a tela inteira estremece 0.18 s
  const ub = u - 1.6, tranco = ub > 0 && ub < 0.18 ? (1 - ub / 0.18) : 0;
  const rj = _semente("tr" + Math.floor(t * 60));
  ctx.save(); ctx.translate((rj() - 0.5) * H * 0.012 * tranco, (rj() - 0.5) * H * 0.012 * tranco);
  // o pano: pendurado numa vara; desenrola de cima para baixo, com o rolo descendo e ficando mais fino
  const cor = PANO[c.cor] || PANO.vermelho, tinta = c.cor === "branco" ? "#8a1410" : "#160604", ouro = "#d8b04a";
  const pw = H * 0.46, ph = H * 0.8, cx = W * 0.33, topo = H * 0.08;
  const e = easeOut(lin(u, 0.05, 1.05)), vis = ph * e, bal = 0.012 * Math.sin(t * 1.2) + (1 - e) * 0.03 * Math.sin(u * 8);
  const tecido = thPano(Math.round(pw), Math.round(ph), cor, "phayant" + (c.cor || "v"));
  ctx.save(); ctx.translate(cx, topo); ctx.rotate(bal);
  ctx.shadowColor = "rgba(0,0,0,.8)"; ctx.shadowBlur = H * 0.05; ctx.shadowOffsetY = H * 0.02;
  ctx.save(); ctx.beginPath(); ctx.rect(-pw / 2, 0, pw, vis); ctx.clip();
  // ondulação do tecido: fatias verticais deslocadas
  const fat = 24;
  for (let i = 0; i < fat; i++) {
    const x0 = (i / fat) * pw, dy = Math.sin(i / fat * 6.28 + t * 1.6) * H * 0.004;
    ctx.drawImage(tecido, x0, 0, pw / fat + 1, ph, -pw / 2 + x0, dy, pw / fat + 1, ph);
  }
  ctx.shadowColor = "transparent";
  // ----- o yantra (tudo em coordenadas do pano; origem no topo-centro)
  ctx.lineCap = "round"; ctx.lineJoin = "round";
  const m = pw * 0.07, x0 = -pw / 2 + m, x1 = pw / 2 - m, y0 = m, y1 = ph - m * 2.2;
  ctx.strokeStyle = tinta; ctx.globalAlpha = 0.92;
  ctx.lineWidth = H * 0.008; thTraco([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], lin(u, 0.9, 0.7), true);
  ctx.lineWidth = H * 0.004; thTraco([[x0 + m * 0.4, y0 + m * 0.4], [x1 - m * 0.4, y0 + m * 0.4], [x1 - m * 0.4, y1 - m * 0.4], [x0 + m * 0.4, y1 - m * 0.4]], lin(u, 1.0, 0.7), true);
  // unalom (a espiral sagrada) no alto: espiral + traço que sobe
  const pu = lin(u, 1.2, 0.6), ux = 0, uy = y0 + ph * 0.13;
  if (pu > 0) { const esp = []; for (let a = 0; a <= 6.28 * 2.2; a += 0.12) esp.push([ux + Math.cos(a) * a * pw * 0.006, uy + Math.sin(a) * a * pw * 0.006]);
    esp.push([ux, uy - ph * 0.08]); ctx.lineWidth = H * 0.006; thTraco(esp, pu); }
  // motivo central (muda por capítulo) — entra com o tambor
  const pm = easeOut(lin(u, 1.6, 0.8)), my = y0 + ph * 0.36, R = pw * 0.24;
  ctx.lineWidth = H * 0.0065;
  const motivo = c.motivo || ["sol", "presas", "aneis", "olho"][((c.numero || 1) - 1) % 4];
  if (motivo === "sol") {          // o dono da terra: círculo com raios
    const cir = []; for (let a = 0; a <= 6.29; a += 0.1) cir.push([Math.cos(a - 1.57) * R * 0.55, my + Math.sin(a - 1.57) * R * 0.55]); thTraco(cir, pm);
    for (let i = 0; i < 12; i++) { const a = i / 12 * 6.28; thTraco([[Math.cos(a) * R * 0.68, my + Math.sin(a) * R * 0.68], [Math.cos(a) * R, my + Math.sin(a) * R]], clamp(pm * 12 - i)); }
  } else if (motivo === "presas") { // a criatura da noite: dois triângulos (presas) e a lua
    thTraco([[-R, my - R * 0.6], [0, my + R], [R, my - R * 0.6]], pm, true);
    thTraco([[-R * 0.55, my + R * 0.75], [0, my - R * 0.95], [R * 0.55, my + R * 0.75]], clamp(pm * 1.4 - 0.4), true);
  } else if (motivo === "aneis") {  // o corpo emprestado: três anéis concêntricos e o cordão sai sin cruzando
    for (let k = 0; k < 3; k++) { const cir = []; for (let a = 0; a <= 6.29; a += 0.1) cir.push([Math.cos(a) * R * (0.35 + k * 0.3), my + Math.sin(a) * R * (0.35 + k * 0.3)]); thTraco(cir, clamp(pm * 3 - k)); }
    ctx.strokeStyle = "rgba(240,236,224,.85)"; ctx.lineWidth = H * 0.003; thTraco([[-pw / 2, my - R * 1.1], [pw / 2, my + R * 1.1]], clamp(pm * 2 - 1)); ctx.strokeStyle = tinta;
  } else {                          // a câmera: o olho (amêndoa + pupila) que tudo registra
    const ol = []; for (let a = 0; a <= 6.29; a += 0.08) ol.push([Math.cos(a) * R, my + Math.sin(a) * R * 0.45 * Math.abs(Math.cos(a / 2) + 0.4)]); thTraco(ol, pm);
    const pp = []; for (let a = 0; a <= 6.29; a += 0.15) pp.push([Math.cos(a) * R * 0.2, my + Math.sin(a) * R * 0.2]); thTraco(pp, clamp(pm * 2 - 1));
  }
  // grade 3×3 (o coração do yantra) e uma sílaba khom por cela
  const gy = y0 + ph * 0.5, gs = pw * 0.5, cel = gs / 3, gx = -gs / 2, pg = lin(u, 1.75, 0.6);
  ctx.lineWidth = H * 0.0045;
  for (let k = 0; k <= 3; k++) { thTraco([[gx, gy + k * cel], [gx + gs, gy + k * cel]], clamp(pg * 2 - k * 0.25)); thTraco([[gx + k * cel, gy], [gx + k * cel, gy + gs]], clamp(pg * 2 - 0.5 - k * 0.25)); }
  const rk = _semente("khom" + (c.numero || 1)), sil = Array.from({ length: 9 }, () => KHOM[Math.floor(rk() * KHOM.length)]);
  ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.font = `400 ${Math.round(cel * 0.52)}px "Moul", "Noto Serif Khmer"`;
  sil.forEach((s, i) => { const p = clamp(lin(u, 2.0, 1.0) * 9 - i); if (p <= 0) return;
    ctx.globalAlpha = 0.92 * p; ctx.fillStyle = tinta; ctx.fillText(s, gx + (i % 3 + 0.5) * cel, gy + (Math.floor(i / 3) + 0.5) * cel + cel * 0.05); });
  // linhas de katha embaixo (escrita corrida, revelada da esquerda para a direita)
  ctx.font = `400 ${Math.round(pw * 0.045)}px "Moul", "Noto Serif Khmer"`; ctx.textAlign = "left";
  for (let L = 0; L < 2; L++) { const yy = gy + gs + ph * 0.035 + L * pw * 0.065, p = lin(u, 2.4 + L * 0.3, 0.7);
    if (p <= 0) continue; const txt = Array.from({ length: 11 }, () => KHOM[Math.floor(rk() * KHOM.length)]).join("");
    ctx.save(); ctx.beginPath(); ctx.rect(x0 + m * 0.6, yy - pw * 0.05, (x1 - x0 - m * 1.2) * p, pw * 0.1); ctx.clip();
    ctx.globalAlpha = 0.85; ctx.fillStyle = tinta; ctx.fillText(txt, x0 + m * 0.7, yy, x1 - x0 - m * 1.4); ctx.restore(); }
  // detalhes em ouro (pontos rituais nos cantos da grade) — brilham com a vela
  ctx.globalAlpha = 0.8 * lin(u, 2.2, 0.5) * resp; ctx.fillStyle = ouro;
  for (const [a, b] of [[0, 0], [3, 0], [0, 3], [3, 3]]) { ctx.beginPath(); ctx.arc(gx + a * cel, gy + b * cel, H * 0.006, 0, 6.29); ctx.fill(); }
  ctx.restore();   // fim do recorte do pano
  // franja puída na base (só quando terminou de desenrolar)
  if (e > 0.98) { const rf = _semente("franja"); ctx.strokeStyle = `rgb(${cor[0] * 0.7},${cor[1] * 0.7},${cor[2] * 0.7})`; ctx.lineWidth = 1.4;
    for (let i = 0; i < 70; i++) { const x = -pw / 2 + (i + rf()) / 70 * pw, L = H * (0.008 + rf() * 0.02); ctx.beginPath(); ctx.moveTo(x, ph); ctx.lineTo(x + Math.sin(t * 2 + i) * 2, ph + L); ctx.stroke(); } }
  // o rolo que desce (diâmetro diminui conforme o pano sai dele)
  if (e < 0.995) { const d = H * (0.07 * (1 - e) + 0.014); const gr = ctx.createLinearGradient(0, vis - d / 2, 0, vis + d / 2);
    gr.addColorStop(0, `rgb(${cor[0] * 0.55},${cor[1] * 0.55},${cor[2] * 0.55})`); gr.addColorStop(0.45, `rgb(${cor[0]},${cor[1]},${cor[2]})`); gr.addColorStop(1, `rgb(${cor[0] * 0.35},${cor[1] * 0.3},${cor[2] * 0.3})`);
    ctx.fillStyle = gr; rr(-pw / 2 - 4, vis - d / 2, pw + 8, d, d / 2); ctx.fill(); }
  // a vara de madeira no alto, com o cordão
  const vg = ctx.createLinearGradient(0, -H * 0.012, 0, H * 0.012); vg.addColorStop(0, "#6b4a2a"); vg.addColorStop(0.5, "#3a2412"); vg.addColorStop(1, "#1a0e06");
  ctx.fillStyle = vg; rr(-pw / 2 - H * 0.03, -H * 0.012, pw + H * 0.06, H * 0.024, H * 0.012); ctx.fill();
  ctx.strokeStyle = "rgba(235,230,215,.75)"; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(-pw * 0.4, 0); ctx.lineTo(0, -H * 0.07); ctx.lineTo(pw * 0.4, 0); ctx.stroke();
  ctx.restore();
  // pó que solta do pano com o tambor
  if (ub > 0 && ub < 1.6) { const rp = _semente("po" + (c.numero || 1)); ctx.fillStyle = "rgba(230,215,190,.5)";
    for (let i = 0; i < 60; i++) { const a = rp() * 6.28, v = rp(), x = cx + (rp() - 0.5) * pw, y = topo + rp() * ph;
      ctx.globalAlpha = 0.5 * (1 - ub / 1.6) * v; ctx.beginPath(); ctx.arc(x + Math.cos(a) * ub * H * 0.04 * v, y + Math.sin(a) * ub * H * 0.03 * v - ub * H * 0.02, 1.5 + v * 2.5, 0, 6.29); ctx.fill(); }
    ctx.globalAlpha = 1; }
  ctx.restore();   // fim do tranco
  // ----- o título em português, à direita, com fio vermelho
  const a2 = easeOut(lin(u, 2.6, 0.7)), xt = W * 0.56;
  if (a2 > 0) {
    ctx.save(); ctx.globalAlpha = a2; ctx.textAlign = "left"; ctx.textBaseline = "alphabetic";
    ctx.fillStyle = "#b3141c"; ctx.fillRect(xt, H * 0.36, W * 0.0035, H * 0.3 * a2);
    ctx.font = `700 ${Math.round(H * 0.028)}px "Inter"`; ctx.fillStyle = "#cdbb98";
    ctx.fillText((c.numero_pt || `CAPÍTULO ${c.numero || 1}`).toUpperCase().split("").join(" "), xt + W * 0.02, H * 0.41);
    let fsT = Math.round(H * 0.07); ctx.font = `700 ${fsT}px "Cinzel"`;
    const tit = c.titulo || "", maxW = W * 0.38; let ls = [tit];
    if (ctx.measureText(tit).width > maxW) { const ps = tit.split(" "), mm = Math.ceil(ps.length / 2); ls = [ps.slice(0, mm).join(" "), ps.slice(mm).join(" ")]; }
    while (Math.max(...ls.map((l) => ctx.measureText(l).width)) > maxW && fsT > 20) { fsT -= 2; ctx.font = `700 ${fsT}px "Cinzel"`; }
    ctx.fillStyle = "#f3ead6"; ctx.shadowColor = "rgba(0,0,0,.9)"; ctx.shadowBlur = 18;
    const n = Math.floor(lin(u, 2.7, 0.9) * tit.length); let resto = n;
    ls.forEach((l, k) => { const q = Math.max(0, Math.min(l.length, resto)); resto -= l.length + 1; ctx.fillText(l.slice(0, q), xt + W * 0.02, H * 0.5 + k * fsT * 1.12); });
    ctx.shadowBlur = 0; ctx.font = `700 ${Math.round(H * 0.034)}px "Inter"`; ctx.fillStyle = "#d9352c"; ctx.globalAlpha = a2 * easeOut(lin(u, 3.4, 0.5));
    ctx.fillText(c.ano || "", xt + W * 0.02, H * 0.5 + ls.length * fsT * 1.12 + H * 0.03);
    ctx.restore();
  }
};

// ---------------------------------------------------------------- 2) CÂMERA DE SEGURANÇA (o Mateus)
// cfg: {cam:"CAM 01 - CORREDOR", hora:"01:12:04", data:"18-09-2025", queda: s (o Wi-Fi cai: tranca e some)}
function thHora(h, mais) { const [a, b, s] = h.split(":").map(Number), x = Math.floor(a * 3600 + b * 60 + s + mais) % 86400;
  return [Math.floor(x / 3600), Math.floor(x / 60) % 60, x % 60].map((v) => String(v).padStart(2, "0")).join(":"); }
KR.efeitos.cctv = function (c, t, cfg = {}) {
  const { W, H } = D, u = t - c.t0;
  const im = _canvas("cctvIm", W, H), g = im.getContext("2d"); g.drawImage(cv, 0, 0);
  ctx.save(); ctx.filter = "grayscale(1) brightness(1.25) contrast(1.3)"; ctx.drawImage(im, 0, 0); ctx.restore();
  ctx.save(); ctx.globalCompositeOperation = "multiply"; ctx.fillStyle = "#c4ffd2"; ctx.fillRect(0, 0, W, H); ctx.restore();   // IR: P&B levemente esverdeado
  // ruído digital (ladrilho em cache, deslocado a cada quadro) + linhas de varredura + faixa que rola
  const nz = TH._c.ruido || (TH._c.ruido = (() => { const o = document.createElement("canvas"); o.width = 480; o.height = 270; const gg = o.getContext("2d"), d = gg.createImageData(480, 270), r = _semente("ruido");
    for (let i = 0; i < d.data.length; i += 4) { const v = r() * 255; d.data[i] = d.data[i + 1] = d.data[i + 2] = v; d.data[i + 3] = 255; } gg.putImageData(d, 0, 0); return o; })());
  const r = rng(Math.floor(t * 30));
  ctx.save(); ctx.globalCompositeOperation = "overlay"; ctx.globalAlpha = 0.22; ctx.drawImage(nz, -r() * 200, -r() * 100, W * 1.3, H * 1.3); ctx.restore();
  ctx.save(); ctx.fillStyle = "rgba(0,0,0,.10)"; for (let y = 0; y < H; y += 4) ctx.fillRect(0, y, W, 1.5); ctx.restore();
  const fy = ((t * 0.12) % 1.2 - 0.1) * H; const fg = ctx.createLinearGradient(0, fy - H * 0.05, 0, fy + H * 0.05);
  fg.addColorStop(0, "rgba(255,255,255,0)"); fg.addColorStop(0.5, "rgba(230,255,235,.05)"); fg.addColorStop(1, "rgba(255,255,255,0)"); ctx.fillStyle = fg; ctx.fillRect(0, fy - H * 0.05, W, H * 0.1);
  // vinheta de lente grande-angular
  const v = ctx.createRadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 0.95); v.addColorStop(0, "rgba(0,0,0,0)"); v.addColorStop(1, "rgba(0,0,0,.7)"); ctx.fillStyle = v; ctx.fillRect(0, 0, W, H);
  // a queda do Wi-Fi: o quadro trava em blocos, rasga e apaga
  if (cfg.queda != null && u > cfg.queda) {
    const q = u - cfg.queda;
    if (q < 0.5) { const b = _canvas("cctvBloco", 64, 36), gb = b.getContext("2d"); gb.drawImage(cv, 0, 0, 64, 36);
      ctx.save(); ctx.imageSmoothingEnabled = false; ctx.drawImage(b, 0, 0, W, H); ctx.restore();
      for (let i = 0; i < 8; i++) { const y = r() * H, h = H * (0.02 + r() * 0.06); ctx.drawImage(cv, 0, y, W, h, (r() - 0.5) * W * 0.2, y, W, h); } }
    else { ctx.fillStyle = "#050605"; ctx.fillRect(0, 0, W, H); ctx.fillStyle = "rgba(220,230,220,.8)"; ctx.font = `600 ${Math.round(H * 0.03)}px "Inter"`;
      ctx.textAlign = "center"; ctx.fillText("SEM SINAL", W / 2, H / 2); ctx.textAlign = "left"; }
  }
  // textos da câmera (sempre por cima)
  const fs = Math.round(H * 0.034); ctx.save(); ctx.font = `600 ${fs}px "DejaVu Sans Mono", monospace`; ctx.textBaseline = "top";
  ctx.shadowColor = "rgba(0,0,0,.9)"; ctx.shadowBlur = 4; ctx.fillStyle = "rgba(240,245,240,.92)";
  ctx.fillText(cfg.cam || "CAM 01 - CORREDOR", W * 0.035, H * 0.045);
  if (Math.floor(t * 1.6) % 2 === 0) { ctx.fillStyle = "#ff2b2b"; ctx.beginPath(); ctx.arc(W * 0.043, H * 0.045 + fs * 1.85, fs * 0.3, 0, 6.29); ctx.fill(); }
  ctx.fillStyle = "rgba(240,245,240,.92)"; ctx.fillText("REC", W * 0.055, H * 0.045 + fs * 1.3);
  ctx.textAlign = "right"; ctx.fillText(cfg.data || "18-09-2025", W * 0.965, H * 0.045);
  ctx.fillText(thHora(cfg.hora || "02:40:18", u), W * 0.965, H * 0.045 + fs * 1.3);
  ctx.restore();
};

// ---------------------------------------------------------------- 3) TRANSIÇÃO: obturador (o "slide" do dossiê)
KR.trans.obturador = function (A, B, k, t) {
  const { W, H } = D, fecha = k < 0.5, e = fecha ? easeInOut(k / 0.5) : 1 - easeInOut((k - 0.5) / 0.5);
  ctx.drawImage(fecha ? A : B, 0, 0);
  ctx.save(); ctx.fillStyle = "#050505"; ctx.translate(W / 2, H / 2);
  for (let i = 0; i < 6; i++) { ctx.save(); ctx.rotate(i / 6 * 6.283 + e * 0.5);   // seis lâminas girando para dentro
    ctx.beginPath(); ctx.moveTo(Math.hypot(W, H) * 0.6 * (1 - e) + 2, -Math.hypot(W, H)); ctx.lineTo(Math.hypot(W, H), -Math.hypot(W, H)); ctx.lineTo(Math.hypot(W, H), Math.hypot(W, H)); ctx.lineTo(Math.hypot(W, H) * 0.6 * (1 - e) + 2, 0); ctx.closePath(); ctx.fill(); ctx.restore(); }
  ctx.restore();
  if (Math.abs(k - 0.5) < 0.06) { ctx.fillStyle = "rgba(255,252,240,.35)"; ctx.fillRect(0, 0, W, H); }   // o flash do projetor
};
