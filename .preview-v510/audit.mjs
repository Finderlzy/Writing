// 批量检查：node audit.mjs <base> [width] [0|1 深色]
// 1) 每一页 scrollWidth 是否等于视口宽；2) 网络请求里有没有境外字体服务；3) 字体体积合计
import fs from "node:fs";
import path from "node:path";
import puppeteer from "./deps/node_modules/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js";

const base = process.argv[2] || "http://127.0.0.1:8321/writing";
const width = Number(process.argv[3] || 375);
const scheme = process.argv[4] === "1" ? "dark" : "light";

const site = path.resolve("..", "site");
const urls = [];
(function walk(dir) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) {
      if (e.name === "assets") continue;
      walk(p);
    } else if (e.name === "index.html") {
      urls.push(path.relative(site, path.dirname(p)).split(path.sep).join("/"));
    }
  }
})(site);
const redirects = new Set(["tech/subscribe-claude-quick"]);
const list = [".", "posts/", "404.html", ...urls.filter((u) => u && u !== "posts" && !redirects.has(u)).map((u) => u + "/")];

const browser = await puppeteer.launch({
  executablePath: "/usr/bin/google-chrome",
  headless: "new",
  args: ["--no-sandbox", "--disable-dev-shm-usage", "--hide-scrollbars"],
});
const page = await browser.newPage();
await page.setViewport({ width, height: 900 });
await page.emulateMediaFeatures([{ name: "prefers-color-scheme", value: scheme }]);
// giscus 是第三方 iframe，挡住它，免得本机网络慢时一直等
await page.setRequestInterception(true);
page.on("request", (req) => {
  if (/giscus\.app|github\.com/.test(req.url())) req.abort();
  else req.continue();
});
const requests = [];
page.on("request", (r) => requests.push(r.url()));
const bad = [];
const fontSeen = new Set();
for (const u of list) {
  const url = base + "/" + u;
  requests.length = 0;
  try {
    const resp = await page.goto(url, { waitUntil: "load", timeout: 30000 });
    await page.evaluate(() => document.fonts.ready).catch(() => {});
    const m = await page.evaluate(() => {
      const vw = document.documentElement.clientWidth;
      const wide = [...document.querySelectorAll("body *")]
        .filter((el) => el.getBoundingClientRect().right > vw + 1)
        .slice(0, 4)
        .map((el) => el.tagName + "." + (typeof el.className === "string" ? el.className : "") + "@" + Math.round(el.getBoundingClientRect().right));
      return {
        sw: document.documentElement.scrollWidth,
        cw: vw,
        body: document.body.scrollWidth,
        wide,
      };
    });
    const offsite = requests.filter((r) => /fonts\.googleapis\.com|fonts\.gstatic\.com|typekit|cdn\.jsdelivr|unpkg\.com/.test(r));
    requests.filter((r) => r.includes("/assets/fonts/")).forEach((f) => fontSeen.add(f));
    if (m.sw > m.cw || offsite.length) bad.push({ url, ...m, offsite, status: resp ? resp.status() : null });
  } catch (e) {
    bad.push({ url, error: String(e).slice(0, 120) });
  }
}
await browser.close();

const fontDir = path.join(site, "assets", "fonts");
let total = 0;
const sizes = {};
for (const f of fs.readdirSync(fontDir)) {
  const s = fs.statSync(path.join(fontDir, f)).size;
  sizes[f] = s;
  total += s;
}
console.log(JSON.stringify({ scheme, width, pages: list.length, bad, fonts: sizes, fontTotal: total, fontRequests: [...fontSeen] }, null, 1));
