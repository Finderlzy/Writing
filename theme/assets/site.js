// 站点的少量交互。没有 JS 时页面照常可读：
// 全部文章页的筛选按钮默认隐藏、列表全部显示；代码块的复制按钮和白天/黑夜按钮也不出现。
(function () {
  "use strict";

  var STAGE_PARAM = "stage";
  var TAG_PARAM = "tag";

  function debounce(func, wait) {
    var timer = null;
    return function () {
      var context = this;
      var args = arguments;
      window.clearTimeout(timer);
      timer = window.setTimeout(function () {
        func.apply(context, args);
      }, wait);
    };
  }

  // ---- 全部文章页：按阶段和主题筛选，状态写在查询参数里 ----
  // 列表按月分组：条目自己的 data-stage、data-tags 决定显不显示，某个月的条目全被筛掉时，
  // 那个月份（[data-month] 的 .month）也一起隐藏，免得标题下空出一块。
  function initFilters() {
    var list = document.querySelector("[data-article-list]");
    var panel = document.querySelector("[data-filters]");
    if (!list || !panel) {
      return;
    }
    var items = Array.prototype.slice.call(list.querySelectorAll(".article-item"));
    var months = Array.prototype.slice.call(list.querySelectorAll("[data-month]"));
    var stageButtons = Array.prototype.slice.call(panel.querySelectorAll("[data-stage]"));
    var tagButtons = Array.prototype.slice.call(panel.querySelectorAll("[data-tag]"));
    var summary = document.querySelector("[data-filter-summary]");
    var empty = document.querySelector("[data-empty-result]");

    function readParams() {
      var params = new URLSearchParams(window.location.search);
      return { stage: params.get(STAGE_PARAM) || "", tag: params.get(TAG_PARAM) || "" };
    }

    function writeParams(state) {
      var params = new URLSearchParams(window.location.search);
      if (state.stage) {
        params.set(STAGE_PARAM, state.stage);
      } else {
        params.delete(STAGE_PARAM);
      }
      if (state.tag) {
        params.set(TAG_PARAM, state.tag);
      } else {
        params.delete(TAG_PARAM);
      }
      var query = params.toString();
      var url = window.location.pathname + (query ? "?" + query : "") + window.location.hash;
      window.history.replaceState(null, "", url);
    }

    function apply(state) {
      var visible = 0;
      items.forEach(function (item) {
        var tags = (item.getAttribute("data-tags") || "").split("\u0001");
        var matchesStage = !state.stage || item.getAttribute("data-stage") === state.stage;
        var matchesTag = !state.tag || tags.indexOf(state.tag) !== -1;
        var show = matchesStage && matchesTag;
        item.hidden = !show;
        if (show) {
          visible += 1;
        }
      });
      // 分组以后要回头看一眼每个月：它下面的条目全被筛掉时，连月份标题一起隐藏
      months.forEach(function (month) {
        var shown = month.querySelectorAll(".article-item:not([hidden])");
        month.hidden = shown.length === 0;
      });
      stageButtons.forEach(function (button) {
        button.setAttribute("aria-pressed", String(button.getAttribute("data-stage") === state.stage));
      });
      tagButtons.forEach(function (button) {
        button.setAttribute("aria-pressed", String(button.getAttribute("data-tag") === state.tag));
      });
      if (summary) {
        var parts = [];
        parts.push(state.stage ? "阶段：" + state.stage : "全部阶段");
        parts.push(state.tag ? "主题：" + state.tag : "全部主题");
        summary.textContent = parts.join("，") + "，共 " + visible + " 篇";
      }
      if (empty) {
        empty.hidden = visible > 0;
      }
    }

    var state = readParams();
    // 查询参数里的值必须对得上页面上的按钮，否则当成没筛选
    if (state.stage && !stageButtons.some(function (button) { return button.getAttribute("data-stage") === state.stage; })) {
      state.stage = "";
    }
    if (state.tag && !tagButtons.some(function (button) { return button.getAttribute("data-tag") === state.tag; })) {
      state.tag = "";
    }
    apply(state);
    panel.hidden = false;
    if (summary) {
      summary.hidden = false;
    }

    stageButtons.forEach(function (button) {
      button.addEventListener("click", function () {
        state.stage = button.getAttribute("data-stage") || "";
        writeParams(state);
        apply(state);
      });
    });
    tagButtons.forEach(function (button) {
      button.addEventListener("click", function () {
        state.tag = button.getAttribute("data-tag") || "";
        writeParams(state);
        apply(state);
      });
    });
  }

  // ---- 文章页：代码块一键复制 ----
  function initCodeCopy() {
    var blocks = document.querySelectorAll(".article-body pre");
    Array.prototype.forEach.call(blocks, function (pre) {
      var code = pre.querySelector("code");
      if (!code) {
        return;
      }
      var button = document.createElement("button");
      button.type = "button";
      button.className = "code-copy";
      button.textContent = "复制";
      button.setAttribute("aria-label", "复制代码");
      button.addEventListener("click", function () {
        var text = code.textContent;
        var done = function () {
          button.textContent = "已复制";
          window.setTimeout(function () {
            button.textContent = "复制";
          }, 2000);
        };
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text).then(done, fallback);
        } else {
          fallback();
        }

        function fallback() {
          var area = document.createElement("textarea");
          area.value = text;
          area.setAttribute("readonly", "");
          area.style.position = "fixed";
          area.style.opacity = "0";
          document.body.appendChild(area);
          area.select();
          try {
            document.execCommand("copy");
            done();
          } finally {
            document.body.removeChild(area);
          }
        }
      });
      pre.parentNode.insertBefore(button, pre.nextSibling);
    });
  }

  // ---- 白天 / 黑夜切换（R-VIS-7） ----
  // 读者没选过时跟随系统；点一下就在两种之间切换并记住。初始值由 base.html 头部的内联脚本写好，
  // 这里只负责按钮、系统设置变化和评论区（Giscus 的 iframe 要用 postMessage 告诉它换主题）。
  var THEME_KEY = "theme";
  var GISCUS_ORIGIN = "https://giscus.app";

  function initThemeToggle() {
    var root = document.documentElement;
    var button = document.querySelector("[data-theme-toggle]");
    var systemDark = window.matchMedia("(prefers-color-scheme: dark)");

    function current() {
      return root.getAttribute("data-theme-current") === "dark" ? "dark" : "light";
    }

    function syncGiscus() {
      var frame = document.querySelector("iframe.giscus-frame");
      if (frame && frame.contentWindow) {
        frame.contentWindow.postMessage({ giscus: { setConfig: { theme: current() } } }, GISCUS_ORIGIN);
      }
    }

    function show(theme) {
      root.setAttribute("data-theme-current", theme);
      if (button) {
        var label = theme === "dark" ? "切换到白天" : "切换到黑夜";
        button.setAttribute("aria-label", label);
        button.title = label;
      }
      syncGiscus();
    }

    // 旧版 Safari（14 以前）的 matchMedia 没有 addEventListener，那时就只在打开页面时跟随系统
    if (systemDark.addEventListener) {
      systemDark.addEventListener("change", function () {
        if (!root.hasAttribute("data-theme")) {
          show(systemDark.matches ? "dark" : "light");
        }
      });
    }

    // Giscus 加载完会发消息过来，这时它还是按系统深浅画的，补发一次当前主题。
    // 只补第一次：它换主题后还会再发调整高度的消息，每次都回应会来回打转
    var giscusSynced = false;
    window.addEventListener("message", function (event) {
      if (!giscusSynced && event.origin === GISCUS_ORIGIN && event.data && event.data.giscus) {
        giscusSynced = true;
        syncGiscus();
      }
    });

    if (!button) {
      return;
    }
    show(current());
    button.hidden = false;
    button.addEventListener("click", function () {
      var next = current() === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try {
        window.localStorage.setItem(THEME_KEY, next);
      } catch (error) {
        // 隐私模式等存不了的情况：本页照样切换，只是下次不记得
      }
      show(next);
    });
  }

  function init() {
    initFilters();
    initCodeCopy();
    initThemeToggle();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
