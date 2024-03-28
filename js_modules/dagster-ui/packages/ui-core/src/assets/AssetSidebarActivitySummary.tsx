import {Body, Box, Colors, Icon, MiddleTruncate, Spinner} from '@dagster-io/ui-components';
import {useEffect} from 'react';
import {Link} from 'react-router-dom';

import {AssetEventSystemTags} from './AssetEventSystemTags';
import {AssetMaterializationGraphs} from './AssetMaterializationGraphs';
import {
  AutomaterializePolicyTag,
  automaterializePolicyDescription,
} from './AutomaterializePolicyTag';
import {CurrentRunsBanner} from './CurrentRunsBanner';
import {FailedRunSinceMaterializationBanner} from './FailedRunSinceMaterializationBanner';
import {LatestMaterializationMetadata} from './LastMaterializationMetadata';
import {OverdueTag, freshnessPolicyDescription} from './OverdueTag';
import {AssetCheckStatusTag} from './asset-checks/AssetCheckStatusTag';
import {ExecuteChecksButton} from './asset-checks/ExecuteChecksButton';
import {assetDetailsPathForAssetCheck, assetDetailsPathForKey} from './assetDetailsPathForKey';
import {useGroupedEvents} from './groupByPartition';
import {isRunlessEvent} from './isRunlessEvent';
import {RecentAssetEvents} from './useRecentAssetEvents';
import {LiveDataForNode} from '../asset-graph/Utils';
import {SidebarAssetFragment} from '../asset-graph/types/SidebarAssetInfo.types';
import {SidebarSection} from '../pipelines/SidebarComponents';

interface Props {
  asset: SidebarAssetFragment;
  liveData?: LiveDataForNode;
  isSourceAsset: boolean;
  stepKey: string;
  recentEvents: RecentAssetEvents;

  // This timestamp is a "hint", when it changes this component will refetch
  // to retrieve new data. Just don't want to poll the entire table query.
  assetLastMaterializedAt: string | undefined;
}

export const AssetSidebarActivitySummary = ({
  asset,
  assetLastMaterializedAt,
  isSourceAsset,
  liveData,
  stepKey,
  recentEvents,
}: Props) => {
  const {xAxis, materializations, observations, loadedPartitionKeys, refetch, loading} =
    recentEvents;

  const grouped = useGroupedEvents(xAxis, materializations, observations, loadedPartitionKeys);
  const displayedEvent = isSourceAsset ? observations[0] : materializations[0];

  useEffect(() => {
    refetch();
  }, [assetLastMaterializedAt, refetch]);

  return (
    <>
      {!asset.partitionDefinition && (
        <>
          <FailedRunSinceMaterializationBanner
            stepKey={stepKey}
            border="top"
            run={liveData?.runWhichFailedToMaterialize || null}
          />
          <CurrentRunsBanner stepKey={stepKey} border="top" liveData={liveData} />
        </>
      )}

      {asset.freshnessPolicy && (
        <SidebarSection title="Freshness policy">
          <Box margin={{horizontal: 24, vertical: 12}} flex={{gap: 12, alignItems: 'flex-start'}}>
            <Body style={{flex: 1}}>{freshnessPolicyDescription(asset.freshnessPolicy)}</Body>
            <OverdueTag policy={asset.freshnessPolicy} assetKey={asset.assetKey} />
          </Box>
        </SidebarSection>
      )}

      {asset.autoMaterializePolicy && (
        <SidebarSection title="Auto-materialize policy">
          <Box
            padding={{horizontal: 24, vertical: 12}}
            flex={{direction: 'row', gap: 4, alignItems: 'center'}}
          >
            <Link to={assetDetailsPathForKey(asset.assetKey, {view: 'automation'})}>
              View automation history
            </Link>
            <Icon name="open_in_new" color={Colors.linkDefault()} />
          </Box>
          <Box margin={{horizontal: 24}} flex={{gap: 12, alignItems: 'flex-start'}}>
            <Body style={{flex: 1, marginBottom: 12}}>
              {automaterializePolicyDescription(asset.autoMaterializePolicy)}
            </Body>
            <AutomaterializePolicyTag policy={asset.autoMaterializePolicy} />
          </Box>
        </SidebarSection>
      )}

      {asset.backfillPolicy && (
        <SidebarSection title="Backfill policy">
          <Box margin={{horizontal: 24, vertical: 12}} flex={{gap: 12, alignItems: 'flex-start'}}>
            <Body style={{flex: 1}}>{asset.backfillPolicy.description}</Body>
          </Box>
        </SidebarSection>
      )}

      {loadedPartitionKeys.length > 1 ? null : (
        <>
          <SidebarSection
            title={
              !isSourceAsset
                ? displayedEvent && isRunlessEvent(displayedEvent)
                  ? 'Last reported materialization'
                  : 'Materialization in last run'
                : 'Observation in last run'
            }
          >
            {displayedEvent ? (
              <div style={{margin: -1, maxWidth: '100%', overflowX: 'auto'}}>
                <LatestMaterializationMetadata
                  assetKey={asset.assetKey}
                  latest={displayedEvent}
                  liveData={liveData}
                  definition={asset}
                />
              </div>
            ) : loading ? (
              <Box padding={{vertical: 20}}>
                <Spinner purpose="section" />
              </Box>
            ) : (
              <Box
                margin={{horizontal: 24, vertical: 12}}
                style={{color: Colors.textLight(), fontSize: '0.8rem'}}
              >
                {!isSourceAsset ? `No materializations found` : `No observations found`}
              </Box>
            )}
          </SidebarSection>
          <SidebarSection
            title={!isSourceAsset ? 'Materialization system tags' : 'Observation system tags'}
            collapsedByDefault
          >
            {displayedEvent ? (
              <div style={{margin: -1, maxWidth: '100%', overflowX: 'auto'}}>
                <AssetEventSystemTags event={displayedEvent} paddingLeft={24} />
              </div>
            ) : loading ? (
              <Box padding={{vertical: 20}}>
                <Spinner purpose="section" />
              </Box>
            ) : (
              <Box
                margin={{horizontal: 24, vertical: 12}}
                style={{color: Colors.textLight(), fontSize: '0.8rem'}}
              >
                {!isSourceAsset ? `No materializations found` : `No observations found`}
              </Box>
            )}
          </SidebarSection>
        </>
      )}
      <SidebarSection title="Metadata plots">
        <AssetMaterializationGraphs
          xAxis={xAxis}
          asSidebarSection
          groups={grouped}
          columnCount={1}
        />
      </SidebarSection>
      {asset.assetChecksOrError.__typename === 'AssetChecks' &&
        asset.assetChecksOrError.checks.length > 0 && (
          <SidebarSection title="Checks">
            <Box padding={{horizontal: 24, vertical: 12}} flex={{gap: 12, alignItems: 'center'}}>
              <ExecuteChecksButton assetNode={asset} checks={asset.assetChecksOrError.checks} />
              <Link to={assetDetailsPathForKey(asset.assetKey, {view: 'checks'})}>
                View all check details
              </Link>
            </Box>

            {asset.assetChecksOrError.checks.slice(0, 10).map((check) => {
              const execution =
                liveData &&
                liveData.assetChecks?.find((c) => c.name === check.name)
                  ?.executionForLatestMaterialization;

              return (
                <Box
                  key={check.name}
                  style={{minHeight: 40}}
                  border={{side: 'top', width: 1, color: Colors.keylineDefault()}}
                  padding={{vertical: 8, right: 12, left: 24}}
                  flex={{
                    gap: 8,
                    direction: 'row',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <Link
                    style={{display: 'flex', flex: 1, overflow: 'hidden'}}
                    to={assetDetailsPathForAssetCheck({
                      name: check.name,
                      assetKey: asset.assetKey,
                    })}
                  >
                    <MiddleTruncate text={check.name} />
                  </Link>
                  {execution ? (
                    <AssetCheckStatusTag execution={execution} />
                  ) : (
                    <Spinner purpose="caption-text" />
                  )}
                </Box>
              );
            })}
            {asset.assetChecksOrError.checks.length > 10 && (
              <Box
                padding={{vertical: 12, right: 12, left: 24}}
                border={{side: 'top', width: 1, color: Colors.keylineDefault()}}
              >
                <Link to={assetDetailsPathForKey(asset.assetKey, {view: 'checks'})}>
                  View {asset.assetChecksOrError.checks.length - 10} more…
                </Link>
              </Box>
            )}
          </SidebarSection>
        )}
    </>
  );
};
