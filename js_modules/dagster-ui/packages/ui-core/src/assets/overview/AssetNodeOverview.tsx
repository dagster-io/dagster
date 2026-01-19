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

import {FreshnessPolicySection} from './FreshnessPolicySection';
import {WorkspaceAssetFragment} from '../../workspace/WorkspaceContext/types/WorkspaceQueries.types';
import {AssetEventMetadataEntriesTable} from '../AssetEventMetadataEntriesTable';
import {metadataForAssetNode} from '../AssetMetadata';
import {AutomationDetailsSection} from './AutomationDetailsSection';
import {AttributeAndValue, NoValue, SectionEmptyState} from './Common';
import {ComputeDetailsSection} from './ComputeDetailsSection';
import {DefinitionSection} from './DefinitionSection';
import {FreshnessPolicyStatus} from './FreshnessPolicyStatus';
import {LineageSection} from './LineageSection';
import {useAssetsLiveData} from '../../asset-data/AssetLiveDataProvider';
import {LiveDataForNode} from '../../asset-graph/Utils';
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
import {RecentUpdatesTimelineForAssetKey} from '../RecentUpdatesTimeline';
import {SimpleStakeholderAssetStatus} from '../SimpleStakeholderAssetStatus';
import {AssetChecksStatusSummary} from '../asset-checks/AssetChecksStatusSummary';
import {buildConsolidatedColumnSchema} from '../buildConsolidatedColumnSchema';
import {globalAssetGraphPathForAssetsAndDescendants} from '../globalAssetGraphPathToString';
import {AssetKey} from '../types';
import {AssetTableDefinitionFragment} from '../types/AssetTableFragment.types';
import {AssetViewDefinitionNodeFragment} from '../types/AssetView.types';
import {useLatestEvents} from '../useLatestEvents';

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
  assetNode: AssetViewDefinitionNodeFragment | undefined | null;
  cachedAssetNode: AssetTableDefinitionFragment | undefined | null;
  upstream: WorkspaceAssetFragment[] | null;
  downstream: WorkspaceAssetFragment[] | null;
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

  const {materialization, observation, loading} = useLatestEvents(
    assetKey,
    assetNodeLoadTimestamp,
    liveData,
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

  let rowCountMeta: IntMetadataEntry | undefined = materialization?.metadataEntries.find((entry) =>
    isCanonicalRowCountMetadataEntry(entry),
  ) as IntMetadataEntry | undefined;

  if (!rowCountMeta && observation) {
    rowCountMeta = observation.metadataEntries.find((entry) =>
      isCanonicalRowCountMetadataEntry(entry),
    ) as IntMetadataEntry | undefined;
  }

  if (!rowCountMeta) {
    rowCountMeta = assetNode?.metadataEntries.find((entry) =>
      isCanonicalRowCountMetadataEntry(entry),
    ) as IntMetadataEntry | undefined;
  }

  // The live data does not include a partition, but the timestamp on the live data triggers
  // an update of `observation` and `materialization`, so they should be in sync. To make sure
  // we never display incorrect data we verify that the timestamps match.
  const liveDataPartition = assetNode?.isObservable
    ? partitionIfMatching(liveData?.lastObservation, observation)
    : partitionIfMatching(liveData?.lastMaterialization, materialization);

  const internalFreshnessPolicy =
    cachedOrLiveAssetNode.internalFreshnessPolicy || assetNode?.internalFreshnessPolicy;

  const sections = [
    1,
    liveData?.assetChecks.length,
    internalFreshnessPolicy,
    rowCountMeta?.intValue,
  ].filter(Boolean).length;

  const renderStatusSection = () => (
    <Box flex={{direction: 'column', gap: 16}}>
      <Box style={{display: `grid`, gridTemplateColumns: `repeat(${sections}, minmax(0, 1fr))`}}>
        <Box flex={{direction: 'column', gap: 6}}>
          <Subtitle2>
            最新{assetNode?.isObservable ? '观测' : '物化'}
          </Subtitle2>
          <Box flex={{gap: 8, alignItems: 'center'}}>
            {liveData ? (
              <SimpleStakeholderAssetStatus
                liveData={liveData}
                partition={liveDataPartition}
                // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
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
            <Subtitle2>检查结果</Subtitle2>
            <AssetChecksStatusSummary
              liveData={liveData}
              rendering="tags"
              assetKey={cachedOrLiveAssetNode.assetKey}
            />
          </Box>
        ) : undefined}
        {internalFreshnessPolicy ? (
          <FreshnessPolicyStatus
            assetKey={cachedOrLiveAssetNode.assetKey}
            freshnessPolicy={internalFreshnessPolicy}
          />
        ) : undefined}
        {rowCountMeta?.intValue ? (
          <Box flex={{direction: 'column', gap: 6}}>
            <Subtitle2>行数</Subtitle2>
            <Box>
              <Tag icon="table_rows">{numberFormatter.format(rowCountMeta.intValue)}</Tag>
            </Box>
          </Box>
        ) : undefined}
      </Box>
      {cachedOrLiveAssetNode.isPartitioned ? null : (
        <RecentUpdatesTimelineForAssetKey assetKey={cachedOrLiveAssetNode.assetKey} />
      )}
    </Box>
  );

  return (
    <AssetNodeOverviewContainer
      left={
        <>
          <LargeCollapsibleSection header="状态" icon="status">
            {renderStatusSection()}
          </LargeCollapsibleSection>
          <LargeCollapsibleSection header="描述" icon="sticky_note">
            {cachedOrLiveAssetNode.description ? (
              <Description description={cachedOrLiveAssetNode.description} maxHeight={260} />
            ) : (
              <SectionEmptyState
                title="未找到描述"
                description="您可以通过添加 `description` 参数来为资产添加描述。"
                learnMoreLink="https://docs.dagster.io/_apidocs/assets#software-defined-assets"
              />
            )}
          </LargeCollapsibleSection>
          {tableSchema && (
            <LargeCollapsibleSection header="列" icon="view_column">
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
          <LargeCollapsibleSection header="元数据" icon="view_list">
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
                  title="未找到元数据"
                  description="将元数据附加到资产定义、物化或观测中即可在此处查看。"
                  learnMoreLink="https://docs.dagster.io/concepts/assets/software-defined-assets#attaching-definition-metadata"
                />
              }
            />
          </LargeCollapsibleSection>
          <LargeCollapsibleSection
            header="数据血缘"
            icon="account_tree"
            right={
              <Link
                to={globalAssetGraphPathForAssetsAndDescendants([cachedOrLiveAssetNode.assetKey])}
                onClick={(e) => e.stopPropagation()}
              >
                <Box flex={{gap: 4, alignItems: 'center'}}>在图中查看</Box>
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
          <LargeCollapsibleSection header="定义" icon="info">
            <DefinitionSection
              repoAddress={repoAddress}
              location={location}
              assetNode={assetNode}
              cachedOrLiveAssetNode={cachedOrLiveAssetNode}
            />
          </LargeCollapsibleSection>
          <LargeCollapsibleSection header="自动化详情" icon="automation_condition">
            <AutomationDetailsSection
              repoAddress={repoAddress}
              assetNode={assetNode}
              cachedOrLiveAssetNode={cachedOrLiveAssetNode}
            />
          </LargeCollapsibleSection>
          {internalFreshnessPolicy ? (
            <LargeCollapsibleSection header="新鲜度策略" icon="freshness">
              <FreshnessPolicySection
                assetKey={cachedOrLiveAssetNode.assetKey}
                policy={internalFreshnessPolicy}
              />
            </LargeCollapsibleSection>
          ) : null}
          {cachedOrLiveAssetNode.isExecutable ? (
            <LargeCollapsibleSection header="计算详情" icon="settings" collapsedByDefault>
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
  return (
    <AssetNodeOverviewContainer
      left={
        <LargeCollapsibleSection header="状态" icon="status">
          <Box flex={{direction: 'column', gap: 16}}>
            <div>
              {lastMaterialization ? (
                <MaterializationTag
                  assetKey={assetKey}
                  event={lastMaterialization}
                  stepKey={null}
                />
              ) : (
                <Caption color={Colors.textLighter()}>从未物化</Caption>
              )}
            </div>
            <RecentUpdatesTimelineForAssetKey assetKey={assetKey} />
          </Box>
        </LargeCollapsibleSection>
      }
      right={
        <LargeCollapsibleSection header="定义" icon="info">
          <Box flex={{direction: 'column', gap: 12}}>
            <NonIdealState
              shrinkable
              description="此资产在您的任何代码位置中都没有软件定义。"
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
        <LargeCollapsibleSection header="状态" icon="status">
          <Box flex={{direction: 'column', gap: 6}}>
            <Skeleton $height={20} $width={170} />
            <Skeleton $height={24} $width={240} />
          </Box>
        </LargeCollapsibleSection>
        <LargeCollapsibleSection header="描述" icon="sticky_note">
          <Box flex={{direction: 'column', gap: 6}}>
            <Skeleton $height={16} $width="90%" />
            <Skeleton $height={16} />
            <Skeleton $height={16} $width="60%" />
          </Box>
        </LargeCollapsibleSection>
      </>
    }
    right={
      <LargeCollapsibleSection header="定义" icon="info">
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

function partitionIfMatching(
  liveDataEvent: {timestamp: string} | null | undefined,
  event: {timestamp: string; partition: string | null} | undefined,
) {
  if (!liveDataEvent || !event) {
    return null;
  }
  return liveDataEvent.timestamp === event.timestamp ? event.partition : null;
}
