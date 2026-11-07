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
  const fams = [D.tema.fonte_titulo, D.tema.fonte_ui, D.tema.fonte_papel, D.tema.fonte_texto];
  for (const f of fams) for (const p of ["400", "500", "700", "800"]) { try { await document.fonts.load(`${p} 40px "${f}"`); } catch (e) {} }
  const lista = [];
  for (const nome of Object.keys(D.avatar.poses)) lista.push(["pose:" + nome, D.avatar.base + nome + ".png"]);
  for (const p of D.paineis) if (p.imagem) lista.push(["img:" + p.imagem, p.imagem]);
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

// ------------------------------------------------------------------ quadro
window.quadro = function (t) {
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.textAlign = "left";
  fundo(t); paineis(t); avatar(t); titulo(t);
  // vinheta e fades de início/fim
  const v = ctx.createRadialGradient(D.W / 2, D.H / 2, D.H * 0.3, D.W / 2, D.H / 2, D.H * 0.75);
  v.addColorStop(0, "rgba(0,0,0,0)"); v.addColorStop(1, "rgba(0,0,0,.55)"); ctx.fillStyle = v; ctx.fillRect(0, 0, D.W, D.H);
  const f = Math.min(lin(t, 0, 0.35), 1 - lin(t, D.duracao - 0.6, 0.6));
  if (f < 1) { ctx.fillStyle = `rgba(0,0,0,${1 - f})`; ctx.fillRect(0, 0, D.W, D.H); }
};
