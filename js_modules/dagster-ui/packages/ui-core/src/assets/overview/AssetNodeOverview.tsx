import {
  Box,
  Caption,
  Colors,
  NonIdealState,
  Skeleton,
  Subtitle2,
  Tag,
} from '@dagster-io/ui-components';
import React, {useMemo} from 'react';
import {Link} from 'react-router-dom';
import {AssetAlertsSection} from 'shared/assets/AssetAlertsSection.oss';

import {AssetEventMetadataEntriesTable} from '../AssetEventMetadataEntriesTable';
import {metadataForAssetNode} from '../AssetMetadata';
import {AutomationDetailsSection} from './AutomationDetailsSection';
import {AttributeAndValue, NoValue, SectionEmptyState} from './Common';
import {ComputeDetailsSection} from './ComputeDetailsSection';
import {DefinitionSection} from './DefinitionSection';
import {LineageSection} from './LineageSection';
import {useAssetsLiveData} from '../../asset-data/AssetLiveDataProvider';
import {LiveDataForNode} from '../../asset-graph/Utils';
import {AssetNodeForGraphQueryFragment} from '../../asset-graph/types/useAssetGraphData.types';
import {IntMetadataEntry} from '../../graphql/types';
import {isCanonicalRowCountMetadataEntry} from '../../metadata/MetadataEntry';
import {TableSchema, TableSchemaAssetContext} from '../../metadata/TableSchema';
import {useRepositoryLocationForAddress} from '../../nav/useRepositoryLocationForAddress';
import {Description} from '../../pipelines/Description';
import {numberFormatter} from '../../ui/formatters';
import {buildRepoAddress} from '../../workspace/buildRepoAddress';
import {LargeCollapsibleSection} from '../LargeCollapsibleSection';
import {MaterializationTag} from '../MaterializationTag';
import {OverdueTag} from '../OverdueTag';
import {RecentUpdatesTimeline} from '../RecentUpdatesTimeline';
import {SimpleStakeholderAssetStatus} from '../SimpleStakeholderAssetStatus';
import {AssetChecksStatusSummary} from '../asset-checks/AssetChecksStatusSummary';
import {buildConsolidatedColumnSchema} from '../buildConsolidatedColumnSchema';
import {globalAssetGraphPathForAssetsAndDescendants} from '../globalAssetGraphPathToString';
import {AssetKey} from '../types';
import {AssetNodeDefinitionFragment} from '../types/AssetNodeDefinition.types';
import {AssetTableDefinitionFragment} from '../types/AssetTableFragment.types';
import {useLatestPartitionEvents} from '../useLatestPartitionEvents';
import {useRecentAssetEvents} from '../useRecentAssetEvents';

export const AssetNodeOverview = ({
  assetKey,
  assetNode,
  cachedAssetNode,
  upstream,
  downstream,
  liveData,
  dependsOnSelf,
}: {
  assetKey: AssetKey;
  assetNode: AssetNodeDefinitionFragment | undefined | null;
  cachedAssetNode: AssetTableDefinitionFragment | undefined | null;
  upstream: AssetNodeForGraphQueryFragment[] | null;
  downstream: AssetNodeForGraphQueryFragment[] | null;
  liveData: LiveDataForNode | undefined;
  dependsOnSelf: boolean;
}) => {
  const cachedOrLiveAssetNode = assetNode ?? cachedAssetNode;
  const repoAddress = cachedOrLiveAssetNode
    ? buildRepoAddress(
        cachedOrLiveAssetNode.repository.name,
        cachedOrLiveAssetNode.repository.location.name,
      )
    : null;
  const location = useRepositoryLocationForAddress(repoAddress);

  const {assetMetadata} = metadataForAssetNode(assetNode);

  const assetNodeLoadTimestamp = location ? location.updatedTimestamp * 1000 : undefined;

  const {materialization, observation, loading} = useLatestPartitionEvents(
    assetKey,
    assetNodeLoadTimestamp,
    liveData,
  );

  const {
    materializations,
    observations,
    loading: materializationsLoading,
  } = useRecentAssetEvents(
    cachedOrLiveAssetNode?.partitionDefinition ? undefined : cachedOrLiveAssetNode?.assetKey,
    {},
    {assetHasDefinedPartitions: false},
  );

  // Start loading neighboring assets data immediately to avoid waterfall.
  useAssetsLiveData(
    useMemo(
      () => [
        ...(downstream || []).map((node) => node.assetKey),
        ...(upstream || []).map((node) => node.assetKey),
      ],
      [downstream, upstream],
    ),
  );

  if (loading || !cachedOrLiveAssetNode) {
    return <AssetNodeOverviewLoading />;
  }

  const {tableSchema, tableSchemaLoadTimestamp} = buildConsolidatedColumnSchema({
    materialization,
    definition: assetNode,
    definitionLoadTimestamp: assetNodeLoadTimestamp,
  });

  const rowCountMeta: IntMetadataEntry | undefined = materialization?.metadataEntries.find(
    (entry) => isCanonicalRowCountMetadataEntry(entry),
  ) as IntMetadataEntry | undefined;

  const renderStatusSection = () => (
    <Box flex={{direction: 'column', gap: 16}}>
      <Box style={{display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))'}}>
        <Box flex={{direction: 'column', gap: 6}}>
          <Subtitle2>
            Latest {assetNode?.isObservable ? 'observation' : 'materialization'}
          </Subtitle2>
          <Box flex={{gap: 8, alignItems: 'center'}}>
            {liveData ? (
              <SimpleStakeholderAssetStatus
                liveData={liveData}
                assetNode={assetNode ?? cachedAssetNode!}
              />
            ) : (
              <NoValue />
            )}
            {assetNode && assetNode.freshnessPolicy && (
              <OverdueTag policy={assetNode.freshnessPolicy} assetKey={assetNode.assetKey} />
            )}
          </Box>
        </Box>
        {liveData?.assetChecks.length ? (
          <Box flex={{direction: 'column', gap: 6}}>
            <Subtitle2>Check results</Subtitle2>
            <AssetChecksStatusSummary
              liveData={liveData}
              rendering="tags"
              assetKey={cachedOrLiveAssetNode.assetKey}
            />
          </Box>
        ) : undefined}
        {rowCountMeta?.intValue ? (
          <Box flex={{direction: 'column', gap: 6}}>
            <Subtitle2>Row count</Subtitle2>
            <Box>
              <Tag icon="table_rows">{numberFormatter.format(rowCountMeta.intValue)}</Tag>
            </Box>
          </Box>
        ) : undefined}
      </Box>
      {cachedOrLiveAssetNode.isPartitioned ? null : (
        <RecentUpdatesTimeline
          materializations={materializations}
          observations={observations}
          assetKey={cachedOrLiveAssetNode.assetKey}
          loading={materializationsLoading}
        />
      )}
    </Box>
  );

  return (
    <AssetNodeOverviewContainer
      left={
        <>
          <LargeCollapsibleSection header="Status" icon="status">
            {renderStatusSection()}
          </LargeCollapsibleSection>
          <LargeCollapsibleSection header="Description" icon="sticky_note">
            {cachedOrLiveAssetNode.description ? (
              <Description description={cachedOrLiveAssetNode.description} maxHeight={260} />
            ) : (
              <SectionEmptyState
                title="No description found"
                description="You can add a description to any asset by adding a `description` argument to it."
                learnMoreLink="https://docs.dagster.io/_apidocs/assets#software-defined-assets"
              />
            )}
          </LargeCollapsibleSection>
          {tableSchema && (
            <LargeCollapsibleSection header="Columns" icon="view_column">
              <TableSchemaAssetContext.Provider
                value={{
                  assetKey: cachedOrLiveAssetNode.assetKey,
                  materializationMetadataEntries: materialization?.metadataEntries,
                  definitionMetadataEntries: assetNode?.metadataEntries,
                }}
              >
                <TableSchema
                  schema={tableSchema.schema}
                  schemaLoadTimestamp={tableSchemaLoadTimestamp}
                />
              </TableSchemaAssetContext.Provider>
            </LargeCollapsibleSection>
          )}
          <LargeCollapsibleSection header="Metadata" icon="view_list">
            <AssetEventMetadataEntriesTable
              assetKey={cachedOrLiveAssetNode.assetKey}
              showHeader
              showTimestamps
              showFilter
              hideEntriesShownOnOverview
              observations={[]}
              definitionMetadata={assetMetadata}
              definitionLoadTimestamp={assetNodeLoadTimestamp}
              assetHasDefinedPartitions={!!cachedOrLiveAssetNode.partitionDefinition}
              repoAddress={repoAddress}
              event={materialization || observation || null}
              emptyState={
                <SectionEmptyState
                  title="No metadata found"
                  description="Attach metadata to your asset definition, materializations or observations to see it here."
                  learnMoreLink="https://docs.dagster.io/concepts/assets/software-defined-assets#attaching-definition-metadata"
                />
              }
            />
          </LargeCollapsibleSection>
          <LargeCollapsibleSection
            header="Lineage"
            icon="account_tree"
            right={
              <Link
                to={globalAssetGraphPathForAssetsAndDescendants([cachedOrLiveAssetNode.assetKey])}
                onClick={(e) => e.stopPropagation()}
              >
                <Box flex={{gap: 4, alignItems: 'center'}}>View in graph</Box>
              </Link>
            }
          >
            <LineageSection
              downstream={downstream}
              upstream={upstream}
              dependsOnSelf={dependsOnSelf}
            />
          </LargeCollapsibleSection>
        </>
      }
      right={
        <>
          <LargeCollapsibleSection header="Definition" icon="info">
            <DefinitionSection
              repoAddress={repoAddress}
              location={location}
              assetNode={assetNode}
              cachedOrLiveAssetNode={cachedOrLiveAssetNode}
            />
          </LargeCollapsibleSection>
          <LargeCollapsibleSection header="Automation details" icon="automation_condition">
            <AutomationDetailsSection
              repoAddress={repoAddress}
              assetNode={assetNode}
              cachedOrLiveAssetNode={cachedOrLiveAssetNode}
            />
          </LargeCollapsibleSection>
          {cachedOrLiveAssetNode.isExecutable ? (
            <LargeCollapsibleSection header="Compute details" icon="settings" collapsedByDefault>
              <ComputeDetailsSection repoAddress={repoAddress} assetNode={assetNode} />
            </LargeCollapsibleSection>
          ) : null}
          <AssetAlertsSection repoAddress={repoAddress} assetNode={cachedOrLiveAssetNode} />
        </>
      }
    />
  );
};

const AssetNodeOverviewContainer = ({
  left,
  right,
}: {
  left: React.ReactNode;
  right: React.ReactNode;
}) => (
  <Box
    flex={{direction: 'row', gap: 8}}
    style={{width: '100%', height: '100%', overflow: 'hidden'}}
  >
    <Box
      flex={{direction: 'column'}}
      padding={{horizontal: 24, vertical: 12}}
      style={{flex: 1, minWidth: 0, overflowY: 'auto'}}
    >
      {left}
    </Box>
    <Box
      border={{side: 'left'}}
      flex={{direction: 'column'}}
      padding={{left: 24, vertical: 12, right: 12}}
      style={{width: '30%', minWidth: 250, overflowY: 'auto'}}
    >
      {right}
    </Box>
  </Box>
);

export const AssetNodeOverviewNonSDA = ({
  assetKey,
  lastMaterialization,
}: {
  assetKey: AssetKey;
  lastMaterialization: {timestamp: string; runId: string} | null | undefined;
}) => {
  const {materializations, observations, loading} = useRecentAssetEvents(
    assetKey,
    {},
    {assetHasDefinedPartitions: false},
  );

  return (
    <AssetNodeOverviewContainer
      left={
        <LargeCollapsibleSection header="Status" icon="status">
          <Box flex={{direction: 'column', gap: 16}}>
            <div>
              {lastMaterialization ? (
                <MaterializationTag
                  assetKey={assetKey}
                  event={lastMaterialization}
                  stepKey={null}
                />
              ) : (
                <Caption color={Colors.textLighter()}>Never materialized</Caption>
              )}
            </div>
            <RecentUpdatesTimeline
              materializations={materializations}
              observations={observations}
              assetKey={assetKey}
              loading={loading}
            />
          </Box>
        </LargeCollapsibleSection>
      }
      right={
        <LargeCollapsibleSection header="Definition" icon="info">
          <Box flex={{direction: 'column', gap: 12}}>
            <NonIdealState
              shrinkable
              description="This asset doesn't have a software definition in any of your code locations."
              icon="materialization"
              title=""
            />
          </Box>
        </LargeCollapsibleSection>
      }
    />
  );
};

export const AssetNodeOverviewLoading = () => (
  <AssetNodeOverviewContainer
    left={
      <>
        <LargeCollapsibleSection header="Status" icon="status">
          <Box flex={{direction: 'column', gap: 6}}>
            <Skeleton $height={20} $width={170} />
            <Skeleton $height={24} $width={240} />
          </Box>
        </LargeCollapsibleSection>
        <LargeCollapsibleSection header="Description" icon="sticky_note">
          <Box flex={{direction: 'column', gap: 6}}>
            <Skeleton $height={16} $width="90%" />
            <Skeleton $height={16} />
            <Skeleton $height={16} $width="60%" />
          </Box>
        </LargeCollapsibleSection>
      </>
    }
    right={
      <LargeCollapsibleSection header="Definition" icon="info">
        <Box flex={{direction: 'column', gap: 12}}>
          <AttributeAndValue label={<Skeleton $width={60} />}>
            <Skeleton $height={20} $width={220} />
          </AttributeAndValue>
          <AttributeAndValue label={<Skeleton $width={80} />}>
            <Skeleton $height={24} $width={180} />
          </AttributeAndValue>
          <AttributeAndValue label={<Skeleton $width={120} />}>
            <Skeleton $height={24} $width={240} />
          </AttributeAndValue>
        </Box>
      </LargeCollapsibleSection>
    }
  />
);
