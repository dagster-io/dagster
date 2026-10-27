import {Box, Icon, IconName, MiddleTruncate, Text} from '@dagster-io/ui-components';
import React from 'react';

import styles from './SelectionAutoComplete.module.css';
import {assertUnreachable} from '../app/Util';

export interface SelectionAutoCompleteProvider {
  /**
   * Retrieves a list of attributes that match the provided query string.
   *
   * @param query - The search string to match attribute names against.
   * @param textCallback - An optional callback to transform the display text of each result. Used to insert spaces or double quotes if necessary depending on surrounding context
   * @returns An array of attributes that match the query.
   */
  getAttributeResultsMatchingQuery: (prop: {
    query: string;
    textCallback?: (value: string) => string;
  }) => Suggestion[];

  /**
   * Retrieves a list of attribute values for a specific attribute that match the provided query string.
   *
   * @param attribute - The name of the attribute to search within.
   * @param query - The search string to match attribute values against.
   * @param textCallback - An optional callback to transform the display text of each result. Used to insert spaces or double quotes if necessary depending on surrounding context
   * @returns An array of attribute values that match the query for the specified attribute.
   */
  getAttributeValueResultsMatchingQuery: (prop: {
    attribute: string;
    query: string;
    textCallback?: (value: string) => string;
    /** The typed value with quotes added, offered in place of "No match found" for a known attribute. */
    quotedValue?: QuotedValue;
    /** Limits results to this tag key's values; set when the cursor is in a key=value pair's value. */
    key?: string;
  }) => Array<Suggestion>;

  /**
   * Retrieves a list of function results that match the provided query string.
   *
   * @param query - The search string to match function names against.
   * @param textCallback - An optional callback to transform the display text of each result. Used to insert spaces or double quotes if necessary depending on surrounding context
   * @param options - Optional settings
   * @returns An array of functions that match the query.
   */
  getFunctionResultsMatchingQuery: (prop: {
    query: string;
    textCallback?: (value: string) => string;
    options?: {
      // If this is true then the result should be returned with parenthesis. (eg. "foo()" instead of "foo")
      // This will be true if there aren't any parenthesis already present.
      includeParenthesis?: boolean;
    };
  }) => Suggestion[];

  /**
   * Retrieves a single substring result that matches the provided query string.
   *
   * @param query - The search string to match substrings against.
   * @param textCallback - An optional callback to transform the display text of each result. Used to insert spaces or double quotes if necessary depending on surrounding context
   * @returns A single substring result that matches the query, or null when the input has no
   * wildcard attribute.
   */
  getSubstringResultMatchingQuery: (prop: {
    query: string;
    textCallback?: (value: string) => string;
  }) => Suggestion | null;

  /**
   * Retrieves a list of attribute values, including their corresponding attribute names, that match the provided query string.
   *
   * @param query - The search string to match attribute values against.
   * @param textCallback - An optional callback to transform the display text of each result. Used to insert spaces or double quotes if necessary depending on surrounding context
   * @returns An array of attribute values along with their attribute names that match the query.
   */
  getAllResults: (prop: {
    query: string;
    textCallback?: (value: string) => string;
  }) => Array<Suggestion>;

  createOperatorSuggestion: (prop: {
    text: string;
    displayText: string;
    type: OperatorType;
  }) => Suggestion;

  useAutoComplete: (prop: {line: string; cursorIndex: number}) => {
    autoCompleteResults: {
      from: number;
      to: number;
      list: Array<Suggestion>;
    };
    loading: boolean;
  };

  supportsTraversal?: boolean;
  supportsNot?: boolean;
}

export type Suggestion =
  | {
      text: string;
      jsx: React.ReactNode;
      trailingSpace?: boolean;
    }
  | {
      text: string;
      jsx: React.ReactNode;
      type: 'no-match';
    };

export type QuotedValue = {
  text: string;
  /** An unquoted value has a `*`, which quoting makes literal except on the primary attribute. */
  hasUnquotedAsterisk: boolean;
};

type OperatorType = 'and' | 'or' | 'not' | 'parenthesis' | 'up-traversal' | 'down-traversal';

const operatorToIconAndLabel: Record<OperatorType, {icon: IconName; label: string}> = {
  and: {
    icon: 'and',
    label: 'And',
  },
  or: {
    icon: 'or',
    label: 'Or',
  },
  not: {
    icon: 'not',
    label: 'Not',
  },
  parenthesis: {
    icon: 'parenthesis',
    label: 'Parenthesis',
  },
  'up-traversal': {
    icon: 'graph_upstream',
    label: 'Include upstream dependencies',
  },
  'down-traversal': {
    icon: 'graph_downstream',
    label: 'Include downstream dependencies',
  },
};

export const Operator = ({displayText, type}: {displayText: string; type: OperatorType}) => {
  const {icon, label} = operatorToIconAndLabel[type];
  return (
    <SuggestionJSXBase
      label={<MiddleTruncate text={label} />}
      icon={icon}
      rightLabel={<MiddleTruncate text={displayText} />}
    />
  );
};

export const AttributeValueTagSuggestion = ({
  tag,
}: {
  tag: {key: string; value?: string | null | undefined};
}) => {
  const {key, value} = tag;
  const valueText = value ? `${key}=${value}` : key;
  return <SuggestionJSXBase label={<MiddleTruncate text={valueText} />} />;
};

export const SuggestionJSXBase = ({
  label,
  icon,
  rightLabel,
}: {
  label: React.ReactNode;
  icon?: IconName | null;
  rightLabel?: React.ReactNode;
}) => {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: `minmax(0, 1fr) ${rightLabel ? 'minmax(0, 1fr)' : ''}`,
        gap: 2,
        justifyContent: 'space-between',
      }}
    >
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: icon ? 'auto minmax(0, 1fr)' : 'minmax(0, 1fr)',
          alignItems: 'center',
          gap: 6,
        }}
      >
        {icon ? <Icon name={icon} size={12} style={{margin: 0}} /> : null}
        <Text size={14} style={{overflow: 'hidden'}}>
          {label}
        </Text>
      </div>
      {rightLabel ? (
        <Text size={14} family="mono" style={{textAlign: 'right', overflow: 'hidden'}}>
          {rightLabel}
        </Text>
      ) : null}
    </div>
  );
};

type Functions = Array<'sinks' | 'roots'>;
type AttributeItems = string[] | {key: string; value?: string}[];
export const createProvider = <
  TAttributeMap extends {[key: string]: AttributeItems},
  TPrimaryAttributeKey extends keyof TAttributeMap,
>({
  attributeToIcon,
  attributeToLabel,
  primaryAttributeKey,
  attributesMap,
  functions = ['sinks', 'roots'],
  formatValue = (value) => `"${value}"`,
}: {
  attributeToIcon: Record<keyof TAttributeMap, IconName>;
  /** Labels for attribute rows. Defaults to the attribute name in sentence case. */
  attributeToLabel?: Partial<Record<keyof TAttributeMap, string>>;
  /** The attribute that bare terms search with wildcards. Omit when the input has none. */
  primaryAttributeKey?: TPrimaryAttributeKey;
  attributesMap: TAttributeMap;
  functions?: Functions;
  /** Formats inserted values and tag keys, and the no-match row's typed value. Quotes by default. */
  formatValue?: (value: string) => string;
}): Omit<SelectionAutoCompleteProvider, 'useAutoComplete'> => {
  function doesValueIncludeQuery({
    value,
    query,
  }: {
    value: TAttributeMap[keyof TAttributeMap][0];
    query: string;
  }) {
    const queryLower = query.toLowerCase();
    if (typeof value !== 'string') {
      return (
        value.key.toLowerCase().includes(queryLower) ||
        value.value?.toLowerCase().includes(queryLower) ||
        `${value.key}=${value.value ?? ''}`.toLowerCase().includes(queryLower)
      );
    }
    return value.toLowerCase().includes(queryLower);
  }

  function getAttributeLabel(attribute: keyof TAttributeMap) {
    const name = (attribute as string).replace(/_/g, ' ');
    return attributeToLabel?.[attribute] ?? name.charAt(0).toUpperCase() + name.slice(1);
  }

  function createAttributeSuggestion({
    attribute,
    text,
  }: {
    attribute: keyof TAttributeMap;
    text: string;
  }) {
    const displayText = `${attribute as string}:`;
    const icon: IconName = attributeToIcon[attribute];
    const label = getAttributeLabel(attribute);
    return {
      text,
      jsx: (
        <SuggestionJSXBase
          label={<MiddleTruncate text={label} />}
          icon={icon}
          rightLabel={<MiddleTruncate text={displayText} />}
        />
      ),
    };
  }

  function nullSuggestion({textCallback}: {textCallback?: (text: string) => string}) {
    return {
      text: textCallback ? textCallback('<null>') : '<null>',
      jsx: <SuggestionJSXBase label={<span className={styles.nullString}>No value</span>} />,
      trailingSpace: true,
    };
  }

  function createAttributeValueSuggestion({
    value,
    textCallback,
  }: {
    value: TAttributeMap[keyof TAttributeMap][0];
    textCallback?: (text: string) => string;
  }) {
    if (typeof value !== 'string') {
      const valueText = value.value
        ? `${formatValue(value.key)}=${formatValue(value.value)}`
        : formatValue(value.key);
      if (value.key === '' && !value.value) {
        return nullSuggestion({textCallback});
      }
      return {
        text: textCallback ? textCallback(valueText) : valueText,
        jsx: <AttributeValueTagSuggestion tag={value} />,
        trailingSpace: true,
      };
    }
    if (value === '') {
      return nullSuggestion({textCallback});
    }
    return {
      text: textCallback ? textCallback(formatValue(value)) : formatValue(value),
      jsx: <SuggestionJSXBase label={<MiddleTruncate text={value} />} />,
      trailingSpace: true,
    };
  }

  function createFunctionSuggestion({
    func,
    text,
    options,
  }: {
    func: (typeof functions)[number];
    text: string;
    options?: {includeParenthesis?: boolean};
  }) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const functionName = func[0]!.toUpperCase() + func.slice(1);
    const rightLabel = options?.includeParenthesis ? `${func}()` : func;
    let icon: IconName;
    switch (func) {
      case 'roots':
        icon = 'roots';
        break;
      case 'sinks':
        icon = 'sinks';
        break;
      default:
        assertUnreachable(func);
    }
    return {
      text,
      jsx: <SuggestionJSXBase label={functionName} icon={icon} rightLabel={rightLabel} />,
    };
  }

  function createSubstringSuggestion({
    attribute,
    query,
    textCallback,
  }: {
    attribute: string;
    query: string;
    textCallback?: (text: string) => string;
  }) {
    const text = `${attribute}:"*${query}*"`;
    const displayAttribute = getAttributeLabel(attribute);
    const displayText = (
      <Box flex={{direction: 'row', alignItems: 'center', gap: 2}}>
        {displayAttribute} contains <MiddleTruncate text={query} />
      </Box>
    );
    return {
      text: textCallback ? textCallback(text) : text,
      jsx: <SuggestionJSXBase label={displayText} rightLabel={<MiddleTruncate text={text} />} />,
      trailingSpace: true,
    };
  }

  function createAttributeAndValueSuggestion({
    attribute,
    value,
    textCallback,
  }: {
    attribute: keyof TAttributeMap;
    value: TAttributeMap[keyof TAttributeMap][0];
    textCallback?: (text: string) => string;
  }) {
    let text;
    let valueText;
    if (typeof value !== 'string') {
      if (value.value) {
        text = `${attribute as string}:${formatValue(value.key)}=${formatValue(value.value)}`;
        valueText = `${value.key}=${value.value}`;
      } else {
        text = `${attribute as string}:${formatValue(value.key)}`;
        valueText = value.key;
      }
    } else {
      text = `${attribute as string}:${formatValue(value)}`;
      valueText = value;
    }
    return {
      text: textCallback ? textCallback(text) : text,
      jsx: (
        <SuggestionJSXBase
          label={
            <Box flex={{direction: 'row', alignItems: 'center', gap: 2}}>
              <Text size={12} family="mono" color="textLight">
                {attribute as string}:
              </Text>
              <Text size={12} family="mono" className={styles.attributeValue}>
                <MiddleTruncate text={valueText} />
              </Text>
            </Box>
          }
        />
      ),
      trailingSpace: true,
    };
  }

  function createQuotedValueSuggestion({
    attribute,
    text,
    textCallback,
  }: {
    attribute: string;
    text: string;
    textCallback?: (text: string) => string;
  }) {
    return {
      text: textCallback ? textCallback(text) : text,
      jsx: (
        <SuggestionJSXBase
          label={
            <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
              <Text size={12} color="textLight">
                Add quotes:
              </Text>
              <Text size={12} family="mono" color="textDefault" className={styles.attributeValue}>
                <MiddleTruncate text={`${attribute}:${text}`} />
              </Text>
            </Box>
          }
        />
      ),
      trailingSpace: true,
    };
  }

  return {
    createOperatorSuggestion: ({type, text, displayText}) => {
      return {
        text,
        jsx: <Operator type={type} displayText={displayText} />,
      };
    },
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
    getAttributeValueResultsMatchingQuery: ({attribute, query, textCallback, quotedValue, key}) => {
      const values = attributesMap[attribute as keyof typeof attributesMap];
      const shouldTreatAsteriskAsWildcard = attribute === primaryAttributeKey;

      const regex = createRegex(query, shouldTreatAsteriskAsWildcard);
      const keyLower = key?.toLowerCase();
      const results = values
        ? filterMap<AttributeItems[0], Suggestion>(
            values,
            (value) => {
              if (keyLower !== undefined && typeof value !== 'string') {
                return (
                  value.key.toLowerCase() === keyLower &&
                  !!value.value &&
                  doesValueIncludeQuery({value: value.value, query})
                );
              }
              if (shouldTreatAsteriskAsWildcard) {
                if (typeof value === 'string') {
                  return regex.test(value);
                }
                return regex.test(value.key) || (value.value ? regex.test(value.value) : false);
              }
              return doesValueIncludeQuery({value, query});
            },
            (value) => createAttributeValueSuggestion({value, textCallback}),
            MAX_RESULTS_PER_ATTRIBUTE,
          )
        : [];
      if (results.length === 0) {
        if (
          values &&
          quotedValue &&
          (!quotedValue.hasUnquotedAsterisk || shouldTreatAsteriskAsWildcard)
        ) {
          return [createQuotedValueSuggestion({attribute, text: quotedValue.text, textCallback})];
        }

        // A bare <null> means an empty value, so it isn't shown quoted.
        const typedQuery = query === '<null>' ? query : formatValue(query);
        const typedValue = key !== undefined ? `${formatValue(key)}=${typedQuery}` : typedQuery;
        return [
          {
            text: '',
            jsx: (
              <Text size={12} color="textLight">
                No match found for{' '}
                <Text size={12} family="mono" color="textDefault">
                  {attribute}:{typedValue}
                </Text>
              </Text>
            ),
            type: 'no-match',
          },
        ];
      }
      return results;
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
      if (primaryAttributeKey === undefined) {
        return null;
      }
      return createSubstringSuggestion({
        attribute: primaryAttributeKey as string,
        query,
        textCallback,
      });
    },
    getAllResults: ({query, textCallback}) => {
      return Object.keys(attributesMap).flatMap((attribute) => {
        return attributesMap[attribute]
          ? filterMap<AttributeItems[0], Suggestion>(
              attributesMap[attribute],
              (value) => doesValueIncludeQuery({value, query}),
              (value) => createAttributeAndValueSuggestion({attribute, value, textCallback}),
              MAX_RESULTS_PER_ATTRIBUTE,
            )
          : [];
      });
    },
  };
};

const MAX_RESULTS_PER_ATTRIBUTE = 50;

/**
 * Like Array.filter().map(), but exits early once `limit` results have been collected.
 * This avoids running the predicate and mapper on the remaining elements.
 */
function filterMap<T, R>(
  items: T[],
  predicate: (item: T) => boolean,
  mapper: (item: T) => R,
  limit: number,
): R[] {
  const results: R[] = [];
  for (const item of items) {
    if (predicate(item)) {
      results.push(mapper(item));
      if (results.length >= limit) {
        break;
      }
    }
  }
  return results;
}

function createRegex(pattern: string, interpretWildcards: boolean): RegExp {
  if (!interpretWildcards) {
    // Escape all regex special characters
    const escaped = pattern.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    return new RegExp(escaped, 'i');
  }

  // Escape all regex special characters except asterisks
  const escaped = pattern.replace(/[.+?^${}()|[\]\\]/g, '\\$&');

  // Replace asterisks with .* for wildcard matching
  const wildcardPattern = escaped.replace(/\*/g, '.*');

  return new RegExp(wildcardPattern, 'i');
}
