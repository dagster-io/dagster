import {CaptionMono, Tooltip} from '@dagster-io/ui-components';
import * as React from 'react';

import {OpTags} from './OpTags';
import {DefinitionTag} from '../graphql/types';
import {linkToAssetTableWithKindFilter} from '../search/links';

export const LEGACY_COMPUTE_KIND_TAG = 'kind';
export const COMPUTE_KIND_TAG = 'dagster/compute_kind';
export const STORAGE_KIND_TAG = 'dagster/storage_kind';

export const KIND_TAG_PREFIX = `dagster/kind/`;

// Older code servers may be using the legacy compute kind tag, so we need to check for both
export const isCanonicalComputeKindTag = (tag: Omit<DefinitionTag, '__typename'>) =>
  tag.key === COMPUTE_KIND_TAG || tag.key === LEGACY_COMPUTE_KIND_TAG;
export const isCanonicalStorageKindTag = (tag: Omit<DefinitionTag, '__typename'>) =>
  tag.key === STORAGE_KIND_TAG;

export const isKindTag = (tag: Omit<DefinitionTag, '__typename'>) =>
  tag.key.startsWith(KIND_TAG_PREFIX);
export const isSystemTag = isKindTag;
export const getKindFromTag = (tag: Omit<DefinitionTag, '__typename'>) =>
  tag.key.slice(KIND_TAG_PREFIX.length);

export const AssetKind = ({
  kind,
  style,
  linkToFilteredAssetsTable: shouldLink,
  onChangeAssetSelection,
  ...rest
}: {
  kind: string;
  style: React.CSSProperties;
  reduceColor?: boolean;
  reduceText?: boolean;
  reversed?: boolean;
  linkToFilteredAssetsTable?: boolean;
  onChangeAssetSelection?: (selection: string) => void;
}) => {
  return (
    <Tooltip
      content={
        onChangeAssetSelection ? (
          <>
            Filter to <CaptionMono>{kind}</CaptionMono> assets
          </>
        ) : shouldLink ? (
          <>
            View all <CaptionMono>{kind}</CaptionMono> assets
          </>
        ) : (
          <>
            Asset kind <CaptionMono>{kind}</CaptionMono>
          </>
        )
      }
      placement="bottom"
    >
      <OpTags
        style={{...style, cursor: shouldLink || onChangeAssetSelection ? 'pointer' : 'default'}}
        {...rest}
        tags={[
          {
            label: kind,
            onClick: onChangeAssetSelection
              ? () => {
                  onChangeAssetSelection?.(`kind:"${kind}"`);
                }
              : shouldLink
                ? () => {
                    window.location.href = linkToAssetTableWithKindFilter(kind);
                  }
                : () => {},
          },
        ]}
      />
    </Tooltip>
  );
};
