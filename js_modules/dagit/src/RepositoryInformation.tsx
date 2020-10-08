import gql from 'graphql-tag';
import * as React from 'react';

import {RepositoryInfoFragment} from 'src/types/RepositoryInfoFragment';
import {RepositoryOriginFragment} from 'src/types/RepositoryOriginFragment';

export const RepositoryInformationFragment = gql`
  fragment RepositoryOriginFragment on RepositoryOrigin {
    ... on PythonRepositoryOrigin {
      codePointer {
        metadata {
          key
          value
        }
      }
      executablePath
    }
    ... on GrpcRepositoryOrigin {
      grpcUrl
    }
  }
  fragment RepositoryInfoFragment on Repository {
    name
    origin {
      ...RepositoryOriginFragment
    }
    location {
      name
    }
  }
`;

export const RepositoryOriginInformation: React.FunctionComponent<{
  origin: RepositoryOriginFragment;
  dagitExecutablePath?: string;
}> = ({origin, dagitExecutablePath}) => {
  if (origin.__typename === 'PythonRepositoryOrigin') {
    return (
      <>
        {origin.codePointer.metadata.map((metadata, idx) => (
          <div key={idx}>
            <span style={{marginRight: 5}}>{metadata.key}:</span>
            <span style={{opacity: 0.5}}>{metadata.value}</span>
          </div>
        ))}
        {dagitExecutablePath && dagitExecutablePath === origin.executablePath ? null : (
          <div>
            <span style={{marginRight: 5}}>executable:</span>
            <span style={{opacity: 0.5}}>{origin.executablePath}</span>
          </div>
        )}
      </>
    );
  } else {
    return <div>{origin.grpcUrl}</div>;
  }
};

export const RepositoryInformation: React.FunctionComponent<{
  repository: RepositoryInfoFragment;
  dagitExecutablePath?: string;
}> = ({repository, dagitExecutablePath}) => {
  return (
    <div>
      <div>
        {repository.name}
        <span style={{marginRight: 5, marginLeft: 5}}>&middot;</span>
        <span style={{opacity: 0.5}}>{repository.location.name}</span>
      </div>
      <div style={{fontSize: 11, marginTop: 5}}>
        <RepositoryOriginInformation
          origin={repository.origin}
          dagitExecutablePath={dagitExecutablePath}
        />
      </div>
    </div>
  );
};
