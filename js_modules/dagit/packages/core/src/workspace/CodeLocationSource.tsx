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

  const isGithub = url.hostname.includes('github.com');
  const isGitlab = url.hostname.includes('gitlab.com');

  if (!isGithub && !isGitlab) {
    // Unknown URL type. Just render the text.
    return <div>{metadataWithURL.value}</div>;
  }

  const metadataWithCommit = metadata.find(({key}) => key === 'commit_hash');
  const commitHash = () => {
    const hashSlice = metadataWithCommit?.value.slice(0, 8);
    return hashSlice ? (
      <>
        <span style={{fontWeight: 500}}>Commit:</span> {hashSlice}
      </>
    ) : null;
  };

  return (
    <Box flex={{direction: 'column', gap: 4, alignItems: 'flex-start'}}>
      <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
        <Icon name={isGithub ? 'github' : 'gitlab'} color={Colors.Link} />
        <a href={metadataWithURL.value} target="_blank" rel="noreferrer">
          {extractProjectName(url.pathname)}
        </a>
      </Box>
      <div style={{fontSize: 12, color: Colors.Gray700}}>{commitHash()}</div>
    </Box>
  );
};

const extractProjectName = (pathname: string) => pathname.split('/').slice(1, 3).join('/');
