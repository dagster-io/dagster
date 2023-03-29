import {IconName} from '@dagster-io/ui';
import React from 'react';

import {Filter} from '../useFilter';

class TestFilter extends Filter<number, number> {
  constructor(name: string, icon: IconName, state: number) {
    super(name, icon, state);
  }

  public isActive(): boolean {
    return this.getState() > 0;
  }

  public renderActiveFilterState(): JSX.Element {
    return this.isActive() ? <div>Active</div> : <div>Inactive</div>;
  }

  public getResults(query: string): {label: JSX.Element; key: string; value: number}[] {
    return [{label: <>Test Result {query}</>, key: 'test', value: this.getState()}];
  }

  public onSelect(selectArg: {
    value: number;
    close: () => void;
    createPortal: (element: JSX.Element) => () => void;
  }): void {
    this.setState(selectArg.value);
  }
}

describe('Filter', () => {
  let testFilter: TestFilter;

  beforeEach(() => {
    testFilter = new TestFilter('Test Filter', 'asset', 0);
  });

  test('constructor sets initial state', () => {
    expect(testFilter.getState()).toBe(0);
  });

  test('isActive returns false when state is 0', () => {
    expect(testFilter.isActive()).toBe(false);
  });

  test('setState updates state', () => {
    testFilter.setState(5);
    expect(testFilter.getState()).toBe(5);
  });

  test('isActive returns true when state is greater than 0', () => {
    testFilter.setState(5);
    expect(testFilter.isActive()).toBe(true);
  });

  test('subscribe adds a listener and returns an unsubscribe function', () => {
    const callback = jest.fn();
    const unsubscribe = testFilter.subscribe(callback);
    testFilter.setState(5);
    expect(callback).toHaveBeenCalledTimes(1);
    unsubscribe();
    testFilter.setState(10);
    expect(callback).toHaveBeenCalledTimes(1);
  });

  test('onSelect sets state to the passed value', () => {
    testFilter.onSelect({value: 10, close: () => {}, createPortal: () => () => {}});
    expect(testFilter.getState()).toBe(10);
  });
});
