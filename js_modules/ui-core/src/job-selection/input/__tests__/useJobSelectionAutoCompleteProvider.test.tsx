import {renderHook} from '@testing-library/react';

import {Job} from '../../AntlrJobSelection';
import {useJobSelectionAutoCompleteProvider} from '../useJobSelectionAutoCompleteProvider';

const buildJob = (name: string): Job => ({
  name,
  repo: {name: 'repo', location: 'location'},
});

describe('useJobSelectionAutoCompleteProvider', () => {
  it('suggests a job that loads after the first render', () => {
    const {result, rerender} = renderHook(
      ({jobs}) => {
        const provider = useJobSelectionAutoCompleteProvider(jobs);
        return provider.useAutoComplete({line: 'name:nigh', cursorIndex: 9});
      },
      {initialProps: {jobs: [buildJob('daily')]}},
    );

    expect(result.current.autoCompleteResults.list.map((item) => item.text)).not.toContain(
      '"nightly"',
    );

    rerender({jobs: [buildJob('daily'), buildJob('nightly')]});

    expect(result.current.autoCompleteResults.list.map((item) => item.text)).toContain('"nightly"');
  });
});
