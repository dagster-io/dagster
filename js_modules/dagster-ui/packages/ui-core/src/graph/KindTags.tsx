import * as React from 'react';

import {OpTags} from './OpTags';
import {DefinitionTag} from '../graphql/types';

export const isCanonicalStorageKindTag = (tag: DefinitionTag) => tag.key === 'dagster/storage_kind';

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
    <OpTags
      {...rest}
      tags={[
        {
          label: definition.computeKind,
          onClick: () => {
            window.requestAnimationFrame(() => document.dispatchEvent(new Event('show-kind-info')));
          },
        },
      ]}
    />
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
    <OpTags
      {...rest}
      tags={[
        {
          label: storageKind,
          onClick: () => {
            window.requestAnimationFrame(() => document.dispatchEvent(new Event('show-kind-info')));
          },
        },
      ]}
    />
  );
};
