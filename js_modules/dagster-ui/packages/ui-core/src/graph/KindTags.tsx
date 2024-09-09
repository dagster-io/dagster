import {CaptionMono, Tooltip} from '@dagster-io/ui-components';
import * as React from 'react';

import {OpTags} from './OpTags';
import {DefinitionTag} from '../graphql/types';
import {linkToAssetTableWithKindFilter} from '../search/useGlobalSearch';
import {StaticSetFilter} from '../ui/BaseFilters/useStaticSetFilter';

export const LEGACY_COMPUTE_KIND_TAG = 'kind';
export const COMPUTE_KIND_TAG = 'dagster/compute_kind';
export const STORAGE_KIND_TAG = 'dagster/storage_kind';

export const KIND_TAG_PREFIX = `dagster/kind/`;

// Older code servers may be using the legacy compute kind tag, so we need to check for both
export const isCanonicalComputeKindTag = (tag: DefinitionTag) =>
  tag.key === COMPUTE_KIND_TAG || tag.key === LEGACY_COMPUTE_KIND_TAG;
export const isCanonicalStorageKindTag = (tag: DefinitionTag) => tag.key === STORAGE_KIND_TAG;

export const isKindTag = (tag: DefinitionTag) => tag.key.startsWith(KIND_TAG_PREFIX);
export const isSystemTag = isKindTag;
export const getKindFromTag = (tag: DefinitionTag) => tag.key.slice(KIND_TAG_PREFIX.length);

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
                    window.location.href = linkToAssetTableWithKindFilter(
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
  currentPageFilter?: StaticSetFilter<string>;
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
            onClick: () => {},
          },
        ]}
      />
    </Tooltip>
  );
};

export const AssetKind = ({
  kind,
  style,
  linkToFilteredAssetsTable: shouldLink,
  currentPageFilter,
  ...rest
}: {
  kind: string;
  style: React.CSSProperties;
  reduceColor?: boolean;
  reduceText?: boolean;
  reversed?: boolean;
  linkToFilteredAssetsTable?: boolean;
  currentPageFilter?: StaticSetFilter<string>;
}) => {
  return (
    <Tooltip
      content={
        currentPageFilter ? (
          <>
            Filter to <CaptionMono>{kind}</CaptionMono> assets
          </>
        ) : shouldLink ? (
          <>
            View all <CaptionMono>{kind}</CaptionMono> assets
          </>
        ) : (
          <>
            Storage kind <CaptionMono>{kind}</CaptionMono>
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
            label: kind,
            onClick: () => {},
          },
        ]}
      />
    </Tooltip>
  );
};
