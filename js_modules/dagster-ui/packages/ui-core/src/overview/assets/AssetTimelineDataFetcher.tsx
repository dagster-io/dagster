import {gql, useApolloClient} from '@apollo/client';
import React from 'react';

import {
  AssetTimelineQuery,
  AssetTimelineQueryVariables,
  RunWithAssetsFragment,
} from './types/AssetTimelineDataFetcher.types';
import {showCustomAlert} from '../../app/CustomAlertProvider';
import {PYTHON_ERROR_FRAGMENT} from '../../app/PythonErrorFragment';
import {PythonErrorInfo} from '../../app/PythonErrorInfo';
import {tokenForAssetKey} from '../../asset-graph/Utils';
import {AssetTableFragment} from '../../assets/types/AssetTableFragment.types';
import {AssetKeyInput, RunStatus} from '../../graphql/types';
import {usePredicateMemo} from '../../hooks/usePredicateMemo';
import {SCHEDULE_FUTURE_TICKS_FRAGMENT} from '../../instance/NextTick';
import {doneStatuses} from '../../runs/RunStatuses';
import {RUN_TIME_FRAGMENT} from '../../runs/RunUtils';

const POLL_INTERVAL = 60 * 1000;

export type CodeLocationNodes = Record<
  string,
  {
    locationName: string;
    repoAddress: {
      name: string;
      location: string;
    };
    groups: Record<
      string,
      {
        groupName: string;
        groupId: string;
        assets: AssetTableFragment[];
      }
    >;
  }
>;

export const DataFetcherContext = React.createContext<{
  subscribeToAssetData: (key: AssetKeyInput, listener: (data: any) => void) => () => void;
  subscribeToGroupData: (name: string, listener: (data: any) => void) => () => void;
  subscribeToCodeLocationData: (name: string, listener: (data: any) => void) => () => void;
}>({
  subscribeToAssetData: (_name, _listener) => () => {},
  subscribeToGroupData: (_name, _listener) => () => {},
  subscribeToCodeLocationData: (_name, _listener) => () => {},
});

export type AssetTimelineRowDataState = {runs: RunWithAssetsFragment[]; loading: boolean};
type Listener = (state: AssetTimelineRowDataState) => void;

export const AssetsTimelineDataFetcher = ({
  codeLocationNodes,
  children,
  range,
}: {
  codeLocationNodes: CodeLocationNodes;
  children: React.ReactNode;
  range: [number, number];
}) => {
  const [start, end] = range;

  const startSecRef = React.useRef(start);
  const endSecRef = React.useRef(start);
  startSecRef.current = start;
  endSecRef.current = end;

  const runsCache = React.useRef<{
    locations: Record<string, {runs: RunWithAssetsFragment[]; loading: boolean}>;
    groups: Record<string, {runs: RunWithAssetsFragment[]; loading: boolean}>;
    assets: Record<string, {runs: RunWithAssetsFragment[]; loading: boolean}>;
  }>({
    locations: {},
    groups: {},
    assets: {},
  });

  const codeLocationSubscriptions = React.useRef<Record<string, Listener>>({});
  const assetSubscriptions = React.useRef<Record<string, Listener>>({});
  const groupSubscriptions = React.useRef<Record<string, Listener>>({});

  const didRangeMeaningfullyChange = usePredicateMemo(
    (prevRange, currentRange) =>
      Math.abs((prevRange?.[0] ?? Infinity) - currentRange[0]!) > 59999 ||
      Math.abs((prevRange?.[1] ?? Infinity) - currentRange[1]!) > 59999,
    [range[0], range[1]],
  );

  const didCodeLocationNodesChange = usePredicateMemo(
    (prev, current) => {
      if (prev?.[1] !== current[1]) {
        return 'range' + didRangeMeaningfullyChange;
      }
      const prevKeys = new Set(Object.keys(prev?.[0] ?? {}));
      const currentKeys = Object.keys(current[0]);
      return currentKeys.every((key) => prevKeys.has(key));
    },
    [codeLocationNodes, didRangeMeaningfullyChange] as const,
  );

  const client = useApolloClient();
  React.useEffect(() => {
    let isInProgress = false;
    let isCanceled = false;
    async function tick(isRefresh: boolean = false) {
      if (isInProgress) {
        return;
      }
      isInProgress = true;
      await Promise.allSettled(
        Object.keys(codeLocationSubscriptions.current).map((locationName) => {
          const node = codeLocationNodes[locationName];
          const groups = node?.groups;
          if (!groups) {
            return Promise.resolve();
          }
          const assetToGroup: Record<string, string> = {};
          const assetKeys = Object.values(groups)
            .flatMap(({assets, groupId}) => {
              assets.forEach((asset) => {
                const stringKey = tokenForAssetKey(asset.key);
                assetToGroup[stringKey] = groupId;
              });
              return assets;
            })
            .map((asset) => ({path: asset.key.path}));

          if (!assetKeys.length) {
            return Promise.resolve();
          }

          function triggerListeners() {
            const listener = codeLocationSubscriptions.current[locationName];
            if (listener) {
              listener(runsCache.current.locations[locationName]!);
            }

            Object.keys(groups!).forEach((groupKey) => {
              const listener = groupSubscriptions.current[groupKey];
              if (listener) {
                listener(runsCache.current.groups[groupKey]!);
              }
              assetKeys.forEach((key) => {
                const stringAssetKey = tokenForAssetKey(key);
                const listener = assetSubscriptions.current[stringAssetKey];
                if (listener) {
                  listener(runsCache.current.assets[stringAssetKey]!);
                }
              });
            });
          }

          if (isRefresh) {
            // Mark all of the assets as loading again
            runsCache.current.locations[locationName] = {
              runs: runsCache.current.locations[locationName]?.runs ?? [],
              loading: true,
            };
            Object.keys(groups).forEach((groupKey) => {
              runsCache.current.groups[groupKey] = {
                runs: runsCache.current.groups[groupKey]?.runs ?? [],
                loading: true,
              };
              assetKeys.forEach((key) => {
                const stringAssetKey = tokenForAssetKey(key);
                runsCache.current.assets[stringAssetKey] = {
                  runs: runsCache.current.assets[stringAssetKey]?.runs ?? [],
                  loading: true,
                };
              });
            });
            triggerListeners();
          }

          return new Promise(async (res) => {
            const {data} = await client.query<AssetTimelineQuery, AssetTimelineQueryVariables>({
              query: ASSET_TIMELINE_QUERY,
              variables: {
                inProgressFilter: {
                  statuses: [RunStatus.CANCELING, RunStatus.STARTED],
                  createdBefore: endSecRef.current / 1000,
                  assetKeys,
                },
                terminatedFilter: {
                  statuses: Array.from(doneStatuses),
                  createdBefore: endSecRef.current / 1000,
                  updatedAfter: startSecRef.current / 1000,
                  assetKeys,
                },
                tickCursor: startSecRef.current / 1000,
                ticksUntil: endSecRef.current / 1000,
              },
            });
            res(void 0);

            if (isCanceled) {
              return;
            }

            const {terminated, unterminated} = data;
            if (terminated.__typename !== 'Runs' || unterminated.__typename !== 'Runs') {
              if (terminated.__typename === 'PythonError') {
                showCustomAlert({
                  title: 'Error',
                  body: <PythonErrorInfo error={terminated} />,
                });
              }
              if (unterminated.__typename === 'PythonError') {
                showCustomAlert({
                  title: 'Error',
                  body: <PythonErrorInfo error={unterminated} />,
                });
              }
              return;
            }

            const groupedRuns = groupRunsByGroup(
              [...terminated.results, ...unterminated.results],
              assetToGroup,
            );

            runsCache.current.locations[locationName] = {
              runs: [...Array.from(terminated.results), ...Array.from(unterminated.results)],
              loading: false,
            };
            Object.keys(groups).forEach((groupKey) => {
              const runs = groupedRuns[groupKey]?.runs ?? [];
              runsCache.current.groups[groupKey] = {
                runs: Array.from(runs),
                loading: false,
              };
              assetKeys.forEach((key) => {
                const stringAssetKey = tokenForAssetKey(key);
                runsCache.current.assets[stringAssetKey] = {
                  runs: groupedRuns[groupKey]?.assets[stringAssetKey] ?? [],
                  loading: false,
                };
              });
            });
            triggerListeners();
          });
        }),
      );
      isInProgress = false;
    }

    const interval = setInterval(tick, POLL_INTERVAL);
    setTimeout(() => tick(true), 100);
    return () => {
      isCanceled = true;
      clearInterval(interval);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [client, didCodeLocationNodesChange, didRangeMeaningfullyChange]);

  const value = React.useMemo(() => {
    return {
      subscribeToAssetData: (key: AssetKeyInput, listener: Listener) => {
        const stringKey = tokenForAssetKey(key);
        assetSubscriptions.current[stringKey] = listener;
        const data = runsCache.current.assets[stringKey];
        if (data) {
          listener(data);
        }
        return () => {
          delete assetSubscriptions.current[stringKey];
        };
      },
      subscribeToGroupData: (groupName: string, listener: Listener) => {
        groupSubscriptions.current[groupName] = listener;
        const data = runsCache.current.groups[groupName];
        if (data) {
          listener(data);
        }
        return () => {
          delete groupSubscriptions.current[groupName];
        };
      },
      subscribeToCodeLocationData: (codeLocation: string, listener: Listener) => {
        codeLocationSubscriptions.current[codeLocation] = listener;
        const data = runsCache.current.locations[codeLocation];
        if (data) {
          listener(data);
        }
        return () => {
          delete codeLocationSubscriptions.current[codeLocation];
        };
      },
    };
  }, []);
  return <DataFetcherContext.Provider value={value}>{children}</DataFetcherContext.Provider>;
};

function groupRunsByGroup(runs: RunWithAssetsFragment[], assetToGroup: Record<string, string>) {
  const groupedRuns: Record<
    string,
    {
      assets: Record<string, RunWithAssetsFragment[]>;
      runs: Set<RunWithAssetsFragment>;
    }
  > = {};

  runs.forEach((run) => {
    const {assets} = run;
    assets.forEach((asset) => {
      const stringKey = tokenForAssetKey(asset.key);
      const group = assetToGroup[stringKey]!;
      groupedRuns[group] = groupedRuns[group] || {
        assets: {},
        runs: new Set(),
      };
      groupedRuns[group]!.runs.add(run);
      groupedRuns[group]!.assets[stringKey] = groupedRuns[group]!.assets[stringKey] || [];
      groupedRuns[group]!.assets[stringKey]!.push(run);
    });
  });

  return groupedRuns;
}

export const ASSET_TIMELINE_QUERY = gql`
  query AssetTimelineQuery(
    $inProgressFilter: RunsFilter!
    $terminatedFilter: RunsFilter!
    $tickCursor: Float
    $ticksUntil: Float
  ) {
    unterminated: runsOrError(filter: $inProgressFilter) {
      ... on Runs {
        results {
          id
          ...RunWithAssetsFragment
        }
      }
      ...PythonErrorFragment
    }
    terminated: runsOrError(filter: $terminatedFilter) {
      ... on Runs {
        results {
          id
          ...RunWithAssetsFragment
        }
      }
      ...PythonErrorFragment
    }
    workspaceOrError {
      ... on Workspace {
        id
        locationEntries {
          id
          name
          loadStatus
          displayMetadata {
            key
            value
          }
          locationOrLoadError {
            ... on RepositoryLocation {
              id
              name
              repositories {
                id
                name
                pipelines {
                  id
                  name
                  isJob
                }
                schedules {
                  id
                  name
                  pipelineName
                  scheduleState {
                    id
                    status
                  }
                  ...ScheduleFutureTicksFragment
                }
              }
            }
          }
        }
      }
    }
  }

  fragment RunWithAssetsFragment on Run {
    id
    pipelineName
    repositoryOrigin {
      id
      repositoryName
      repositoryLocationName
    }
    assets {
      id
      key {
        path
      }
    }
    assetMaterializations {
      assetKey {
        path
      }
    }
    ...RunTimeFragment
  }

  ${RUN_TIME_FRAGMENT}
  ${SCHEDULE_FUTURE_TICKS_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;
