import * as React from 'react';
import {gql} from '@apollo/client';

import {InstigationStateFragment} from '../instigation/types/InstigationUtils.types';

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

export const InstigatorSelectorInformation = ({
  instigatorState,
}: {
  instigatorState: InstigationStateFragment;
}) => {
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
