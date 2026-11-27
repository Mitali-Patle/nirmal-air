// The colour switch repaints the page in place. A click marks its option at once; htmx posts
// the choice, the server saves it and replies with the new sky band, and its "theme-change"
// event (HX-Trigger) carries the phase, haze and theme set here. Colours cross-fade.
(() => {
  const root = document.documentElement;
  const FADE_MS = 600;

  document.addEventListener("click", (event) => {
    const choice = event.target.closest(".switch button");
    if (!choice) return;
    for (const option of choice.parentElement.querySelectorAll("button")) {
      option.setAttribute("aria-pressed", String(option === choice));
    }
  });

  // The server sends the control back after each change, which would drop keyboard focus to
  // the page: remember the focused button and give focus to its replacement.
  let refocus = null;
  document.addEventListener("htmx:beforeRequest", () => {
    const focused = document.activeElement;
    if (!focused?.closest("#theme-form")) return;
    refocus = focused.classList.contains("cycle")
      ? "#theme-form .cycle"
      : `#theme-form .switch button[value="${focused.value}"]`;
  });
  document.addEventListener("htmx:afterSettle", () => {
    if (!refocus) return;
    const again = document.querySelector(refocus);
    refocus = null;
    if (again) again.focus();
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
