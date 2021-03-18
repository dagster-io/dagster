const redirectUrls = require("./util/redirectUrls.json");

module.exports = {
  async redirects() {
    return [
      {
        source: "/docs",
        destination: "/docs/latest",
        permanent: true,
      },
      {
        source: "/",
        destination: "/getting-started",
        permanent: true,
      },
      ...redirectUrls,
    ];
  },
};
