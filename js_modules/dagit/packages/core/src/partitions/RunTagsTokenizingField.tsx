import {TokenizingField, stringFromValue, tokenizedValuesFromString} from '@dagster-io/ui';
import uniq from 'lodash/uniq';
import * as React from 'react';

import {RunFilterToken, RunFilterTokenType} from '../runs/RunsFilterInput';

interface RunTagsTokenizingFieldProps {
  runs: {tags: {key: string; value: string}[]}[];
  tokens: RunFilterToken[];
  onChange: (tokens: RunFilterToken[]) => void;
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
      onChange={(values) => onChange(values as RunFilterToken[])}
      placeholder="Filter partition runs..."
      suggestionProviders={suggestions}
      loading={false}
    />
  );
};
