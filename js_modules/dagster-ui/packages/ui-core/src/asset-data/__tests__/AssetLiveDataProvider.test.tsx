jest.useFakeTimers();

import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {render, act} from '@testing-library/react';
import React from 'react';

import {
  AssetGraphLiveQuery,
  AssetGraphLiveQueryVariables,
} from '../../asset-graph/types/useLiveDataForAssetKeys.types';
import {ASSETS_GRAPH_LIVE_QUERY} from '../../asset-graph/useLiveDataForAssetKeys';
import {
  AssetKeyInput,
  buildAssetKey,
  buildAssetLatestInfo,
  buildAssetNode,
} from '../../graphql/types';
import {buildQueryMock, getMockResultFn} from '../../testing/mocking';
import {AssetLiveDataProvider, useAssetNodeLiveData} from '../AssetLiveDataProvider';

Object.defineProperty(document, 'visibilityState', {value: 'visible', writable: true});
Object.defineProperty(document, 'hidden', {value: false, writable: true});

function buildMockedQuery(assetKeys: AssetKeyInput[]) {
  return buildQueryMock<AssetGraphLiveQuery, AssetGraphLiveQueryVariables>({
    query: ASSETS_GRAPH_LIVE_QUERY,
    variables: {
      // strip __typename
      assetKeys: assetKeys.map((assetKey) => ({path: assetKey.path})),
    },
    data: {
      assetNodes: assetKeys.map((assetKey) =>
        buildAssetNode({assetKey: buildAssetKey(assetKey), id: JSON.stringify(assetKey)}),
      ),
      assetsLatestInfo: assetKeys.map((assetKey) =>
        buildAssetLatestInfo({assetKey: buildAssetKey(assetKey), id: JSON.stringify(assetKey)}),
      ),
    },
  });
}

function Test({
  mocks,
  hooks,
}: {
  mocks: MockedResponse[];
  hooks: [
    {
      keys: AssetKeyInput[];
      hookResult: (data: ReturnType<typeof useAssetNodeLiveData>) => void;
    },
  ];
}) {
  function Hook({
    keys,
    hookResult,
  }: {
    keys: AssetKeyInput[];
    hookResult: (data: ReturnType<typeof useAssetNodeLiveData>) => void;
  }) {
    hookResult(useAssetNodeLiveData(keys));
    return <div />;
  }
  return (
    <MockedProvider mocks={mocks}>
      <AssetLiveDataProvider>
        {hooks.map(({keys, hookResult}, idx) => (
          <Hook key={idx} keys={keys} hookResult={hookResult} />
        ))}
      </AssetLiveDataProvider>
    </MockedProvider>
  );
}

describe('AssetLiveDataProvider', () => {
  it('provides asset data and uses cache if recently fetched', async () => {
    const assetKeys = [buildAssetKey({path: ['key1']})];
    const mockedQuery = buildMockedQuery(assetKeys);

    const resultFn = getMockResultFn(mockedQuery);

    const hookResult = jest.fn();

    const {rerender} = render(
      <Test mocks={[mockedQuery]} hooks={[{keys: assetKeys, hookResult}]} />,
    );

    // Initially an empty object
    expect(resultFn).toHaveBeenCalledTimes(0);
    expect(hookResult.mock.results[0]!.value).toEqual(undefined);

    act(() => {
      jest.runOnlyPendingTimers();
    });

    expect(resultFn).toHaveBeenCalledTimes(1);
    expect(hookResult.mock.results.length).toEqual(3);

    // Re-render with the same asset keys and expect the cache to be used this time.

    const assetKeys2 = [buildAssetKey({path: ['key1']})];
    const mockedQuery2 = buildMockedQuery(assetKeys);

    const resultFn2 = getMockResultFn(mockedQuery);
    const hookResult2 = jest.fn();

    rerender(<Test mocks={[mockedQuery2]} hooks={[{keys: assetKeys2, hookResult: hookResult2}]} />);

    // Initially an empty object
    expect(resultFn2).toHaveBeenCalledTimes(0);
    expect(hookResult2.mock.results[0]!.value).toEqual(undefined);
    act(() => {
      jest.runOnlyPendingTimers();
    });

    // Not called because we use the cache instead
    expect(resultFn2).not.toHaveBeenCalled();
    expect(hookResult2.mock.results[1]).toEqual(hookResult.mock.results[1]);

    // Commented out due to weird issue where Date.now is not advancing....
    // act(() => {
    //   jest.advanceTimersByTime(SUBSCRIPTION_IDLE_POLL_RATE + 1);
    // });
    // // Next setInterval fires and we fetch and use the mocked response
    // act(() => {
    //   jest.runOnlyPendingTimers();
    // });
    // expect(resultFn2).toHaveBeenCalled();
    // expect(hookResult2.mock.results[2]).toEqual(hookResult.mock.results[1]);
  });
});
