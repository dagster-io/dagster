import {gql, useQuery} from '@apollo/client';
// eslint-disable-next-line no-restricted-imports
import {Collapse} from '@blueprintjs/core';
import {
  Body,
  Body2,
  Box,
  Button,
  ButtonLink,
  Caption,
  Colors,
  ConfigTypeSchema,
  Icon,
  IconName,
  MiddleTruncate,
  NonIdealState,
  Subtitle1,
  Subtitle2,
  Tag,
  UnstyledButton,
} from '@dagster-io/ui-components';
import dayjs from 'dayjs';
import React, {useContext, useMemo, useState} from 'react';
import {Link} from 'react-router-dom';

import {AssetDefinedInMultipleReposNotice} from './AssetDefinedInMultipleReposNotice';
import {AssetEventMetadataEntriesTable} from './AssetEventMetadataEntriesTable';
import {metadataForAssetNode} from './AssetMetadata';
import {insitigatorsByType} from './AssetNodeInstigatorTag';
import {DependsOnSelfBanner} from './DependsOnSelfBanner';
import {OverdueTag, freshnessPolicyDescription} from './OverdueTag';
import {UnderlyingOpsOrGraph} from './UnderlyingOpsOrGraph';
import {asAssetKeyInput} from './asInput';
import {AssetChecksStatusSummary} from './asset-checks/AssetChecksStatusSummary';
import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {globalAssetGraphPathForAssetsAndDescendants} from './globalAssetGraphPathToString';
import {AssetNodeDefinitionFragment} from './types/AssetNodeDefinition.types';
import {
  AssetOverviewMetadataEventsQuery,
  AssetOverviewMetadataEventsQueryVariables,
} from './types/AssetNodeOverview.types';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {COMMON_COLLATOR} from '../app/Util';
import {Timestamp} from '../app/time/Timestamp';
import {StatusCase} from '../asset-graph/AssetNodeStatusContent';
import {AssetRunLink} from '../asset-graph/AssetRunLinking';
import {
  LiveDataForNode,
  displayNameForAssetKey,
  isHiddenAssetGroupJob,
  sortAssetKeys,
  tokenForAssetKey,
} from '../asset-graph/Utils';
import {StatusDot} from '../asset-graph/sidebar/StatusDot';
import {StatusCaseDot} from '../asset-graph/sidebar/util';
import {AssetNodeForGraphQueryFragment} from '../asset-graph/types/useAssetGraphData.types';
import {DagsterTypeSummary} from '../dagstertype/DagsterType';
import {AssetComputeKindTag} from '../graph/OpTags';
import {useStateWithStorage} from '../hooks/useStateWithStorage';
import {METADATA_ENTRY_FRAGMENT} from '../metadata/MetadataEntry';
import {TableSchema, isCanonicalTableSchemaEntry} from '../metadata/TableSchema';
import {RepositoryLink} from '../nav/RepositoryLink';
import {ScheduleOrSensorTag} from '../nav/ScheduleOrSensorTag';
import {Description} from '../pipelines/Description';
import {PipelineReference} from '../pipelines/PipelineReference';
import {titleForRun} from '../runs/RunUtils';
import {WorkspaceContext} from '../workspace/WorkspaceContext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

export const AssetNodeOverview = ({
  assetNode,
  upstream,
  downstream,
  liveData,
  dependsOnSelf,
}: {
  assetNode: AssetNodeDefinitionFragment;
  upstream: AssetNodeForGraphQueryFragment[] | null;
  downstream: AssetNodeForGraphQueryFragment[] | null;
  liveData: LiveDataForNode | undefined;
  dependsOnSelf: boolean;
}) => {
  const repoAddress = buildRepoAddress(
    assetNode.repository.name,
    assetNode.repository.location.name,
  );
  const location = useLocationForRepoAddress(repoAddress);

  const {assetType, assetMetadata} = metadataForAssetNode(assetNode);
  const {schedules, sensors} = useMemo(() => insitigatorsByType(assetNode), [assetNode]);
  const configType = assetNode.configField?.configType;
  const assetConfigSchema = configType && configType.key !== 'Any' ? configType : null;
  const visibleJobNames = assetNode.jobNames.filter((jobName) => !isHiddenAssetGroupJob(jobName));

  const assetNodeLoadTimestamp = location ? location.updatedTimestamp * 1000 : undefined;
  const latestPartitionEvents = useLatestPartitionEvents(
    assetNode,
    assetNodeLoadTimestamp,
    liveData,
  );

  const tableSchema = [...(latestPartitionEvents.materialization?.metadataEntries || [])].find(
    isCanonicalTableSchemaEntry,
  );

  return (
    <Box
      flex={{direction: 'row', gap: 8}}
      style={{width: '100%', height: '100%', overflowY: 'auto'}}
    >
      <Box padding={{horizontal: 24, vertical: 12}} flex={{direction: 'column'}} style={{flex: 1}}>
        <LargeCollapsibleSection header="Status" icon="status">
          <Box flex={{direction: 'row'}}>
            <Box flex={{direction: 'column', gap: 6}} style={{width: '50%'}}>
              <Subtitle2>
                Latest {assetNode?.isSource ? 'observation' : 'materialization'}
              </Subtitle2>
              <Box flex={{gap: 8, alignItems: 'center'}}>
                <SimpleAssetStatus liveData={liveData} assetNode={assetNode} />
                {assetNode && assetNode.freshnessPolicy && (
                  <OverdueTag policy={assetNode.freshnessPolicy} assetKey={assetNode.assetKey} />
                )}
              </Box>
            </Box>
            {liveData?.assetChecks.length ? (
              <Box flex={{direction: 'column', gap: 6}} style={{width: '50%'}}>
                <Subtitle2>Check results</Subtitle2>
                <AssetChecksStatusSummary liveData={liveData} rendering="tags" />
              </Box>
            ) : undefined}
          </Box>
        </LargeCollapsibleSection>
        <LargeCollapsibleSection header="Description" icon="sticky_note">
          {assetNode.description ? (
            <Description description={assetNode.description} maxHeight={260} />
          ) : (
            <Caption color={Colors.textLight()}>No description provided</Caption>
          )}
        </LargeCollapsibleSection>
        <LargeCollapsibleSection header="Columns" icon="view_column">
          {tableSchema ? (
            <TableSchema
              schema={tableSchema.schema}
              schemaLoadTimestamp={latestPartitionEvents.materialization?.timestamp}
            />
          ) : (
            <Caption color={Colors.textLight()}>No table schema</Caption>
          )}
        </LargeCollapsibleSection>
        <LargeCollapsibleSection header="Metadata" icon="view_list">
          <AssetEventMetadataEntriesTable
            showHeader
            showTimestamps
            showFilter
            hideTableSchema
            observations={
              latestPartitionEvents.observation && latestPartitionEvents.materialization
                ? [latestPartitionEvents.observation]
                : []
            }
            definitionMetadata={assetMetadata}
            definitionLoadTimestamp={assetNodeLoadTimestamp}
            event={
              latestPartitionEvents.materialization || latestPartitionEvents.observation || null
            }
          />
        </LargeCollapsibleSection>
        <LargeCollapsibleSection
          header="Lineage"
          icon="account_tree"
          right={
            <Link
              to={globalAssetGraphPathForAssetsAndDescendants([assetNode.assetKey])}
              onClick={(e) => e.stopPropagation()}
            >
              <Box flex={{gap: 4, alignItems: 'center'}}>View in graph</Box>
            </Link>
          }
        >
          {dependsOnSelf && (
            <Box padding={{bottom: 12}}>
              <DependsOnSelfBanner />
            </Box>
          )}

          <Box flex={{direction: 'row'}}>
            <Box flex={{direction: 'column', gap: 6}} style={{width: '50%'}}>
              <Subtitle2>Upstream assets</Subtitle2>
              {upstream?.length ? (
                <AssetLinksWithStatus assets={upstream} />
              ) : (
                <Box>
                  <NoValue />
                </Box>
              )}
            </Box>
            <Box flex={{direction: 'column', gap: 6}} style={{width: '50%'}}>
              <Subtitle2>Downstream assets</Subtitle2>
              {downstream?.length ? (
                <AssetLinksWithStatus assets={downstream} />
              ) : (
                <Box>
                  <NoValue />
                </Box>
              )}
            </Box>
          </Box>
        </LargeCollapsibleSection>
      </Box>
      <Box
        style={{width: '30%'}}
        border={{side: 'left'}}
        flex={{direction: 'column'}}
        padding={{left: 24, vertical: 12, right: 12}}
      >
        <LargeCollapsibleSection header="Definition" icon="info">
          <Box flex={{direction: 'column', gap: 12}}>
            <AttributeAndValue label="Key">
              {displayNameForAssetKey(assetNode.assetKey)}
            </AttributeAndValue>

            <AttributeAndValue label="Group">
              <Tag icon="asset_group">
                <Link
                  to={workspacePathFromAddress(repoAddress, `/asset-groups/${assetNode.groupName}`)}
                >
                  {assetNode.groupName}
                </Link>
              </Tag>
            </AttributeAndValue>

            <AttributeAndValue label="Code location">
              <Box flex={{direction: 'column'}}>
                <AssetDefinedInMultipleReposNotice
                  assetKey={assetNode.assetKey}
                  loadedFromRepo={repoAddress}
                />
                <RepositoryLink repoAddress={repoAddress} />
                {location && (
                  <Caption color={Colors.textLighter()}>
                    Loaded {dayjs.unix(location.updatedTimestamp).fromNow()}
                  </Caption>
                )}
              </Box>
            </AttributeAndValue>
            <AttributeAndValue label="Compute kind">
              {assetNode.computeKind && (
                <AssetComputeKindTag
                  style={{position: 'relative'}}
                  definition={assetNode}
                  reduceColor
                />
              )}
            </AttributeAndValue>
          </Box>
        </LargeCollapsibleSection>
        <LargeCollapsibleSection header="Automation details" icon="auto_materialize_policy">
          <Box flex={{direction: 'column', gap: 12}}>
            <AttributeAndValue label="Jobs">
              {visibleJobNames.map((jobName) => (
                <Tag key={jobName}>
                  <PipelineReference
                    isJob
                    showIcon
                    pipelineName={jobName}
                    pipelineHrefContext={repoAddress}
                  />
                </Tag>
              ))}
            </AttributeAndValue>
            <AttributeAndValue label="Sensors">
              {sensors.length > 0 && (
                <ScheduleOrSensorTag
                  repoAddress={repoAddress}
                  sensors={sensors}
                  showSwitch={false}
                />
              )}
            </AttributeAndValue>
            <AttributeAndValue label="Schedules">
              {schedules.length > 0 && (
                <ScheduleOrSensorTag
                  repoAddress={repoAddress}
                  schedules={schedules}
                  showSwitch={false}
                />
              )}
            </AttributeAndValue>
          </Box>
        </LargeCollapsibleSection>
        <LargeCollapsibleSection header="Compute details" icon="settings" collapsedByDefault>
          <Box flex={{direction: 'column', gap: 12}}>
            <AttributeAndValue label="Computed by">
              <Tag>
                <UnderlyingOpsOrGraph
                  assetNode={assetNode}
                  repoAddress={repoAddress}
                  hideIfRedundant={false}
                />
              </Tag>
            </AttributeAndValue>

            <AttributeAndValue label="Code version">{assetNode.opVersion}</AttributeAndValue>

            <AttributeAndValue label="Resources">
              {[...assetNode.requiredResources]
                .sort((a, b) => COMMON_COLLATOR.compare(a.resourceKey, b.resourceKey))
                .map((resource) => (
                  <Tag key={resource.resourceKey}>
                    <Icon name="resource" color={Colors.accentGray()} />
                    {repoAddress ? (
                      <Link
                        to={workspacePathFromAddress(
                          repoAddress,
                          `/resources/${resource.resourceKey}`,
                        )}
                      >
                        {resource.resourceKey}
                      </Link>
                    ) : (
                      resource.resourceKey
                    )}
                  </Tag>
                ))}
            </AttributeAndValue>

            <AttributeAndValue label="Config schema">
              {assetConfigSchema && (
                <ButtonLink
                  onClick={() => {
                    showCustomAlert({
                      title: 'Config schema',
                      body: (
                        <ConfigTypeSchema
                          type={assetConfigSchema}
                          typesInScope={assetConfigSchema.recursiveConfigTypes}
                        />
                      ),
                    });
                  }}
                >
                  View config details
                </ButtonLink>
              )}
            </AttributeAndValue>

            <AttributeAndValue label="Type">
              {assetType && assetType.displayName !== 'Any' && (
                <ButtonLink
                  onClick={() => {
                    showCustomAlert({
                      title: 'Type summary',
                      body: <DagsterTypeSummary type={assetType} />,
                    });
                  }}
                >
                  View type details
                </ButtonLink>
              )}
            </AttributeAndValue>

            <AttributeAndValue label="Freshness policy">
              {assetNode.autoMaterializePolicy && (
                <Body>{freshnessPolicyDescription(assetNode.freshnessPolicy)}</Body>
              )}
            </AttributeAndValue>

            <AttributeAndValue label="Backfill policy">
              {assetNode.backfillPolicy?.description}
            </AttributeAndValue>
          </Box>
        </LargeCollapsibleSection>
      </Box>
    </Box>
  );
};

const AttributeAndValue = ({label, children}: {label: string; children: React.ReactNode}) => (
  <Box flex={{direction: 'column', gap: 6, alignItems: 'flex-start'}}>
    <Subtitle2>{label}</Subtitle2>
    <Body2>
      <Box flex={{gap: 2}}>
        {children && !(children instanceof Array && children.length === 0) ? children : <NoValue />}
      </Box>
    </Body2>
  </Box>
);

const NoValue = () => <Body2 color={Colors.textLighter()}>–</Body2>;

export const AssetNodeOverviewEmpty = () => (
  <Box padding={{vertical: 32}}>
    <NonIdealState
      title="No definition"
      description="This asset doesn't have a software definition in any of your code locations."
      icon="materialization"
    />
  </Box>
);

export const AssetNodeOverviewLoading = () => (
  <Box padding={{vertical: 32}}>
    <NonIdealState
      title="No definition"
      description="This asset doesn't have a software definition in any of your code locations."
      icon="materialization"
    />
  </Box>
);

const LargeCollapsibleSection = ({
  header,
  icon,
  children,
  right,
  collapsedByDefault = false,
}: {
  header: string;
  icon: IconName;
  children: React.ReactNode;
  right?: React.ReactNode;
  collapsedByDefault?: boolean;
}) => {
  const [isCollapsed, setIsCollapsed] = useStateWithStorage<boolean>(
    `collapsible-section-${header}`,
    (storedValue) =>
      storedValue === true || storedValue === false ? storedValue : collapsedByDefault,
  );

  return (
    <Box flex={{direction: 'column'}}>
      <UnstyledButton onClick={() => setIsCollapsed(!isCollapsed)}>
        <Box
          flex={{direction: 'row', alignItems: 'center', gap: 6}}
          padding={{vertical: 12, right: 12}}
          border="bottom"
        >
          <Icon size={20} name={icon} />
          <Subtitle1 style={{flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis'}}>
            {header}
          </Subtitle1>
          {right}
          <Icon
            name="arrow_drop_down"
            size={20}
            style={{transform: isCollapsed ? 'rotate(-90deg)' : 'rotate(0deg)'}}
          />
        </Box>
      </UnstyledButton>
      <Collapse isOpen={!isCollapsed}>
        <Box padding={{vertical: 12}}>{children}</Box>
      </Collapse>
    </Box>
  );
};

/** We explicitly don't want to share partition-level information with stakeholders,
 * so this status component exposes only basic "materializing, success, failed, missing"
 * states.
 */
const SimpleAssetStatus = ({
  liveData,
  assetNode,
}: {
  liveData: LiveDataForNode | undefined;
  assetNode: AssetNodeDefinitionFragment;
}) => {
  if (!liveData) {
    return <NoValue />;
  }

  if ((liveData.inProgressRunIds || []).length > 0) {
    return (
      <Caption>
        Materializing in{' '}
        <AssetRunLink assetKey={assetNode.assetKey} runId={liveData.inProgressRunIds[0]!} />
      </Caption>
    );
  }

  if (liveData.runWhichFailedToMaterialize) {
    return (
      <Tag intent="danger">
        <Box flex={{gap: 4, alignItems: 'center'}}>
          <StatusCaseDot statusCase={StatusCase.FAILED_MATERIALIZATION} />
          Failed in
          <AssetRunLink
            assetKey={assetNode.assetKey}
            runId={liveData.runWhichFailedToMaterialize.id}
          >
            <Box style={{color: Colors.textRed()}}>
              {titleForRun(liveData.runWhichFailedToMaterialize)}
            </Box>
          </AssetRunLink>
        </Box>
      </Tag>
    );
  }
  if (liveData.lastMaterialization) {
    return (
      <Tag intent="success">
        <Box flex={{gap: 4, alignItems: 'center'}}>
          <StatusCaseDot statusCase={StatusCase.MATERIALIZED} />
          <AssetRunLink
            assetKey={assetNode.assetKey}
            runId={liveData.lastMaterialization.runId}
            event={{
              timestamp: liveData.lastMaterialization.timestamp,
              stepKey: liveData.stepKey,
            }}
          >
            <Box style={{color: Colors.textGreen()}} flex={{gap: 4}}>
              <Timestamp timestamp={{ms: Number(liveData.lastMaterialization.timestamp)}} />
            </Box>
          </AssetRunLink>
        </Box>
      </Tag>
    );
  }
  if (liveData.lastObservation && assetNode.isSource) {
    return (
      <Tag intent="none">
        <Timestamp timestamp={{ms: Number(liveData.lastObservation.timestamp)}} />
      </Tag>
    );
  }

  return (
    <Caption color={Colors.textLighter()}>
      {assetNode.isSource ? 'Never observed' : 'Never materialized'}
    </Caption>
  );
};

const AssetLinksWithStatus = ({
  assets,
  displayedByDefault = 20,
}: {
  assets: AssetNodeForGraphQueryFragment[];
  displayedByDefault?: number;
}) => {
  const [displayedCount, setDisplayedCount] = useState(displayedByDefault);

  const displayed = React.useMemo(
    () => assets.sort((a, b) => sortAssetKeys(a.assetKey, b.assetKey)).slice(0, displayedCount),
    [assets, displayedCount],
  );

  return (
    <Box flex={{direction: 'column', gap: 6}}>
      {displayed.map((asset) => (
        <Link to={assetDetailsPathForKey(asset.assetKey)} key={tokenForAssetKey(asset.assetKey)}>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'auto minmax(0, 1fr)',
              gap: '6px',
              alignItems: 'center',
            }}
          >
            <StatusDot node={{assetKey: asset.assetKey, definition: asset}} />
            <MiddleTruncate text={displayNameForAssetKey(asset.assetKey)} />
          </div>
        </Link>
      ))}
      <Box>
        {displayed.length < assets.length ? (
          <Button small onClick={() => setDisplayedCount(Number.MAX_SAFE_INTEGER)}>
            Show {assets.length - displayed.length} more
          </Button>
        ) : displayed.length > displayedByDefault ? (
          <Button small onClick={() => setDisplayedCount(displayedByDefault)}>
            Show less
          </Button>
        ) : undefined}
      </Box>
    </Box>
  );
};

function useLocationForRepoAddress(repoAddress: RepoAddress) {
  const {locationEntries} = useContext(WorkspaceContext);
  return locationEntries.find(
    (r) =>
      r.locationOrLoadError?.__typename === 'RepositoryLocation' &&
      r.locationOrLoadError.repositories.some(
        (repo) => repo.name === repoAddress.name && repo.location.name === repoAddress.location,
      ),
  );
}

function useLatestPartitionEvents(
  assetNode: AssetNodeDefinitionFragment,
  assetNodeLoadTimestamp: number | undefined,
  liveData: LiveDataForNode | undefined,
) {
  const refreshHint = liveData?.lastMaterialization?.timestamp;

  const {data, refetch} = useQuery<
    AssetOverviewMetadataEventsQuery,
    AssetOverviewMetadataEventsQueryVariables
  >(ASSET_OVERVIEW_METADATA_EVENTS_QUERY, {
    variables: {assetKey: asAssetKeyInput(assetNode)},
  });

  React.useEffect(() => {
    refetch();
  }, [refetch, refreshHint, assetNodeLoadTimestamp]);

  const materialization =
    data?.assetOrError.__typename === 'Asset'
      ? data.assetOrError.assetMaterializations[0]
      : undefined;
  const observation =
    data?.assetOrError.__typename === 'Asset' ? data.assetOrError.assetObservations[0] : undefined;

  return {materialization, observation};
}

export const ASSET_OVERVIEW_METADATA_EVENTS_QUERY = gql`
  query AssetOverviewMetadataEventsQuery($assetKey: AssetKeyInput!) {
    assetOrError(assetKey: $assetKey) {
      ... on Asset {
        id
        assetMaterializations(limit: 1, partitionInLast: 1) {
          timestamp
          runId
          metadataEntries {
            ...MetadataEntryFragment
          }
        }
        assetObservations(limit: 1, partitionInLast: 1) {
          timestamp
          runId
          metadataEntries {
            ...MetadataEntryFragment
          }
        }
      }
    }
  }

  ${METADATA_ENTRY_FRAGMENT}
`;
