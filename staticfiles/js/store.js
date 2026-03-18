// Infinite scroll pagination for store products
// Mirrors the behavior of event/eve/static/js/list.js
(function () {
  document.addEventListener("DOMContentLoaded", function () {
    const container = document.getElementById("product-list-container");
    const productList = document.getElementById("product-list");
    const statusEl = document.querySelector("#product-pagination-status .js-pagination-label");

    if (!container || !productList) return;

    const mode = container.getAttribute("data-mode") || "cursor"; // cursor or search
    let page = parseInt(container.getAttribute("data-page") || "1", 10);
    let lastCursor = container.getAttribute("data-last-cursor") || "";
    let hasNext = container.getAttribute("data-has-next") === "true";
    let pauseRequest = false;
    let emptyPage = !hasNext;

    function setStatusLoading(isLoading) {
      if (!statusEl) return;
      if (isLoading) {
        statusEl.textContent = "Loading more products…";
      } else if (emptyPage) {
        statusEl.textContent = "You’ve reached the end";
      } else {
        statusEl.textContent = "Scroll to load more";
      }
    }

    function parseMetaAndUpdate(fragment) {
      const meta = fragment.querySelector("#pagination-meta");
      if (!meta) {
        emptyPage = true;
        hasNext = false;
        return;
      }
      const nextCursor = meta.getAttribute("data-last-cursor") || "";
      const nextHas = meta.getAttribute("data-has-next") === "true";
      const nextPage = meta.getAttribute("data-page");
      if (mode === "cursor") {
        lastCursor = nextCursor;
      } else if (mode === "search" && nextPage) {
        page = parseInt(nextPage, 10);
      }
      hasNext = nextHas;
      emptyPage = !nextHas;
      meta.remove();
    }

    function buildNextUrl() {
      const currentPath = window.location.pathname;
      const params = new URLSearchParams(window.location.search);
      params.set("list_only", "1");

      if (mode === "cursor") {
        if (lastCursor) {
          params.set("cursor", lastCursor);
        } else {
          params.delete("cursor");
        }
      } else {
        page += 1;
        params.set("page", page);
      }
      return `${currentPath}?${params.toString()}`;
    }

    window.addEventListener("scroll", function () {
      const margin = document.body.clientHeight - window.innerHeight - 200;
      if (emptyPage || pauseRequest || !hasNext) return;
      if (window.pageYOffset <= margin) return;

      pauseRequest = true;
      setStatusLoading(true);
      const url = buildNextUrl();

      fetch(url)
        .then((response) => response.text())
        .then((html) => {
          if (!html) {
            emptyPage = true;
            hasNext = false;
            setStatusLoading(false);
            return;
          }
          const fragment = document.createElement("div");
          fragment.innerHTML = html;

          parseMetaAndUpdate(fragment);

          while (fragment.firstChild) {
            productList.appendChild(fragment.firstChild);
          }

          pauseRequest = false;
          setStatusLoading(false);
        })
        .catch((err) => {
          console.error("Error loading more products:", err);
          emptyPage = true;
          hasNext = false;
          setStatusLoading(false);
        });
    });

    // Trigger initial check
    window.dispatchEvent(new Event("scroll"));
  });
})();


