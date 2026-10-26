// 1) 复制按钮真的把内容写进剪贴板；2) 订阅教程系列入口篇的系列导航；3) 深色模式对比度；4) 375px 首页卡片跳转
import puppeteer from "./deps/node_modules/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js";

const base = "http://127.0.0.1:8321/writing/";
const out = {};
const browser = await puppeteer.launch({
  executablePath: "/usr/bin/google-chrome",
  headless: "new",
  args: ["--no-sandbox", "--disable-dev-shm-usage", "--hide-scrollbars"],
});

// 复制按钮
{
  const page = await browser.newPage();
  const ctx = browser.defaultBrowserContext();
  await ctx.overridePermissions("http://127.0.0.1:8321", ["clipboard-read", "clipboard-write"]);
  await page.setViewport({ width: 1440, height: 900 });
  await page.goto(base + "blog/87557c89/", { waitUntil: "networkidle0" });
  const before = await page.evaluate(() => document.querySelector(".code-copy")?.textContent.trim());
  await page.click(".code-copy");
  await new Promise((r) => setTimeout(r, 300));
  const after = await page.evaluate(() => document.querySelector(".code-copy")?.textContent.trim());
  const clip = await page.evaluate(() => navigator.clipboard.readText().catch((e) => "ERR " + e));
  const code = await page.evaluate(() => document.querySelector("pre code")?.innerText);
  out.copy = { before, after, clipboard: clip, code: code?.slice(0, 60) };
  await page.close();
}

// 系列入口篇
{
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });
  await page.goto(base + "blog/subscribe-claude-quick/", { waitUntil: "networkidle0" });
  out.series = await page.evaluate(() => ({
    title: document.title,
    seriesLine: document.querySelector(".article-series-line")?.innerText.replace(/\s+/g, " "),
    next: document.querySelector(".series-next")?.innerText.replace(/\s+/g, " "),
    nextHref: document.querySelector(".series-next a")?.getAttribute("href"),
    neighbours: [...document.querySelectorAll(".neighbour")].map((a) => a.getAttribute("href") + " " + a.innerText.replace(/\s+/g, " ")),
    toc: document.querySelectorAll(".article-toc a").length,
    comments: !!document.querySelector(".comments"),
    say: document.querySelector(".say")?.innerText.slice(0, 40),
  }));
  await page.goto(base + "blog/subscribe-claude-quick-new/", { waitUntil: "networkidle0" });
  out.seriesNew = await page.evaluate(() => ({
    seriesLine: document.querySelector(".article-series-line")?.innerText.replace(/\s+/g, " "),
    next: document.querySelector(".series-next")?.innerText.replace(/\s+/g, " "),
  }));
  await page.close();
}

// 无 description 的文章
{
  const page = await browser.newPage();
  await page.goto(base + "blog/87557c89/", { waitUntil: "networkidle0" });

  out.noDescription = await page.evaluate(() => ({ say: document.querySelector(".say"), sayCount: document.querySelectorAll(".say").length }));
  await page.goto(base + "thoughts/48b08046/", { waitUntil: "networkidle0" });
  out.aveMujica = await page.evaluate(() => ({
    giants: [...document.querySelectorAll(".giant")].map((e) => e.innerText),
    say: document.querySelector(".say")?.innerText?.slice(0, 30) ?? null,
    minutes: document.querySelector(".ring b")?.innerText,
  }));
  await page.goto(base + "thoughts/a452588a/", { waitUntil: "networkidle0" });
  out.clannad = await page.evaluate(() => ({
    giants: [...document.querySelectorAll(".giant")].map((e) => e.innerText),
    bodyStart: document.querySelector(".article-body")?.innerText.slice(0, 80),
    blockquotes: document.querySelectorAll(".article-body blockquote").length,
    dateNote: document.querySelector(".article-body")?.innerText.match(/写于|更新于/g),
    minutes: document.querySelector(".ring b")?.innerText,
  }));
  await page.goto(base + "opus/0b4224e7/", { waitUntil: "networkidle0" });
  out.heikuang = await page.evaluate(() => ({
    giants: [...document.querySelectorAll(".giant")].map((e) => e.innerText),
    minutes: document.querySelector(".ring b")?.innerText,
    words: document.querySelector(".article-body")?.innerText.replace(/\s/g, "").length,
    kicker: document.querySelector(".kicker")?.innerText.replace(/\s+/g, " "),
    bodyHasDateNote: /^\s*(写于|更新于)/.test(document.querySelector(".article-body")?.innerText || ""),
  }));
  await page.close();
}

// 深色模式对比度
{
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });
  await page.emulateMediaFeatures([{ name: "prefers-color-scheme", value: "dark" }]);
  const pages = { home: "", posts: "posts/", post: "opus/0b4224e7/", tutorial: "blog/87557c89/", nf: "nope/" };
  out.dark = {};
  for (const [name, u] of Object.entries(pages)) {
    await page.goto(base + u, { waitUntil: "networkidle0" });
    out.dark[name] = await page.evaluate(() => {
      const parse = (c) => {
        const m = c.match(/rgba?\(([^)]+)\)/);
        if (!m) return null;
        const p = m[1].split(",").map(Number);
        return { r: p[0], g: p[1], b: p[2], a: p[3] === undefined ? 1 : p[3] };
      };
      const lum = ({ r, g, b }) => {
        const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; };
        return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
      };
      const bgOf = (el) => {
        let cur = el;
        while (cur) {
          const c = getComputedStyle(cur).backgroundColor;
          const p = parse(c);
          if (p && p.a > 0.5) return p;
          cur = cur.parentElement;
        }
        return { r: 255, g: 255, b: 255, a: 1 };
      };
      const ratio = (el) => {
        const fg = parse(getComputedStyle(el).color);
        const bg = bgOf(el);
        if (!fg) return null;
        const l1 = lum(fg), l2 = lum(bg);
        const hi = Math.max(l1, l2), lo = Math.min(l1, l2);
        return Math.round(((hi + 0.05) / (lo + 0.05)) * 100) / 100;
      };
      const pick = (sel) => {
        const el = document.querySelector(sel);
        return el ? { sel, text: el.innerText.slice(0, 18).replace(/\n/g, " "), ratio: ratio(el) } : null;
      };
      const items = [".site-nav a", "h1", ".post-title", ".kicker .date", ".article-body p", ".items .t strong", ".items .d", ".month-label", ".filter-button", ".say", ".article-body td", ".article-body th", ".series-next", ".not-found-say", ".site-footer-links"]
        .map(pick)
        .filter(Boolean);
      const borders = [...document.querySelectorAll(".neighbour, .back-link, .say, .bubble, .line, .window")].slice(0, 4).map((el) => ({ cls: el.className, border: getComputedStyle(el).borderTopColor, shadow: getComputedStyle(el).boxShadow.slice(0, 40) }));
      return { low: items.filter((i) => i.ratio !== null && i.ratio < 4.5), count: items.length, borders, bg: getComputedStyle(document.body).backgroundColor };
    });
  }
  await page.close();
}

await browser.close();
console.log(JSON.stringify(out, null, 1));
