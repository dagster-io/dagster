import {gql} from '@apollo/client';
import * as React from 'react';

import {RepositoryInfoFragment} from 'src/workspace/types/RepositoryInfoFragment';
import {RepositoryOriginFragment} from 'src/workspace/types/RepositoryOriginFragment';

export const REPOSITORY_ORIGIN_FRAGMENT = gql`
  fragment RepositoryOriginFragment on RepositoryOrigin {
    id
    repositoryLocationName
    repositoryName
    repositoryLocationMetadata {
      key
      value
    }
  }
`;

export const REPOSITORY_INFO_FRAGMENT = gql`
  fragment RepositoryInfoFragment on Repository {
    id
    name
    origin {
      id
      ...RepositoryOriginFragment
    }
    location {
      id
      name
    }
  }
  ${REPOSITORY_ORIGIN_FRAGMENT}
`;

export const RepositoryOriginInformation: React.FunctionComponent<{
  origin: RepositoryOriginFragment;
}> = ({origin}) => {
  return (
    <>
      {origin.repositoryLocationMetadata.map((metadata, idx) => (
        <div key={idx}>
          <span style={{marginRight: 5}}>{metadata.key}:</span>
          <span style={{opacity: 0.5}}>{metadata.value}</span>
        </div>
      ))}
    </>
  );
};

export const RepositoryInformation: React.FunctionComponent<{
  repository: RepositoryInfoFragment;
}> = ({repository}) => {
  return (
    <div>
      <div>
        {repository.name}
        <span style={{marginRight: 5, marginLeft: 5}}>&middot;</span>
        <span style={{opacity: 0.5}}>{repository.location.name}</span>
      </div>
      <div style={{fontSize: 11, marginTop: 5}}>
        <RepositoryOriginInformation origin={repository.origin} />
      </div>
    </div>
  );
};
