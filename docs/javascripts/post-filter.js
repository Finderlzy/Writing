(function () {
  // 文章列表页的标签筛选：按钮由构建生成，没有 JS 时按钮保持隐藏、列表全部显示
  function init() {
    var filter = document.querySelector("[data-post-filter]");
    if (!filter) {
      return;
    }
    var items = [];
    Array.prototype.forEach.call(document.querySelectorAll(".md-content .post-tags"), function (span) {
      var li = span.closest("li");
      if (li) {
        items.push({ li: li, tags: JSON.parse(span.getAttribute("data-tags") || "[]") });
      }
    });
    var buttons = filter.querySelectorAll("button[data-tag]");

    function apply(tag) {
      items.forEach(function (item) {
        item.li.hidden = tag !== "" && item.tags.indexOf(tag) === -1;
      });
      Array.prototype.forEach.call(buttons, function (button) {
        button.setAttribute("aria-pressed", String(button.getAttribute("data-tag") === tag));
      });
    }

    Array.prototype.forEach.call(buttons, function (button) {
      button.addEventListener("click", function () {
        apply(button.getAttribute("data-tag"));
      });
    });
    filter.hidden = false;
    apply("");
  }

  if (typeof document$ !== "undefined" && document$.subscribe) {
    document$.subscribe(init);
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
