import {Operator, SelectionAutoCompleteProvider, Suggestion} from './SelectionAutoCompleteProvider';

/**
 * Creates a `SelectionAutoCompleteProvider` based on the provided attribute map and configuration functions.
 *
 * This provider excludes the `renderResult` and `useAutoComplete` methods from the base `SelectionAutoCompleteProvider`.
 * It generates autocomplete suggestions for attributes, attribute values, functions, substrings, and combined attribute-value suggestions.
 *
 * @type TAttributeMap - A map of attribute names to arrays of values.
 * @type TNameBase - The key of the `attributesMap` that serves as the identifier for the objects we're filtering. This key will support substring queries.
 * @type TSuggestion - The shape of each autocomplete suggestion, containing at least a `text` property.
 */
export function createSelectionAutoCompleteProviderFromAttributeMap<
  TAttributeMap extends {[key: string]: any[]},
  TNameBase extends keyof TAttributeMap,
  TFunc extends string,
>({
  nameBase,
  attributesMap,
  functions,
  createAttributeSuggestion,
  createAttributeValueSuggestion,
  createFunctionSuggestion,
  createSubstringSuggestion,
  createAttributeValueIncludeAttributeSuggestion,
  createOperatorSuggestion,
  doesValueIncludeQuery,
}: {
  nameBase: TNameBase;

  attributesMap: TAttributeMap;

  functions: readonly TFunc[];
  createAttributeSuggestion: <K extends keyof TAttributeMap>({
    attribute,
    text,
  }: {
    attribute: K;
    text: string;
  }) => Suggestion;
  createAttributeValueSuggestion: <K extends keyof TAttributeMap>({
    attribute,
    value,
    textCallback,
  }: {
    // @ts-expect-error - TNameBase is a string
    attribute: K | `${TNameBase}_substring`;
    value: TAttributeMap[K][number];
    textCallback?: (value: string) => string;
  }) => Suggestion;
  createFunctionSuggestion: ({
    func,
    options,
    text,
  }: {
    func: TFunc;
    options?: {includeParenthesis?: boolean};
    text: string;
  }) => Suggestion;
  createSubstringSuggestion: ({
    query,
    textCallback,
  }: {
    query: string;
    textCallback?: (value: string) => string;
  }) => Suggestion;
  createAttributeValueIncludeAttributeSuggestion: <K extends keyof TAttributeMap>({
    attribute,
    value,
    textCallback,
  }: {
    attribute: K;
    value: TAttributeMap[K][number];
    textCallback?: (value: string) => string;
  }) => Suggestion;
  createOperatorSuggestion: ({
    type,
    text,
    displayText,
  }: {
    type: Parameters<typeof Operator>[0]['type'];
    text: string;
    displayText: string;
  }) => Suggestion;
  doesValueIncludeQuery: <K extends keyof TAttributeMap>({
    attribute,
    value,
    query,
  }: {
    attribute: K;
    value: TAttributeMap[K][number];
    query: string;
  }) => boolean;
}): Omit<SelectionAutoCompleteProvider, 'renderResult' | 'useAutoComplete'> {
  return {
    createOperatorSuggestion,
    getAttributeResultsMatchingQuery: ({query, textCallback}) => {
      return Object.keys(attributesMap)
        .filter((attr) => attr.startsWith(query))
        .map((attr) =>
          createAttributeSuggestion({
            attribute: attr,
            text: textCallback ? textCallback(`${attr}:`) : `${attr}:`,
          }),
        );
    },
    getAttributeValueResultsMatchingQuery: ({attribute, query, textCallback}) => {
      let values = attributesMap[attribute as keyof typeof attributesMap];
      if (attribute === `${nameBase as string}_substring`) {
        values = attributesMap[nameBase];
      }
      return (
        values
          ?.filter((value) => doesValueIncludeQuery({attribute, value, query}))
          .map((value) =>
            createAttributeValueSuggestion({
              attribute,
              value,
              textCallback,
            }),
          ) ?? []
      );
    },
    getFunctionResultsMatchingQuery: ({query, textCallback, options}) => {
      return functions
        .filter((func) => func.startsWith(query))
        .map((func) => {
          const value = options?.includeParenthesis ? `${func}()` : func;
          return createFunctionSuggestion({
            func,
            text: textCallback ? textCallback(value) : value,
            options,
          });
        });
    },
    getSubstringResultMatchingQuery: ({query, textCallback}) => {
      return createSubstringSuggestion({query, textCallback});
    },
    getAttributeValueIncludeAttributeResultsMatchingQuery: ({query, textCallback}) => {
      return Object.keys(attributesMap).flatMap((attribute) => {
        return (
          attributesMap[attribute]
            ?.filter((value) => doesValueIncludeQuery({attribute, value, query}))
            .map((value) =>
              createAttributeValueIncludeAttributeSuggestion({
                attribute,
                value,
                textCallback,
              }),
            ) ?? []
        );
      });
    },
  };
}
