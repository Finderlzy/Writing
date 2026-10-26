// 站点的少量交互。没有 JS 时页面照常可读：
// 全部文章页的筛选按钮默认隐藏、列表全部显示；代码块的复制按钮也不出现。
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
  function initFilters() {
    var list = document.querySelector("[data-article-list]");
    var panel = document.querySelector("[data-filters]");
    if (!list || !panel) {
      return;
    }
    var items = Array.prototype.slice.call(list.querySelectorAll(".article-item"));
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
      pre.classList.add("has-copy");
    });
  }

  function init() {
    initFilters();
    initCodeCopy();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
