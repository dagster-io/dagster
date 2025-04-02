// eslint-disable-next-line no-restricted-imports
import {BreadcrumbProps} from '@blueprintjs/core';
import {Alert, Box, ErrorBoundary, Spinner, Tag} from '@dagster-io/ui-components';
import {useContext, useEffect, useMemo} from 'react';
import {Link, Redirect, useLocation, useRouteMatch} from 'react-router-dom';
import {useSetRecoilState} from 'recoil';
import {FeatureFlag} from 'shared/app/FeatureFlags.oss';
import {AssetPageHeader} from 'shared/assets/AssetPageHeader.oss';
import {getAssetFilterStateQueryString} from 'shared/assets/useAssetDefinitionFilterState.oss';

import {ASSET_NODE_CONFIG_FRAGMENT} from './AssetConfig';
import {AssetEvents} from './AssetEvents';
import {AssetFeatureContext} from './AssetFeatureContext';
import {ASSET_NODE_OP_METADATA_FRAGMENT} from './AssetMetadata';
import {ASSET_NODE_INSTIGATORS_FRAGMENT} from './AssetNodeInstigatorTag';
import {AssetNodeLineage} from './AssetNodeLineage';
import {AssetPartitions} from './AssetPartitions';
import {AssetTabs} from './AssetTabs';
import {AssetAutomationRoot} from './AutoMaterializePolicyPage/AssetAutomationRoot';
import {ChangedReasonsTag} from './ChangedReasons';
import {LaunchAssetExecutionButton} from './LaunchAssetExecutionButton';
import {UNDERLYING_OPS_ASSET_NODE_FRAGMENT} from './UnderlyingOpsOrGraph';
import {AssetChecks} from './asset-checks/AssetChecks';
import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {gql} from '../apollo-client';
import {featureEnabled} from '../app/Flags';
import {AssetNodeOverview, AssetNodeOverviewNonSDA} from './overview/AssetNodeOverview';
import {AssetKey, AssetViewParams} from './types';
import {AssetTableDefinitionFragment} from './types/AssetTableFragment.types';
import {AssetViewDefinitionNodeFragment} from './types/AssetView.types';
import {useAssetDefinition} from './useAssetDefinition';
import {useAssetViewParams} from './useAssetViewParams';
import {useDeleteDynamicPartitionsDialog} from './useDeleteDynamicPartitionsDialog';
import {healthRefreshHintFromLiveData} from './usePartitionHealthData';
import {useReportEventsDialog} from './useReportEventsDialog';
import {useWipeDialog} from './useWipeDialog';
import {currentPageAtom} from '../app/analytics';
import {Timestamp} from '../app/time/Timestamp';
import {AssetLiveDataRefreshButton, useAssetLiveData} from '../asset-data/AssetLiveDataProvider';
import {ASSET_NODE_FRAGMENT} from '../asset-graph/AssetNode';
import {
  GraphData,
  LiveDataForNodeWithStaleData,
  nodeDependsOnSelf,
  toGraphId,
  tokenForAssetKey,
} from '../asset-graph/Utils';
import {useAssetGraphData} from '../asset-graph/useAssetGraphData';
import {StaleReasonsTag} from '../assets/Stale';
import {IndeterminateLoadingBar} from '../ui/IndeterminateLoadingBar';
import {buildRepoAddress} from '../workspace/buildRepoAddress';

interface Props {
  assetKey: AssetKey;
  headerBreadcrumbs: BreadcrumbProps[];
  writeAssetVisit?: (assetKey: AssetKey) => void;
  currentPath: string[];
}

export const AssetView = ({assetKey, headerBreadcrumbs, writeAssetVisit, currentPath}: Props) => {
  const [params, setParams] = useAssetViewParams();
  const {useTabBuilder, renderFeatureView} = useContext(AssetFeatureContext);

  // Load the asset definition
  const {cachedDefinition, definition, definitionQueryResult, lastMaterialization} =
    useAssetDefinition(assetKey);

  const cachedOrLiveDefinition = definition ?? cachedDefinition;

  useEffect(() => {
    // If the asset exists, add it to the recently visited list
    if (
      definitionQueryResult.loading === false &&
      definitionQueryResult.data?.assetOrError.__typename === 'Asset' &&
      writeAssetVisit
    ) {
      writeAssetVisit({path: assetKey.path});
    }
  }, [definitionQueryResult, writeAssetVisit, assetKey.path]);

  const tabList = useTabBuilder({definition: cachedOrLiveDefinition, params});

  const defaultTab = 'overview';
  const selectedTab = params.view || defaultTab;

  // Load the asset graph - a large graph for the Lineage tab, a small graph for the Definition tab
  // tab, or just the current node for other tabs. NOTE: Changing the query does not re-fetch data,
  // it just re-filters.
  const visible = getQueryForVisibleAssets(assetKey, selectedTab, params);
  const visibleAssetGraph = useAssetGraphData(visible.query, {
    hideEdgesToNodesOutsideQuery: true,
  });

  const {upstream, downstream} = useNeighborsFromGraph(visibleAssetGraph.assetGraphData, assetKey);
  const node = visibleAssetGraph.assetGraphData?.nodes[toGraphId(assetKey)];

  const {liveData, refresh} = useAssetLiveData(assetKey);

  // The "live" data is preferable and more current, but only available for SDAs. Fallback
  // to the materialization timestamp we loaded from assetOrError if live data is not available.
  const lastMaterializedAt = (liveData?.lastMaterialization || lastMaterialization)?.timestamp;
  const viewingMostRecent = !params.asOf || Number(lastMaterializedAt) <= Number(params.asOf);

  // Some tabs make expensive queries that should be refreshed after materializations or failures.
  // We build a hint string from the live summary info and refresh the views when the hint changes.
  const dataRefreshHint = liveData
    ? healthRefreshHintFromLiveData(liveData)
    : lastMaterialization?.timestamp;

  const isLoading = !definitionQueryResult.previousData && !definitionQueryResult.data;

  const renderOverviewTab = () => {
    if (!definition && !isLoading) {
      return (
        <AssetNodeOverviewNonSDA assetKey={assetKey} lastMaterialization={lastMaterialization} />
      );
    }
    return (
      <AssetNodeOverview
        assetKey={assetKey}
        assetNode={definition}
        cachedAssetNode={cachedDefinition}
        upstream={upstream}
        downstream={downstream}
        liveData={liveData}
        dependsOnSelf={node ? nodeDependsOnSelf(node) : false}
      />
    );
  };

  const renderLineageTab = () => {
    if (!visibleAssetGraph.assetGraphData) {
      return (
        <Box style={{flex: 1}} flex={{alignItems: 'center', justifyContent: 'center'}}>
          <Spinner purpose="page" />
        </Box>
      );
    }
    return (
      <AssetNodeLineage
        params={params}
        setParams={setParams}
        assetKey={assetKey}
        requestedDepth={visible.requestedDepth}
        assetGraphData={visibleAssetGraph.assetGraphData}
        graphQueryItems={visibleAssetGraph.graphQueryItems}
      />
    );
  };

  const renderPartitionsTab = () => {
    // We don't render <AssetLoadingDefinitionState /> here like the other tabs because
    // AssetPartitions makes graphql requests and we want to avoid a request waterfall.
    // Instead AssetPartitions will render the AssetLoadingDefinitionState itself.
    if (!isLoading && !definition?.isMaterializable) {
      return <Redirect to={assetDetailsPathForKey(assetKey, {view: 'events'})} />;
    }

    return (
      <AssetPartitions
        assetKey={assetKey}
        assetPartitionDimensions={definition?.partitionKeysByDimension.map((k) => k.name)}
        isLoadingDefinition={definitionQueryResult.loading && !definitionQueryResult.previousData}
        dataRefreshHint={dataRefreshHint}
        params={params}
        paramsTimeWindowOnly={!!params.asOf}
        setParams={setParams}
      />
    );
  };

  const renderEventsTab = () => {
    if (isLoading) {
      return <AssetLoadingDefinitionState />;
    }
    return (
      <AssetEvents
        assetKey={assetKey}
        assetNode={definition}
        dataRefreshHint={dataRefreshHint}
        params={params}
        paramsTimeWindowOnly={!!params.asOf}
        setParams={setParams}
        liveData={definition ? liveData : undefined}
      />
    );
  };

  const renderAutomaterializeHistoryTab = () => {
    if (isLoading) {
      return <AssetLoadingDefinitionState />;
    }

    return <AssetAutomationRoot assetKey={assetKey} definition={definition} />;
  };

  const renderChecksTab = () => {
    if (isLoading) {
      return <AssetLoadingDefinitionState />;
    }
    return (
      <AssetChecks
        assetKey={assetKey}
        lastMaterializationTimestamp={lastMaterialization?.timestamp}
      />
    );
  };

  const renderContent = () => {
    switch (selectedTab) {
      case 'overview':
        return renderOverviewTab();
      case 'lineage':
        return renderLineageTab();
      case 'partitions':
        return renderPartitionsTab();
      case 'events':
        return renderEventsTab();
      case 'automation':
        return renderAutomaterializeHistoryTab();
      case 'checks':
        return renderChecksTab();
      default:
        return renderFeatureView({
          selectedTab,
          assetKey,
          definition,
        });
    }
  };

  const repoAddress = useMemo(
    () =>
      definition
        ? buildRepoAddress(definition.repository.name, definition.repository.location.name)
        : null,
    [definition],
  );

  const setCurrentPage = useSetRecoilState(currentPageAtom);
  const {path} = useRouteMatch();
  useEffect(() => {
    setCurrentPage(({specificPath}) => ({specificPath, path: `${path}?view=${selectedTab}`}));
  }, [path, selectedTab, setCurrentPage]);

  const wipe = useWipeDialog(
    definition && !definition.isObservable
      ? {
          assetKey: definition.assetKey,
          repository: definition.repository,
        }
      : null,
    refresh,
  );

  const dynamicPartitionsDelete = useDeleteDynamicPartitionsDialog(
    definition && repoAddress ? {assetKey: definition.assetKey, definition, repoAddress} : null,
    () => {
      definitionQueryResult.fetch();
      refresh();
    },
  );

  const reportEvents = useReportEventsDialog(
    definition && !definition.isObservable && repoAddress
      ? {
          assetKey: definition.assetKey,
          isPartitioned: definition.isPartitioned,
          hasReportRunlessAssetEventPermission: definition.hasReportRunlessAssetEventPermission,
          repoAddress,
        }
      : null,
    refresh,
  );

  if (definitionQueryResult.data?.assetOrError.__typename === 'AssetNotFoundError') {
    // Redirect to the asset catalog
    return (
      <Redirect
        to={`/assets/${currentPath.join('/')}?view=folder${getAssetFilterStateQueryString()}`}
      />
    );
  }

  return (
    <Box
      flex={{direction: 'column', grow: 1}}
      style={{height: '100%', width: '100%', overflowY: 'auto'}}
    >
      <AssetPageHeader
        view="asset"
        assetKey={assetKey}
        headerBreadcrumbs={headerBreadcrumbs}
        tags={
          <AssetViewPageHeaderTags
            definition={cachedOrLiveDefinition}
            liveData={liveData}
            onShowUpstream={() => setParams({...params, view: 'lineage', lineageScope: 'upstream'})}
          />
        }
        tabs={
          <div>
            <IndeterminateLoadingBar $loading={isLoading} />
            <Box flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'flex-end'}}>
              <AssetTabs selectedTab={selectedTab} tabs={tabList} />
              <Box padding={{bottom: 8}}>
                <AssetLiveDataRefreshButton />
              </Box>
            </Box>
          </div>
        }
        right={
          <Box style={{margin: '-4px 0'}} flex={{direction: 'row', gap: 8}}>
            {reportEvents.element}
            {wipe.element}
            {dynamicPartitionsDelete.element}
            {cachedOrLiveDefinition && cachedOrLiveDefinition.jobNames.length > 0 ? (
              <LaunchAssetExecutionButton
                scope={{all: [cachedOrLiveDefinition]}}
                showChangedAndMissingOption={false}
                additionalDropdownOptions={[
                  ...reportEvents.dropdownOptions,
                  ...wipe.dropdownOptions,
                  ...dynamicPartitionsDelete.dropdownOptions,
                ]}
              />
            ) : undefined}
          </Box>
        }
      />
      {!viewingMostRecent && params.asOf && (
        <HistoricalViewAlert asOf={params.asOf} hasDefinition={!!definition} />
      )}
      <ErrorBoundary region="page" resetErrorOnChange={[assetKey, params]}>
        {renderContent()}
      </ErrorBoundary>
    </Box>
  );
};

const AssetLoadingDefinitionState = () => (
  <Box
    style={{height: 390}}
    flex={{direction: 'row', justifyContent: 'center', alignItems: 'center'}}
  >
    <Spinner purpose="page" />
  </Box>
);

// This is a helper method that returns the "asset graph query string" for the current
// AssetView tab + page settings. eg:
// - If you're viewing the "Lineage > Upstream 4 layers", it returns `++++token`
// - If you're viewing the definition tab, it returns  "+token+" (upstream, downstream are visible)
// - If you're viewing the overview / events tabs, it just returns "token"
//
function getQueryForVisibleAssets(
  assetKey: AssetKey,
  view: string,
  {lineageDepth, lineageScope}: AssetViewParams,
) {
  const token = tokenForAssetKey(assetKey);

  if (view === 'definition' || view === 'overview') {
    return {
      query: featureEnabled(FeatureFlag.flagSelectionSyntax)
        ? `1+key:"${token}"+1`
        : `+"${token}"+`,
      requestedDepth: 1,
    };
  }
  if (view === 'lineage') {
    const defaultDepth = 1;
    const requestedDepth = Number(lineageDepth) || defaultDepth;

    if (featureEnabled(FeatureFlag.flagSelectionSyntax)) {
      if (lineageScope === 'upstream') {
        return {
          query: `${requestedDepth}+key:"${token}"`,
          requestedDepth,
        };
      } else if (lineageScope === 'downstream') {
        return {
          query: `key:"${token}"+${requestedDepth}`,
          requestedDepth,
        };
      }
      return {
        query: `${requestedDepth}+key:"${token}"+${requestedDepth}`,
        requestedDepth,
      };
    }

    const depthStr = '+'.repeat(requestedDepth);

    // Load the asset lineage (for both lineage tab and definition "Upstream" / "Downstream")
    const query =
      view === 'lineage' && lineageScope === 'upstream'
        ? `${depthStr}"${token}"`
        : view === 'lineage' && lineageScope === 'downstream'
          ? `"${token}"${depthStr}`
          : `${depthStr}"${token}"${depthStr}`;

    return {
      query,
      requestedDepth,
    };
  }
  return {query: `"${token}"`, requestedDepth: 0};
}

function useNeighborsFromGraph(graphData: GraphData | null, assetKey: AssetKey) {
  const graphId = toGraphId(assetKey);

  return useMemo(() => {
    if (!graphData) {
      return {upstream: null, downstream: null};
    }
    return {
      upstream: Object.values(graphData.nodes)
        .filter((n) => graphData.upstream[graphId]?.[toGraphId(n.assetKey)])
        .map((n) => n.definition),
      downstream: Object.values(graphData.nodes)
        .filter((n) => graphData.downstream[graphId]?.[toGraphId(n.assetKey)])
        .map((n) => n.definition),
    };
  }, [graphData, graphId]);
}

export const ASSET_VIEW_DEFINITION_QUERY = gql`
  query AssetViewDefinitionQuery($assetKey: AssetKeyInput!) {
    assetOrError(assetKey: $assetKey) {
      ... on Asset {
        id
        key {
          path
        }
        assetMaterializations(limit: 1) {
          timestamp
          runId
        }
        definition {
          id
          ...AssetViewDefinitionNode
        }
      }
    }
  }

  fragment AssetViewDefinitionNode on AssetNode {
    id
    pools
    groupName
    isExecutable
    automationCondition {
      label
      expandedLabel
    }
    partitionDefinition {
      description
      dimensionTypes {
        type
        dynamicPartitionsDefinitionName
      }
    }
    partitionKeysByDimension {
      name
    }
    owners {
      ... on TeamAssetOwner {
        team
      }
      ... on UserAssetOwner {
        email
      }
    }
    autoMaterializePolicy {
      rules {
        className
        description
        decisionType
      }
    }
    freshnessPolicy {
      maximumLagMinutes
      cronSchedule
      cronScheduleTimezone
    }
    backfillPolicy {
      description
    }
    requiredResources {
      resourceKey
    }
    repository {
      id
      name
      location {
        id
        name
      }
    }
    hasReportRunlessAssetEventPermission

    ...AssetNodeFragment
    ...AssetNodeConfigFragment
    ...AssetNodeInstigatorsFragment
    ...UnderlyingOpsAssetNodeFragment
    ...AssetNodeOpMetadataFragment
  }

  ${ASSET_NODE_FRAGMENT}
  ${ASSET_NODE_CONFIG_FRAGMENT}
  ${ASSET_NODE_INSTIGATORS_FRAGMENT}
  ${ASSET_NODE_OP_METADATA_FRAGMENT}
  ${UNDERLYING_OPS_ASSET_NODE_FRAGMENT}
`;

const HistoricalViewAlert = ({asOf, hasDefinition}: {asOf: string; hasDefinition: boolean}) => {
  const {pathname, search} = useLocation();
  const searchParams = new URLSearchParams(search);
  searchParams.delete('asOf');
  searchParams.set('time', asOf);

  return (
    <Box padding={{vertical: 16, horizontal: 24}} border="bottom">
      <Alert
        intent="info"
        title={
          <span>
            This is a historical view of materializations as of{' '}
            <span style={{fontWeight: 600}}>
              <Timestamp
                timestamp={{ms: Number(asOf)}}
                timeFormat={{showSeconds: true, showTimezone: true}}
              />
            </span>
            .
          </span>
        }
        description={
          <Link to={`${pathname}?${searchParams.toString()}`}>
            {hasDefinition
              ? 'Show definition and latest materializations'
              : 'Show latest materializations'}
          </Link>
        }
      />
    </Box>
  );
};

const AssetViewPageHeaderTags = ({
  definition,
  liveData,
  onShowUpstream,
}: {
  definition: AssetViewDefinitionNodeFragment | AssetTableDefinitionFragment | null | undefined;
  liveData?: LiveDataForNodeWithStaleData;
  onShowUpstream: () => void;
}) => {
  // In the new UI, all other tags are shown in the right sidebar of the overview tab.
  // When the old code below is removed, some of these components may no longer be used.
  return (
    <>
      {definition ? (
        <>
          <StaleReasonsTag
            liveData={liveData}
            assetKey={definition.assetKey}
            onClick={onShowUpstream}
          />
          <ChangedReasonsTag
            changedReasons={definition.changedReasons}
            assetKey={definition.assetKey}
          />
        </>
      ) : null}
      {!definition?.isMaterializable ? <Tag>External Asset</Tag> : undefined}
    </>
  );
};
