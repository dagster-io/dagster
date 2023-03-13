import React from 'react';

import {QueryPersistedStateConfig, useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {useSetStateUpdateCallback} from '../hooks/useSetStateUpdateCallback';
import {
  allPartitionsSpan,
  partitionsToText,
  allPartitionsRange,
  spanTextToSelections,
} from '../partitions/SpanRepresentation';

import {placeholderDimensionSelection} from './MultipartitioningSupport';
import {PartitionHealthData, PartitionDimensionSelection} from './usePartitionHealthData';

type DimensionQueryState = {
  name: string;
  rangeText: string | undefined;
  isFromPartitionQueryStringParam: boolean;
};

function buildSerializer(assetHealth: Pick<PartitionHealthData, 'dimensions'>) {
  const serializer: QueryPersistedStateConfig<DimensionQueryState[]> = {
    defaults: {},
    encode: (state) => {
      return Object.fromEntries(state.map((s) => [`${s.name}_range`, s.rangeText]));
    },
    decode: (qs) => {
      const results: Record<string, {text: string; isFromPartitionQueryStringParam: boolean}> = {};
      for (const key in qs) {
        if (key.endsWith('_range')) {
          const name = key.replace(/_range$/, '');
          results[name] = {text: qs[key], isFromPartitionQueryStringParam: false};
        } else if (key === 'partition') {
          const partitions = qs[key].split('|');
          for (let i = 0; i < partitions.length; i++) {
            const partitionText = partitions[i];
            const name = assetHealth?.dimensions[i]?.name;
            if (name) {
              results[name] = {text: partitionText, isFromPartitionQueryStringParam: true};
            }
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
  assetHealth: Pick<PartitionHealthData, 'dimensions'>;
  modifyQueryString: boolean;
  knownDimensionNames?: string[]; // improves loading state if available
  skipPartitionKeyValidation?: boolean;
  shouldReadPartitionQueryStringParam?: boolean; // This hook is used in 2 different cases and it's a little weird because the first use case is inconsistent with the second.
  // The first use case uses the data to filter the UI, whereas the second use case uses it ONLY to record the user's selections.

  // The first use case is in AssetPartitions.tsx and it uses this state to filter the partitions in the table but only for time partitioned dimensions.
  // For non time partitioned dimension we don't want to do any filtering at all in this view. So for that reason we set shouldFilterPartitions to false
  // which means we ignore the "partition" query string param and only rely on the "date_range" params.

  // The second use case is in LaunchAssetChoosePartitionsDialog and it's being used to record the selections the user makes.
  // In this case we don't ignore the "partition" query string param
}) => {
  const {
    assetHealth,
    knownDimensionNames = [],
    modifyQueryString,
    skipPartitionKeyValidation,
    shouldReadPartitionQueryStringParam = false,
  } = opts;

  const serializer = React.useMemo(() => buildSerializer(assetHealth), [assetHealth]);
  const [query, setQuery] = useQueryPersistedState<DimensionQueryState[]>(serializer);
  const [local, setLocal] = React.useState<DimensionQueryState[]>([]);

  const knownDimensionNamesJSON = JSON.stringify(knownDimensionNames);

  const inflated = React.useMemo((): PartitionDimensionSelection[] => {
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
        return {
          dimension,
          ...spanTextToSelections(
            dimension.partitionKeys,
            saved.rangeText,
            skipPartitionKeyValidation,
          ),
        };
      } else {
        return {
          dimension,
          selectedRanges: [allPartitionsRange(dimension)],
          selectedKeys: [...dimension.partitionKeys],
        };
      }
    });
  }, [
    assetHealth,
    knownDimensionNamesJSON,
    local,
    query,
    shouldReadPartitionQueryStringParam,
    skipPartitionKeyValidation,
  ]);

  const setInflated = (ranges: PartitionDimensionSelection[]) => {
    const next = ranges.map((r) => {
      const rangeText = partitionsToText(
        r.selectedKeys,
        skipPartitionKeyValidation ? undefined : r.dimension.partitionKeys,
      );

      const saved =
        local.find((s) => s.name === r.dimension.name) ||
        query.find((s) => s.name === r.dimension.name);

      return {
        name: r.dimension.name,
        rangeText: rangeText !== allPartitionsSpan(r.dimension) ? rangeText : undefined,
        isFromPartitionQueryStringParam:
          saved?.rangeText === rangeText ? saved.isFromPartitionQueryStringParam : false,
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
