import {Box, Colors, Tag} from '@dagster-io/ui-components';
import {UserDisplay} from 'shared/runs/UserDisplay.oss';
import styled from 'styled-components';

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
          <UserOwnerWrapper key={idx}>
            <UserDisplay email={owner.email} size="very-small" />
          </UserOwnerWrapper>
        ) : (
          <Tag icon="people" key={idx}>
            {(owner as TeamOwner).team}
          </Tag>
        ),
      )}
    </Box>
  );
};

const UserOwnerWrapper = styled.div`
  > div {
    border: 1px solid ${Colors.backgroundGray()};
    border-radius: 8px;
  }
`;
