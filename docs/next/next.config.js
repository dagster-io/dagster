const ALL_VERSIONS = ["0.9.19", "0.9.20", "0.9.21"];

module.exports = {
  async redirects() {
    return [
      {
        source: "/docs",
        destination: "/docs/latest",
        permanent: true,
      },
    ];
  },
  i18n: {
    locales: ["master", ...ALL_VERSIONS],
    defaultLocale:
      // process.env.NODE_ENV == "production" ? ALL_VERSIONS[0] : "master",
      "master",
  },
};
