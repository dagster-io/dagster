import gql from 'graphql-tag';
import * as React from 'react';

import {RepositoryInfoFragment} from './types/RepositoryInfoFragment';

export const RepositoryInformationFragment = gql`
  fragment RepositoryInfoFragment on Repository {
    name
    origin {
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
    location {
      name
    }
  }
`;

export const RepositoryInformation: React.FunctionComponent<{
  repository: RepositoryInfoFragment;
  dagitExecutablePath?: string;
}> = ({repository, dagitExecutablePath}) => {
  let originInfo;
  if (repository.origin.__typename === 'PythonRepositoryOrigin') {
    originInfo = (
      <>
        {repository.origin.codePointer.metadata.map((metadata, idx) => (
          <div key={idx}>
            <span style={{marginRight: 5}}>{metadata.key}:</span>
            <span style={{opacity: 0.5}}>{metadata.value}</span>
          </div>
        ))}
        {dagitExecutablePath && dagitExecutablePath === repository.origin.executablePath ? null : (
          <div>
            <span style={{marginRight: 5}}>executable:</span>
            <span style={{opacity: 0.5}}>{repository.origin.executablePath}</span>
          </div>
        )}
      </>
    );
  } else {
    originInfo = <div>{repository.origin.grpcUrl}</div>;
  }

  return (
    <div>
      <div>
        {repository.name}
        <span style={{marginRight: 5, marginLeft: 5}}>&middot;</span>
        <span style={{opacity: 0.5}}>{repository.location.name}</span>
      </div>
      <div style={{fontSize: 11, marginTop: 5}}>{originInfo}</div>
    </div>
  );
};
