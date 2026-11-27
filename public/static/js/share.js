// "Share today's air": passes a short summary of today's measured air (built on the server
// from the same facts as the page) to a family, building, school or society group, with the
// phone's share sheet, or by copying it. The button stays hidden where neither works.
(() => {
  "use strict";
  const button = document.getElementById("share");
  const status = document.getElementById("share-status");
  if (!button || !status) return;
  const canShare = typeof navigator.share === "function";
  const canCopy = Boolean(navigator.clipboard && navigator.clipboard.writeText);
  if (!canShare && !canCopy) return;
  button.hidden = false;

  const copy = async (text) => {
    await navigator.clipboard.writeText(text);
    status.textContent = "Copied. Paste it into your family, building or school group.";
  };

  button.addEventListener("click", async () => {
    const text = button.dataset.shareText;
    status.textContent = "";
    try {
      if (canShare) {
        await navigator.share({ title: button.dataset.shareTitle, text });
      } else {
        await copy(text);
      }
    } catch (error) {
      if (error && error.name === "AbortError") return; // the visitor closed the share sheet
      try {
        await copy(text);
      } catch {
        status.textContent = "Sharing is not available here.";
      }
    }
  });
})();
