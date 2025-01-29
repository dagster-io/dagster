import {Operator, SelectionAutoCompleteProvider, Suggestion} from './SelectionAutoCompleteProvider';

/**
 * @type TAttributeMap - A map of attribute names to arrays of values.
 * @type TPrimaryAttributeKey - The key of the `attributesMap` that serves as the identifier for the objects we're filtering. This key will support substring queries.
 * @type TSuggestion - The shape of each autocomplete suggestion, containing at least a `text` property.
 */
/**
 * Creates an autocomplete provider that suggests completions based on a map of attributes and their values
 * @param primaryAttributeKey - The key used for substring searches and primary identification
 * @param attributesMap - Map of attribute names to their possible values
 * @param functions - List of available function names that can be suggested
 * @param createAttributeSuggestion - Factory function to create suggestions for attributes
 * @param createAttributeValueSuggestion - Factory function to create suggestions for attribute values
 * @param createFunctionSuggestion - Factory function to create suggestions for functions
 * @param createSubstringSuggestion - Factory function to create suggestions for substring matches
 * @param createAttributeValueIncludeAttributeSuggestion - Factory function for suggestions that include both attribute and value
 * @param createOperatorSuggestion - Factory function to create suggestions for operators
 * @param doesValueIncludeQuery - Function to determine if a value matches the search query
 */
export function createAttributeBasedAutoCompleteProvider<
  TAttributeMap extends {
    [key: string]: string[] | {key: string; value?: string | null | undefined}[];
  },
  TPrimaryAttributeKey extends keyof TAttributeMap,
  TFunctionName extends string,
>({
  primaryAttributeKey,
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
  primaryAttributeKey: TPrimaryAttributeKey;

  attributesMap: TAttributeMap;

  functions: readonly TFunctionName[];
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
    // @ts-expect-error - TPrimaryAttributeKey is a string
    attribute: K | `${TPrimaryAttributeKey}_substring`;
    value: TAttributeMap[K][number];
    textCallback?: (value: string) => string;
  }) => Suggestion;
  createFunctionSuggestion: ({
    func,
    options,
    text,
  }: {
    func: TFunctionName;
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
      if (attribute === `${primaryAttributeKey as string}_substring`) {
        values = attributesMap[primaryAttributeKey];
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
