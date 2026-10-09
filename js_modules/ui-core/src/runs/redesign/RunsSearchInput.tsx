import {tokensAsStringArray} from '@dagster-io/ui-components';
import isEqual from 'lodash/isEqual';
import {useState} from 'react';

import {getRunsSearchText} from './getRunsSearchText';
import {lintRunsSearch} from './lintRunsSearch';
import {parseRunsSearch} from './parseRunsSearch';
import {SelectionAutoCompleteInput} from '../../selection/SelectionInput';
import {RunFilterToken} from '../RunsFilterUtils';
import {useRunsSearchAutoComplete} from './useRunsSearchAutoComplete';

type Props = {
  tokens: RunFilterToken[];
  onChange: (tokens: RunFilterToken[]) => void;
};

type UnappliedCommit = {
  text: string;
  tokenStrings: string[];
};

export const RunsSearchInput = ({tokens, onChange}: Props) => {
  const [unappliedCommit, setUnappliedCommit] = useState<UnappliedCommit | null>(null);

  const appliedText = getRunsSearchText(tokens);
  const tokenStrings = tokensAsStringArray(tokens);

  // A commit that doesn't change the tokens (invalid, or the same filter reordered) stays in
  // the input, so lint errors show and the input doesn't look uncommitted. New tokens
  // (Back/Forward, a status tab) discard it for good, so returning to the old tokens doesn't
  // bring it back.
  const isUnappliedCommitStale =
    unappliedCommit !== null && !isEqual(unappliedCommit.tokenStrings, tokenStrings);
  if (isUnappliedCommitStale) {
    setUnappliedCommit(null);
  }
  const value = unappliedCommit && !isUnappliedCommitStale ? unappliedCommit.text : appliedText;

  const onCommit = (text: string) => {
    const result = parseRunsSearch(text);

    // Compare canonical forms, ignoring order, so Enter on an unedited legacy search
    // (for example `pipeline:` tokens) or a reordered one doesn't rewrite the URL.
    const appliedTokens = parseRunsSearch(appliedText).tokens ?? tokens;
    const isUnchanged =
      result.tokens !== null &&
      isEqual(tokensAsStringArray(result.tokens).sort(), tokensAsStringArray(appliedTokens).sort());

    if (!result.tokens || isUnchanged) {
      setUnappliedCommit({text, tokenStrings});
      return;
    }

    setUnappliedCommit(null);
    onChange(result.tokens);
  };

  return (
    <SelectionAutoCompleteInput
      id="runs-search"
      recentSearchesKey="runs-search"
      placeholder="Search and filter runs"
      useAutoComplete={useRunsSearchAutoComplete}
      linter={lintRunsSearch}
      value={value}
      onChange={onCommit}
    />
  );
};
