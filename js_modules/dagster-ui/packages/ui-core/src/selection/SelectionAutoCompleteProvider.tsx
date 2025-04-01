import {
  BodySmall,
  Box,
  Colors,
  Icon,
  IconName,
  MiddleTruncate,
  MonoSmall,
} from '@dagster-io/ui-components';
import React from 'react';

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
   * @returns A single substring result that matches the query.
   */
  getSubstringResultMatchingQuery: (prop: {
    query: string;
    textCallback?: (value: string) => string;
  }) => Suggestion;

  /**
   * Retrieves a list of attribute values, including their corresponding attribute names, that match the provided query string.
   *
   * @param query - The search string to match attribute values against.
   * @param textCallback - An optional callback to transform the display text of each result. Used to insert spaces or double quotes if necessary depending on surrounding context
   * @returns An array of attribute values along with their attribute names that match the query.
   */
  getAttributeValueIncludeAttributeResultsMatchingQuery: (prop: {
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
}

export type Suggestion =
  | {
      text: string;
      jsx: React.ReactNode;
    }
  | {
      text: string;
      jsx: React.ReactNode;
      type: 'no-match';
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

export const FunctionSuggestionJSX = ({
  functionName,
  includeParenthesis,
}: {
  functionName: string;
  includeParenthesis?: boolean;
}) => {
  const fn = includeParenthesis ? `${functionName}()` : functionName;
  return <SuggestionJSXBase label={fn} />;
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
        <BodySmall style={{overflow: 'hidden'}}>{label}</BodySmall>
      </div>
      {rightLabel ? (
        <MonoSmall style={{textAlign: 'right', overflow: 'hidden'}}>{rightLabel}</MonoSmall>
      ) : null}
    </div>
  );
};

export const createProvider = <
  TAttributeMap extends {[key: string]: string[] | {key: string; value?: string}[]},
  TPrimaryAttributeKey extends keyof TAttributeMap,
>({
  attributeToIcon,
  primaryAttributeKey,
  attributesMap,
}: {
  attributeToIcon: Record<keyof TAttributeMap, IconName>;
  primaryAttributeKey: TPrimaryAttributeKey;
  attributesMap: TAttributeMap;
}): Omit<SelectionAutoCompleteProvider, 'useAutoComplete'> => {
  const functions = ['sinks', 'roots'] as const;
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

  function createAttributeSuggestion({
    attribute,
    text,
  }: {
    attribute: keyof TAttributeMap;
    text: string;
  }) {
    const displayText = `${attribute as string}:`;
    const icon: IconName = attributeToIcon[attribute];
    let label = (attribute as string).replace(/_/g, ' ');
    label = label[0]!.toUpperCase() + label.slice(1);
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

  function createAttributeValueSuggestion({
    value,
    textCallback,
  }: {
    value: TAttributeMap[keyof TAttributeMap][0];
    textCallback?: (text: string) => string;
  }) {
    if (typeof value !== 'string') {
      const valueText = value.value ? `"${value.key}"="${value.value}"` : `"${value.key}"`;
      return {
        text: textCallback ? textCallback(valueText) : valueText,
        jsx: <AttributeValueTagSuggestion tag={value} />,
      };
    }
    return {
      text: textCallback ? textCallback(`"${value}"`) : `"${value}"`,
      jsx: <SuggestionJSXBase label={<MiddleTruncate text={value} />} />,
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
    query,
    textCallback,
  }: {
    query: string;
    textCallback?: (text: string) => string;
  }) {
    const attribute = primaryAttributeKey as string;
    const text = `${attribute}:"*${query}*"`;
    let displayAttribute = attribute.replace(/_/g, ' ');
    displayAttribute = displayAttribute[0]!.toUpperCase() + displayAttribute.slice(1);
    const displayText = (
      <Box flex={{direction: 'row', alignItems: 'center', gap: 2}}>
        {displayAttribute} contains <MiddleTruncate text={query} />
      </Box>
    );
    return {
      text: textCallback ? textCallback(text) : text,
      jsx: <SuggestionJSXBase label={displayText} rightLabel={<MiddleTruncate text={text} />} />,
    };
  }

  function createAttributeValueIncludeAttributeSuggestion({
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
        text = `${attribute as string}:"${value.key}"="${value.value}"`;
        valueText = `${value.key}=${value.value}`;
      } else {
        text = `${attribute as string}:"${value.key}"`;
        valueText = value.key;
      }
    } else {
      text = `${attribute as string}:"${value}"`;
      valueText = value;
    }
    return {
      text: textCallback ? textCallback(text) : text,
      jsx: (
        <SuggestionJSXBase
          label={
            <Box flex={{direction: 'row', alignItems: 'center', gap: 2}}>
              <MonoSmall color={Colors.textLight()}>{attribute as string}:</MonoSmall>
              <MonoSmall style={{overflow: 'hidden'}}>
                <MiddleTruncate text={valueText} />
              </MonoSmall>
            </Box>
          }
        />
      ),
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
    getAttributeValueResultsMatchingQuery: ({attribute, query, textCallback}) => {
      const values = attributesMap[attribute as keyof typeof attributesMap];
      const results =
        values
          ?.filter((value) => doesValueIncludeQuery({value, query}))
          .map((value) =>
            createAttributeValueSuggestion({
              value,
              textCallback,
            }),
          ) ?? [];
      if (results.length === 0) {
        return [
          {
            text: '',
            jsx: (
              <BodySmall color={Colors.textLight()}>
                No match found for{' '}
                <MonoSmall color={Colors.textDefault()}>
                  {attribute}:&quot;{query}&quot;
                </MonoSmall>
              </BodySmall>
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
      return createSubstringSuggestion({query, textCallback});
    },
    getAttributeValueIncludeAttributeResultsMatchingQuery: ({query, textCallback}) => {
      return Object.keys(attributesMap).flatMap((attribute) => {
        return (
          attributesMap[attribute]
            ?.filter((value) => doesValueIncludeQuery({value, query}))
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
};
