// Motor do estilo "avatar + painel animado".
// Desenha o quadro do instante t (função pura de t) a partir da linha do tempo D gerada pelo gerar.py.
"use strict";
let cv = document.getElementById("tela");
let ctx = cv.getContext("2d");
let D = null;
const IMG = {};

// ------------------------------------------------------------------ utilidades
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lin = (t, t0, d) => clamp((t - t0) / d);
const easeOut = (x) => 1 - Math.pow(1 - clamp(x), 3);
const easeInOut = (x) => (x = clamp(x), x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
const back = (x) => { x = clamp(x); const c = 1.9; return 1 + (c + 1) * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); };
function rng(seed) { return () => { seed |= 0; seed = (seed + 0x6d2b79f5) | 0; let t = Math.imul(seed ^ (seed >>> 15), 1 | seed); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
function alpha(cor, a) { // "#rrggbb" -> rgba
  const n = parseInt(cor.slice(1), 16);
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
}
function rr(x, y, w, h, r) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); }
function digitado(texto, t, t0, cps) { // texto digitado letra a letra
  if (t < t0) return "";
  return texto.slice(0, Math.floor((t - t0) * cps) + 1);
}
function fonte(peso, tam, fam) { ctx.font = `${peso} ${tam}px "${fam}"`; }
function carregarImg(src) {
  return new Promise((ok) => { const i = new Image(); i.onload = () => ok(i); i.onerror = () => ok(null); i.src = src; });
}

// ------------------------------------------------------------------ preparação
window.preparar = async function (dados) {
  D = dados;
  cv.width = D.W; cv.height = D.H;
  const fams = [D.tema.fonte_titulo, D.tema.fonte_ui, D.tema.fonte_papel, D.tema.fonte_texto, "Cinzel", "Special Elite", "Anton", "Yuji Syuku", "Shippori Mincho", "Nanum Brush Script", "Nanum Myeongjo"];
  for (const f of fams) for (const p of ["400", "500", "700", "800"]) { try { await document.fonts.load(`${p} 40px "${f}"`); } catch (e) {} }
  const lista = [];
  for (const nome of Object.keys(D.avatar.poses)) lista.push(["pose:" + nome, D.avatar.base + nome + ".png"]);
  for (const p of D.paineis || []) if (p.imagem) lista.push(["img:" + p.imagem, p.imagem]);
  for (const c of D.cenas || []) for (const x of [...(c.mensagens || []), ...(c.lados || [])]) if (x.imagem) lista.push(["img:" + x.imagem, x.imagem]);
  for (const c of D.cenas || []) { if (c.imagem) lista.push(["img:" + c.imagem, c.imagem]); if (c.revelar && c.revelar.clara) lista.push(["img:" + c.revelar.clara, c.revelar.clara]); }
  for (const [k, src] of lista) IMG[k] = await carregarImg(src);
  D._estrelas = (() => { const r = rng(7); return Array.from({ length: 16 }, () => ({ x: r(), y: r(), f: 0.3 + r() * 0.8, fase: r() * 6.28, s: 0.6 + r() * 0.8 })); })();
  D._poeira = (() => { const r = rng(11); return Array.from({ length: 40 }, () => ({ x: r(), y: r(), v: 0.004 + r() * 0.01, s: 1 + r() * 2.5, fase: r() * 6.28 })); })();
  return true;
};

// ------------------------------------------------------------------ fundo
function fundo(t) {
  const { W, H } = D, T = D.tema;
  const g = ctx.createLinearGradient(0, 0, 0, H);
  g.addColorStop(0, T.fundo[0]); g.addColorStop(0.55, T.fundo[1]); g.addColorStop(1, T.fundo[0]);
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  // brilho central atrás do painel e névoa lenta
  const brilho = ctx.createRadialGradient(W * 0.5, H * 0.42, 50, W * 0.5, H * 0.42, W * 0.85);
  brilho.addColorStop(0, alpha(T.brilho, 0.22)); brilho.addColorStop(1, alpha(T.brilho, 0));
  ctx.fillStyle = brilho; ctx.fillRect(0, 0, W, H);
  for (let i = 0; i < 4; i++) {
    const x = W * (0.2 + 0.6 * ((i * 0.37 + t * 0.012 * (i % 2 ? 1 : -1)) % 1 + 1) % 1);
    const y = H * (0.25 + 0.18 * i);
    const n = ctx.createRadialGradient(x, y, 10, x, y, 420);
    n.addColorStop(0, alpha(T.nevoa, 0.06)); n.addColorStop(1, alpha(T.nevoa, 0));
    ctx.fillStyle = n; ctx.fillRect(0, 0, W, H);
  }
  // perfurações de filme nas laterais
  ctx.fillStyle = alpha(T.moldura, 0.10);
  const passo = 64, desl = (t * 6) % passo;
  for (let y = -passo + desl; y < H; y += passo) {
    rr(14, y, 26, 36, 5); ctx.fill();
    rr(W - 40, y, 26, 36, 5); ctx.fill();
  }
  ctx.fillStyle = alpha(T.moldura, 0.05); ctx.fillRect(52, 0, 3, H); ctx.fillRect(W - 55, 0, 3, H);
  // cantoneiras de visor
  ctx.strokeStyle = alpha(T.moldura, 0.35); ctx.lineWidth = 3;
  const m = 80, L = 46;
  for (const [x, y, sx, sy] of [[m, 230, 1, 1], [W - m, 230, -1, 1], [m, H - 330, 1, -1], [W - m, H - 330, -1, -1]]) {
    ctx.beginPath(); ctx.moveTo(x, y + sy * L); ctx.lineTo(x, y); ctx.lineTo(x + sx * L, y); ctx.stroke();
  }
  // poeira flutuando
  for (const p of D._poeira) {
    const y = ((p.y - t * p.v) % 1 + 1) % 1 * H, x = p.x * W + Math.sin(t * 0.6 + p.fase) * 12;
    ctx.fillStyle = alpha(T.particulas, 0.18 + 0.15 * Math.sin(t * 1.3 + p.fase));
    ctx.beginPath(); ctx.arc(x, y, p.s, 0, 6.29); ctx.fill();
  }
  // cruzes cintilando
  for (const e of D._estrelas) {
    const a = Math.pow(Math.max(0, Math.sin(t * e.f * 2 + e.fase)), 3);
    if (a < 0.02) continue;
    const x = 90 + e.x * (W - 180), y = 260 + e.y * (H - 650), s = 9 * e.s;
    ctx.strokeStyle = alpha(T.particulas, 0.75 * a); ctx.lineWidth = 2.5;
    ctx.beginPath(); ctx.moveTo(x - s, y); ctx.lineTo(x + s, y); ctx.moveTo(x, y - s); ctx.lineTo(x, y + s); ctx.stroke();
  }
  // assinatura
  if (D.assinatura) {
    fonte(700, 26, T.fonte_ui); ctx.textAlign = "right"; ctx.fillStyle = alpha(T.texto, 0.45);
    ctx.fillText(D.assinatura, W - 90, 200); ctx.textAlign = "left";
  }
}

// ------------------------------------------------------------------ título cinético
function titulo(t) {
  const T = D.tema;
  let atual = null;
  for (const ti of D.titulos) if (ti.t <= t) atual = ti;
  if (!atual) return;
  const [l1, l2] = atual.linhas;
  const cps = 26, x = 80, y1 = 330, tam = 118;
  const n1 = l1 ? l1.length : 0;
  const s1 = digitado(l1 || "", t, atual.t, cps);
  const t2 = atual.t + n1 / cps;
  const s2 = digitado(l2 || "", t, t2, cps);
  fonte(400, tam, T.fonte_titulo); ctx.textBaseline = "alphabetic";
  if (s1) {
    ctx.fillStyle = T.texto; ctx.shadowColor = "rgba(0,0,0,.6)"; ctx.shadowBlur = 18;
    ctx.fillText(s1, x, y1); ctx.shadowBlur = 0;
  }
  if (l2 && t >= t2) {
    const w = ctx.measureText(s2).width, pad = 22, y2 = y1 + tam + 16;
    const pop = back(lin(t, t2, 0.18));
    ctx.save(); ctx.translate(x, y2 - tam * 0.42); ctx.scale(1, pop); ctx.translate(-x, -(y2 - tam * 0.42));
    ctx.fillStyle = T.acento; ctx.shadowColor = alpha(T.acento, 0.45); ctx.shadowBlur = 30;
    rr(x - pad * 0.6, y2 - tam * 0.93, w + pad * 1.6, tam * 1.08, 10); ctx.fill(); ctx.shadowBlur = 0;
    ctx.strokeStyle = alpha("#000000", 0.35); ctx.lineWidth = 3; ctx.stroke();
    ctx.fillStyle = T.acento_texto; ctx.fillText(s2, x + pad * 0.2, y2 - 4);
    ctx.restore();
  }
}

// ------------------------------------------------------------------ ícones (traço simples)
function icone(nome, x, y, s, cor) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s / 100, s / 100);
  ctx.strokeStyle = cor; ctx.fillStyle = cor; ctx.lineWidth = 8; ctx.lineCap = "round"; ctx.lineJoin = "round";
  const P = () => ctx.beginPath();
  switch (nome) {
    case "olho": P(); ctx.moveTo(-42, 0); ctx.quadraticCurveTo(0, -40, 42, 0); ctx.quadraticCurveTo(0, 40, -42, 0); ctx.stroke(); P(); ctx.arc(0, 0, 13, 0, 6.29); ctx.fill(); break;
    case "lua": P(); ctx.arc(0, 0, 36, 0.6, 5.7); ctx.arc(14, -6, 28, 5.2, 1.1, true); ctx.closePath(); ctx.fill(); break;
    case "vela": ctx.strokeRect(-14, -8, 28, 50); P(); ctx.moveTo(0, -14); ctx.quadraticCurveTo(-12, -30, 0, -46); ctx.quadraticCurveTo(12, -30, 0, -14); ctx.fill(); break;
    case "chave": P(); ctx.arc(-22, 0, 16, 0, 6.29); ctx.stroke(); P(); ctx.moveTo(-6, 0); ctx.lineTo(40, 0); ctx.moveTo(26, 0); ctx.lineTo(26, 14); ctx.moveTo(38, 0); ctx.lineTo(38, 12); ctx.stroke(); break;
    case "porta": ctx.strokeRect(-24, -40, 48, 80); P(); ctx.arc(12, 4, 4, 0, 6.29); ctx.fill(); break;
    case "relogio": P(); ctx.arc(0, 0, 36, 0, 6.29); ctx.stroke(); P(); ctx.moveTo(0, 0); ctx.lineTo(0, -22); ctx.moveTo(0, 0); ctx.lineTo(16, 8); ctx.stroke(); break;
    case "alerta": P(); ctx.moveTo(0, -38); ctx.lineTo(40, 34); ctx.lineTo(-40, 34); ctx.closePath(); ctx.stroke(); P(); ctx.moveTo(0, -10); ctx.lineTo(0, 10); ctx.stroke(); P(); ctx.arc(0, 22, 4, 0, 6.29); ctx.fill(); break;
    case "casa": P(); ctx.moveTo(-36, -2); ctx.lineTo(0, -34); ctx.lineTo(36, -2); ctx.moveTo(-26, -8); ctx.lineTo(-26, 34); ctx.lineTo(26, 34); ctx.lineTo(26, -8); ctx.stroke(); break;
    case "livro": P(); ctx.moveTo(0, -26); ctx.lineTo(0, 30); ctx.moveTo(0, -26); ctx.quadraticCurveTo(-20, -36, -40, -28); ctx.lineTo(-40, 28); ctx.quadraticCurveTo(-20, 20, 0, 30); ctx.quadraticCurveTo(20, 20, 40, 28); ctx.lineTo(40, -28); ctx.quadraticCurveTo(20, -36, 0, -26); ctx.stroke(); break;
    case "farol": P(); ctx.moveTo(-16, 40); ctx.lineTo(-10, -18); ctx.lineTo(10, -18); ctx.lineTo(16, 40); ctx.closePath(); ctx.stroke(); ctx.strokeRect(-12, -36, 24, 18); P(); ctx.moveTo(14, -27); ctx.lineTo(44, -40); ctx.moveTo(-14, -27); ctx.lineTo(-44, -40); ctx.stroke(); break;
    case "barco": P(); ctx.moveTo(-40, 10); ctx.lineTo(40, 10); ctx.lineTo(26, 32); ctx.lineTo(-26, 32); ctx.closePath(); ctx.stroke(); P(); ctx.moveTo(0, 10); ctx.lineTo(0, -38); ctx.lineTo(28, 0); ctx.lineTo(0, 0); ctx.stroke(); break;
    case "pessoa": P(); ctx.arc(0, -18, 16, 0, 6.29); ctx.stroke(); P(); ctx.moveTo(-30, 38); ctx.quadraticCurveTo(-30, 6, 0, 6); ctx.quadraticCurveTo(30, 6, 30, 38); ctx.stroke(); break;
    case "camera": rr(-38, -22, 76, 52, 8); ctx.stroke(); P(); ctx.arc(0, 4, 15, 0, 6.29); ctx.stroke(); ctx.strokeRect(-14, -32, 26, 10); break;
    case "capa": P(); ctx.moveTo(-14, -34); ctx.lineTo(14, -34); ctx.lineTo(34, -14); ctx.lineTo(28, 38); ctx.lineTo(-28, 38); ctx.lineTo(-34, -14); ctx.closePath(); ctx.stroke(); P(); ctx.moveTo(0, -34); ctx.lineTo(0, 38); ctx.stroke(); break;
    case "caveira": P(); ctx.arc(0, -6, 32, Math.PI * 0.85, Math.PI * 2.15); ctx.lineTo(18, 34); ctx.lineTo(-18, 34); ctx.closePath(); ctx.stroke(); P(); ctx.arc(-12, -4, 8, 0, 6.29); ctx.arc(12, -4, 8, 0, 6.29); ctx.fill(); break;
    case "ondas": for (let k = -1; k <= 1; k++) { P(); ctx.moveTo(-40, k * 20); for (let i = -40; i <= 40; i += 20) ctx.quadraticCurveTo(i + 5, k * 20 - 12, i + 10, k * 20), ctx.quadraticCurveTo(i + 15, k * 20 + 12, i + 20, k * 20); ctx.stroke(); } break;
    case "interrogacao": default: fonte(400, 90, D.tema.fonte_titulo); ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText(nome === "interrogacao" || !nome ? "?" : nome[0].toUpperCase(), 0, 4); ctx.textAlign = "left"; ctx.textBaseline = "alphabetic";
  }
  ctx.restore();
}

function risco(x, y, s, p, cor) { // risco diagonal animado sobre um ícone
  if (p <= 0) return;
  ctx.save(); ctx.strokeStyle = cor; ctx.lineWidth = 9; ctx.lineCap = "round";
  ctx.shadowColor = "rgba(0,0,0,.6)"; ctx.shadowBlur = 6;
  ctx.beginPath(); ctx.moveTo(x - s * 0.5, y + s * 0.5); ctx.lineTo(x - s * 0.5 + s * p, y + s * 0.5 - s * p); ctx.stroke(); ctx.restore();
}

// ------------------------------------------------------------------ painéis
const BOX = { x: 110, y: 560, w: 860, h: 660 };

function moldura(p, t, claro) {
  const T = D.tema, { x, y, w, h } = BOX;
  if (!claro) {
    ctx.fillStyle = alpha(T.painel, 0.82); rr(x, y, w, h, 18); ctx.fill();
  }
  ctx.strokeStyle = alpha(T.moldura, 0.85); ctx.lineWidth = 3; rr(x, y, w, h, 18); ctx.stroke();
  ctx.strokeStyle = alpha(T.moldura, 0.25); ctx.lineWidth = 1.5; rr(x + 10, y + 10, w - 20, h - 20, 12); ctx.stroke();
  if (p.etiqueta) {
    fonte(800, 24, T.fonte_ui); const tw = ctx.measureText(p.etiqueta).width;
    ctx.fillStyle = T.acento; rr(x + 28, y - 18, tw + 30, 38, 6); ctx.fill();
    ctx.fillStyle = T.acento_texto; ctx.fillText(p.etiqueta, x + 43, y + 9);
  }
}

const PAINEIS = {
  lista(p, t) {
    const T = D.tema, { x, y, w } = BOX;
    moldura(p, t);
    const lh = 128, top = y + 60;
    p.itens.forEach((it, i) => {
      if (t < it.t) {
        ctx.strokeStyle = alpha(T.moldura, 0.18); ctx.lineWidth = 2; rr(x + 40, top + i * (lh + 18), w - 80, lh, 12); ctx.stroke();
        return;
      }
      const e = easeOut(lin(t, it.t, 0.25)), yy = top + i * (lh + 18) + (1 - e) * 24;
      ctx.globalAlpha = e;
      ctx.fillStyle = alpha(T.painel_item, 0.95); rr(x + 40, yy, w - 80, lh, 12); ctx.fill();
      ctx.strokeStyle = alpha(T.moldura, 0.6); ctx.lineWidth = 2; ctx.stroke();
      icone(it.icone, x + 115, yy + lh / 2, 64, T.texto);
      if (it.risco_t != null) risco(x + 115, yy + lh / 2, 76, easeOut(lin(t, it.risco_t, 0.22)), T.perigo);
      fonte(700, 56, T.fonte_ui); ctx.fillStyle = T.texto;
      const s = digitado(it.texto, t, it.t + 0.05, 30);
      ctx.fillText(s, x + 185, yy + lh / 2 + 20);
      const tw = ctx.measureText(it.texto).width;
      ctx.fillStyle = T.acento; ctx.fillRect(x + 187, yy + lh / 2 + 36, tw * 0.45 * easeOut(lin(t, it.t + 0.2, 0.5)), 6);
      ctx.globalAlpha = 1;
    });
  },

  checklist(p, t) { // papel com linhas e caixinhas
    const T = D.tema, { x, y, w, h } = BOX;
    ctx.fillStyle = T.papel; rr(x, y, w, h, 14); ctx.fill();
    ctx.strokeStyle = alpha(T.papel_texto, 0.10); ctx.lineWidth = 2;
    for (let yy = y + 120; yy < y + h - 20; yy += 64) { ctx.beginPath(); ctx.moveTo(x + 30, yy); ctx.lineTo(x + w - 30, yy); ctx.stroke(); }
    moldura(p, t, true);
    fonte(700, 46, T.fonte_papel); ctx.fillStyle = T.papel_texto;
    ctx.fillText(digitado(p.cabecalho || "", t, p.t0 + 0.2, 30), x + 50, y + 92);
    p.itens.forEach((it, i) => {
      if (t < it.t) return;
      const yy = y + 190 + i * 118, e = easeOut(lin(t, it.t, 0.2));
      ctx.globalAlpha = e;
      ctx.strokeStyle = T.papel_texto; ctx.lineWidth = 4; ctx.strokeRect(x + 50, yy - 38, 46, 46);
      fonte(700, 50, T.fonte_papel); ctx.fillStyle = T.papel_texto;
      ctx.fillText(digitado(it.texto, t, it.t + 0.05, 30), x + 120, yy);
      if (it.icone) icone(it.icone, x + w - 90, yy - 16, 50, T.papel_texto);
      ctx.fillStyle = alpha(T.papel_texto, 0.15); ctx.fillRect(x + 120, yy + 22, 420, 8);
      ctx.fillStyle = T.perigo; ctx.fillRect(x + 120, yy + 22, 420 * (it.barra ?? 0.25) * easeOut(lin(t, it.t + 0.2, 0.6)), 8);
      if (it.marca_t != null && t >= it.marca_t) {
        const m = easeOut(lin(t, it.marca_t, 0.18));
        ctx.strokeStyle = it.marca === "ok" ? T.ok : T.perigo; ctx.lineWidth = 9; ctx.lineCap = "round";
        ctx.beginPath();
        if (it.marca === "ok") { ctx.moveTo(x + 56, yy - 16); ctx.lineTo(x + 56 + 16 * m, yy - 16 + 16 * m); if (m > 0.5) ctx.lineTo(x + 72 + 30 * (m - 0.5) * 2, yy - 0 - 40 * (m - 0.5) * 2); }
        else { ctx.moveTo(x + 52, yy - 40); ctx.lineTo(x + 52 + 44 * m, yy - 40 + 44 * m); ctx.moveTo(x + 96, yy - 40); ctx.lineTo(x + 96 - 44 * m, yy - 40 + 44 * m); }
        ctx.stroke();
        if (it.risca_texto) { fonte(700, 50, T.fonte_papel); const tw = ctx.measureText(it.texto).width; ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(x + 116, yy - 16); ctx.lineTo(x + 116 + (tw + 8) * m, yy - 16); ctx.stroke(); }
      }
      ctx.globalAlpha = 1;
    });
  },

  ficha(p, t) { // dossiê com campos e carimbo
    const T = D.tema, { x, y, w, h } = BOX;
    ctx.fillStyle = T.papel; rr(x, y, w, h, 14); ctx.fill();
    // textura de papel envelhecido
    const g = ctx.createRadialGradient(x + w / 2, y + h / 2, 100, x + w / 2, y + h / 2, w * 0.75);
    g.addColorStop(0, "rgba(0,0,0,0)"); g.addColorStop(1, "rgba(60,40,10,.35)"); ctx.fillStyle = g; rr(x, y, w, h, 14); ctx.fill();
    moldura(p, t, true);
    fonte(400, 40, T.fonte_papel); ctx.fillStyle = alpha(T.papel_texto, 0.75);
    ctx.fillText(digitado(p.cabecalho || "", t, p.t0 + 0.15, 32), x + 50, y + 90);
    ctx.fillStyle = alpha(T.papel_texto, 0.35); ctx.fillRect(x + 50, y + 108, w - 100, 3);
    let fotoW = 0;
    if (p.imagem && IMG["img:" + p.imagem]) {
      fotoW = 260;
      const fx = x + w - 50 - fotoW, fy = y + 140, im = IMG["img:" + p.imagem];
      const e = easeOut(lin(t, p.t0 + 0.3, 0.3));
      ctx.save(); ctx.globalAlpha = e; ctx.translate(fx + fotoW / 2, fy + 170); ctx.rotate(0.035);
      ctx.fillStyle = "#f2efe6"; ctx.fillRect(-fotoW / 2 - 12, -170 - 12, fotoW + 24, 340 + 50);
      cobrir(im, -fotoW / 2, -170, fotoW, 340, 1 + 0.06 * lin(t, p.t0, 8));
      ctx.restore(); ctx.globalAlpha = 1;
    }
    p.campos.forEach((c, i) => {
      if (t < c.t) return;
      const yy = y + 190 + i * 104;
      fonte(400, 30, T.fonte_papel); ctx.fillStyle = alpha(T.papel_texto, 0.6);
      ctx.fillText(c.rotulo.toUpperCase(), x + 50, yy - 34);
      fonte(700, 50, T.fonte_papel); ctx.fillStyle = T.papel_texto;
      ctx.fillText(digitado(c.valor, t, c.t, 28), x + 50, yy + 14);
    });
    if (p.carimbo && t >= p.carimbo.t) {
      const e = lin(t, p.carimbo.t, 0.16), s = 1 + 0.9 * (1 - easeOut(e));
      ctx.save(); ctx.translate(x + w * 0.5, y + h - 120); ctx.rotate(-0.13); ctx.scale(s, s); ctx.globalAlpha = Math.min(1, e * 2) * 0.88;
      fonte(400, 78, T.fonte_titulo); const tw = ctx.measureText(p.carimbo.texto).width;
      ctx.strokeStyle = T.perigo; ctx.lineWidth = 8; rr(-tw / 2 - 28, -62, tw + 56, 96, 10); ctx.stroke();
      ctx.fillStyle = T.perigo; ctx.textAlign = "center"; ctx.fillText(p.carimbo.texto, 0, 14); ctx.textAlign = "left";
      ctx.restore();
    }
  },

  contador(p, t) {
    const T = D.tema, { x, y, w, h } = BOX;
    moldura(p, t);
    fonte(700, 46, T.fonte_ui); ctx.fillStyle = alpha(T.texto, 0.8); ctx.textAlign = "center";
    ctx.fillText(digitado(p.rotulo || "", t, p.t0 + 0.1, 30), x + w / 2, y + 150);
    const e = easeInOut(lin(t, p.t_contagem ?? p.t0 + 0.3, p.duracao_contagem ?? 1.6));
    const v = Math.round(p.de + (p.ate - p.de) * e);
    fonte(400, 230, T.fonte_titulo); ctx.fillStyle = T.acento;
    ctx.shadowColor = alpha(T.acento, 0.5); ctx.shadowBlur = 40;
    ctx.fillText((p.prefixo || "") + v.toLocaleString("pt-BR", { useGrouping: !!p.milhar }) + (p.sufixo || ""), x + w / 2, y + 420); ctx.shadowBlur = 0;
    if (p.nota) { fonte(500, 40, T.fonte_ui); ctx.fillStyle = alpha(T.texto, 0.7); ctx.fillText(digitado(p.nota, t, p.t_nota ?? p.t0 + 1.8, 30), x + w / 2, y + 540); }
    ctx.textAlign = "left";
  },

  chat(p, t) {
    const T = D.tema, { x, y, w } = BOX;
    moldura(p, t);
    let yy = y + 70;
    for (const m of p.mensagens) {
      if (t < m.t) break;
      const eu = m.de === "eu";
      fonte(700, 42, T.fonte_ui);
      const pensando = !eu && t < m.t + 0.7;
      const txt = pensando ? "" : digitado(m.texto, t, eu ? m.t : m.t + 0.7, 40);
      const tw = Math.min(w - 200, Math.max(120, ctx.measureText(m.texto).width + 60));
      const bx = eu ? x + w - 50 - tw : x + 50;
      ctx.fillStyle = eu ? T.acento : alpha(T.painel_item, 1);
      rr(bx, yy, tw, 90, 22); ctx.fill();
      if (pensando) {
        for (let k = 0; k < 3; k++) { ctx.fillStyle = alpha(T.texto, 0.4 + 0.6 * Math.max(0, Math.sin(t * 9 - k))); ctx.beginPath(); ctx.arc(bx + 45 + k * 30, yy + 45, 9, 0, 6.29); ctx.fill(); }
      } else { ctx.fillStyle = eu ? T.acento_texto : T.texto; ctx.fillText(txt, bx + 30, yy + 60); }
      yy += 120;
    }
  },

  impacto(p, t) { // tela preta com frase de efeito
    const T = D.tema, { x, y, w, h } = BOX;
    ctx.fillStyle = "#050607"; rr(x, y, w, h, 18); ctx.fill();
    ctx.save(); rr(x, y, w, h, 18); ctx.clip();
    const r = rng(3);
    for (let i = 0; i < 70; i++) {
      const sx = x + r() * w, sy = y + ((r() * h + t * 12 * (0.3 + r())) % h), a = 0.3 + 0.7 * Math.abs(Math.sin(t * 2 + i));
      ctx.fillStyle = alpha(T.particulas, a * easeOut(lin(t, p.t0, 0.6))); ctx.fillRect(sx, sy, 3, 3);
    }
    ctx.restore();
    ctx.strokeStyle = alpha(T.moldura, 0.5); ctx.lineWidth = 3; rr(x, y, w, h, 18); ctx.stroke();
    ctx.textAlign = "center";
    if (p.pequeno) { fonte(500, 40, T.fonte_ui); ctx.fillStyle = alpha(T.texto, 0.85); ctx.fillText(digitado(p.pequeno, t, p.t0 + 0.1, 30), x + w / 2, y + 120); }
    if (p.grande && t >= p.t_grande) {
      const e = lin(t, p.t_grande, 0.2), s = 1 + 0.35 * (1 - easeOut(e));
      const linhas = p.grande.split("\n");
      ctx.save(); ctx.translate(x + w / 2, y + h / 2 + 40); ctx.scale(s, s); ctx.globalAlpha = clamp(e * 2);
      fonte(400, 130, T.fonte_titulo); ctx.fillStyle = T.acento; ctx.shadowColor = alpha(T.acento, 0.6); ctx.shadowBlur = 40;
      linhas.forEach((l, i) => ctx.fillText(l, 0, (i - (linhas.length - 1) / 2) * 140));
      ctx.shadowBlur = 0; ctx.restore();
      const u = easeOut(lin(t, p.t_grande + 0.2, 0.4)); ctx.fillStyle = T.acento;
      ctx.fillRect(x + w / 2 - 260 * u, y + h / 2 + 40 + linhas.length * 70 + 10, 520 * u, 7);
    }
    ctx.textAlign = "left";
  },

  imagem(p, t) { // cena ilustrada dentro do painel, com movimento de câmera lento
    const T = D.tema, { x, y, w, h } = BOX, im = IMG["img:" + p.imagem];
    ctx.save(); rr(x, y, w, h, 18); ctx.clip();
    if (im) cobrir(im, x, y, w, h, 1.0 + 0.1 * easeInOut(lin(t, p.t0, p.t1 - p.t0)), p.foco);
    const g = ctx.createLinearGradient(0, y + h * 0.55, 0, y + h); g.addColorStop(0, "rgba(0,0,0,0)"); g.addColorStop(1, "rgba(0,0,0,.85)");
    ctx.fillStyle = g; ctx.fillRect(x, y, w, h); ctx.restore();
    moldura(p, t, true);
    if (p.legenda) { fonte(700, 46, T.fonte_ui); ctx.fillStyle = T.texto; ctx.fillText(digitado(p.legenda, t, p.t_legenda ?? p.t0 + 0.4, 30), x + 46, y + h - 50); }
  },
};

function cobrir(im, x, y, w, h, zoom = 1, foco = [0.5, 0.5]) {
  const s = Math.max(w / im.width, h / im.height) * zoom, iw = im.width * s, ih = im.height * s;
  const ox = x + (w - iw) * foco[0], oy = y + (h - ih) * foco[1];
  ctx.drawImage(im, ox, oy, iw, ih);
}

function paineis(t) {
  for (const p of D.paineis) {
    if (t < p.t0 || t > p.t1 + 0.2) continue;
    const ent = easeOut(lin(t, p.t0, 0.28)), sai = 1 - lin(t, p.t1, 0.18);
    ctx.save();
    ctx.globalAlpha = Math.min(ent, sai);
    const s = 0.94 + 0.06 * ent, cx = BOX.x + BOX.w / 2, cy = BOX.y + BOX.h / 2;
    ctx.translate(cx, cy + (1 - ent) * 30); ctx.scale(s, s); ctx.translate(-cx, -cy);
    (PAINEIS[p.tipo] || PAINEIS.lista)(p, t);
    ctx.restore();
  }
}

// ------------------------------------------------------------------ avatar
const AV = { cx: 540, topo: 1300, w: 420, h: 440 };

function arco(x, y, w, h) { // janela gótica
  ctx.beginPath(); ctx.moveTo(x, y + h); ctx.lineTo(x, y + w * 0.42);
  ctx.quadraticCurveTo(x, y, x + w / 2, y - w * 0.08); ctx.quadraticCurveTo(x + w, y, x + w, y + w * 0.42);
  ctx.lineTo(x + w, y + h); ctx.closePath();
}

function desenharPose(nome, a, t) {
  const im = IMG["pose:" + nome], m = D.avatar.poses[nome];
  if (!im || !m) return;
  const alvo = 255, s = alvo / clamp(m.largura_cabeca, D.avatar.mediana * 0.85, D.avatar.mediana * 1.2);
  const resp = 1 + 0.008 * Math.sin(t * 2 * Math.PI / 3.4);
  const S = s * resp;
  const x = AV.cx - m.centro_x * S, y = AV.topo + 10 - m.topo * S + Math.sin(t * 1.7) * 3;
  ctx.globalAlpha = a; ctx.drawImage(im, x, y, im.width * S, im.height * S); ctx.globalAlpha = 1;
}

function avatar(t) {
  const T = D.tema, x = AV.cx - AV.w / 2, y = AV.topo, { w, h } = AV;
  // halo
  const g = ctx.createRadialGradient(AV.cx, y + h * 0.45, 40, AV.cx, y + h * 0.45, w * 0.95);
  g.addColorStop(0, alpha(T.halo, 0.45)); g.addColorStop(1, alpha(T.halo, 0));
  ctx.fillStyle = g; ctx.fillRect(x - w, y - h * 0.4, w * 3, h * 1.8);
  // interior da janela
  ctx.save(); arco(x, y, w, h); ctx.fillStyle = alpha(T.painel, 0.9); ctx.fill(); ctx.clip();
  const gi = ctx.createRadialGradient(AV.cx, y + h * 0.4, 20, AV.cx, y + h * 0.4, w * 0.7);
  gi.addColorStop(0, alpha(T.halo, 0.35)); gi.addColorStop(1, alpha(T.halo, 0)); ctx.fillStyle = gi; ctx.fillRect(x, y - 60, w, h + 60);
  // pose atual (com fusão curta na troca)
  let i = -1; D.poses.forEach((p, k) => { if (p.t <= t) i = k; });
  if (i >= 0) {
    const atual = D.poses[i], ant = D.poses[i - 1], f = easeOut(lin(t, atual.t, 0.14));
    if (ant && f < 1) desenharPose(ant.pose, 1 - f, t);
    ctx.save();
    const pop = 1 + 0.035 * (1 - f); ctx.translate(AV.cx, y + h); ctx.scale(pop, pop); ctx.translate(-AV.cx, -(y + h));
    desenharPose(atual.pose, f, t); ctx.restore();
  }
  // esfuma a base (esconde cortes retos dos recortes)
  const gb = ctx.createLinearGradient(0, y + h - 110, 0, y + h); gb.addColorStop(0, alpha(T.painel, 0)); gb.addColorStop(1, alpha(T.painel, 1));
  ctx.fillStyle = gb; ctx.fillRect(x, y + h - 110, w, 110);
  ctx.restore();
  // moldura dourada
  ctx.strokeStyle = T.moldura; ctx.lineWidth = 5; arco(x, y, w, h); ctx.stroke();
  ctx.strokeStyle = alpha(T.moldura, 0.35); ctx.lineWidth = 2; arco(x - 12, y - 6, w + 24, h + 6); ctx.stroke();
  icone("lua", AV.cx, y - 62, 38, T.moldura);
  // barra de tensão
  if (D.barra) {
    const bx = x + w + 40, by = y + h - 40, seg = 8, n = Math.ceil(seg * clamp(t / D.duracao) + 0.001);
    fonte(800, 26, T.fonte_ui); ctx.fillStyle = alpha(T.texto, 0.8); ctx.fillText(D.barra, bx, by - 16);
    for (let k = 0; k < seg; k++) {
      ctx.fillStyle = k < n ? alpha(T.perigo, k === n - 1 ? 0.6 + 0.4 * Math.sin(t * 8) : 0.95) : alpha(T.texto, 0.15);
      ctx.fillRect(bx + k * 22, by, 16, 22);
    }
  }
}

// ================================================================== modo CENAS (imagens em tela cheia)
let GRAO = null, MASCARA = null;
function prepararCenas() {
  // textura de granulação (reaproveitada com deslocamento aleatório a cada quadro)
  GRAO = document.createElement("canvas"); GRAO.width = 512; GRAO.height = 512;
  const g = GRAO.getContext("2d"), im = g.createImageData(512, 512), r = rng(5);
  for (let i = 0; i < im.data.length; i += 4) { const v = 128 + (r() - 0.5) * 255; im.data[i] = im.data[i + 1] = im.data[i + 2] = v; im.data[i + 3] = 255; }
  g.putImageData(im, 0, 0);
  MASCARA = document.createElement("canvas");
  D._chuva = (() => { const r = rng(21); return Array.from({ length: 140 }, () => ({ x: r(), y: r(), v: 0.9 + r() * 0.8, l: 30 + r() * 70, a: 0.05 + r() * 0.12 })); })();
}

function cenaAtual(t) {
  let i = -1; D.cenas.forEach((c, k) => { if (c.t0 <= t) i = k; });
  return i;
}

// relógio digital desenhado (7 segmentos), ex.: "03:12"
function relogioDigital(c, t, a) {
  const { W, H } = D, txt = c.hora || "03:12";
  const z = 1 + 0.06 * easeInOut(lin(t, c.t0, Math.max(1, c.t1 - c.t0)));
  ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = "#020303"; ctx.fillRect(0, 0, W, H);
  ctx.translate(W / 2, H / 2); ctx.scale(z, z);
  const dh = Math.min(W, H) * 0.26, dw = dh * 0.52, esp = dw * 0.32, lw = dh * 0.11;
  const cor = c.cor || "#ff2a1f", pisca = (Math.floor((t - c.t0) * 1) % 2 === 0) ? 1 : 0.25;
  const SEG = { "0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd", "6": "afgedc", "7": "abc", "8": "abcdefg", "9": "abfgcd" };
  let total = 0; for (const ch of txt) total += ch === ":" ? esp * 1.2 : dw + esp; total -= esp;
  let x = -total / 2;
  const seg = (x0, y0, x1, y1) => { ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke(); };
  ctx.lineCap = "round"; ctx.lineWidth = lw; ctx.shadowColor = cor; ctx.shadowBlur = lw * 2.2;
  for (const ch of txt) {
    if (ch === ":") {
      ctx.fillStyle = alpha(cor, pisca); ctx.beginPath(); ctx.arc(x + esp * 0.6, -dh * 0.2, lw * 0.55, 0, 6.29); ctx.arc(x + esp * 0.6, dh * 0.2, lw * 0.55, 0, 6.29); ctx.fill();
      x += esp * 1.2; continue;
    }
    const on = SEG[ch] || "";
    const L = x, R = x + dw, T0 = -dh / 2, M = 0, B = dh / 2, g = lw * 0.6;
    const P = { a: [L + g, T0, R - g, T0], b: [R, T0 + g, R, M - g], c: [R, M + g, R, B - g], d: [L + g, B, R - g, B], e: [L, M + g, L, B - g], f: [L, T0 + g, L, M - g], g: [L + g, M, R - g, M] };
    for (const k of "abcdefg") { ctx.strokeStyle = on.includes(k) ? cor : "rgba(255,40,30,0.06)"; seg(...P[k]); }
    x += dw + esp;
  }
  ctx.restore();
  // reflexo na mesa
  const r = ctx.createLinearGradient(0, H * 0.72, 0, H); r.addColorStop(0, alpha(c.cor || "#ff2a1f", 0.06 * a)); r.addColorStop(1, "rgba(0,0,0,0)");
  ctx.fillStyle = r; ctx.fillRect(0, H * 0.72, W, H * 0.28);
}

// interface de câmera de segurança (REC, CAM, horário correndo, linhas)
function interfaceCCTV(c, t) {
  const { W, H } = D, k = c.cctv, u = Math.min(W, H) / 1080;
  ctx.save();
  ctx.globalAlpha = 0.10; ctx.fillStyle = "#000";
  for (let y = (t * 40) % 4; y < H; y += 4) ctx.fillRect(0, y, W, 1.5);
  ctx.globalAlpha = 1;
  const seg0 = (k.inicio || "02:48:00").split(":").map(Number), base = seg0[0] * 3600 + seg0[1] * 60 + (seg0[2] || 0);
  const s = Math.floor(base + (t - c.t0) * (k.velocidade || 1)), hh = String(Math.floor(s / 3600) % 24).padStart(2, "0"),
    mm = String(Math.floor(s / 60) % 60).padStart(2, "0"), ss = String(s % 60).padStart(2, "0");
  ctx.font = `700 ${Math.round(40 * u)}px "DejaVu Sans Mono", monospace`; ctx.fillStyle = "rgba(235,245,235,.9)";
  ctx.shadowColor = "rgba(0,0,0,.9)"; ctx.shadowBlur = 6;
  // tudo no topo: a base da tela fica livre para o Vigia e a legenda
  ctx.textAlign = "right"; ctx.fillText(`${k.data || "14/03"}  ${hh}:${mm}:${ss}`, W - 70 * u, 92 * u);
  if (k.velocidade && k.velocidade > 1.5) ctx.fillText(`▶▶ x${k.velocidade}`, W - 70 * u, 142 * u);
  ctx.textAlign = "left";
  if (Math.floor(t * 1.4) % 2 === 0) { ctx.fillStyle = "#ff2b2b"; ctx.beginPath(); ctx.arc(84 * u, 78 * u, 14 * u, 0, 6.29); ctx.fill(); }
  ctx.fillStyle = "rgba(235,245,235,.9)"; ctx.fillText("REC", 110 * u, 92 * u);
  ctx.fillText(k.cam || "CAM 01", 70 * u, 142 * u);
  // cantos de visor
  ctx.strokeStyle = "rgba(235,245,235,.55)"; ctx.lineWidth = 3 * u; const m = 40 * u, L = 70 * u;
  for (const [x, y, sx, sy] of [[m, m, 1, 1], [W - m, m, -1, 1], [m, H - m, 1, -1], [W - m, H - m, -1, -1]]) { ctx.beginPath(); ctx.moveTo(x, y + sy * L); ctx.lineTo(x, y); ctx.lineTo(x + sx * L, y); ctx.stroke(); }
  ctx.restore();
}

// tela preta com texto digitado; a última palavra (ou "vermelho") em vermelho
function telaTexto(c, t, a) {
  const { W, H } = D, T = D.tema;
  ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = "#030303"; ctx.fillRect(0, 0, W, H);
  // estilos: "maquina" (máquina de escrever) e "impacto" (serifada grande, com brilho)
  const est = c.estilo === "impacto" ? { fonte: "Cinzel", peso: 700, tam: 118 } : c.estilo === "maquina" ? { fonte: "Special Elite", peso: 400, tam: Math.round(Math.min(D.W, D.H) * 0.07) } : {};
  const tam = c.tamanho || est.tam || Math.round(Math.min(W, H) * 0.055);
  const fam0 = c.fonte || est.fonte || T.fonte_texto;
  const peso0 = c.peso || est.peso || 500;
  ctx.font = `${peso0} ${tam}px "${fam0}"`;
  const linhas = [];
  for (const par of (c.texto || "").split("\n")) {   // quebra para caber em 78% da largura
    let atual = "";
    for (const p of par.split(" ")) {
      const tent = atual ? atual + " " + p : p;
      if (ctx.measureText(tent).width > W * 0.78 && atual) { linhas.push(atual); atual = p; } else atual = tent;
    }
    linhas.push(atual);
  }
  const cps = c.cps || 22, dt = Math.max(0, t - c.t0 - 0.25);
  let mostrados = Math.floor(dt * cps);
  ctx.textAlign = "left"; ctx.textBaseline = "middle";
  const fam = fam0;
  if (c.estilo === "impacto") {   // leve aproximação + tremor sutil para dar peso
    const k = easeOut(lin(t, c.t0, 0.9)); ctx.translate(W / 2, H / 2); ctx.scale(1.06 - 0.06 * k, 1.06 - 0.06 * k); ctx.translate(-W / 2, -H / 2);
  }
  linhas.forEach((ln, k) => {
    const y = H / 2 + (k - (linhas.length - 1) / 2) * tam * 1.5;
    const palavras = ln.split(" ");
    const verm = c.vermelho ? c.vermelho.split(" ") : [palavras[palavras.length - 1]];
    ctx.font = `${peso0} ${tam}px "${fam}"`;
    const larg = ctx.measureText(ln).width; let x = W / 2 - larg / 2;
    for (const p of palavras) {
      const n = Math.max(0, Math.min(p.length, mostrados));
      mostrados -= p.length + 1;
      if (n <= 0) break;
      const ehV = k === linhas.length - 1 && verm.includes(p);
      ctx.fillStyle = ehV ? "#d9302a" : "rgba(236,230,214,.92)";
      if (ehV) { ctx.shadowColor = "rgba(217,48,42,.75)"; ctx.shadowBlur = c.estilo === "impacto" ? 40 : 18; }
      else if (c.estilo === "impacto") { ctx.shadowColor = "rgba(255,240,220,.25)"; ctx.shadowBlur = 24; } else ctx.shadowBlur = 0;
      ctx.fillText(p.slice(0, n), x, y);
      x += ctx.measureText(p + " ").width;
    }
  });
  ctx.restore();
}

// cartão emoldurado (documento/foto) sobre o fundo desfocado
function cartao(c, t, a) {
  const im = IMG["img:" + c.imagem]; if (!im) return;
  const { W, H } = D;
  ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = "#050505"; ctx.fillRect(0, 0, W, H);
  ctx.filter = "blur(30px) brightness(0.35)";
  const sb = Math.max(W / im.width, H / im.height) * 1.1; ctx.drawImage(im, (W - im.width * sb) / 2, (H - im.height * sb) / 2, im.width * sb, im.height * sb);
  ctx.filter = "none";
  const e = easeInOut(lin(t, c.t0, Math.max(1, c.t1 - c.t0)));
  const z = (c.zoom ? c.zoom[0] + (c.zoom[1] - c.zoom[0]) * e : 1);
  const sc = Math.min(W * 0.72 / im.width, H * 0.72 / im.height) * z, w = im.width * sc, h = im.height * sc;
  const ent = easeOut(lin(t, c.t0, 0.5));
  ctx.translate(W / 2, H / 2 + (1 - ent) * 40); ctx.rotate(((c.giro ?? -1.5) * Math.PI) / 180);
  ctx.shadowColor = "rgba(0,0,0,.85)"; ctx.shadowBlur = 60; ctx.fillStyle = "#e9e3d3";
  const b = Math.round(Math.min(W, H) * 0.012); ctx.fillRect(-w / 2 - b, -h / 2 - b, w + 2 * b, h + 2 * b + (c.legenda_cartao ? b * 5 : 0));
  ctx.shadowBlur = 0; ctx.drawImage(im, -w / 2, -h / 2, w, h);
  if (c.legenda_cartao) {
    ctx.fillStyle = "#2a2116"; ctx.font = `600 ${Math.round(b * 2.6)}px "${D.tema.fonte_papel || D.tema.fonte_texto}"`;
    ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText(c.legenda_cartao, 0, h / 2 + b * 3.2);
  }
  ctx.restore();
}

function desenharCena(c, t, a = 1) {
  if (c.tipo === "relogio") return relogioDigital(c, t, a);
  if (c.tipo === "texto") return telaTexto(c, t, a);
  if (c.tipo === "cartao") return cartao(c, t, a);
  const im = IMG["img:" + c.imagem];
  if (!im) return;
  const ra = im.width / im.height, rt = D.W / D.H;
  if (c.encaixe === "conter" || (c.encaixe !== "cobrir" && (ra / rt < 0.7 || ra / rt > 1.45))) {
    // formato muito diferente do vídeo: fundo desfocado + imagem inteira no centro
    ctx.save(); ctx.globalAlpha = a; ctx.filter = "blur(28px) brightness(0.45)";
    const ep = easeInOut(lin(t, c.t0, Math.max(0.5, c.t1 - c.t0))), sb = Math.max(D.W / im.width, D.H / im.height) * (1.12 + 0.06 * ep);
    ctx.drawImage(im, (D.W - im.width * sb) / 2 - D.W * 0.03 * ep, (D.H - im.height * sb) / 2, im.width * sb, im.height * sb);
    ctx.filter = "none";
    const z = (c.zoom ? c.zoom[0] + (c.zoom[1] - c.zoom[0]) * easeInOut(lin(t, c.t0, Math.max(0.5, c.t1 - c.t0))) : 1);
    const sc = Math.min(D.W / im.width, D.H / im.height) * z, w = im.width * sc, h = im.height * sc;
    ctx.shadowColor = "rgba(0,0,0,.8)"; ctx.shadowBlur = 50;
    ctx.drawImage(im, (D.W - w) / 2, (D.H - h) / 2, w, h); ctx.restore();
    c._tf = [(D.W - w) / 2, (D.H - h) / 2, w, h];
    return;
  }
  const dur = Math.max(0.5, c.t1 - c.t0), e = (c.curva === "rapida" ? easeOut : easeInOut)(lin(t, c.t0, c.curva === "rapida" ? Math.min(dur, c.duracao_zoom || 1.2) : dur));
  const [z0, z1] = c.zoom || [1.0, 1.04];
  const [f0, f1] = c.foco || [[0.5, 0.5], [0.5, 0.5]];
  const z = z0 + (z1 - z0) * e, fx = f0[0] + (f1[0] - f0[0]) * e, fy = f0[1] + (f1[1] - f0[1]) * e;
  // escala para cobrir a tela; o foco (fração da imagem) fica no centro da tela quando possível
  const s = Math.max(D.W / im.width, D.H / im.height) * z, iw = im.width * s, ih = im.height * s;
  let ox = D.W / 2 - fx * iw, oy = D.H / 2 - fy * ih;
  ox = Math.min(0, Math.max(D.W - iw, ox)); oy = Math.min(0, Math.max(D.H - ih, oy));
  // tremor sutil (impacto)
  if (c.tremor && t - c.t0 < 0.5) { const k = (1 - (t - c.t0) / 0.5) * c.tremor; ox += Math.sin(t * 90) * k; oy += Math.cos(t * 77) * k; }
  ctx.globalAlpha = a;
  if (c.desaturar) ctx.filter = "saturate(0.25) sepia(0.25) brightness(1.06)";   // lembrança / reinterpretação
  ctx.drawImage(im, ox, oy, iw, ih); ctx.filter = "none"; ctx.globalAlpha = 1;
  c._tf = [ox, oy, iw, ih];   // posição da imagem na tela (para a revelação achar a criatura)
}

// ------------------------------------------------------------------ kanji sobre a imagem (Ep. 08) — v2, 12/11
// Pedido do usuário: "mais destaque, mais bem feitos". Estilo título de filme japonês:
//   pincelada de fundo (nanquim/vermelho, cerdas falhando), kanji grosso com sombra de profundidade,
//   carimbo hanko vermelho que "bate" no fim, respingos de tinta, pulso de luz ao terminar, aberração de cor opcional.
// c.kanji = [{texto, t|atraso, x, y, tam, vertical, modo:"luz"|"sangue"|"tinta"|"recorte"|"placa", fonte:"pincel"|"mincho",
//   fundo:"nanquim"|"vermelho"|"nenhum" (padrão por modo), selo:"怪" (hanko), respingos (true), glitch (bool),
//   escrever (s), legenda, lado_legenda, sombra (0–1), opacidade, sair}]
function _semente(s) { let h = 2166136261; for (const ch of s) h = Math.imul(h ^ ch.charCodeAt(0), 16777619); return () => ((h = Math.imul(h ^ (h >>> 15), 2246822507) ^ Math.imul(h ^ (h >>> 13), 3266489909)) >>> 0) / 4294967296; }
let _ruidoPincel = null;
function ruidoPincel() {
  if (_ruidoPincel) return _ruidoPincel;
  const n = 256, oc = document.createElement("canvas"); oc.width = oc.height = n;
  const g = oc.getContext("2d"), im = g.createImageData(n, n), r = _semente("pincel");
  for (let i = 0; i < n * n; i++) {
    const y = Math.floor(i / n), x = i % n;
    const fibra = 0.95 + 0.05 * Math.sin(y * 1.7 + Math.sin(x * 0.04) * 4);
    const v = fibra - (r() < 0.006 ? 0.8 : 0) - (r() < 0.04 ? 0.15 : 0);
    im.data[i * 4 + 3] = Math.max(0, Math.min(255, v * 255)); im.data[i * 4] = im.data[i * 4 + 1] = im.data[i * 4 + 2] = 255;
  }
  g.putImageData(im, 0, 0); _ruidoPincel = oc; return oc;
}
const _cacheK = {};
function _canvas(k, W, H) { let c = _cacheK[k]; if (!c) { c = _cacheK[k] = document.createElement("canvas"); } if (c.width !== W || c.height !== H) { c.width = W; c.height = H; } return c; }
// pincelada larga com cerdas: desenhada uma vez por kanji (cache), revelada junto com a escrita
function _pincelada(K, W, H, cx, cy, comp, larg, vert, cor) {
  const chave = "pin:" + K.texto + cx + cy + comp + cor;
  if (_cacheK[chave]) return _cacheK[chave];
  const oc = document.createElement("canvas"); oc.width = W; oc.height = H; const g = oc.getContext("2d"), r = _semente(K.texto + "p");
  g.save(); g.translate(cx, cy); if (!vert) g.rotate(-Math.PI / 2);
  g.rotate((r() - 0.5) * 0.06);
  const L = comp * 1.12, meia = larg / 2, passos = 140;
  g.fillStyle = cor;
  for (let i = 0; i <= passos; i++) {            // corpo: espessura varia (pressão do pincel), ponta afina
    const u = i / passos, y = -L / 2 + u * L;
    const pres = Math.sin(Math.min(1, u * 6) * Math.PI / 2) * (1 - Math.pow(Math.max(0, u - 0.82) / 0.18, 1.6) * 0.75);
    const w = meia * (0.82 + 0.18 * Math.sin(u * 9 + r())) * pres;
    const dx = Math.sin(u * 3.1) * meia * 0.12;
    g.fillRect(dx - w, y, w * 2, L / passos + 1.5);
  }
  g.globalCompositeOperation = "destination-out";   // cerdas: riscos finos sem tinta ao longo do traço, mais na cauda
  for (let k = 0; k < 46; k++) {
    const x = (r() - 0.5) * larg * 0.95, y0 = -L / 2 + L * (0.3 + r() * 0.55), y1 = L / 2 + 10;
    g.globalAlpha = 0.35 + r() * 0.6; g.lineWidth = 1 + r() * larg * 0.025;
    g.beginPath(); g.moveTo(x, y0); g.lineTo(x + (r() - 0.5) * 8, y1); g.stroke();
  }
  g.globalAlpha = 1; g.globalCompositeOperation = "destination-in";
  g.fillStyle = g.createPattern(ruidoPincel(), "repeat"); g.fillRect(-W, -H, W * 2, H * 2);
  g.restore();
  _cacheK[chave] = oc; return oc;
}
function _respingos(K, W, H, cx, cy, raio, cor) {
  const chave = "resp:" + K.texto + cx + cy + cor;
  if (_cacheK[chave]) return _cacheK[chave];
  const oc = document.createElement("canvas"); oc.width = W; oc.height = H; const g = oc.getContext("2d"), r = _semente(K.texto + "r");
  g.fillStyle = cor;
  for (let k = 0; k < 22; k++) {
    const a = r() * 6.283, d = raio * (0.55 + r() * 0.75), s = raio * (0.006 + r() * r() * 0.05);
    const x = cx + Math.cos(a) * d * 0.7, y = cy + Math.sin(a) * d;
    g.beginPath(); g.arc(x, y, s, 0, 6.283); g.fill();
    if (r() < 0.4) { g.beginPath(); g.arc(x + Math.cos(a) * s * 2.6, y + Math.sin(a) * s * 2.6, s * 0.45, 0, 6.283); g.fill(); }
  }
  _cacheK[chave] = oc; return oc;
}
function kanjiSobre(c, t) {
  const { W, H } = D;
  for (const K of c.kanji) {
    const t0 = K.t ?? (c.t0 + (K.atraso ?? 0.5));
    if (t < t0) continue;
    const modo = K.modo || "luz", vert = K.vertical !== false, txt = [...(K.texto || "")];
    const tam = Math.round(H * (K.tam ?? (vert ? 0.2 : 0.21)));
    const fonte = K.fonte === "mincho" ? `800 ${tam}px "Shippori Mincho", "Nanum Myeongjo"` : `400 ${tam}px "Yuji Syuku", "Nanum Brush Script"`;
    const passo = tam * (vert ? 1.0 : 0.98);
    const cx = W * (K.x ?? 0.78), cy = H * (K.y ?? 0.5);
    const larg = vert ? tam : txt.length * passo, alt = vert ? txt.length * passo : tam;
    const comp = vert ? alt : larg;
    // tempos: pincelada (0–35%), escrita (20–100%), carimbo e respingos no fim, pulso de luz
    const dur = K.escrever ?? Math.min(2.6, 0.38 * txt.length + 0.7);
    const fundoPadrao = { luz: "vermelho", sangue: "nanquim", tinta: "vermelho", recorte: "nanquim", placa: "nenhum" }[modo];
    const fundo = txt.length < 2 && K.fundo == null ? "nenhum" : (K.fundo ?? fundoPadrao);
    const pP = easeOut(lin(t, t0, dur * 0.4)), pE = easeOut(lin(t, t0 + dur * 0.2, dur * 0.8));
    const fimE = t0 + dur, vida = Math.max(0.5, c.t1 - t0);
    const sair = K.sair ?? 0.6, aOut = 1 - easeInOut(lin(t, c.t1 - sair, sair));
    const op = (K.opacidade ?? 1) * aOut;
    const e = easeInOut(lin(t, t0, vida)), dy = -H * 0.01 * e;
    const pulso = Math.max(0, 1 - Math.abs(t - fimE) / 0.25);           // flash curto quando termina de escrever
    const soco = 1 + 0.035 * Math.max(0, 1 - (t - fimE) / 0.3) * (t >= fimE ? 1 : 0);
    ctx.save(); ctx.globalAlpha = op;
    ctx.translate(cx, cy + dy); ctx.scale(soco, soco); ctx.translate(-cx, -cy);
    // 1) vinheta de leitura
    const sb = K.sombra ?? (modo === "tinta" ? 0.15 : 0.55);
    if (sb > 0) {
      const rg = ctx.createRadialGradient(cx, cy, 0, cx, cy, Math.max(larg, alt) * 0.95);
      rg.addColorStop(0, `rgba(0,0,0,${sb})`); rg.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = rg; ctx.fillRect(0, 0, W, H);
    }
    // 2) pincelada de fundo, revelada no sentido do traço
    if (fundo !== "nenhum" && pP > 0) {
      const corF = fundo === "vermelho" ? "#a3171a" : "#070605";
      const pin = _pincelada(K, W, H, cx, cy, comp, tam * 1.55, vert, corF);
      const m = _canvas("mascP", W, H), g = m.getContext("2d"); g.clearRect(0, 0, W, H); g.drawImage(pin, 0, 0);
      g.globalCompositeOperation = "destination-in";
      const pena = tam * 0.5; let gr;
      if (vert) { const a = cy - comp * 0.6, b = cy + comp * 0.6, f = a + (b - a + pena) * pP; gr = g.createLinearGradient(0, f - pena, 0, f); }
      else { const a = cx - comp * 0.6, b = cx + comp * 0.6, f = a + (b - a + pena) * pP; gr = g.createLinearGradient(f - pena, 0, f, 0); }
      gr.addColorStop(0, "#000"); gr.addColorStop(1, "rgba(0,0,0,0)"); g.fillStyle = gr; g.fillRect(0, 0, W, H);
      g.globalCompositeOperation = "source-over";
      ctx.globalAlpha = op * (fundo === "vermelho" ? 0.9 : 0.92); ctx.drawImage(m, 0, 0); ctx.globalAlpha = op;
    }
    // 3) máscara do texto (com engrossamento de tinta e textura), revelada caractere a caractere
    const mk = _canvas("mascK", W, H), g = mk.getContext("2d");
    g.clearRect(0, 0, W, H); g.font = fonte; g.textAlign = "center"; g.textBaseline = "middle";
    g.fillStyle = "#fff"; g.strokeStyle = "#fff"; g.lineJoin = "round"; g.lineWidth = tam * (K.fonte === "mincho" ? 0.012 : 0.03);
    txt.forEach((ch, i) => {
      const px = vert ? cx : cx - larg / 2 + passo * (i + 0.5), py = vert ? cy - alt / 2 + passo * (i + 0.5) : cy;
      g.fillText(ch, px, py); g.strokeText(ch, px, py);
    });
    g.globalCompositeOperation = "destination-in";
    g.fillStyle = g.createPattern(ruidoPincel(), "repeat"); g.fillRect(0, 0, W, H);
    const pena = tam * 0.45; let gr;
    if (vert) { const a = cy - alt / 2 - pena, b = cy + alt / 2, f = a + (b - a + pena) * pE; gr = g.createLinearGradient(0, f - pena, 0, f); }
    else { const a = cx - larg / 2 - pena, b = cx + larg / 2, f = a + (b - a + pena) * pE; gr = g.createLinearGradient(f - pena, 0, f, 0); }
    gr.addColorStop(0, "#000"); gr.addColorStop(1, "rgba(0,0,0,0)"); g.fillStyle = gr; g.fillRect(0, 0, W, H);
    g.globalCompositeOperation = "source-over";
    const tinge = (cor, chave = "tinge") => {
      const o = _canvas(chave, W, H), h = o.getContext("2d"); h.globalCompositeOperation = "source-over"; h.clearRect(0, 0, W, H);
      h.drawImage(mk, 0, 0); h.globalCompositeOperation = "source-in"; h.fillStyle = cor; h.fillRect(0, 0, W, H);
      h.globalCompositeOperation = "source-over"; return o;
    };
    // 4) sombra de profundidade (deslocada e desfocada) — lê em qualquer fundo
    if (modo !== "tinta") {
      ctx.globalAlpha = op * 0.85; ctx.filter = `blur(${Math.round(tam * 0.035)}px)`;
      ctx.drawImage(tinge("#000"), tam * 0.035, tam * 0.05); ctx.filter = "none"; ctx.globalAlpha = op;
    }
    // 5) o texto, por modo
    if (modo === "tinta") {
      ctx.globalCompositeOperation = "multiply"; ctx.drawImage(tinge("#0d0a08"), 0, 0); ctx.globalCompositeOperation = "source-over";
      ctx.globalAlpha = op * 0.5; ctx.drawImage(tinge("#0d0a08"), 0, 0); ctx.globalAlpha = op;
    } else if (modo === "sangue") {     // vermelho-sangue sólido, brilho só por baixo, contorno escuro fino
      ctx.globalAlpha = op * (0.55 + 0.45 * pulso); ctx.filter = `blur(${Math.round(tam * 0.08)}px)`; ctx.drawImage(tinge("#e0100f"), 0, 0); ctx.filter = "none";
      ctx.globalAlpha = op; ctx.filter = `drop-shadow(0 0 ${Math.max(1, Math.round(tam * 0.012))}px #000)`;
      ctx.drawImage(tinge("#ff1622"), 0, 0); ctx.filter = "none"; ctx.drawImage(tinge("#ff1622"), 0, 0);
    } else if (modo === "recorte") {
      const o = _canvas("rec", W, H), h = o.getContext("2d"); h.clearRect(0, 0, W, H);
      h.filter = "brightness(3.4) contrast(1.5) saturate(0.4)"; h.drawImage(cv, 0, 0); h.filter = "none";
      h.globalCompositeOperation = "destination-in"; h.drawImage(mk, 0, 0); h.globalCompositeOperation = "source-over";
      ctx.globalAlpha = op * 0.6; ctx.filter = `blur(${Math.round(tam * 0.06)}px)`; ctx.drawImage(tinge("#fff6e0"), 0, 0); ctx.filter = "none";
      ctx.globalAlpha = op; ctx.drawImage(o, 0, 0); ctx.drawImage(o, 0, 0);
      ctx.globalAlpha = op * 0.6; ctx.drawImage(tinge("#fffaf0"), 0, 0); ctx.globalAlpha = op;
    } else if (modo === "placa") {
      ctx.drawImage(tinge("#121010"), 0, 0);
    } else {   // luz: papel quente brilhante sobre nanquim
      ctx.globalAlpha = op * (0.45 + 0.5 * pulso); ctx.filter = `blur(${Math.round(tam * 0.1)}px)`; ctx.drawImage(tinge("#ffe9c2"), 0, 0); ctx.filter = "none";
      ctx.globalAlpha = op; ctx.drawImage(tinge("#fbf5e8"), 0, 0); ctx.drawImage(tinge("#fbf5e8"), 0, 0);
    }
    // 6) aberração de cor (glitch) — só onde pedido, oscila de leve
    if (K.glitch && modo !== "tinta") {
      const d = tam * 0.012 * (1 + Math.sin(t * 23) * 0.6);
      ctx.globalCompositeOperation = "screen"; ctx.globalAlpha = op * 0.45;
      ctx.drawImage(tinge("#ff0030", "gR"), -d, 0); ctx.drawImage(tinge("#00e5ff", "gB"), d, 0);
      ctx.globalCompositeOperation = "source-over"; ctx.globalAlpha = op;
    }
    // 7) respingos de tinta (aparecem com o fim da escrita)
    if ((K.respingos ?? modo !== "placa") && t >= fimE - 0.15) {
      const corR = modo === "sangue" ? "#a3121a" : modo === "luz" || modo === "recorte" ? "#0b0908" : "#0d0a08";
      ctx.globalAlpha = op * Math.min(1, (t - fimE + 0.15) / 0.12);
      ctx.drawImage(_respingos(K, W, H, cx, cy, Math.max(larg, alt) * 0.75, corR), 0, 0); ctx.globalAlpha = op;
    }
    // 8) carimbo hanko: bate no fim (escala 1.35→1, gira 6°→-4°)
    if (K.selo && t >= fimE - 0.05) {
      const k = easeOut(lin(t, fimE - 0.05, 0.22)), s = tam * 0.6;
      const hx = vert ? cx + larg * 0.5 + s * 0.75 : cx + larg / 2 + s * 0.85, hy = vert ? cy + alt / 2 - s * 0.35 : cy + tam * 0.3;
      ctx.save(); ctx.translate(hx, hy); ctx.rotate((6 - 10 * k) * Math.PI / 180); ctx.scale(1.35 - 0.35 * k, 1.35 - 0.35 * k);
      ctx.globalAlpha = op * Math.min(1, k * 2.5);
      const o = _canvas("selo", Math.ceil(s * 1.2), Math.ceil(s * 1.2)), h = o.getContext("2d"), z = o.width;
      h.clearRect(0, 0, z, z); h.fillStyle = "#b71c1c"; h.beginPath();
      if (h.roundRect) h.roundRect(z * 0.08, z * 0.08, z * 0.84, z * 0.84, z * 0.08); else h.rect(z * 0.08, z * 0.08, z * 0.84, z * 0.84);
      h.fill();
      h.globalCompositeOperation = "destination-out"; h.font = `800 ${Math.round(z * 0.62)}px "Shippori Mincho", "Nanum Myeongjo"`; h.textAlign = "center"; h.textBaseline = "middle";
      h.fillStyle = "#000"; h.fillText(K.selo, z / 2, z / 2 + z * 0.03);
      h.globalAlpha = 0.5; h.fillStyle = h.createPattern(ruidoPincel(), "repeat"); h.fillRect(0, 0, z, z);   // carimbo gasto
      h.globalAlpha = 1; h.globalCompositeOperation = "source-over";
      ctx.drawImage(o, -z / 2, -z / 2); ctx.restore();
    }
    ctx.restore();
    // 9) legenda em português (fora da escala do soco)
    if (K.legenda) {
      const al = easeOut(lin(t, fimE - 0.1, 0.6)) * op;
      if (al > 0) {
        const fs = Math.round(H * 0.032), lado = K.lado_legenda || (vert ? ((K.x ?? 0.78) > 0.5 ? "esq" : "dir") : "baixo");
        ctx.save(); ctx.font = `700 ${fs}px "Inter", "Oswald", sans-serif`; ctx.fillStyle = `rgba(244,238,224,${al})`;
        ctx.shadowColor = "rgba(0,0,0,.95)"; ctx.shadowBlur = 16;
        const letras = K.legenda.toUpperCase().split("").join(" ");
        const linha = (x0, y0, x1, y1) => { ctx.strokeStyle = `rgba(190,30,30,${al})`; ctx.lineWidth = Math.max(2, fs * 0.12); ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke(); };
        if (lado === "baixo") {   // 13/11: em várias linhas (" · ") e sem passar da largura da tela (Shorts)
          ctx.textAlign = "center";
          const partes = ctx.measureText(letras).width > W * 0.9 ? K.legenda.toUpperCase().split(" · ") : [letras];
          let yy = cy + alt / 2 + fs * 2.0, wmax = 0;
          partes.forEach((pt, k) => {
            let f = k ? Math.round(fs * 0.85) : fs; ctx.font = `${k ? 500 : 700} ${f}px "Inter", "Oswald", sans-serif`;
            while (ctx.measureText(pt).width > W * 0.9 && f > 12) { f -= 2; ctx.font = `${k ? 500 : 700} ${f}px "Inter", "Oswald", sans-serif`; }
            ctx.fillText(pt, cx, yy); wmax = Math.max(wmax, ctx.measureText(pt).width); yy += fs * 1.35;
          });
          linha(cx - wmax * 0.2, yy - fs * 0.35, cx + wmax * 0.2, yy - fs * 0.35);
        }
        else {   // 13/11: legenda SEMPRE na horizontal (antes girava 90° e ninguém lia), maior, ao lado do kanji
          const fs2 = Math.round(H * 0.034); ctx.font = `700 ${fs2}px "Inter", "Oswald", sans-serif`;
          const partes = K.legenda.toUpperCase().split(" · "), esq = lado === "esq", lx = esq ? cx - larg * 0.75 : cx + larg * 0.75;
          ctx.textAlign = esq ? "right" : "left";
          const y0 = cy - (partes.length - 1) * fs2 * 0.65;
          partes.forEach((pt, k) => { ctx.font = `${k ? 500 : 700} ${k ? Math.round(fs2 * 0.8) : fs2}px "Inter", "Oswald", sans-serif`; ctx.fillText(pt, lx, y0 + k * fs2 * 1.3); });
          ctx.font = `700 ${fs2}px "Inter", "Oswald", sans-serif`;
          const w = Math.min(ctx.measureText(partes[0]).width, fs2 * 4); linha(esq ? lx - w : lx, y0 + fs2 * 0.45, esq ? lx : lx + w, y0 + fs2 * 0.45);
        }
        ctx.restore();
      }
    }
  }
}

// ================================================================== OBRA-PRIMA (Ep. 08, 12/11)
// Cada cena é pintada inteira numa camada própria (camadaCena) e as transições juntam duas camadas:
//   entrada: "nanquim" (mancha de tinta abre a próxima), "shoji" (porta de correr), "vela" (apaga e acende),
//            "fundir", "preto" (como antes). duracao_entrada (s).
// Câmera:  mao (0–1, celular na mão), dof {x,y,r,atraso} (foco com desfoque em volta), paralaxe nas gravuras.
// Atmosfera: atmos: ["neblina","poeira","vela","pelicula","fumaca"] (ou {neblina:0.6,...}).
// Celular: celular {hora, vertical, sinal:"fraco"}, zoom_digital {ate, x, y, atraso, dur}.
// Tipos novos: "chat" (grupo da família), "mapa" (ponto azul), "capitulo" (第一章), "relogios" (dois fusos).
// Sobreposição: linha {anos:[...], atual} (linha do tempo das lendas).
function _ruido1(t, s) { return (Math.sin(t * 1.7 + s) + Math.sin(t * 2.9 + s * 1.3) * 0.6 + Math.sin(t * 5.3 + s * 2.1) * 0.3) / 1.9; }
let _texNevoa = null, _campoTinta = null;
function _fbm(n, w, h, sem, oitavas = 5, per = false) {   // per: periódico na horizontal (textura sem emenda)   // ruído fractal em grade baixa (valores 0–1)
  const r = _semente(sem), base = [];
  for (let o = 0; o < oitavas; o++) { const g = 2 ** (o + 2); const arr = []; for (let i = 0; i < (g + 1) * (g + 1); i++) arr.push(r()); base.push([g, arr]); }
  const out = new Float32Array(w * h);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    let v = 0, amp = 1, tot = 0;
    for (const [g, arr] of base) {
      const fx = x / w * g, fy = y / h * g, x0 = Math.floor(fx), y0 = Math.floor(fy), tx = fx - x0, ty = fy - y0;
      const sx = tx * tx * (3 - 2 * tx), sy = ty * ty * (3 - 2 * ty);
      const x1 = per ? (x0 + 1) % g : x0 + 1, a = arr[y0 * (g + 1) + x0], b = arr[y0 * (g + 1) + x1], c = arr[(y0 + 1) * (g + 1) + x0], d = arr[(y0 + 1) * (g + 1) + x1];
      v += amp * (a + (b - a) * sx + (c - a) * sy + (a - b - c + d) * sx * sy); tot += amp; amp *= 0.55;
    }
    out[y * w + x] = v / tot;
  }
  return out;
}
function texNevoa() {
  if (_texNevoa) return _texNevoa;
  const w = 512, h = 256, f = _fbm(0, w, h, "nevoa", 5, true), oc = document.createElement("canvas"); oc.width = w; oc.height = h;
  const g = oc.getContext("2d"), im = g.createImageData(w, h);
  for (let i = 0; i < w * h; i++) { const yb = Math.floor(i / w), borda = Math.pow(Math.sin(Math.PI * (yb + 0.5) / h), 0.8), v = Math.max(0, Math.min(1, (f[i] - 0.38) * 2.4)) * borda; im.data[i * 4] = 205; im.data[i * 4 + 1] = 212; im.data[i * 4 + 2] = 220; im.data[i * 4 + 3] = v * 255; }
  // 13/11: ruído periódico em x + bordas verticais suaves = sem a "linha passando" na neblina
  g.putImageData(im, 0, 0); _texNevoa = oc; return oc;
}
// ------------------------------------------------------------------ camada de cena
function camadaCena(c, t, alvo) {
  const { W, H } = D, sCtx = ctx, sCv = cv;
  cv = alvo; ctx = alvo.getContext("2d");
  ctx.save(); ctx.globalAlpha = 1; ctx.globalCompositeOperation = "source-over"; ctx.filter = "none";
  ctx.fillStyle = "#000"; ctx.fillRect(0, 0, W, H);
  if (c.tipo === "chat") telaChat(c, t);
  else if (c.tipo === "mapa") telaMapa(c, t);
  else if (c.tipo === "capitulo") telaCapitulo(c, t);
  else if (c.tipo === "relogios") telaRelogios(c, t);
  else {
    ctx.save();
    if (c.mao) {   // celular na mão: deriva + micro-tremor + leve giro
      const k = c.mao, ox = W * 0.006 * k * _ruido1(t * 0.9, 1) + W * 0.0015 * k * Math.sin(t * 17), oy = H * 0.008 * k * _ruido1(t * 0.8, 4) + H * 0.0015 * k * Math.sin(t * 13 + 1);
      ctx.translate(W / 2 + ox, H / 2 + oy); ctx.rotate(0.006 * k * _ruido1(t * 0.6, 7)); ctx.scale(1 + 0.03 * k, 1 + 0.03 * k); ctx.translate(-W / 2, -H / 2);
    }
    if (c.celular && c.celular.vertical) videoVertical(c, t); else desenharCena(c, t);
    ctx.restore();
    if (c.zoom_digital) zoomDigital(c, t);
    if (c.dof) profundidade(c, t);
  }
  if (c.atmos) atmosfera(c, t);
  if (c.celular) interfaceCelular(c, t);
  if (c.kanji) kanjiSobre(c, t);
  if (c.linha) linhaTempo(c, t);
  ctx.restore();
  ctx = sCtx; cv = sCv;
}
// ------------------------------------------------------------------ transições
function _mascaraTinta(p, W, H) {
  const w = 192, h = 108;
  if (!_campoTinta) {   // campo: ruído fractal + manchas que crescem de 3 sementes
    const f = _fbm(0, w, h, "tinta", 5), r = _semente("sementes"), sem = [[0.5 + (r() - 0.5) * 0.3, 0.5 + (r() - 0.5) * 0.3], [r(), r()], [r(), r()]];
    _campoTinta = new Float32Array(w * h);
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      let d = 9; for (const [sx, sy] of sem) d = Math.min(d, Math.hypot(x / w - sx, (y / h - sy) * 0.6));
      _campoTinta[y * w + x] = 0.55 * d / 0.62 + 0.45 * f[y * w + x];
    }
  }
  const m = _canvas("mTinta", w, h), g = m.getContext("2d"), im = g.createImageData(w, h);
  const borda = _canvas("bTinta", w, h), gb = borda.getContext("2d"), ib = gb.createImageData(w, h);
  const lim = p * 1.12;
  for (let i = 0; i < w * h; i++) {
    const v = _campoTinta[i], a = Math.max(0, Math.min(1, (lim - v) / 0.025));
    im.data[i * 4 + 3] = a * 255;
    const e = Math.max(0, 1 - Math.abs(v - lim) / 0.035); ib.data[i * 4 + 3] = e * 230;
  }
  g.putImageData(im, 0, 0); gb.putImageData(ib, 0, 0);
  return [m, borda];
}
function transicao(tipo, A, B, k, t) {
  const { W, H } = D;
  if (tipo === "nanquim") {
    ctx.drawImage(A, 0, 0);
    const [m, borda] = _mascaraTinta(k, W, H);
    const o = _canvas("trB", W, H), g = o.getContext("2d");
    g.globalCompositeOperation = "source-over"; g.clearRect(0, 0, W, H); g.drawImage(B, 0, 0);
    g.globalCompositeOperation = "destination-in"; g.imageSmoothingEnabled = true; g.drawImage(m, 0, 0, W, H); g.globalCompositeOperation = "source-over";
    ctx.drawImage(o, 0, 0);
    ctx.save(); ctx.globalAlpha = 0.85 * Math.sin(Math.PI * Math.min(1, k * 1.05)); ctx.filter = "blur(3px)";
    const ob = _canvas("trBorda", W, H), gb = ob.getContext("2d"); gb.clearRect(0, 0, W, H); gb.drawImage(borda, 0, 0, W, H);
    gb.globalCompositeOperation = "source-in"; gb.fillStyle = "#050403"; gb.fillRect(0, 0, W, H); gb.globalCompositeOperation = "source-over";
    ctx.drawImage(ob, 0, 0); ctx.restore();
  } else if (tipo === "shoji") {
    const e = easeInOut(k), x = W * (1 - e);
    ctx.save(); ctx.filter = `brightness(${1 - 0.45 * e})`; ctx.drawImage(A, -W * 0.12 * e, 0); ctx.restore();
    ctx.save(); ctx.beginPath(); ctx.rect(x, 0, W - x, H); ctx.clip(); ctx.drawImage(B, x * 0.25, 0);
    // treliça de papel por cima da cena que entra, sumindo
    ctx.globalAlpha = 0.55 * (1 - e); ctx.fillStyle = "#efe6d2"; ctx.fillRect(x, 0, W - x, H);
    ctx.globalAlpha = 0.6 * (1 - e); ctx.strokeStyle = "#3a2a1c"; ctx.lineWidth = Math.max(2, W / 640);
    const cel = W / 9; for (let gx = x; gx < W; gx += cel) { ctx.beginPath(); ctx.moveTo(gx, 0); ctx.lineTo(gx, H); ctx.stroke(); }
    for (let gy = 0; gy < H; gy += cel * 0.75) { ctx.beginPath(); ctx.moveTo(x, gy); ctx.lineTo(W, gy); ctx.stroke(); }
    ctx.restore();
    // a moldura de madeira da porta
    const bw = W * 0.016; const gr = ctx.createLinearGradient(x - bw, 0, x + bw, 0);
    gr.addColorStop(0, "rgba(0,0,0,0)"); gr.addColorStop(0.35, "#2a1b10"); gr.addColorStop(0.55, "#5a3b22"); gr.addColorStop(0.7, "#24170d"); gr.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = gr; ctx.fillRect(x - bw, 0, bw * 2, H);
  } else if (tipo === "vela") {   // íris fecha na cena velha (com fumaça) e abre na nova
    const fecha = k < 0.5, kk = fecha ? 1 - k * 2 : (k - 0.5) * 2, img = fecha ? A : B;
    ctx.fillStyle = "#000"; ctx.fillRect(0, 0, W, H);
    const r = Math.hypot(W, H) * 0.55 * easeInOut(kk);
    if (r > 2) {
      const o = _canvas("trV", W, H), g = o.getContext("2d"); g.globalCompositeOperation = "source-over"; g.clearRect(0, 0, W, H); g.drawImage(img, 0, 0);
      const rg = g.createRadialGradient(W / 2, H * 0.48, r * 0.55, W / 2, H * 0.48, r);
      rg.addColorStop(0, "#000"); rg.addColorStop(1, "rgba(0,0,0,0)");
      g.globalCompositeOperation = "destination-in"; g.fillStyle = rg; g.fillRect(0, 0, W, H); g.globalCompositeOperation = "source-over";
      ctx.drawImage(o, 0, 0);
      ctx.save(); ctx.globalCompositeOperation = "soft-light"; ctx.globalAlpha = 0.5 * (1 - kk); ctx.fillStyle = "#ff9a40"; ctx.fillRect(0, 0, W, H); ctx.restore();
    }
    // fumaça subindo do centro quando escurece
    const fum = Math.sin(Math.PI * k); if (fum > 0.02) {
      ctx.save(); ctx.globalAlpha = 0.35 * fum; ctx.strokeStyle = "#cfcfcf"; ctx.lineCap = "round";
      for (let i = 0; i < 4; i++) { ctx.lineWidth = W * (0.004 + i * 0.002); ctx.filter = `blur(${4 + i * 3}px)`; ctx.beginPath();
        for (let s = 0; s <= 30; s++) { const u = s / 30, y = H * (0.55 - u * 0.5 * (0.6 + k)), x = W / 2 + Math.sin(u * 6 + t * 2 + i) * W * 0.03 * u * (1 + i); s ? ctx.lineTo(x, y) : ctx.moveTo(x, y); }
        ctx.stroke(); }
      ctx.restore();
    }
  } else if (tipo === "fundir") { ctx.drawImage(A, 0, 0); ctx.globalAlpha = easeInOut(k); ctx.drawImage(B, 0, 0); ctx.globalAlpha = 1; }
  else if (tipo === "preto") { ctx.fillStyle = "#000"; ctx.fillRect(0, 0, W, H); ctx.globalAlpha = easeInOut(k); ctx.drawImage(B, 0, 0); ctx.globalAlpha = 1; }
  else ctx.drawImage(B, 0, 0);
}
// ------------------------------------------------------------------ câmera
function profundidade(c, t) {   // foco num ponto: o resto desfoca e escurece, entra devagar
  const { W, H } = D, F = c.dof, k = easeInOut(lin(t, c.t0 + (F.atraso ?? 0.8), F.dur ?? 1.6));
  if (k <= 0) return;
  const nit = _canvas("dofN", W, H), g = nit.getContext("2d"); g.clearRect(0, 0, W, H); g.drawImage(cv, 0, 0);
  ctx.save(); ctx.filter = `blur(${Math.round(12 * k)}px) brightness(${1 - 0.35 * k})`; ctx.drawImage(nit, 0, 0); ctx.restore();
  const tf = c._tf || [0, 0, W, H], cx = tf[0] + tf[2] * F.x, cy = tf[1] + tf[3] * F.y, r = Math.min(W, H) * (F.r ?? 0.25);
  const rg = g.createRadialGradient(cx, cy, r * 0.45, cx, cy, r);
  rg.addColorStop(0, "#000"); rg.addColorStop(1, "rgba(0,0,0,0)");
  g.globalCompositeOperation = "destination-in"; g.fillStyle = rg; g.fillRect(0, 0, W, H); g.globalCompositeOperation = "source-over";
  ctx.drawImage(nit, 0, 0);
}
function zoomDigital(c, t) {   // zoom de celular até um ponto, pixelando cada vez mais
  const { W, H } = D, Z = c.zoom_digital, k = easeInOut(lin(t, c.t0 + (Z.atraso ?? 0.5), Z.dur ?? Math.max(1, c.t1 - c.t0 - 0.6)));
  if (k <= 0) return;
  const tf = c._tf || [0, 0, W, H], z = 1 + ((Z.ate ?? 5) - 1) * k, cx = tf[0] + tf[2] * (Z.x ?? 0.5), cy = tf[1] + tf[3] * (Z.y ?? 0.4);
  const fonte = _canvas("zdF", W, H), g = fonte.getContext("2d"); g.clearRect(0, 0, W, H); g.drawImage(cv, 0, 0);
  // 13/11: no vídeo vertical o zoom fica DENTRO do quadro do celular (antes ampliava a tela toda, com o fundo)
  const [rx, ry, rw, rh] = c._vv ? [c._vv[0], 0, c._vv[1], H] : [0, 0, W, H];
  const pix = Math.max(1, Math.round(1 + (z - 1) * 1.1)), pw = Math.max(9, Math.round(rw / pix)), ph = Math.max(9, Math.round(rh / pix));
  const pq = _canvas("zdP" + pw + "x" + ph, pw, ph), gp = pq.getContext("2d"); gp.imageSmoothingEnabled = true;
  const sw = rw / z, sh = rh / z, sx = Math.min(rx + rw - sw, Math.max(rx, cx - sw / 2)), sy = Math.min(ry + rh - sh, Math.max(ry, cy - sh / 2));
  gp.clearRect(0, 0, pw, ph); gp.drawImage(fonte, sx, sy, sw, sh, 0, 0, pw, ph);
  ctx.save(); ctx.imageSmoothingEnabled = pix < 3; ctx.drawImage(pq, rx, ry, rw, rh); ctx.restore();
}
// ------------------------------------------------------------------ atmosfera
function atmosfera(c, t) {
  const { W, H } = D, A = Array.isArray(c.atmos) ? Object.fromEntries(c.atmos.map((n) => [n, 1])) : c.atmos;
  ctx.save();
  if (A.neblina || A.fumaca) {
    const tex = texNevoa(), forte = A.neblina || A.fumaca, sobe = !!A.fumaca;
    ctx.globalCompositeOperation = "screen";
    for (let cam = 0; cam < 2; cam++) {
      const vel = (cam ? 0.018 : 0.011) * W, esc = cam ? 1.6 : 2.4, tw = W * esc, th = H * esc * 0.6;
      const ox = -((t * vel) % tw), oy = sobe ? -((t * H * 0.02 * (cam + 1)) % th) : H * (cam ? 0.25 : 0.45) - th * 0.5;
      ctx.globalAlpha = forte * (cam ? 0.18 : 0.24);
      for (let x = ox; x < W; x += tw) for (let y = sobe ? oy : oy; y < H; y += sobe ? th : H * 9) ctx.drawImage(tex, x, y, tw, th);
    }
  }
  if (A.poeira) {
    const r = _semente("poeira"); ctx.globalCompositeOperation = "screen";
    for (let i = 0; i < 70; i++) {
      const z = 0.3 + r() * 0.7, x = ((r() * W + t * W * 0.006 * z + Math.sin(t * 0.7 + i) * 12) % W + W) % W, y = ((r() * H - t * H * 0.01 * z) % H + H) % H;
      const s = 1 + z * 2.6, a = A.poeira * (0.15 + 0.5 * z) * (0.6 + 0.4 * Math.sin(t * 2 + i));
      ctx.globalAlpha = a; ctx.fillStyle = "#fff4dc"; ctx.beginPath(); ctx.arc(x, y, s, 0, 6.283); ctx.fill();
    }
  }
  if (A.vela) {   // luz de vela: quente, tremendo, de baixo
    const n = 0.75 + 0.25 * _ruido1(t * 3.2, 2) + 0.08 * Math.sin(t * 31);
    const vx = W * (c.vela_x ?? 0.5), vy = H * (c.vela_y ?? 0.8);
    ctx.globalCompositeOperation = "soft-light"; ctx.globalAlpha = A.vela * 0.55 * n;
    const rg = ctx.createRadialGradient(vx, vy, 0, vx, vy, H * 0.9); rg.addColorStop(0, "#ffb050"); rg.addColorStop(1, "rgba(255,120,30,0)");
    ctx.fillStyle = rg; ctx.fillRect(0, 0, W, H);
    ctx.globalCompositeOperation = "multiply"; ctx.globalAlpha = A.vela * (1 - n) * 0.5; ctx.fillStyle = "#000"; ctx.fillRect(0, 0, W, H);
  }
  if (A.pelicula) {   // película 1970: vazamento de luz, riscos, poeira, tremor de janela
    const f = Math.floor(t * 24), r = _semente("pel" + f);
    ctx.globalCompositeOperation = "screen";
    const lx = W * (0.85 + 0.15 * Math.sin(t * 0.37)), ly = H * (0.2 + 0.3 * Math.sin(t * 0.23 + 1));
    const lg = ctx.createRadialGradient(lx, ly, 0, lx, ly, W * 0.45); lg.addColorStop(0, "rgba(255,110,40,.55)"); lg.addColorStop(0.5, "rgba(255,60,20,.18)"); lg.addColorStop(1, "rgba(0,0,0,0)");
    ctx.globalAlpha = A.pelicula * (0.5 + 0.5 * _ruido1(t, 9)); ctx.fillStyle = lg; ctx.fillRect(0, 0, W, H);
    ctx.globalCompositeOperation = "source-over";
    for (let i = 0; i < 3; i++) if (r() < 0.35) { ctx.globalAlpha = 0.25 * A.pelicula; ctx.fillStyle = r() < 0.5 ? "#fff" : "#000"; ctx.fillRect(r() * W, 0, 1 + r() * 1.5, H); }
    for (let i = 0; i < 14; i++) { ctx.globalAlpha = 0.5 * A.pelicula * r(); ctx.fillStyle = r() < 0.5 ? "#fff" : "#000"; ctx.beginPath(); ctx.arc(r() * W, r() * H, 0.6 + r() * 2.2, 0, 6.283); ctx.fill(); }
    ctx.globalCompositeOperation = "soft-light"; ctx.globalAlpha = 0.35 * A.pelicula; ctx.fillStyle = "#c8902a"; ctx.fillRect(0, 0, W, H);
  }
  ctx.restore();
}
// ------------------------------------------------------------------ celular
function videoVertical(c, t) {   // vídeo de celular em pé dentro do quadro 16:9, com fundo desfocado dele mesmo
  const { W, H } = D, im = IMG["img:" + c.imagem]; if (!im) return;
  ctx.save(); ctx.filter = "blur(30px) brightness(0.35)";
  const sb = Math.max(W / im.width, H / im.height) * 1.1; ctx.drawImage(im, (W - im.width * sb) / 2, (H - im.height * sb) / 2, im.width * sb, im.height * sb);
  ctx.restore();
  const vh = H, vw = H * 9 / 16, vx = (W - vw) / 2, e = easeInOut(lin(t, c.t0, Math.max(0.5, c.t1 - c.t0)));
  const [z0, z1] = c.zoom || [1.0, 1.06], z = z0 + (z1 - z0) * e, f = c.foco || [[0.5, 0.5], [0.5, 0.5]];
  const fx = f[0][0] + (f[1][0] - f[0][0]) * e, fy = f[0][1] + (f[1][1] - f[0][1]) * e;
  const s = Math.max(vw / im.width, vh / im.height) * z, iw = im.width * s, ih = im.height * s;
  let ox = vx + vw / 2 - fx * iw, oy = vh / 2 - fy * ih; ox = Math.min(vx, Math.max(vx + vw - iw, ox)); oy = Math.min(0, Math.max(vh - ih, oy));
  ctx.save(); ctx.beginPath(); ctx.rect(vx, 0, vw, vh); ctx.clip(); ctx.drawImage(im, ox, oy, iw, ih); ctx.restore();
  c._tf = [ox, oy, iw, ih];
  ctx.save(); ctx.shadowColor = "rgba(0,0,0,.8)"; ctx.shadowBlur = 40; ctx.strokeStyle = "rgba(0,0,0,.6)"; ctx.lineWidth = 2; ctx.strokeRect(vx, 0, vw, vh); ctx.restore();
  c._vv = [vx, vw];
}
function interfaceCelular(c, t) {
  const { W, H } = D, C = c.celular, u = H / 1080;
  const [vx, vw] = C.vertical && c._vv ? c._vv : [0, W];
  ctx.save();
  // foco caçando: pulsos curtos de desfoque
  const caça = Math.max(0, Math.sin(t * 1.3 + 2) - 0.86) / 0.14 + (t - c.t0 < 0.8 ? 1 - (t - c.t0) / 0.8 : 0);
  if (caça > 0.02) { const o = _canvas("celF", W, H), g = o.getContext("2d"); g.clearRect(0, 0, W, H); g.drawImage(cv, 0, 0); ctx.filter = `blur(${(caça * 6).toFixed(1)}px)`; ctx.drawImage(o, 0, 0); ctx.filter = "none"; }
  // compressão de sinal fraco: blocos
  if (C.sinal === "fraco" && Math.sin(t * 2.3) > 0.55) {
    const o = _canvas("celB", W, H), g = o.getContext("2d"); g.clearRect(0, 0, W, H); g.drawImage(cv, 0, 0);
    const p = _canvas("celP", Math.round(W / 14), Math.round(H / 14)), gp = p.getContext("2d"); gp.drawImage(o, 0, 0, p.width, p.height);
    ctx.save(); ctx.imageSmoothingEnabled = false; ctx.globalAlpha = 0.55; ctx.drawImage(p, 0, 0, W, H); ctx.restore();
  }
  ctx.font = `600 ${Math.round(26 * u)}px "Inter", sans-serif`; ctx.fillStyle = "rgba(255,255,255,.92)"; ctx.shadowColor = "rgba(0,0,0,.8)"; ctx.shadowBlur = 6;
  const s = Math.floor(t - c.t0), mm = String(Math.floor(s / 60)).padStart(2, "0"), ss = String(s % 60).padStart(2, "0");
  ctx.textAlign = "center";
  ctx.fillStyle = "rgba(220,30,30,.95)"; ctx.beginPath(); ctx.roundRect ? ctx.roundRect(vx + vw / 2 - 62 * u, 26 * u, 124 * u, 40 * u, 8 * u) : ctx.rect(vx + vw / 2 - 62 * u, 26 * u, 124 * u, 40 * u); ctx.fill();
  ctx.fillStyle = "#fff"; ctx.fillText(`${mm}:${ss}`, vx + vw / 2, 55 * u);
  ctx.textAlign = "left"; ctx.fillText(C.hora || "23:41", vx + 26 * u, 55 * u);
  ctx.textAlign = "right"; ctx.fillText(C.sinal === "fraco" ? "sem serviço" : "4G", vx + vw - 26 * u, 55 * u);
  // quadrado de foco
  const fx = vx + vw * (C.foco_x ?? 0.5), fy = H * (C.foco_y ?? 0.5), q = 70 * u * (1 + 0.15 * caça);
  ctx.strokeStyle = `rgba(255,214,10,${0.5 + 0.5 * Math.min(1, caça)})`; ctx.lineWidth = 2 * u; ctx.shadowBlur = 0;
  for (const [sx, sy] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) { ctx.beginPath(); ctx.moveTo(fx + sx * q, fy + sy * q * 0.6); ctx.lineTo(fx + sx * q, fy + sy * q); ctx.lineTo(fx + sx * q * 0.6, fy + sy * q); ctx.stroke(); }
  ctx.restore();
}
function _telefone(t, desenho) {   // moldura de celular no centro, grande, com aproximação lenta (lê no celular do espectador)
  const { W, H } = D, ph = H * 1.0, pw = ph * 0.56, px = (W - pw) / 2, py = (H - ph) / 2 + H * 0.02, u = ph / 680;
  const c0 = D.cenas[cenaAtual(t)] || { t0: t, t1: t + 1 }, zc = 1 + 0.07 * easeInOut(lin(t, c0.t0, Math.max(1, c0.t1 - c0.t0)));
  ctx.translate(W / 2, H * 0.62); ctx.scale(zc, zc); ctx.translate(-W / 2, -H * 0.62);
  const rg = ctx.createRadialGradient(W / 2, H / 2, 0, W / 2, H / 2, W * 0.6); rg.addColorStop(0, "#14181c"); rg.addColorStop(1, "#020203");
  ctx.fillStyle = rg; ctx.fillRect(0, 0, W, H);
  ctx.save(); ctx.shadowColor = "rgba(120,170,255,.25)"; ctx.shadowBlur = 80; ctx.fillStyle = "#0a0a0b";
  ctx.beginPath(); ctx.roundRect(px - 10 * u, py - 10 * u, pw + 20 * u, ph + 20 * u, 46 * u); ctx.fill(); ctx.restore();
  ctx.save(); ctx.beginPath(); ctx.roundRect(px, py, pw, ph, 38 * u); ctx.clip(); desenho(px, py, pw, ph, u); ctx.restore();
}
function telaChat(c, t) {
  _telefone(t, (px, py, pw, ph, u) => {
    ctx.fillStyle = "#101418"; ctx.fillRect(px, py, pw, ph);
    const digit = (c.mensagens || []).find((m) => m.digitando_ate && t >= m.digitando_de && t < m.digitando_ate);
    ctx.save(); ctx.beginPath(); ctx.rect(px, py + 100 * u, pw, ph - 100 * u); ctx.clip();
    // mensagens visíveis (as que já chegaram), de baixo pra cima
    const vis = (c.mensagens || []).filter((m) => t >= (m.t ?? c.t0));
    let y = py + ph - (digit ? 112 : 40) * u; const fs = Math.round(22 * u), larg = pw * 0.72;   // com "digitando", as mensagens sobem
    ctx.font = `500 ${fs}px "Inter", "Noto Color Emoji", sans-serif`;
    const blocos = vis.map((m) => {
      const linhas = []; let atual = "";
      if (m.tipo === "audio") return { m, h: (m.de && m.de !== "eu" ? 96 : 64) * u, linhas };
      if (m.tipo === "foto" || m.tipo === "video") return { m, h: larg * 0.75 + 30 * u, linhas };
      for (const p of (m.texto || "").split(" ")) { const tt = atual ? atual + " " + p : p; if (ctx.measureText(tt).width > larg - 40 * u && atual) { linhas.push(atual); atual = p; } else atual = tt; }
      linhas.push(atual); return { m, h: linhas.length * fs * 1.3 + (m.de && m.de !== "eu" ? 30 : 12) * u + 44 * u, linhas };   // 13/11: espaço pro horário
    });
    for (let i = blocos.length - 1; i >= 0 && y > py + 110 * u; i--) {
      const { m, h, linhas } = blocos[i], meu = m.de === "eu";
      const ent = easeOut(lin(t, m.t ?? c.t0, 0.25)); ctx.font = `700 ${Math.round(17 * u)}px "Inter", sans-serif`; const wNome = m.de && m.de !== "eu" ? ctx.measureText(m.de).width + 40 * u : 0; ctx.font = `500 ${fs}px "Inter", "Noto Color Emoji", sans-serif`;
      const bw = m.tipo === "audio" ? larg * 0.8 : m.tipo === "foto" || m.tipo === "video" ? larg : Math.min(larg, Math.max(wNome, ...linhas.map((l) => ctx.measureText(l).width + 40 * u)));
      const av = meu ? 0 : 50 * u, bx = meu ? px + pw - bw - 18 * u : px + 18 * u + av, by = y - h;
      const COR = { Dani: "#e6a95a", Bia: "#e6a95a", Lucas: "#6fb3ff", "Mãe": "#ff8fb1", Pai: "#7fd18b", "Tia Nena": "#7fd18b" }, corP = m.cor || COR[m.de] || "#c9a7ff";
      ctx.save(); ctx.globalAlpha = ent; ctx.translate(0, (1 - ent) * 20 * u);
      if (!meu) {   // avatar com a inicial, ao lado do balão
        ctx.fillStyle = corP; ctx.globalAlpha = ent * 0.9; ctx.beginPath(); ctx.arc(bx - 26 * u, by + 22 * u, 19 * u, 0, 6.283); ctx.fill(); ctx.globalAlpha = ent;
        ctx.fillStyle = "#101418"; ctx.font = `800 ${Math.round(18 * u)}px "Inter", sans-serif`; ctx.textAlign = "center"; ctx.fillText(m.de[0], bx - 26 * u, by + 28 * u); ctx.textAlign = "left";
      }
      ctx.fillStyle = meu ? "#2c4a6e" : "#232b33"; ctx.beginPath(); ctx.roundRect(bx, by, bw, h - 10 * u, 16 * u); ctx.fill();
      let ty = by + 30 * u;
      if (!meu && m.de) { ctx.fillStyle = corP; ctx.font = `700 ${Math.round(17 * u)}px "Inter", sans-serif`; ctx.fillText(m.de, bx + 18 * u, ty - 2 * u); ty += 26 * u; }
      ctx.font = `500 ${fs}px "Inter", "Noto Color Emoji", sans-serif`; ctx.fillStyle = "#eef2f5";
      if (m.tipo === "audio") {   // áudio com onda
        const ya = (!meu && m.de) ? ty + 14 * u : by + (h - 10 * u) / 2, nb = Math.floor((bw - 150 * u) / (9 * u));   // onda ABAIXO do nome
        ctx.fillStyle = "#cfd8df"; ctx.beginPath(); ctx.arc(bx + 34 * u, ya, 14 * u, 0, 6.283); ctx.fill();
        const r = _semente(m.texto || "audio"); for (let k = 0; k < nb; k++) { const hh = (6 + r() * 22) * u; ctx.fillRect(bx + 62 * u + k * 9 * u, ya - hh / 2, 4 * u, hh); }
        ctx.font = `500 ${Math.round(15 * u)}px "Inter", sans-serif`; ctx.fillText(m.duracao || "0:07", bx + bw - 54 * u, by + h - 22 * u);
      } else if (m.tipo === "foto" || m.tipo === "video") {
        const im = IMG["img:" + m.imagem]; const iw = bw - 16 * u, ih = larg * 0.75 - 10 * u;
        if (im) { const s = Math.max(iw / im.width, ih / im.height); ctx.save(); ctx.beginPath(); ctx.roundRect(bx + 8 * u, ty - 16 * u, iw, ih, 10 * u); ctx.clip(); ctx.drawImage(im, bx + 8 * u + (iw - im.width * s) / 2, ty - 16 * u + (ih - im.height * s) / 2, im.width * s, im.height * s); ctx.restore(); }
        if (m.tipo === "video") { ctx.fillStyle = "rgba(0,0,0,.5)"; ctx.beginPath(); ctx.arc(bx + bw / 2, ty - 16 * u + ih / 2, 30 * u, 0, 6.283); ctx.fill(); ctx.fillStyle = "#fff"; ctx.beginPath(); ctx.moveTo(bx + bw / 2 - 9 * u, ty - 16 * u + ih / 2 - 14 * u); ctx.lineTo(bx + bw / 2 + 15 * u, ty - 16 * u + ih / 2); ctx.lineTo(bx + bw / 2 - 9 * u, ty - 16 * u + ih / 2 + 14 * u); ctx.fill(); }
      } else linhas.forEach((l, k) => ctx.fillText(l, bx + 20 * u, ty + k * fs * 1.3));
      ctx.font = `500 ${Math.round(13 * u)}px "Inter", sans-serif`; ctx.fillStyle = "#93a1ad"; ctx.textAlign = "right";
      ctx.fillText((m.hora || "") + (meu ? "  " + (m.check || "✓✓") : ""), bx + bw - 14 * u, by + h - 18 * u); ctx.textAlign = "left";
      ctx.restore();
      y = by - 8 * u;
    }
    ctx.restore();
    // cabeçalho do grupo POR CIMA (genérico, sem marca)
    ctx.fillStyle = "#1b222a"; ctx.fillRect(px, py, pw, 100 * u);
    ctx.fillStyle = "#5a6b7d"; ctx.beginPath(); ctx.arc(px + 50 * u, py + 56 * u, 22 * u, 0, 6.283); ctx.fill();
    ctx.fillStyle = "#e9eef2"; ctx.font = `700 ${Math.round(24 * u)}px "Inter", "Noto Color Emoji", sans-serif`; ctx.textAlign = "left";
    ctx.fillText(c.grupo || "Família 🏠", px + 86 * u, py + 52 * u);
    ctx.font = `500 ${Math.round(16 * u)}px "Inter", sans-serif`; ctx.fillStyle = digit ? "#7fd18b" : "#93a1ad";
    ctx.fillText(digit ? `${digit.de} está digitando…` : (c.membros || "Dani, Lucas, Mãe, Pai"), px + 86 * u, py + 76 * u);
    if (digit) {   // balão "digitando" com três pontos
      const bx = px + 68 * u, by = py + ph - 100 * u; ctx.fillStyle = "#232b33"; ctx.beginPath(); ctx.roundRect(bx, by, 90 * u, 46 * u, 16 * u); ctx.fill();
      for (let k = 0; k < 3; k++) { ctx.globalAlpha = 0.4 + 0.6 * Math.max(0, Math.sin(t * 7 - k * 0.8)); ctx.fillStyle = "#cfd8df"; ctx.beginPath(); ctx.arc(bx + 26 * u + k * 19 * u, by + 23 * u, 6 * u, 0, 6.283); ctx.fill(); }
      ctx.globalAlpha = 1;
    }
  });
}
function telaMapa(c, t) {   // mapa de celular "de verdade": cidade, arrozais, rio, ferrovia, rodovia, serra; câmera segue o ponto
  _telefone(t, (px, py, pw, ph, u) => {
    const MW = pw * 1.35, MH = ph * 1.12, r = _semente("mapa2");
    const rota = [[0.12, 0.88], [0.2, 0.8], [0.27, 0.74], [0.33, 0.66], [0.4, 0.6], [0.46, 0.52], [0.53, 0.47], [0.6, 0.4], [0.66, 0.33], [0.72, 0.27], [0.78, 0.2], [0.82, 0.15]];
    const dur = Math.max(1, (c.some ?? (c.t1 - c.t0)) - 0.4), P = c.progresso || [0, 1], p = P[0] + (P[1] - P[0]) * easeInOut(lin(t, c.t0 + 0.3, dur)), n = rota.length - 1, f = p * n, k0 = Math.min(n - 1, Math.floor(f)), fr = f - k0;
    const dx = (rota[k0][0] + (rota[k0 + 1][0] - rota[k0][0]) * fr), dy = (rota[k0][1] + (rota[k0 + 1][1] - rota[k0][1]) * fr);
    const camX = Math.min(MW - pw, Math.max(0, dx * MW - pw / 2)), camY = Math.min(MH - ph, Math.max(0, dy * MH - ph * 0.55));
    ctx.save(); ctx.translate(px - camX, py - camY);
    ctx.fillStyle = "#1e2622"; ctx.fillRect(0, 0, MW, MH);
    // arrozais (retângulos claros em grade torta) na planície
    for (let i = 0; i < 160; i++) { const x = r() * MW * 0.75, y = MH * 0.35 + r() * MH * 0.65; ctx.fillStyle = r() < 0.5 ? "#26332a" : "#2a382d"; ctx.save(); ctx.translate(x, y); ctx.rotate(0.3); ctx.fillRect(0, 0, 22 * u + r() * 28 * u, 14 * u + r() * 16 * u); ctx.restore(); }
    // serra: manchas de mata escura com curvas de nível e sombra
    for (let i = 0; i < 7; i++) { const x = MW * (0.55 + r() * 0.45), y = MH * (r() * 0.45), rx = MW * (0.1 + r() * 0.12), ry = MH * (0.08 + r() * 0.1);
      const gr = ctx.createRadialGradient(x - rx * 0.3, y - ry * 0.3, 0, x, y, rx); gr.addColorStop(0, "#2f4434"); gr.addColorStop(1, "#18241b"); ctx.fillStyle = gr; ctx.beginPath(); ctx.ellipse(x, y, rx, ry, r() * 3, 0, 6.283); ctx.fill();
      ctx.strokeStyle = "rgba(120,150,120,.22)"; ctx.lineWidth = 1.1 * u; for (let k = 1; k < 6; k++) { ctx.beginPath(); ctx.ellipse(x, y, rx * k / 6, ry * k / 6, 0.4, 0, 6.283); ctx.stroke(); } }
    // cidade (quadras) no canto de baixo
    for (let gx = 0; gx < 9; gx++) for (let gy = 0; gy < 7; gy++) { if (r() < 0.15) continue; ctx.fillStyle = "#353b3e"; ctx.fillRect(MW * 0.01 + gx * 24 * u, MH * 0.76 + gy * 19 * u, 19 * u, 14 * u); }
    // rio
    ctx.strokeStyle = "#1f4a66"; ctx.lineWidth = 16 * u; ctx.lineCap = "round"; ctx.beginPath(); ctx.moveTo(MW * 0.32, 0); ctx.bezierCurveTo(MW * 0.25, MH * 0.35, MW * 0.48, MH * 0.55, MW * 0.36, MH); ctx.stroke();
    // ferrovia (cinza com dormentes) saindo da cidade
    ctx.strokeStyle = "#8a8f93"; ctx.lineWidth = 4 * u; ctx.beginPath(); ctx.moveTo(MW * 0.05, MH * 0.82); ctx.bezierCurveTo(MW * 0.3, MH * 0.72, MW * 0.35, MH * 0.4, MW * 0.6, MH * 0.12); ctx.stroke();
    ctx.setLineDash([3 * u, 9 * u]); ctx.lineWidth = 10 * u; ctx.strokeStyle = "rgba(138,143,147,.6)"; ctx.stroke(); ctx.setLineDash([]);
    // estradas: rodovia amarela + ruas
    ctx.strokeStyle = "#3f4a4c"; ctx.lineWidth = 5 * u; for (let i = 0; i < 14; i++) { ctx.beginPath(); ctx.moveTo(r() * MW, r() * MH); ctx.quadraticCurveTo(r() * MW, r() * MH, r() * MW, r() * MH); ctx.stroke(); }
    ctx.strokeStyle = "#b08a2e"; ctx.lineWidth = 9 * u; ctx.beginPath(); rota.forEach(([x, y], k) => k ? ctx.lineTo(x * MW, y * MH) : ctx.moveTo(x * MW, y * MH)); ctx.stroke();
    ctx.strokeStyle = "#e0b44a"; ctx.lineWidth = 5 * u; ctx.stroke();
    // rótulos
    const rot = (txt, x, y, tam, cor) => { ctx.font = `700 ${Math.round(tam * u)}px "Inter", "Shippori Mincho", "Nanum Myeongjo", sans-serif`; ctx.fillStyle = cor; ctx.strokeStyle = "rgba(10,14,12,.85)"; ctx.lineWidth = 4 * u; ctx.strokeText(txt, x, y); ctx.fillText(txt, x, y); };
    rot("浜松 Hamamatsu", MW * 0.03, MH * 0.72, 20, "#e6e9ea"); rot("天竜川", MW * 0.37, MH * 0.3, 15, "#6fa8d0"); rot("国道152号", MW * 0.47, MH * 0.5, 14, "#e0b44a");
    rot("山", MW * 0.7, MH * 0.12, 22, "#9fb79f"); rot("山", MW * 0.88, MH * 0.3, 22, "#9fb79f");
    // rastro azul do caminho já feito
    ctx.strokeStyle = "rgba(66,133,244,.85)"; ctx.lineWidth = 7 * u; ctx.beginPath();
    for (let k = 0; k <= k0; k++) k ? ctx.lineTo(rota[k][0] * MW, rota[k][1] * MH) : ctx.moveTo(rota[k][0] * MW, rota[k][1] * MH);
    ctx.lineTo(dx * MW, dy * MH); ctx.stroke();
    // o ponto: azul com cone de direção; quando some, fica cinza e congela
    const some = c.some != null && t >= c.t0 + c.some, x = dx * MW, y = dy * MH;
    if (!some) {
      const ang = Math.atan2(rota[k0 + 1][1] - rota[k0][1], rota[k0 + 1][0] - rota[k0][0]);
      ctx.fillStyle = "rgba(66,133,244,.22)"; ctx.beginPath(); ctx.moveTo(x, y); ctx.arc(x, y, 60 * u, ang - 0.45, ang + 0.45); ctx.fill();
      ctx.fillStyle = "rgba(66,133,244,.2)"; ctx.beginPath(); ctx.arc(x, y, (24 + 10 * Math.sin(t * 4)) * u, 0, 6.283); ctx.fill();
    }
    ctx.fillStyle = "#fff"; ctx.beginPath(); ctx.arc(x, y, 13 * u, 0, 6.283); ctx.fill();
    ctx.fillStyle = some ? "#7d8790" : "#4285f4"; ctx.beginPath(); ctx.arc(x, y, 9 * u, 0, 6.283); ctx.fill();
    ctx.restore();
    // barra de cima (contato) e de baixo (estado)
    ctx.fillStyle = "rgba(14,18,22,.92)"; ctx.fillRect(px, py, pw, 92 * u);
    ctx.fillStyle = "#e6a95a"; ctx.beginPath(); ctx.arc(px + 44 * u, py + 50 * u, 20 * u, 0, 6.283); ctx.fill();
    ctx.fillStyle = "#101418"; ctx.font = `800 ${Math.round(18 * u)}px "Inter", sans-serif`; ctx.textAlign = "center"; ctx.fillText("D", px + 44 * u, py + 57 * u); ctx.textAlign = "left";
    ctx.fillStyle = "#e9eef2"; ctx.font = `700 ${Math.round(21 * u)}px "Inter", sans-serif`; ctx.fillText("Dani", px + 76 * u, py + 44 * u);
    ctx.font = `500 ${Math.round(15 * u)}px "Inter", sans-serif`; ctx.fillStyle = some ? "#e2685a" : "#7fd18b";
    ctx.fillText(some ? "Localização indisponível" : "Localização em tempo real", px + 76 * u, py + 68 * u);
    const km = (3.2 + 14.6 * p).toFixed(1).replace(".", ","), hm = c.hora_inicio || "23:43", [hh, mn] = hm.split(":").map(Number), mi = mn + Math.floor(p * 15);
    ctx.fillStyle = "rgba(14,18,22,.92)"; ctx.fillRect(px, py + ph - 110 * u, pw, 110 * u);
    ctx.fillStyle = "#e9eef2"; ctx.font = `700 ${Math.round(22 * u)}px "Inter", sans-serif`; ctx.fillText(`${km} km de Hamamatsu`, px + 26 * u, py + ph - 66 * u);
    ctx.font = `500 ${Math.round(16 * u)}px "Inter", sans-serif`; ctx.fillStyle = "#93a1ad";
    ctx.fillText(some ? `Última atualização ${c.hora_fim || "23:58"}` : `Atualizado agora · ${String(hh).padStart(2, "0")}:${String(mi % 60).padStart(2, "0")}`, px + 26 * u, py + ph - 36 * u);
  });
}
function telaCapitulo(c, t) {   // abertura de capítulo: papel escuro, número em kanji, título e ano
  const { W, H } = D;
  const im = c.imagem ? IMG["img:" + c.imagem] : null;
  if (im) { ctx.save(); ctx.filter = "blur(6px) brightness(0.28) saturate(0.5)"; const s = Math.max(W / im.width, H / im.height) * (1.05 + 0.04 * lin(t, c.t0, 6)); ctx.drawImage(im, (W - im.width * s) / 2, (H - im.height * s) / 2, im.width * s, im.height * s); ctx.restore(); }
  else { const g = ctx.createRadialGradient(W / 2, H / 2, 0, W / 2, H / 2, W * 0.7); g.addColorStop(0, "#1a1512"); g.addColorStop(1, "#050404"); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); }
  const a = easeOut(lin(t, c.t0 + 0.9, 0.8));
  ctx.save(); ctx.globalAlpha = a; ctx.textAlign = "left";
  ctx.fillStyle = "#b51b1b"; ctx.fillRect(W * 0.42, H * 0.36, W * 0.004, H * 0.28 * a);
  ctx.font = `700 ${Math.round(H * 0.03)}px "Inter", sans-serif`; ctx.fillStyle = "#c9b9a0"; ctx.fillText((c.numero_pt || "CAPÍTULO 1").toUpperCase().split("").join(" "), W * 0.44, H * 0.405);
  ctx.font = `700 ${Math.round(H * 0.085)}px "Cinzel", serif`; ctx.fillStyle = "#f2ead8"; ctx.shadowColor = "rgba(0,0,0,.9)"; ctx.shadowBlur = 20;
  const titulo = c.titulo || "", n = Math.floor(lin(t, c.t0 + 1.1, 0.9) * titulo.length);
  let fsT = Math.round(H * 0.085); ctx.font = `700 ${fsT}px "Cinzel", serif`;
  const maxW = W * 0.5; let linhasT = [titulo];
  if (ctx.measureText(titulo).width > maxW) { const ps = titulo.split(" "), meio = Math.ceil(ps.length / 2); linhasT = [ps.slice(0, meio).join(" "), ps.slice(meio).join(" ")]; }
  while (Math.max(...linhasT.map((l) => ctx.measureText(l).width)) > maxW && fsT > 20) { fsT -= 2; ctx.font = `700 ${fsT}px "Cinzel", serif`; }
  let resto = n; linhasT.forEach((l, k) => { const m = Math.max(0, Math.min(l.length, resto)); resto -= l.length + 1; ctx.fillText(l.slice(0, m), W * 0.44, H * 0.51 + k * fsT * 1.1 - (linhasT.length - 1) * fsT * 0.35); });
  ctx.font = `700 ${Math.round(H * 0.04)}px "Inter", sans-serif`; ctx.fillStyle = "#d4302a"; ctx.globalAlpha = a * easeOut(lin(t, c.t0 + 1.8, 0.5));
  ctx.fillText(c.ano || "", W * 0.44, H * (c.titulo && c.titulo.length > 22 ? 0.67 : 0.6));
  ctx.restore();
  if (!c.kanji && c.numero) c.kanji = [{ texto: c.numero, x: 0.3, y: 0.5, tam: 0.17, modo: "luz", fundo: "vermelho", atraso: 0.15, escrever: 1.0, sombra: 0.3, respingos: true, selo: c.selo }];
}
function telaRelogios(c, t) {   // dois fusos: Hamamatsu (noite) × Londrina (dia); 13/11: no vertical, um em cima do outro
  const { W, H } = D, L = c.lados || [], pe = H > W;
  [0, 1].forEach((i) => {
    const lado = L[i] || {}, im = lado.imagem ? IMG["img:" + lado.imagem] : null;
    const x0 = pe ? 0 : i * W / 2, y0 = pe ? i * H / 2 : 0, qw = pe ? W : W / 2, qh = pe ? H / 2 : H;
    ctx.save(); ctx.beginPath(); ctx.rect(x0, y0, qw, qh); ctx.clip();
    if (im) { const s = Math.max(qw / im.width, qh / im.height) * (1.04 + 0.04 * lin(t, c.t0, 6)); ctx.filter = `brightness(${lado.brilho ?? 0.6})`; ctx.drawImage(im, x0 + (qw - im.width * s) / 2, y0 + (qh - im.height * s) / 2, im.width * s, im.height * s); ctx.filter = "none"; }
    else { ctx.fillStyle = i ? "#c9b48a" : "#0b0e14"; ctx.fillRect(x0, y0, qw, qh); }
    ctx.fillStyle = "rgba(0,0,0,.35)"; ctx.fillRect(x0, y0, qw, qh);
    const base = (lado.hora || "23:40").split(":").map(Number), s = Math.floor((t - c.t0) * (c.velocidade || 1)), mm = base[1] + Math.floor(s / 60);
    const txt = `${String(base[0] + Math.floor(mm / 60)).padStart(2, "0")}:${String(mm % 60).padStart(2, "0")}`;
    const M = Math.min(W, H), cxr = x0 + qw / 2, cyr = pe ? y0 + qh * (i ? 0.72 : 0.55) : H * 0.55;   // o de baixo desce: a legenda fica a 62% da altura
    ctx.textAlign = "center"; ctx.font = `700 ${Math.round(M * 0.17 * (pe ? 1.25 : 1))}px "DejaVu Sans Mono", monospace`; ctx.fillStyle = i ? "#fff4d8" : "#cfe3ff";
    ctx.shadowColor = i ? "rgba(255,200,120,.6)" : "rgba(120,170,255,.6)"; ctx.shadowBlur = 30; ctx.fillText(txt, cxr, cyr);
    ctx.shadowBlur = 8; ctx.font = `700 ${Math.round(M * 0.032 * (pe ? 1.3 : 1))}px "Inter", sans-serif`; ctx.fillStyle = "#f4efe4";
    ctx.fillText((lado.nome || "").toUpperCase().split("").join(" "), cxr, cyr + M * (pe ? 0.13 : 0.11));
    ctx.restore();
  });
  ctx.fillStyle = "#b51b1b";
  if (pe) ctx.fillRect(W * 0.1, H / 2 - 2, W * 0.8 * easeOut(lin(t, c.t0, 0.8)), 4);
  else ctx.fillRect(W / 2 - 2, H * 0.1, 4, H * 0.8 * easeOut(lin(t, c.t0, 0.8)));
}
function linhaTempo(c, t) {   // linha do tempo das lendas — 13/11: com faixa, todos os anos, ano atual grande (antes ninguém via)
  const { W, H } = D, Lt = c.linha, anos = Lt.anos, dur = Lt.dur ?? 6;
  const a = Math.min(easeOut(lin(t, c.t0 + 0.2, 0.6)), 1 - easeInOut(lin(t, c.t0 + dur, 0.8)));
  if (a <= 0) return;
  const x0 = W * 0.12, x1 = W * 0.88, y = H * 0.1, mn = anos[0], mx = anos[anos.length - 1], X = (ano) => x0 + (x1 - x0) * (ano - mn) / (mx - mn);
  ctx.save(); ctx.globalAlpha = a;
  const fx = ctx.createLinearGradient(0, 0, 0, H * 0.24); fx.addColorStop(0, "rgba(0,0,0,.78)"); fx.addColorStop(1, "rgba(0,0,0,0)");
  ctx.fillStyle = fx; ctx.fillRect(0, 0, W, H * 0.24);
  ctx.strokeStyle = "rgba(240,232,215,.6)"; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(x0, y); ctx.lineTo(x1, y); ctx.stroke();
  const de = Lt.de ?? anos[0], k = easeInOut(lin(t, c.t0 + 0.5, 1.6)), xa = X(de) + (X(Lt.atual) - X(de)) * k;
  ctx.strokeStyle = "#e0302a"; ctx.lineWidth = 6; ctx.shadowColor = "rgba(224,48,42,.8)"; ctx.shadowBlur = 14;
  ctx.beginPath(); ctx.moveTo(x0, y); ctx.lineTo(xa, y); ctx.stroke(); ctx.shadowBlur = 0;
  ctx.textAlign = "center";
  for (const ano of anos) {
    const x = X(ano), at = ano === Lt.atual;
    ctx.fillStyle = at ? "#ff3b30" : "rgba(240,232,215,.85)"; ctx.beginPath(); ctx.arc(x, y, at ? 11 : 6, 0, 6.283); ctx.fill();
    if (!at) { ctx.font = `600 ${Math.round(H * 0.022)}px "Inter", sans-serif`; ctx.fillStyle = "rgba(240,232,215,.75)"; ctx.fillText(String(ano), x, y + H * 0.045); }
  }
  // o ano atual, grande, com o marcador "andando" até ele
  ctx.font = `800 ${Math.round(H * 0.05)}px "Inter", sans-serif`; ctx.fillStyle = "#fff"; ctx.shadowColor = "rgba(0,0,0,.9)"; ctx.shadowBlur = 12;
  ctx.fillText(String(Lt.atual), X(Lt.atual), y + H * 0.085);
  ctx.restore();
}

function cenas(t) {
  const { W, H } = D, T = D.tema;
  ctx.fillStyle = "#000"; ctx.fillRect(0, 0, W, H);
  const i = cenaAtual(t);
  if (i < 0) return;
  const c = D.cenas[i], ant = D.cenas[i - 1];
  const padrao = { nanquim: 1.3, shoji: 0.9, vela: 1.6 }[c.entrada] || 0.5;
  const dt = c.duracao_entrada || padrao;
  const A = _canvas("camA", W, H), B = _canvas("camB", W, H);
  if (c.entrada && c.entrada !== "corte" && t < c.t0 + dt && (ant || c.entrada === "preto")) {
    if (ant) camadaCena(ant, t, A);
    camadaCena(c, t, B);
    transicao(c.entrada, A, B, lin(t, c.t0, dt), t);
  } else { camadaCena(c, t, A); ctx.drawImage(A, 0, 0); }
  // revelação: clareia as sombras só na região onde a criatura sempre esteve e desenha um círculo vermelho
  if (c.revelar) {
    const R = c.revelar, k = easeInOut(lin(t, c.t0 + (R.atraso ?? 0.6), R.duracao ?? 1.4));
    const clara = R.clara ? IMG["img:" + R.clara] : null, tf = c._tf || [0, 0, W, H];
    if (k > 0) {
      const cx = tf[0] + R.x * tf[2], cy = tf[1] + R.y * tf[3], rr_ = R.r * Math.min(tf[2], tf[3]);
      ctx.save();
      ctx.fillStyle = `rgba(0,0,0,${0.5 * k})`; ctx.fillRect(0, 0, W, H);   // o resto escurece
      ctx.beginPath(); ctx.arc(cx, cy, rr_ * 1.25, 0, 6.29); ctx.clip();
      ctx.globalAlpha = k;
      if (clara) ctx.drawImage(clara, tf[0], tf[1], tf[2], tf[3]);       // versão clareada: a criatura aparece
      ctx.restore();
      if (R.circulo !== false) {
        const p = easeOut(lin(t, c.t0 + (R.atraso ?? 0.6) + 0.3, 0.7));
        ctx.save(); ctx.strokeStyle = "rgba(230,40,35,.95)"; ctx.lineWidth = Math.max(4, W / 380);
        ctx.shadowColor = "rgba(230,40,35,.8)"; ctx.shadowBlur = 18;
        ctx.beginPath(); ctx.arc(cx, cy, rr_ * 1.3, -Math.PI / 2, -Math.PI / 2 + 6.29 * p); ctx.stroke(); ctx.restore();
      }
    }
  }
  // relâmpagos (abertura)
  for (const r of c.relampagos || []) {
    const dtr = t - c.t0 - r;
    if (dtr >= 0 && dtr < 0.35) { ctx.fillStyle = `rgba(225,235,255,${0.55 * Math.pow(1 - dtr / 0.35, 2) * (dtr < 0.05 ? 1 : 0.8)})`; ctx.fillRect(0, 0, W, H); }
  }
  // flash curto no corte (opcional)
  if (c.flash && t < c.t0 + 0.18) { ctx.fillStyle = `rgba(220,235,230,${0.35 * (1 - lin(t, c.t0, 0.18))})`; ctx.fillRect(0, 0, W, H); }
  // chuva animada por cima (leve)
  if (D.chuva) {
    ctx.save(); ctx.strokeStyle = "rgba(200,220,215,1)"; ctx.lineWidth = 1.6;
    for (const g of D._chuva) {
      const y = ((g.y + t * g.v) % 1) * (H + 200) - 100, x = g.x * W + (y * 0.18);
      ctx.globalAlpha = g.a * D.chuva; ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + g.l * 0.18, y + g.l); ctx.stroke();
    }
    ctx.restore();
  }
  // tratamento: tom frio, contraste, vinheta, granulação
  ctx.save();
  ctx.globalCompositeOperation = "soft-light"; ctx.fillStyle = alpha(T.tom || "#2f5f57", 0.35); ctx.fillRect(0, 0, W, H);
  ctx.globalCompositeOperation = "source-over";
  const v = ctx.createRadialGradient(W / 2, H * 0.45, H * 0.25, W / 2, H * 0.45, H * 0.78);
  v.addColorStop(0, "rgba(0,0,0,0)"); v.addColorStop(1, "rgba(0,0,0,.62)"); ctx.fillStyle = v; ctx.fillRect(0, 0, W, H);
  // escurece levemente a base para legenda e Vigia
  const b = ctx.createLinearGradient(0, H * 0.55, 0, H); b.addColorStop(0, "rgba(0,0,0,0)"); b.addColorStop(1, "rgba(0,0,0,.55)");
  ctx.fillStyle = b; ctx.fillRect(0, H * 0.55, W, H * 0.45);
  ctx.globalCompositeOperation = "overlay"; ctx.globalAlpha = D.grao ?? 0.16;
  const r = rng(Math.floor(t * D.fps) + 1), dx = -Math.floor(r() * 512), dy = -Math.floor(r() * 512);
  for (let x = dx; x < W; x += 512) for (let y = dy; y < H; y += 512) ctx.drawImage(GRAO, x, y);
  // "respiração" da luz (projetor/lâmpada velha): a imagem parada deixa de parecer foto — variação lenta e mínima
  if (D.cintilar) {
    const n = (Math.sin(t * 2.1) + Math.sin(t * 3.7 + 1.3) + Math.sin(t * 0.9 + 4)) / 3;
    ctx.globalCompositeOperation = "source-over"; ctx.globalAlpha = D.cintilar * (0.5 + 0.5 * n);
    ctx.fillStyle = "#000"; ctx.fillRect(0, 0, W, H);
  }
  ctx.restore();
  if (c.cctv) interfaceCCTV(c, t);
  // escurecimento pontual (pausa / queda)
  for (const q of D.escuros || []) {
    if (t >= q.t0 && t <= q.t1) { const a = Math.min(lin(t, q.t0, 0.3), 1 - lin(t, q.t1 - 0.3, 0.3)) * q.forca; ctx.fillStyle = `rgba(0,0,0,${a})`; ctx.fillRect(0, 0, W, H); }
  }
}

// Vigia no canto: destacado (luz de contorno, brilho), "fala" no ritmo da voz, troca de pose com impulso
function envVoz(t) {
  const e = D.voz_env; if (!e || !e.length) return 0;
  const i = Math.min(e.length - 1, Math.max(0, Math.floor(t * D.fps)));
  return e[i];
}
function vigiaCanto(t) {
  let i = -1; D.poses.forEach((p, k) => { if (p.t <= t) i = k; });
  if (i < 0) return;
  const ci = cenaAtual(t), destaque = ci >= 0 && D.cenas[ci].vigia;
  let C = destaque ? D.canto_destaque : D.canto;
  // lado direito: mesma pose (sem espelhar, para não inverter o broche), posição refletida na tela
  if (!destaque && ci >= 0 && D.cenas[ci].lado === "dir") C = Object.assign({}, C, { x: D.W - C.x - C.w });
  const T = D.tema, atual = D.poses[i], ant = D.poses[i - 1];
  const f = easeOut(lin(t, atual.t, 0.12)), e = envVoz(t);
  const alvo = C.w * 0.55;                       // largura da cabeça na tela
  const cx = C.x + C.w / 2, topoCabeca = C.base - 2.45 * alvo;
  // luz ambiente atrás dele: elipse suave SEM bordas (o retângulo antigo cortava o círculo e aparecia "quadrado"),
  // fraca e com a cor da própria cena, para ele parecer estar no lugar e não colado por cima
  const hy = topoCabeca + alvo * 1.1, hr = C.w * 0.85;
  const halo = ctx.createRadialGradient(cx, hy, 0, cx, hy, hr);
  const corH = T.halo_suave || T.halo;
  halo.addColorStop(0, alpha(corH, 0.10 + 0.04 * e)); halo.addColorStop(0.6, alpha(corH, 0.04)); halo.addColorStop(1, alpha(corH, 0));
  ctx.save(); ctx.fillStyle = halo; ctx.beginPath(); ctx.ellipse(cx, hy, hr, hr * 1.25, 0, 0, Math.PI * 2); ctx.fill(); ctx.restore();
  const desenha = (nome, a, pop, dx) => {
    const im = IMG["pose:" + nome], m = D.avatar.poses[nome];
    if (!im || !m) return;
    const s = alvo / m.largura_cabeca * pop * (1 + 0.016 * e) * (1 + 0.005 * Math.sin(t * 1.9));
    const w = im.width * s, h = im.height * s;
    MASCARA.width = Math.ceil(w) + 80; MASCARA.height = Math.ceil(h) + 80;
    const g = MASCARA.getContext("2d");
    g.clearRect(0, 0, MASCARA.width, MASCARA.height); g.imageSmoothingQuality = "high";
    g.filter = "brightness(1.06) contrast(1.04) saturate(0.95)";   // sem "brilho de adesivo"
    g.shadowColor = alpha(T.contorno || "#a9d6c4", 0.16); g.shadowBlur = 22;   // luz de recorte bem sutil
    g.drawImage(im, 40, 40, w, h); g.filter = "none"; g.shadowBlur = 0;
    const y = topoCabeca - m.topo * s - 40 - 5 * e + Math.sin(t * 1.4) * 2;
    const x = cx - m.centro_x * s - 40 + dx;
    // base dissolvida numa linha fixa da tela (todas as poses terminam igual)
    g.globalCompositeOperation = "destination-in";
    const yb = C.base - y, gr = g.createLinearGradient(0, yb - alvo * 0.75, 0, yb);
    gr.addColorStop(0, "rgba(0,0,0,1)"); gr.addColorStop(1, "rgba(0,0,0,0)");
    g.fillStyle = gr; g.fillRect(0, 0, MASCARA.width, MASCARA.height); g.globalCompositeOperation = "source-over";
    ctx.save(); ctx.globalAlpha = a;
    const ang = (Math.sin(t * 0.9) * 0.3 + Math.sin(t * 2.3) * 0.6 * e) * Math.PI / 180;
    ctx.translate(cx, C.base); ctx.rotate(ang); ctx.translate(-cx, -C.base);
    ctx.drawImage(MASCARA, x, y); ctx.restore(); ctx.globalAlpha = 1;
  };
  if (ant && f < 1) desenha(ant.pose, 1 - f, 1, 0);
  const forte = atual.tipo === "enfase" ? 1 : atual.tipo === "conversa" ? 0.25 : 0.7;
  const imp = 1 - easeOut(lin(t, atual.t, atual.tipo === "enfase" ? 0.32 : 0.2));
  desenha(atual.pose, f, 1 + 0.07 * forte * imp, -10 * forte * imp);
}

// Vigia de corpo inteiro (ou do joelho para cima): pés/joelho apoiados na base do canto
function vigiaCorpo(t) {
  let i = -1; D.poses.forEach((p, k) => { if (p.t <= t) i = k; });
  if (i < 0) return;
  const C = D.canto, T = D.tema, atual = D.poses[i], ant = D.poses[i - 1];
  const joelho = C.enquadramento === "joelho";
  const f = easeOut(lin(t, atual.t, 0.12)), e = envVoz(t);
  const cx = C.x + C.largura / 2;
  const halo = ctx.createRadialGradient(cx, C.base - C.altura * 0.6, 20, cx, C.base - C.altura * 0.6, C.altura * 0.6);
  halo.addColorStop(0, alpha(T.halo, 0.26 + 0.1 * e)); halo.addColorStop(1, alpha(T.halo, 0));
  ctx.fillStyle = halo; ctx.fillRect(cx - C.altura, C.base - C.altura * 1.3, C.altura * 2, C.altura * 1.4);
  if (!joelho) { // sombra no chão
    const sg = ctx.createRadialGradient(cx, C.base, 5, cx, C.base, C.largura * 0.7);
    sg.addColorStop(0, "rgba(0,0,0,.6)"); sg.addColorStop(1, "rgba(0,0,0,0)");
    ctx.save(); ctx.translate(cx, C.base); ctx.scale(1, 0.18); ctx.translate(-cx, -C.base);
    ctx.fillStyle = sg; ctx.fillRect(cx - C.largura, C.base - C.largura, C.largura * 2, C.largura * 2); ctx.restore();
  }
  const desenha = (nome, a, pop, dx) => {
    const im = IMG["pose:" + nome], m = D.avatar.poses[nome];
    if (!im || !m) return;
    const corpo = joelho ? C.altura / 0.74 : C.altura;          // no joelho, o corpo "inteiro" seria maior
    const s = corpo / m.altura_ref * pop * (1 + 0.012 * e) * (1 + 0.004 * Math.sin(t * 1.9));
    const w = im.width * s, h = im.height * s;
    MASCARA.width = Math.ceil(w) + 40; MASCARA.height = Math.ceil(h) + 40;
    const g = MASCARA.getContext("2d");
    g.clearRect(0, 0, MASCARA.width, MASCARA.height);
    g.imageSmoothingQuality = "high";
    g.filter = "brightness(1.3) contrast(1.1) saturate(1.08)";
    g.shadowColor = alpha(T.contorno || "#a9d6c4", 0.55); g.shadowBlur = 12;
    g.drawImage(im, 20, 20, w, h); g.filter = "none"; g.shadowBlur = 0;
    let ancoraY = m.pe_y * s + 20;                                // pés
    if (joelho) {
      ancoraY = (m.topo + 0.74 * (m.pe_y - m.topo)) * s + 20;    // joelho
      g.globalCompositeOperation = "destination-in";
      const gr = g.createLinearGradient(0, ancoraY - 120, 0, ancoraY); gr.addColorStop(0, "rgba(0,0,0,1)"); gr.addColorStop(1, "rgba(0,0,0,0)");
      g.fillStyle = gr; g.fillRect(0, 0, MASCARA.width, MASCARA.height); g.globalCompositeOperation = "source-over";
    }
    const x = cx - (m.centro_x * s + 20) + dx, y = C.base - ancoraY;
    ctx.save(); ctx.globalAlpha = a;
    // balanço sutil em torno dos pés + inclinação ao falar
    const ang = (Math.sin(t * 0.9) * 0.4 + Math.sin(t * 2.3) * 0.7 * e) * Math.PI / 180;
    ctx.translate(x + m.centro_x * s + 20, C.base); ctx.rotate(ang); ctx.translate(-(x + m.centro_x * s + 20), -C.base);
    ctx.drawImage(MASCARA, x, y); ctx.restore(); ctx.globalAlpha = 1;
  };
  if (ant && f < 1) desenha(ant.pose, 1 - f, 1, 0);
  // conversa: troca discreta; ênfase: impulso maior para o olho perceber
  const forte = atual.tipo === "enfase" ? 1 : atual.tipo === "conversa" ? 0.25 : 0.7;
  const imp = 1 - easeOut(lin(t, atual.t, atual.tipo === "enfase" ? 0.32 : 0.2));
  desenha(atual.pose, f, 1 + 0.07 * forte * imp, -10 * forte * imp);
}

// Legendas: frases de até 2 linhas, branco quente, sombra discreta, poucas palavras em destaque
function legendas(t) {
  const T = D.tema;
  for (const L of D.legendas || []) {
    if (t < L.t0 || t > L.t1) continue;
    const a = Math.min(lin(t, L.t0, 0.12), 1 - lin(t, L.t1 - 0.12, 0.12));
    const tam = D.legenda_tam || 56, lh = tam * 1.22, y0 = D.legenda_y - (L.linhas.length - 1) * lh;
    fonte(700, tam, T.fonte_texto); ctx.textBaseline = "alphabetic";
    if (D.H > D.W || D.legenda_caixa) {   // 13/11: Shorts — faixa escura atrás da legenda (lê em cima de imagem clara)
      const lmax = Math.max(...L.linhas.map((l) => ctx.measureText(l).width)), px = tam * 0.45;
      ctx.globalAlpha = a * 0.5; ctx.fillStyle = "#000";
      const bx = D.W / 2 - lmax / 2 - px, by = y0 - tam * 1.0, bw = lmax + 2 * px, bh = (L.linhas.length - 1) * lh + tam * 1.45;
      ctx.beginPath(); ctx.roundRect ? ctx.roundRect(bx, by, bw, bh, tam * 0.3) : ctx.rect(bx, by, bw, bh); ctx.fill(); ctx.globalAlpha = 1;
    }
    L.linhas.forEach((linha, k) => {
      const pal = linha.split(" ");
      const larg = ctx.measureText(linha).width;
      const ciL = cenaAtual(t), cxL = (ciL >= 0 && D.cenas[ciL].vigia && D.W > D.H) ? D.W * 0.64 : D.W / 2;
      let x = cxL - larg / 2;
      for (const p of pal) {
        const dest = L.destaques.includes(norm(p));
        ctx.globalAlpha = a; ctx.shadowColor = "rgba(0,0,0,.85)"; ctx.shadowBlur = 14; ctx.shadowOffsetY = 3;
        ctx.fillStyle = dest ? T.destaque_legenda : T.texto_legenda;
        ctx.fillText(p, x, y0 + k * lh);
        x += ctx.measureText(p + " ").width;
      }
    });
    ctx.shadowBlur = 0; ctx.shadowOffsetY = 0; ctx.globalAlpha = 1;
  }
}
function norm(p) { return p.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]/g, ""); }


// Chamada para ação do YouTube (tela final): escurece a cena, botão Inscrever-se, clique e sino
function sino(x, y, r, ang, cor) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(ang); ctx.fillStyle = cor;
  ctx.beginPath(); ctx.moveTo(-r * 0.75, r * 0.45); ctx.quadraticCurveTo(-r * 0.7, -r * 0.75, 0, -r * 0.8);
  ctx.quadraticCurveTo(r * 0.7, -r * 0.75, r * 0.75, r * 0.45); ctx.lineTo(r * 0.95, r * 0.65); ctx.lineTo(-r * 0.95, r * 0.65); ctx.closePath(); ctx.fill();
  ctx.beginPath(); ctx.arc(0, r * 0.82, r * 0.2, 0, 6.29); ctx.fill();
  ctx.beginPath(); ctx.arc(0, -r * 0.88, r * 0.12, 0, 6.29); ctx.fill(); ctx.restore();
}
function cursorMao(x, y, s) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  ctx.fillStyle = "#ffffff"; ctx.strokeStyle = "#111"; ctx.lineWidth = 3;
  ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(0, 46); ctx.lineTo(11, 36); ctx.lineTo(19, 54); ctx.lineTo(27, 50); ctx.lineTo(19, 33); ctx.lineTo(34, 33); ctx.closePath();
  ctx.fill(); ctx.stroke(); ctx.restore();
}
function chamadaYouTube(t) {
  const c = D.cta; if (!c || t < c.t0) return;
  const { W, H } = D, T = D.tema, dt = t - c.t0;
  ctx.fillStyle = `rgba(0,0,0,${0.62 * easeOut(lin(dt, 0, 0.4))})`; ctx.fillRect(0, 0, W, H);
  const cy = H > W ? H * 0.27 : H * 0.42;   // no vertical, o texto sobe e o Vigia fica embaixo
  ctx.save();
  const ciC = cenaAtual(t);
  if (ciC >= 0 && D.cenas[ciC].vigia && W > H) ctx.translate(W * 0.16, 0);   // abre espaço para o Vigia em destaque
  ctx.textAlign = "center";
  // pergunta
  const a1 = easeOut(lin(dt, 0.1, 0.35));
  ctx.globalAlpha = a1; fonte(800, 58, T.fonte_texto); ctx.fillStyle = T.texto_legenda;
  ctx.shadowColor = "rgba(0,0,0,.8)"; ctx.shadowBlur = 16;
  // quebra o título em linhas que caibam em 88% da largura (o de baixo fica no lugar de sempre)
  const linhasT = [];
  for (const p of (c.titulo || "Gostou dessa história?").split(" ")) {
    const ult = linhasT.length ? linhasT[linhasT.length - 1] + " " + p : p;
    if (linhasT.length && ctx.measureText(ult).width <= W * 0.88) linhasT[linhasT.length - 1] = ult;
    else linhasT.push(p);
  }
  linhasT.forEach((l, i) => ctx.fillText(l, W / 2, cy - 150 - (linhasT.length - 1 - i) * 70 + (1 - a1) * 20));
  ctx.shadowBlur = 0;
  // botão
  const clique = c.clique ?? 1.35, inscrito = dt >= clique;
  const pop = back(lin(dt, 0.35, 0.35)) * (dt > clique && dt < clique + 0.15 ? 0.94 : 1);
  ctx.globalAlpha = Math.min(1, lin(dt, 0.35, 0.15));
  const bw = 600, bh = 130, bx = W / 2, by = cy;
  ctx.save(); ctx.translate(bx, by); ctx.scale(pop, pop);
  ctx.fillStyle = inscrito ? "#3a3a3a" : "#e62117";
  ctx.shadowColor = inscrito ? "rgba(0,0,0,.5)" : "rgba(230,33,23,.55)"; ctx.shadowBlur = 40;
  rr(-bw / 2, -bh / 2, bw, bh, bh / 2); ctx.fill(); ctx.shadowBlur = 0;
  fonte(800, 56, T.fonte_texto); ctx.fillStyle = "#fff"; ctx.textBaseline = "middle";
  ctx.fillText(inscrito ? (D.cta.botao_ok || "INSCRITO") : (D.cta.botao || "INSCREVER-SE"), -30, 4);
  const balanco = inscrito ? Math.sin((dt - clique) * 22) * 0.45 * Math.max(0, 1 - (dt - clique) / 0.9) : 0;
  sino(bw / 2 - 75, -4, 34, balanco, "#fff");
  ctx.restore(); ctx.textBaseline = "alphabetic";
  // brilho do clique
  if (inscrito && dt < clique + 0.5) {
    const k = lin(dt, clique, 0.5); ctx.strokeStyle = `rgba(255,255,255,${0.6 * (1 - k)})`; ctx.lineWidth = 5;
    rr(bx - bw / 2 - 20 * k, by - bh / 2 - 20 * k, bw + 40 * k, bh + 40 * k, bh); ctx.stroke();
  }
  // cursor chega e clica
  const c0 = Math.max(0.7, clique - 0.9);   // o cursor só aparece pouco antes do clique
  if (dt > c0 && dt < clique + 0.9) {
    const m = easeInOut(lin(dt, c0, clique - c0));
    const x = W * 0.86 + (bx + 120 - W * 0.86) * m, y = H * 0.62 + (by + 10 - H * 0.62) * m;
    cursorMao(x, y, dt > clique && dt < clique + 0.12 ? 1.25 : 1.4);
  }
  // canal
  const a3 = easeOut(lin(dt, 0.6, 0.4));
  ctx.globalAlpha = a3; fonte(700, 44, T.fonte_texto); ctx.fillStyle = T.destaque_legenda;
  ctx.fillText(c.canal || "@ovigia", W / 2, cy + 150);
  if (c.subtitulo) { fonte(500, 36, T.fonte_texto); ctx.fillStyle = T.texto_legenda; ctx.fillText(c.subtitulo, W / 2, cy + 205); }
  ctx.globalAlpha = 1; ctx.textAlign = "left"; ctx.restore();
}

// ------------------------------------------------------------------ vídeo nas cenas
// cada cena com vídeo tem os quadros em JPG; antes de desenhar, troca a imagem da cena pelo quadro do instante t
async function atualizarVideos(t) {
  for (const c of D.cenas || []) {
    const q = c.quadros;
    if (!q || t < c.t0 - 1.5 || t > c.t1 + 1.5) continue;
    const i = Math.max(0, Math.min(q.n - 1, Math.floor((t - c.t0) * q.fps + 1e-6)));
    if (c._qi === i) continue;
    const im = await carregarImg(q.dir + "/" + String(i + 1).padStart(5, "0") + ".jpg");
    if (im) { IMG["img:" + c.imagem] = im; c._qi = i; }
  }
}

// 13/11 (Ep. 09): entrada do episódio JUNTO com o Vigia — o nome escrito ao lado dele, sem corte para outro cartão.
// D.titulo_ep = {t0, t1, linhas: ["O VIGIA · EPISÓDIO 09", "O QUARTO", "DO ANDAR F"], vermelho: "ANDAR F", x}
function tituloEpisodio(t) {
  const T = D.titulo_ep; if (t < T.t0 || t > T.t1 + 1.2) return;
  const { W, H } = D, a = Math.min(easeOut(lin(t, T.t0, 1.4)), 1 - easeInOut(lin(t, T.t1, 1.2)));
  if (a <= 0) return;
  const x = W * (T.x ?? 0.56);
  ctx.save(); ctx.globalAlpha = a;
  const g = ctx.createLinearGradient(x - W * 0.08, 0, W, 0);      // escurece só atrás do texto
  g.addColorStop(0, "rgba(0,0,0,0)"); g.addColorStop(0.25, "rgba(0,0,0,.55)"); g.addColorStop(1, "rgba(0,0,0,.7)");
  ctx.fillStyle = g; ctx.fillRect(x - W * 0.08, 0, W, H);
  const [l0, ...grandes] = T.linhas, tam = Math.round(H * 0.105);
  ctx.textAlign = "left"; ctx.textBaseline = "alphabetic";
  ctx.font = `700 ${Math.round(H * 0.026)}px "Inter", sans-serif`; ctx.fillStyle = "#c9b9a0";
  ctx.fillText(l0.split("").join(" "), x, H * 0.38);
  ctx.fillStyle = "#b51b1b"; ctx.fillRect(x, H * 0.405, W * 0.3 * easeOut(lin(t, T.t0 + 0.4, 1.2)), Math.max(2, H * 0.004));
  ctx.font = `400 ${tam}px "Anton", sans-serif`; ctx.shadowColor = "rgba(0,0,0,.9)"; ctx.shadowBlur = 24;
  grandes.forEach((l, k) => {
    const y = H * 0.52 + k * tam * 1.05, ent = easeOut(lin(t, T.t0 + 0.6 + k * 0.5, 1.0));
    ctx.globalAlpha = a * ent;
    const v = T.vermelho && l.includes(T.vermelho) ? T.vermelho : null;
    if (v) {
      const antes = l.slice(0, l.indexOf(v)); ctx.fillStyle = "#f2ead8"; ctx.fillText(antes, x, y);
      ctx.fillStyle = "#d4302a"; ctx.fillText(v, x + ctx.measureText(antes).width, y);
    } else { ctx.fillStyle = "#f2ead8"; ctx.fillText(l, x, y); }
  });
  ctx.restore();
}
// ------------------------------------------------------------------ quadro
window.quadro = async function (t) {
  await atualizarVideos(t);
  quadroSinc(t);
};
function quadroSinc(t) {
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.textAlign = "left";
  if (D.modo === "cenas") {
    if (!GRAO) prepararCenas();
    cenas(t);
    const J = D.abertura_janela || (D.abertura_fim ? [0, D.abertura_fim] : null);
    if (!(J && t >= J[0] && t < J[1])) {
      if (!(D.cta && t >= D.cta.t0)) legendas(t);
      chamadaYouTube(t);
      const ciT = cenaAtual(t);
      // sem Vigia nas telas de texto e nas cenas marcadas "sem_vigia" (tensão/imersão): sai e volta junto com o corte
      const cT = ciT >= 0 ? D.cenas[ciT] : {};
      const semV = cT.tipo === "texto" || cT.sem_vigia || (D.vigia_padrao === false && !cT.com_vigia && !cT.vigia);
      // 13/11 (Ep. 09): o Vigia entra e sai JUNTO com a fusão da cena do abrigo (antes ele surgia de uma vez por cima
      // da imagem anterior ainda sumindo, e sumia de uma vez enquanto o abrigo ainda estava na tela)
      const cA = ciT > 0 ? D.cenas[ciT - 1] : null, emFusao = cT.entrada && cT.entrada !== "corte",
            dtF = cT.duracao_entrada || 0.5, pF = emFusao ? lin(t, cT.t0, dtF) : 1;
      const ehV = (x) => x && (x.vigia || x.com_vigia || (D.vigia_padrao !== false && x.tipo !== "texto" && !x.sem_vigia));
      let aV = 1;
      if (!semV && !ehV(cA)) aV = easeInOut(pF);                         // entrando no Vigia
      const saindo = semV && ehV(cA) && pF < 1;                          // saindo do Vigia para outra cena
      if (saindo) aV = 1 - easeInOut(pF);
      if ((!semV || saindo) || (D.cta && t >= D.cta.t0)) {
        const desenhaV = () => (D.avatar.tipo === "corpo" ? vigiaCorpo : vigiaCanto)(t);
        if (aV >= 0.999 || (D.cta && t >= D.cta.t0)) desenhaV();
        else if (aV > 0.001) {
          const VC = _canvas("camV", D.W, D.H), sC = ctx; VC.getContext("2d").clearRect(0, 0, D.W, D.H);
          ctx = VC.getContext("2d"); ctx.save();
          if (saindo) { const sv = D.cenas[ciT]; D.cenas[ciT] = cA; desenhaV(); D.cenas[ciT] = sv; } else desenhaV();
          ctx.restore(); ctx = sC;
          ctx.save(); ctx.globalAlpha = aV; ctx.drawImage(VC, 0, 0); ctx.restore();
        }
      }
    }
    if (D.titulo_ep) tituloEpisodio(t);
    const f = Math.min(lin(t, 0, 0.3), 1 - lin(t, D.duracao - 0.5, 0.5));
    if (f < 1) { ctx.fillStyle = `rgba(0,0,0,${1 - f})`; ctx.fillRect(0, 0, D.W, D.H); }
    return;
  }
  fundo(t); paineis(t); avatar(t); titulo(t);
  // vinheta e fades de início/fim
  const v = ctx.createRadialGradient(D.W / 2, D.H / 2, D.H * 0.3, D.W / 2, D.H / 2, D.H * 0.75);
  v.addColorStop(0, "rgba(0,0,0,0)"); v.addColorStop(1, "rgba(0,0,0,.55)"); ctx.fillStyle = v; ctx.fillRect(0, 0, D.W, D.H);
  const f = Math.min(lin(t, 0, 0.35), 1 - lin(t, D.duracao - 0.6, 0.6));
  if (f < 1) { ctx.fillStyle = `rgba(0,0,0,${1 - f})`; ctx.fillRect(0, 0, D.W, D.H); }
};
