import {useQuery} from '@apollo/client';
import * as React from 'react';
import styled from 'styled-components/macro';

import {graphql} from '../graphql';
import {SidebarOpDefinition} from '../pipelines/SidebarOpDefinition';
import {SidebarOpInvocationInfo} from '../pipelines/SidebarOpHelpers';
import {Loading} from '../ui/Loading';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {OpCard} from './OpCard';

interface UsedSolidDetailsProps {
  name: string;
  onClickInvocation: (arg: SidebarOpInvocationInfo) => void;
  repoAddress: RepoAddress;
}

export const UsedSolidDetails: React.FC<UsedSolidDetailsProps> = (props) => {
  const {name, onClickInvocation, repoAddress} = props;
  const repositorySelector = repoAddressToSelector(repoAddress);

  const queryResult = useQuery(USED_SOLID_DETAILS_QUERY, {
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
            <OpCard definition={usedSolid.definition} />
            <SidebarOpDefinition
              definition={usedSolid.definition}
              showingSubgraph={false}
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

const USED_SOLID_DETAILS_QUERY = graphql(`
  query UsedSolidDetailsQuery($name: String!, $repositorySelector: RepositorySelector!) {
    repositoryOrError(repositorySelector: $repositorySelector) {
      ... on Repository {
        id
        usedSolid(name: $name) {
          __typename
          definition {
            ...OpCardSolidDefinitionFragment
            ...SidebarOpDefinitionFragment
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
`);

export const OpDetailScrollContainer = styled.div`
  overflow: scroll;
  flex: 1;
`;
