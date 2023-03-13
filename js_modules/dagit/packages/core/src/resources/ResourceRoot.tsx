import {gql, useQuery} from '@apollo/client';
import {
  Alert,
  Box,
  ButtonLink,
  Colors,
  Group,
  Heading,
  Mono,
  Page,
  PageHeader,
  SplitPanelContainer,
  Subheading,
  Table,
  Tag,
  Tooltip,
} from '@dagster-io/ui';
import * as React from 'react';
import {Link, useParams} from 'react-router-dom';
import styled from 'styled-components/macro';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {RepositoryLink} from '../nav/RepositoryLink';
import {SidebarSection} from '../pipelines/SidebarComponents';
import {Loading} from '../ui/Loading';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {ResourceRootQuery, ResourceRootQueryVariables} from './types/ResourceRoot.types';

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

const succinctType = (resourceType: string | undefined): string | null => {
  return resourceType?.split('.').pop() || null;
};

const resourceDisplayName = (
  resource: undefined | {name: string; resourceType: string},
): string | null => {
  if (!resource) {
    return null;
  }
  return resource.name.startsWith('_nested_')
    ? succinctType(resource?.resourceType)
    : resource.name;
};

const SectionHeader: React.FC = (props) => {
  return (
    <Box
      padding={{left: 24, vertical: 16}}
      background={Colors.Gray50}
      border={{width: 1, color: Colors.KeylineGray, side: 'all'}}
    >
      {props.children}
    </Box>
  );
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
  const queryResult = useQuery<ResourceRootQuery, ResourceRootQueryVariables>(RESOURCE_ROOT_QUERY, {
    variables: {
      resourceSelector,
    },
  });

  const displayName =
    (queryResult.data?.topLevelResourceDetailsOrError.__typename === 'ResourceDetails' &&
      resourceDisplayName(queryResult.data?.topLevelResourceDetailsOrError)) ||
    resourceName;
  return (
    <Page style={{height: '100%', overflow: 'hidden'}}>
      <PageHeader title={<Heading>{displayName}</Heading>} />
      <Loading queryResult={queryResult} allowStaleData={true}>
        {({topLevelResourceDetailsOrError}) => {
          if (topLevelResourceDetailsOrError.__typename !== 'ResourceDetails') {
            let message: string | null = null;
            if (topLevelResourceDetailsOrError.__typename === 'PythonError') {
              message = topLevelResourceDetailsOrError.message;
            }

            return (
              <Alert
                intent="warning"
                title={
                  <Group direction="row" spacing={4}>
                    <div>Could not load resource.</div>
                    {message && (
                      <ButtonLink
                        color={Colors.Link}
                        underline="always"
                        onClick={() => {
                          showCustomAlert({
                            title: 'Python error',
                            body: message,
                          });
                        }}
                      >
                        View error
                      </ButtonLink>
                    )}
                  </Group>
                }
              />
            );
          }

          const configuredValues = Object.fromEntries(
            topLevelResourceDetailsOrError.configuredValues.map((cv) => [
              cv.key,
              {value: cv.value, type: cv.type},
            ]),
          );
          const nestedResources = topLevelResourceDetailsOrError.nestedResources;
          const resourceTypeSuccinct = succinctType(topLevelResourceDetailsOrError.resourceType);
          return (
            <div style={{height: '100%', display: 'flex'}}>
              <SplitPanelContainer
                identifier="explorer"
                firstInitialPercent={50}
                firstMinSize={400}
                first={
                  <div style={{overflowY: 'scroll'}}>
                    {nestedResources.length > 0 && (
                      <Box>
                        <SectionHeader>
                          <Subheading>Resource dependencies</Subheading>
                        </SectionHeader>
                        <Table>
                          <thead>
                            <tr>
                              <th style={{width: 120}}>Key</th>
                              <th style={{width: 180}}>Resource</th>
                            </tr>
                          </thead>
                          <tbody>
                            {nestedResources.map((resource) => {
                              return (
                                <tr key={resource.name}>
                                  <td>
                                    <strong>{resource.name}</strong>
                                  </td>
                                  <td colSpan={2}>
                                    <Tag icon="resource">
                                      {' '}
                                      <Link
                                        to={workspacePathFromAddress(
                                          repoAddress,
                                          `/resources/${resource.name}`,
                                        )}
                                      >
                                        {resourceDisplayName(resource.resource)}
                                      </Link>
                                    </Tag>
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </Table>
                      </Box>
                    )}
                    <Box>
                      <SectionHeader>
                        <Subheading>Configuration</Subheading>
                      </SectionHeader>
                      <Table>
                        <thead>
                          <tr>
                            <th style={{width: 120}}>Key</th>
                            <th style={{width: 90}}>Type</th>
                            <th style={{width: 90}}>Value</th>
                          </tr>
                        </thead>
                        <tbody>
                          {topLevelResourceDetailsOrError.configFields.map((field) => {
                            const defaultValue = field.defaultValueAsJson;
                            const type = configuredValues.hasOwnProperty(field.name)
                              ? configuredValues[field.name].type
                              : null;
                            const actualValue = configuredValues.hasOwnProperty(field.name)
                              ? configuredValues[field.name].value
                              : defaultValue;

                            const isDefault = type === 'VALUE' && defaultValue === actualValue;
                            return (
                              <tr key={field.name}>
                                <td>
                                  <Box
                                    flex={{direction: 'column', gap: 4, alignItems: 'flex-start'}}
                                  >
                                    <strong>{field.name}</strong>
                                    <div style={{fontSize: 12, color: Colors.Gray700}}>
                                      {field.description}
                                    </div>
                                  </Box>
                                </td>
                                <td>{remapName(field.configTypeKey)}</td>
                                <td>
                                  <Box flex={{direction: 'row', gap: 8}}>
                                    <Tooltip
                                      content={<>Default: {defaultValue}</>}
                                      canShow={!isDefault}
                                    >
                                      {type === 'ENV_VAR' ? <Tag>{actualValue}</Tag> : actualValue}
                                    </Tooltip>
                                    {isDefault && <Tag>Default</Tag>}
                                    {type === 'ENV_VAR' && <Tag intent="success">Env var</Tag>}
                                  </Box>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </Table>
                    </Box>
                  </div>
                }
                second={
                  <RightInfoPanel>
                    <RightInfoPanelContent>
                      <Box
                        flex={{gap: 4, direction: 'column'}}
                        margin={{left: 24, right: 12, vertical: 16}}
                      >
                        <Heading>{displayName}</Heading>

                        <Tooltip content={topLevelResourceDetailsOrError.resourceType || ''}>
                          <Mono>{resourceTypeSuccinct}</Mono>
                        </Tooltip>
                      </Box>

                      <SidebarSection title="Definition">
                        <Box padding={{vertical: 16, horizontal: 24}}>
                          <Tag icon="resource">
                            Resource in{' '}
                            <RepositoryLink repoAddress={repoAddress} showRefresh={false} />
                          </Tag>
                        </Box>
                      </SidebarSection>
                      {topLevelResourceDetailsOrError.description ? (
                        <SidebarSection title="Description">
                          <Box padding={{vertical: 16, horizontal: 24}}>
                            {topLevelResourceDetailsOrError.description}
                          </Box>
                        </SidebarSection>
                      ) : null}
                    </RightInfoPanelContent>
                  </RightInfoPanel>
                }
              />
            </div>
          );
        }}
      </Loading>
    </Page>
  );
};

export const RightInfoPanel = styled.div`
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
    topLevelResourceDetailsOrError(resourceSelector: $resourceSelector) {
      ... on ResourceDetails {
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
          type
        }
        nestedResources {
          name
          resource {
            name
            resourceType
          }
        }
        resourceType
      }
      ...PythonErrorFragment
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
`;
