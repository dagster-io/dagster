import {gql, useQuery} from '@apollo/client';
import * as React from 'react';
import styled from 'styled-components/macro';

import {
  SidebarSolidDefinition,
  SIDEBAR_SOLID_DEFINITION_FRAGMENT,
} from 'src/pipelines/SidebarSolidDefinition';
import {SidebarSolidInvocationInfo} from 'src/pipelines/SidebarSolidHelpers';
import {SolidCard, SOLID_CARD_SOLID_DEFINITION_FRAGMENT} from 'src/solids/SolidCard';
import {UsedSolidDetailsQuery} from 'src/solids/types/UsedSolidDetailsQuery';
import {Loading} from 'src/ui/Loading';
import {repoAddressToSelector} from 'src/workspace/repoAddressToSelector';
import {RepoAddress} from 'src/workspace/types';

interface UsedSolidDetailsProps {
  name: string;
  onClickInvocation: (arg: SidebarSolidInvocationInfo) => void;
  repoAddress: RepoAddress;
}

export const UsedSolidDetails: React.FC<UsedSolidDetailsProps> = (props) => {
  const {name, onClickInvocation, repoAddress} = props;
  const repositorySelector = repoAddressToSelector(repoAddress);

  const queryResult = useQuery<UsedSolidDetailsQuery>(USED_SOLID_DETAILS_QUERY, {
    variables: {
      name,
      repositorySelector,
    },
  });

  return (
    <Loading queryResult={queryResult}>
      {({repositoryOrError}) => {
        if (!(repositoryOrError?.__typename === 'Repository' && repositoryOrError.usedSolid)) {
          return null;
        }
        const usedSolid = repositoryOrError.usedSolid;
        return (
          <>
            <SolidCard definition={usedSolid.definition} />
            <SidebarSolidDefinition
              definition={usedSolid.definition}
              showingSubsolids={false}
              onClickInvocation={onClickInvocation}
              getInvocations={() => {
                return usedSolid.invocations.map((i) => ({
                  handleID: i.solidHandle.handleID,
                  pipelineName: i.pipeline.name,
                }));
              }}
            />
          </>
        );
      }}
    </Loading>
  );
};

const USED_SOLID_DETAILS_QUERY = gql`
  query UsedSolidDetailsQuery($name: String!, $repositorySelector: RepositorySelector!) {
    repositoryOrError(repositorySelector: $repositorySelector) {
      ... on Repository {
        id
        usedSolid(name: $name) {
          __typename
          definition {
            ...SolidCardSolidDefinitionFragment
            ...SidebarSolidDefinitionFragment
          }
          invocations {
            __typename
            pipeline {
              id
              name
            }
            solidHandle {
              handleID
            }
          }
        }
      }
    }
  }

  ${SOLID_CARD_SOLID_DEFINITION_FRAGMENT}
  ${SIDEBAR_SOLID_DEFINITION_FRAGMENT}
`;

export const SolidDetailScrollContainer = styled.div`
  overflow: scroll;
  flex: 1;
`;
