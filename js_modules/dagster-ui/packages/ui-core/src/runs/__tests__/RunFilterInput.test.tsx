import {MockedProvider, MockedResponse} from '@apollo/client/testing';
import {act, render, waitFor} from '@testing-library/react';
import {renderHook} from '@testing-library/react-hooks';
import userEvent from '@testing-library/user-event';
import * as React from 'react';

import {
  buildPipeline,
  buildRepository,
  buildRepositoryLocation,
  buildRunTagKeys,
  buildWorkspaceLocationEntry,
} from '../../graphql/types';
import {mockViewportClientRect, restoreViewportClientRect} from '../../testing/mocking';
import {calculateTimeRanges} from '../../ui/BaseFilters/useTimeRangeFilter';
import {WorkspaceProvider} from '../../workspace/WorkspaceContext/WorkspaceContext';
import {buildWorkspaceMocks} from '../../workspace/WorkspaceContext/__fixtures__/Workspace.fixtures';
import {DagsterTag} from '../RunTag';
import {
  RUN_TAG_KEYS_QUERY,
  RunFilterToken,
  RunsFilterInputProps,
  tagSuggestionValueObject,
  tagValueToFilterObject,
  useRunsFilterInput,
  useTagDataFilterValues,
} from '../RunsFilterInput';
import {buildRunTagValuesQueryMockedResponse} from '../__fixtures__/RunsFilterInput.fixtures';
import {RunTagKeysQuery} from '../types/RunsFilterInput.types';

const workspaceMocks = buildWorkspaceMocks([
  buildWorkspaceLocationEntry({
    name: 'some_workspace',
    locationOrLoadError: buildRepositoryLocation({
      name: 'some_location',
      repositories: [
        buildRepository({
          name: 'some_repo',
          pipelines: [
            buildPipeline({
              name: 'some_job',
            }),
          ],
        }),
      ],
    }),
  }),
]);

const runTagKeysMock: MockedResponse<RunTagKeysQuery> = {
  request: {
    query: RUN_TAG_KEYS_QUERY,
  },
  result: {
    data: {
      __typename: 'Query',
      runTagKeysOrError: buildRunTagKeys({
        keys: [DagsterTag.Partition, DagsterTag.PartitionSet],
      }),
    },
  },
};

const backfillRunTagsValuesMock = buildRunTagValuesQueryMockedResponse(DagsterTag.Backfill, [
  'value1',
  'value2',
]);

beforeAll(() => {
  mockViewportClientRect();
});

afterAll(() => {
  restoreViewportClientRect();
});

describe('useTagDataFilterValues', () => {
  it('should return the correct filter values based on the tag data', async () => {
    // Render the hook and pass the mockTagData as an argument
    const {result} = renderHook(() => useTagDataFilterValues(DagsterTag.Backfill), {
      wrapper: ({children}: {children?: React.ReactNode}) => (
        <MockedProvider mocks={[backfillRunTagsValuesMock]}>{children}</MockedProvider>
      ),
    });

    expect(result.current[1]).toEqual([]);
    act(() => {
      result.current[0]();
    });

    await waitFor(() => {
      expect(result.current[1]).toEqual([
        {
          label: 'value1',
          value: {
            key: DagsterTag.Backfill + '=value1',
            type: DagsterTag.Backfill,
            value: 'value1',
          },
          match: ['value1'],
          final: true,
        },
        {
          label: 'value2',
          value: {
            key: DagsterTag.Backfill + '=value2',
            type: DagsterTag.Backfill,
            value: 'value2',
          },
          match: ['value2'],
          final: true,
        },
      ]);
    });
  });
});

describe('tagValueToFilterObject', () => {
  it('should return an object with the correct properties', () => {
    const result = tagValueToFilterObject('tag1=value1');
    expect(result).toEqual({
      key: 'tag1=value1',
      type: 'tag1',
      value: 'value1',
    });
  });
});

describe('tagSuggestionValueObject', () => {
  it('should return an object with the correct properties', () => {
    const result = tagSuggestionValueObject('tag1', 'value1');
    expect(result).toEqual({
      final: true,
      value: {
        key: 'tag1',
        value: 'value1',
      },
    });
  });
});

function TestRunsFilterInput({
  mocks,
  tokens,
  onChange,
  enabledFilters,
}: RunsFilterInputProps & {
  mocks?: MockedResponse[];
}) {
  function RunsFilterInput(props: RunsFilterInputProps) {
    const {button, activeFiltersJsx} = useRunsFilterInput(props);
    return (
      <div>
        {button}
        {activeFiltersJsx}
      </div>
    );
  }
  return (
    <MockedProvider mocks={mocks?.length ? [...workspaceMocks, ...mocks] : workspaceMocks}>
      <WorkspaceProvider>
        <RunsFilterInput tokens={tokens} onChange={onChange} enabledFilters={enabledFilters} />
      </WorkspaceProvider>
    </MockedProvider>
  );
}

describe('<RunFilterInput  />', () => {
  // b. Test rendering with all enabledFilters
  // (Include tests for rendering with different combinations of enabledFilters)
  it('should call onChange with updated tokens when created DATE filter is updated', async () => {
    const onChange = jest.fn();
    const tokens: RunFilterToken[] = [
      {token: 'created_date_before', value: '1609459200'}, // 1/1/2021
      {token: 'created_date_after', value: '1577836800'}, // 1/1/2020
    ];
    const {getByText} = render(<TestRunsFilterInput tokens={tokens} onChange={onChange} />);

    expect(onChange).toHaveBeenCalledWith([
      {token: 'created_date_after', value: '1577836800'},
      {token: 'created_date_before', value: '1609459200'},
    ]);

    onChange.mockClear();

    expect(getByText('1/1/2020')).toBeVisible();
    expect(getByText('1/1/2021')).toBeVisible();

    await userEvent.click(getByText('Filter'));
    await userEvent.click(getByText('Created date'));
    await userEvent.click(getByText('Today'));

    const todayRange = calculateTimeRanges('UTC').timeRanges.TODAY.range;

    expect(onChange).toHaveBeenCalledWith([
      {
        token: 'created_date_after',
        value: '' + todayRange[0]! / 1000,
      },
    ]);
  });

  it('should call onChange with updated tokens when JOB filter is updated', async () => {
    const onChange = jest.fn();
    const tokens: RunFilterToken[] = [];
    const {getByText} = render(
      <TestRunsFilterInput
        tokens={tokens}
        onChange={onChange}
        enabledFilters={['job']}
        mocks={workspaceMocks}
      />,
    );

    onChange.mockClear();

    await userEvent.click(getByText('Filter'));
    await userEvent.click(getByText('Job'));

    await waitFor(async () => {
      await userEvent.click(getByText('some_job'));
    });

    expect(onChange).toHaveBeenCalledWith([{token: 'job', value: 'some_job'}]);
  });

  it('should call onChange with updated tokens when BACKFILL filter is updated', async () => {
    const onChange = jest.fn();
    const tokens: RunFilterToken[] = [];
    const {getByText} = render(
      <TestRunsFilterInput
        tokens={tokens}
        onChange={onChange}
        enabledFilters={['backfill']}
        mocks={[backfillRunTagsValuesMock]}
      />,
    );

    onChange.mockClear();

    await userEvent.click(getByText('Filter'));
    await userEvent.click(getByText('Backfill ID'));

    await waitFor(async () => {
      await userEvent.click(getByText('value1'));
    });

    expect(onChange).toHaveBeenCalledWith([{token: 'tag', value: 'dagster/backfill=value1'}]);
  });

  it('should call onChange with updated tokens when TAG filter is updated', async () => {
    const onChange = jest.fn();
    const tokens: RunFilterToken[] = [];
    const {getByText} = render(
      <TestRunsFilterInput
        tokens={tokens}
        onChange={onChange}
        mocks={[
          runTagKeysMock,
          buildRunTagValuesQueryMockedResponse(DagsterTag.PartitionSet, ['set1', 'set2']),
        ]}
      />,
    );

    onChange.mockClear();

    await userEvent.click(getByText('Filter'));
    await userEvent.click(getByText('Tag'));

    await waitFor(async () => {
      await userEvent.click(getByText(DagsterTag.PartitionSet));
    });

    await waitFor(async () => {
      await userEvent.click(getByText('set1'));
    });

    expect(onChange).toHaveBeenCalledWith([
      {token: 'tag', value: `${DagsterTag.PartitionSet}=set1`},
    ]);
  });
});
