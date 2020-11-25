import {useQuery, gql} from '@apollo/client';
import {NonIdealState} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import React from 'react';

import {Loading} from 'src/Loading';
import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {SENSOR_FRAGMENT} from 'src/sensors/SensorFragment';
import {SensorsTable} from 'src/sensors/SensorsTable';
import {SensorsRootQuery} from 'src/sensors/types/SensorsRootQuery';
import {Page} from 'src/ui/Page';
import {repoAddressToSelector} from 'src/workspace/repoAddressToSelector';
import {RepoAddress} from 'src/workspace/types';

interface Props {
  repoAddress: RepoAddress;
}

export const SensorsRoot = (props: Props) => {
  const {repoAddress} = props;
  useDocumentTitle('Sensors');
  const repositorySelector = repoAddressToSelector(repoAddress);

  const queryResult = useQuery<SensorsRootQuery>(SENSORS_ROOT_QUERY, {
    variables: {
      repositorySelector: repositorySelector,
    },
    fetchPolicy: 'cache-and-network',
    pollInterval: 50 * 1000,
    partialRefetch: true,
  });

  return (
    <Page>
      <Loading queryResult={queryResult} allowStaleData={true}>
        {(result) => {
          const {sensorsOrError} = result;
          const content = () => {
            if (sensorsOrError.__typename === 'PythonError') {
              return <PythonErrorInfo error={sensorsOrError} />;
            }
            if (sensorsOrError.__typename === 'RepositoryNotFoundError') {
              return (
                <NonIdealState
                  icon={IconNames.ERROR}
                  title="Repository not found"
                  description="Could not load this repository."
                />
              );
            }
            return <SensorsTable repoAddress={repoAddress} sensors={sensorsOrError.results} />;
          };

          return <div>{content()}</div>;
        }}
      </Loading>
    </Page>
  );
};

const SENSORS_ROOT_QUERY = gql`
  query SensorsRootQuery($repositorySelector: RepositorySelector!) {
    sensorsOrError(repositorySelector: $repositorySelector) {
      __typename
      ...PythonErrorFragment
      ... on Sensors {
        results {
          id
          ...SensorFragment
        }
      }
    }
  }
  ${PythonErrorInfo.fragments.PythonErrorFragment}
  ${SENSOR_FRAGMENT}
`;
