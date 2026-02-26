import {useCallback, useMemo} from 'react';

export const useSuggestionsForString = (
  buildSuggestions: (value: string) => string[],
  value: string,
) => {
  const tokens = value.toLocaleLowerCase().trim().split(/\s+/);
  const queryString = tokens[tokens.length - 1] || '';

  const suggestions = useMemo(() => buildSuggestions(queryString), [buildSuggestions, queryString]);

  const onSelectSuggestion = useCallback(
    (suggestion: string) => {
      const lastIndex = value.toLocaleLowerCase().lastIndexOf(queryString);
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

  return useMemo(
    () => ({
      suggestions,
      onSelectSuggestion,
    }),
    [onSelectSuggestion, suggestions],
  );
};
