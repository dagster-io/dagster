import * as React from 'react';

export const useSuggestionsForString = (
  buildSuggestions: (value: string) => string[],
  value: string,
) => {
  const tokens = value.trim().split(/\s+/);
  const lastToken = tokens.length ? tokens[tokens.length - 1] : '';
  const queryString = lastToken.toLocaleLowerCase();

  const suggestions = React.useMemo(() => buildSuggestions(queryString), [
    buildSuggestions,
    queryString,
  ]);

  const onSelectSuggestion = React.useCallback(
    (suggestion: string) => {
      const lastIndex = value.lastIndexOf(queryString);
      if (lastIndex !== -1) {
        const keep = value.slice(0, lastIndex);
        return `${keep}${suggestion}`;
      }

      // Shouldn't really ever fall through to this, since `queryString` should definitely
      // be the last token in `value`. No-op just in case.
      return value;
    },
    [queryString, value],
  );

  return React.useMemo(
    () => ({
      suggestions,
      onSelectSuggestion,
    }),
    [onSelectSuggestion, suggestions],
  );
};
