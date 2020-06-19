import { useMemo } from 'react';

import data from 'data/searchindex.json';
import examples from 'data/examples.json';
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
        path: doc.replace('sections/api/apidocs/', '/docs/apidocs/'),
      });
    }
  }

  const { NEXT_PUBLIC_DEV_MODE } = process.env;
  if (!NEXT_PUBLIC_DEV_MODE || NEXT_PUBLIC_DEV_MODE !== 'true') {
    console.log('Not in dev mode, deleting overview');
    delete treeOfContents['Overview'];
  }

  if (NEXT_PUBLIC_DEV_MODE == 'true') {
    const EXAMPLES_PAGES = [];
    const exampleNames = Object.keys(examples);
    for (const example of exampleNames) {
      EXAMPLES_PAGES.push({
        name: example,
        path: '/docs/examples/' + example,
      });
    }

    return Object.assign({}, treeOfContents, {
      Examples: {
        name: 'Examples',
        path: '/docs/examples',
        children: EXAMPLES_PAGES,
      },
    });
  }

  return treeOfContents;
};

export const useTreeOfContents = () =>
  useMemo(() => createTreeOfContents(), []);
