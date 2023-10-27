import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {act, render, waitFor} from '@testing-library/react';
import React from 'react';

import {
  buildAssetKey,
  buildSubscription,
  buildMaterializationEvent,
  buildPipelineRunLogsSubscriptionSuccess,
} from '../../graphql/types';
import {
  ASSET_LIVE_RUN_LOGS_SUBSCRIPTION,
  AssetRunLogObserver,
  ObservedRunCallback,
  observeAssetEventsInRuns,
} from '../AssetRunLogObserver';
import {AssetLiveRunLogsSubscription} from '../types/AssetRunLogObserver.types';

const SubscriptionMock: MockedResponse<AssetLiveRunLogsSubscription> = {
  request: {
    query: ASSET_LIVE_RUN_LOGS_SUBSCRIPTION,
    variables: {runId: '12345'},
  },
  result: jest.fn(() => ({
    data: buildSubscription({
      pipelineRunLogs: buildPipelineRunLogsSubscriptionSuccess({
        messages: [
          buildMaterializationEvent({
            assetKey: buildAssetKey({path: ['hello']}),
          }),
        ],
      }),
    }),
  })),
};

describe('AssetRunLogObserver', () => {
  it('should open a subscription when a callback is added, send asset events and reference count correctly', async () => {
    jest.useFakeTimers();

    const received: any[] = [];
    const cb: ObservedRunCallback = (events) => {
      received.push(...events);
    };

    // Note: Putting htis in the mocks array twice allows us to
    // subscribe / unsubscribe / subscribe again.
    render(
      <MockedProvider mocks={[SubscriptionMock, SubscriptionMock]}>
        <AssetRunLogObserver />
      </MockedProvider>,
    );

    const observers: (() => void)[] = [];
    act(() => {
      observers.push(observeAssetEventsInRuns(['12345'], cb));
    });

    await waitFor(() => {
      expect(SubscriptionMock.result).toHaveBeenCalled();
      expect(received).toEqual([{assetKey: {__typename: 'AssetKey', path: ['hello']}}]);
    });

    (SubscriptionMock.result as jest.Mock).mockClear();

    // Add a second observer
    act(() => {
      observers.push(observeAssetEventsInRuns(['12345'], cb));
    });

    // Expect that it has not started another subscription
    await waitFor(() => {
      expect(SubscriptionMock.result).not.toHaveBeenCalled();
      expect(received).toEqual([{assetKey: {__typename: 'AssetKey', path: ['hello']}}]);
    });

    // Remove all the observers
    act(() => {
      observers.forEach((o) => o());
      jest.advanceTimersByTime(1200);
    });

    // Add a third observer. This time, it /should/ start another subscription
    // because the first one was entirely cleaned up when we removed the last
    // observer above.
    act(() => {
      observers.push(observeAssetEventsInRuns(['12345'], cb));
    });
    await waitFor(() => {
      expect(SubscriptionMock.result).toHaveBeenCalled();
      expect(received).toEqual([
        {assetKey: {__typename: 'AssetKey', path: ['hello']}},
        {assetKey: {__typename: 'AssetKey', path: ['hello']}},
      ]);
    });
  });
});
