import {act, render, screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as React from 'react';

import {TestProvider} from '../testing/TestProvider';
import {repoAddressFromPath} from '../workspace/repoAddressFromPath';

import {buildStorageKey, useRepoExpansionState} from './useRepoExpansionState';

const TEMP_EXPANDED_STORAGE_KEY = 'temp-expanded-key';
const COLLAPSED_STORAGE_KEY = 'collapsed-key';
const ALL_REPO_KEYS = ['lorem@ipsum', 'dolorsit@amet', 'consectetur@adipiscing'];

describe('useRepoExpansionState', () => {
  const Test = () => {
    const {expandedKeys, onToggle, onToggleAll} = useRepoExpansionState(
      TEMP_EXPANDED_STORAGE_KEY,
      COLLAPSED_STORAGE_KEY,
      ALL_REPO_KEYS,
    );

    return (
      <TestProvider>
        <div>
          {ALL_REPO_KEYS.map((key) => (
            <div key={key}>
              <div>{`${key} ${expandedKeys.includes(key) ? 'expanded' : 'collapsed'}`}</div>
              <button
                onClick={() => {
                  const repoAddress = repoAddressFromPath(key);
                  if (repoAddress) {
                    onToggle(repoAddress);
                  }
                }}
              >
                {`toggle ${key}`}
              </button>
            </div>
          ))}
          <button onClick={() => onToggleAll(true)}>expand all</button>
          <button onClick={() => onToggleAll(false)}>collapse all</button>
        </div>
      </TestProvider>
    );
  };

  beforeEach(() => {
    window.localStorage.clear();
  });

  it('provides a list of expanded keys for the stored state', async () => {
    window.localStorage.setItem(buildStorageKey('', COLLAPSED_STORAGE_KEY), JSON.stringify([]));
    await act(async () => {
      render(<Test />);
    });

    // Expect all keys to be expanded
    expect(screen.getByText('lorem@ipsum expanded')).toBeVisible();
    expect(screen.getByText('dolorsit@amet expanded')).toBeVisible();
    expect(screen.getByText('consectetur@adipiscing expanded')).toBeVisible();
  });

  it('tracks collapsed keys', async () => {
    window.localStorage.setItem(
      buildStorageKey('', COLLAPSED_STORAGE_KEY),
      JSON.stringify(['lorem@ipsum']),
    );
    await act(async () => {
      render(<Test />);
    });

    // Expect keys to have appropriate state. One collapsed!
    expect(screen.getByText('lorem@ipsum collapsed')).toBeVisible();
    expect(screen.getByText('dolorsit@amet expanded')).toBeVisible();
    expect(screen.getByText('consectetur@adipiscing expanded')).toBeVisible();
  });

  it('toggles a key to expanded', async () => {
    const fullCollapsedKey = buildStorageKey('', COLLAPSED_STORAGE_KEY);
    window.localStorage.setItem(fullCollapsedKey, JSON.stringify(['lorem@ipsum']));
    await act(async () => {
      render(<Test />);
    });

    const button = screen.getByRole('button', {name: 'toggle lorem@ipsum'});
    await act(async () => {
      userEvent.click(button);
    });

    expect(screen.getByText('lorem@ipsum expanded')).toBeVisible();
    expect(window.localStorage.getItem(fullCollapsedKey)).toEqual('[]');
  });

  it('toggles a key to collapsed', async () => {
    const fullCollapsedKey = buildStorageKey('', COLLAPSED_STORAGE_KEY);
    window.localStorage.setItem(fullCollapsedKey, JSON.stringify([]));
    await act(async () => {
      render(<Test />);
    });

    const button = screen.getByRole('button', {name: 'toggle lorem@ipsum'});
    await act(async () => {
      userEvent.click(button);
    });

    expect(screen.getByText('lorem@ipsum collapsed')).toBeVisible();
    expect(window.localStorage.getItem(fullCollapsedKey)).toEqual(JSON.stringify(['lorem@ipsum']));
  });

  it('toggles all to expanded', async () => {
    const fullCollapsedKey = buildStorageKey('', COLLAPSED_STORAGE_KEY);
    window.localStorage.setItem(fullCollapsedKey, JSON.stringify(['lorem@ipsum', 'dolorsit@amet']));
    await act(async () => {
      render(<Test />);
    });

    const button = screen.getByRole('button', {name: 'expand all'});
    await act(async () => {
      userEvent.click(button);
    });

    // Everything expanded!
    expect(screen.getByText('lorem@ipsum expanded')).toBeVisible();
    expect(screen.getByText('dolorsit@amet expanded')).toBeVisible();
    expect(screen.getByText('consectetur@adipiscing expanded')).toBeVisible();
  });

  it('toggles all to collapsed', async () => {
    const fullCollapsedKey = buildStorageKey('', COLLAPSED_STORAGE_KEY);
    window.localStorage.setItem(fullCollapsedKey, JSON.stringify(['lorem@ipsum']));
    await act(async () => {
      render(<Test />);
    });

    const button = screen.getByRole('button', {name: 'collapse all'});
    await act(async () => {
      userEvent.click(button);
    });

    // Everything collapsed!
    expect(screen.getByText('lorem@ipsum collapsed')).toBeVisible();
    expect(screen.getByText('dolorsit@amet collapsed')).toBeVisible();
    expect(screen.getByText('consectetur@adipiscing collapsed')).toBeVisible();
  });

  // Temporary! Todo dish: Delete in November 2022.
  it('must convert "expanded" state to "collapsed" state if no stored collapsed state', async () => {
    const fullExpandedKey = buildStorageKey('', TEMP_EXPANDED_STORAGE_KEY);
    const fullCollapsedKey = buildStorageKey('', COLLAPSED_STORAGE_KEY);

    window.localStorage.setItem(fullExpandedKey, JSON.stringify(['lorem@ipsum', 'dolorsit@amet']));
    await act(async () => {
      render(<Test />);
    });

    expect(window.localStorage.getItem(fullCollapsedKey)).toEqual(
      JSON.stringify(['consectetur@adipiscing']),
    );

    // Expanded/collapsed state matches stored state.
    expect(screen.getByText('lorem@ipsum expanded')).toBeVisible();
    expect(screen.getByText('dolorsit@amet expanded')).toBeVisible();
    expect(screen.getByText('consectetur@adipiscing collapsed')).toBeVisible();
  });
});
