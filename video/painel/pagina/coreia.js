// Identidade coreana (Ep. 09 v4, 15/11) — "melhor que o Ep. 08 em todos os quesitos".
// Marca: o BUJEOK (부적), talismã amarelo de papel com tinta vermelha de cinábrio; o HANJI (papel coreano de fibra);
// o DOJANG (carimbo vermelho); o JING (gongo). Carregado depois de motor.js; o motor chama:
//   KR.cenas[tipo](c, t)          — telas inteiras ("talisma", "sombra", "agua", "crt", "sumuk", "elevador")
//   KR.efeitos[nome](c, t, cfg)   — por cima da cena (c.efeitos: {flash, aovivo, jing, brasas})
//   KR.trans[tipo](A, B, k, t)    — transições ("queimar", "rasgo", "hanji")
"use strict";
const KR = { cenas: {}, efeitos: {}, trans: {}, _c: {} };
const CINABRIO = "#b3141c", OCRE = "#d8b244";

// ---------------------------------------------------------------- texturas (geradas uma vez, em cache)
function krHanji(w, h, cor = [232, 222, 196], chave = "hanji") {
  const k = `${chave}${w}x${h}`;
  if (KR._c[k]) return KR._c[k];
  const oc = document.createElement("canvas"); oc.width = w; oc.height = h;
  const g = oc.getContext("2d"), f = _fbm(0, Math.ceil(w / 4), Math.ceil(h / 4), chave, 5), fw = Math.ceil(w / 4);
  const im = g.createImageData(w, h), r = _semente(chave + "g");
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const v = f[Math.floor(y / 4) * fw + Math.floor(x / 4)], n = (r() - 0.5) * 10, i = (y * w + x) * 4, m = 0.86 + v * 0.22;
    im.data[i] = cor[0] * m + n; im.data[i + 1] = cor[1] * m + n; im.data[i + 2] = cor[2] * m + n; im.data[i + 3] = 255;
  }
  g.putImageData(im, 0, 0);
  // fibras: fios finos e curvos, mais claros e mais escuros (o que faz o hanji parecer hanji)
  for (let i = 0; i < (w * h) / 900; i++) {
    const x = r() * w, y = r() * h, L = 8 + r() * 46, a = r() * 6.28, cl = r() < 0.6;
    g.strokeStyle = cl ? `rgba(255,250,235,${0.25 + r() * 0.3})` : `rgba(90,70,40,${0.08 + r() * 0.12})`;
    g.lineWidth = 0.4 + r() * 1.1; g.beginPath(); g.moveTo(x, y);
    g.quadraticCurveTo(x + Math.cos(a + 0.8) * L * 0.5, y + Math.sin(a + 0.8) * L * 0.5, x + Math.cos(a) * L, y + Math.sin(a) * L); g.stroke();
  }
  KR._c[k] = oc; return oc;
}
function krCampo(w, h, chave) {   // campo de ruído 0..1 para máscaras (queimar, rasgo, tinta)
  const k = "campo" + chave + w + "x" + h;
  if (!KR._c[k]) KR._c[k] = _fbm(0, w, h, chave, 5);
  return KR._c[k];
}
function krImg(c) { return c.imagem ? IMG["img:" + c.imagem] : null; }
function krFundo(im, t, c, filtro, zoom = [1.04, 1.1]) {
  const { W, H } = D;
  if (!im) { ctx.fillStyle = "#070605"; ctx.fillRect(0, 0, W, H); return; }
  const z = zoom[0] + (zoom[1] - zoom[0]) * easeInOut(lin(t, c.t0, Math.max(1, c.t1 - c.t0)));
  ctx.save(); ctx.filter = filtro || "none"; cobrir(im, 0, 0, W, H, z, c.foco ? c.foco[0] || c.foco : [0.5, 0.5]); ctx.restore();
}

// ---------------------------------------------------------------- 1) CARTÃO DE CAPÍTULO: o talismã
// c: {tipo:"talisma", numero:"제1장", numero_pt:"CAPÍTULO 1", titulo:"O quarto do magistrado", ano:"séc. XVI",
//     selo:"恨", imagem (fundo)}
// Tempo: 0–0.7 o talismã desce e assenta · 0.5–1.9 o pincel escreve o número (de cima para baixo) · 1.9 o carimbo
// bate (o gongo jing entra no plano de som nesse instante) · 2.2–3.2 o título em português · fim: queima (transição).
KR.cenas.talisma = function (c, t) {
  const { W, H } = D, u = t - c.t0;
  krFundo(krImg(c), t, c, "blur(7px) brightness(0.3) saturate(0.55) sepia(0.25)", [1.08, 1.0]);
  // luz de vela por trás (quente, respirando)
  const resp = 0.85 + 0.15 * Math.sin(t * 7.3) * Math.sin(t * 3.1 + 1);
  const lg = ctx.createRadialGradient(W * 0.36, H * 0.5, 0, W * 0.36, H * 0.5, H * 0.75);
  lg.addColorStop(0, `rgba(255,150,60,${0.22 * resp})`); lg.addColorStop(1, "rgba(0,0,0,0)");
  ctx.fillStyle = lg; ctx.fillRect(0, 0, W, H);
  // o talismã: desce balançando e assenta
  const pw = H * 0.34, ph = H * 0.86, cx = W * 0.36, cy = H * 0.5;
  const e = easeOut(lin(u, 0, 0.7)), y = cy - (1 - e) * H * 0.35, ang = (1 - e) * 0.12 * Math.sin(u * 9) + 0.012 * Math.sin(t * 1.3);
  const al = lin(u, 0, 0.25);
  const papel = KR._papelTalisma || (KR._papelTalisma = (() => {
    const oc = document.createElement("canvas"); oc.width = Math.round(pw); oc.height = Math.round(ph);
    const g = oc.getContext("2d"), tx = krHanji(oc.width, oc.height, [222, 182, 72], "bujeok");
    // borda irregular (papel cortado à mão)
    const r = _semente("borda"); g.beginPath();
    const pts = [];
    for (let i = 0; i <= 40; i++) pts.push([i / 40 * oc.width, r() * 3]);
    for (let i = 0; i <= 80; i++) pts.push([oc.width - r() * 3, i / 80 * oc.height]);
    for (let i = 40; i >= 0; i--) pts.push([i / 40 * oc.width, oc.height - r() * 3]);
    for (let i = 80; i >= 0; i--) pts.push([r() * 3, i / 80 * oc.height]);
    pts.forEach(([x, y], i) => (i ? g.lineTo(x, y) : g.moveTo(x, y))); g.closePath(); g.clip();
    g.drawImage(tx, 0, 0);
    // manchas de idade nas bordas
    const v = g.createRadialGradient(oc.width / 2, oc.height / 2, oc.width * 0.2, oc.width / 2, oc.height / 2, oc.height * 0.62);
    v.addColorStop(0, "rgba(0,0,0,0)"); v.addColorStop(1, "rgba(90,50,10,.45)"); g.fillStyle = v; g.fillRect(0, 0, oc.width, oc.height);
    return oc;
  })());
  ctx.save(); ctx.globalAlpha = al; ctx.translate(cx, y); ctx.rotate(ang);
  ctx.shadowColor = "rgba(0,0,0,.75)"; ctx.shadowBlur = H * 0.05; ctx.shadowOffsetY = H * 0.015;
  ctx.drawImage(papel, -pw / 2, -ph / 2); ctx.shadowColor = "transparent";
  // moldura dupla em cinábrio, traçada pelo pincel
  const pb = easeInOut(lin(u, 0.45, 0.6));
  ctx.strokeStyle = CINABRIO; ctx.globalAlpha = al * 0.92; ctx.lineJoin = "round";
  for (const [m, lw] of [[0.07, H * 0.006], [0.1, H * 0.0025]]) {
    const x0 = -pw / 2 + pw * m, y0 = -ph / 2 + pw * m, w = pw * (1 - 2 * m), h = ph - 2 * pw * m, per = 2 * (w + h);
    ctx.lineWidth = lw; ctx.setLineDash([per * pb, per]); ctx.strokeRect(x0, y0, w, h);
  }
  ctx.setLineDash([]);
  // o número em hangul, vertical, escrito de cima para baixo (pincel): revela por recorte com borda de tinta
  const txt = (c.numero || "제1장").split(""), fs = pw * 0.5;
  ctx.font = `400 ${fs}px "Nanum Brush Script"`; ctx.textAlign = "center"; ctx.textBaseline = "middle";
  const topo = -ph / 2 + ph * 0.2, passo = fs * 0.98, pe = lin(u, 0.55, 1.35) * txt.length;
  txt.forEach((ch, i) => {
    const p = clamp(pe - i); if (p <= 0) return;
    const yy = topo + i * passo;
    ctx.save(); ctx.beginPath(); ctx.rect(-pw / 2, yy - fs * 0.6, pw, fs * 1.2 * easeOut(p)); ctx.clip();
    if (/[0-9]/.test(ch)) ctx.font = `800 ${fs * 0.82}px "Nanum Myeongjo"`; else ctx.font = `400 ${fs}px "Nanum Brush Script"`;
    ctx.fillStyle = "rgba(150,10,15,.35)"; ctx.filter = "blur(3px)"; ctx.fillText(ch, 2, yy + 2);   // tinta que espalha no papel
    ctx.filter = "none"; ctx.fillStyle = CINABRIO; ctx.fillText(ch, 0, yy);
    ctx.restore();
  });
  // pequenos riscos rituais (as "patas" do talismã) na base
  const pr = easeOut(lin(u, 1.6, 0.4));
  if (pr > 0) {
    ctx.strokeStyle = CINABRIO; ctx.lineWidth = H * 0.004; ctx.lineCap = "round";
    const yb = ph / 2 - pw * 0.42;
    for (let i = -2; i <= 2; i++) { ctx.beginPath(); ctx.moveTo(i * pw * 0.11, yb); ctx.lineTo(i * pw * 0.11 + Math.sin(i * 2) * pw * 0.03, yb + pw * 0.22 * pr); ctx.stroke(); }
  }
  ctx.restore();
  // o carimbo (dojang) bate: escala 1.7 → 1, tranco na tela
  const ts = 1.9, us = u - ts;
  if (us > 0) {
    const s = 1 + 0.7 * Math.pow(1 - easeOut(lin(us, 0, 0.16)), 2), sx = cx + pw * 0.22, sy = cy + ph * 0.34, lado = pw * 0.36;
    ctx.save(); ctx.translate(sx, sy); ctx.rotate(-0.06); ctx.scale(s, s); ctx.globalAlpha = 0.9 * lin(us, 0, 0.05);
    ctx.fillStyle = "#c0161e"; rr(-lado / 2, -lado / 2, lado, lado, lado * 0.08); ctx.fill();
    ctx.globalCompositeOperation = "destination-out"; ctx.font = `700 ${lado * 0.72}px "Nanum Myeongjo", "Shippori Mincho"`;
    ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText(c.selo || "恨", 0, lado * 0.04);
    // falhas da tinta do carimbo
    const r = _semente("selo" + (c.selo || "")); for (let i = 0; i < 26; i++) { ctx.beginPath(); ctx.arc((r() - 0.5) * lado, (r() - 0.5) * lado, r() * lado * 0.035, 0, 6.29); ctx.fill(); }
    ctx.restore();
  }
  // título em português à direita, com fio vermelho
  const a2 = easeOut(lin(u, 2.2, 0.7)), xt = W * 0.53;
  if (a2 > 0) {
    ctx.save(); ctx.globalAlpha = a2; ctx.textAlign = "left"; ctx.textBaseline = "alphabetic";
    ctx.fillStyle = CINABRIO; ctx.fillRect(xt, H * 0.36, W * 0.0035, H * 0.3 * a2);
    ctx.font = `700 ${Math.round(H * 0.028)}px "Inter"`; ctx.fillStyle = "#cdbb98";
    ctx.fillText((c.numero_pt || "").toUpperCase().split("").join(" "), xt + W * 0.02, H * 0.41);
    let fsT = Math.round(H * 0.078); ctx.font = `700 ${fsT}px "Cinzel"`;
    const tit = c.titulo || "", maxW = W * 0.42; let ls = [tit];
    if (ctx.measureText(tit).width > maxW) { const ps = tit.split(" "), m = Math.ceil(ps.length / 2); ls = [ps.slice(0, m).join(" "), ps.slice(m).join(" ")]; }
    while (Math.max(...ls.map((l) => ctx.measureText(l).width)) > maxW && fsT > 20) { fsT -= 2; ctx.font = `700 ${fsT}px "Cinzel"`; }
    ctx.fillStyle = "#f3ead6"; ctx.shadowColor = "rgba(0,0,0,.9)"; ctx.shadowBlur = 18;
    const n = Math.floor(lin(u, 2.3, 0.9) * tit.length); let resto = n;
    ls.forEach((l, k) => { const m = Math.max(0, Math.min(l.length, resto)); resto -= l.length + 1; ctx.fillText(l.slice(0, m), xt + W * 0.02, H * 0.5 + k * fsT * 1.12); });
    ctx.shadowBlur = 0; ctx.font = `700 ${Math.round(H * 0.036)}px "Inter"`; ctx.fillStyle = "#d9352c"; ctx.globalAlpha = a2 * easeOut(lin(u, 3.0, 0.5));
    ctx.fillText(c.ano || "", xt + W * 0.02, H * 0.5 + ls.length * fsT * 1.12 + H * 0.03);
    ctx.restore();
  }
  KR.efeitos.jing(c, t, { em: ts, forca: 0.9 });   // tranco + clarão quente no instante do carimbo
};

// ---------------------------------------------------------------- 2) EFEITOS por cima da cena
// jing: o gongo — tranco de câmera que decai + clarão quente + leve separação de cor. cfg {em (s após t0), forca}
KR.efeitos.jing = function (c, t, cfg = {}) {
  const { W, H } = D, u = t - c.t0 - (cfg.em ?? 0), f = cfg.forca ?? 1;
  if (u < 0 || u > 1.2) return;
  const dec = Math.exp(-u * 5.5) * f;
  const im = _canvas("jingCopia", W, H); const g = im.getContext("2d"); g.clearRect(0, 0, W, H); g.drawImage(cv, 0, 0);
  const dx = Math.sin(u * 70) * W * 0.008 * dec, dy = Math.cos(u * 53) * H * 0.008 * dec, s = 1 + 0.025 * dec;
  ctx.save(); ctx.fillStyle = "#000"; ctx.fillRect(0, 0, W, H);
  ctx.translate(W / 2 + dx, H / 2 + dy); ctx.scale(s, s); ctx.translate(-W / 2, -H / 2); ctx.drawImage(im, 0, 0);
  if (dec > 0.05) { ctx.globalCompositeOperation = "screen"; ctx.globalAlpha = 0.28 * dec; ctx.filter = "hue-rotate(-40deg) saturate(3)"; ctx.drawImage(im, W * 0.004 * dec, 0); }
  ctx.restore();
  if (u < 0.25) { ctx.fillStyle = `rgba(255,214,150,${0.32 * f * (1 - u / 0.25)})`; ctx.fillRect(0, 0, W, H); }
};
// flash: foto de celular com flash no escuro — tudo preto, estoura o branco, a imagem "dura" congela e escurece.
// cfg {em, imagem (opcional: a foto revelada)}
KR.efeitos.flash = function (c, t, cfg = {}) {
  const { W, H } = D, u = t - c.t0 - (cfg.em ?? 0.8);
  if (u < 0) { ctx.fillStyle = "rgba(0,0,0,.93)"; ctx.fillRect(0, 0, W, H); return; }
  const im = cfg.imagem ? IMG["img:" + cfg.imagem] : null;
  if (im) { ctx.save(); ctx.filter = "contrast(1.5) brightness(1.25) saturate(0.6)"; cobrir(im, 0, 0, W, H, 1.0); ctx.restore(); }
  const rg = ctx.createRadialGradient(W / 2, H / 2, H * 0.1, W / 2, H / 2, H * 0.85);   // luz do flash: centro estourado
  rg.addColorStop(0, "rgba(255,255,255,.18)"); rg.addColorStop(0.6, "rgba(0,0,0,0)"); rg.addColorStop(1, "rgba(0,0,0,.85)");
  ctx.fillStyle = rg; ctx.fillRect(0, 0, W, H);
  if (u < 0.35) { ctx.fillStyle = `rgba(255,255,255,${Math.pow(1 - u / 0.35, 1.6)})`; ctx.fillRect(0, 0, W, H); }
};
// aovivo: transmissão ao vivo da madrugada (Gonjiam) — visão noturna verde, ● AO VIVO, espectadores subindo,
// quadro que trava e pixela. cfg {espectadores:[ini, fim], travar:[t, ...]}
KR.efeitos.aovivo = function (c, t, cfg = {}) {
  const { W, H } = D, u = t - c.t0;
  const im = _canvas("aoVivo", W, H), g = im.getContext("2d"); g.drawImage(cv, 0, 0);
  ctx.save(); ctx.filter = "grayscale(1) brightness(1.35) contrast(1.25)"; ctx.drawImage(im, 0, 0); ctx.restore();
  ctx.save(); ctx.globalCompositeOperation = "multiply"; ctx.fillStyle = "#5dff8a"; ctx.fillRect(0, 0, W, H); ctx.restore();
  for (const tv of cfg.travar || []) {   // trava: repete um quadro em blocos
    if (u > tv && u < tv + 0.45) { const b = _canvas("aoBloco", 96, 54), gb = b.getContext("2d"); gb.drawImage(cv, 0, 0, 96, 54);
      ctx.save(); ctx.imageSmoothingEnabled = false; ctx.globalAlpha = 0.85; ctx.drawImage(b, 0, 0, W, H); ctx.restore(); }
  }
  const r = rng(Math.floor(t * 30)); ctx.fillStyle = "rgba(255,255,255,.05)";
  for (let i = 0; i < 160; i++) ctx.fillRect(r() * W, r() * H, 2, 2);
  ctx.save(); ctx.fillStyle = "rgba(0,0,0,.45)"; rr(W * 0.03, H * 0.04, W * 0.2, H * 0.065, 8); ctx.fill();
  ctx.fillStyle = Math.floor(t * 2) % 2 ? "#ff2a2a" : "#a81a1a"; ctx.beginPath(); ctx.arc(W * 0.05, H * 0.072, H * 0.012, 0, 6.29); ctx.fill();
  ctx.fillStyle = "#fff"; ctx.font = `800 ${Math.round(H * 0.03)}px "Inter"`; ctx.textBaseline = "middle"; ctx.fillText("AO VIVO", W * 0.065, H * 0.073);
  const [e0, e1] = cfg.espectadores || [312, 4870], n = Math.round(e0 + (e1 - e0) * easeInOut(lin(u, 0, Math.max(1, c.t1 - c.t0))));
  ctx.font = `500 ${Math.round(H * 0.024)}px "Inter"`; ctx.fillText(`👁 ${n.toLocaleString("pt-BR")}`, W * 0.155, H * 0.073);
  const s = Math.floor(u), hh = String(3 + Math.floor((12 * 60 + s) / 3600)).padStart(2, "0"), mm = String(Math.floor((12 * 60 + s) / 60) % 60).padStart(2, "0");
  ctx.textAlign = "right"; ctx.font = `500 ${Math.round(H * 0.026)}px "Special Elite"`; ctx.fillText(`${hh}:${mm}:${String(s % 60).padStart(2, "0")}`, W * 0.97, H * 0.073);
  ctx.restore();
};
// brasas subindo (para o fim do talismã e cenas de vela)
KR.efeitos.brasas = function (c, t, cfg = {}) {
  const { W, H } = D, n = cfg.n ?? 40, r = _semente("brasa");
  ctx.save(); ctx.globalCompositeOperation = "lighter";
  for (let i = 0; i < n; i++) {
    const x0 = r(), v = 0.05 + r() * 0.12, f = r() * 6.28, y = (1.1 - ((t * v + r()) % 1.2)) * H, x = (x0 + 0.02 * Math.sin(t * 1.5 + f)) * W;
    ctx.fillStyle = `rgba(255,${120 + r() * 80},40,${0.5 + 0.4 * Math.sin(t * 9 + f)})`; ctx.beginPath(); ctx.arc(x, y, 1 + r() * 2.5, 0, 6.29); ctx.fill();
  }
  ctx.restore();
};

// ---------------------------------------------------------------- 3) CENAS EXCLUSIVAS de cada história
// ARANG — teatro de sombras: a porta de papel iluminada por dentro, a vela tremendo no canto; a sombra de uma moça
// de cabelo solto cresce atrás do papel (ela se aproxima) e a chama se inclina para a porta. cfg na cena:
// {tipo:"sombra", imagem (opcional: fundo do quarto), chega:[t0, dur] (s após o início), vela:[x,y]}
KR.cenas.sombra = function (c, t) {
  const { W, H } = D, u = t - c.t0, [c0, cd] = c.chega || [0.8, 4.5], p = easeInOut(lin(u, c0, cd));
  const im = krImg(c);
  if (im) krFundo(im, t, c, "brightness(0.55) saturate(0.6)", [1.02, 1.08]); else { ctx.fillStyle = "#0b0806"; ctx.fillRect(0, 0, W, H); }
  // a porta: grade de madeira com hanji iluminado
  const px = W * 0.18, py = H * 0.06, pw = W * 0.64, ph = H * 0.9;
  const tx = krHanji(512, 512, [236, 214, 170], "porta");
  const fl = 0.85 + 0.15 * (Math.sin(t * 11) * 0.5 + Math.sin(t * 6.7 + 2) * 0.5) * (1 - 0.6 * p);
  ctx.save(); ctx.beginPath(); ctx.rect(px, py, pw, ph); ctx.clip();
  ctx.globalAlpha = 0.97; ctx.drawImage(tx, px, py, pw, ph);
  const lz = ctx.createRadialGradient(W * 0.5, H * 0.55, 0, W * 0.5, H * 0.55, pw * 0.75);
  lz.addColorStop(0, `rgba(255,190,110,${0.55 * fl})`); lz.addColorStop(1, `rgba(60,30,10,${0.75})`);
  ctx.globalCompositeOperation = "multiply"; ctx.globalAlpha = 1; ctx.fillStyle = lz; ctx.fillRect(px, py, pw, ph);
  ctx.globalCompositeOperation = "source-over";
  // a sombra: silhueta feminina, cabelo solto e comprido; cresce e fica nítida conforme se aproxima do papel
  const esc = 0.55 + 0.6 * p, nit = 14 * (1 - p) + 2, sx = W * 0.5 + W * 0.04 * Math.sin(u * 0.4), base = py + ph;
  ctx.save(); ctx.filter = `blur(${nit}px)`; ctx.globalAlpha = 0.25 + 0.6 * p; ctx.fillStyle = "#1a0f08";
  ctx.translate(sx, base); ctx.scale(esc, esc); const hh = ph * 0.95;
  // metade direita do contorno (x, y em frações da altura), espelhada: cabelo solto cobrindo cabeça e ombros,
  // braços caídos, hanbok de luto até o chão
  const P = [[0, -1.0], [0.045, -0.995], [0.072, -0.965], [0.08, -0.92], [0.082, -0.87], [0.09, -0.83], [0.12, -0.8],
             [0.135, -0.76], [0.14, -0.7], [0.15, -0.62], [0.142, -0.55], [0.155, -0.5], [0.13, -0.47], [0.152, -0.44],
             [0.16, -0.36], [0.175, -0.25], [0.2, -0.13], [0.23, -0.02], [0.21, 0]];
  ctx.beginPath(); ctx.moveTo(0, -hh);
  for (const [x, y] of P) ctx.lineTo(x * hh, y * hh);
  for (const [x, y] of [...P].reverse()) ctx.lineTo(-x * hh * (1 + 0.04 * Math.sin(y * 9)), y * hh);
  ctx.closePath(); ctx.fill();
  ctx.restore();
  ctx.restore();
  // a treliça de madeira da porta por cima
  ctx.save(); ctx.strokeStyle = "#1d130b"; ctx.lineWidth = W * 0.007;
  ctx.strokeRect(px, py, pw, ph); ctx.lineWidth = W * 0.0035;
  for (let i = 1; i < 6; i++) { const x = px + pw * i / 6; ctx.beginPath(); ctx.moveTo(x, py); ctx.lineTo(x, py + ph); ctx.stroke(); }
  for (let j = 1; j < 8; j++) { const y = py + ph * j / 8; ctx.beginPath(); ctx.moveTo(px, y); ctx.lineTo(px + pw, y); ctx.stroke(); }
  ctx.restore();
  // a vela (do lado de cá): chama que treme e, no fim, se inclina para a porta
  const [vx, vy] = c.vela || [0.1, 0.8], X = W * vx, Y = H * vy, inc = -0.5 * p;
  ctx.save(); ctx.fillStyle = "#e9dcc0"; ctx.fillRect(X - W * 0.008, Y, W * 0.016, H * 0.16);
  const lg = ctx.createRadialGradient(X, Y - H * 0.03, 0, X, Y - H * 0.03, H * 0.25); lg.addColorStop(0, `rgba(255,180,80,${0.45 * fl})`); lg.addColorStop(1, "rgba(0,0,0,0)");
  ctx.globalCompositeOperation = "lighter"; ctx.fillStyle = lg; ctx.fillRect(0, 0, W, H);
  ctx.translate(X, Y); ctx.rotate(inc + 0.08 * Math.sin(t * 13) * (1 - p)); const fh = H * 0.05 * (0.9 + 0.2 * fl);
  const ch = ctx.createLinearGradient(0, 0, 0, -fh); ch.addColorStop(0, "rgba(255,120,30,1)"); ch.addColorStop(0.5, "rgba(255,215,120,1)"); ch.addColorStop(1, "rgba(255,255,220,0)");
  ctx.fillStyle = ch; ctx.beginPath(); ctx.moveTo(-W * 0.006, 0); ctx.quadraticCurveTo(-W * 0.006, -fh * 0.6, 0, -fh); ctx.quadraticCurveTo(W * 0.006, -fh * 0.6, W * 0.006, 0); ctx.fill();
  ctx.restore();
  const v = ctx.createRadialGradient(W / 2, H / 2, H * 0.3, W / 2, H / 2, H * 0.85); v.addColorStop(0, "rgba(0,0,0,0)"); v.addColorStop(1, "rgba(0,0,0,.7)"); ctx.fillStyle = v; ctx.fillRect(0, 0, W, H);
};
// AS IRMÃS DO LAGO — água viva: a metade de baixo da imagem (o lago) ondula de verdade, a névoa corre em camadas,
// e num instante abrem-se círculos na água onde ela afundou. {tipo:"agua", imagem, horizonte:0.55, afunda:[x,y,t]}
KR.cenas.agua = function (c, t) {
  const { W, H } = D, im = krImg(c), hz = (c.horizonte ?? 0.55) * H;
  krFundo(im, t, c, "brightness(0.8) saturate(0.7)", [1.06, 1.12]);
  const cp = _canvas("aguaCp", W, H), g = cp.getContext("2d"); g.drawImage(cv, 0, 0);
  const faixa = 3;
  for (let y = hz; y < H; y += faixa) {
    const prof = (y - hz) / (H - hz), amp = W * 0.004 * (0.3 + prof * 1.6);
    const dx = Math.sin(y * 0.045 + t * 1.6) * amp + Math.sin(y * 0.013 - t * 0.9) * amp * 0.6;
    ctx.drawImage(cp, 0, y, W, faixa, dx, y, W, faixa);
  }
  // brilho do luar mexendo na água
  ctx.save(); ctx.globalCompositeOperation = "screen";
  for (let i = 0; i < 26; i++) { const y = hz + (H - hz) * (i / 26) ** 1.4, w = W * (0.03 + 0.08 * (i / 26)), x = W * 0.5 + Math.sin(i * 7.1 + t * 1.3) * W * 0.05;
    ctx.globalAlpha = 0.1 * (0.5 + 0.5 * Math.sin(t * 3 + i)); ctx.fillStyle = "#cfe2ff"; ctx.fillRect(x - w / 2, y, w, 2); }
  ctx.restore();
  // círculos onde ela afundou
  if (c.afunda) {
    const [ax, ay, at] = c.afunda, ua = t - c.t0 - at;
    if (ua > 0) for (let k = 0; k < 4; k++) {
      const uk = ua - k * 0.55; if (uk <= 0) continue;
      const R = W * 0.03 + uk * W * 0.07, a = Math.max(0, 0.6 - uk * 0.18);
      ctx.save(); ctx.strokeStyle = `rgba(220,235,255,${a})`; ctx.lineWidth = 2; ctx.beginPath(); ctx.ellipse(ax * W, ay * H, R, R * 0.22, 0, 0, 6.29); ctx.stroke(); ctx.restore();
    }
  }
  // névoa em duas camadas, correndo em sentidos opostos sobre a água
  const nv = texNevoa();
  for (const [vel, y0, al, esc] of [[18, hz - H * 0.12, 0.5, 1.0], [-11, hz + H * 0.02, 0.35, 1.4]]) {
    const w = W * esc, off = ((t * vel) % w + w) % w;
    ctx.save(); ctx.globalAlpha = al; for (let x = -off; x < W; x += w) ctx.drawImage(nv, x, y0, w, H * 0.3); ctx.restore();
  }
};
// TV DE TUBO dos anos 70 (Jeonseol-ui Gohyang): a imagem dentro de um televisor de madeira numa sala escura, com
// linhas, chuvisco, a imagem rolando e o "liga/desliga" que colapsa numa linha. {tipo:"crt", imagem, liga:0.2,
// desliga:(s antes do fim) ou null, rolar:[t...]}
KR.cenas.crt = function (c, t) {
  // 15/11 v2 ("melhorar a TV"): uma SALA coreana dos anos 70 de verdade — parede de papel, a TV de madeira com
  // antena de coelho e paninho de crochê, a família de costas no chão (silhuetas), a luz da tela tremendo nas
  // costas deles e na parede; na tela: fósforo esverdeado, vidro curvo (barril), faixa de interferência rolando,
  // perda de sincronia horizontal, chuvisco, e o liga/desliga que colapsa numa linha e num ponto.
  const { W, H } = D, u = t - c.t0, im = krImg(c), dur = Math.max(1, c.t1 - c.t0);
  const lg = c.liga ?? 0.2, dl = c.desliga != null ? dur - c.desliga : 1e9;
  let ky = 1, kx = 1;
  if (u < lg + 0.35) { const k = lin(u, lg, 0.35); ky = easeOut(k); kx = Math.min(1, k * 3); }
  if (u > dl) { const k = lin(u, dl, 0.45); ky = Math.max(0.004, 1 - easeInOut(k * 1.6)); kx = 1 - easeInOut(Math.max(0, k - 0.6) / 0.4); }
  const brilho = ky * kx, osc = 0.82 + 0.18 * Math.sin(t * 23) * Math.sin(t * 7.7 + 1);   // a tela pisca
  // câmera: entra devagar, de trás da família, e se aproxima da tela
  const z = 1 + 0.12 * easeInOut(lin(u, 0, dur));
  ctx.save(); ctx.translate(W / 2, H * 0.42); ctx.scale(z, z); ctx.translate(-W / 2, -H * 0.42);
  // sala: parede de hanji escura, rodapé de madeira, piso de ondol (papel oleado amarelado)
  const pw0 = ctx.createLinearGradient(0, 0, 0, H * 0.66); pw0.addColorStop(0, "#2a2219"); pw0.addColorStop(1, "#3b3022");
  ctx.fillStyle = pw0; ctx.fillRect(0, 0, W, H * 0.66);
  ctx.save(); ctx.globalAlpha = 0.18; ctx.globalCompositeOperation = "overlay"; ctx.drawImage(krHanji(1920, 1080, [128, 128, 128], "parede70b"), 0, 0, W, H * 0.66); ctx.restore();
  const pg = ctx.createLinearGradient(0, H * 0.66, 0, H); pg.addColorStop(0, "#3a2614"); pg.addColorStop(1, "#1d1209");
  ctx.fillStyle = pg; ctx.fillRect(0, H * 0.66, W, H * 0.34);
  ctx.strokeStyle = "rgba(0,0,0,.35)"; ctx.lineWidth = 2; for (let i = 0; i < 9; i++) { const y = H * 0.66 + (H * 0.34) * (i / 9) ** 1.6; ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
  ctx.fillStyle = "#24160b"; ctx.fillRect(0, H * 0.64, W, H * 0.025);
  // a TV: gabinete de madeira com pés, alto-falante de tecido, dois botões grandes, antena de coelho, paninho
  const tw = W * 0.34, th = tw * 0.76, tx = W * 0.5 - tw * 0.62, ty = H * 0.2, cw = tw * 1.42, ch = th * 1.22, cx0 = tx - tw * 0.07, cy0 = ty - th * 0.11;
  ctx.fillStyle = "#120b05"; ctx.fillRect(cx0 + cw * 0.08, cy0 + ch, cw * 0.05, H * 0.12); ctx.fillRect(cx0 + cw * 0.87, cy0 + ch, cw * 0.05, H * 0.12);
  const mg = ctx.createLinearGradient(cx0, 0, cx0 + cw, 0); mg.addColorStop(0, "#2e1a0c"); mg.addColorStop(0.45, "#5b351a"); mg.addColorStop(1, "#26150a");
  ctx.fillStyle = mg; rr(cx0, cy0, cw, ch, tw * 0.03); ctx.fill();
  ctx.strokeStyle = "rgba(0,0,0,.25)"; ctx.lineWidth = 1; for (let i = 0; i < 40; i++) { const y = cy0 + ch * i / 40; ctx.beginPath(); ctx.moveTo(cx0, y + Math.sin(i) * 2); ctx.lineTo(cx0 + cw, y + Math.cos(i) * 2); ctx.stroke(); }   // veio da madeira
  const ax = tx + tw * 1.08, aw = cw - (ax - cx0) - tw * 0.05;
  ctx.fillStyle = "#1a120b"; rr(ax, ty + th * 0.08, aw, th * 0.5, 6); ctx.fill();
  ctx.strokeStyle = "rgba(120,90,60,.35)"; for (let y = ty + th * 0.1; y < ty + th * 0.56; y += 5) { ctx.beginPath(); ctx.moveTo(ax + 4, y); ctx.lineTo(ax + aw - 4, y); ctx.stroke(); }
  for (let i = 0; i < 2; i++) { const bx = ax + aw / 2, by = ty + th * (0.7 + i * 0.17), br = aw * 0.24;
    const gb = ctx.createRadialGradient(bx - br * 0.3, by - br * 0.3, 0, bx, by, br); gb.addColorStop(0, "#c9c2b2"); gb.addColorStop(1, "#4a443a");
    ctx.fillStyle = gb; ctx.beginPath(); ctx.arc(bx, by, br, 0, 6.29); ctx.fill(); ctx.strokeStyle = "#222"; ctx.beginPath(); ctx.moveTo(bx, by); ctx.lineTo(bx + br * Math.cos(1 + i), by + br * Math.sin(1 + i)); ctx.stroke(); }
  ctx.fillStyle = "rgba(225,218,200,.85)"; ctx.beginPath();   // paninho de crochê
  for (let i = 0; i <= 24; i++) { const x = cx0 + cw * 0.2 + cw * 0.6 * i / 24; ctx.lineTo(x, cy0 + 6 + (i % 2 ? 10 : 0)); }
  ctx.lineTo(cx0 + cw * 0.8, cy0 - 2); ctx.lineTo(cx0 + cw * 0.2, cy0 - 2); ctx.fill();
  ctx.strokeStyle = "#8a8f94"; ctx.lineWidth = 3; ctx.lineCap = "round";   // antena de coelho
  const ab = [cx0 + cw * 0.5, cy0 - 4];
  ctx.fillStyle = "#1b1b1b"; ctx.beginPath(); ctx.ellipse(ab[0], ab[1], cw * 0.05, cw * 0.018, 0, 0, 6.29); ctx.fill();
  for (const a of [-2.05, -1.12]) { ctx.beginPath(); ctx.moveTo(ab[0], ab[1]); ctx.lineTo(ab[0] + Math.cos(a) * H * 0.33, ab[1] + Math.sin(a) * H * 0.33); ctx.stroke(); }
  // a imagem da tela (640×480), com sinal ruim
  const sc = _canvas("crtTela", 640, 480), g = sc.getContext("2d");
  g.fillStyle = "#000"; g.fillRect(0, 0, 640, 480);
  if (im) {
    let rol = 0; for (const rt of c.rolar || []) { const ur = u - rt; if (ur > 0 && ur < 0.9) rol = (easeInOut(ur / 0.9) * 480) % 480; }
    g.filter = "grayscale(1) contrast(1.35) brightness(1.08) blur(0.7px)";
    const s = Math.max(640 / im.width, 480 / im.height) * 1.04, iw = im.width * s, ih = im.height * s;
    for (let y = 0; y < 480; y += 4) {   // perda de sincronia horizontal: as linhas escorregam
      const jit = (Math.sin(y * 0.09 + t * 40) * (Math.sin(t * 2.3) > 0.85 ? 18 : 1.5));
      g.drawImage(im, 0, ((y + rol) % 480 - (480 - ih) / 2) / s, im.width, 4 / s, (640 - iw) / 2 + jit, y, iw, 4);
    }
    g.filter = "none";
  }
  const r = rng(Math.floor(t * 30) + 3), img = g.getImageData(0, 0, 640, 480), d = img.data;
  const banda = ((t * 0.35) % 1.3 - 0.15) * 480;   // a faixa de interferência que sobe
  for (let i = 0; i < d.length; i += 4) {
    const y = (i / 4 / 640) | 0, nb = Math.max(0, 1 - Math.abs(y - banda) / 26), n = (r() - 0.5) * 255 * (0.16 + 0.35 * nb);
    d[i] = (d[i] + n) * 0.86; d[i + 1] = (d[i + 1] + n) * 1.0; d[i + 2] = (d[i + 2] + n) * 0.9;   // fósforo levemente verde
  }
  g.putImageData(img, 0, 0);
  g.fillStyle = "rgba(0,0,0,.33)"; for (let y = 0; y < 480; y += 3) g.fillRect(0, y, 640, 1);
  // vidro curvo: desenha a tela em faixas com largura variando (barril) + brilho que vaza
  ctx.save(); rr(tx, ty, tw, th, tw * 0.07); ctx.clip(); ctx.fillStyle = "#070807"; ctx.fillRect(tx, ty, tw, th);
  if (kx > 0.001) {
    const N = 48, ah = th * ky, a0 = ty + (th - ah) / 2;
    for (let i = 0; i < N; i++) { const fy = i / N, curv = 1 - 0.06 * Math.pow(2 * fy - 1, 2), w = tw * kx * curv;
      ctx.globalAlpha = osc; ctx.drawImage(sc, 0, fy * 480, 640, 480 / N, tx + (tw - w) / 2, a0 + fy * ah, w, ah / N + 1); }
    ctx.globalAlpha = 1;
  }
  const vz = ctx.createRadialGradient(tx + tw * 0.38, ty + th * 0.3, 0, tx + tw / 2, ty + th / 2, tw * 0.62);
  vz.addColorStop(0, "rgba(255,255,255,.07)"); vz.addColorStop(0.6, "rgba(0,0,0,0)"); vz.addColorStop(1, "rgba(0,0,0,.8)");
  ctx.fillStyle = vz; ctx.fillRect(tx, ty, tw, th); ctx.restore();
  // a luz da tela na sala (brilho que vaza do vidro + parede)
  ctx.save(); ctx.globalCompositeOperation = "screen";
  const lz = ctx.createRadialGradient(tx + tw / 2, ty + th / 2, 0, tx + tw / 2, ty + th / 2, W * 0.75);
  lz.addColorStop(0, `rgba(150,185,175,${0.32 * brilho * osc})`); lz.addColorStop(1, "rgba(0,0,0,0)"); ctx.fillStyle = lz; ctx.fillRect(0, 0, W, H);
  ctx.restore();
  // a família de costas no chão (silhuetas), com a borda acesa pela TV
  // silhuetas desfocadas (perto da câmera = fora de foco), cabelo e ombros orgânicos, borda acesa pela TV
  const fam = [[0.16, 1.08, 0.36, -0.08], [0.43, 1.16, 0.44, 0.03], [0.7, 1.1, 0.32, 0.06], [0.9, 1.18, 0.4, -0.05]];
  for (const [fx, fy, fs, inc] of fam) {
    const X = W * fx, Y = H * fy, s = H * fs;
    ctx.save(); ctx.translate(X, Y); ctx.rotate(inc); ctx.filter = "blur(7px)"; ctx.fillStyle = "#040302";
    ctx.beginPath();
    ctx.moveTo(-s * 0.75, s * 0.5); ctx.bezierCurveTo(-s * 0.72, -s * 0.35, -s * 0.38, -s * 0.52, -s * 0.2, -s * 0.6);   // ombro esq.
    ctx.bezierCurveTo(-s * 0.3, -s * 0.9, -s * 0.26, -s * 1.28, 0, -s * 1.3);                                          // cabeça (com cabelo)
    ctx.bezierCurveTo(s * 0.26, -s * 1.28, s * 0.3, -s * 0.9, s * 0.2, -s * 0.6);
    ctx.bezierCurveTo(s * 0.38, -s * 0.52, s * 0.72, -s * 0.35, s * 0.75, s * 0.5); ctx.closePath(); ctx.fill();
    ctx.globalCompositeOperation = "screen"; ctx.filter = "blur(5px)"; ctx.strokeStyle = `rgba(150,190,180,${0.28 * brilho * osc})`; ctx.lineWidth = s * 0.025;
    ctx.beginPath(); ctx.moveTo(-s * 0.26, -s * 1.0); ctx.bezierCurveTo(-s * 0.26, -s * 1.28, s * 0.26, -s * 1.28, s * 0.26, -s * 1.0); ctx.stroke();
    ctx.restore();
  }
  ctx.restore();
  const v = ctx.createRadialGradient(W / 2, H * 0.45, H * 0.25, W / 2, H * 0.45, H * 0.9); v.addColorStop(0, "rgba(0,0,0,0)"); v.addColorStop(1, "rgba(0,0,0,.75)");
  ctx.fillStyle = v; ctx.fillRect(0, 0, W, H);
};
// IRMÃ RAPOSA — pintura em nanquim (sumuk-hwa) se pintando: a imagem vira tinta sobre hanji e aparece pincelada a
// pincelada; um toque de vermelho no fim (os olhos / o fígado). {tipo:"sumuk", imagem, pintar:4.5}
KR.cenas.sumuk = function (c, t) {
  const { W, H } = D, u = t - c.t0, im = krImg(c), dur = c.pintar ?? 4.5;
  ctx.drawImage(krHanji(W, H, [226, 214, 188], "sumukFundo"), 0, 0);
  if (!im) return;
  const tinta = _canvas("sumukT", W, H), g = tinta.getContext("2d");
  g.globalCompositeOperation = "source-over"; g.clearRect(0, 0, W, H);
  g.filter = "grayscale(1) brightness(1.75) contrast(2.6) blur(0.6px)";
  const z = 1.02 + 0.05 * lin(u, 0, Math.max(1, c.t1 - c.t0)), s = Math.max(W / im.width, H / im.height) * z;
  g.drawImage(im, (W - im.width * s) / 2, (H - im.height * s) / 2, im.width * s, im.height * s); g.filter = "none";
  // máscara de pinceladas: faixas largas com borda de cerdas, na ordem de um pintor (de cima/esquerda para baixo)
  const m = _canvas("sumukM", W, H), gm = m.getContext("2d"); gm.clearRect(0, 0, W, H);
  const r = _semente("sumuk" + (c.imagem || "")), N = 22;
  for (let i = 0; i < N; i++) {
    const p = clamp(lin(u, 0.2 + (i / N) * dur * 0.85, dur * 0.25)); if (p <= 0) continue;
    const y = H * (0.05 + 0.9 * (i / N) + (r() - 0.5) * 0.08), x0 = W * (r() * 0.3 - 0.1), x1 = W * (0.75 + r() * 0.35), lw = H * (0.09 + r() * 0.08);
    gm.lineCap = "round"; gm.strokeStyle = "#000"; gm.lineWidth = lw * 1.4; gm.filter = "blur(22px)";
    gm.beginPath(); gm.moveTo(x0, y); gm.quadraticCurveTo((x0 + x1) / 2, y + (r() - 0.5) * H * 0.12, x0 + (x1 - x0) * easeOut(p), y + (r() - 0.5) * H * 0.04); gm.stroke();
  }
  gm.filter = "none";
  g.globalCompositeOperation = "destination-in"; g.drawImage(m, 0, 0); g.globalCompositeOperation = "source-over";
  ctx.save(); ctx.globalCompositeOperation = "multiply"; ctx.drawImage(tinta, 0, 0); ctx.restore();
  // o vermelho: um ponto que aparece no fim (c.vermelho:[x,y])
  if (c.vermelho) { const a = easeOut(lin(u, dur + 0.3, 0.8)); if (a > 0) { ctx.save(); ctx.globalAlpha = a * 0.85; ctx.fillStyle = CINABRIO; ctx.filter = "blur(2px)";
    for (const [x, y] of c.vermelho) { ctx.beginPath(); ctx.arc(x * W, y * H, H * 0.008, 0, 6.29); ctx.fill(); } ctx.restore(); } }
  const v = ctx.createRadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 0.9); v.addColorStop(0, "rgba(0,0,0,0)"); v.addColorStop(1, "rgba(40,25,10,.55)"); ctx.fillStyle = v; ctx.fillRect(0, 0, W, H);
};
// ELEVADOR — o painel de botões desenhado (nada de IA inventando número): acende na ordem do ritual.
// {tipo:"elevador", sequencia:[[botao, t], ...], andares:10}
KR.cenas.elevador = function (c, t) {
  // 15/11 v2 ("melhorar o elevador"): dentro da cabine, em perspectiva — parede de aço escovado com reflexo, o
  // painel de botões redondos com número gravado e pontos em braile, o mostrador de andar em LED vermelho em cima
  // (sobe de verdade: 1, 2, 3… e o ▲ piscando), câmera na mão chegando perto, lâmpada fluorescente piscando e a luz
  // do botão aceso respingando no metal. {sequencia:[[botão, t], ...], andar:[[andar, t], ...], andares:10}
  const { W, H } = D, u = t - c.t0, n = c.andares || 10, dur = Math.max(1, c.t1 - c.t0);
  const fl = Math.sin(t * 41) > 0.9 || (Math.sin(t * 3.1) > 0.97) ? 0.55 : 1;   // fluorescente falhando
  const mx = W * 0.004 * _ruido1(t * 0.8, 2), my = H * 0.004 * _ruido1(t * 0.7, 5);    // câmera na mão
  const z = 1.0 + 0.22 * easeInOut(lin(u, 0, dur));
  ctx.save(); ctx.translate(W / 2 + mx, H / 2 + my); ctx.scale(z, z); ctx.rotate(0.004 * _ruido1(t * 0.5, 9)); ctx.translate(-W / 2, -H / 2);
  // as duas paredes em perspectiva (canto da cabine) + teto
  const aco = (x0, y0, x1, y1, x2, y2, x3, y3, tom) => {
    ctx.save(); ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.lineTo(x2, y2); ctx.lineTo(x3, y3); ctx.closePath(); ctx.clip();
    const g = ctx.createLinearGradient(x0, 0, x1, 0); g.addColorStop(0, `rgb(${tom * 0.55},${tom * 0.57},${tom * 0.6})`); g.addColorStop(0.5, `rgb(${tom},${tom * 1.02},${tom * 1.05})`); g.addColorStop(1, `rgb(${tom * 0.45},${tom * 0.47},${tom * 0.5})`);
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    const r = _semente("escovado" + tom); ctx.globalAlpha = 0.06; ctx.strokeStyle = "#fff";
    for (let i = 0; i < 260; i++) { const y = r() * H; ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y + (r() - 0.5) * 4); ctx.stroke(); }
    ctx.restore();
  };
  aco(-W * 0.1, -H * 0.1, W * 0.72, H * 0.06, W * 0.72, H * 0.98, -W * 0.1, H * 1.1, 92 * fl);       // parede do painel
  aco(W * 0.72, H * 0.06, W * 1.1, -H * 0.2, W * 1.1, H * 1.25, W * 0.72, H * 0.98, 60 * fl);         // parede lateral (mais escura)
  ctx.strokeStyle = "rgba(0,0,0,.6)"; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(W * 0.72, H * 0.06); ctx.lineTo(W * 0.72, H * 0.98); ctx.stroke();
  // reflexo borrado de uma figura na parede lateral (aparece depois do 5)
  const t5 = (c.sequencia || []).find(([b]) => b === 5); const rf = t5 ? easeInOut(lin(u, t5[1] + 0.4, 1.2)) : 0;
  if (rf > 0) { ctx.save(); ctx.globalAlpha = 0.28 * rf; ctx.filter = "blur(14px)"; ctx.fillStyle = "#0a0806";
    ctx.beginPath(); ctx.ellipse(W * 0.86, H * 0.32, W * 0.03, H * 0.07, 0, 0, 6.29); ctx.fill(); ctx.fillRect(W * 0.825, H * 0.38, W * 0.07, H * 0.5); ctx.restore(); }
  // mostrador do andar (LED vermelho de 7 segmentos) — segue c.andar ou acompanha os botões
  let andar = 1; for (const [a, ta] of c.andar || []) if (u >= ta) andar = a;
  const dx = W * 0.25, dy = H * 0.1, dw = W * 0.22, dh = H * 0.13;
  ctx.fillStyle = "#050404"; rr(dx, dy, dw, dh, 8); ctx.fill(); ctx.strokeStyle = "#555a5f"; ctx.lineWidth = 3; ctx.stroke();
  ctx.save(); ctx.font = `700 ${dh * 0.78}px "Special Elite"`; ctx.textAlign = "center"; ctx.textBaseline = "middle";
  ctx.fillStyle = "rgba(90,10,10,.35)"; ctx.fillText(andar >= 10 ? "88" : "8", dx + dw * 0.6, dy + dh * 0.54);   // segmentos apagados
  ctx.fillStyle = "#ff3322"; ctx.shadowColor = "#ff2010"; ctx.shadowBlur = 18; ctx.fillText(String(andar), dx + dw * 0.6, dy + dh * 0.54);
  if (Math.floor(t * 2.5) % 2 && u > 0.3) { ctx.beginPath(); ctx.moveTo(dx + dw * 0.14, dy + dh * 0.68); ctx.lineTo(dx + dw * 0.24, dy + dh * 0.68); ctx.lineTo(dx + dw * 0.19, dy + dh * 0.32); ctx.fill(); }
  ctx.restore();
  // o painel: placa de aço mais clara, parafusos, botões em 2 colunas, braile ao lado
  const px = W * 0.27, py = H * 0.3, pw = W * 0.2, ph = H * 0.64;
  const gp = ctx.createLinearGradient(px, py, px + pw, py + ph); gp.addColorStop(0, `rgb(${150 * fl},${153 * fl},${158 * fl})`); gp.addColorStop(1, `rgb(${85 * fl},${88 * fl},${92 * fl})`);
  ctx.save(); ctx.shadowColor = "rgba(0,0,0,.6)"; ctx.shadowBlur = 20; ctx.fillStyle = gp; rr(px, py, pw, ph, 10); ctx.fill(); ctx.restore();
  for (const [sx, sy] of [[0.08, 0.04], [0.92, 0.04], [0.08, 0.96], [0.92, 0.96]]) { ctx.fillStyle = "#3c3f42"; ctx.beginPath(); ctx.arc(px + pw * sx, py + ph * sy, 5, 0, 6.29); ctx.fill(); }
  const acesos = {}; for (const [b, tb] of c.sequencia || []) if (u >= tb) acesos[b] = u - tb;
  const linhas = Math.ceil(n / 2), R = pw * 0.15;
  for (let i = 0; i < n; i++) {
    const num = i + 1, col = i % 2, ln = linhas - 1 - Math.floor(i / 2);
    const x = px + pw * (0.3 + col * 0.42), y = py + ph * 0.1 + ln * (ph * 0.82 / linhas) + R;
    const ac = acesos[num] != null, f = ac ? Math.min(1, acesos[num] / 0.06) : 0, ap = ac ? Math.max(0, 1 - acesos[num] / 0.18) : 0;
    ctx.save();
    // anel e botão (afunda um pouco quando aperta)
    ctx.fillStyle = "#2a2c2e"; ctx.beginPath(); ctx.arc(x, y, R * 1.12, 0, 6.29); ctx.fill();
    const gb = ctx.createRadialGradient(x - R * 0.35, y - R * 0.35, 0, x, y, R); gb.addColorStop(0, "#e9ecee"); gb.addColorStop(0.7, "#a3a8ad"); gb.addColorStop(1, "#6c7176");
    ctx.fillStyle = gb; ctx.beginPath(); ctx.arc(x, y + ap * 2, R * (1 - 0.05 * ap), 0, 6.29); ctx.fill();
    if (ac) { ctx.lineWidth = R * 0.16; ctx.strokeStyle = `rgba(255,70,50,${0.7 + 0.3 * f})`; ctx.shadowColor = "rgba(255,40,20,1)"; ctx.shadowBlur = R * 1.4 * f; ctx.beginPath(); ctx.arc(x, y, R * 1.04, 0, 6.29); ctx.stroke(); ctx.shadowBlur = 0;
      const sp = ctx.createRadialGradient(x, y, 0, x, y, R * 4); sp.addColorStop(0, `rgba(255,50,30,${0.22 * f})`); sp.addColorStop(1, "rgba(0,0,0,0)");
      ctx.globalCompositeOperation = "screen"; ctx.fillStyle = sp; ctx.fillRect(x - R * 4, y - R * 4, R * 8, R * 8); ctx.globalCompositeOperation = "source-over"; }
    ctx.fillStyle = ac ? "#7a1a12" : "#3a3d40"; ctx.font = `700 ${R * 0.95}px "Inter"`; ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText(String(num), x, y + ap * 2 + R * 0.04);
    ctx.fillStyle = "rgba(40,42,44,.8)"; for (let b = 0; b < 3; b++) { ctx.beginPath(); ctx.arc(x + R * 1.45, y - R * 0.4 + b * R * 0.4, R * 0.07, 0, 6.29); ctx.fill(); }   // braile
    ctx.restore();
  }
  ctx.restore();
  // luz fria do teto + vinheta + leve desfoque nas bordas (lente)
  const lt = ctx.createLinearGradient(0, 0, 0, H); lt.addColorStop(0, `rgba(210,230,255,${0.12 * fl})`); lt.addColorStop(0.5, "rgba(0,0,0,0)"); ctx.fillStyle = lt; ctx.fillRect(0, 0, W, H);
  const v = ctx.createRadialGradient(W * 0.42, H * 0.55, H * 0.3, W * 0.42, H * 0.55, H); v.addColorStop(0, "rgba(0,0,0,0)"); v.addColorStop(1, "rgba(0,0,0,.8)"); ctx.fillStyle = v; ctx.fillRect(0, 0, W, H);
};
// ---------------------------------------------------------------- 4) TRANSIÇÕES
// queimar: a cena velha (ou o talismã) queima de baixo para cima com borda incandescente e brasas, revelando a nova
KR.trans.queimar = function (A, B, k, t) {
  const { W, H } = D, w = 240, h = 135, f = krCampo(w, h, "fogo");
  ctx.drawImage(B, 0, 0);
  const m = _canvas("qM", w, h), gm = m.getContext("2d"), im = gm.createImageData(w, h);
  const bo = _canvas("qB", w, h), gb = bo.getContext("2d"), ib = gb.createImageData(w, h), lim = k * 1.35 - 0.1;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const i = y * w + x, v = f[i] * 0.55 + (1 - y / h) * 0.6;   // queima mais rápido embaixo
    const a = clamp((v - lim) / 0.03); im.data[i * 4 + 3] = a * 255;
    const e = Math.max(0, 1 - Math.abs(v - lim) / 0.045); ib.data[i * 4] = 255; ib.data[i * 4 + 1] = 120 + 100 * e; ib.data[i * 4 + 2] = 30; ib.data[i * 4 + 3] = e * 255;
  }
  gm.putImageData(im, 0, 0); gb.putImageData(ib, 0, 0);
  const o = _canvas("qA", W, H), go = o.getContext("2d"); go.globalCompositeOperation = "source-over"; go.clearRect(0, 0, W, H); go.drawImage(A, 0, 0);
  go.globalCompositeOperation = "destination-in"; go.drawImage(m, 0, 0, W, H); go.globalCompositeOperation = "source-over";
  // papel chamuscado: escurece perto da borda
  ctx.drawImage(o, 0, 0);
  ctx.save(); ctx.globalCompositeOperation = "lighter"; ctx.filter = "blur(6px)"; ctx.drawImage(bo, 0, 0, W, H); ctx.filter = "blur(1px)"; ctx.drawImage(bo, 0, 0, W, H); ctx.restore();
  KR.efeitos.brasas({ t0: 0 }, t, { n: Math.round(60 * Math.sin(Math.PI * k)) });
};
// rasgo: o papel da cena velha rasga numa linha irregular e as duas metades se afastam
KR.trans.rasgo = function (A, B, k, t) {
  const { W, H } = D, e = easeInOut(k), r = _semente("rasgo"), pts = [];
  for (let i = 0; i <= 24; i++) pts.push([W * (0.45 + (r() - 0.5) * 0.12) + (i / 24 - 0.5) * W * 0.18, (i / 24) * H]);
  ctx.drawImage(B, 0, 0);
  for (const lado of [-1, 1]) {
    ctx.save(); ctx.translate(lado * W * 0.55 * e, 0); ctx.rotate(lado * 0.04 * e);
    ctx.beginPath(); if (lado < 0) { ctx.moveTo(0, 0); pts.forEach(([x, y]) => ctx.lineTo(x, y)); ctx.lineTo(0, H); }
    else { ctx.moveTo(W, 0); pts.forEach(([x, y]) => ctx.lineTo(x, y)); ctx.lineTo(W, H); }
    ctx.closePath(); ctx.clip(); ctx.drawImage(A, 0, 0);
    ctx.strokeStyle = "rgba(240,232,214,.9)"; ctx.lineWidth = W * 0.004; ctx.beginPath(); pts.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y))); ctx.stroke();   // fibras brancas na borda rasgada
    ctx.restore();
  }
};
// hanji: a cena nova "molha" o papel — mancha de tinta que corre pelas fibras (borda fibrosa, não lisa)
KR.trans.hanji = function (A, B, k, t) {
  const { W, H } = D, w = 240, h = 135, f = krCampo(w, h, "fibra"), fib = krCampo(w, h, "fibra2");
  ctx.drawImage(A, 0, 0);
  const m = _canvas("hM", w, h), gm = m.getContext("2d"), im = gm.createImageData(w, h), lim = k * 1.2;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const i = y * w + x, d = Math.hypot(x / w - 0.5, (y / h - 0.5) * 0.7) * 1.6, v = d * 0.6 + f[i] * 0.3 + (fib[(y * 7 % h) * w + x] - 0.5) * 0.25;
    im.data[i * 4 + 3] = clamp((lim - v) / 0.02) * 255;
  }
  gm.putImageData(im, 0, 0);
  const o = _canvas("hB", W, H), go = o.getContext("2d"); go.globalCompositeOperation = "source-over"; go.clearRect(0, 0, W, H); go.drawImage(B, 0, 0);
  go.globalCompositeOperation = "destination-in"; go.drawImage(m, 0, 0, W, H); go.globalCompositeOperation = "source-over";
  ctx.drawImage(o, 0, 0);
};
window.KR = KR;
