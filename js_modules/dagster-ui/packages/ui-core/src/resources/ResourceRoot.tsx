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
  NonIdealState,
  Page,
  PageHeader,
  SplitPanelContainer,
  Subheading,
  Table,
  Tag,
  Tooltip,
} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link, useParams, useRouteMatch} from 'react-router-dom';
import styled from 'styled-components';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {useTrackPageView} from '../app/analytics';
import {AssetLink} from '../assets/AssetLink';
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

export const succinctType = (resourceType: string | undefined): string | null => {
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

const SectionHeader = (props: {children: React.ReactNode}) => {
  return (
    <Box padding={{left: 24, vertical: 16}} background={Colors.Gray50} border="all">
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

  const numUses =
    queryResult.data?.topLevelResourceDetailsOrError.__typename === 'ResourceDetails'
      ? queryResult.data.topLevelResourceDetailsOrError.parentResources.length +
        queryResult.data.topLevelResourceDetailsOrError.assetKeysUsing.length +
        queryResult.data.topLevelResourceDetailsOrError.jobsOpsUsing.length +
        queryResult.data.topLevelResourceDetailsOrError.schedulesUsing.length +
        queryResult.data.topLevelResourceDetailsOrError.sensorsUsing.length
      : 0;

  const tab = useRouteMatch<{tab?: string}>(['/locations/:repoPath/resources/:name/:tab?'])?.params
    .tab;

  return (
    <Page style={{height: '100%', overflow: 'hidden'}}>
      <PageHeader
        title={<Heading>{displayName}</Heading>}
        tabs={
          <ResourceTabs repoAddress={repoAddress} resourceName={resourceName} numUses={numUses} />
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
                identifier="resource-explorer"
                firstInitialPercent={50}
                firstMinSize={400}
                first={
                  <Box padding={{bottom: 48}} style={{overflowY: 'auto'}}>
                    {tab === 'uses' ? (
                      <ResourceUses
                        resourceDetails={topLevelResourceDetailsOrError}
                        repoAddress={repoAddress}
                        numUses={numUses}
                      />
                    ) : (
                      <ResourceConfig
                        resourceDetails={topLevelResourceDetailsOrError}
                        repoAddress={repoAddress}
                      />
                    )}
                  </Box>
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
                      key={resource.name}
                      url={workspacePathFromAddress(repoAddress, `/resources/${resource.name}`)}
                      name={resourceDisplayName(resource.resource) || ''}
                      description={resource.resource.description || undefined}
                    />
                  ) : (
                    <ResourceEntry key={resource.name} name={resource.name} />
                  );

                return (
                  <tr key={resource.name}>
                    <td>
                      <strong>{resource.name}</strong>
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
            {resourceDetails.configFields.length === 0 ? (
              <tr>
                <td colSpan={3}>
                  <Box padding={{vertical: 8}}>
                    <NonIdealState
                      icon="settings"
                      title="No configuration"
                      description="This resource has no configuration fields."
                    />
                  </Box>
                </td>
              </tr>
            ) : (
              resourceDetails.configFields.map((field) => {
                const defaultValue = field.defaultValueAsJson;
                const type = configuredValues.hasOwnProperty(field.name)
                  ? configuredValues[field.name]!.type
                  : null;
                const actualValue = configuredValues.hasOwnProperty(field.name)
                  ? configuredValues[field.name]!.value
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
                      <Box flex={{direction: 'row', gap: 16}}>
                        <Tooltip
                          content={<>Default: {defaultValue}</>}
                          canShow={!isDefault && !!defaultValue}
                        >
                          {type === 'ENV_VAR' ? <Tag>{actualValue}</Tag> : actualValue}
                        </Tooltip>
                        {isDefault && <Tag>Default</Tag>}
                        {type === 'ENV_VAR' && <Tag intent="success">Env var</Tag>}
                      </Box>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </Table>
      </Box>
    </>
  );
};

const ResourceUses: React.FC<{
  resourceDetails: ResourceDetailsFragment;
  repoAddress: RepoAddress;
  numUses: number;
}> = (props) => {
  const {resourceDetails, repoAddress, numUses} = props;

  if (numUses === 0) {
    return (
      <Box padding={{vertical: 16}}>
        <NonIdealState
          icon="list"
          title="No uses"
          description="This resource is not used by any assets or resources."
        />
      </Box>
    );
  }

  const parentResources = resourceDetails.parentResources;
  return (
    <>
      {parentResources.length > 0 && (
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
                      <td>
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
      )}
      {resourceDetails.assetKeysUsing.length > 0 && (
        <Box>
          <SectionHeader>
            <Subheading>Assets</Subheading>
          </SectionHeader>
          <Table>
            <thead>
              <tr>
                <th>Asset key</th>
              </tr>
            </thead>
            <tbody>
              {resourceDetails.assetKeysUsing.map((assetKey) => {
                return (
                  <tr key={assetKey.path.join('/')}>
                    <td>
                      <AssetLink key={assetKey.path.join('/')} path={assetKey.path} icon="asset" />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </Table>
        </Box>
      )}
      {resourceDetails.jobsOpsUsing.length > 0 && (
        <Box>
          <SectionHeader>
            <Subheading>Jobs</Subheading>
          </SectionHeader>
          <Table>
            <thead>
              <tr>
                <th>Job name</th>
                <th>Ops</th>
              </tr>
            </thead>
            <tbody>
              {resourceDetails.jobsOpsUsing.map((jobOps) => {
                return (
                  <tr key={jobOps.job.name}>
                    <td>
                      <Box
                        flex={{
                          direction: 'row',
                          alignItems: 'center',
                          display: 'inline-flex',
                          gap: 8,
                        }}
                        style={{maxWidth: '100%'}}
                      >
                        <Icon name="job" color={Colors.Gray400} />

                        <Link
                          to={workspacePathFromAddress(repoAddress, `/jobs/${jobOps.job.name}`)}
                        >
                          <MiddleTruncate text={jobOps.job.name} />
                        </Link>
                      </Box>
                    </td>
                    <td>
                      <Box
                        flex={{
                          direction: 'row',
                          alignItems: 'center',
                          display: 'inline-flex',
                          gap: 8,
                        }}
                        style={{maxWidth: '100%'}}
                      >
                        {jobOps.opsUsing.map((op) => (
                          <Box
                            flex={{
                              direction: 'row',
                              alignItems: 'center',
                              display: 'inline-flex',
                              gap: 8,
                            }}
                            style={{maxWidth: '100%'}}
                            key={op.handleID}
                          >
                            <Icon name="op" color={Colors.Gray400} />

                            <Link
                              to={workspacePathFromAddress(
                                repoAddress,
                                `/jobs/${jobOps.job.name}/${op.handleID.split('.').join('/')}`,
                              )}
                            >
                              <MiddleTruncate text={op.solid.name} />
                            </Link>
                          </Box>
                        ))}
                      </Box>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </Table>
        </Box>
      )}
      {[
        {
          name: 'Schedules',
          objects: resourceDetails.schedulesUsing,
          icon: <Icon name="schedule" color={Colors.Gray400} />,
        },
        {
          name: 'Sensors',
          objects: resourceDetails.sensorsUsing,
          icon: <Icon name="sensors" color={Colors.Gray400} />,
        },
      ]
        .filter(({objects}) => objects.length > 0)
        .map(({name, objects, icon}) => (
          <div key={name}>
            <SectionHeader>
              <Subheading>{name}</Subheading>
            </SectionHeader>
            <Table>
              <thead>
                <tr>
                  <th>Name</th>
                </tr>
              </thead>
              <tbody>
                {objects.map((itemName) => {
                  return (
                    <tr key={name + ':' + itemName}>
                      <td>
                        <Box
                          flex={{
                            direction: 'row',
                            alignItems: 'center',
                            display: 'inline-flex',
                            gap: 8,
                          }}
                          style={{maxWidth: '100%'}}
                        >
                          {icon}

                          <Link
                            to={workspacePathFromAddress(
                              repoAddress,
                              `/${name.toLowerCase()}/${itemName}`,
                            )}
                          >
                            <MiddleTruncate text={itemName} />
                          </Link>
                        </Box>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </Table>
          </div>
        ))}
    </>
  );
};

const ResourceEntry: React.FC<{
  name: string;
  url?: string;
  description?: string;
}> = (props) => {
  const {url, name, description} = props;

  return (
    <Box flex={{direction: 'column'}}>
      <Box flex={{direction: 'row', alignItems: 'center', gap: 4}} style={{maxWidth: '100%'}}>
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

const RightInfoPanel = styled.div`
  position: relative;

  height: 100%;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: ${Colors.White};
`;

const RightInfoPanelContent = styled.div`
  flex: 1;
  overflow-y: auto;
`;

const RESOURCE_DETAILS_FRAGMENT = gql`
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
    assetKeysUsing {
      path
    }
    schedulesUsing
    sensorsUsing
    jobsOpsUsing {
      job {
        id
        name
      }
      opsUsing {
        handleID
        solid {
          name
        }
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
