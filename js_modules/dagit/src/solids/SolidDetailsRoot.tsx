import {gql, useQuery} from '@apollo/client';
import * as React from 'react';
import styled from 'styled-components/macro';

import {
  SidebarSolidDefinition,
  SIDEBAR_SOLID_DEFINITION_FRAGMENT,
} from '../pipelines/SidebarSolidDefinition';
import {SidebarSolidInvocationInfo} from '../pipelines/SidebarSolidHelpers';
import {Loading} from '../ui/Loading';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {SolidCard, SOLID_CARD_SOLID_DEFINITION_FRAGMENT} from './SolidCard';
import {UsedSolidDetailsQuery} from './types/UsedSolidDetailsQuery';

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
