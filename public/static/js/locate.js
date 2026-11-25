// "Use my location": fills the hidden latitude and longitude fields from the browser.
// The button stays hidden where the browser cannot locate, and nothing is sent until the
// form is submitted. The server checks the point is in India and names the nearest town.
(function () {
  "use strict";
  const button = document.getElementById("locate");
  const status = document.getElementById("locate-status");
  if (!button || !status || !("geolocation" in navigator)) {
    return;
  }
  button.hidden = false;
  button.addEventListener("click", function () {
    status.textContent = "Finding your location…";
    navigator.geolocation.getCurrentPosition(
      function (position) {
        document.getElementById("geo_lat").value = position.coords.latitude.toFixed(4);
        document.getElementById("geo_lon").value = position.coords.longitude.toFixed(4);
        status.textContent = "Location set. The nearest station will be used.";
      },
      function () {
        status.textContent = "Location was not shared. Type a place instead.";
      },
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 600000 }
    );
  });
})();
