import {gql, useQuery} from '@apollo/client';
import * as React from 'react';
import styled from 'styled-components/macro';

import {Loading} from 'src/Loading';
import {SidebarSolidDefinition} from 'src/SidebarSolidDefinition';
import {SidebarSolidInvocationInfo} from 'src/SidebarSolidHelpers';
import {SolidCard} from 'src/solids/SolidCard';
import {UsedSolidDetailsQuery} from 'src/solids/types/UsedSolidDetailsQuery';
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

export const USED_SOLID_DETAILS_QUERY = gql`
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

  ${SolidCard.fragments.SolidCardSolidDefinitionFragment}
  ${SidebarSolidDefinition.fragments.SidebarSolidDefinitionFragment}
`;

export const SolidDetailScrollContainer = styled.div`
  overflow: scroll;
  flex: 1;
`;
