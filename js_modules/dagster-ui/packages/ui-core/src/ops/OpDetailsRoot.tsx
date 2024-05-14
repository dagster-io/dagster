import {gql, useQuery} from '@apollo/client';
import styled from 'styled-components';

import {OP_CARD_SOLID_DEFINITION_FRAGMENT, OpCard} from './OpCard';
import {UsedSolidDetailsQuery, UsedSolidDetailsQueryVariables} from './types/OpDetailsRoot.types';
import {
  SIDEBAR_OP_DEFINITION_FRAGMENT,
  SidebarOpDefinition,
} from '../pipelines/SidebarOpDefinition';
import {SidebarOpInvocationInfo} from '../pipelines/SidebarOpHelpers';
import {Loading} from '../ui/Loading';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

interface UsedSolidDetailsProps {
  name: string;
  onClickInvocation: (arg: SidebarOpInvocationInfo) => void;
  repoAddress: RepoAddress;
}

export const UsedSolidDetails = (props: UsedSolidDetailsProps) => {
  const {name, onClickInvocation, repoAddress} = props;
  const repositorySelector = repoAddressToSelector(repoAddress);

  const queryResult = useQuery<UsedSolidDetailsQuery, UsedSolidDetailsQueryVariables>(
    USED_SOLID_DETAILS_QUERY,
    {
      variables: {
        name,
        repositorySelector,
      },
    },
  );

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

const USED_SOLID_DETAILS_QUERY = gql`
  query UsedSolidDetailsQuery($name: String!, $repositorySelector: RepositorySelector!) {
    repositoryOrError(repositorySelector: $repositorySelector) {
      ... on Repository {
        id
        usedSolid(name: $name) {
          definition {
            ...OpCardSolidDefinitionFragment
            ...SidebarOpDefinitionFragment
          }
          invocations {
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

  ${OP_CARD_SOLID_DEFINITION_FRAGMENT}
  ${SIDEBAR_OP_DEFINITION_FRAGMENT}
`;

export const OpDetailScrollContainer = styled.div`
  overflow-y: scroll;
  flex: 1;
`;
