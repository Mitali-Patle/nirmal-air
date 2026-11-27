// "Use my location": fills the hidden latitude and longitude fields from the browser, then
// asks the server to name the place and its nearest station so the visitor sees what was
// found. Typing a place afterwards clears the location, so the typed place wins.
(() => {
  const button = document.getElementById("locate");
  const status = document.getElementById("locate-status");
  const lat = document.getElementById("geo_lat");
  const lon = document.getElementById("geo_lon");
  const typed = document.getElementById("place_query");
  if (!button || !status || !lat || !lon || !("geolocation" in navigator)) {
    return;
  }
  const WAIT_MS = 15000;
  const reasons = {
    1: "Location permission was not given. Allow it in the browser, or type a place.",
    2: "Your browser could not find a location (common on desktops). Type a place instead.",
    3: "Finding your location took too long. Try again, or type a place.",
  };
  let pending = null;

  function finish(message) {
    window.clearTimeout(pending);
    pending = null;
    button.disabled = false;
    status.textContent = message;
  }

  button.hidden = false;
  button.addEventListener("click", () => {
    button.disabled = true;
    status.textContent = "Finding your location… if the browser asks, choose Allow.";
    pending = window.setTimeout(() => {
      finish(reasons[3]);
    }, WAIT_MS);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        // A late answer (the permission prompt can take a while) is still used.
        lat.value = position.coords.latitude.toFixed(4);
        lon.value = position.coords.longitude.toFixed(4);
        if (typed) {
          typed.value = "";
        }
        const choices = document.getElementById("place-choices");
        if (choices) {
          choices.textContent = "";
        }
        const query = `lat=${encodeURIComponent(lat.value)}&lon=${encodeURIComponent(lon.value)}`;
        fetch(`/near?${query}`)
          .then((reply) => (reply.ok ? reply.text() : Promise.reject(reply.status)))
          .then((text) => {
            finish(text.trim());
          })
          .catch(() => {
            finish("Location set. The nearest station will be used.");
          });
      },
      (error) => {
        if (pending !== null) {
          finish(reasons[error.code] || reasons[2]);
        }
      },
      { enableHighAccuracy: false, timeout: WAIT_MS, maximumAge: 600000 },
    );
  });
  if (typed) {
    typed.addEventListener("input", () => {
      if (lat.value) {
        lat.value = "";
        lon.value = "";
        status.textContent = "Using the place you type instead of your location.";
      }
    });
  }
})();
