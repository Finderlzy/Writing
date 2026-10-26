import puppeteer from "./deps/node_modules/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js";
const browser = await puppeteer.launch({ executablePath: "/usr/bin/google-chrome", headless: "new", args: ["--no-sandbox", "--hide-scrollbars"] });
const page = await browser.newPage();
await page.setViewport({ width: 1440, height: 900 });
page.on("console", (m) => console.log("console:" + m.type() + ":" + m.text().slice(0, 200)));
page.on("requestfailed", (r) => console.log("failed:" + r.url() + " " + r.failure()?.errorText));
await page.goto(process.argv[2], { waitUntil: "load", timeout: 30000 });
await new Promise((r) => setTimeout(r, 800));
console.log(await page.evaluate(() => {
  const sheets = [...document.styleSheets].map((s) => ({ href: s.href, rules: (() => { try { return s.cssRules.length; } catch (e) { return "err"; } })() }));
  const el = document.querySelector(".site-main");
  return JSON.stringify({ sheets, mainDisplay: el ? getComputedStyle(el).maxWidth : null, bodyFont: getComputedStyle(document.body).fontFamily, notFoundPos: document.querySelector(".not-found") ? getComputedStyle(document.querySelector(".not-found")).position : null });
}));
await browser.close();
