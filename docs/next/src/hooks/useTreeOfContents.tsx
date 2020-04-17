import { useMemo } from 'react';

import data from 'data/searchindex.json';
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

  // Don't mutate state for now - hardcoded
  // (treeOfContents['API Docs'] as TreeLink).children = API_DOCS_PAGES;
  return treeOfContents;
};

export const useTreeOfContents = () =>
  useMemo(() => createTreeOfContents(), []);
