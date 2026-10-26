// 局部截图：node crop.mjs <url> <out.png> <selector> [width] [dark|light] [scrollY]
import puppeteer from "./deps/node_modules/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js";
const [url, out, sel, width = "1440", scheme = "light", y = "0"] = process.argv.slice(2);
const browser = await puppeteer.launch({ executablePath: "/usr/bin/google-chrome", headless: "new", args: ["--no-sandbox", "--hide-scrollbars"] });
const page = await browser.newPage();
await page.setViewport({ width: Number(width), height: 1000 });
await page.emulateMediaFeatures([{ name: "prefers-color-scheme", value: scheme }]);
await page.goto(url, { waitUntil: "networkidle0", timeout: 45000 });
await page.evaluate(() => document.fonts.ready);
if (Number(y)) await page.evaluate((yy) => window.scrollTo(0, yy), Number(y));
await new Promise((r) => setTimeout(r, 400));
const el = await page.$(sel);
if (!el) { console.log("selector not found: " + sel); process.exit(2); }
await el.screenshot({ path: out });
console.log(JSON.stringify({ out }));
await browser.close();
