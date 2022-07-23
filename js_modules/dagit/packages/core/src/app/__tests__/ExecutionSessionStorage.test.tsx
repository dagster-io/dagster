import {render, screen, waitFor} from '@testing-library/react';
import * as React from 'react';

import {
  IExecutionSession,
  makeKey,
  makeOldKey,
  useExecutionSessionStorage,
} from '../ExecutionSessionStorage';

describe('ExecutionSessionStorage', () => {
  const BASE_PATH = '';
  const REPO_ADDRESS = {
    name: 'test-name',
    location: 'test-location',
  };
  const JOB_NAME = 'test-job';

  const oldKey = makeOldKey(REPO_ADDRESS, JOB_NAME);
  const newKey = makeKey(BASE_PATH, REPO_ADDRESS, JOB_NAME);

  const TestComponent = (props: {initial?: Partial<IExecutionSession>}) => {
    const [data] = useExecutionSessionStorage(REPO_ADDRESS, JOB_NAME, props.initial);
    return (
      <>
        <div>Current: {data.current}</div>
        <div>{`YAML: "${data.sessions[data.current].runConfigYaml}"`}</div>
      </>
    );
  };

  beforeEach(() => {
    window.localStorage.clear();
  });

  describe('Migration', () => {
    it('Migrates old localStorage data from old format', async () => {
      const testData = {sessions: {test: 'test'}, current: 'test'};
      window.localStorage.setItem(oldKey, JSON.stringify(testData));

      const {rerender} = render(<TestComponent />);

      await waitFor(() => {
        expect(screen.queryByText(/current: test/i)).toBeVisible();
      });

      // Data is at the new key, and the old key is deleted.
      expect(JSON.parse(window.localStorage.getItem(newKey) as any)).toEqual(testData);
      expect(window.localStorage.getItem(oldKey)).toEqual(null);

      // Render it again, expect the data to still be there.
      rerender(<TestComponent />);

      // Data is at the new key, and the old key remains deleted.
      expect(JSON.parse(window.localStorage.getItem(newKey) as any)).toEqual(testData);
      expect(window.localStorage.getItem(oldKey)).toEqual(null);
    });
  });

  describe('Initialization', () => {
    it('initializes with `initial`, if provided', async () => {
      const testData = {runConfigYaml: 'hello yaml'};
      render(<TestComponent initial={testData} />);

      await waitFor(() => {
        expect(screen.queryByText(/current: s[0-9]+/i)).toBeVisible();
        expect(screen.queryByText(/yaml: "hello yaml"/i)).toBeVisible();
      });
    });

    it('initializes without `initial`, if none provided', async () => {
      render(<TestComponent />);

      await waitFor(() => {
        expect(screen.queryByText(/current: s[0-9]+/i)).toBeVisible();
        expect(screen.queryByText(/yaml: ""/i)).toBeVisible();
      });
    });
  });

  describe('Preserve session object', () => {
    let storedObject: any = null;
    const TestComponent = (props: {initial?: Partial<IExecutionSession>}) => {
      const [data] = useExecutionSessionStorage(REPO_ADDRESS, JOB_NAME, props.initial);
      storedObject = data;
      return (
        <>
          <div>Current: {data.current}</div>
          <div>{`YAML: "${data.sessions[data.current].runConfigYaml}"`}</div>
        </>
      );
    };

    beforeEach(() => {
      storedObject = null;
    });

    it('no initial: tracks the same stored object across multiple renders', async () => {
      const {rerender} = render(<TestComponent />);

      await waitFor(() => {
        expect(screen.queryByText(/current: s[0-9]+/i)).toBeVisible();
      });

      const storedObjectA = storedObject;
      rerender(<TestComponent />);

      await waitFor(() => {
        expect(screen.queryByText(/current: s[0-9]+/i)).toBeVisible();
      });

      const storedObjectB = storedObject;
      expect(storedObjectA).toBe(storedObjectB);

      rerender(<TestComponent />);

      await waitFor(() => {
        expect(screen.queryByText(/current: s[0-9]+/i)).toBeVisible();
      });

      const storedObjectC = storedObject;
      expect(storedObjectC).toBe(storedObjectA);
    });

    it('with initial: tracks the same stored object across multiple renders', async () => {
      const testData = {runConfigYaml: 'hello yaml'};
      const {rerender} = render(<TestComponent initial={testData} />);

      await waitFor(() => {
        expect(screen.queryByText(/current: s[0-9]+/i)).toBeVisible();
      });

      const storedObjectA = storedObject;
      rerender(<TestComponent initial={testData} />);

      await waitFor(() => {
        expect(screen.queryByText(/current: s[0-9]+/i)).toBeVisible();
      });

      const storedObjectB = storedObject;
      expect(storedObjectA).toBe(storedObjectB);

      rerender(<TestComponent initial={testData} />);

      await waitFor(() => {
        expect(screen.queryByText(/current: s[0-9]+/i)).toBeVisible();
      });

      const storedObjectC = storedObject;
      expect(storedObjectC).toBe(storedObjectA);
    });
  });
});
