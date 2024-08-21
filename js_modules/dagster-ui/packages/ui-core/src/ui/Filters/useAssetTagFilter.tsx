import isEqual from 'lodash/isEqual';
import memoize from 'lodash/memoize';
import {useMemo} from 'react';
import {HIDDEN_TAG_PREFIX} from 'shared/graph/KindTags';

import {DefinitionTag} from '../../graphql/types';
import {TruncatedTextWithFullTextOnHover} from '../../nav/getLeftNavItemsForOption';
import {StaticBaseConfig, useStaticSetFilter} from '../BaseFilters/useStaticSetFilter';
import {buildTagString} from '../tagAsString';

const emptyArray: any[] = [];

export const useAssetTagFilter = ({
  allAssetTags,
  tags,
  setTags,
}: {
  allAssetTags: DefinitionTag[];
  tags?: null | DefinitionTag[];
  setTags?: null | ((s: DefinitionTag[]) => void);
}) => {
  const memoizedState = useMemo(() => tags?.map(buildDefinitionTag), [tags]);
  return useStaticSetFilter<DefinitionTag>({
    ...BaseConfig,
    allValues: useMemo(
      () =>
        allAssetTags.map((value) => ({
          value,
          match: [value.key + ':' + value.value],
        })),
      [allAssetTags],
    ),
    menuWidth: '300px',
    state: memoizedState ?? emptyArray,
    onStateChanged: (values) => {
      setTags?.(Array.from(values));
    },
    canSelectAll: false,
  });
};

export const buildDefinitionTag = memoize(
  (tag: DefinitionTag) => {
    return tag;
  },
  (tag) => [tag.key, tag.value].join('|@-@|'),
);

export function useAssetTagsForAssets(
  assets: {definition?: {tags?: DefinitionTag[] | null} | null}[],
): DefinitionTag[] {
  return useMemo(
    () =>
      Array.from(
        new Set(
          assets
            .flatMap(
              (a) =>
                a.definition?.tags
                  ?.filter((tag) => !tag.key.startsWith(HIDDEN_TAG_PREFIX))
                  .map((tag) => JSON.stringify(tag)) ?? [],
            )
            .filter((o) => o),
        ),
      )
        .map((jsonTag) => buildDefinitionTag(JSON.parse(jsonTag)))
        .sort((a, b) =>
          // Sort by key then by value
          a.key.localeCompare(b.key) === 0
            ? a.value.localeCompare(b.value)
            : a.key.localeCompare(b.key),
        ),
    [assets],
  );
}

export function doesFilterArrayMatchValueArray<T, V>(
  filterArray: T[],
  valueArray: V[],
  isMatch: (value1: T, value2: V) => boolean = (val1, val2) => {
    return isEqual(val1, val2);
  },
) {
  if (filterArray.length && !valueArray.length) {
    return false;
  }
  return !filterArray.some(
    (filterTag) =>
      // If no asset tags match this filter tag return true
      !valueArray.find((value) => isMatch(filterTag, value)),
  );
}

export const BaseConfig: StaticBaseConfig<DefinitionTag> = {
  name: 'Tag',
  icon: 'tag',
  renderLabel: ({value}: {value: DefinitionTag}) => {
    return (
      <TruncatedTextWithFullTextOnHover
        text={buildTagString({key: value.key, value: value.value})}
      />
    );
  },
  getStringValue: ({value, key}: DefinitionTag) => `${key}: ${value}`,
  matchType: 'all-of',
};
