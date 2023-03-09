import {gql, useQuery} from '@apollo/client';
import {
  Alert,
  Box,
  ButtonLink,
  CaptionMono,
  Colors,
  Group,
  Heading,
  Icon,
  MiddleTruncate,
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
import {Link, useParams, useRouteMatch} from 'react-router-dom';
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

import {ResourceTabs} from './ResourceTabs';
import {
  ResourceRootQuery,
  ResourceRootQueryVariables,
  ResourceDetailsFragment,
} from './types/ResourceRoot.types';

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

  const numParentResources =
    queryResult.data?.topLevelResourceDetailsOrError.__typename === 'ResourceDetails'
      ? queryResult.data?.topLevelResourceDetailsOrError.parentResources.length
      : 0;

  const tab = useRouteMatch<{tab?: string; selector: string}>([
    '/locations/:repoPath/resources/:name/:tab?',
  ])?.params.tab;

  return (
    <Page style={{height: '100%', overflow: 'hidden'}}>
      <PageHeader
        title={<Heading>{displayName}</Heading>}
        tabs={
          <ResourceTabs
            repoAddress={repoAddress}
            resourceName={resourceName}
            numParentResources={numParentResources}
          />
        }
      />
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

          const resourceTypeSuccinct = succinctType(topLevelResourceDetailsOrError.resourceType);

          return (
            <div style={{height: '100%', display: 'flex'}}>
              <SplitPanelContainer
                identifier="explorer"
                firstInitialPercent={50}
                firstMinSize={400}
                first={
                  <div style={{overflowY: 'scroll'}}>
                    {tab === 'uses' ? (
                      <ResourceUses
                        resourceDetails={topLevelResourceDetailsOrError}
                        repoAddress={repoAddress}
                      />
                    ) : (
                      <ResourceConfig
                        resourceDetails={topLevelResourceDetailsOrError}
                        repoAddress={repoAddress}
                      />
                    )}
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

const ResourceConfig: React.FC<{
  resourceDetails: ResourceDetailsFragment;
  repoAddress: RepoAddress;
}> = (props) => {
  const {resourceDetails, repoAddress} = props;

  const configuredValues = Object.fromEntries(
    resourceDetails.configuredValues.map((cv) => [cv.key, {value: cv.value, type: cv.type}]),
  );
  const nestedResources = resourceDetails.nestedResources;

  return (
    <>
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
                const resourceEntry =
                  resource.type === 'TOP_LEVEL' && resource.resource ? (
                    <ResourceEntry
                      url={workspacePathFromAddress(repoAddress, `/resources/${resource.name}`)}
                      name={resourceDisplayName(resource.resource) || ''}
                      description={resource.resource.description || undefined}
                    />
                  ) : (
                    <ResourceEntry name={resource.name} description={undefined} />
                  );

                return (
                  <tr key={resource.name}>
                    <td>
                      <Box flex={{direction: 'column', gap: 4, alignItems: 'flex-start'}}>
                        <strong>{resource.name}</strong>
                      </Box>
                    </td>
                    <td colSpan={2}>{resourceEntry}</td>
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
            {resourceDetails.configFields.map((field) => {
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
                    <Box flex={{direction: 'column', gap: 4, alignItems: 'flex-start'}}>
                      <strong>{field.name}</strong>
                      <div style={{fontSize: 12, color: Colors.Gray700}}>{field.description}</div>
                    </Box>
                  </td>
                  <td>{remapName(field.configTypeKey)}</td>
                  <td>
                    <Box flex={{direction: 'row', justifyContent: 'space-between'}}>
                      <Tooltip content={<>Default: {defaultValue}</>} canShow={!isDefault}>
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
    </>
  );
};

const ResourceUses: React.FC<{
  resourceDetails: ResourceDetailsFragment;
  repoAddress: RepoAddress;
}> = (props) => {
  const {resourceDetails, repoAddress} = props;

  const parentResources = resourceDetails.parentResources;
  return (
    <>
      <Box>
        <SectionHeader>
          <Subheading>Parent resources</Subheading>
        </SectionHeader>
        <Table>
          <thead>
            <tr>
              <th>Resource</th>
            </tr>
          </thead>
          <tbody>
            {parentResources.map((resource) => {
              return (
                resource.resource && (
                  <tr key={resource.name}>
                    <td colSpan={2}>
                      <ResourceEntry
                        url={workspacePathFromAddress(repoAddress, `/resources/${resource.name}`)}
                        name={resourceDisplayName(resource.resource) || ''}
                        description={resource.resource.description || undefined}
                      />
                    </td>
                  </tr>
                )
              );
            })}
          </tbody>
        </Table>
      </Box>
    </>
  );
};

export const ResourceEntry: React.FC<{
  name: string;
  url?: string;
  description?: string;
}> = (props) => {
  const {url, name, description} = props;

  return (
    <Box flex={{direction: 'column'}}>
      <Box
        flex={{direction: 'row', alignItems: 'center', display: 'inline-flex', gap: 4}}
        style={{maxWidth: '100%'}}
      >
        <Icon name="resource" color={Colors.Blue700} />
        <div style={{maxWidth: '100%', whiteSpace: 'nowrap', fontWeight: 500}}>
          {url ? (
            <Link to={url} style={{overflow: 'hidden'}}>
              <MiddleTruncate text={name} />
            </Link>
          ) : (
            <MiddleTruncate text={name} />
          )}
        </div>
      </Box>
      <CaptionMono>{description}</CaptionMono>
    </Box>
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
export const RESOURCE_DETAILS_FRAGMENT = gql`
  fragment ResourceDetailsFragment on ResourceDetails {
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
      type
      resource {
        name
        resourceType
        description
      }
    }
    parentResources {
      name
      resource {
        name
        resourceType
        description
      }
    }
    resourceType
  }
`;
const RESOURCE_ROOT_QUERY = gql`
  query ResourceRootQuery($resourceSelector: ResourceSelector!) {
    topLevelResourceDetailsOrError(resourceSelector: $resourceSelector) {
      ...ResourceDetailsFragment
      ...PythonErrorFragment
    }
  }
  ${RESOURCE_DETAILS_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;
