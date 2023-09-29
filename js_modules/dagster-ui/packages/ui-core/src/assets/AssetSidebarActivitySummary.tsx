import {Body, Box, Colors, Icon, MiddleTruncate, Spinner} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {LiveDataForNode} from '../asset-graph/Utils';
import {SidebarAssetFragment} from '../asset-graph/types/SidebarAssetInfo.types';
import {SidebarSection} from '../pipelines/SidebarComponents';

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
import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {useGroupedEvents} from './groupByPartition';
import {useRecentAssetEvents} from './useRecentAssetEvents';

interface Props {
  asset: SidebarAssetFragment;
  liveData?: LiveDataForNode;
  isSourceAsset: boolean;
  stepKey: string;

  // This timestamp is a "hint", when it changes this component will refetch
  // to retrieve new data. Just don't want to poll the entire table query.
  assetLastMaterializedAt: string | undefined;
}

export const AssetSidebarActivitySummary: React.FC<Props> = ({
  asset,
  assetLastMaterializedAt,
  isSourceAsset,
  liveData,
  stepKey,
}) => {
  const {materializations, observations, loadedPartitionKeys, loading, refetch, xAxis} =
    useRecentAssetEvents(
      asset.assetKey,
      {},
      {assetHasDefinedPartitions: !!asset.partitionDefinition},
    );

  const grouped = useGroupedEvents(xAxis, materializations, observations, loadedPartitionKeys);
  const displayedEvent = isSourceAsset ? observations[0] : materializations[0];

  React.useEffect(() => {
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
            <Link to={assetDetailsPathForKey(asset.assetKey, {view: 'auto-materialize-history'})}>
              View auto-materialize history
            </Link>
            <Icon name="open_in_new" color={Colors.Link} />
          </Box>
          <Box margin={{horizontal: 24}} flex={{gap: 12, alignItems: 'flex-start'}}>
            <Body style={{flex: 1, marginBottom: 12}}>
              {automaterializePolicyDescription(asset.autoMaterializePolicy)}
            </Body>
            <AutomaterializePolicyTag policy={asset.autoMaterializePolicy} />
          </Box>
        </SidebarSection>
      )}

      {loadedPartitionKeys.length > 1 ? null : (
        <>
          <SidebarSection
            title={!isSourceAsset ? 'Materialization in last run' : 'Observation in last run'}
          >
            {displayedEvent ? (
              <div style={{margin: -1, maxWidth: '100%', overflowX: 'auto'}}>
                <LatestMaterializationMetadata
                  assetKey={asset.assetKey}
                  latest={displayedEvent}
                  liveData={liveData}
                />
              </div>
            ) : loading ? (
              <Box padding={{vertical: 20}}>
                <Spinner purpose="section" />
              </Box>
            ) : (
              <Box
                margin={{horizontal: 24, vertical: 12}}
                style={{color: Colors.Gray500, fontSize: '0.8rem'}}
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
                style={{color: Colors.Gray500, fontSize: '0.8rem'}}
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
      {liveData && liveData.assetChecks.length > 0 && (
        <SidebarSection title="Checks">
          <Box padding={{horizontal: 24, vertical: 12}} flex={{gap: 12, alignItems: 'center'}}>
            <ExecuteChecksButton assetNode={asset} checks={liveData.assetChecks} />
            <Link to={assetDetailsPathForKey(asset.assetKey, {view: 'checks'})}>
              View all check details
            </Link>
          </Box>

          {liveData.assetChecks.slice(0, 10).map((check) => (
            <Box
              key={check.name}
              border={{side: 'top', width: 1, color: Colors.KeylineGray}}
              padding={{vertical: 8, right: 12, left: 24}}
              flex={{
                gap: 8,
                direction: 'row',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <MiddleTruncate text={`${check.name}`} />
              <AssetCheckStatusTag
                check={check}
                execution={check.executionForLatestMaterialization}
              />
            </Box>
          ))}
          {liveData.assetChecks.length > 10 && (
            <Box
              padding={{vertical: 12, right: 12, left: 24}}
              border={{side: 'top', width: 1, color: Colors.KeylineGray}}
            >
              <Link to={assetDetailsPathForKey(asset.assetKey, {view: 'checks'})}>
                View {liveData.assetChecks.length - 10} more…
              </Link>
            </Box>
          )}
        </SidebarSection>
      )}
    </>
  );
};
