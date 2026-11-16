// Renderiza um cartão de capítulo 3D (cena.js) em MP4, quadro a quadro, com WebGL por software (SwiftShader) no
// Chromium sem tela, em paralelo (a cena é função do tempo, sem estado).
// Uso: node render_cartao.js '{"numero":1,"titulo":"…","ano":"…","cor":"vermelho","dur":7.6}' saida.mp4 [--workers 4] [--quadros a:b] [--previa t1,t2]
"use strict";
const { chromium } = require("playwright");
const http = require("http"), fs = require("fs"), path = require("path");
const { spawn, spawnSync } = require("child_process");

const a = process.argv.slice(2);
const cfg = JSON.parse(a[0]), saida = path.resolve(a[1]);
const opt = (n, d) => { const i = a.indexOf(n); return i >= 0 ? a[i + 1] : d; };
const WORKERS = +opt("--workers", 2), FPS = 30, DUR = cfg.dur || 7.6, N = Math.round(DUR * FPS);
cfg.dur = DUR; cfg.W = cfg.W || 1920; cfg.H = cfg.H || 1080;
const TIPOS = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".ttf": "font/ttf", ".woff2": "font/woff2", ".json": "application/json" };
const srv = http.createServer((req, res) => {
  const f = decodeURIComponent(req.url.split("?")[0]);
  fs.readFile(f, (e, b) => { if (e) { res.writeHead(404); return res.end(); } res.writeHead(200, { "Content-Type": TIPOS[path.extname(f)] || "application/octet-stream" }); res.end(b); });
});

async function pagina(browser, porta) {
  const p = await browser.newPage({ viewport: { width: cfg.W, height: cfg.H } });
  p.on("pageerror", (e) => console.error("erro na página:", e.message));
  p.on("console", (m) => { if (m.type() === "error") console.error("console:", m.text()); });
  await p.goto(`http://127.0.0.1:${porta}${path.join(__dirname, cfg.pagina || "index.html")}`);   // 16/11: cfg.pagina = "index_runa.html" (Ep. 11)
  await p.waitForFunction(() => window.pronto === true, null, { timeout: 60000 });
  await p.evaluate((c) => window.preparar(c), cfg);
  return p;
}

(async () => {
  await new Promise((r) => srv.listen(0, "127.0.0.1", r)); const porta = srv.address().port;
  // 16/11: "--use-angle=swiftshader" levava ~19 s por quadro; "swiftshader-webgl" ~3.5 s
  const browser = await chromium.launch({ args: ["--use-gl=angle", "--use-angle=swiftshader-webgl", "--enable-unsafe-swiftshader"] });
  const prev = opt("--previa", null);
  if (prev) {   // só alguns quadros soltos em JPEG (para conferir)
    const p = await pagina(browser, porta);
    for (const t of prev.split(",").map(Number)) {
      await p.evaluate((tt) => window.quadro(tt), t);
      fs.writeFileSync(saida.replace(/\.\w+$/, "") + `_${t}.jpg`, await p.screenshot({ type: "jpeg", quality: 93 }));
    }
    console.log("tempos (ms, soma):", JSON.stringify(await p.evaluate(() => window.tempos)));
    await browser.close(); srv.close(); return;
  }
  const [q0, q1] = (opt("--quadros", `0:${N}`)).split(":").map(Number);
  const tmp = fs.mkdtempSync("/tmp/cartao_"), partes = [], t0 = Date.now();
  const por = Math.ceil((q1 - q0) / WORKERS);
  await Promise.all(Array.from({ length: WORKERS }, async (_, k) => {
    const i0 = q0 + k * por, i1 = Math.min(q1, i0 + por); if (i0 >= i1) return;
    const arq = path.join(tmp, `p${k}.mp4`); partes[k] = arq;
    const p = await pagina(browser, porta);
    const ff = spawn("ffmpeg", ["-y", "-v", "error", "-f", "image2pipe", "-c:v", "mjpeg", "-r", String(FPS), "-i", "-",
      "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", arq], { stdio: ["pipe", "inherit", "inherit"] });
    for (let i = i0; i < i1; i++) {
      await p.evaluate((tt) => window.quadro(tt), i / FPS);
      const jpg = await p.screenshot({ type: "jpeg", quality: 93 });
      if (!ff.stdin.write(jpg)) await new Promise((r) => ff.stdin.once("drain", r));
      if (k === 0 && (i - i0) % 10 === 0) console.log(`  quadro ${i - i0}/${i1 - i0} (${((Date.now() - t0) / 1000).toFixed(0)} s)`);
    }
    ff.stdin.end(); await new Promise((r) => ff.on("close", r));
  }));
  const lista = path.join(tmp, "lista.txt"); fs.writeFileSync(lista, partes.filter(Boolean).map((p) => `file '${p}'`).join("\n"));
  spawnSync("ffmpeg", ["-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lista, "-c", "copy", "-movflags", "+faststart", saida], { stdio: "inherit" });
  fs.rmSync(tmp, { recursive: true, force: true });
  console.log(`ok ${saida} — ${q1 - q0} quadros em ${((Date.now() - t0) / 1000).toFixed(0)} s`);
  await browser.close(); srv.close();
})();
