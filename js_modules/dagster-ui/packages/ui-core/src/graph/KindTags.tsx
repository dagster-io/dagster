import {CaptionMono, Tooltip} from '@dagster-io/ui-components';
import * as React from 'react';

import {OpTags} from './OpTags';
import {DefinitionTag, buildDefinitionTag} from '../graphql/types';

export const isCanonicalStorageKindTag = (tag: DefinitionTag) => tag.key === 'dagster/storage_kind';
export const buildStorageKindTag = (storageKind: string): DefinitionTag =>
  buildDefinitionTag({key: 'dagster/storage_kind', value: storageKind});

export const AssetComputeKindTag = ({
  definition,
  ...rest
}: {
  definition: {computeKind: string | null};
  style: React.CSSProperties;
  reduceColor?: boolean;
  reduceText?: boolean;
  reversed?: boolean;
}) => {
  if (!definition.computeKind) {
    return null;
  }
  return (
    <Tooltip
      content={
        <>
          Compute kind <CaptionMono>{definition.computeKind}</CaptionMono>
        </>
      }
      placement="bottom"
    >
      <OpTags
        {...rest}
        tags={[
          {
            label: definition.computeKind,
            onClick: () => {
              window.requestAnimationFrame(() =>
                document.dispatchEvent(new Event('show-kind-info')),
              );
            },
          },
        ]}
      />
    </Tooltip>
  );
};

export const AssetStorageKindTag = ({
  storageKind,
  ...rest
}: {
  storageKind: string;
  style: React.CSSProperties;
  reduceColor?: boolean;
  reduceText?: boolean;
  reversed?: boolean;
}) => {
  return (
    <Tooltip
      content={
        <>
          Storage kind <CaptionMono>{storageKind}</CaptionMono>
        </>
      }
      placement="bottom"
    >
      <OpTags
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
