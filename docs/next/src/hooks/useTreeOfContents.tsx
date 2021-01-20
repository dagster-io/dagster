import { useMemo } from 'react';

import data from 'data/searchindex.json';
import examples from 'pages/examples/examples.json';
import treeOfContents from 'treeOfContents.json';

const createTreeOfContents = () => {
  const EXAMPLES_PAGES = [];
  for (const example of examples) {
    EXAMPLES_PAGES.push({
      name: example.title,
      path: '/examples/' + example.name,
    });
  }
  const examplesEntry = {
    name: 'Examples',
    path: '/examples',
    children: EXAMPLES_PAGES,
  };

  const entriesByName = Object.assign(
    { Examples: examplesEntry },
    ...treeOfContents.map((entry) => ({ [entry.name]: entry })),
  );

  const ORDERING = [
    'Install',
    'Tutorial',
    'Examples',
    'Overviews',
    'Deploy',
    'Troubleshooting',
    'Community',
    'API Docs',
  ];
  const result = ORDERING.map((name) => entriesByName[name]);
  return result;
};

export const useTreeOfContents = () =>
  useMemo(() => createTreeOfContents(), []);
