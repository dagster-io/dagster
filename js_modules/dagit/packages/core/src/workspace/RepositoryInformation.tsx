import {gql} from '@apollo/client';
import * as React from 'react';

import {InstigationStateFragment} from '../instigation/types/InstigationStateFragment';

export const REPOSITORY_INFO_FRAGMENT = gql`
  fragment RepositoryInfoFragment on Repository {
    id
    name
    location {
      id
      name
    }
    displayMetadata {
      key
      value
    }
  }
`;

export const InstigatorSelectorInformation: React.FC<{
  instigatorState: InstigationStateFragment;
}> = ({instigatorState}) => {
  return (
    <>
      <div>
        <span style={{marginRight: 5}}>repository:</span>
        <span style={{opacity: 0.5}}>
          {instigatorState.repositoryName}@{instigatorState.repositoryLocationName}
        </span>
      </div>
    </>
  );
};
