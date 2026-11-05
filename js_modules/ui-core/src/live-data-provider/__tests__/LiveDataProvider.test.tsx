import {renderHook} from '@testing-library/react';

import {useLiveData} from '../LiveDataProvider';
import {LiveDataThreadManager} from '../LiveDataThreadManager';

type Data = {value: number};

const KEYS = ['a', 'b'];

function buildManager() {
  const manager = new LiveDataThreadManager<Data>(jest.fn().mockResolvedValue({}), 10, 1);
  const unsubscribe = jest.fn();
  const subscribe = jest.spyOn(manager, 'subscribe').mockImplementation(() => unsubscribe);
  return {manager, subscribe, unsubscribe};
}

describe('useLiveData', () => {
  it('does not subscribe while skipped and subscribes when skip flips to false', () => {
    const {manager, subscribe, unsubscribe} = buildManager();

    const {rerender} = renderHook(({skip}) => useLiveData(KEYS, manager, 'default', skip), {
      initialProps: {skip: true},
    });
    expect(subscribe).not.toHaveBeenCalled();

    rerender({skip: false});
    expect(subscribe).toHaveBeenCalledTimes(KEYS.length);
    expect(subscribe.mock.calls.map(([key]) => key)).toEqual(KEYS);

    rerender({skip: true});
    expect(unsubscribe).toHaveBeenCalledTimes(KEYS.length);
    expect(subscribe).toHaveBeenCalledTimes(KEYS.length);
  });

  it('clears data when skip flips to true', () => {
    const {manager, subscribe} = buildManager();
    subscribe.mockImplementation((key, listener) => {
      listener(key, {value: 1});
      return () => {};
    });
    jest.spyOn(window, 'requestAnimationFrame').mockImplementation((cb) => {
      cb(0);
      return 0;
    });

    const {result, rerender} = renderHook(({skip}) => useLiveData(KEYS, manager, 'default', skip), {
      initialProps: {skip: false},
    });
    expect(Object.keys(result.current.liveDataByNode)).toEqual(KEYS);

    rerender({skip: true});
    expect(result.current.liveDataByNode).toEqual({});
  });
});
