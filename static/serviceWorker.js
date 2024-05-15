const CACHE_NAME = "weather-data-cache-v1";
const urlsToCache = [
  "/",
  "https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css",
  "https://cdn.jsdelivr.net/npm/chart.js",
  "/templates/weather_forecast.html",
  "https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=fnd&lang=en",
];

self.addEventListener("install", function (event) {
  console.log("Service Worker: Installing...");
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then(function (cache) {
        console.log("Opened cache");
        return Promise.all(
          urlsToCache.map(function (url) {
            return fetch(url)
              .then(function (response) {
                if (!response.ok) {
                  throw new Error(
                    "Request failed with status " + response.status
                  );
                }
                return cache.put(url, response);
              })
              .catch(function (error) {
                console.error("Failed to cache", url, error);
              });
          })
        );
      })
      .catch(function (err) {
        console.error("Cache open failed: ", err);
      })
  );
});

self.addEventListener("fetch", function (event) {
  console.log("Service Worker: Fetching resource:", event.request.url);
  event.respondWith(
    fetch(event.request)
      .then(function (response) {
        if (!response || response.status !== 200 || response.type !== "basic") {
          console.error("Fetch failed; returning cached response instead.");
          throw new Error("Network response was not ok");
        }
        var responseToCache = response.clone();
        caches.open(CACHE_NAME).then(function (cache) {
          cache
            .put(event.request, responseToCache)
            .then(() => {
              console.log("Resource cached:", event.request.url);
            })
            .catch(function (err) {
              console.error("Cache put failed: ", err);
            });
        });
        return response;
      })
      .catch(function () {
        console.log(
          "Network request failed; looking up in cache:",
          event.request.url
        );
        return caches
          .match(event.request)
          .then(function (response) {
            if (response) {
              console.log("Serving cached response for:", event.request.url);
              return response;
            } else if (
              event.request.headers.get("accept").includes("text/html")
            ) {
              console.log("No cached response; serving fallback offline.html.");
              return caches.match("/templates/offline.html");
            }
            return new Response("Network and cache both failed.");
          })
          .catch(function (err) {
            console.error("Cache match failed: ", err);
            return new Response("Network and cache both failed.");
          });
      })
  );
});

self.addEventListener("activate", function (event) {
  console.log("Service Worker: Activating...");
  var cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(function (cacheNames) {
      return Promise.all(
        cacheNames.map(function (cacheName) {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            console.log("Service Worker: Deleting old cache:", cacheName);
            return caches.delete(cacheName).catch(function (err) {
              console.error("Cache delete failed: ", err);
            });
          }
        })
      );
    })
  );
});
