import {Colors, Icon} from '@dagster-io/ui';
import React from 'react';

export const formatRepositoryUrl = (url: string): string => {
  try {
    const urlObj = new URL(url);
    let org, repo, tag;
    if (urlObj.host === 'github.com') {
      [, org, repo, , tag] = urlObj.pathname.split('/', 7);
    } else if (urlObj.host === 'gitlab.com') {
      [, org, repo, , , tag] = urlObj.pathname.split('/', 8);
    }
    if (org && repo && tag) {
      return `${org}/${repo}@${tag}`;
    }
  } catch (error) {
    return url;
  }
  return url;
};

export const RepositoryRemoteLocationLink: React.FC<{repositoryUrl: string}> = ({
  repositoryUrl,
}) => {
  const formattedUrl = formatRepositoryUrl(repositoryUrl);

  return (
    <a href={repositoryUrl} target="_blank" rel="noopener noreferrer">
      <Icon
        color={Colors.Link}
        name="link"
        style={{display: 'inline-block', verticalAlign: 'middle'}}
      />{' '}
      {formattedUrl}
    </a>
  );
};
