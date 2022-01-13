import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Fuse from 'fuse.js';
import * as React from 'react';

import {TestProvider} from '../testing/TestProvider';

import {SearchResult} from './types';
import {useAssetSearch} from './useRepoSearch';

const GETTYSBURG =
  'four score and seven years ago our fathers brought forth upon this continent a new nation conceived in liberty and dedicated to the proposition that all men are created equal';

describe('useAssetSearch', () => {
  const mocks = {
    AssetConnection: () => ({
      nodes: () => [
        {id: 'foo', key: {path: ['foo', 'bar']}},
        {id: 'bar', key: {path: ['baz', 'derp']}},
        {
          id: 'gettysburg',
          key: {
            path: GETTYSBURG.split(' '),
          },
        },
      ],
    }),
  };

  const Test = () => {
    const {loading, performSearch} = useAssetSearch();
    const [value, setValue] = React.useState('');
    const [results, setResults] = React.useState<Fuse.FuseResult<SearchResult>[]>(() => []);

    const onClick = () => setResults(performSearch(value));

    return (
      <div>
        <input type="text" onChange={(e) => setValue(e.target.value)} value={value} />
        <div>Loading: {String(loading)}</div>
        <div>{`Results (${results.length}):`}</div>
        {results.map((result, ii) => (
          <div key={ii}>{`Item: ${result.item.label}`}</div>
        ))}
        <button onClick={onClick}>Search</button>
      </div>
    );
  };

  it('finds a matching asset', async () => {
    render(
      <TestProvider apolloProps={{mocks}}>
        <Test />
      </TestProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText(/Loading: true/)).toBeVisible();
    });

    userEvent.type(screen.getByRole('textbox'), 'fo');
    userEvent.click(screen.getByRole('button'));

    await waitFor(() => {
      // Two matches, `foo`, and Gettysburg.
      expect(screen.queryByText(/Results \(2\)/)).toBeVisible();
      expect(screen.queryByText(/Item: foo \u203a bar/)).toBeVisible();
    });
  });

  it('fails to find a matching asset if no string match', async () => {
    render(
      <TestProvider apolloProps={{mocks}}>
        <Test />
      </TestProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText(/Loading: true/)).toBeVisible();
    });

    userEvent.type(screen.getByRole('textbox'), 'ZILCH NADA');
    userEvent.click(screen.getByRole('button'));

    await waitFor(() => {
      // No matches.
      expect(screen.queryByText(/Results \(0\)/)).toBeVisible();
      expect(screen.queryByText(/Item: foo \u203a bar/)).toBeNull();
    });
  });

  it('finds a matching asset deep in the key path due to segment matching', async () => {
    render(
      <TestProvider apolloProps={{mocks}}>
        <Test />
      </TestProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText(/Loading: true/)).toBeVisible();
    });

    userEvent.type(screen.getByRole('textbox'), 'equal');
    userEvent.click(screen.getByRole('button'));

    await waitFor(() => {
      // Gettysburg is our only match.
      expect(screen.queryByText(/Results \(1\)/)).toBeVisible();
      expect(screen.queryByText(`Item: ${GETTYSBURG.split(' ').join(' \u203a ')}`)).toBeVisible();
    });
  });
});
