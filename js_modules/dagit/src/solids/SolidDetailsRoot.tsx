import {gql, useQuery} from '@apollo/client';
import * as React from 'react';
import {RouteComponentProps} from 'react-router';
import styled from 'styled-components/macro';

import {DagsterRepositoryContext, useRepositorySelector} from 'src/DagsterRepositoryContext';
import {Loading} from 'src/Loading';
import {SidebarSolidDefinition} from 'src/SidebarSolidDefinition';
import {SidebarSolidInvocationInfo} from 'src/SidebarSolidHelpers';
import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {SolidCard} from 'src/solids/SolidCard';
import {UsedSolidDetailsQuery} from 'src/solids/types/UsedSolidDetailsQuery';

export const SolidDetailsRoot: React.FunctionComponent<RouteComponentProps<{
  name: string;
}>> = (props) => {
  const {name} = props.match.params;
  useDocumentTitle(`Solid: ${name}`);
  return (
    <SolidDetailScrollContainer>
      <UsedSolidDetails
        name={name}
        onClickInvocation={({pipelineName, handleID}) =>
          props.history.push(`/pipeline/${pipelineName}/${handleID.split('.').join('/')}`)
        }
      />
    </SolidDetailScrollContainer>
  );
};

export const UsedSolidDetails: React.FunctionComponent<{
  name: string;
  onClickInvocation: (arg: SidebarSolidInvocationInfo) => void;
}> = ({name, onClickInvocation}) => {
  const repoContext = React.useContext(DagsterRepositoryContext);
  const repositorySelector = useRepositorySelector();
  const queryResult = useQuery<UsedSolidDetailsQuery>(USED_SOLID_DETAILS_QUERY, {
    skip: !repoContext?.repository || !repoContext?.repositoryLocation,
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
