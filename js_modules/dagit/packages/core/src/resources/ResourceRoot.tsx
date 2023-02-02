import {gql, useQuery} from '@apollo/client';
import {
  Box,
  Colors,
  Heading,
  Page,
  PageHeader,
  SplitPanelContainer,
  Table,
  Tag,
  Tooltip,
} from '@dagster-io/ui';
import * as React from 'react';
import {useParams} from 'react-router-dom';
import styled from 'styled-components/macro';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {RepositoryLink} from '../nav/RepositoryLink';
import {SidebarSection} from '../pipelines/SidebarComponents';
import {Loading} from '../ui/Loading';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {ResourceRootQuery} from './types/ResourceRoot.types';

interface Props {
  repoAddress: RepoAddress;
}

const remapName = (inName: string): string => {
  if (inName === 'StringSourceType') {
    return 'String';
  } else if (inName === 'IntSourceType') {
    return 'Int';
  } else if (inName === 'BoolSourceType') {
    return 'Bool';
  }
  return inName;
};

export const ResourceRoot: React.FC<Props> = (props) => {
  useTrackPageView();

  const {repoAddress} = props;

  const {resourceName} = useParams<{resourceName: string}>();

  useDocumentTitle(`Resource: ${resourceName}`);

  const resourceSelector = {
    ...repoAddressToSelector(repoAddress),
    resourceName,
  };
  const queryResult = useQuery<ResourceRootQuery>(RESOURCE_ROOT_QUERY, {
    variables: {
      resourceSelector,
    },
    fetchPolicy: 'cache-and-network',
    partialRefetch: true,
    notifyOnNetworkStatusChange: true,
  });

  return (
    <Page>
      <PageHeader
        title={
          <Box flex={{direction: 'row', alignItems: 'center', gap: 12}}>
            <Heading>{resourceName}</Heading>
          </Box>
        }
      />
      <Loading queryResult={queryResult} allowStaleData={true}>
        {({topLevelResourceOrError}) => {
          if (topLevelResourceOrError.__typename !== 'TopLevelResource') {
            return null;
          }

          const configuredValues = Object.fromEntries(
            topLevelResourceOrError.configuredValues.map((cv) => [cv.key, cv.value]),
          );

          return (
            <SplitPanelContainer
              identifier="explorer"
              firstInitialPercent={70}
              firstMinSize={400}
              height="calc(100% - 60px)"
              first={
                <Table>
                  <thead>
                    <tr>
                      <th style={{width: 120}}>Key</th>
                      <th style={{width: 90}}>Type</th>
                      <th style={{width: 90}}>Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    {topLevelResourceOrError.configFields.map((field) => {
                      const defaultValue = field.defaultValueAsJson;
                      const actualValue = configuredValues[field.name];

                      const isDefault = defaultValue === actualValue;

                      return (
                        <tr key={field.name}>
                          <td>
                            <Box flex={{direction: 'column', gap: 4, alignItems: 'flex-start'}}>
                              <strong>{field.name}</strong>
                              <div style={{fontSize: 12, color: Colors.Gray700}}>
                                {field.description}
                              </div>
                            </Box>
                          </td>
                          <td>{remapName(field.configTypeKey)}</td>
                          <td>
                            <Box flex={{direction: 'row', justifyContent: 'space-between'}}>
                              <Tooltip content={<>Default: {defaultValue}</>} canShow={!isDefault}>
                                {actualValue}
                              </Tooltip>
                              {isDefault && <Tag>Default</Tag>}
                            </Box>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </Table>
              }
              second={
                <RightInfoPanel>
                  <RightInfoPanelContent>
                    <Box
                      flex={{gap: 4, direction: 'column'}}
                      margin={{left: 24, right: 12, vertical: 16}}
                    >
                      <Heading>{resourceName}</Heading>
                    </Box>

                    <SidebarSection title="Definition">
                      <Box padding={{vertical: 16, horizontal: 24}}>
                        <Tag icon="resource">
                          Resource in{' '}
                          <RepositoryLink repoAddress={repoAddress} showRefresh={false} />
                        </Tag>
                      </Box>
                    </SidebarSection>
                    {topLevelResourceOrError.description ? (
                      <SidebarSection title="Description">
                        <Box padding={{vertical: 16, horizontal: 24}}>
                          {topLevelResourceOrError.description}
                        </Box>
                      </SidebarSection>
                    ) : null}
                  </RightInfoPanelContent>
                </RightInfoPanel>
              }
            />
          );
        }}
      </Loading>
    </Page>
  );
};

export const RightInfoPanel = styled.div`
  // Fixes major perofmance hit. To reproduce, add enough content to
  // the sidebar that it scrolls (via overflow-y below) and then try
  // to pan the DAG.
  position: relative;

  height: 100%;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: ${Colors.White};
`;

export const RightInfoPanelContent = styled.div`
  flex: 1;
  overflow-y: auto;
`;

const RESOURCE_ROOT_QUERY = gql`
  query ResourceRootQuery($resourceSelector: ResourceSelector!) {
    topLevelResourceOrError(resourceSelector: $resourceSelector) {
      ... on TopLevelResource {
        name
        description
        configFields {
          name
          description
          configTypeKey
          isRequired
          defaultValueAsJson
        }
        configuredValues {
          key
          value
        }
      }
      ...PythonErrorFragment
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
`;
