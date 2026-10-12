(function () {
  var BUSUANZI_SRC = "https://busuanzi.ibruce.info/busuanzi/2.3/busuanzi.pure.mini.js";
  var STORAGE_KEY = "writing_ignore_stat";
  var scriptLoaded = false;

  function checkAdminStatus() {
    try {
      var params = new URLSearchParams(window.location.search);
      if (params.get("ignore_stat") === "true" || params.get("admin") === "true") {
        localStorage.setItem(STORAGE_KEY, "true");
      } else if (params.get("ignore_stat") === "false" || params.get("admin") === "false") {
        localStorage.removeItem(STORAGE_KEY);
      }
    } catch (e) {}

    var isLocal =
      window.location.hostname === "localhost" ||
      window.location.hostname === "127.0.0.1" ||
      window.location.protocol === "file:";

    var isAdmin = false;
    try {
      isAdmin = localStorage.getItem(STORAGE_KEY) === "true";
    } catch (e) {}

    return isLocal || isAdmin;
  }

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

  function fillCounterDOM(isIgnored) {
    // 占位元素由 overrides/partials/footer.html 预渲染，这里只填内容，避免页脚布局跳动
    var counterDiv = document.getElementById("site-busuanzi-counter");
    if (!counterDiv || counterDiv.childNodes.length) {
      return;
    }

    if (isIgnored) {
      counterDiv.innerHTML =
        '本站总访问量 <span id="busuanzi_value_site_pv">--</span> 次 · ' +
        '总访客数 <span id="busuanzi_value_site_uv">--</span> 人 ' +
        '<span style="opacity: 0.65;" title="当前处于管理员模式或本地环境，已暂停计入统计">(已忽略自身访问)</span>';
    } else {
      counterDiv.innerHTML =
        '本站总访问量 <span id="busuanzi_value_site_pv">--</span> 次 · ' +
        '总访客数 <span id="busuanzi_value_site_uv">--</span> 人';
    }
  }

  function init() {
    var isIgnored = checkAdminStatus();
    fillCounterDOM(isIgnored);
    if (!isIgnored) {
      ensureBusuanziScript();
    }
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
