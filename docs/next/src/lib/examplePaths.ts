export function getExamplePaths() {
  const names = ['dep_dsl', 'config_mapping'];
  return {
    paths: names.map((i) => {
      return {
        params: {
          page: [i],
        },
      };
    }),
    fallback: false,
  };
}
