// 截图：node shot.mjs <url> <out.png> [width] [height] [dark|light] [reduced]
import puppeteer from "./deps/node_modules/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js";

const [url, out, width = "1440", height = "900", scheme = "light", motion = "no-preference"] = process.argv.slice(2);
const browser = await puppeteer.launch({
  executablePath: "/usr/bin/google-chrome",
  headless: "new",
  args: ["--no-sandbox", "--disable-dev-shm-usage", "--hide-scrollbars", "--font-render-hinting=none"],
});
const page = await browser.newPage();
await page.setViewport({ width: Number(width), height: Number(height), deviceScaleFactor: 1 });
await page.emulateMediaFeatures([
  { name: "prefers-color-scheme", value: scheme },
  { name: "prefers-reduced-motion", value: motion },
]);
const requests = [];
page.on("request", (req) => requests.push(req.url()));
await page.goto(url, { waitUntil: "networkidle0", timeout: 45000 });
await page.evaluate(() => document.fonts.ready);
await new Promise((r) => setTimeout(r, 400));
await page.screenshot({ path: out, fullPage: true });
console.log(JSON.stringify({ out, requests }, null, 0));
await browser.close();
