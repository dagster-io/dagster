import {BodySmall, Box, Colors, Icon, IconName, MonoSmall} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {GraphQueryItem} from '../app/GraphQueryImpl';
import {useUpdatingRef} from '../hooks/useUpdatingRef';
import {createSelectionAutoComplete} from '../selection/SelectionAutoComplete';
import {
  BaseSuggestion,
  SelectionAutoCompleteProvider,
} from '../selection/SelectionAutoCompleteProvider';
import {createSelectionAutoCompleteProviderFromAttributeMap} from '../selection/SelectionAutoCompleteProviderFromAttributeMap';

const FUNCTIONS = ['sinks', 'roots'];

type Suggestion =
  | {
      text: string;
      displayText: string;
      type: 'function' | 'attribute-value' | 'attribute-with-value';
      attributeName?: string;
    }
  | {
      text: string;
      displayText: string;
      type: 'attribute';
      attributeName: 'name';
    }
  | {
      text: string;
      type: 'substring';
      value: string;
    };

export const useOpGraphSelectionAutoCompleteProvider = (
  items: GraphQueryItem[],
): SelectionAutoCompleteProvider<Suggestion> => {
  const attributesMap = useMemo(() => {
    const names = new Set<string>();
    items.forEach((item) => {
      names.add(item.name);
    });
    return {name: Array.from(names)};
  }, [items]);

  const attributesMapRef = useUpdatingRef(attributesMap);

  const baseProvider = useMemo(
    () =>
      createSelectionAutoCompleteProviderFromAttributeMap<
        typeof attributesMapRef.current,
        Suggestion
      >({
        attributesMapRef,
        functions: FUNCTIONS,
        doesValueIncludeQuery: (_attribute, value, query) => value.includes(query),
        createAttributeSuggestion: (attribute, textCallback) => {
          const text = `${attribute}:`;
          return {
            text: textCallback ? textCallback(text) : text,
            displayText: text,
            type: 'attribute',
            attributeName: attribute,
            nameBase: attribute === 'name',
          };
        },
        createAttributeValueSuggestion: (attribute, value, textCallback) => {
          const text = `"${value}"`;
          return {
            text: textCallback ? textCallback(text) : text,
            displayText: value,
            type: 'attribute-value',
            attributeName: attribute,
          };
        },
        createFunctionSuggestion: (func, textCallback, options) => {
          const text = options?.includeParenthesis ? `${func}()` : func;
          return {
            text: textCallback ? textCallback(text) : text,
            displayText: `${func}()`,
            type: 'function',
          };
        },
        createSubstringSuggestion: (query, textCallback) => {
          const text = `key_substring:"${query}"`;
          return {
            text: textCallback ? textCallback(text) : text,
            value: query,
            type: 'substring',
          };
        },
        createAttributeValueIncludeAttributeSuggestion: (attribute, value, textCallback) => {
          const text = `${attribute}:"${value}"`;
          return {
            text: textCallback ? textCallback(text) : text,
            displayText: `${attribute}:${value}`,
            type: 'attribute-with-value',
            attributeName: attribute,
          };
        },
      }),
    [attributesMapRef],
  );
  const selectionHint = useMemo(() => createSelectionAutoComplete(baseProvider), [baseProvider]);

  return useMemo(
    () => ({
      ...baseProvider,
      useAutoComplete: (line, cursorIndex) => {
        const autoCompleteResults = useMemo(
          () => selectionHint(line, cursorIndex),
          [line, cursorIndex],
        );
        return {
          autoCompleteResults,
          loading: false,
        };
      },
      renderResult: (suggestion) => <SuggestionItem suggestion={suggestion} />,
    }),
    [baseProvider, selectionHint],
  );
};

const SuggestionItem = ({suggestion}: {suggestion: Suggestion | BaseSuggestion}) => {
  let label;
  let icon: IconName | null = null;
  let value: string | null = 'displayText' in suggestion ? suggestion.displayText : null;
  if (suggestion.type === 'attribute' && suggestion.attributeName === 'name') {
    if (suggestion.text.endsWith('_substring:')) {
      icon = 'magnify_glass_checked';
      label = 'Contains match';
    } else {
      icon = 'magnify_glass';
      label = 'Exact match';
    }
  } else if (suggestion.type === 'down-traversal' || suggestion.type === 'up-traversal') {
    icon = 'curly_braces';
    label =
      suggestion.type === 'down-traversal'
        ? 'Include downstream dependencies'
        : 'Include upstream dependencies';
  } else if (suggestion.type === 'logical_operator') {
    icon = 'curly_braces';
    label = suggestion.displayText.toUpperCase();
  } else if (suggestion.type === 'parenthesis') {
    icon = 'curly_braces';
    label = 'Parenthesis';
    value = suggestion.text;
  } else if (suggestion.type === 'function') {
    if (suggestion.displayText === 'roots()') {
      label = 'Roots';
      icon = 'arrow_upward';
    } else if (suggestion.displayText === 'sinks()') {
      label = 'Sinks';
      icon = 'arrow_indent';
    }
  } else if (suggestion.type === 'attribute-with-value') {
    const firstColon = suggestion.displayText.indexOf(':');
    const attributeKey = suggestion.displayText.slice(0, firstColon);
    const attributeValue = suggestion.displayText.slice(firstColon + 1);
    label = (
      <Box flex={{direction: 'row', alignItems: 'center', gap: 2}}>
        <MonoSmall color={Colors.textLight()}>{attributeKey}:</MonoSmall>
        <MonoSmall>{attributeValue}</MonoSmall>
      </Box>
    );
    value = null;
  } else if (suggestion.type === 'attribute-value') {
    label = suggestion.displayText;
    value = null;
  } else if (suggestion.type === 'substring') {
    label = `Step name contains "${suggestion.value}"`;
    value = `name_substring:${suggestion.value}`;
  }
  return (
    <Box flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 24}}>
      <Box flex={{direction: 'row', alignItems: 'center', gap: 6}}>
        {icon ? <Icon name={icon} size={12} style={{margin: 0}} /> : null}
        <BodySmall>{label}</BodySmall>
      </Box>
      <MonoSmall>{value}</MonoSmall>
    </Box>
  );
};
