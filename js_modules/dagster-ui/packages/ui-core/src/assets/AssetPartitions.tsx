import {
  Box,
  Colors,
  Icon,
  Menu,
  MenuItem,
  Popover,
  Spinner,
  TextInput,
  Tooltip,
} from '@dagster-io/ui-components';
import isEqual from 'lodash/isEqual';
import uniq from 'lodash/uniq';
import {useMemo, useState} from 'react';

import {AssetPartitionDetailEmpty, AssetPartitionDetailLoader} from './AssetPartitionDetail';
import {AssetPartitionList} from './AssetPartitionList';
import {AssetPartitionStatus} from './AssetPartitionStatus';
import {AssetPartitionStatusCheckboxes} from './AssetPartitionStatusCheckboxes';
import {isTimeseriesDimension} from './MultipartitioningSupport';
import {AssetKey, AssetViewParams} from './types';
import {usePartitionDimensionSelections} from './usePartitionDimensionSelections';
import {
  keyCountByStateInSelection,
  partitionStatusAtIndex,
  rangesClippedToSelection,
  selectionRangeWithSingleKey,
  usePartitionHealthData,
} from './usePartitionHealthData';
import {usePartitionKeyInParams} from './usePartitionKeyInParams';
import {LiveDataForNode} from '../asset-graph/Utils';
import {PartitionDefinitionType, RepositorySelector} from '../graphql/types';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {SortButton} from '../launchpad/ConfigEditorConfigPicker';
import {DimensionRangeWizard} from '../partitions/DimensionRangeWizard';
import {testId} from '../testing/testId';
import {assertExists} from '../util/invariant';

interface Props {
  assetKey: AssetKey;
  assetPartitionDimensions?: string[];
  liveData?: LiveDataForNode;
  params: AssetViewParams;
  paramsTimeWindowOnly: boolean;
  setParams: (params: AssetViewParams) => void;

  // This timestamp is a "hint", when it changes this component will refetch
  // to retrieve new data. Just don't want to poll the entire table query.
  dataRefreshHint: string | undefined;

  repository?: RepositorySelector;
  opName?: string | null;
  isLoadingDefinition: boolean;
}

const DISPLAYED_STATUSES: AssetPartitionStatus[] = [
  AssetPartitionStatus.MISSING,
  AssetPartitionStatus.MATERIALIZING,
  AssetPartitionStatus.MATERIALIZED,
  AssetPartitionStatus.FAILED,
].sort();

enum SortType {
  CREATION,
  REVERSE_CREATION,
  ALPHABETICAL,
  REVERSE_ALPHABETICAL,
}

export const AssetPartitions = ({
  assetKey,
  assetPartitionDimensions,
  params,
  setParams,
  dataRefreshHint,
  isLoadingDefinition,
}: Props) => {
  const assetHealth = usePartitionHealthData([assetKey], dataRefreshHint)[0];
  const [selections, setSelections] = usePartitionDimensionSelections({
    knownDimensionNames: assetPartitionDimensions,
    modifyQueryString: true,
    assetHealth,
    shouldReadPartitionQueryStringParam: false,
    defaultSelection: 'all',
  });

  const [sortTypes, setSortTypes] = useState<Array<SortType>>([]);

  const [statusFilters, setStatusFilters] = useQueryPersistedState<AssetPartitionStatus[]>({
    defaults: {status: [...DISPLAYED_STATUSES].sort().join(',')},
    encode: (val) => ({status: [...val].sort().join(',')}),
    decode: (qs) => {
      const status = qs.status;
      if (typeof status === 'string') {
        return status
          .split(',')
          .filter((s): s is AssetPartitionStatus =>
            DISPLAYED_STATUSES.includes(s as AssetPartitionStatus),
          );
      }
      return [];
    },
  });

  const [searchValues, setSearchValues] = useState<string[]>([]);
  const updateSearchValue = (idx: number, value: string) => {
    setSearchValues((prev) => {
      const next = [...prev];

      // add empty strings for missing indices
      while (next.length <= idx) {
        next.push('');
      }

      next[idx] = value;
      return next;
    });
  };

  // Determine which axis we will show at the top of the page, if any.
  const timeDimensionIdx = selections.findIndex((s) => isTimeseriesDimension(s.dimension));

  const [focusedDimensionKeys, setFocusedDimensionKey] = usePartitionKeyInParams({
    params,
    setParams,
    dimensionCount: selections.length,
    defaultKeyInDimension: (dimensionIdx) =>
      assertExists(
        dimensionKeysInSelection(dimensionIdx)[0],
        'Expected at least one key in dimension selection',
      ),
  });

  // Get asset health on all dimensions, with the non-time dimensions scoped
  // to the time dimension selection (so the status of partition "VA" reflects
  // the selection you've made on the time axis.)
  const rangesForEachDimension = useMemo(() => {
    const [firstSelection] = selections;
    if (!assetHealth || !firstSelection) {
      return selections.map(() => []);
    }

    const timeDimensionSelection =
      timeDimensionIdx !== -1 ? selections[timeDimensionIdx] : undefined;

    return selections.map((_s, idx) =>
      assetHealth.rangesForSingleDimension(
        idx,
        idx === 1 && focusedDimensionKeys[0]
          ? [selectionRangeWithSingleKey(focusedDimensionKeys[0], firstSelection.dimension)]
          : timeDimensionSelection && idx !== timeDimensionIdx
            ? timeDimensionSelection.selectedRanges
            : undefined,
      ),
    );
  }, [assetHealth, selections, timeDimensionIdx, focusedDimensionKeys]);

  // This function returns the list of dimension keys INSIDE the `selections.selectedRanges`
  // specified at the top of the page that MATCH the state filters (success / completed).
  // There are pieces of this that could be moved to shared helpers, but we may discourage
  // loading the full key space and shift responsibility for this to GraphQL in the future.
  //
  const dimensionKeysInSelection = (idx: number) => {
    const selection = selections[idx];
    if (!selection) {
      return []; // loading
    }
    // Special case: If you have cleared the time selection in the top bar, we
    // clear all dimension columns, (even though you still have a dimension 2 selection)
    if (
      timeDimensionIdx !== -1 &&
      assertExists(selections[timeDimensionIdx], 'Expected time dimension selection').selectedRanges
        .length === 0
    ) {
      return [];
    }

    const {dimension, selectedRanges} = selection;
    const allKeys = dimension.partitionKeys;
    const sortType = getSort(sortTypes, idx, selection.dimension.type);

    const filterResultsBySearch = (keys: string[]) => {
      const searchLower = searchValues?.[idx]?.toLocaleLowerCase().trim() || '';
      return keys.filter((key) => key.toLowerCase().includes(searchLower));
    };

    const getSelectionKeys = () =>
      uniq(selectedRanges.flatMap(({start, end}) => allKeys.slice(start.idx, end.idx + 1)));

    // Early exit #1: If you have no status filters applied, just apply the
    // text search filter, sort and return.
    if (isEqual(DISPLAYED_STATUSES, statusFilters)) {
      return sortResults(filterResultsBySearch(getSelectionKeys()), sortType);
    }

    // Get the health ranges, and then explode them into a `matching` set of keys
    // that have the requested statuses.
    const healthRangesInSelection = rangesClippedToSelection(
      assertExists(rangesForEachDimension[idx], `Expected ranges for dimension ${idx}`),
      selectedRanges,
    );
    const getKeysWithStates = (states: AssetPartitionStatus[]) =>
      healthRangesInSelection.flatMap((r) =>
        states.some((s) => r.value.includes(s)) ? allKeys.slice(r.start.idx, r.end.idx + 1) : [],
      );
    const matching = uniq(
      getKeysWithStates(statusFilters.filter((f) => f !== AssetPartitionStatus.MISSING)),
    );

    let result;

    // We have to add in "missing" separately because it's the absence of a range.
    if (statusFilters.includes(AssetPartitionStatus.MISSING)) {
      const selectionKeys = getSelectionKeys();
      const isMissingForIndex = (idx: number) =>
        !healthRangesInSelection.some(
          (r) =>
            r.start.idx <= idx &&
            r.end.idx >= idx &&
            !r.value.includes(AssetPartitionStatus.MISSING),
        );

      const matchingSet = new Set(matching);
      const selectionKeysSet = new Set(selectionKeys);
      result = allKeys.filter(
        (a, pidx) => selectionKeysSet.has(a) && (matchingSet.has(a) || isMissingForIndex(pidx)),
      );
    } else {
      result = matching;
    }

    return sortResults(filterResultsBySearch(result), sortType);
  };

  if (!assetHealth) {
    return (
      <Box
        style={{height: 390}}
        flex={{direction: 'row', justifyContent: 'center', alignItems: 'center'}}
      >
        <Spinner purpose="page" />
      </Box>
    );
  }

  const countsByStateInSelection = keyCountByStateInSelection(assetHealth, selections);
  const countsFiltered = statusFilters.reduce((a, b) => a + countsByStateInSelection[b], 0);

  if (isLoadingDefinition) {
    return (
      <Box
        style={{height: 390}}
        flex={{direction: 'row', justifyContent: 'center', alignItems: 'center'}}
      >
        <Spinner purpose="page" />
      </Box>
    );
  }

  const timeDimensionSelection =
    timeDimensionIdx !== -1
      ? assertExists(selections[timeDimensionIdx], 'Expected time dimension selection')
      : null;

  return (
    <>
      {timeDimensionSelection && (
        <Box padding={{vertical: 16, horizontal: 24}} border="bottom">
          <DimensionRangeWizard
            dimensionType={timeDimensionSelection.dimension.type}
            partitionKeys={timeDimensionSelection.dimension.partitionKeys}
            health={{
              ranges: assertExists(
                rangesForEachDimension[timeDimensionIdx],
                'Expected ranges for time dimension',
              ),
            }}
            selected={timeDimensionSelection.selectedKeys}
            setSelected={(selectedKeys) =>
              setSelections(
                selections.map((r, idx) => (idx === timeDimensionIdx ? {...r, selectedKeys} : r)),
              )
            }
            showQuickSelectOptionsForStatuses={false}
          />
        </Box>
      )}
      <Box
        padding={{vertical: 16, horizontal: 24}}
        flex={{direction: 'row', justifyContent: 'space-between'}}
        border="bottom"
      >
        <div data-testid={testId('partitions-selected')}>
          已选择 {countsFiltered.toLocaleString()} 个分区
        </div>
        <AssetPartitionStatusCheckboxes
          counts={countsByStateInSelection}
          allowed={DISPLAYED_STATUSES}
          value={statusFilters}
          onChange={setStatusFilters}
        />
      </Box>
      <Box style={{flex: 1, minHeight: 0, outline: 'none'}} flex={{direction: 'row'}} tabIndex={-1}>
        {selections.map((selection, idx) => {
          const sortType = getSort(sortTypes, idx, selection.dimension.type);
          return (
            <Box
              key={selection.dimension.name}
              style={{display: 'flex', flex: 1, paddingRight: 1, minWidth: 200}}
              flex={{direction: 'column'}}
              border="right"
              background={Colors.backgroundLight()}
              data-testid={testId(`partitions-${selection.dimension.name}`)}
            >
              <Box
                border="bottom"
                background={Colors.backgroundDefault()}
                padding={{right: 16, vertical: 8, left: idx === 0 ? 24 : 16}}
              >
                <TextInput
                  icon="search"
                  fill
                  style={{width: `100%`}}
                  value={searchValues[idx] || ''}
                  onChange={(e) => updateSearchValue(idx, e.target.value)}
                  placeholder={
                    selection.dimension.name !== 'default'
                      ? `按 ${selection.dimension.name} 筛选…`
                      : '按名称筛选…'
                  }
                  data-testid={testId(`search-${idx}`)}
                  rightElement={
                    <Popover
                      content={
                        <Menu>
                          <MenuItem
                            text={
                              <Tooltip content="按分区创建顺序排序">
                                <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
                                  <span>按创建顺序</span>
                                  <Icon name="info" />
                                </Box>
                              </Tooltip>
                            }
                            active={SortType.CREATION === sortType}
                            onClick={() => {
                              setSortTypes((sorts) => {
                                const copy = [...sorts];
                                copy[idx] = SortType.CREATION;
                                return copy;
                              });
                            }}
                            data-testid={testId('sort-creation')}
                          />
                          <MenuItem
                            text={
                              <Tooltip content="按分区创建顺序的逆序排序">
                                <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
                                  <span>按创建逆序</span>
                                  <Icon name="info" />
                                </Box>
                              </Tooltip>
                            }
                            active={SortType.REVERSE_CREATION === sortType}
                            onClick={() => {
                              setSortTypes((sorts) => {
                                const copy = [...sorts];
                                copy[idx] = SortType.REVERSE_CREATION;
                                return copy;
                              });
                            }}
                            data-testid={testId('sort-reverse-creation')}
                          />
                          <MenuItem
                            text="按字母顺序"
                            active={SortType.ALPHABETICAL === sortType}
                            onClick={() => {
                              setSortTypes((sorts) => {
                                const copy = [...sorts];
                                copy[idx] = SortType.ALPHABETICAL;
                                return copy;
                              });
                            }}
                            data-testid={testId('sort-alphabetical')}
                          />
                          <MenuItem
                            text="按字母逆序"
                            active={SortType.REVERSE_ALPHABETICAL === sortType}
                            onClick={() => {
                              setSortTypes((sorts) => {
                                const copy = [...sorts];
                                copy[idx] = SortType.REVERSE_ALPHABETICAL;
                                return [...copy];
                              });
                            }}
                            data-testid={testId('sort-reverse-alphabetical')}
                          />
                        </Menu>
                      }
                      position="bottom-left"
                    >
                      <SortButton
                        data-testid={`sort-${idx}`}
                        style={{margin: 0, marginRight: -4, borderRadius: 6}}
                      >
                        <Icon name="sort_by_alpha" color={Colors.accentGray()} />
                      </SortButton>
                    </Popover>
                  }
                />
              </Box>

              {!assetHealth ? (
                <Box flex={{alignItems: 'center', justifyContent: 'center'}} style={{flex: 1}}>
                  <Spinner purpose="section" />
                </Box>
              ) : (
                <AssetPartitionList
                  partitions={dimensionKeysInSelection(idx)}
                  statusForPartition={(dimensionKey) => {
                    if (idx === 1 && focusedDimensionKeys[0]) {
                      return [assetHealth.stateForKey([focusedDimensionKeys[0], dimensionKey])];
                    }
                    const dimensionKeyIdx = selection.dimension.partitionKeys.indexOf(dimensionKey);
                    return partitionStatusAtIndex(
                      assertExists(
                        rangesForEachDimension[idx],
                        `Expected ranges for dimension ${idx}`,
                      ),
                      dimensionKeyIdx,
                    ).filter((s) => statusFilters.includes(s));
                  }}
                  focusedDimensionKey={focusedDimensionKeys[idx]}
                  setFocusedDimensionKey={(dimensionKey) => {
                    setFocusedDimensionKey(idx, dimensionKey);
                  }}
                />
              )}
            </Box>
          );
        })}

        <Box style={{flex: 3, minWidth: 0, overflowY: 'auto'}} flex={{direction: 'column'}}>
          {params.partition && focusedDimensionKeys.length === selections.length ? (
            <AssetPartitionDetailLoader assetKey={assetKey} partitionKey={params.partition} />
          ) : (
            <AssetPartitionDetailEmpty />
          )}
        </Box>
      </Box>
    </>
  );
};

const alphabeticalCollator = new Intl.Collator(navigator.language, {sensitivity: 'base'});

function sortResults(results: string[], sortType: SortType) {
  switch (sortType) {
    case SortType.CREATION:
      return results;
    case SortType.REVERSE_CREATION:
      return [...results].reverse();
    case SortType.ALPHABETICAL:
      return [...results].sort(alphabeticalCollator.compare);
    case SortType.REVERSE_ALPHABETICAL:
      return [...results].sort((a, b) => -alphabeticalCollator.compare(a, b));
  }
}

function getSort(sortTypes: Array<SortType>, idx: number, definitionType: PartitionDefinitionType) {
  const sortType = sortTypes[idx];
  if (sortType === undefined) {
    return definitionType === PartitionDefinitionType.TIME_WINDOW
      ? SortType.REVERSE_CREATION
      : SortType.CREATION;
  }
  return sortType;
}
