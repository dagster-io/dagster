import {uniq} from 'lodash';
import React from 'react';

import {
  TokenizingField,
  TokenizingFieldValue,
  stringFromValue,
  tokenizedValuesFromString,
} from 'src/TokenizingField';

interface RunTagsTokenizingFieldProps {
  runs: {tags: {key: string; value: string}[]}[];
  tokens: TokenizingFieldValue[];
  onChange: (tokens: TokenizingFieldValue[]) => void;
}

export const RunTagsTokenizingField: React.FunctionComponent<RunTagsTokenizingFieldProps> = ({
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
