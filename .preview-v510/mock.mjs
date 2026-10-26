// 样稿截图：node mock.mjs <out.png> <home|post|all|404> [width] [dark|light]
import puppeteer from "./deps/node_modules/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js";

const [out, view = "home", width = "1440", scheme = "light"] = process.argv.slice(2);
const url = "file:///home/finderzly/Workspace/writing/开发文档/设计样稿/5.1.0-首页与文章页.html";
const browser = await puppeteer.launch({
  executablePath: "/usr/bin/google-chrome",
  headless: "new",
  args: ["--no-sandbox", "--disable-dev-shm-usage", "--hide-scrollbars"],
});
const page = await browser.newPage();
await page.setViewport({ width: Number(width), height: 900, deviceScaleFactor: 1 });
await page.emulateMediaFeatures([{ name: "prefers-color-scheme", value: scheme }]);
await page.goto(url, { waitUntil: "networkidle0", timeout: 45000 }).catch(() => {});
await page.evaluate(() => document.fonts.ready);
if (scheme === "dark") {
  const d = await page.$('#scheme-dark, [data-scheme="dark"], button[data-theme="dark"]');
  if (d) await d.click().catch(() => {});
}
await new Promise((r) => setTimeout(r, 300));
await page.evaluate((v) => {
  for (const el of document.querySelectorAll("[id^='v-']")) el.hidden = el.id !== "v-" + v;
}, view);
await new Promise((r) => setTimeout(r, 300));
await page.screenshot({ path: out, fullPage: true });
console.log(JSON.stringify({ out, view }));
await browser.close();
