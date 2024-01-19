jest.useFakeTimers();

import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {act, render, waitFor} from '@testing-library/react';
import {GraphQLError} from 'graphql/error';
import React from 'react';

import {buildMockedAssetGraphLiveQuery} from './util';
import {AssetKey, AssetKeyInput, buildAssetKey} from '../../graphql/types';
import {getMockResultFn} from '../../testing/mocking';
import {
  AssetLiveDataProvider,
  BATCH_SIZE,
  SUBSCRIPTION_IDLE_POLL_RATE,
  _resetLastFetchedOrRequested,
  useAssetsLiveData,
} from '../AssetLiveDataProvider';

Object.defineProperty(document, 'visibilityState', {value: 'visible', writable: true});
Object.defineProperty(document, 'hidden', {value: false, writable: true});

afterEach(() => {
  _resetLastFetchedOrRequested();
});

function Test({
  mocks,
  hooks,
}: {
  mocks: MockedResponse[];
  hooks: {
    keys: AssetKeyInput[];
    hookResult: (data: ReturnType<typeof useAssetsLiveData>['liveDataByNode']) => void;
  }[];
}) {
  function Hook({
    keys,
    hookResult,
  }: {
    keys: AssetKeyInput[];
    hookResult: (data: ReturnType<typeof useAssetsLiveData>['liveDataByNode']) => void;
  }) {
    hookResult(useAssetsLiveData(keys).liveDataByNode);
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
    const mockedQuery = buildMockedAssetGraphLiveQuery(assetKeys);
    const mockedQuery2 = buildMockedAssetGraphLiveQuery(assetKeys);

    const resultFn = getMockResultFn(mockedQuery);
    const resultFn2 = getMockResultFn(mockedQuery2);

    const hookResult = jest.fn();
    const hookResult2 = jest.fn();

    const {rerender} = render(
      <Test mocks={[mockedQuery, mockedQuery2]} hooks={[{keys: assetKeys, hookResult}]} />,
    );

    // Initially an empty object
    expect(resultFn).toHaveBeenCalledTimes(0);
    expect(hookResult.mock.calls[0]!.value).toEqual(undefined);

    act(() => {
      jest.runOnlyPendingTimers();
    });

    expect(resultFn).toHaveBeenCalled();
    await waitFor(() => {
      expect(hookResult.mock.calls[1]!.value).not.toEqual({});
    });
    expect(resultFn2).not.toHaveBeenCalled();

    // Re-render with the same asset keys and expect the cache to be used this time.

    rerender(
      <Test
        mocks={[mockedQuery, mockedQuery2]}
        hooks={[{keys: assetKeys, hookResult: hookResult2}]}
      />,
    );

    // Initially an empty object
    expect(resultFn2).not.toHaveBeenCalled();
    expect(hookResult2.mock.calls[0][0]).toEqual({});
    act(() => {
      jest.runOnlyPendingTimers();
    });

    // Not called because we use the cache instead
    expect(resultFn2).not.toHaveBeenCalled();
    expect(hookResult2.mock.calls[1]).toEqual(hookResult.mock.calls[1]);

    await act(async () => {
      await Promise.resolve();
    });

    // We make a request this time so resultFn2 is called
    act(() => {
      jest.advanceTimersByTime(SUBSCRIPTION_IDLE_POLL_RATE + 1);
    });
    expect(resultFn2).toHaveBeenCalled();
    expect(hookResult2.mock.calls[1]).toEqual(hookResult.mock.calls[1]);
  });

  it('obeys document visibility', async () => {
    const assetKeys = [buildAssetKey({path: ['key1']})];
    const mockedQuery = buildMockedAssetGraphLiveQuery(assetKeys);
    const mockedQuery2 = buildMockedAssetGraphLiveQuery(assetKeys);

    const resultFn = getMockResultFn(mockedQuery);
    const resultFn2 = getMockResultFn(mockedQuery2);

    const hookResult = jest.fn();
    const hookResult2 = jest.fn();

    const {rerender} = render(
      <Test mocks={[mockedQuery, mockedQuery2]} hooks={[{keys: assetKeys, hookResult}]} />,
    );

    // Initially an empty object
    expect(resultFn).toHaveBeenCalledTimes(0);
    expect(hookResult.mock.calls[0]!.value).toEqual(undefined);

    act(() => {
      jest.runOnlyPendingTimers();
    });

    expect(resultFn).toHaveBeenCalled();
    expect(resultFn2).not.toHaveBeenCalled();

    // Re-render with the same asset keys and expect the cache to be used this time.

    rerender(
      <Test
        mocks={[mockedQuery, mockedQuery2]}
        hooks={[{keys: assetKeys, hookResult: hookResult2}]}
      />,
    );

    // Initially an empty object
    expect(resultFn2).not.toHaveBeenCalled();
    expect(hookResult2.mock.calls[0]!.value).toEqual(undefined);
    act(() => {
      jest.runOnlyPendingTimers();
    });

    // Not called because we use the cache instead
    expect(resultFn2).not.toHaveBeenCalled();
    expect(hookResult2.mock.calls[1]).toEqual(hookResult.mock.calls[1]);

    await act(async () => {
      await Promise.resolve();
    });

    act(() => {
      (document as any).visibilityState = 'hidden';
      document.dispatchEvent(new Event('visibilitychange'));
    });

    // Document isn't visible so we don't make a request
    act(() => {
      jest.advanceTimersByTime(SUBSCRIPTION_IDLE_POLL_RATE + 1);
    });
    expect(resultFn2).not.toHaveBeenCalled();

    act(() => {
      (document as any).visibilityState = 'visible';
      document.dispatchEvent(new Event('visibilitychange'));
    });

    // Document is now visible so we make the request
    await waitFor(() => {
      expect(resultFn2).toHaveBeenCalled();
    });
  });

  it('chunks asset requests', async () => {
    const assetKeys = [];
    for (let i = 0; i < 2 * BATCH_SIZE; i++) {
      assetKeys.push(buildAssetKey({path: [`key${i}`]}));
    }
    const chunk1 = assetKeys.slice(0, BATCH_SIZE);
    const chunk2 = assetKeys.slice(BATCH_SIZE, 2 * BATCH_SIZE);

    const mockedQuery = buildMockedAssetGraphLiveQuery(chunk1);
    const mockedQuery2 = buildMockedAssetGraphLiveQuery(chunk2);

    const resultFn = getMockResultFn(mockedQuery);
    const resultFn2 = getMockResultFn(mockedQuery2);

    const hookResult = jest.fn();

    render(<Test mocks={[mockedQuery, mockedQuery2]} hooks={[{keys: assetKeys, hookResult}]} />);

    // Initially an empty object
    expect(resultFn).not.toHaveBeenCalled();
    expect(hookResult.mock.calls[0][0]).toEqual({});

    act(() => {
      jest.runOnlyPendingTimers();
    });

    // Only the first batch is sent (No stacking).
    expect(resultFn).toHaveBeenCalled();
    expect(resultFn2).not.toHaveBeenCalled();

    act(() => {
      jest.runOnlyPendingTimers();
    });

    // Second chunk is fetched
    await waitFor(() => {
      expect(resultFn2).toHaveBeenCalled();
    });
  });

  it('batches asset requests from separate hooks', async () => {
    const hookResult = jest.fn();

    const assetKeys = [];
    for (let i = 0; i < 100; i++) {
      assetKeys.push(buildAssetKey({path: [`key${i}`]}));
    }
    const chunk1 = assetKeys.slice(0, BATCH_SIZE);
    const chunk2 = assetKeys.slice(BATCH_SIZE, 2 * BATCH_SIZE);

    const hook1Keys = assetKeys.slice(0, Math.floor((2 / 3) * BATCH_SIZE));
    const hook2Keys = assetKeys.slice(
      Math.floor((2 / 3) * BATCH_SIZE),
      Math.floor((4 / 3) * BATCH_SIZE),
    );
    const hook3Keys = assetKeys.slice(Math.floor((4 / 3) * BATCH_SIZE), 2 * BATCH_SIZE);

    const mockedQuery = buildMockedAssetGraphLiveQuery(chunk1);
    const mockedQuery2 = buildMockedAssetGraphLiveQuery(chunk2);

    const resultFn = getMockResultFn(mockedQuery);
    const resultFn2 = getMockResultFn(mockedQuery2);

    render(
      <Test
        mocks={[mockedQuery, mockedQuery2]}
        hooks={[
          {keys: hook1Keys, hookResult},
          {keys: hook2Keys, hookResult},
          {keys: hook3Keys, hookResult},
        ]}
      />,
    );
    act(() => {
      jest.runOnlyPendingTimers();
    });

    // Only the first batch is sent (No stacking).
    expect(resultFn).toHaveBeenCalled();
    expect(resultFn2).not.toHaveBeenCalled();

    await waitFor(() => {
      expect(resultFn2).toHaveBeenCalled();
    });
  });

  it('prioritizes assets which were never fetched over previously fetched assets', async () => {
    const hookResult = jest.fn();
    const assetKeys = [];
    for (let i = 0; i < 2 * BATCH_SIZE; i++) {
      assetKeys.push(buildAssetKey({path: [`key${i}`]}));
    }

    // First we fetch these specific keys
    const fetch1Keys = [assetKeys[0], assetKeys[2]] as AssetKey[];

    // Next we fetch all of the keys after waiting SUBSCRIPTION_IDLE_POLL_RATE
    // which would have made the previously fetched keys elgible for fetching again
    const firstPrioritizedFetchKeys = assetKeys
      .filter((key) => fetch1Keys.indexOf(key) === -1)
      .slice(0, BATCH_SIZE);

    // Next we fetch all of the keys not fetched in the previous batch with the originally fetched keys
    // at the end of the batch since they were previously fetched already
    const secondPrioritizedFetchKeys = assetKeys.filter(
      (key) => firstPrioritizedFetchKeys.indexOf(key) === -1 && fetch1Keys.indexOf(key) === -1,
    );

    secondPrioritizedFetchKeys.push(...fetch1Keys);

    const mockedQuery = buildMockedAssetGraphLiveQuery(fetch1Keys);
    const mockedQuery2 = buildMockedAssetGraphLiveQuery(firstPrioritizedFetchKeys);
    const mockedQuery3 = buildMockedAssetGraphLiveQuery(secondPrioritizedFetchKeys);

    const resultFn = getMockResultFn(mockedQuery);
    const resultFn2 = getMockResultFn(mockedQuery2);
    const resultFn3 = getMockResultFn(mockedQuery3);

    // First we fetch the keys from fetch1
    const {unmount} = render(
      <Test
        mocks={[mockedQuery, mockedQuery2, mockedQuery3]}
        hooks={[{keys: fetch1Keys, hookResult}]}
      />,
    );

    await waitFor(() => {
      expect(resultFn).toHaveBeenCalled();
    });
    await waitFor(() => {
      expect(hookResult.mock.calls[1]!.value).not.toEqual({});
    });
    expect(resultFn2).not.toHaveBeenCalled();
    expect(resultFn3).not.toHaveBeenCalled();

    act(() => {
      unmount();
    });

    act(() => {
      // Advance timers so that the previously fetched keys are eligible for fetching but make sure they're still not prioritized
      jest.advanceTimersByTime(2 * SUBSCRIPTION_IDLE_POLL_RATE);
    });

    // Now we request all of the asset keys and see that the first batch excludes the keys from fetch1 since they
    // were previously fetched.
    render(
      <Test
        mocks={[mockedQuery, mockedQuery2, mockedQuery3]}
        hooks={[{keys: assetKeys, hookResult}]}
      />,
    );

    await waitFor(() => {
      expect(resultFn2).toHaveBeenCalled();
      expect(resultFn3).not.toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(resultFn3).toHaveBeenCalled();
    });
  });

  it('Skips over asset keys that fail to fetch', async () => {
    const assetKeys = [buildAssetKey({path: ['key1']})];
    const mockedQuery = buildMockedAssetGraphLiveQuery(assetKeys, undefined, [
      new GraphQLError('500'),
    ]);
    const mockedQuery2 = buildMockedAssetGraphLiveQuery(assetKeys, undefined, [
      new GraphQLError('500'),
    ]);

    const resultFn = getMockResultFn(mockedQuery);
    const resultFn2 = getMockResultFn(mockedQuery2);

    const hookResult = jest.fn();
    const hookResult2 = jest.fn();

    const {rerender} = render(
      <Test mocks={[mockedQuery, mockedQuery2]} hooks={[{keys: assetKeys, hookResult}]} />,
    );

    // Initially an empty object
    expect(resultFn).toHaveBeenCalledTimes(0);
    expect(hookResult.mock.calls[0]!.value).toEqual(undefined);

    act(() => {
      jest.runOnlyPendingTimers();
    });

    expect(resultFn).toHaveBeenCalled();
    await waitFor(() => {
      expect(hookResult.mock.calls[1]!.value).not.toEqual({});
    });
    expect(resultFn2).not.toHaveBeenCalled();

    // Re-render with the same asset keys and expect no fetches to be made

    rerender(
      <Test
        mocks={[mockedQuery, mockedQuery2]}
        hooks={[{keys: assetKeys, hookResult: hookResult2}]}
      />,
    );

    // Initially an empty object
    expect(resultFn2).not.toHaveBeenCalled();
    expect(hookResult2.mock.calls[0][0]).toEqual({});
    act(() => {
      jest.runOnlyPendingTimers();
    });

    // Not called because they failed to fetch recently
    expect(resultFn2).not.toHaveBeenCalled();
    expect(hookResult2.mock.calls[1]).toEqual(hookResult.mock.calls[1]);

    await act(async () => {
      await Promise.resolve();
    });

    // After the poll interval we retry the previously failed assets
    act(() => {
      jest.advanceTimersByTime(SUBSCRIPTION_IDLE_POLL_RATE + 1);
    });
    expect(resultFn2).toHaveBeenCalled();
    expect(hookResult2.mock.calls[1]).toEqual(hookResult.mock.calls[1]);
  });
});
