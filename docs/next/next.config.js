const ALL_VERSIONS = [];

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
