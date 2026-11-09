// Motor do estilo "avatar + painel animado".
// Desenha o quadro do instante t (função pura de t) a partir da linha do tempo D gerada pelo gerar.py.
"use strict";
const cv = document.getElementById("tela");
const ctx = cv.getContext("2d");
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
  const fams = [D.tema.fonte_titulo, D.tema.fonte_ui, D.tema.fonte_papel, D.tema.fonte_texto, "Cinzel", "Special Elite", "Anton"];
  for (const f of fams) for (const p of ["400", "500", "700", "800"]) { try { await document.fonts.load(`${p} 40px "${f}"`); } catch (e) {} }
  const lista = [];
  for (const nome of Object.keys(D.avatar.poses)) lista.push(["pose:" + nome, D.avatar.base + nome + ".png"]);
  for (const p of D.paineis || []) if (p.imagem) lista.push(["img:" + p.imagem, p.imagem]);
  for (const c of D.cenas || []) { lista.push(["img:" + c.imagem, c.imagem]); if (c.revelar && c.revelar.clara) lista.push(["img:" + c.revelar.clara, c.revelar.clara]); }
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
  const est = c.estilo === "impacto" ? { fonte: "Cinzel", peso: 700, tam: 118 } : c.estilo === "maquina" ? { fonte: "Special Elite", peso: 400, tam: 56 } : {};
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
    const sb = Math.max(D.W / im.width, D.H / im.height) * 1.1;
    ctx.drawImage(im, (D.W - im.width * sb) / 2, (D.H - im.height * sb) / 2, im.width * sb, im.height * sb);
    ctx.filter = "none";
    const z = (c.zoom ? c.zoom[0] + (c.zoom[1] - c.zoom[0]) * easeInOut(lin(t, c.t0, Math.max(0.5, c.t1 - c.t0))) : 1);
    const sc = Math.min(D.W / im.width, D.H / im.height) * z, w = im.width * sc, h = im.height * sc;
    ctx.shadowColor = "rgba(0,0,0,.8)"; ctx.shadowBlur = 50;
    ctx.drawImage(im, (D.W - w) / 2, (D.H - h) / 2, w, h); ctx.restore();
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

function cenas(t) {
  const { W, H } = D, T = D.tema;
  ctx.fillStyle = "#000"; ctx.fillRect(0, 0, W, H);
  const i = cenaAtual(t);
  if (i < 0) return;
  const c = D.cenas[i], ant = D.cenas[i - 1];
  const dt = c.duracao_entrada || 0.5;
  if (c.entrada === "fundir" && ant && t < c.t0 + dt) {
    desenharCena(ant, t); desenharCena(c, t, easeInOut(lin(t, c.t0, dt)));
  } else if (c.entrada === "preto" && t < c.t0 + dt) {
    desenharCena(c, t, easeInOut(lin(t, c.t0, dt)));
  } else desenharCena(c, t);
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
  const halo = ctx.createRadialGradient(cx, topoCabeca + alvo * 0.8, 10, cx, topoCabeca + alvo * 0.8, C.w * 0.95);
  halo.addColorStop(0, alpha(T.halo, 0.28 + 0.12 * e)); halo.addColorStop(1, alpha(T.halo, 0));
  ctx.fillStyle = halo; ctx.fillRect(cx - C.w, topoCabeca - C.w * 0.3, C.w * 2, C.w * 2);
  const desenha = (nome, a, pop, dx) => {
    const im = IMG["pose:" + nome], m = D.avatar.poses[nome];
    if (!im || !m) return;
    const s = alvo / m.largura_cabeca * pop * (1 + 0.016 * e) * (1 + 0.005 * Math.sin(t * 1.9));
    const w = im.width * s, h = im.height * s;
    MASCARA.width = Math.ceil(w) + 40; MASCARA.height = Math.ceil(h) + 40;
    const g = MASCARA.getContext("2d");
    g.clearRect(0, 0, MASCARA.width, MASCARA.height); g.imageSmoothingQuality = "high";
    g.filter = "brightness(1.22) contrast(1.08) saturate(1.06)";
    g.shadowColor = alpha(T.contorno || "#a9d6c4", 0.5); g.shadowBlur = 12;
    g.drawImage(im, 20, 20, w, h); g.filter = "none"; g.shadowBlur = 0;
    const y = topoCabeca - m.topo * s - 20 - 5 * e + Math.sin(t * 1.4) * 2;
    const x = cx - m.centro_x * s - 20 + dx;
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
  ctx.fillText(c.titulo || "Gostou dessa história?", W / 2, cy - 150 + (1 - a1) * 20);
  ctx.shadowBlur = 0;
  // botão
  const clique = 1.35, inscrito = dt >= clique;
  const pop = back(lin(dt, 0.35, 0.35)) * (dt > clique && dt < clique + 0.15 ? 0.94 : 1);
  ctx.globalAlpha = Math.min(1, lin(dt, 0.35, 0.15));
  const bw = 600, bh = 130, bx = W / 2, by = cy;
  ctx.save(); ctx.translate(bx, by); ctx.scale(pop, pop);
  ctx.fillStyle = inscrito ? "#3a3a3a" : "#e62117";
  ctx.shadowColor = inscrito ? "rgba(0,0,0,.5)" : "rgba(230,33,23,.55)"; ctx.shadowBlur = 40;
  rr(-bw / 2, -bh / 2, bw, bh, bh / 2); ctx.fill(); ctx.shadowBlur = 0;
  fonte(800, 56, T.fonte_texto); ctx.fillStyle = "#fff"; ctx.textBaseline = "middle";
  ctx.fillText(inscrito ? "INSCRITO" : "INSCREVER-SE", -30, 4);
  const balanco = inscrito ? Math.sin((dt - clique) * 22) * 0.45 * Math.max(0, 1 - (dt - clique) / 0.9) : 0;
  sino(bw / 2 - 75, -4, 34, balanco, "#fff");
  ctx.restore(); ctx.textBaseline = "alphabetic";
  // brilho do clique
  if (inscrito && dt < clique + 0.5) {
    const k = lin(dt, clique, 0.5); ctx.strokeStyle = `rgba(255,255,255,${0.6 * (1 - k)})`; ctx.lineWidth = 5;
    rr(bx - bw / 2 - 20 * k, by - bh / 2 - 20 * k, bw + 40 * k, bh + 40 * k, bh); ctx.stroke();
  }
  // cursor chega e clica
  if (dt > 0.7 && dt < clique + 0.9) {
    const m = easeInOut(lin(dt, 0.7, clique - 0.7));
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

// ------------------------------------------------------------------ quadro
window.quadro = function (t) {
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.textAlign = "left";
  if (D.modo === "cenas") {
    if (!GRAO) prepararCenas();
    cenas(t);
    const J = D.abertura_janela || (D.abertura_fim ? [0, D.abertura_fim] : null);
    if (!(J && t >= J[0] && t < J[1])) {
      if (!(D.cta && t >= D.cta.t0)) legendas(t);
      chamadaYouTube(t);
      const ciT = cenaAtual(t);
      if (!(ciT >= 0 && D.cenas[ciT].tipo === "texto")) (D.avatar.tipo === "corpo" ? vigiaCorpo : vigiaCanto)(t);
    }
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
