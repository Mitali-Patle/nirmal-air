// The colour switch repaints the page in place. A click marks its option at once; htmx posts
// the choice, the server saves it and replies with the new sky band, and its "theme-change"
// event (HX-Trigger) carries the phase, haze and theme set here. Colours cross-fade.
(() => {
  "use strict";
  const root = document.documentElement;
  const FADE_MS = 600;

  document.addEventListener("click", (event) => {
    const choice = event.target.closest(".switch button");
    if (!choice) return;
    for (const option of choice.parentElement.querySelectorAll("button")) {
      option.setAttribute("aria-pressed", String(option === choice));
    }
  });

  document.addEventListener("theme-change", (event) => {
    const { phase, haze, theme } = event.detail;
    root.classList.add("theme-fade");
    root.dataset.phase = phase;
    root.dataset.haze = String(haze);
    root.dataset.theme = theme;
    window.setTimeout(() => root.classList.remove("theme-fade"), FADE_MS);
  });
})();
