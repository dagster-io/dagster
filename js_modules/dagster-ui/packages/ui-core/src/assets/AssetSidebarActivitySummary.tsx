import {Body, Box, Colors, MiddleTruncate, Spinner} from '@dagster-io/ui-components';
import {useEffect} from 'react';
import {Link} from 'react-router-dom';

import {AssetPartitionMetadataPlots, AssetTimeMetadataPlots} from './AssetEventMetadataPlots';
import {AssetEventSystemTags} from './AssetEventSystemTags';
import {CurrentRunsBanner} from './CurrentRunsBanner';
import {FailedRunSinceMaterializationBanner} from './FailedRunSinceMaterializationBanner';
import {LatestMaterializationMetadata} from './LastMaterializationMetadata';
import {OverdueTag, freshnessPolicyDescription} from './OverdueTag';
import {AssetCheckStatusTag} from './asset-checks/AssetCheckStatusTag';
import {ExecuteChecksButton} from './asset-checks/ExecuteChecksButton';
import {assetDetailsPathForAssetCheck, assetDetailsPathForKey} from './assetDetailsPathForKey';
import {RecentAssetEvents} from './useRecentAssetEvents';
import {LiveDataForNodeWithStaleData} from '../asset-graph/Utils';
import {SidebarAssetFragment} from '../asset-graph/types/SidebarAssetInfo.types';
import {PoolTag} from '../instance/PoolTag';
import {SidebarSection} from '../pipelines/SidebarComponents';

interface Props {
  asset: SidebarAssetFragment;
  liveData?: LiveDataForNodeWithStaleData;
  isObservable: boolean;
  stepKey: string;
  recentEvents: RecentAssetEvents;

  // This timestamp is a "hint", when it changes this component will refetch
  // to retrieve new data. Just don't want to poll the entire table query.
  assetLastMaterializedAt: string | undefined;
}

export const AssetSidebarActivitySummary = ({
  asset,
  assetLastMaterializedAt,
  isObservable,
  liveData,
  stepKey,
  recentEvents,
}: Props) => {
  const {events, refetch, loading} = recentEvents;
  const displayedEvent = events[0];
  const pools = asset.pools || [];
  const isPartitionedAsset = !!asset?.partitionDefinition;

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

      {pools.length ? (
        <SidebarSection title={pools.length === 1 ? 'Pool' : 'Pools'}>
          <Box margin={{horizontal: 24, vertical: 12}} flex={{gap: 4}}>
            {pools.map((pool, idx) => (
              <PoolTag key={idx} pool={pool} />
            ))}
          </Box>
        </SidebarSection>
      ) : null}

      {asset.freshnessPolicy && (
        <SidebarSection title="Freshness policy">
          <Box margin={{horizontal: 24, vertical: 12}} flex={{gap: 12, alignItems: 'flex-start'}}>
            <Body style={{flex: 1}}>{freshnessPolicyDescription(asset.freshnessPolicy)}</Body>
            <OverdueTag policy={asset.freshnessPolicy} assetKey={asset.assetKey} />
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

      {isPartitionedAsset ? null : (
        <>
          <SidebarSection title={!isObservable ? 'Latest materialization' : 'Latest observation'}>
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
                {!isObservable ? `No materializations found` : `No observations found`}
              </Box>
            )}
          </SidebarSection>
          <SidebarSection
            title={!isObservable ? 'Materialization tags' : 'Observation tags'}
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
                {!isObservable ? `No materializations found` : `No observations found`}
              </Box>
            )}
          </SidebarSection>
        </>
      )}
      <SidebarSection title="Metadata plots">
        {isPartitionedAsset ? (
          <AssetPartitionMetadataPlots
            assetKey={asset.assetKey}
            limit={120}
            columnCount={1}
            asSidebarSection
          />
        ) : (
          <AssetTimeMetadataPlots
            assetKey={asset.assetKey}
            limit={100}
            columnCount={1}
            asSidebarSection
          />
        )}
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
