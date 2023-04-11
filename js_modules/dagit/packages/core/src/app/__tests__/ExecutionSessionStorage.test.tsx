import {render, screen, waitFor} from '@testing-library/react';
import * as React from 'react';

import {
  IExecutionSession,
  IStorageData,
  MAX_SESSION_WRITE_ATTEMPTS,
  allStoredSessions,
  removeSession,
  useExecutionSessionStorage,
  writeLaunchpadSessionToStorage,
} from '../ExecutionSessionStorage';

describe('ExecutionSessionStorage', () => {
  const REPO_ADDRESS = {
    name: 'test-name',
    location: 'test-location',
  };
  const JOB_NAME = 'test-job';

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

  describe('localStorage management', () => {
    beforeEach(() => {
      window.localStorage.setItem(
        'abc',
        JSON.stringify({current: 's0', sessions: {s0: {runConfigYaml: 'foo bar'}}}),
      );

      window.localStorage.setItem(
        'def',
        JSON.stringify({
          current: 's2',
          sessions: {s2: {runConfigYaml: 'bar baz'}, s5: {runConfigYaml: 'bar baz borp'}},
        }),
      );

      window.localStorage.setItem(
        'ghi',
        JSON.stringify({
          current: 's1',
          sessions: {
            s8: {runConfigYaml: 'bar baz derp'},
            s1: {runConfigYaml: 'gorp baz'},
            s10: {runConfigYaml: 'gorp baz'},
          },
        }),
      );

      window.localStorage.setItem('not-a-session', '1234');
      window.localStorage.setItem('my-boolean', 'true');
    });

    describe('allStoredSessions', () => {
      it('retrieves tuples for all stored sessions, ordered by session recency', () => {
        const tuples = allStoredSessions();
        expect(tuples).toEqual([
          ['abc', 's0'],
          ['ghi', 's1'],
          ['def', 's2'],
          ['def', 's5'],
          ['ghi', 's8'],
          ['ghi', 's10'],
        ]);
      });
    });

    describe('removeSession', () => {
      it('removes sessions from storage', () => {
        removeSession('abc', 's0');
        expect(window.localStorage.getItem('abc')).toBe('{"sessions":{}}');

        expect(() => {
          removeSession('nothing', 's2');
        }).not.toThrow();

        removeSession('def', 's2');
        expect(window.localStorage.getItem('def')).toBe(
          '{"current":"s5","sessions":{"s5":{"runConfigYaml":"bar baz borp"}}}',
        );
      });
    });

    describe('Handle quota error', () => {
      it('Clears old sessions when encountering a quota error', () => {
        const mockSetter = jest
          .fn()
          .mockImplementationOnce(() => {
            throw new Error('Quota error!');
          })
          .mockImplementationOnce(() => {
            throw new Error('Quota error!');
          })
          .mockImplementation((data: IStorageData) => {
            window.localStorage.setItem('xyz', JSON.stringify(data));
            return true;
          });

        expect(allStoredSessions()).toEqual([
          ['abc', 's0'],
          ['ghi', 's1'],
          ['def', 's2'],
          ['def', 's5'],
          ['ghi', 's8'],
          ['ghi', 's10'],
        ]);

        const writeSession = writeLaunchpadSessionToStorage(mockSetter);

        writeSession({
          current: 's100',
          sessions: {
            s100: {
              key: 'abc',
              name: 'abc',
              base: null,
              mode: 'default',
              needsRefresh: false,
              assetSelection: null,
              solidSelection: null,
              solidSelectionQuery: '*',
              flattenGraphs: false,
              configChangedSinceRun: false,
              tags: [],
              runConfigYaml: 'new stuff',
            },
          },
        });

        expect(mockSetter).toHaveBeenCalled();

        // The loop has removed the two oldest sessions, then added in the newest.
        expect(allStoredSessions()).toEqual([
          ['def', 's2'],
          ['def', 's5'],
          ['ghi', 's8'],
          ['ghi', 's10'],
          ['xyz', 's100'],
        ]);
      });

      it('Eventually gives up trying to write the session, avoiding an unexpected infinite loop', () => {
        const mockSetter = jest.fn().mockImplementation(() => {
          throw new Error('Quota error!');
        });

        expect(allStoredSessions()).toEqual([
          ['abc', 's0'],
          ['ghi', 's1'],
          ['def', 's2'],
          ['def', 's5'],
          ['ghi', 's8'],
          ['ghi', 's10'],
        ]);

        const writeSession = writeLaunchpadSessionToStorage(mockSetter);

        writeSession({
          current: 's100',
          sessions: {
            s100: {
              key: 'abc',
              name: 'abc',
              base: null,
              mode: 'default',
              needsRefresh: false,
              assetSelection: null,
              solidSelection: null,
              solidSelectionQuery: '*',
              flattenGraphs: false,
              configChangedSinceRun: false,
              tags: [],
              runConfigYaml: 'new stuff',
            },
          },
        });

        expect(mockSetter).toHaveBeenCalledTimes(MAX_SESSION_WRITE_ATTEMPTS);

        // The loop has correctly removed all of the sessions.
        expect(allStoredSessions()).toEqual([]);
      });
    });
  });
});
