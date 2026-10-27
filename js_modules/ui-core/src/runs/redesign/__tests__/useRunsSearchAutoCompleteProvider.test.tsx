import {MockedProvider} from '@apollo/client/testing';
import {act, renderHook, waitFor} from '@testing-library/react';
import {ReactNode} from 'react';

import {
  buildPipeline,
  buildRepository,
  buildRepositoryLocation,
  buildWorkspaceLocationEntry,
} from '../../../graphql/builders';
import {WorkspaceProvider} from '../../../workspace/WorkspaceContext/WorkspaceContext';
import {buildWorkspaceMocks} from '../../../workspace/WorkspaceContext/__fixtures__/Workspace.fixtures';
import {DUNDER_REPO_NAME} from '../../../workspace/buildRepoAddress';
import {DagsterTag} from '../../RunTag';
import {
  buildRunTagFocusMocks,
  buildRunTagValuesQueryMockedResponse,
} from '../../__fixtures__/RunTagQueries.fixtures';
import {getRunsSearchText} from '../getRunsSearchText';
import {parseRunsSearch} from '../parseRunsSearch';
import {useRunsSearchAutoCompleteProvider} from '../useRunsSearchAutoCompleteProvider';

const WORKSPACE_MOCKS = buildWorkspaceMocks([
  buildWorkspaceLocationEntry({
    name: 'single',
    locationOrLoadError: buildRepositoryLocation({
      name: 'single',
      repositories: [
        buildRepository({
          id: 'single',
          name: DUNDER_REPO_NAME,
          pipelines: [
            buildPipeline({name: 'nightly', isJob: true}),
            buildPipeline({name: '__ASSET_JOB', isJob: true}),
            buildPipeline({name: '__anonymous_asset_job_a', isJob: true}),
          ],
        }),
      ],
    }),
  }),
  buildWorkspaceLocationEntry({
    name: 'zeta',
    locationOrLoadError: buildRepositoryLocation({
      name: 'zeta',
      repositories: [
        buildRepository({
          id: 'repo_a',
          name: 'repo_a',
          pipelines: [buildPipeline({name: 'hourly', isJob: true})],
        }),
        buildRepository({id: 'repo_b', name: 'repo_b', pipelines: []}),
      ],
    }),
  }),
  buildWorkspaceLocationEntry({
    name: 'my@loc',
    locationOrLoadError: buildRepositoryLocation({
      name: 'my@loc',
      repositories: [buildRepository({id: 'at', name: DUNDER_REPO_NAME, pipelines: []})],
    }),
  }),
]);

const SEARCH_VALUE_MOCKS = buildRunTagFocusMocks({
  values: {
    [DagsterTag.SensorName]: ['my_sensor'],
    [DagsterTag.User]: ['a@b.com', ''],
  },
});

type MocksProps = {
  children: ReactNode;
};

const Mocks = ({children}: MocksProps) => (
  <MockedProvider
    mocks={[
      ...WORKSPACE_MOCKS,
      ...SEARCH_VALUE_MOCKS,
      buildRunTagValuesQueryMockedResponse('team', ['dev', '', 'data']),
    ]}
  >
    <WorkspaceProvider>{children}</WorkspaceProvider>
  </MockedProvider>
);

/** Renders the provider for `line` after the input gains focus. */
const renderSuggestions = (line: string, cursorIndex = line.length) => {
  const {result} = renderHook(
    () => {
      const {useAutoComplete, fetchValues} = useRunsSearchAutoCompleteProvider();
      return {
        fetchValues,
        ...useAutoComplete({line, cursorIndex}),
      };
    },
    {wrapper: Mocks},
  );
  act(() => result.current.fetchValues());
  return result;
};

type SuggestionsResult = ReturnType<typeof renderSuggestions>;

const getRowTexts = (result: SuggestionsResult) =>
  result.current.autoCompleteResults.list.map(({text}) => text);

const applyRows = (line: string, result: SuggestionsResult) => {
  const {list, from, to} = result.current.autoCompleteResults;
  return list.map(({text}) => `${line.slice(0, from)}${text}${line.slice(to)}`);
};

describe('useRunsSearchAutoCompleteProvider', () => {
  it('lists attributes in the order the search writes them', async () => {
    const result = renderSuggestions('');

    await waitFor(() =>
      expect(getRowTexts(result)).toEqual([
        'status:',
        'sensor:',
        'schedule:',
        'user:',
        'job:',
        'code_location:',
        'id:',
        'backfill:',
        'partition:',
        'tag:',
        'snapshot_id:',
        '()',
      ]),
    );
  });

  it('reports loading until the workspace loads', async () => {
    // Skips fetchValues so no tag value query is in flight.
    const {result} = renderHook(
      () => useRunsSearchAutoCompleteProvider().useAutoComplete({line: 'job:', cursorIndex: 4}),
      {wrapper: Mocks},
    );

    expect(result.current.loading).toBe(true);
    await waitFor(() => expect(result.current.loading).toBe(false));
  });

  it.each([
    {line: 'status:FA', rows: ['FAILURE']},
    {line: 'job:', rows: ['hourly', 'nightly']},
    {
      line: 'code_location:',
      rows: ['"__repository__@my@loc"', '"repo_a@zeta"', '"repo_b@zeta"', 'single'],
    },
    {line: 'sensor:', rows: ['my_sensor']},
    {line: 'user:', rows: ['"a@b.com"']},
    {line: 'tag:team=', rows: ['team=data', 'team=dev']},
    {line: 'tag:team=da', rows: ['team=data']},
    {line: 'tag:"team"=', rows: ['team=data', 'team=dev']},
    {line: 'job:hourly and tag:team=da', rows: ['team=data']},
  ])('suggests values for $line as the search writes them', async ({line, rows}) => {
    const result = renderSuggestions(line);

    await waitFor(() => expect(getRowTexts(result)).toEqual(rows));
    const applied = applyRows(line, result);
    expect(applied.map((text) => getRunsSearchText(parseRunsSearch(text).tokens ?? []))).toEqual(
      applied,
    );
  });

  it.each([
    {line: 'tag:team', applied: 'tag:team='},
    {line: 'tag:my-team', applied: 'tag:"my-team"='},
  ])('offers the typed key for $line, leaving the cursor on the value', async ({line, applied}) => {
    const result = renderSuggestions(line);

    await waitFor(() => expect(applyRows(line, result)).toEqual([applied]));
    expect(result.current.autoCompleteResults.list).toEqual([
      expect.not.objectContaining({trailingSpace: true}),
    ]);
  });

  it.each(['tag:a\\b', 'tag:my*'])(
    'offers no typed key for %s, which quoting would change',
    async (line) => {
      const result = renderSuggestions(line);

      await waitFor(() => expect(result.current.loading).toBe(false));
      expect(getRowTexts(result)).toEqual([]);
    },
  );

  it.each([
    {input: 'tag:te|am=data', applied: 'tag:team=data'},
    {input: 'tag:te|am=', applied: 'tag:team='},
    {input: 'tag:team|=', applied: 'tag:team='},
    {input: 'tag:"te|am"=data', applied: 'tag:team=data'},
    {input: 'tag:"my|*"', applied: 'tag:"my*"='},
    {input: 'tag:te|am=data and job:nightly', applied: 'tag:team=data and job:nightly'},
  ])('keeps the rest of the pair when choosing a key in $input', async ({input, applied}) => {
    const cursorIndex = input.indexOf('|');
    const line = input.replace('|', '');
    const result = renderSuggestions(line, cursorIndex);

    await waitFor(() => expect(applyRows(line, result)).toEqual([applied]));
  });

  it('keeps the shared range for operators after a quoted key', async () => {
    const line = 'tag:"team"=data';
    const cursorIndex = line.indexOf('=');
    const result = renderSuggestions(line, cursorIndex);

    await waitFor(() =>
      expect(result.current.autoCompleteResults).toEqual(
        expect.objectContaining({from: cursorIndex, to: cursorIndex}),
      ),
    );
  });
});
