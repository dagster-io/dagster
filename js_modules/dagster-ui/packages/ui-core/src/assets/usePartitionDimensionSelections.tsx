import {useMemo, useState} from 'react';

import {placeholderDimensionSelection} from './MultipartitioningSupport';
import {
  PartitionDimensionSelection,
  PartitionHealthData,
  PartitionHealthDimension,
} from './usePartitionHealthData';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {QueryPersistedStateConfig, useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {useSetStateUpdateCallback} from '../hooks/useSetStateUpdateCallback';
import {
  allPartitionsRange,
  allPartitionsSpan,
  partitionsToText,
  spanTextToSelectionsOrError,
} from '../partitions/SpanRepresentation';

export type DimensionQueryState = {
  name: string;
  rangeText: string | undefined;
  isFromPartitionQueryStringParam: boolean;
};

export function buildSerializer(assetHealth: Pick<PartitionHealthData, 'dimensions'> | undefined) {
  const serializer: QueryPersistedStateConfig<DimensionQueryState[]> = {
    defaults: {},
    encode: (state) => {
      return Object.fromEntries(state.map((s) => [`${s.name}_range`, s.rangeText]));
    },
    decode: (qs) => {
      const results: Record<string, {text: string; isFromPartitionQueryStringParam: boolean}> = {};
      const {partition, ...remaining} = qs;

      // Set `partition` values first, then `_range` values. We need to ensure that the order
      // of the parameters in the `qs` object doesn't affect how `results` is populated.
      if (typeof partition === 'string') {
        const partitions = partition.split('|');
        partitions.forEach((partitionText, i) => {
          const name = assetHealth?.dimensions[i]?.name;
          if (name) {
            results[name] = {text: partitionText, isFromPartitionQueryStringParam: true};
          }
        });
      }

      // E.g. `default_range`
      for (const key in remaining) {
        if (key.endsWith('_range')) {
          const name = key.replace(/_range$/, '');
          const value = qs[key];
          if (typeof value === 'string') {
            results[name] = {text: value, isFromPartitionQueryStringParam: false};
          }
        }
      }

      return Object.entries(results).map(([name, {text, isFromPartitionQueryStringParam}]) => ({
        name,
        rangeText: text,
        isFromPartitionQueryStringParam,
      }));
    },
  };
  return serializer;
}

/**
 * This hook behaves like useState and manages the user's selected partition key
 * ranges on each partition dimension.
 *
 * Internally, this hook reads initial state from the query string and (optionally)
 * writes changes back to the query string using the compacted "spans" format.
 */
export const usePartitionDimensionSelections = (opts: {
  assetHealth: Pick<PartitionHealthData, 'dimensions'> | undefined;
  modifyQueryString: boolean;
  defaultSelection?: 'empty' | 'all';
  knownDimensionNames?: string[]; // improves loading state if available
  skipPartitionKeyValidation?: boolean;
  shouldReadPartitionQueryStringParam?: boolean; // This hook is used in 2 different cases
  // The first use case (AssetPartitions.tsx) uses this state to filter the available partitions to select from when filtering using time based partitions.
  // The second use case (LaunchAssetChoosePartitionsDialog.tsx) uses this state to store the user's selections, which includes non-time based partitions.
  //   For the second use case we rely on the "partition" query string param in addition to the existing "{dimension}_range" query string params.
}) => {
  const {
    assetHealth,
    defaultSelection = 'all',
    knownDimensionNames = [],
    modifyQueryString,
    skipPartitionKeyValidation,
    shouldReadPartitionQueryStringParam = false,
  } = opts;

  const serializer = useMemo(() => buildSerializer(assetHealth), [assetHealth]);
  const [query, setQuery] = useQueryPersistedState<DimensionQueryState[]>(serializer);
  const [local, setLocal] = useState<DimensionQueryState[]>([]);

  const knownDimensionNamesJSON = JSON.stringify(knownDimensionNames);

  const inflated = useMemo((): PartitionDimensionSelection[] => {
    if (!assetHealth || !assetHealth.dimensions.length) {
      return JSON.parse(knownDimensionNamesJSON).map(placeholderDimensionSelection);
    }
    return assetHealth.dimensions.map((dimension) => {
      const saved =
        local.find((s) => s.name === dimension.name) ||
        query.find((s) => s.name === dimension.name);

      // Note: It's valid for the user to clear the range to "", so it's
      // important that we persist "" and specifically check for `undefined`
      // when filling in the default value (all keys)
      if (
        saved?.rangeText !== undefined &&
        (shouldReadPartitionQueryStringParam || !saved?.isFromPartitionQueryStringParam)
      ) {
        const selections = spanTextToSelectionsOrError(
          dimension.partitionKeys,
          saved.rangeText,
          skipPartitionKeyValidation,
        );
        if (selections instanceof Error) {
          window.requestAnimationFrame(() => showCustomAlert({body: selections.message}));
          return emptyDimensionSelection(dimension);
        }
        return {dimension, ...selections};
      } else {
        return defaultSelection === 'all'
          ? allDimensionSelection(dimension)
          : emptyDimensionSelection(dimension);
      }
    });
  }, [
    assetHealth,
    knownDimensionNamesJSON,
    local,
    query,
    shouldReadPartitionQueryStringParam,
    skipPartitionKeyValidation,
    defaultSelection,
  ]);

  const setInflated = (dimensions: PartitionDimensionSelection[]) => {
    const next = dimensions.map((r) => {
      const allowedKeys = skipPartitionKeyValidation ? undefined : r.dimension.partitionKeys;
      const rangeText = partitionsToText(r.selectedKeys, allowedKeys);

      const saved =
        local.find((s) => s.name === r.dimension.name) ||
        query.find((s) => s.name === r.dimension.name);

      const defaultText = defaultSelection === 'all' ? allPartitionsSpan(r.dimension) : '';

      return {
        name: r.dimension.name,
        rangeText: rangeText !== defaultText ? rangeText : undefined,
        isFromPartitionQueryStringParam:
          saved && saved?.rangeText === rangeText ? saved.isFromPartitionQueryStringParam : false,
      };
    });
    if (modifyQueryString) {
      setQuery(next);
    } else {
      setLocal(next);
    }
  };

  return [inflated, useSetStateUpdateCallback(inflated, setInflated)] as const;
};

function emptyDimensionSelection(dimension: PartitionHealthDimension): PartitionDimensionSelection {
  return {dimension, selectedRanges: [], selectedKeys: []};
}

function allDimensionSelection(dimension: PartitionHealthDimension): PartitionDimensionSelection {
  return {
    dimension,
    selectedRanges: [allPartitionsRange(dimension)],
    selectedKeys: [...dimension.partitionKeys],
  };
}
