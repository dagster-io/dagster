// eslint-disable-next-line no-restricted-imports
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
  MiddleTruncate,
  NonIdealState,
  Skeleton,
  Subtitle2,
  Tag,
  Tooltip,
} from '@dagster-io/ui-components';
import dayjs from 'dayjs';
import React, {useMemo, useState} from 'react';
import {Link} from 'react-router-dom';
import {UserDisplay} from 'shared/runs/UserDisplay.oss';
import styled from 'styled-components';

import {AssetDefinedInMultipleReposNotice} from './AssetDefinedInMultipleReposNotice';
import {AssetEventMetadataEntriesTable} from './AssetEventMetadataEntriesTable';
import {metadataForAssetNode} from './AssetMetadata';
import {insitigatorsByType} from './AssetNodeInstigatorTag';
import {EvaluationUserLabel} from './AutoMaterializePolicyPage/EvaluationConditionalLabel';
import {DependsOnSelfBanner} from './DependsOnSelfBanner';
import {LargeCollapsibleSection} from './LargeCollapsibleSection';
import {MaterializationTag} from './MaterializationTag';
import {OverdueTag, freshnessPolicyDescription} from './OverdueTag';
import {RecentUpdatesTimeline} from './RecentUpdatesTimeline';
import {SimpleStakeholderAssetStatus} from './SimpleStakeholderAssetStatus';
import {UnderlyingOpsOrGraph} from './UnderlyingOpsOrGraph';
import {AssetChecksStatusSummary} from './asset-checks/AssetChecksStatusSummary';
import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {buildConsolidatedColumnSchema} from './buildConsolidatedColumnSchema';
import {globalAssetGraphPathForAssetsAndDescendants} from './globalAssetGraphPathToString';
import {AssetKey} from './types';
import {AssetNodeDefinitionFragment} from './types/AssetNodeDefinition.types';
import {AssetTableDefinitionFragment} from './types/AssetTableFragment.types';
import {useLatestPartitionEvents} from './useLatestPartitionEvents';
import {useRecentAssetEvents} from './useRecentAssetEvents';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {showSharedToaster} from '../app/DomUtils';
import {COMMON_COLLATOR} from '../app/Util';
import {useCopyToClipboard} from '../app/browser';
import {useAssetsLiveData} from '../asset-data/AssetLiveDataProvider';
import {
  LiveDataForNode,
  displayNameForAssetKey,
  isHiddenAssetGroupJob,
  sortAssetKeys,
  tokenForAssetKey,
} from '../asset-graph/Utils';
import {StatusDot} from '../asset-graph/sidebar/StatusDot';
import {AssetNodeForGraphQueryFragment} from '../asset-graph/types/useAssetGraphData.types';
import {CodeLink, getCodeReferenceKey} from '../code-links/CodeLink';
import {DagsterTypeSummary} from '../dagstertype/DagsterType';
import {AssetKind, isCanonicalStorageKindTag, isSystemTag} from '../graph/KindTags';
import {CodeReferencesMetadataEntry, IntMetadataEntry} from '../graphql/types';
import {useStateWithStorage} from '../hooks/useStateWithStorage';
import {isCanonicalRowCountMetadataEntry} from '../metadata/MetadataEntry';
import {
  TableSchema,
  TableSchemaAssetContext,
  isCanonicalCodeSourceEntry,
  isCanonicalRelationIdentifierEntry,
  isCanonicalUriEntry,
} from '../metadata/TableSchema';
import {RepositoryLink} from '../nav/RepositoryLink';
import {ScheduleOrSensorTag} from '../nav/ScheduleOrSensorTag';
import {useRepositoryLocationForAddress} from '../nav/useRepositoryLocationForAddress';
import {Description} from '../pipelines/Description';
import {PipelineTag} from '../pipelines/PipelineReference';
import {numberFormatter} from '../ui/formatters';
import {buildTagString} from '../ui/tagAsString';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {workspacePathFromAddress} from '../workspace/workspacePath';

const SystemTagsToggle = ({tags}: {tags: Array<{key: string; value: string}>}) => {
  const [shown, setShown] = useStateWithStorage('show-asset-definition-system-tags', Boolean);

  if (!shown) {
    return (
      <Caption>
        <ButtonLink onClick={() => setShown(true)}>
          <Box flex={{alignItems: 'center'}}>
            <span>Show system tags ({tags.length || 0})</span>
            <Icon name="arrow_drop_down" style={{transform: 'rotate(0deg)'}} />
          </Box>
        </ButtonLink>
      </Caption>
    );
  } else {
    return (
      <Box flex={{direction: 'column', gap: 8}}>
        <Box>
          {tags.map((tag, idx) => (
            <Tag key={idx}>{buildTagString(tag)}</Tag>
          ))}
        </Box>
        <Caption>
          <ButtonLink onClick={() => setShown(false)}>
            <Box flex={{alignItems: 'center'}}>
              <span>Hide system tags</span>
              <Icon name="arrow_drop_down" style={{transform: 'rotate(180deg)'}} />
            </Box>
          </ButtonLink>
        </Caption>
      </Box>
    );
  }
};

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

  const {assetType, assetMetadata} = metadataForAssetNode(assetNode);
  const {schedules, sensors} = useMemo(() => insitigatorsByType(assetNode), [assetNode]);
  const configType = assetNode?.configField?.configType;
  const assetConfigSchema = configType && configType.key !== 'Any' ? configType : null;
  const visibleJobNames =
    cachedOrLiveAssetNode?.jobNames.filter((jobName) => !isHiddenAssetGroupJob(jobName)) || [];

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

  const renderDescriptionSection = () =>
    cachedOrLiveAssetNode.description ? (
      <Description description={cachedOrLiveAssetNode.description} maxHeight={260} />
    ) : (
      <SectionEmptyState
        title="No description found"
        description="You can add a description to any asset by adding a `description` argument to it."
        learnMoreLink="https://docs.dagster.io/_apidocs/assets#software-defined-assets"
      />
    );

  const renderLineageSection = () => (
    <>
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
    </>
  );

  const storageKindTag = cachedOrLiveAssetNode.tags?.find(isCanonicalStorageKindTag);
  const filteredTags = cachedOrLiveAssetNode.tags?.filter(
    (tag) => tag.key !== 'dagster/storage_kind',
  );

  const nonSystemTags = filteredTags?.filter((tag) => !isSystemTag(tag));
  const systemTags = filteredTags?.filter(isSystemTag);

  const relationIdentifierMetadata = assetNode?.metadataEntries?.find(
    isCanonicalRelationIdentifierEntry,
  );
  const uriMetadata = assetNode?.metadataEntries?.find(isCanonicalUriEntry);

  const codeSource = assetNode?.metadataEntries?.find((m) => isCanonicalCodeSourceEntry(m)) as
    | CodeReferencesMetadataEntry
    | undefined;

  const renderDefinitionSection = () => (
    <Box flex={{direction: 'column', gap: 12}}>
      <AttributeAndValue label="Group">
        <Tag icon="asset_group">
          <Link
            to={workspacePathFromAddress(
              repoAddress!,
              `/asset-groups/${cachedOrLiveAssetNode.groupName}`,
            )}
          >
            {cachedOrLiveAssetNode.groupName}
          </Link>
        </Tag>
      </AttributeAndValue>

      <AttributeAndValue label="Code location">
        <Box flex={{direction: 'column'}}>
          <AssetDefinedInMultipleReposNotice
            assetKey={cachedOrLiveAssetNode.assetKey}
            loadedFromRepo={repoAddress!}
          />
          <RepositoryLink repoAddress={repoAddress!} />
          {location && (
            <Caption color={Colors.textLighter()}>
              Loaded {dayjs.unix(location.updatedTimestamp).fromNow()}
            </Caption>
          )}
        </Box>
      </AttributeAndValue>
      <AttributeAndValue label="Owners">
        {cachedOrLiveAssetNode.owners &&
          cachedOrLiveAssetNode.owners.length > 0 &&
          cachedOrLiveAssetNode.owners.map((owner, idx) =>
            owner.__typename === 'UserAssetOwner' ? (
              <UserAssetOwnerWrapper key={idx}>
                <UserDisplay key={idx} email={owner.email} size="very-small" />
              </UserAssetOwnerWrapper>
            ) : (
              <Tag icon="people" key={idx}>
                {owner.team}
              </Tag>
            ),
          )}
      </AttributeAndValue>
      <AttributeAndValue label="Compute kind">
        {cachedOrLiveAssetNode.computeKind && (
          <AssetKind
            style={{position: 'relative'}}
            kind={cachedOrLiveAssetNode.computeKind}
            reduceColor
            linkToFilteredAssetsTable
          />
        )}
      </AttributeAndValue>
      <AttributeAndValue label="Kinds">
        {(cachedOrLiveAssetNode.kinds.length > 1 || !cachedOrLiveAssetNode.computeKind) &&
          cachedOrLiveAssetNode.kinds.map((kind) => (
            <AssetKind
              key={kind}
              style={{position: 'relative'}}
              kind={kind}
              reduceColor
              linkToFilteredAssetsTable
            />
          ))}
      </AttributeAndValue>
      <AttributeAndValue label="Storage">
        {(relationIdentifierMetadata || uriMetadata || storageKindTag) && (
          <Box flex={{direction: 'column', gap: 4}} style={{minWidth: 0}}>
            {relationIdentifierMetadata && (
              <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
                <MiddleTruncate text={relationIdentifierMetadata.text} />
                <CopyButton value={relationIdentifierMetadata.text} />
              </Box>
            )}
            {uriMetadata && (
              <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
                {uriMetadata.__typename === 'TextMetadataEntry' ? (
                  uriMetadata.text
                ) : (
                  <a target="_blank" rel="noreferrer" href={uriMetadata.url}>
                    {uriMetadata.url}
                  </a>
                )}
                <CopyButton
                  value={
                    uriMetadata.__typename === 'TextMetadataEntry'
                      ? uriMetadata?.text
                      : uriMetadata.url
                  }
                />
              </Box>
            )}
            {storageKindTag && (
              <AssetKind
                style={{position: 'relative'}}
                kind={storageKindTag.value}
                reduceColor
                linkToFilteredAssetsTable
              />
            )}
          </Box>
        )}
      </AttributeAndValue>
      <AttributeAndValue label="Tags">
        {filteredTags && filteredTags.length > 0 && (
          <Box flex={{direction: 'column', gap: 8}}>
            <Box>
              {nonSystemTags.map((tag, idx) => (
                <Tag key={idx}>{buildTagString(tag)}</Tag>
              ))}
            </Box>
            {systemTags.length > 0 && <SystemTagsToggle tags={systemTags} />}
          </Box>
        )}
      </AttributeAndValue>
      <AttributeAndValue label="Source code">
        {codeSource &&
          codeSource.codeReferences &&
          codeSource.codeReferences.map((ref) => (
            <CodeLink key={getCodeReferenceKey(ref)} sourceLocation={ref} />
          ))}
      </AttributeAndValue>
    </Box>
  );

  const renderAutomationDetailsSection = () => {
    const attributes = [
      {
        label: 'Jobs',
        children: visibleJobNames.map((jobName) => (
          <PipelineTag
            key={jobName}
            isJob
            showIcon
            pipelineName={jobName}
            pipelineHrefContext={repoAddress!}
          />
        )),
      },
      {
        label: 'Sensors',
        children: assetNode ? (
          sensors.length > 0 ? (
            <ScheduleOrSensorTag repoAddress={repoAddress!} sensors={sensors} showSwitch={false} />
          ) : null
        ) : (
          <SectionSkeleton />
        ),
      },
      {
        label: 'Schedules',
        children: assetNode ? (
          schedules.length > 0 && (
            <ScheduleOrSensorTag
              repoAddress={repoAddress!}
              schedules={schedules}
              showSwitch={false}
            />
          )
        ) : (
          <SectionSkeleton />
        ),
      },
      {
        label: 'Freshness policy',
        children: assetNode ? (
          assetNode?.freshnessPolicy && (
            <Body>{freshnessPolicyDescription(assetNode.freshnessPolicy)}</Body>
          )
        ) : (
          <SectionSkeleton />
        ),
      },
    ];

    if (
      attributes.every((props) => isEmptyChildren(props.children)) &&
      !cachedOrLiveAssetNode.automationCondition
    ) {
      return (
        <SectionEmptyState
          title="No automations found for this asset"
          description="Dagster offers several ways to run data pipelines without manual intervention, including traditional scheduling and event-based triggers."
          learnMoreLink="https://docs.dagster.io/concepts/automation#automation"
        />
      );
    } else {
      if (assetNode?.automationCondition && assetNode?.automationCondition.label) {
        return (
          <EvaluationUserLabel
            userLabel={assetNode?.automationCondition.label}
            expandedLabel={assetNode?.automationCondition.expandedLabel}
          />
        );
      }
    }

    return (
      <Box flex={{direction: 'column', gap: 12}}>
        {attributes.map((props) => (
          <AttributeAndValue key={props.label} {...props} />
        ))}
      </Box>
    );
  };

  const renderComputeDetailsSection = () => {
    if (!assetNode) {
      return <SectionSkeleton />;
    }
    return (
      <Box flex={{direction: 'column', gap: 12}}>
        <AttributeAndValue label="Computed by">
          <Tag>
            <UnderlyingOpsOrGraph
              assetNode={assetNode}
              repoAddress={repoAddress!}
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
                <Box flex={{gap: 4, alignItems: 'center'}}>
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
                </Box>
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

        <AttributeAndValue label="Backfill policy">
          {assetNode.backfillPolicy?.description}
        </AttributeAndValue>
      </Box>
    );
  };

  return (
    <AssetNodeOverviewContainer
      left={
        <>
          <LargeCollapsibleSection header="Status" icon="status">
            {renderStatusSection()}
          </LargeCollapsibleSection>
          <LargeCollapsibleSection header="Description" icon="sticky_note">
            {renderDescriptionSection()}
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
              hideTableSchema
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
            {renderLineageSection()}
          </LargeCollapsibleSection>
        </>
      }
      right={
        <>
          <LargeCollapsibleSection header="Definition" icon="info">
            {renderDefinitionSection()}
          </LargeCollapsibleSection>
          <LargeCollapsibleSection header="Automation details" icon="auto_materialize_policy">
            {renderAutomationDetailsSection()}
          </LargeCollapsibleSection>
          {cachedOrLiveAssetNode.isExecutable ? (
            <LargeCollapsibleSection header="Compute details" icon="settings" collapsedByDefault>
              {renderComputeDetailsSection()}
            </LargeCollapsibleSection>
          ) : null}
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

const isEmptyChildren = (children: React.ReactNode) =>
  !children || (children instanceof Array && children.length === 0);

const CopyButton = ({value}: {value: string}) => {
  const copy = useCopyToClipboard();
  const onCopy = async () => {
    copy(value);
    await showSharedToaster({
      intent: 'success',
      icon: 'copy_to_clipboard_done',
      message: 'Copied!',
    });
  };

  return (
    <Tooltip content="Copy" placement="bottom" display="block">
      <div onClick={onCopy} style={{cursor: 'pointer'}}>
        <Icon name="content_copy" />
      </div>
    </Tooltip>
  );
};

const AttributeAndValue = ({
  label,
  children,
}: {
  label: React.ReactNode;
  children: React.ReactNode;
}) => {
  if (isEmptyChildren(children)) {
    return null;
  }

  return (
    <Box flex={{direction: 'column', gap: 6, alignItems: 'stretch'}}>
      <Subtitle2>{label}</Subtitle2>
      <Body2 style={{maxWidth: '100%'}}>
        <Box flex={{gap: 4, wrap: 'wrap'}}>{children}</Box>
      </Body2>
    </Box>
  );
};

const NoValue = () => <Body2 color={Colors.textLighter()}>–</Body2>;

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

const SectionEmptyState = ({
  title,
  description,
  learnMoreLink,
}: {
  title: string;
  description: string;
  learnMoreLink: string;
}) => (
  <Box
    padding={24}
    style={{background: Colors.backgroundLight(), borderRadius: 8}}
    flex={{direction: 'column', gap: 8}}
  >
    <Subtitle2>{title}</Subtitle2>
    <Body2>{description}</Body2>
    {learnMoreLink ? (
      <a href={learnMoreLink} target="_blank" rel="noreferrer">
        Learn more
      </a>
    ) : undefined}
  </Box>
);

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

const UserAssetOwnerWrapper = styled.div`
  > div {
    background-color: ${Colors.backgroundGray()};
  }
`;

const SectionSkeleton = () => (
  <Box flex={{direction: 'column', gap: 6}} style={{width: '100%'}}>
    <Skeleton $height={16} $width="90%" />
    <Skeleton $height={16} />
    <Skeleton $height={16} $width="60%" />
  </Box>
);
