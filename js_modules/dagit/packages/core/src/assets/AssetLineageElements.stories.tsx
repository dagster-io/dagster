import {Meta} from '@storybook/react/types-6-0';
import * as React from 'react';

import {AssetLineageElements} from './AssetLineageElements';
import {AssetLineageFragment} from './types/AssetLineageFragment';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'AssetLineageElements',
  component: AssetLineageElements,
} as Meta;

export const FewParents = () => {
  const timestamp = React.useMemo(() => Date.now(), []);
  const elements: AssetLineageFragment[] = [
    {
      __typename: 'AssetLineageInfo',
      partitions: ['2021-01-01'],
      assetKey: {
        __typename: 'AssetKey',
        path: ['tables', 'reduce'],
      },
    },
    {
      __typename: 'AssetLineageInfo',
      partitions: ['2021-01-01'],
      assetKey: {
        __typename: 'AssetKey',
        path: ['tables', 'reuse'],
      },
    },
    {
      __typename: 'AssetLineageInfo',
      partitions: ['2021-01-01'],
      assetKey: {
        __typename: 'AssetKey',
        path: ['tables', 'recycle'],
      },
    },
  ];

  return <AssetLineageElements elements={elements} timestamp={`${timestamp}`} />;
};

export const ManyParents = () => {
  const timestamp = React.useMemo(() => Date.now(), []);
  const elements: AssetLineageFragment[] = [];
  for (let ii = 0; ii < 20; ii++) {
    elements.push({
      __typename: 'AssetLineageInfo',
      partitions: ['2021-01-01'],
      assetKey: {
        __typename: 'AssetKey',
        path: ['tables', `step.${ii}`],
      },
    });
  }
  return <AssetLineageElements elements={elements} timestamp={`${timestamp}`} />;
};
