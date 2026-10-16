import {render, screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import {RunFilterToken} from '../../RunsFilterUtils';
import {RunsSearchInput} from '../RunsSearchInput';

jest.mock('../../../selection/SelectionInput', () => ({
  SelectionAutoCompleteInput: jest.requireActual('../__fixtures__/MockSelectionInput.fixtures')
    .MockSelectionInput,
}));

const LEGACY_TOKENS: RunFilterToken[] = [
  {token: 'pipeline', value: 'nightly_etl'},
  {token: 'tag', value: 'user=a@b.com'},
];

const replaceSearch = async (text: string) => {
  const user = userEvent.setup();
  const input = await screen.findByRole('textbox', {name: 'Search and filter runs'});
  await user.clear(input);
  await user.type(input, `${text}{Enter}`);
  return input;
};

describe('RunsSearchInput', () => {
  it('shows legacy tokens as search text', async () => {
    render(<RunsSearchInput tokens={LEGACY_TOKENS} onChange={jest.fn()} />);

    expect(await screen.findByRole('textbox', {name: 'Search and filter runs'})).toHaveValue(
      'job:nightly_etl and user:"a@b.com"',
    );
  });

  it('applies a valid search as legacy tokens', async () => {
    const onChange = jest.fn();
    render(<RunsSearchInput tokens={LEGACY_TOKENS} onChange={onChange} />);

    await replaceSearch('status:failure and code_location:"repo@loc"');

    expect(onChange).toHaveBeenCalledTimes(1);
    expect(onChange).toHaveBeenCalledWith([
      {token: 'status', value: 'FAILURE'},
      {token: 'tag', value: '.dagster/repository=repo@loc'},
    ]);
  });

  it('keeps the applied filter and shows the error for an invalid search', async () => {
    const onChange = jest.fn();
    render(<RunsSearchInput tokens={LEGACY_TOKENS} onChange={onChange} />);

    const input = await replaceSearch('id:a or job:b');

    expect(onChange).not.toHaveBeenCalled();
    expect(input).toHaveValue('id:a or job:b');
    expect(await screen.findByRole('alert')).toHaveTextContent('or only combines IDs or statuses');
  });

  it('does not apply a search that matches the current filter', async () => {
    const onChange = jest.fn();
    render(<RunsSearchInput tokens={LEGACY_TOKENS} onChange={onChange} />);

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
    render(<RunsSearchInput tokens={tokens} onChange={onChange} />);

    const input = await replaceSearch('status:success or status:failure');

    expect(onChange).not.toHaveBeenCalled();
    expect(input).toHaveAttribute('data-uncommitted', 'false');
  });

  it('discards an invalid search when the tokens change, even after returning to them', async () => {
    const {rerender} = render(<RunsSearchInput tokens={LEGACY_TOKENS} onChange={jest.fn()} />);
    await replaceSearch('id:a or job:b');
    expect(await screen.findByRole('alert')).toHaveTextContent('or only combines IDs or statuses');

    rerender(<RunsSearchInput tokens={[{token: 'id', value: 'abc'}]} onChange={jest.fn()} />);

    expect(await screen.findByRole('textbox', {name: 'Search and filter runs'})).toHaveValue(
      'id:abc',
    );
    expect(await screen.findByRole('alert')).toBeEmptyDOMElement();

    rerender(<RunsSearchInput tokens={LEGACY_TOKENS} onChange={jest.fn()} />);

    expect(await screen.findByRole('textbox', {name: 'Search and filter runs'})).toHaveValue(
      'job:nightly_etl and user:"a@b.com"',
    );
    expect(await screen.findByRole('alert')).toBeEmptyDOMElement();
  });
});
