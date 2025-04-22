var config = {
  mode: "fixed_servers",
  rules: {
    singleProxy: {
      scheme: "http",
      host: "us.smartproxy.com",
      port: 10001,
    },
    bypassList: ["localhost"],
  },
};

chrome.proxy.settings.set({ value: config, scope: "regular" }, function () {});

chrome.webRequest.onAuthRequired.addListener(
  function (details, callbackFn) {
    callbackFn({
      authCredentials: {
        username: "spgcen825j",
        password: "ebG_7Etrvh4Dg8zQ7w",
      },
    });
  },
  { urls: ["<all_urls>"] },
  ["blocking"]
);
