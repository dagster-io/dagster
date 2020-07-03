import { useMemo } from 'react';

import data from 'data/searchindex.json';
import examples from 'pages/examples/examples.json';
import treeOfContents from 'treeOfContents.json';

const createTreeOfContents = () => {
  const API_DOCS_PAGES = [];
  const docnames = data.docnames;
  for (const i in docnames) {
    const doc = docnames[i];
    const title = data.titles[i];
    if (doc.includes('api/apidocs')) {
      API_DOCS_PAGES.push({
        name: title,
        path: doc.replace('sections/api/apidocs/', '/_apidocs/'),
      });
    }
  }

  delete treeOfContents['Learn'];

  const EXAMPLES_PAGES = [];
  for (const example of examples) {
    EXAMPLES_PAGES.push({
      name: example.title,
      path: '/examples/' + example.name,
    });
  }

  return Object.assign({}, treeOfContents, {
    Examples: {
      name: 'Examples',
      path: '/examples',
      children: EXAMPLES_PAGES,
    },
  });
};

export const useTreeOfContents = () =>
  useMemo(() => createTreeOfContents(), []);
