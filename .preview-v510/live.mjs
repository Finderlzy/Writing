import puppeteer from "./deps/node_modules/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js";
const browser = await puppeteer.launch({ executablePath: "/usr/bin/google-chrome", headless: "new", args: ["--no-sandbox", "--hide-scrollbars"] });
const page = await browser.newPage();
await page.setViewport({ width: 1440, height: 900 });
const reqs = [];
page.on("request", (r) => reqs.push(r.url()));
const results = {};
for (const [name, url] of Object.entries({
  home: "https://finderlzy.github.io/writing/",
  post: "https://finderlzy.github.io/writing/opus/0b4224e7/",
  old: "https://finderlzy.github.io/writing/tech/subscribe-claude-quick/",
  nf: "https://finderlzy.github.io/writing/no-such-page-xyz/",
})) {
  reqs.length = 0;
  const resp = await page.goto(url, { waitUntil: "networkidle0", timeout: 45000 });
  const info = await page.evaluate(() => ({
    title: document.title,
    url: location.href,
    h1: document.querySelector("h1")?.innerText.replace(/\s+/g, " ").slice(0, 40),
    giant: [...document.querySelectorAll(".giant")].map((e) => e.innerText).slice(0, 3),
    sheets: [...document.styleSheets].map((s) => s.href && s.href.replace("https://finderlzy.github.io", "")),
    fontOk: document.fonts.check('900 2rem "Noto Sans SC"'),
    count: document.querySelector(".count b")?.innerText,
    say: document.querySelector(".say") ? true : false,
    items: document.querySelectorAll(".article-item").length,
  }));
  results[name] = { status: resp && resp.status(), ...info, offsiteFonts: reqs.filter((r) => /fonts\.(googleapis|gstatic)/.test(r)) };
}
console.log(JSON.stringify(results, null, 1));
await page.goto("https://finderlzy.github.io/writing/", { waitUntil: "networkidle0" });
await page.screenshot({ path: "live-home.png", fullPage: false });
await browser.close();
