import {CaptionMono, Tooltip} from '@dagster-io/ui-components';
import * as React from 'react';

import {OpTags} from './OpTags';
import {DefinitionTag, buildDefinitionTag} from '../graphql/types';
import {
  linkToAssetTableWithComputeKindFilter,
  linkToAssetTableWithStorageKindFilter,
} from '../search/useGlobalSearch';
import {StaticSetFilter} from '../ui/BaseFilters/useStaticSetFilter';

export const LEGACY_COMPUTE_KIND_TAG = 'kind';
export const COMPUTE_KIND_TAG = 'dagster/compute_kind';
export const STORAGE_KIND_TAG = 'dagster/storage_kind';

export const HIDDEN_TAG_PREFIX = '.dagster/';

// Older code servers may be using the legacy compute kind tag, so we need to check for both
export const isCanonicalComputeKindTag = (tag: DefinitionTag) =>
  tag.key === COMPUTE_KIND_TAG || tag.key === LEGACY_COMPUTE_KIND_TAG;
export const isCanonicalStorageKindTag = (tag: DefinitionTag) => tag.key === STORAGE_KIND_TAG;
export const buildStorageKindTag = (storageKind: string): DefinitionTag =>
  buildDefinitionTag({key: 'dagster/storage_kind', value: storageKind});

export const AssetComputeKindTag = ({
  definition,
  linkToFilteredAssetsTable: shouldLink,
  style,
  currentPageFilter,
  ...rest
}: {
  definition: {computeKind: string | null};
  style: React.CSSProperties;
  reduceColor?: boolean;
  reduceText?: boolean;
  reversed?: boolean;
  linkToFilteredAssetsTable?: boolean;
  currentPageFilter?: StaticSetFilter<string>;
}) => {
  if (!definition.computeKind) {
    return null;
  }
  return (
    <Tooltip
      content={
        currentPageFilter ? (
          <>
            Filter to <CaptionMono>{definition.computeKind}</CaptionMono> assets
          </>
        ) : shouldLink ? (
          <>
            View all <CaptionMono>{definition.computeKind}</CaptionMono> assets
          </>
        ) : (
          <>
            Compute kind <CaptionMono>{definition.computeKind}</CaptionMono>
          </>
        )
      }
      placement="bottom"
    >
      <OpTags
        {...rest}
        style={{...style, cursor: shouldLink || currentPageFilter ? 'pointer' : 'default'}}
        tags={[
          {
            label: definition.computeKind,
            onClick:
              currentPageFilter && definition.computeKind
                ? () => currentPageFilter.setState(new Set([definition.computeKind || '']))
                : shouldLink
                ? () => {
                    window.location.href = linkToAssetTableWithComputeKindFilter(
                      definition.computeKind || '',
                    );
                  }
                : () => {},
          },
        ]}
      />
    </Tooltip>
  );
};

export const AssetStorageKindTag = ({
  storageKind,
  style,
  linkToFilteredAssetsTable: shouldLink,
  currentPageFilter,
  ...rest
}: {
  storageKind: string;
  style: React.CSSProperties;
  reduceColor?: boolean;
  reduceText?: boolean;
  reversed?: boolean;
  linkToFilteredAssetsTable?: boolean;
  currentPageFilter?: StaticSetFilter<DefinitionTag>;
}) => {
  return (
    <Tooltip
      content={
        currentPageFilter ? (
          <>
            Filter to <CaptionMono>{storageKind}</CaptionMono> assets
          </>
        ) : shouldLink ? (
          <>
            View all <CaptionMono>{storageKind}</CaptionMono> assets
          </>
        ) : (
          <>
            Storage kind <CaptionMono>{storageKind}</CaptionMono>
          </>
        )
      }
      placement="bottom"
    >
      <OpTags
        style={{...style, cursor: shouldLink || currentPageFilter ? 'pointer' : 'default'}}
        {...rest}
        tags={[
          {
            label: storageKind,
            onClick: currentPageFilter
              ? () => currentPageFilter.setState(new Set([buildStorageKindTag(storageKind)]))
              : shouldLink
              ? () => {
                  window.location.href = linkToAssetTableWithStorageKindFilter(storageKind);
                }
              : () => {},
          },
        ]}
      />
    </Tooltip>
  );
};
