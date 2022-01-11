import {NonIdealState} from '@dagster-io/ui';
import * as React from 'react';

export const AssetsEmptyState = ({prefixPath}: {prefixPath: string[]}) => (
  <NonIdealState
    icon="asset"
    title="Assets"
    description={
      <p>
        {prefixPath && prefixPath.length
          ? `There are no matching materialized assets with the specified asset key. `
          : `There are no known materialized assets. `}
        Any asset keys that have been specified with an <code>AssetMaterialization</code> during a
        pipeline run will appear here. See the{' '}
        <a href="https://docs.dagster.io/_apidocs/ops#dagster.AssetMaterialization">
          AssetMaterialization documentation
        </a>{' '}
        for more information.
      </p>
    }
  />
);
