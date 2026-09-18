(function () {
  var BUSUANZI_SRC = "https://busuanzi.ibruce.info/busuanzi/2.3/busuanzi.pure.mini.js";
  var scriptLoaded = false;

  function ensureBusuanziScript() {
    if (scriptLoaded || document.querySelector('script[src*="busuanzi"]')) {
      return;
    }
    var script = document.createElement("script");
    script.src = BUSUANZI_SRC;
    script.async = true;
    script.referrerPolicy = "no-referrer-when-downgrade";
    document.head.appendChild(script);
    scriptLoaded = true;
  }

  function injectCounterDOM() {
    var footerMeta = document.querySelector(".md-footer-meta__inner");
    if (!footerMeta) {
      return;
    }
    var existing = document.getElementById("site-busuanzi-counter");
    if (existing) {
      return;
    }

    var counterDiv = document.createElement("div");
    counterDiv.id = "site-busuanzi-counter";
    counterDiv.className = "md-footer-busuanzi";
    counterDiv.style.fontSize = "0.64rem";
    counterDiv.style.color = "var(--md-footer-fg-color--lighter, #888)";
    counterDiv.style.padding = "0.4rem 0";
    counterDiv.style.margin = "auto 0.6rem";
    counterDiv.style.textAlign = "right";

    counterDiv.innerHTML =
      '本站总访问量 <span id="busuanzi_value_site_pv">--</span> 次 · ' +
      '总访客数 <span id="busuanzi_value_site_uv">--</span> 人';

    footerMeta.appendChild(counterDiv);
  }

  function init() {
    injectCounterDOM();
    ensureBusuanziScript();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  if (typeof document$ !== "undefined" && document$.subscribe) {
    document$.subscribe(function () {
      init();
    });
  }
})();
