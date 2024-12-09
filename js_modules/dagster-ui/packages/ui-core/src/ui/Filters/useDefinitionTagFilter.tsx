import memoize from 'lodash/memoize';
import {useCallback, useMemo} from 'react';

import {isKindTag} from '../../graph/KindTags';
import {DefinitionTag} from '../../graphql/types';
import {useQueryPersistedState} from '../../hooks/useQueryPersistedState';
import {TruncatedTextWithFullTextOnHover} from '../../nav/getLeftNavItemsForOption';
import {StaticBaseConfig, useStaticSetFilter} from '../BaseFilters/useStaticSetFilter';
import {buildTagString} from '../tagAsString';

const emptyArray: any[] = [];

export type Tag = Omit<DefinitionTag, '__typename'>;

export const useDefinitionTagFilter = ({
  allTags,
  tags,
  setTags,
}: {
  allTags: Tag[];
  tags: null | Tag[];
  setTags: null | ((s: Tag[]) => void);
}) => {
  const memoizedState = useMemo(() => tags?.map(buildDefinitionTag), [tags]);
  return useStaticSetFilter<Tag>({
    ...BaseConfig,
    allValues: useMemo(
      () =>
        allTags.map((value) => ({
          value,
          match: [value.key + ':' + value.value],
        })),
      [allTags],
    ),
    menuWidth: '300px',
    state: memoizedState ?? emptyArray,
    onStateChanged: (values) => {
      const nextTags = Array.from(values);
      setTags?.(nextTags);
    },
    canSelectAll: false,
  });
};

export const useDefinitionTagFilterWithManagedState = ({allTags}: {allTags: Tag[]}) => {
  const [tags, setTags] = useQueryPersistedState<Tag[]>({queryKey: 'tags'});

  return useDefinitionTagFilter({
    allTags,
    tags,
    setTags,
  });
};

export const buildDefinitionTag = memoize(
  (tag: Tag) => {
    return tag;
  },
  (tag) => [tag.key, tag.value].join('|@-@|'),
);

export function useTagsForAssets(assets: {definition?: {tags?: Tag[] | null} | null}[]) {
  return useTagsForObjects(
    assets,
    useCallback(
      (asset: (typeof assets)[0]) => asset.definition?.tags?.filter((tag) => !isKindTag(tag)) ?? [],
      [],
    ),
  );
}

export function useTagsForObjects<T>(
  objects: T[],
  getTags: (obj: T) => Omit<DefinitionTag, '__typename'>[],
) {
  return useMemo(
    () =>
      Array.from(
        new Set(
          objects
            .flatMap((a) => getTags(a).map((tag) => JSON.stringify(tag)) ?? [])
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
    [objects, getTags],
  );
}

export const BaseConfig: StaticBaseConfig<Tag> = {
  name: 'Tag',
  icon: 'tag',
  renderLabel: ({value}) => {
    return (
      <TruncatedTextWithFullTextOnHover
        text={buildTagString({key: value.key, value: value.value})}
      />
    );
  },
  getStringValue: ({value, key}) => `${key}: ${value}`,
  matchType: 'all-of',
};
