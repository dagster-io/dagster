/* eslint-disable @typescript-eslint/no-require-imports */
import {act, renderHook} from '@testing-library/react';
import {FeatureFlag} from 'shared/app/FeatureFlags.oss';

// Immediately import to force the mock constructor to file
import '../../hooks/useStateWithStorage';

// We're using isolateModules but we want to enforce the reference to React stays the same otherwise testing-library will fail
// https://github.com/jestjs/jest/issues/11471
jest.mock('react', () => jest.requireActual('react'));

// eslint-disable-next-line no-var
var mockGetJSONForKey: jest.Mock;

jest.mock('../../hooks/useStateWithStorage', () => {
  if (!mockGetJSONForKey) {
    mockGetJSONForKey = jest.fn(() => {});
  }
  return {
    getJSONForKey: mockGetJSONForKey,
  };
});

describe('Feature Flags with In-Memory Cache and BroadcastChannel', () => {
  const mockBroadcastChannel: any = new global.BroadcastChannel('feature-flags');

  let mockBroadcastChannelInstance: any;

  beforeEach(() => {
    localStorage.clear();
    mockGetJSONForKey.mockClear();

    mockBroadcastChannelInstance = (global as any).BroadcastChannel.prototype;
    mockBroadcastChannelInstance.listeners = [];
  });

  it('should migrate old array format to new object format', () => {
    jest.isolateModules(() => {
      const oldFlags = [FeatureFlag.__TestFlagDefaultTrue];
      mockGetJSONForKey.mockReturnValue(oldFlags);

      const {getFeatureFlags} = require('../Flags');

      expect(getFeatureFlags()[FeatureFlag.__TestFlagDefaultTrue]).toBe(true);
      expect(localStorage.getItem('DAGSTER_FLAGS')).toBe(
        JSON.stringify({[FeatureFlag.__TestFlagDefaultTrue]: true}),
      );
      expect(Array.isArray(getFeatureFlags())).toBe(false);
    });
  });

  it('should return default value for unset flags', () => {
    jest.isolateModules(() => {
      const {featureEnabled, getFeatureFlags} = require('../Flags');

      const isEnabled = featureEnabled(FeatureFlag.__TestFlagDefaultTrue);
      expect(isEnabled).toBe(true);

      const isEnabled2 = featureEnabled(FeatureFlag.__TestFlagDefaultFalse);
      expect(isEnabled2).toBe(false);

      expect(getFeatureFlags()[FeatureFlag.__TestFlagDefaultFalse]).toBe(false);
      expect(getFeatureFlags()[FeatureFlag.__TestFlagDefaultTrue]).toBe(true);
      expect(getFeatureFlags()[FeatureFlag.__TestFlagDefaultNone]).toBe(undefined);
    });
  });

  it('should react to changes in feature flags across contexts', () => {
    jest.isolateModules(() => {
      const {useFeatureFlags, setFeatureFlags} = require('../Flags');
      const {result} = renderHook(() => useFeatureFlags());

      expect(result.current[FeatureFlag.__TestFlagDefaultNone]).toBe(false); // Default

      act(() => {
        setFeatureFlags({[FeatureFlag.__TestFlagDefaultNone]: true});
      });

      expect(result.current[FeatureFlag.__TestFlagDefaultNone]).toBe(true);

      act(() => {
        setFeatureFlags({[FeatureFlag.__TestFlagDefaultNone]: false});
        mockBroadcastChannel.postMessage('updated');
      });

      expect(result.current[FeatureFlag.__TestFlagDefaultNone]).toBe(false);
    });
  });

  it('should handle unset state correctly', () => {
    jest.isolateModules(() => {
      const {useFeatureFlags, setFeatureFlags} = require('../Flags');
      const {result} = renderHook(() => useFeatureFlags());

      expect(result.current[FeatureFlag.__TestFlagDefaultNone]).toBe(false); // Default

      act(() => {
        setFeatureFlags({[FeatureFlag.__TestFlagDefaultNone]: true});
        mockBroadcastChannel.postMessage('updated');
      });
      expect(result.current[FeatureFlag.__TestFlagDefaultNone]).toBe(true);

      act(() => {
        setFeatureFlags({[FeatureFlag.__TestFlagDefaultNone]: false});
        mockBroadcastChannel.postMessage('updated');
      });
      expect(result.current[FeatureFlag.__TestFlagDefaultNone]).toBe(false);

      act(() => {
        setFeatureFlags({});
        mockBroadcastChannel.postMessage('updated');
      });
      expect(result.current[FeatureFlag.__TestFlagDefaultNone]).toBe(false); // Default
    });
  });

  it('should update in-memory cache without reading localStorage on each access', () => {
    jest.isolateModules(() => {
      const {featureEnabled, setFeatureFlags, getFeatureFlags} = require('../Flags');
      expect(mockGetJSONForKey).toHaveBeenCalledTimes(1);

      expect(featureEnabled(FeatureFlag.__TestFlagDefaultNone)).toBe(false);

      act(() => {
        setFeatureFlags({[FeatureFlag.__TestFlagDefaultNone]: true});
        mockBroadcastChannel.postMessage('updated');
      });

      expect(getFeatureFlags()[FeatureFlag.__TestFlagDefaultNone]).toBe(true);
      expect(featureEnabled(FeatureFlag.__TestFlagDefaultNone)).toBe(true);
      expect(mockGetJSONForKey).toHaveBeenCalledTimes(1); // Still only 1, from initialization
    });
  });
});
