import uniq from 'lodash/uniq';
import * as React from 'react';

import {RunFilterTokenType} from '../runs/RunsFilterInput';
import {
  TokenizingField,
  TokenizingFieldValue,
  stringFromValue,
  tokenizedValuesFromString,
} from '../ui/TokenizingField';

interface RunTagsTokenizingFieldProps {
  runs: {tags: {key: string; value: string}[]}[];
  tokens: TokenizingFieldValue[];
  onChange: (tokens: TokenizingFieldValue[]) => void;
}

// BG TODO: This should most likely be folded into RunsFilterInput, but that component loads autocompletions
// from all runs in the repo and doesn't support being scoped to a particular pipeline.

export const RunTagsSupportedTokens: RunFilterTokenType[] = ['tag'];

export const RunTagsTokenizingField: React.FC<RunTagsTokenizingFieldProps> = ({
  runs,
  tokens,
  onChange,
}) => {
  const suggestions = [
    {
      token: 'tag',
      values: () => {
        const runTags = runs.map((r) => r.tags).reduce((a, b) => [...a, ...b], []);
        const runTagValues = runTags.map((t) => `${t.key}=${t.value}`);
        return uniq(runTagValues).sort();
      },
    },
  ];
  const search = tokenizedValuesFromString(stringFromValue(tokens), suggestions);
  return (
    <TokenizingField
      small
      values={search}
      onChange={onChange}
      placeholder="Filter partition runs..."
      suggestionProviders={suggestions}
      loading={false}
    />
  );
};
