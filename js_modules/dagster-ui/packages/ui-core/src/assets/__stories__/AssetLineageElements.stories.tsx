import {useMemo} from 'react';

import {AssetLineageElements} from '../AssetLineageElements';
import {AssetLineageFragment} from '../types/AssetLineageElements.types';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Assets/Asset Lineage',
  component: AssetLineageElements,
};

export const FewParents = () => {
  const timestamp = useMemo(() => Date.now(), []);
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
  const timestamp = useMemo(() => Date.now(), []);
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
