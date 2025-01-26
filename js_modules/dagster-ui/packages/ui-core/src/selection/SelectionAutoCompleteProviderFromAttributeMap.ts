import {SelectionAutoCompleteProvider} from './SelectionAutoCompleteProvider';

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
  // text is required -- it's the text that will be inserted into the input if the suggestion is selected.
  TSuggestion extends {text: string},
>({
  nameBase,
  attributesMapRef,
  functions,
  createAttributeSuggestion,
  createAttributeValueSuggestion,
  createFunctionSuggestion,
  createSubstringSuggestion,
  createAttributeValueIncludeAttributeSuggestion,
  doesValueIncludeQuery,
}: {
  nameBase: TNameBase;

  // This is a ref, to avoid re-creating the provider if the values in the attributes map changes.
  attributesMapRef: React.MutableRefObject<TAttributeMap>;

  functions: string[];
  createAttributeSuggestion: <K extends keyof TAttributeMap>(
    attribute: K,
    textCallback?: (value: string) => string,
  ) => TSuggestion;
  createAttributeValueSuggestion: <K extends keyof TAttributeMap>(
    // @ts-expect-error - TNameBase is a string
    attribute: K | `${TNameBase}_substring`,
    value: TAttributeMap[K][number],
    textCallback?: (value: string) => string,
  ) => TSuggestion;
  createFunctionSuggestion: (
    func: string,
    textCallback?: (value: string) => string,
    options?: {includeParenthesis?: boolean},
  ) => TSuggestion;
  createSubstringSuggestion: (
    query: string,
    textCallback?: (value: string) => string,
  ) => TSuggestion;
  createAttributeValueIncludeAttributeSuggestion: <K extends keyof TAttributeMap>(
    attribute: K,
    value: TAttributeMap[K][number],
    textCallback?: (value: string) => string,
  ) => TSuggestion;
  doesValueIncludeQuery: <K extends keyof TAttributeMap>(
    attribute: K,
    value: TAttributeMap[K][number],
    query: string,
  ) => boolean;
}): Omit<SelectionAutoCompleteProvider<TSuggestion>, 'renderResult' | 'useAutoComplete'> {
  return {
    getAttributeResultsMatchingQuery: (query: string, textCallback?: (value: string) => string) => {
      return Object.keys(attributesMapRef.current)
        .filter((attr) => attr.startsWith(query))
        .map((attr) => createAttributeSuggestion(attr, textCallback));
    },
    getAttributeValueResultsMatchingQuery: (
      attribute: keyof TAttributeMap,
      query: string,
      textCallback?: (value: string) => string,
    ) => {
      let values = attributesMapRef.current[attribute];
      if (attribute === `${nameBase as string}_substring`) {
        values = attributesMapRef.current[nameBase];
      }
      return (
        values
          ?.filter((value) => doesValueIncludeQuery(nameBase, value, query))
          .map((value) => createAttributeValueSuggestion(attribute, value, textCallback)) ?? []
      );
    },
    getFunctionResultsMatchingQuery: (
      query: string,
      textCallback?: (value: string) => string,
      options?: {includeParenthesis?: boolean},
    ) => {
      return functions
        .filter((func) => func.startsWith(query))
        .map((func) => createFunctionSuggestion(func, textCallback, options));
    },
    getSubstringResultMatchingQuery: (query: string, textCallback?: (value: string) => string) => {
      return createSubstringSuggestion(query, textCallback);
    },
    getAttributeValueIncludeAttributeResultsMatchingQuery: (
      query: string,
      textCallback?: (value: string) => string,
    ) => {
      return Object.keys(attributesMapRef.current).flatMap((attribute) => {
        return (
          attributesMapRef.current[attribute]
            ?.filter((value) => doesValueIncludeQuery(attribute, value, query))
            .map((value) =>
              createAttributeValueIncludeAttributeSuggestion(attribute, value, textCallback),
            ) ?? []
        );
      });
    },
  };
}
