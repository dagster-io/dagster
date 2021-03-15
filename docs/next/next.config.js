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
    ];
  },
};
