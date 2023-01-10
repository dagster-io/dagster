import * as React from 'react';

import {graphql} from '../graphql';
import {InstigationStateFragmentFragment} from '../graphql/graphql';

export const REPOSITORY_INFO_FRAGMENT = graphql(`
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
`);

export const InstigatorSelectorInformation: React.FC<{
  instigatorState: InstigationStateFragmentFragment;
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
