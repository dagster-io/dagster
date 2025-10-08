import {Box, Tag} from '@dagster-io/ui-components';
import {UserDisplay} from 'shared/runs/UserDisplay.oss';

import styles from './css/DefinitionOwners.module.css';

export interface UserOwner {
  __typename: 'UserDefinitionOwner' | 'UserAssetOwner';
  email: string;
}

export interface TeamOwner {
  __typename: 'TeamDefinitionOwner' | 'TeamAssetOwner';
  team: string;
}

export type Owner = UserOwner | TeamOwner;

export interface DefinitionOwnersProps {
  owners: Owner[];
}

export const DefinitionOwners = ({owners}: DefinitionOwnersProps) => {
  if (!owners || owners.length === 0) {
    return null;
  }

  return (
    <Box flex={{gap: 4, wrap: 'wrap'}}>
      {owners.map((owner, idx) =>
        owner.__typename === 'UserDefinitionOwner' || owner.__typename === 'UserAssetOwner' ? (
          <div key={idx} className={styles.userDisplay}>
            <UserDisplay email={owner.email} size="very-small" />
          </div>
        ) : (
          <Tag icon="people" key={idx}>
            {(owner as TeamOwner).team}
          </Tag>
        ),
      )}
    </Box>
  );
};
