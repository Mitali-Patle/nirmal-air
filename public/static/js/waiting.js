// When a request fails (a server error, no network, or no reply within the timeout), the part
// of the page that was waiting says so and how to try again, instead of waiting for ever.
(() => {
  const MESSAGES = {
    plan: "Today's plan could not be written just now. The air, timing and estimates on this page are still current; reload the page to try again.",
    answer: "That question could not be answered just now. Please try again in a moment.",
  };

  const say = (target, text) => {
    const note = document.createElement("p");
    note.className = "note";
    note.setAttribute("role", "alert");
    note.textContent = text;
    if (target.id === "plan") {
      for (const part of target.querySelectorAll(".plan-head, .steps")) part.remove();
      target.append(note);
    } else {
      target.replaceChildren(note);
    }
  };

  const failed = (event) => {
    const target = event.detail?.target;
    if (target && target.id in MESSAGES) say(target, MESSAGES[target.id]);
  };

  for (const name of ["htmx:responseError", "htmx:sendError", "htmx:timeout"]) {
    document.addEventListener(name, failed);
  }
})();
