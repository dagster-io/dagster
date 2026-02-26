import {render} from '@testing-library/react';
import {useLayoutEffect, useMemo, useState} from 'react';

import {DeferredCallbackRegistry} from '../DeferredCallbackRegistry';

// Define a test callback interface
interface TestCallbacks extends Record<string, (...args: any[]) => any> {
  onChange: (value: string) => void;
  onError: (error: Error) => void;
  onComplete: () => void;
}

describe('DeferredCallbackRegistry', () => {
  let registry: DeferredCallbackRegistry<TestCallbacks>;
  let mockTargetFn: jest.Mock;

  beforeEach(() => {
    registry = new DeferredCallbackRegistry<TestCallbacks>();
    mockTargetFn = jest.fn();
  });

  describe('main usecase - allowing a parent component to subscribe to data from a child component without referencing the child component directly', () => {
    it('should allow child component to register a callback that the parent component can call', () => {
      const childDataMock = jest.fn();
      function ChildComponent({registry}: {registry: DeferredCallbackRegistry<TestCallbacks>}) {
        useLayoutEffect(() => {
          registry.register(({onChange}) => {
            onChange?.('fake-data');
          });
        }, [registry]);
        return <div>ChildComponent</div>;
      }
      function ParentComponent() {
        const registry = useMemo(() => new DeferredCallbackRegistry<TestCallbacks>(), []);

        const [childData, setChildData] = useState<string>('');
        useLayoutEffect(() => {
          registry.watch({onChange: setChildData});
        }, [registry]);

        childDataMock(childData);

        return <ChildComponent registry={registry} />;
      }

      render(<ParentComponent />);

      expect(childDataMock).toHaveBeenCalledWith('fake-data');
    });
  });

  describe('register', () => {
    it('should return false initially', () => {
      expect(registry.isRegistered()).toBe(false);
    });

    it('should register a target function', () => {
      registry.register(mockTargetFn);
      expect(registry.isRegistered()).toBe(true);
    });

    it('should execute queued callbacks when target function is registered', () => {
      const onChange = jest.fn();
      const onError = jest.fn();

      // Watch before registering (should queue)
      registry.watch({onChange, onError});

      expect(mockTargetFn).not.toHaveBeenCalled();

      // Register target function
      registry.register(mockTargetFn);

      // Should execute queued callbacks
      expect(mockTargetFn).toHaveBeenCalledTimes(1);
      expect(mockTargetFn).toHaveBeenCalledWith({
        onChange: expect.any(Function),
        onError: expect.any(Function),
      });
    });

    it('should execute multiple queued callbacks in order', () => {
      const callOrder: string[] = [];
      const onChange1 = jest.fn(() => {
        callOrder.push('onChange1');
      });
      const onChange2 = jest.fn(() => {
        callOrder.push('onChange2');
      });

      // Queue multiple callbacks
      registry.watch({onChange: onChange1});
      registry.watch({onChange: onChange2});

      mockTargetFn.mockImplementation(({onChange}) => {
        onChange();
      });

      registry.register(mockTargetFn);

      expect(mockTargetFn).toHaveBeenCalledTimes(2);
      expect(callOrder).toEqual(['onChange1', 'onChange2']);
    });
  });

  describe('watch', () => {
    it('should call target function immediately when already registered', () => {
      const onChange = jest.fn();

      registry.register(mockTargetFn);
      registry.watch({onChange});

      expect(mockTargetFn).toHaveBeenCalledTimes(1);
      expect(mockTargetFn).toHaveBeenCalledWith({
        onChange: expect.any(Function),
      });
    });

    it('should queue callbacks when target function is not registered', () => {
      const onChange = jest.fn();

      registry.watch({onChange});

      expect(mockTargetFn).not.toHaveBeenCalled();
      expect(registry.isRegistered()).toBe(false);
    });

    it('should handle partial callback objects', () => {
      const onChange = jest.fn();

      registry.register(mockTargetFn);
      registry.watch({onChange});

      expect(mockTargetFn).toHaveBeenCalledWith({
        onChange: expect.any(Function),
      });
    });

    it('should handle empty callback objects', () => {
      registry.register(mockTargetFn);
      registry.watch({});

      expect(mockTargetFn).toHaveBeenCalledWith({});
    });

    it('should return an unsubscribe function', () => {
      const onChange = jest.fn();

      const unsubscribe = registry.watch({onChange});

      expect(typeof unsubscribe).toBe('function');
    });

    it('should wrap callbacks to ensure unique references', () => {
      const onChange = jest.fn();

      registry.register(mockTargetFn);
      registry.watch({onChange});

      const calledCallback = mockTargetFn.mock.calls[0][0].onChange;
      expect(calledCallback).not.toBe(onChange); // Should be wrapped
      expect(typeof calledCallback).toBe('function');
    });
  });

  describe('unsubscribe functionality', () => {
    it('should remove listeners when unsubscribe is called', () => {
      const onChange = jest.fn();

      const unsubscribe = registry.watch({onChange});

      expect(registry.getListeners('onChange').size).toBe(1);

      unsubscribe();

      expect(registry.getListeners('onChange').size).toBe(0);
    });

    it('should handle multiple callbacks and unsubscribe correctly', () => {
      const onChange1 = jest.fn();
      const onChange2 = jest.fn();

      const unsubscribe1 = registry.watch({onChange: onChange1});
      const unsubscribe2 = registry.watch({onChange: onChange2});

      expect(registry.getListeners('onChange').size).toBe(2);

      unsubscribe1();
      expect(registry.getListeners('onChange').size).toBe(1);

      unsubscribe2();
      expect(registry.getListeners('onChange').size).toBe(0);
    });

    it('should handle unsubscribing multiple callback types', () => {
      const onChange = jest.fn();
      const onError = jest.fn();

      const unsubscribe = registry.watch({onChange, onError});

      expect(registry.getListeners('onChange').size).toBe(1);
      expect(registry.getListeners('onError').size).toBe(1);

      unsubscribe();

      expect(registry.getListeners('onChange').size).toBe(0);
      expect(registry.getListeners('onError').size).toBe(0);
    });
  });

  describe('getListeners', () => {
    it('should return empty set for callback type with no listeners', () => {
      const listeners = registry.getListeners('onChange');
      expect(listeners).toBeInstanceOf(Set);
      expect(listeners.size).toBe(0);
    });

    it('should return listeners for registered callbacks', () => {
      const onChange = jest.fn();

      registry.watch({onChange});

      const listeners = registry.getListeners('onChange');
      expect(listeners.size).toBe(1);
    });

    it('should return separate sets for different callback types', () => {
      const onChange = jest.fn();
      const onError = jest.fn();

      registry.watch({onChange, onError});

      const changeListeners = registry.getListeners('onChange');
      const errorListeners = registry.getListeners('onError');

      expect(changeListeners.size).toBe(1);
      expect(errorListeners.size).toBe(1);
      expect(changeListeners).not.toBe(errorListeners);
    });
  });

  describe('callback execution', () => {
    it('should execute wrapped callbacks with correct arguments', () => {
      const onChange = jest.fn();

      registry.register((callbacks) => {
        callbacks.onChange?.('test value');
      });

      registry.watch({onChange});

      expect(onChange).toHaveBeenCalledWith('test value');
    });

    it('should handle callback execution with multiple arguments', () => {
      const onError = jest.fn();

      registry.register((callbacks) => {
        const error = new Error('test error');
        callbacks.onError?.(error);
      });

      registry.watch({onError});

      expect(onError).toHaveBeenCalledWith(expect.any(Error));
      expect(onError.mock.calls[0][0].message).toBe('test error');
    });

    it('should handle callback execution with no arguments', () => {
      const onComplete = jest.fn();

      registry.register((callbacks) => {
        callbacks.onComplete?.();
      });

      registry.watch({onComplete});

      expect(onComplete).toHaveBeenCalledWith();
    });
  });

  describe('edge cases', () => {
    it('should handle registering target function multiple times', () => {
      const onChange = jest.fn();
      const mockTargetFn2 = jest.fn();

      registry.watch({onChange});

      registry.register(mockTargetFn);
      registry.register(mockTargetFn2);

      expect(mockTargetFn).toHaveBeenCalledTimes(1);
      expect(mockTargetFn2).not.toHaveBeenCalled(); // Queue is already empty
    });

    it('should handle null/undefined callbacks gracefully', () => {
      registry.register(mockTargetFn);

      // This should not throw
      registry.watch({
        onChange: undefined as any,
        onError: null as any,
      });

      expect(mockTargetFn).toHaveBeenCalledWith({});
    });

    it('should handle unsubscribing when no listeners exist', () => {
      const unsubscribe = registry.watch({});

      // Should not throw
      expect(() => unsubscribe()).not.toThrow();
    });
  });
});
