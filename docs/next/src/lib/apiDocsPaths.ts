import data from '../data/searchindex.json';

export function getApiDocsPaths() {
  const names = [];
  const docnames = data.docnames;
  for (const doc of docnames) {
    if (
      doc.includes('sections/api/') &&
      doc !== 'sections/api/index' &&
      doc !== 'sections/api/libraries'
    ) {
      names.push(doc.replace('sections/api/apidocs/', '').split('/'));
    }
  }
  return {
    paths: names.map((i) => {
      return {
        params: {
          page: i,
        },
      };
    }),
    fallback: false,
  };
}
