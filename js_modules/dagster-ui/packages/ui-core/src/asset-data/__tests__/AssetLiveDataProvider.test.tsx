jest.useFakeTimers();

import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {act, render, waitFor} from '@testing-library/react';
import {GraphQLError} from 'graphql/error';

import {buildMockedAssetGraphLiveQuery} from './util';
import {AssetKey, AssetKeyInput, buildAssetKey} from '../../graphql/types';
import {LiveDataThreadID} from '../../live-data-provider/LiveDataThread';
import {BATCH_SIZE, SUBSCRIPTION_IDLE_POLL_RATE} from '../../live-data-provider/util';
import {getMockResultFn} from '../../testing/mocking';
import {useAssetsBaseData} from '../AssetBaseDataProvider';
import {AssetLiveDataProvider, __resetForJest} from '../AssetLiveDataProvider';

Object.defineProperty(document, 'visibilityState', {value: 'visible', writable: true});
Object.defineProperty(document, 'hidden', {value: false, writable: true});

afterEach(() => {
  __resetForJest();
});

let mockBatchParallelFetches = 1;
jest.mock('../../live-data-provider/util', () => {
  const actual = jest.requireActual('../../live-data-provider/util');
  return {
    ...actual,
    get BATCH_PARALLEL_FETCHES() {
      return mockBatchParallelFetches;
    },
  };
});

jest.mock('../../live-data-provider/LiveDataScheduler', () => {
  return {
    LiveDataScheduler: class LiveDataScheduler {
      scheduleStartFetchLoop(doStart: () => void) {
        doStart();
      }
      scheduleStopFetchLoop(doStop: () => void) {
        doStop();
      }
    },
  };
});

function Test({
  mocks,
  hooks,
}: {
  mocks: MockedResponse[];
  hooks: {
    keys: AssetKeyInput[];
    thread?: LiveDataThreadID;
    hookResult: (data: ReturnType<typeof useAssetsBaseData>['liveDataByNode']) => void;
  }[];
}) {
  function Hook({
    keys,
    thread,
    hookResult,
  }: {
    keys: AssetKeyInput[];
    thread?: LiveDataThreadID;
    hookResult: (data: ReturnType<typeof useAssetsBaseData>['liveDataByNode']) => void;
  }) {
    hookResult(useAssetsBaseData(keys, thread).liveDataByNode);
    return <div />;
  }
  return (
    <MockedProvider mocks={mocks}>
      <AssetLiveDataProvider>
        {hooks.map(({keys, thread, hookResult}, idx) => (
          <Hook key={idx} keys={keys} hookResult={hookResult} thread={thread} />
        ))}
      </AssetLiveDataProvider>
    </MockedProvider>
  );
}

describe('AssetLiveDataProvider', () => {
  it('provides asset data and uses cache if recently fetched', async () => {
    const assetKeys = [buildAssetKey({path: ['key1']})];
    const [mockedQuery, mockedFreshnessQuery] = buildMockedAssetGraphLiveQuery(assetKeys);
    const [mockedQuery2, mockedFreshnessQuery2] = buildMockedAssetGraphLiveQuery(assetKeys);

    const resultFn = getMockResultFn(mockedQuery);
    const resultFn2 = getMockResultFn(mockedQuery2);

    const hookResult = jest.fn();
    const hookResult2 = jest.fn();

    const {rerender} = render(
      <Test
        mocks={[mockedQuery, mockedFreshnessQuery, mockedQuery2, mockedFreshnessQuery2]}
        hooks={[{keys: assetKeys, hookResult}]}
      />,
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
    const [mockedQuery, mockedFreshnessQuery] = buildMockedAssetGraphLiveQuery(assetKeys);
    const [mockedQuery2, mockedFreshnessQuery2] = buildMockedAssetGraphLiveQuery(assetKeys);

    const resultFn = getMockResultFn(mockedQuery);
    const resultFn2 = getMockResultFn(mockedQuery2);

    const hookResult = jest.fn();
    const hookResult2 = jest.fn();

    const {rerender} = render(
      <Test
        mocks={[mockedQuery, mockedFreshnessQuery, mockedQuery2, mockedFreshnessQuery2]}
        hooks={[{keys: assetKeys, hookResult}]}
      />,
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
        mocks={[mockedQuery, mockedFreshnessQuery, mockedQuery2, mockedFreshnessQuery2]}
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

    const [mockedQuery, mockedFreshnessQuery] = buildMockedAssetGraphLiveQuery(chunk1);
    const [mockedQuery2, mockedFreshnessQuery2] = buildMockedAssetGraphLiveQuery(chunk2);

    const resultFn = getMockResultFn(mockedQuery);
    const resultFn2 = getMockResultFn(mockedQuery2);

    const hookResult = jest.fn();

    render(
      <Test
        mocks={[mockedQuery, mockedFreshnessQuery, mockedQuery2, mockedFreshnessQuery2]}
        hooks={[{keys: assetKeys, hookResult}]}
      />,
    );

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

    const [mockedQuery, mockedFreshnessQuery] = buildMockedAssetGraphLiveQuery(chunk1);
    const [mockedQuery2, mockedFreshnessQuery2] = buildMockedAssetGraphLiveQuery(chunk2);

    const resultFn = getMockResultFn(mockedQuery);
    const resultFn2 = getMockResultFn(mockedQuery2);

    render(
      <Test
        mocks={[mockedQuery, mockedFreshnessQuery, mockedQuery2, mockedFreshnessQuery2]}
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

    const [mockedQuery, mockedFreshnessQuery] = buildMockedAssetGraphLiveQuery(fetch1Keys);
    const [mockedQuery2, mockedFreshnessQuery2] =
      buildMockedAssetGraphLiveQuery(firstPrioritizedFetchKeys);
    const [mockedQuery3, mockedFreshnessQuery3] = buildMockedAssetGraphLiveQuery(
      secondPrioritizedFetchKeys,
    );

    const resultFn = getMockResultFn(mockedQuery);
    const resultFn2 = getMockResultFn(mockedQuery2);
    const resultFn3 = getMockResultFn(mockedQuery3);

    // First we fetch the keys from fetch1
    const {unmount} = render(
      <Test
        mocks={[
          mockedQuery,
          mockedFreshnessQuery,
          mockedQuery2,
          mockedFreshnessQuery2,
          mockedQuery3,
          mockedFreshnessQuery3,
        ]}
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
        mocks={[
          mockedQuery,
          mockedFreshnessQuery,
          mockedQuery2,
          mockedFreshnessQuery2,
          mockedQuery3,
          mockedFreshnessQuery3,
        ]}
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
    const [mockedQuery, mockedFreshnessQuery] = buildMockedAssetGraphLiveQuery(
      assetKeys,
      undefined,
      [new GraphQLError('500')],
    );
    const [mockedQuery2, mockedFreshnessQuery2] = buildMockedAssetGraphLiveQuery(
      assetKeys,
      undefined,
      [new GraphQLError('500')],
    );

    const resultFn = getMockResultFn(mockedQuery);
    const resultFn2 = getMockResultFn(mockedQuery2);

    const hookResult = jest.fn();
    const hookResult2 = jest.fn();

    const {rerender} = render(
      <Test
        mocks={[mockedQuery, mockedFreshnessQuery, mockedQuery2, mockedFreshnessQuery2]}
        hooks={[{keys: assetKeys, hookResult}]}
      />,
    );

    // Initially an empty object
    expect(resultFn).toHaveBeenCalledTimes(0);
    expect(hookResult.mock.calls[0]!.value).toEqual(undefined);

    act(() => {
      jest.runOnlyPendingTimers();
    });

    expect(resultFn).toHaveBeenCalled();
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

  it('Has multiple threads', async () => {
    const assetKeys = [buildAssetKey({path: ['key1']})];
    const assetKeys2 = [buildAssetKey({path: ['key2']})];
    const [mockedQuery, mockedFreshnessQuery] = buildMockedAssetGraphLiveQuery(assetKeys);
    const [mockedQuery2, mockedFreshnessQuery2] = buildMockedAssetGraphLiveQuery(assetKeys2);

    const resultFn = getMockResultFn(mockedQuery);
    const resultFn2 = getMockResultFn(mockedQuery2);

    const hookResult = jest.fn();
    const hookResult2 = jest.fn();

    render(
      <Test
        mocks={[mockedQuery, mockedFreshnessQuery, mockedQuery2, mockedFreshnessQuery2]}
        hooks={[
          {keys: assetKeys, thread: 'default', hookResult},
          {keys: assetKeys2, thread: 'context-menu', hookResult: hookResult2},
        ]}
      />,
    );

    // Initially an empty object
    expect(resultFn).toHaveBeenCalledTimes(0);
    expect(resultFn2).toHaveBeenCalledTimes(0);
    expect(hookResult.mock.calls[0]!.value).toEqual(undefined);
    expect(hookResult2.mock.calls[0]!.value).toEqual(undefined);

    act(() => {
      jest.runOnlyPendingTimers();
    });

    expect(resultFn).toHaveBeenCalled();
    expect(resultFn2).toHaveBeenCalled();
    await waitFor(() => {
      expect(hookResult.mock.calls[1]!.value).not.toEqual({});
      expect(hookResult2.mock.calls[1]!.value).not.toEqual({});
    });
  });

  it('Supports parallel fetches', async () => {
    mockBatchParallelFetches = 2;
    jest.resetModules();

    const assetKeys = [];
    for (let i = 0; i < 4 * BATCH_SIZE; i++) {
      assetKeys.push(buildAssetKey({path: [`key${i}`]}));
    }
    const chunk1 = assetKeys.slice(0, BATCH_SIZE);
    const chunk2 = assetKeys.slice(BATCH_SIZE, 2 * BATCH_SIZE);
    const chunk3 = assetKeys.slice(2 * BATCH_SIZE, 3 * BATCH_SIZE);
    const chunk4 = assetKeys.slice(3 * BATCH_SIZE, 4 * BATCH_SIZE);

    const [mockedQuery, mockedFreshnessQuery] = buildMockedAssetGraphLiveQuery(chunk1);
    const [mockedQuery2, mockedFreshnessQuery2] = buildMockedAssetGraphLiveQuery(chunk2);
    const [mockedQuery3, mockedFreshnessQuery3] = buildMockedAssetGraphLiveQuery(chunk3);
    const [mockedQuery4, mockedFreshnessQuery4] = buildMockedAssetGraphLiveQuery(chunk4);

    const resultFn = getMockResultFn(mockedQuery);
    const resultFn2 = getMockResultFn(mockedQuery2);
    const resultFn3 = getMockResultFn(mockedQuery3);
    const resultFn4 = getMockResultFn(mockedQuery4);

    const hookResult = jest.fn();

    render(
      <Test
        mocks={[
          mockedQuery,
          mockedFreshnessQuery,
          mockedQuery2,
          mockedFreshnessQuery2,
          mockedQuery3,
          mockedFreshnessQuery3,
          mockedQuery4,
          mockedFreshnessQuery4,
        ]}
        hooks={[{keys: assetKeys, hookResult}]}
      />,
    );

    // Initially an empty object
    expect(resultFn).not.toHaveBeenCalled();
    expect(hookResult.mock.calls[0][0]).toEqual({});

    act(() => {
      jest.runOnlyPendingTimers();
    });

    // 2 batches are sent .
    expect(resultFn).toHaveBeenCalled();
    expect(resultFn2).toHaveBeenCalled();
    expect(resultFn4).not.toHaveBeenCalled();
    expect(resultFn3).not.toHaveBeenCalled();

    act(() => {
      jest.runOnlyPendingTimers();
    });

    // Second chunk is fetched
    await waitFor(() => {
      expect(resultFn3).toHaveBeenCalled();
      expect(resultFn4).toHaveBeenCalled();
    });
  });
});
