import {useEffect, useState} from 'react';

import {LATEST_VERSION} from '../../util/version';

import {Fence} from './FencedCodeBlock';

// Logic to get code snippets from files in dagster github repo
// The following URL contains the raw file https://raw.githubusercontent.com/dagster-io/dagster/master/examples/docs_snippets/docs_snippets/concepts/configuration/config_map_example.py

// Some work to handle versioning will be needed.
// The good news is the url contains versioning.
// For example, the following URL contains the version 1.7.6 as a
// Prefix to the URL: https://release-1-7-6.dagster.dagster-docs.io
// Would map to the following URL for the content as a place to fetch the code
// snippets from the dagster repo:
// https://raw.githubusercontent.com/dagster-io/dagster/release-1.7.6/examples/docs_snippets/

// So the approach we'll need to take is to get the url from the browser
// and since it's react, we'll need to use the useEffect hook to get the
// URL and then fetch the content.
const url =
  'https://raw.githubusercontent.com/dagster-io/dagster/master/examples/docs_snippets/docs_snippets/concepts/configuration/config_map_example.py';

const fetchSnippet = async (url) => {
  console.log('Begin getSnippet \n Starting fetch ', url);
  const response = await fetch(url);
  const data = await response.text();
  console.log(data);
  return data;
};

export const CodeSnippet = (props) => {
  console.log('CodeSnippet.tsx');
  console.log(LATEST_VERSION);
  const [text, setText] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      const snippet = await fetchSnippet(url);
      setText(snippet);
    };
    
    fetchData();
  }, []); // Empty dependency array means this effect runs once after the initial render

  return (
    <div>
      <h3>CodeSnippet</h3>
      <Fence data-language="python">{text}</Fence>
    </div>
  );
};
