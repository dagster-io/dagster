import {render, screen, waitFor} from '@testing-library/react';
import * as React from 'react';

import {TestProvider} from '../../testing/TestProvider';
import {RepoAddress} from '../../workspace/types';
import {AppContext} from '../AppContext';
import {
  getKey,
  makeNamespace,
  makeOldNamespace,
  useExecutionSessionStorage,
} from '../ExecutionSessionStorage';

function mockedLocalStorage() {
  let store = {};
  return {
    setItem(key: string, item: any) {
      store[key] = item;
    },
    getItem(key: string) {
      return store[key];
    },
    removeItem(key: string) {
      delete store[key];
    },
    clear() {
      store = {};
    },
    get length() {
      return Object.keys(store).length;
    },
    key(n: number) {
      return Object.keys(store)[n];
    },
  };
}

let BASE_PATH = '';
const REPO_ADDRESS = {
  name: 'test-name',
  location: 'test-location',
};

const PIPELINE = 'test-pipeline';

describe('ExecutionSessionStorage', () => {
  const originalLocalStorage = window.localStorage;
  beforeEach(() => {
    window.localStorage = mockedLocalStorage();
    jest.resetModules();
  });
  afterEach(() => {
    window.localStorage = originalLocalStorage;
  });

  it('Migrates old localStorage data from old format', async () => {
    const testData = {sessions: {test: 'test'}, current: 'test'};
    const oldFormat = getKey(makeOldNamespace(REPO_ADDRESS, PIPELINE));
    const newFormat = getKey(makeNamespace(BASE_PATH, REPO_ADDRESS, PIPELINE));

    window.localStorage.setItem(oldFormat, JSON.stringify(testData));

    function TestComponent() {
      const context = React.useContext(AppContext);
      BASE_PATH = context.basePath;
      const [data] = useExecutionSessionStorage(REPO_ADDRESS, PIPELINE);
      return <div>Current: {data.current}</div>;
    }

    const {rerender} = render(
      <TestProvider>
        <TestComponent />
      </TestProvider>,
    );

    await waitFor(() => {
      expect(screen.queryByText(/current: test/i)).toBeVisible();
    });

    // Its at the new key
    expect(JSON.parse(window.localStorage.getItem(newFormat) as any)).toEqual(testData);

    // old key is deleted
    expect(window.localStorage.getItem(oldFormat)).toEqual(null);

    // Render it again, expect the data to still be there

    rerender(
      <TestProvider>
        <TestComponent />
      </TestProvider>,
    );

    // Its at the new key
    expect(JSON.parse(window.localStorage.getItem(newFormat) as any)).toEqual(testData);

    // old key is deleted
    expect(window.localStorage.getItem(oldFormat)).toEqual(null);
  });
});
