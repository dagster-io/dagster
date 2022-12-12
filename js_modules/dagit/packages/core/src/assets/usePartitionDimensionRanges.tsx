import React from 'react';

import {QueryPersistedStateConfig, useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {
  allPartitionsSpan,
  partitionsToText,
  textToPartitions,
} from '../partitions/SpanRepresentation';

import {placeholderDimensionRange} from './MultipartitioningSupport';
import {PartitionHealthData, PartitionHealthDimensionRange} from './usePartitionHealthData';

type DimensionQueryState = {
  name: string;
  rangeText: string | undefined;
};

const serializer: QueryPersistedStateConfig<DimensionQueryState[]> = {
  defaults: {},
  encode: (state) => Object.fromEntries(state.map((s) => [`${s.name}_range`, s.rangeText])),
  decode: (qs) =>
    Object.entries(qs)
      .filter(([key]) => key.endsWith('_range'))
      .map(([key, rangeText]) => ({name: key.replace(/_range$/, ''), rangeText})),
};

/**
 * This hook behaves like useState and manages the user's selected partition key
 * ranges on each partition dimension.
 *
 * Internally, this hook reads initial state from the query string and (optionally)
 * writes changes back to the query string using the compacted "spans" format.
 */
export const usePartitionDimensionRanges = (
  assetHealth: Pick<PartitionHealthData, 'dimensions'>,
  knownDimensionNames: string[] = [], // improves loading state if available
  modifyQueryString = true,
) => {
  const [query, setQuery] = useQueryPersistedState<DimensionQueryState[]>(serializer);
  const [local, setLocal] = React.useState<DimensionQueryState[]>([]);

  const knownDimensionNamesJSON = JSON.stringify(knownDimensionNames);
  const inflated = React.useMemo((): PartitionHealthDimensionRange[] => {
    if (!assetHealth) {
      return JSON.parse(knownDimensionNamesJSON).map(placeholderDimensionRange);
    }
    return assetHealth.dimensions.map((dimension) => {
      const saved =
        local.find((s) => s.name === dimension.name) ||
        query.find((s) => s.name === dimension.name);

      // Note: It's valid for the user to clear the range to "", so it's
      // important that we persist "" and specifically check for `undefined`
      // when filling in the default value (all keys)
      return {
        dimension,
        selected:
          saved?.rangeText !== undefined
            ? textToPartitions(saved.rangeText, dimension.partitionKeys)
            : dimension.partitionKeys,
      };
    });
  }, [query, local, assetHealth, knownDimensionNamesJSON]);

  const setInflated = React.useCallback(
    (ranges: PartitionHealthDimensionRange[]) => {
      const next = ranges.map((r) => {
        const rangeText = partitionsToText(r.selected, r.dimension.partitionKeys);
        return {
          name: r.dimension.name,
          rangeText: rangeText !== allPartitionsSpan(r.dimension) ? rangeText : undefined,
        };
      });
      if (modifyQueryString) {
        setQuery(next);
      } else {
        setLocal(next);
      }
    },
    [setQuery, modifyQueryString],
  );

  return [inflated, setInflated] as const;
};
