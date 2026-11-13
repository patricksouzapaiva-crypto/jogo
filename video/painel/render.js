// Renderiza a linha do tempo em MP4 (sem áudio) com Chromium headless em paralelo.
// Uso: node render.js linha_do_tempo.json saida.mp4 [--workers 4] [--rascunho] [--quadros i0:i1]
// --quadros: desenha só esse trecho (ex.: refazer o começo de um vídeo pronto e emendar)
"use strict";
const { chromium } = require("playwright");
const http = require("http");
const fs = require("fs");
const path = require("path");
const { spawn, spawnSync } = require("child_process");

const args = process.argv.slice(2);
const entrada = path.resolve(args[0]), saida = path.resolve(args[1]);
const W_ARG = args.indexOf("--workers");
const WORKERS = W_ARG >= 0 ? +args[W_ARG + 1] : 4;
const RASCUNHO = args.includes("--rascunho");
const Q_ARG = args.indexOf("--quadros");
const D = JSON.parse(fs.readFileSync(entrada, "utf8"));

const TIPOS = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".woff2": "font/woff2", ".json": "application/json" };
const servidor = http.createServer((req, res) => {
  const f = decodeURIComponent(req.url.split("?")[0]);
  fs.readFile(f, (err, buf) => {
    if (err) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { "Content-Type": TIPOS[path.extname(f).toLowerCase()] || "application/octet-stream" });
    res.end(buf);
  });
});

async function trabalhador(browser, porta, i0, i1, arq) {
  const escala = RASCUNHO ? 0.5 : 1;
  const page = await browser.newPage({ viewport: { width: Math.round(D.W * escala), height: Math.round(D.H * escala) } });
  page.on("pageerror", (e) => console.error("erro na página:", e.message));
  await page.goto(`http://127.0.0.1:${porta}${path.join(__dirname, "pagina", "index.html")}`);
  await page.evaluate((d) => window.preparar(d), D);
  const ff = spawn("ffmpeg", ["-y", "-v", "error", "-f", "image2pipe", "-c:v", "mjpeg", "-r", String(D.fps), "-i", "-",
    ...(RASCUNHO ? ["-vf", `scale=${D.W / 2}:${D.H / 2}`] : []),
    "-c:v", "libx264", "-preset", RASCUNHO ? "veryfast" : "medium", "-crf", "17", "-pix_fmt", "yuv420p", arq], { stdio: ["pipe", "inherit", "inherit"] });
  for (let i = i0; i < i1; i++) {
    const b64 = await page.evaluate(async (t) => { await window.quadro(t); return document.getElementById("tela").toDataURL("image/jpeg", 0.95).split(",")[1]; }, i / D.fps);
    const buf = Buffer.from(b64, "base64");
    if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once("drain", r));
  }
  ff.stdin.end();
  await new Promise((r) => ff.on("close", r));
  await page.close();
}

(async () => {
  await new Promise((r) => servidor.listen(0, "127.0.0.1", r));
  const porta = servidor.address().port;
  const browser = await chromium.launch({ args: ["--disable-web-security"] });
  const total = Math.ceil(D.duracao * D.fps);
  const [q0, q1] = Q_ARG >= 0 ? args[Q_ARG + 1].split(":").map(Number) : [0, total];
  const n = Math.min(q1, total) - q0, por = Math.ceil(n / WORKERS);
  const tmp = fs.mkdtempSync(path.join(require("os").tmpdir(), "painel_"));
  const partes = [];
  const t0 = Date.now();
  await Promise.all(Array.from({ length: WORKERS }, (_, k) => {
    const i0 = q0 + k * por, i1 = Math.min(q0 + n, i0 + por);
    if (i0 >= i1) return null;
    const arq = path.join(tmp, `parte_${k}.mp4`); partes[k] = arq;
    return trabalhador(browser, porta, i0, i1, arq);
  }));
  await browser.close(); servidor.close();
  const lista = path.join(tmp, "lista.txt");
  fs.writeFileSync(lista, partes.filter(Boolean).map((p) => `file '${p}'`).join("\n"));
  spawnSync("ffmpeg", ["-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lista, "-c", "copy", saida], { stdio: "inherit" });
  console.log(`vídeo: ${saida} (${n} quadros em ${((Date.now() - t0) / 1000).toFixed(0)} s)`);
})();
