import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {act, render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {ReactNode} from 'react';

import {DefaultOptions} from '../../../apollo-client';
import {buildPythonError} from '../../../graphql/builders';
import {RunFilterToken} from '../../RunsFilterUtils';
import {buildRunTagFocusMocks} from '../../__fixtures__/RunTagQueries.fixtures';
import {RunsSearchInput} from '../RunsSearchInput';

jest.mock('../../../selection/SelectionInput', () => ({
  SelectionAutoCompleteInput: jest.requireActual('../__fixtures__/MockSelectionInput.fixtures')
    .MockSelectionInput,
}));

const LEGACY_TOKENS: RunFilterToken[] = [
  {token: 'pipeline', value: 'nightly_etl'},
  {token: 'tag', value: 'user=a@b.com'},
];

// Each query can answer twice, so a repeated request shows up in the call count.
const buildCountedFocusMocks = () =>
  buildRunTagFocusMocks().map((mock) => ({
    ...mock,
    result: jest.fn().mockReturnValue(mock.result),
    maxUsageCount: 2,
  }));

// Matches the app client's default, under which each lazy fetch sends a request.
const APP_DEFAULT_OPTIONS = {
  watchQuery: {fetchPolicy: 'cache-and-network'},
} as const satisfies DefaultOptions;

type RenderSearchProps = {
  tokens?: RunFilterToken[];
  onChange?: jest.Mock;
  mocks?: MockedResponse[];
};

const renderSearch = ({
  tokens = [],
  onChange = jest.fn(),
  mocks = buildRunTagFocusMocks(),
}: RenderSearchProps = {}) =>
  render(<RunsSearchInput tokens={tokens} onChange={onChange} />, {
    wrapper: ({children}: {children: ReactNode}) => (
      <MockedProvider mocks={mocks} defaultOptions={APP_DEFAULT_OPTIONS}>
        {children}
      </MockedProvider>
    ),
  });

const replaceSearch = async (text: string) => {
  const user = userEvent.setup();
  const input = await screen.findByRole('textbox', {name: 'Search and filter runs'});
  await user.clear(input);
  await user.type(input, `${text}{Enter}`);
  return input;
};

describe('RunsSearchInput', () => {
  it('shows legacy tokens as search text', async () => {
    renderSearch({tokens: LEGACY_TOKENS});

    expect(await screen.findByRole('textbox', {name: 'Search and filter runs'})).toHaveValue(
      'user:"a@b.com" and job:nightly_etl',
    );
  });

  it('applies a valid search as legacy tokens', async () => {
    const onChange = jest.fn();
    renderSearch({tokens: LEGACY_TOKENS, onChange});

    await replaceSearch('status:failure and code_location:"repo@loc"');

    expect(onChange).toHaveBeenCalledTimes(1);
    expect(onChange).toHaveBeenCalledWith([
      {token: 'status', value: 'FAILURE'},
      {token: 'tag', value: '.dagster/repository=repo@loc'},
    ]);
  });

  it('keeps the applied filter and shows the error for an invalid search', async () => {
    const onChange = jest.fn();
    renderSearch({tokens: LEGACY_TOKENS, onChange});

    const input = await replaceSearch('id:a or job:b');

    expect(onChange).not.toHaveBeenCalled();
    expect(input).toHaveValue('id:a or job:b');
    expect(await screen.findByRole('alert')).toHaveTextContent('or only combines IDs or statuses');
  });

  it('does not apply a search that matches the current filter', async () => {
    const onChange = jest.fn();
    renderSearch({tokens: LEGACY_TOKENS, onChange});

    const input = await replaceSearch('user:"a@b.com" and job:nightly_etl');

    expect(onChange).not.toHaveBeenCalled();
    expect(input).toHaveValue('user:"a@b.com" and job:nightly_etl');
    expect(input).toHaveAttribute('data-uncommitted', 'false');
  });

  it('does not apply a search that reverses the values in an or group', async () => {
    const onChange = jest.fn();
    const tokens: RunFilterToken[] = [
      {token: 'status', value: 'FAILURE'},
      {token: 'status', value: 'SUCCESS'},
    ];
    renderSearch({tokens, onChange});

    const input = await replaceSearch('status:success or status:failure');

    expect(onChange).not.toHaveBeenCalled();
    expect(input).toHaveAttribute('data-uncommitted', 'false');
  });

  it('discards an invalid search when the tokens change, even after returning to them', async () => {
    const {rerender} = renderSearch({tokens: LEGACY_TOKENS});
    await replaceSearch('id:a or job:b');
    expect(await screen.findByRole('alert')).toHaveTextContent('or only combines IDs or statuses');

    rerender(<RunsSearchInput tokens={[{token: 'id', value: 'abc'}]} onChange={jest.fn()} />);

    expect(await screen.findByRole('textbox', {name: 'Search and filter runs'})).toHaveValue(
      'id:abc',
    );
    expect(await screen.findByRole('alert')).toBeEmptyDOMElement();

    rerender(<RunsSearchInput tokens={LEGACY_TOKENS} onChange={jest.fn()} />);

    expect(await screen.findByRole('textbox', {name: 'Search and filter runs'})).toHaveValue(
      'user:"a@b.com" and job:nightly_etl',
    );
    expect(await screen.findByRole('alert')).toBeEmptyDOMElement();
  });

  it('loads suggestions when the input gains focus', async () => {
    const mocks = buildCountedFocusMocks();
    renderSearch({mocks});
    const input = await screen.findByRole('textbox', {name: 'Search and filter runs'});
    mocks.forEach(({result}) => expect(result).not.toHaveBeenCalled());

    await userEvent.setup().click(input);

    await waitFor(() => {
      mocks.forEach(({result}) => expect(result).toHaveBeenCalledTimes(1));
    });
  });

  it('does not reload the suggested values when the input gains focus again', async () => {
    const mocks = buildCountedFocusMocks();
    renderSearch({mocks});
    const user = userEvent.setup();
    const input = await screen.findByRole('textbox', {name: 'Search and filter runs'});
    await user.click(input);
    await waitFor(() => {
      mocks.forEach(({result}) => expect(result).toHaveBeenCalledTimes(1));
    });

    await user.tab();
    await user.click(input);
    await act(() => new Promise((resolve) => setTimeout(resolve, 0)));

    mocks.forEach(({result}) => expect(result).toHaveBeenCalledTimes(1));
  });

  it('retries a failed value query when the input gains focus again', async () => {
    const mocks = buildCountedFocusMocks();
    const failed = mocks.at(-1);
    if (!failed) {
      throw new Error('Expected a value query mock');
    }
    renderSearch({
      mocks: [{request: failed.request, error: new Error('Request failed')}, ...mocks],
    });
    const user = userEvent.setup();
    const input = await screen.findByRole('textbox', {name: 'Search and filter runs'});
    await user.click(input);
    await waitFor(() => {
      mocks.slice(0, -1).forEach(({result}) => expect(result).toHaveBeenCalledTimes(1));
    });
    expect(failed.result).not.toHaveBeenCalled();

    await user.tab();
    await user.click(input);

    await waitFor(() => expect(failed.result).toHaveBeenCalledTimes(1));
    mocks.forEach(({result}) => expect(result).toHaveBeenCalledTimes(1));
  });

  it('retries a value query that returned an error when the input gains focus again', async () => {
    const mocks = buildCountedFocusMocks();
    const failed = mocks.at(-1);
    if (!failed) {
      throw new Error('Expected a value query mock');
    }
    const errorResult = jest.fn().mockReturnValue({
      data: {__typename: 'Query', runTagsOrError: buildPythonError()},
    });
    renderSearch({mocks: [{request: failed.request, result: errorResult}, ...mocks]});
    const user = userEvent.setup();
    const input = await screen.findByRole('textbox', {name: 'Search and filter runs'});
    await user.click(input);
    await waitFor(() => expect(errorResult).toHaveBeenCalledTimes(1));
    expect(failed.result).not.toHaveBeenCalled();

    await user.tab();
    await user.click(input);

    await waitFor(() => expect(failed.result).toHaveBeenCalledTimes(1));
  });

  it('retries the tag key query that returned an error when the input gains focus again', async () => {
    const mocks = buildCountedFocusMocks();
    const [keysMock] = mocks;
    if (!keysMock) {
      throw new Error('Expected the tag key query mock');
    }
    const errorResult = jest.fn().mockReturnValue({
      data: {__typename: 'Query', runTagKeysOrError: buildPythonError()},
    });
    renderSearch({mocks: [{request: keysMock.request, result: errorResult}, ...mocks]});
    const user = userEvent.setup();
    const input = await screen.findByRole('textbox', {name: 'Search and filter runs'});
    await user.click(input);
    await waitFor(() => expect(errorResult).toHaveBeenCalledTimes(1));
    expect(keysMock.result).not.toHaveBeenCalled();

    await user.tab();
    await user.click(input);

    await waitFor(() => expect(keysMock.result).toHaveBeenCalledTimes(1));
  });
});
