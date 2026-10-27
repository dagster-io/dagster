import {MockedProvider} from '@apollo/client/testing';
import {renderHook, waitFor} from '@testing-library/react';
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

type MocksProps = {
  children: ReactNode;
};

const Mocks = ({children}: MocksProps) => (
  <MockedProvider mocks={WORKSPACE_MOCKS}>
    <WorkspaceProvider>{children}</WorkspaceProvider>
  </MockedProvider>
);

/** Renders the provider for `line` with the cursor at its end. */
const renderSuggestions = (line: string) => {
  const {result} = renderHook(
    () => useRunsSearchAutoCompleteProvider().useAutoComplete({line, cursorIndex: line.length}),
    {wrapper: Mocks},
  );
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
    const result = renderSuggestions('job:');

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
  ])('suggests values for $line as the search writes them', async ({line, rows}) => {
    const result = renderSuggestions(line);

    await waitFor(() => expect(getRowTexts(result)).toEqual(rows));
    const applied = applyRows(line, result);
    expect(applied.map((text) => getRunsSearchText(parseRunsSearch(text).tokens ?? []))).toEqual(
      applied,
    );
  });
});
