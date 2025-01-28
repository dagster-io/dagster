import {BodySmall, Box, Colors, Icon, IconName, MonoSmall} from '@dagster-io/ui-components';
import React from 'react';

import {createSelectionAutoCompleteProviderFromAttributeMap} from './SelectionAutoCompleteProviderFromAttributeMap';
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
    type: 'and' | 'or' | 'not' | 'parenthesis' | 'up-traversal' | 'down-traversal';
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

export type Suggestion = {
  text: string;
  jsx: React.ReactNode;
};

export const Operator = ({
  displayText,
  type,
}: {
  displayText: string;
  type: 'and' | 'or' | 'not' | 'parenthesis' | 'up-traversal' | 'down-traversal';
}) => {
  const icon: IconName | null = 'curly_braces';
  let label: string | null = null;

  switch (type) {
    case 'or':
    case 'not':
    case 'and': {
      label = displayText.toUpperCase();
      break;
    }
    case 'parenthesis': {
      label = 'Parenthesis';
      break;
    }
    case 'up-traversal': {
      label = 'Include upstream dependencies';
      break;
    }
    case 'down-traversal': {
      label = 'Include downstream dependencies';
      break;
    }
    default:
      assertUnreachable(type);
  }
  return <SuggestionJSXBase label={label} icon={icon} rightLabel={displayText} />;
};

export const AttributeValueTagSuggestion = ({
  key,
  value,
}: {
  key: string;
  value?: string | null | undefined;
}) => {
  const valueText = value ? `${key}=${value}` : key;
  return <SuggestionJSXBase label={valueText} />;
};

export const AttributeWithStringValueSuggestionJSX = ({
  icon,
  attributeName,
  value,
}: {
  icon?: IconName | null;
  attributeName: string;
  value: string;
}) => {
  return (
    <SuggestionJSXBase
      icon={icon}
      label={
        <Box flex={{direction: 'row', alignItems: 'center', gap: 2}}>
          <MonoSmall color={Colors.textLight()}>{attributeName}:</MonoSmall>
          <MonoSmall>{value}</MonoSmall>
        </Box>
      }
    />
  );
};

export const AttributeWithTagValueSuggestionJSX = ({
  icon,
  attributeName,
  tag,
}: {
  icon?: IconName | null;
  attributeName: string;
  tag: {
    key: string;
    value?: string | null | undefined;
  };
}) => {
  return (
    <SuggestionJSXBase
      icon={icon}
      label={
        <Box flex={{direction: 'row', alignItems: 'center', gap: 2}}>
          <MonoSmall color={Colors.textLight()}>{attributeName}:</MonoSmall>
          <MonoSmall>{tag.value ? `${tag.key}=${tag.value}` : tag.key}</MonoSmall>
        </Box>
      }
    />
  );
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
    <Box flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 24}}>
      <Box flex={{direction: 'row', alignItems: 'center', gap: 6}}>
        {icon ? <Icon name={icon} size={12} style={{margin: 0}} /> : null}
        <BodySmall>{label}</BodySmall>
      </Box>
      {rightLabel ? <MonoSmall>{rightLabel}</MonoSmall> : null}
    </Box>
  );
};

const FUNCTIONS = ['sinks', 'roots'] as const;

export const createProvider = <
  TAttributeMap extends {[key: string]: string[] | {key: string; value?: string}[]},
  TPrimaryAttributeKey extends keyof TAttributeMap,
>({
  attributeToIcon,
  primaryAttributeKey,
}: {
  attributeToIcon: Record<keyof TAttributeMap, IconName>;
  primaryAttributeKey: TPrimaryAttributeKey;
}): Omit<
  Parameters<
    typeof createSelectionAutoCompleteProviderFromAttributeMap<
      TAttributeMap,
      TPrimaryAttributeKey,
      'sinks' | 'roots'
    >
  >[0],
  'attributesMap'
> => ({
  primaryAttributeKey,
  functions: FUNCTIONS,
  doesValueIncludeQuery: ({value, query}) => {
    if (typeof value !== 'string') {
      // This is a tag
      return (
        value.key.includes(query) ||
        value.value?.includes(query) ||
        `${value.key}=${value.value ?? ''}`.includes(query)
      );
    }
    return value.includes(query);
  },
  createOperatorSuggestion: ({type, text, displayText}) => {
    return {
      text,
      jsx: <Operator type={type} displayText={displayText} />,
    };
  },
  createAttributeSuggestion: ({attribute, text}) => {
    const displayText = `${attribute as string}:`;
    const icon: IconName = attributeToIcon[attribute];
    let label;
    switch (attribute) {
      case primaryAttributeKey as string:
        label = 'Exact match';
        break;
      default:
        label = (attribute as string).replace(/_/g, ' ');
        label = label[0]!.toUpperCase() + label.slice(1);
    }
    return {
      text,
      jsx: <SuggestionJSXBase label={label} icon={icon} rightLabel={displayText} />,
    };
  },
  createAttributeValueSuggestion: ({attribute, value, textCallback}) => {
    if (typeof value !== 'string') {
      const valueText = value.value ? `"${value.key}"="${value.value}"` : `"${value.key}"`;
      return {
        text: textCallback ? textCallback(valueText) : valueText,
        jsx: <AttributeValueTagSuggestion key={value.key} value={value.value} />,
      };
    }
    return {
      text: textCallback ? textCallback(`"${value}"`) : `"${value}"`,
      jsx: <SuggestionJSXBase label={attribute as string} />,
    };
  },
  createFunctionSuggestion: ({func, text, options}) => {
    const displayText = options?.includeParenthesis ? `${func}()` : func;
    let icon: IconName;
    switch (func) {
      case 'roots':
        icon = 'arrow_upward';
        break;
      case 'sinks':
        icon = 'arrow_indent';
        break;
      default:
        assertUnreachable(func);
    }
    return {
      text,
      jsx: <SuggestionJSXBase label={func} icon={icon} rightLabel={displayText} />,
    };
  },
  createSubstringSuggestion: ({query, textCallback}) => {
    const text = `key_substring:"${query}"`;
    return {
      text: textCallback ? textCallback(text) : text,
      jsx: <SuggestionJSXBase label={`Asset key contains "${query}"`} rightLabel={text} />,
    };
  },
  createAttributeValueIncludeAttributeSuggestion: ({attribute, value, textCallback}) => {
    if (typeof value !== 'string') {
      if (value.value) {
        const text = `${attribute as string}:"${value.key}"="${value.value}"`;
        return {
          text: textCallback ? textCallback(text) : text,
          jsx: <SuggestionJSXBase label={attribute as string} />,
        };
      }
      const text = `${attribute as string}:"${value.key}"`;
      return {
        text: textCallback ? textCallback(text) : text,
        jsx: <SuggestionJSXBase label={attribute as string} />,
      };
    }
    const text = `${attribute as string}:"${value}"`;
    return {
      text: textCallback ? textCallback(text) : text,
      jsx: <SuggestionJSXBase label={attribute as string} />,
    };
  },
});
