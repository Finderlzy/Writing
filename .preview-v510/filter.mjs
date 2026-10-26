// 筛选、跳转、404、动态效果的检查
import puppeteer from "./deps/node_modules/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js";

const base = "http://127.0.0.1:8321/writing/";
const out = {};
const browser = await puppeteer.launch({
  executablePath: "/usr/bin/google-chrome",
  headless: "new",
  args: ["--no-sandbox", "--disable-dev-shm-usage", "--hide-scrollbars"],
});

async function open(url, opts = {}) {
  const page = await browser.newPage();
  await page.setViewport({ width: opts.width || 1440, height: 900 });
  await page.emulateMediaFeatures([
    { name: "prefers-color-scheme", value: opts.scheme || "light" },
    { name: "prefers-reduced-motion", value: opts.motion || "no-preference" },
  ]);
  await page.goto(url, { waitUntil: "networkidle0", timeout: 45000 });
  await page.evaluate(() => document.fonts.ready);
  return page;
}

// 1. 首页列表条数与博客/作品篇数
{
  const page = await open(base);
  const home = await page.evaluate(() => ({
    items: document.querySelectorAll(".archive-list .article-item, .list .items li, .items li").length,
    count: document.querySelector(".count b")?.textContent.trim(),
    headline: document.querySelector(".bubble h1")?.innerText.replace(/\s+/g, " ").trim(),
    h1: [...document.querySelectorAll("h1")].map((e) => e.innerText),
    body: document.body.innerText.includes("首页"),
    monthGroups: document.querySelectorAll(".month").length,
  }));
  await page.goto(base + "posts/", { waitUntil: "networkidle0" });
  const posts = await page.evaluate(() => ({
    total: document.querySelector(".hero-lead-count")?.textContent,
    items: Array.from(document.querySelectorAll(".article-item")).map((li) => ({
      stage: li.dataset.stage,
      text: li.querySelector(".t")?.innerText.replace(/\s+/g, " "),
    })),
    filtersHidden: document.querySelector(".filters")?.hidden,
  }));
  out.home = home;
  out.posts = { total: posts.total, count: posts.items.length, filtersHidden: posts.filtersHidden };

  // 2. 筛选：思考 + 学习
  await page.goto(base + "posts/?stage=" + encodeURIComponent("思考") + "&tag=" + encodeURIComponent("学习"), { waitUntil: "networkidle0" });
  await new Promise((r) => setTimeout(r, 300));
  out.filterThinkStudy = await page.evaluate(() => ({
    visible: [...document.querySelectorAll(".article-item")].filter((li) => !li.hidden).length,
    pressed: [...document.querySelectorAll(".filter-button[aria-pressed='true']")].map((b) => b.textContent.trim()),
    monthsVisible: [...document.querySelectorAll(".month")].filter((m) => !m.hidden).length,
    url: location.search,
    summary: document.querySelector(".filter-summary")?.innerText,
  }));
  // 3. 空结果：作品 + 学习
  await page.goto(base + "posts/?stage=" + encodeURIComponent("作品") + "&tag=" + encodeURIComponent("学习"), { waitUntil: "networkidle0" });
  await new Promise((r) => setTimeout(r, 300));
  out.filterEmpty = await page.evaluate(() => ({
    visible: [...document.querySelectorAll(".article-item")].filter((li) => !li.hidden).length,
    monthsVisible: [...document.querySelectorAll(".month")].filter((m) => !m.hidden).length,
    emptyShown: (() => { const e = document.querySelector(".empty-result"); return e ? !e.hidden : null; })(),
    emptyText: document.querySelector(".empty-result")?.innerText,
  }));
  // 4. 点按钮筛选：首页卡片“初稿”
  await page.goto(base, { waitUntil: "networkidle0" });
  const cardHref = await page.evaluate(() => [...document.querySelectorAll(".line .path a, .line a")].map((a) => a.getAttribute("href")));
  out.cardLinks = cardHref;
  await page.goto(base + "posts/?stage=" + encodeURIComponent("初稿"), { waitUntil: "networkidle0" });
  await new Promise((r) => setTimeout(r, 300));
  out.filterDraft = await page.evaluate(() => ({
    visible: [...document.querySelectorAll(".article-item")].filter((li) => !li.hidden).length,
  }));
  await page.close();
}

// 5. 首页卡片跳转：点“思考”chip
{
  const page = await open(base);
  const links = await page.$$(".line .path a");
  const hrefs = [];
  for (const a of links) hrefs.push(await page.evaluate((el) => el.href, a));
  out.heroCardHrefs = hrefs;
  await page.close();
}

// 6. 404
{
  const page = await open(base + "nope/");
  out.notFound = await page.evaluate(() => ({
    title: document.title,
    h: document.querySelector(".not-found h1, h1")?.innerText,
    giant: document.querySelector(".not-found .giant")?.innerText,
    links: [...document.querySelectorAll(".back-link")].map((a) => a.getAttribute("href")),
  }));
  await page.close();
}

// 7. 旧链接跳转
{
  const page = await open(base + "tech/subscribe-claude-quick/");
  await page.waitForNavigation({ timeout: 10000 }).catch(() => {});
  await new Promise((r) => setTimeout(r, 800));
  out.redirect = { finalUrl: page.url(), title: await page.title() };
  await page.close();
}

// 8. 减少动态效果：悬停卡片不动
{
  const page = await open(base + "blog/residential-ip-test/", { motion: "reduce" });
  const sel = ".neighbour.next";
  const before = await page.evaluate((s) => getComputedStyle(document.querySelector(s)).transform, sel);
  await page.hover(sel);
  await new Promise((r) => setTimeout(r, 300));
  const after = await page.evaluate((s) => ({ t: getComputedStyle(document.querySelector(s)).transform, sh: getComputedStyle(document.querySelector(s)).boxShadow }), sel);
  const transition = await page.evaluate((s) => getComputedStyle(document.querySelector(s)).transitionProperty, sel);
  out.reducedMotionNeighbour = { before, after, transition };
  await page.close();
}
{
  const page = await open(base + "blog/residential-ip-test/", { motion: "no-preference" });
  const sel = ".neighbour.next";
  const before = await page.evaluate((s) => getComputedStyle(document.querySelector(s)).transform, sel);
  await page.hover(sel);
  await new Promise((r) => setTimeout(r, 400));
  const after = await page.evaluate((s) => getComputedStyle(document.querySelector(s)).transform, sel);
  out.normalMotionNeighbour = { before, after };
  await page.close();
}
{
  const page = await open(base, { motion: "reduce" });
  const sel = ".line";
  const before = await page.evaluate((s) => getComputedStyle(document.querySelector(s)).transform, sel);
  await page.hover(sel);
  await new Promise((r) => setTimeout(r, 300));
  const after = await page.evaluate((s) => getComputedStyle(document.querySelector(s)).transform, sel);
  out.reducedMotionLine = { before, after };
  await page.close();
}

await browser.close();
console.log(JSON.stringify(out, null, 1));
