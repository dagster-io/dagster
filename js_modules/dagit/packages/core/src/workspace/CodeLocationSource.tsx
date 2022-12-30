import {Box, Colors, Icon} from '@dagster-io/ui';
import * as React from 'react';

interface Metadata {
  key: string;
  value: string;
}

export const CodeLocationSource: React.FC<{metadata: Metadata[]}> = ({metadata}) => {
  const metadataWithURL = metadata.find(({key}) => key === 'url');
  if (!metadataWithURL) {
    return <div>{'\u2013'}</div>;
  }

  let url = null;
  try {
    url = new URL(metadataWithURL.value);
  } catch (e) {
    // Not a URL. Just show the string, don't try to link it.
  }

  if (!url) {
    return <div>{metadataWithURL.value}</div>;
  }

  if (url.hostname.includes('github.com')) {
    return (
      <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
        <Icon name="github" color={Colors.Link} />
        <a href={metadataWithURL.value} target="_blank" rel="noreferrer">
          {extractProjectName(url.pathname)}
        </a>
      </Box>
    );
  }

  if (url.hostname.includes('gitlab.com')) {
    return (
      <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
        <Icon name="gitlab" color={Colors.Link} />
        <a href={metadataWithURL.value} target="_blank" rel="noreferrer">
          {extractProjectName(url.pathname)}
        </a>
      </Box>
    );
  }

  // Unknown URL type. Just render the text.
  return <div>{metadataWithURL.value}</div>;
};

const extractProjectName = (pathname: string) => pathname.split('/').slice(1, 3).join('/');
