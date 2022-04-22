import {render} from '@testing-library/react';
import * as React from 'react';

import {TestProvider} from '../../testing/TestProvider';
import {AppContext} from '../AppContext';
import {useExecutionSessionStorage} from '../ExecutionSessionStorage';

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

const oldKeyFormat = (repoAddress: typeof REPO_ADDRESS, pipelineOrJobName: string) => {
  return `dagit.v2.${repoAddress.name}.${pipelineOrJobName}`;
};

const newKeyFormat = (
  basePath: string,
  repoAddress: typeof REPO_ADDRESS,
  pipelineOrJobName: string,
) => {
  return `dagit.v2.${basePath}-${repoAddress.location}-${repoAddress.name}-${pipelineOrJobName}`;
};

describe('ExecutionSessionStorage', () => {
  const originalLocalStorage = window.localStorage;
  beforeEach(() => {
    window.localStorage = mockedLocalStorage();
    jest.resetModules();
  });
  afterEach(() => {
    window.localStorage = originalLocalStorage;
  });

  it('Migrates old localStorage data from old format', () => {
    const testData = {sessions: {test: 'test'}, current: 'test'};
    const oldFormat = oldKeyFormat(REPO_ADDRESS, PIPELINE);
    const newFormat = newKeyFormat(BASE_PATH, REPO_ADDRESS, PIPELINE);

    window.localStorage.setItem(oldFormat, JSON.stringify(testData));

    function TestComponent() {
      const context = React.useContext(AppContext);
      BASE_PATH = context.basePath;
      const [data] = useExecutionSessionStorage(REPO_ADDRESS, PIPELINE);
      expect(data).toEqual(testData);
      return <div />;
    }

    render(
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
