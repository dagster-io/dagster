// text is the text to be inserted into the input
export interface SelectionAutoCompleteProvider<T extends {text: string}> {
  /**
   * Retrieves a list of attributes that match the provided query string.
   *
   * @param query - The search string to match attribute names against.
   * @param textCallback - An optional callback to transform the display text of each result. Used to insert spaces or double quotes if necessary depending on surrounding context
   * @returns An array of attributes that match the query.
   */
  getAttributeResultsMatchingQuery: (
    query: string,
    textCallback?: (value: string) => string,
  ) => T[];

  /**
   * Retrieves a list of attribute values for a specific attribute that match the provided query string.
   *
   * @param attribute - The name of the attribute to search within.
   * @param query - The search string to match attribute values against.
   * @param textCallback - An optional callback to transform the display text of each result. Used to insert spaces or double quotes if necessary depending on surrounding context
   * @returns An array of attribute values that match the query for the specified attribute.
   */
  getAttributeValueResultsMatchingQuery: (
    attribute: string,
    query: string,
    textCallback?: (value: string) => string,
  ) => T[];

  /**
   * Retrieves a list of function results that match the provided query string.
   *
   * @param query - The search string to match function names against.
   * @param textCallback - An optional callback to transform the display text of each result. Used to insert spaces or double quotes if necessary depending on surrounding context
   * @param options - Optional settings
   * @returns An array of functions that match the query.
   */
  getFunctionResultsMatchingQuery: (
    query: string,
    textCallback?: (value: string) => string,
    options?: {
      // If this is true then the result should be returned with parenthesis. (eg. "foo()" instead of "foo")
      // This will be true if there aren't any parenthesis already present.
      includeParenthesis?: boolean;
    },
  ) => T[];

  /**
   * Retrieves a single substring result that matches the provided query string.
   *
   * @param query - The search string to match substrings against.
   * @param textCallback - An optional callback to transform the display text of each result. Used to insert spaces or double quotes if necessary depending on surrounding context
   * @returns A single substring result that matches the query.
   */
  getSubstringResultMatchingQuery: (query: string, textCallback?: (value: string) => string) => T;

  /**
   * Retrieves a list of attribute values, including their corresponding attribute names, that match the provided query string.
   *
   * @param query - The search string to match attribute values against.
   * @param textCallback - An optional callback to transform the display text of each result. Used to insert spaces or double quotes if necessary depending on surrounding context
   * @returns An array of attribute values along with their attribute names that match the query.
   */
  getAttributeValueIncludeAttributeResultsMatchingQuery: (
    query: string,
    textCallback?: (value: string) => string,
  ) => T[];

  /**
   * Renders a single autocomplete result into a React node for display.
   *
   * @param result - The autocomplete result to be rendered.
   * @returns A React node representing the rendered autocomplete result.
   */
  renderResult: (result: T | BaseSuggestion) => React.ReactNode;

  useAutoComplete: (
    line: string,
    cursorIndex: number,
  ) => {
    autoCompleteResults: {
      from: number;
      to: number;
      list: Array<T | BaseSuggestion>;
    };
    loading: boolean;
  };
}

export type BaseSuggestion =
  | {
      text: string; // The text to be inserted into the input
      displayText: string; // The text to be displayed in the dropdown
      type: 'logical_operator' | 'parenthesis';
    }
  | {
      text: string; // The text to be inserted into the input
      displayText: string; // The text to be displayed in the dropdown
      type: 'up-traversal' | 'down-traversal';
    };
