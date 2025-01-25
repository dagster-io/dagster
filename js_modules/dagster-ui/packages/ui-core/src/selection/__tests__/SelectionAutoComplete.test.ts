import {createSelectionAutoComplete} from '../SelectionAutoComplete';
import {createSelectionAutoCompleteProviderFromAttributeMap} from '../SelectionAutoCompleteProviderFromAttributeMap';

describe('createAssetSelectionHint', () => {
  const attributesMap = {
    key: ['asset1', 'asset2', 'asset3'],
    tag: ['tag1', 'tag2', 'tag3'],
    owner: ['marco@dagsterlabs.com', 'team:frontend'],
    group: ['group1', 'group2'],
    kind: ['kind1', 'kind2'],
    code_location: ['repo1@location1', 'repo2@location2'],
  };
  const provider = createSelectionAutoCompleteProviderFromAttributeMap<
    typeof attributesMap,
    'key',
    any
  >({
    nameBase: 'key',
    attributesMapRef: {current: attributesMap},
    functions: ['sinks', 'roots'],
    doesValueIncludeQuery: (_attribute, value, query) => value.includes(query),
    createAttributeSuggestion: (attribute, textCallback) => {
      const text = `${attribute}:`;
      return {
        text: textCallback ? textCallback(text) : text,
        displayText: text,
        type: 'attribute',
        attributeName: attribute,
        nameBase: attribute === 'key',
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
        attributeName: 'key_substring',
        text: textCallback ? textCallback(text) : text,
        displayText: `key_substring:${query}`,
        type: 'attribute-with-value',
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
  });
  const selectionHint = createSelectionAutoComplete(provider);

  function testAutocomplete(testString: string) {
    const cursorIndex = testString.indexOf('|');
    const string = testString.replace('|', '');

    const hints = selectionHint(string, cursorIndex);

    return {
      list: hints?.list,
      from: hints?.from,
      to: hints?.to,
    };
  }

  it('should suggest asset names after typing key_substring:', () => {
    // cursorIndex 14
    expect(testAutocomplete('key_substring:|')).toEqual({
      list: [
        {
          text: '"asset1"',
          displayText: 'asset1',
          type: 'attribute-value',
          attributeName: 'key_substring',
        },
        {
          text: '"asset2"',
          displayText: 'asset2',
          type: 'attribute-value',
          attributeName: 'key_substring',
        },
        {
          text: '"asset3"',
          displayText: 'asset3',
          type: 'attribute-value',
          attributeName: 'key_substring',
        },
      ],
      from: 14, // cursor location
      to: 14, // cursor location
    });
  });

  it('should suggest owners after typing owner:', () => {
    expect(testAutocomplete('owner:|')).toEqual({
      list: [
        {
          text: '"marco@dagsterlabs.com"',
          displayText: 'marco@dagsterlabs.com',
          type: 'attribute-value',
          attributeName: 'owner',
        },
        {
          text: '"team:frontend"',
          displayText: 'team:frontend',
          type: 'attribute-value',
          attributeName: 'owner',
        },
      ],
      from: 6, // cursor location
      to: 6, // cursor location
    });
  });

  it('should suggest tag names after typing tag:', () => {
    expect(testAutocomplete('tag:|')).toEqual({
      list: [
        {text: '"tag1"', displayText: 'tag1', type: 'attribute-value', attributeName: 'tag'},
        {text: '"tag2"', displayText: 'tag2', type: 'attribute-value', attributeName: 'tag'},
        {text: '"tag3"', displayText: 'tag3', type: 'attribute-value', attributeName: 'tag'},
      ],
      from: 4, // cursor location
      to: 4, // cursor location
    });

    expect(testAutocomplete('tag:"|"')).toEqual({
      list: [
        {text: '"tag1"', displayText: 'tag1', type: 'attribute-value', attributeName: 'tag'},
        {text: '"tag2"', displayText: 'tag2', type: 'attribute-value', attributeName: 'tag'},
        {text: '"tag3"', displayText: 'tag3', type: 'attribute-value', attributeName: 'tag'},
      ],
      from: 4, // cursor location
      to: 6, // cursor location
    });
  });

  it('should suggest logical operators after an expression', () => {
    expect(testAutocomplete('key:"asset1" |')).toEqual({
      list: [
        {text: ' and ', displayText: 'and', type: 'logical_operator'},
        {text: ' or ', displayText: 'or', type: 'logical_operator'},
        {text: '+', displayText: '+', type: 'down-traversal'},
      ],
      from: 13, // cursor location
      to: 13, // cursor location
    });

    expect(testAutocomplete('key:"asset1"|')).toEqual({
      list: [
        {text: ' and ', displayText: 'and', type: 'logical_operator'},
        {text: ' or ', displayText: 'or', type: 'logical_operator'},
        {text: '+', displayText: '+', type: 'down-traversal'},
      ],
      from: 12, // cursor location
      to: 12, // cursor location
    });
  });

  it('should filter suggestions based on partial input', () => {
    expect(testAutocomplete('owner:marco|')).toEqual({
      list: [
        {
          text: '"marco@dagsterlabs.com"',
          displayText: 'marco@dagsterlabs.com',
          type: 'attribute-value',
          attributeName: 'owner',
        },
      ],
      from: 6, // start of value "marco"
      to: 11, // end of value
    });
  });

  it('should suggest possible keywords', () => {
    // empty case
    expect(testAutocomplete('|')).toEqual({
      list: [
        {
          displayText: 'key:',
          text: 'key:',
          type: 'attribute',
          attributeName: 'key',
          nameBase: true,
        },
        {
          displayText: 'tag:',
          text: 'tag:',
          type: 'attribute',
          attributeName: 'tag',
          nameBase: false,
        },
        {
          displayText: 'owner:',
          text: 'owner:',
          type: 'attribute',
          attributeName: 'owner',
          nameBase: false,
        },
        {
          displayText: 'group:',
          text: 'group:',
          type: 'attribute',
          attributeName: 'group',
          nameBase: false,
        },
        {
          displayText: 'kind:',
          text: 'kind:',
          type: 'attribute',
          attributeName: 'kind',
          nameBase: false,
        },
        {
          displayText: 'code_location:',
          text: 'code_location:',
          type: 'attribute',
          attributeName: 'code_location',
          nameBase: false,
        },
        {displayText: 'sinks()', text: 'sinks()', type: 'function'},
        {displayText: 'roots()', text: 'roots()', type: 'function'},
        {displayText: 'not', text: 'not ', type: 'logical_operator'},
        {displayText: '+', text: '+', type: 'up-traversal'},
        {displayText: '(', text: '()', type: 'parenthesis'},
      ],
      from: 0, // cursor location
      to: 0, // cursor location
    });

    // filtered case
    expect(testAutocomplete('o|')).toEqual({
      list: [
        {
          displayText: 'key_substring:o',
          text: 'key_substring:"o"',
          type: 'attribute-with-value',
          attributeName: 'key_substring',
        },
        {
          displayText: 'owner:',
          text: 'owner:',
          type: 'attribute',
          attributeName: 'owner',
          nameBase: false,
        },
        {
          displayText: 'owner:marco@dagsterlabs.com',
          text: 'owner:"marco@dagsterlabs.com"',
          type: 'attribute-with-value',
          attributeName: 'owner',
        },
        {
          displayText: 'owner:team:frontend',
          text: 'owner:"team:frontend"',
          type: 'attribute-with-value',
          attributeName: 'owner',
        },
        {
          displayText: 'group:group1',
          text: 'group:"group1"',
          type: 'attribute-with-value',
          attributeName: 'group',
        },
        {
          displayText: 'group:group2',
          text: 'group:"group2"',
          type: 'attribute-with-value',
          attributeName: 'group',
        },
        {
          displayText: 'code_location:repo1@location1',
          text: 'code_location:"repo1@location1"',
          type: 'attribute-with-value',
          attributeName: 'code_location',
        },
        {
          displayText: 'code_location:repo2@location2',
          text: 'code_location:"repo2@location2"',
          type: 'attribute-with-value',
          attributeName: 'code_location',
        },
      ],
      from: 0, // start of input
      to: 1, // cursor location
    });
  });

  it('should handle traversal operators correctly', () => {
    expect(testAutocomplete('+|')).toEqual({
      list: [
        {
          displayText: 'key:',
          text: 'key:',
          type: 'attribute',
          attributeName: 'key',
          nameBase: true,
        },
        {
          displayText: 'tag:',
          text: 'tag:',
          type: 'attribute',
          attributeName: 'tag',
          nameBase: false,
        },
        {
          displayText: 'owner:',
          text: 'owner:',
          type: 'attribute',
          attributeName: 'owner',
          nameBase: false,
        },
        {
          displayText: 'group:',
          text: 'group:',
          type: 'attribute',
          attributeName: 'group',
          nameBase: false,
        },
        {
          attributeName: 'kind',
          displayText: 'kind:',
          nameBase: false,
          text: 'kind:',
          type: 'attribute',
        },
        {
          displayText: 'code_location:',
          text: 'code_location:',
          type: 'attribute',
          attributeName: 'code_location',
          nameBase: false,
        },
        {displayText: 'sinks()', text: 'sinks()', type: 'function'},
        {displayText: 'roots()', text: 'roots()', type: 'function'},
        {displayText: '(', text: '()', type: 'parenthesis'},
      ],
      from: 1, // cursor location
      to: 1, // cursor location
    });

    expect(testAutocomplete('* |')).toEqual({
      from: 2,
      list: [
        {displayText: 'and', text: ' and ', type: 'logical_operator'},
        {displayText: 'or', text: ' or ', type: 'logical_operator'},
      ],
      to: 2,
    });

    expect(testAutocomplete('+ |')).toEqual({
      from: 2,
      list: [
        {
          displayText: 'key:',
          text: 'key:',
          type: 'attribute',
          attributeName: 'key',
          nameBase: true,
        },
        {
          displayText: 'tag:',
          text: 'tag:',
          type: 'attribute',
          attributeName: 'tag',
          nameBase: false,
        },
        {
          displayText: 'owner:',
          text: 'owner:',
          type: 'attribute',
          attributeName: 'owner',
          nameBase: false,
        },
        {
          displayText: 'group:',
          text: 'group:',
          type: 'attribute',
          attributeName: 'group',
          nameBase: false,
        },
        {
          displayText: 'kind:',
          text: 'kind:',
          type: 'attribute',
          attributeName: 'kind',
          nameBase: false,
        },
        {
          displayText: 'code_location:',
          text: 'code_location:',
          type: 'attribute',
          attributeName: 'code_location',
          nameBase: false,
        },
        {displayText: 'sinks()', text: 'sinks()', type: 'function'},
        {displayText: 'roots()', text: 'roots()', type: 'function'},
        {displayText: 'not', text: 'not ', type: 'logical_operator'},
        {displayText: '(', text: '()', type: 'parenthesis'},
      ],
      to: 2,
    });

    expect(testAutocomplete('+|')).toEqual({
      from: 1,
      list: [
        {
          displayText: 'key:',
          text: 'key:',
          type: 'attribute',
          attributeName: 'key',
          nameBase: true,
        },
        {
          displayText: 'tag:',
          text: 'tag:',
          type: 'attribute',
          attributeName: 'tag',
          nameBase: false,
        },
        {
          displayText: 'owner:',
          text: 'owner:',
          type: 'attribute',
          attributeName: 'owner',
          nameBase: false,
        },
        {
          displayText: 'group:',
          text: 'group:',
          type: 'attribute',
          attributeName: 'group',
          nameBase: false,
        },
        {
          attributeName: 'kind',
          displayText: 'kind:',
          nameBase: false,
          text: 'kind:',
          type: 'attribute',
        },
        {
          displayText: 'code_location:',
          text: 'code_location:',
          type: 'attribute',
          attributeName: 'code_location',
          nameBase: false,
        },
        {displayText: 'sinks()', text: 'sinks()', type: 'function'},
        {displayText: 'roots()', text: 'roots()', type: 'function'},
        {displayText: '(', text: '()', type: 'parenthesis'},
      ],
      to: 1,
    });
  });

  it('should suggest code locations after typing code_location:', () => {
    expect(testAutocomplete('code_location:|')).toEqual({
      list: [
        {
          text: '"repo1@location1"',
          displayText: 'repo1@location1',
          type: 'attribute-value',
          attributeName: 'code_location',
        },
        {
          text: '"repo2@location2"',
          displayText: 'repo2@location2',
          type: 'attribute-value',
          attributeName: 'code_location',
        },
      ],
      from: 14,
      to: 14,
    });
  });

  it('should handle incomplete "not" expressions', () => {
    expect(testAutocomplete('not|')).toEqual({
      list: [
        {
          text: ' key:',
          displayText: 'key:',
          type: 'attribute',
          attributeName: 'key',
          nameBase: true,
        },
        {
          text: ' tag:',
          displayText: 'tag:',
          type: 'attribute',
          attributeName: 'tag',
          nameBase: false,
        },
        {
          text: ' owner:',
          displayText: 'owner:',
          type: 'attribute',
          attributeName: 'owner',
          nameBase: false,
        },
        {
          text: ' group:',
          displayText: 'group:',
          type: 'attribute',
          attributeName: 'group',
          nameBase: false,
        },
        {
          text: ' kind:',
          displayText: 'kind:',
          type: 'attribute',
          attributeName: 'kind',
          nameBase: false,
        },
        {
          text: ' code_location:',
          displayText: 'code_location:',
          type: 'attribute',
          attributeName: 'code_location',
          nameBase: false,
        },
        {text: ' sinks()', displayText: 'sinks()', type: 'function'},
        {text: ' roots()', displayText: 'roots()', type: 'function'},
        {text: ' +', displayText: '+', type: 'up-traversal'},
        {text: ' ()', displayText: '(', type: 'parenthesis'},
      ],
      from: 3, // cursor location
      to: 3, // cursor location
    });

    expect(testAutocomplete('not |')).toEqual({
      list: [
        {
          text: 'key:',
          displayText: 'key:',
          type: 'attribute',
          attributeName: 'key',
          nameBase: true,
        },
        {
          text: 'tag:',
          displayText: 'tag:',
          type: 'attribute',
          attributeName: 'tag',
          nameBase: false,
        },
        {
          text: 'owner:',
          displayText: 'owner:',
          type: 'attribute',
          attributeName: 'owner',
          nameBase: false,
        },
        {
          text: 'group:',
          displayText: 'group:',
          type: 'attribute',
          attributeName: 'group',
          nameBase: false,
        },
        {
          attributeName: 'kind',
          displayText: 'kind:',
          nameBase: false,
          text: 'kind:',
          type: 'attribute',
        },
        {
          text: 'code_location:',
          displayText: 'code_location:',
          type: 'attribute',
          attributeName: 'code_location',
          nameBase: false,
        },
        {text: 'sinks()', displayText: 'sinks()', type: 'function'},
        {text: 'roots()', displayText: 'roots()', type: 'function'},
        {text: '+', displayText: '+', type: 'up-traversal'},
        {text: '()', displayText: '(', type: 'parenthesis'},
      ],
      from: 4, // cursor location
      to: 4, // cursor location
    });
  });

  it('should handle incomplete and expressions', () => {
    expect(testAutocomplete('key:"asset1" and |')).toEqual({
      list: [
        {
          text: 'key:',
          displayText: 'key:',
          type: 'attribute',
          attributeName: 'key',
          nameBase: true,
        },
        {
          text: 'tag:',
          displayText: 'tag:',
          type: 'attribute',
          attributeName: 'tag',
          nameBase: false,
        },
        {
          text: 'owner:',
          displayText: 'owner:',
          type: 'attribute',
          attributeName: 'owner',
          nameBase: false,
        },
        {
          text: 'group:',
          displayText: 'group:',
          type: 'attribute',
          attributeName: 'group',
          nameBase: false,
        },
        {
          attributeName: 'kind',
          displayText: 'kind:',
          nameBase: false,
          text: 'kind:',
          type: 'attribute',
        },
        {
          text: 'code_location:',
          displayText: 'code_location:',
          type: 'attribute',
          attributeName: 'code_location',
          nameBase: false,
        },
        {text: 'sinks()', displayText: 'sinks()', type: 'function'},
        {text: 'roots()', displayText: 'roots()', type: 'function'},
        {text: 'not ', displayText: 'not', type: 'logical_operator'},
        {text: '+', displayText: '+', type: 'up-traversal'},
        {text: '()', displayText: '(', type: 'parenthesis'},
      ],
      from: 17, // cursor location
      to: 17, // cursor location
    });
  });

  it('should handle incomplete or expressions', () => {
    expect(testAutocomplete('key:"asset1" or |')).toEqual({
      list: [
        {
          text: 'key:',
          displayText: 'key:',
          type: 'attribute',
          attributeName: 'key',
          nameBase: true,
        },
        {
          text: 'tag:',
          displayText: 'tag:',
          type: 'attribute',
          attributeName: 'tag',
          nameBase: false,
        },
        {
          text: 'owner:',
          displayText: 'owner:',
          type: 'attribute',
          attributeName: 'owner',
          nameBase: false,
        },
        {
          text: 'group:',
          displayText: 'group:',
          type: 'attribute',
          attributeName: 'group',
          nameBase: false,
        },
        {
          attributeName: 'kind',
          displayText: 'kind:',
          nameBase: false,
          text: 'kind:',
          type: 'attribute',
        },
        {
          text: 'code_location:',
          displayText: 'code_location:',
          type: 'attribute',
          attributeName: 'code_location',
          nameBase: false,
        },
        {text: 'sinks()', displayText: 'sinks()', type: 'function'},
        {text: 'roots()', displayText: 'roots()', type: 'function'},
        {text: 'not ', displayText: 'not', type: 'logical_operator'},
        {text: '+', displayText: '+', type: 'up-traversal'},
        {text: '()', displayText: '(', type: 'parenthesis'},
      ],
      from: 16, // cursor location
      to: 16, // cursor location
    });
  });

  it('should handle incomplete quoted strings gracefully', () => {
    expect(testAutocomplete('key:"asse|')).toEqual({
      list: [
        {
          displayText: 'asset1',
          text: '"asset1"',
          type: 'attribute-value',
          attributeName: 'key',
        },
        {
          displayText: 'asset2',
          text: '"asset2"',
          type: 'attribute-value',
          attributeName: 'key',
        },
        {
          displayText: 'asset3',
          text: '"asset3"',
          type: 'attribute-value',
          attributeName: 'key',
        },
      ],
      from: 4, // start of value
      to: 9, // end of value
    });
  });

  it('should handle incomplete or expression within function', () => {
    expect(
      testAutocomplete('sinks(key_substring:"FIVETRAN/google_ads/ad_group_history" or |)'),
    ).toEqual({
      list: [
        {
          text: 'key:',
          displayText: 'key:',
          type: 'attribute',
          attributeName: 'key',
          nameBase: true,
        },
        {
          text: 'tag:',
          displayText: 'tag:',
          type: 'attribute',
          attributeName: 'tag',
          nameBase: false,
        },
        {
          text: 'owner:',
          displayText: 'owner:',
          type: 'attribute',
          attributeName: 'owner',
          nameBase: false,
        },
        {
          text: 'group:',
          displayText: 'group:',
          type: 'attribute',
          attributeName: 'group',
          nameBase: false,
        },
        {
          attributeName: 'kind',
          displayText: 'kind:',
          nameBase: false,
          text: 'kind:',
          type: 'attribute',
        },
        {
          text: 'code_location:',
          displayText: 'code_location:',
          type: 'attribute',
          attributeName: 'code_location',
          nameBase: false,
        },
        {text: 'sinks()', displayText: 'sinks()', type: 'function'},
        {text: 'roots()', displayText: 'roots()', type: 'function'},
        {text: 'not ', displayText: 'not', type: 'logical_operator'},
        {text: '+', displayText: '+', type: 'up-traversal'},
        {text: '()', displayText: '(', type: 'parenthesis'},
      ],
      from: 62, // cursor location
      to: 62, // cursor location
    });
  });

  it('should handle incomplete or expression within function with cursor right after the "or"', () => {
    expect(
      testAutocomplete('sinks(key_substring:"FIVETRAN/google_ads/ad_group_history" or|)'),
    ).toEqual({
      list: [
        // Inserts a space before the string
        {
          text: ' key:',
          displayText: 'key:',
          type: 'attribute',
          attributeName: 'key',
          nameBase: true,
        },
        {
          text: ' tag:',
          displayText: 'tag:',
          type: 'attribute',
          attributeName: 'tag',
          nameBase: false,
        },
        {
          text: ' owner:',
          displayText: 'owner:',
          type: 'attribute',
          attributeName: 'owner',
          nameBase: false,
        },
        {
          attributeName: 'group',
          displayText: 'group:',
          nameBase: false,
          text: ' group:',
          type: 'attribute',
        },
        {
          attributeName: 'kind',
          displayText: 'kind:',
          nameBase: false,
          text: ' kind:',
          type: 'attribute',
        },
        {
          text: ' code_location:',
          displayText: 'code_location:',
          type: 'attribute',
          attributeName: 'code_location',
          nameBase: false,
        },
        {text: ' sinks()', displayText: 'sinks()', type: 'function'},
        {text: ' roots()', displayText: 'roots()', type: 'function'},
        {text: ' not ', displayText: 'not', type: 'logical_operator'},
        {text: ' +', displayText: '+', type: 'up-traversal'},
        {text: ' ()', displayText: '(', type: 'parenthesis'},
      ],
      from: 61, // cursor location
      to: 61, // cursor location
    });
  });

  it('should suggest tag values to the right of colon of an attribute expression inside of an IncompleteAttributeExpression, OrExpression, and ParenthesizedExpression', () => {
    expect(
      testAutocomplete(
        'sinks(key_substring:"FIVETRAN/google_ads/ad_group_history" or key_substring:|)',
      ),
    ).toEqual({
      list: [
        {
          text: '"asset1"',
          displayText: 'asset1',
          type: 'attribute-value',
          attributeName: 'key_substring',
        },
        {
          text: '"asset2"',
          displayText: 'asset2',
          type: 'attribute-value',
          attributeName: 'key_substring',
        },
        {
          text: '"asset3"',
          displayText: 'asset3',
          type: 'attribute-value',
          attributeName: 'key_substring',
        },
      ],
      from: 76, // cursor location
      to: 76, // cursor location
    });
  });

  it('suggestions after downtraversal "+"', () => {
    expect(testAutocomplete('key:"value"+|')).toEqual({
      list: [
        {text: ' and ', displayText: 'and', type: 'logical_operator'},
        {text: ' or ', displayText: 'or', type: 'logical_operator'},
      ],
      from: 12, // cursor location
      to: 12, // cursor location
    });

    // UpAndDownTraversal
    expect(testAutocomplete('+key:"value"|+')).toEqual({
      list: [
        {text: ' and ', displayText: 'and', type: 'logical_operator'},
        {text: ' or ', displayText: 'or', type: 'logical_operator'},
        {text: '+', displayText: '+', type: 'down-traversal'},
      ],
      from: 12, // cursor location
      to: 12, // cursor location
    });

    // DownTraversal
    expect(testAutocomplete('key:"value"|+')).toEqual({
      list: [
        {text: ' and ', displayText: 'and', type: 'logical_operator'},
        {text: ' or ', displayText: 'or', type: 'logical_operator'},
        {text: '+', displayText: '+', type: 'down-traversal'},
      ],
      from: 11, // cursor location
      to: 11, // cursor location
    });
  });

  it('suggestions after IncompleteOrExpression chain', () => {
    expect(
      testAutocomplete('key:"test" or key_substring:"FIVETRAN/google_ads/ad_group_history"+ or |'),
    ).toEqual({
      list: [
        {
          text: 'key:',
          displayText: 'key:',
          type: 'attribute',
          attributeName: 'key',
          nameBase: true,
        },
        {
          text: 'tag:',
          displayText: 'tag:',
          type: 'attribute',
          attributeName: 'tag',
          nameBase: false,
        },
        {
          text: 'owner:',
          displayText: 'owner:',
          type: 'attribute',
          attributeName: 'owner',
          nameBase: false,
        },
        {
          text: 'group:',
          displayText: 'group:',
          type: 'attribute',
          attributeName: 'group',
          nameBase: false,
        },
        {
          text: 'kind:',
          displayText: 'kind:',
          type: 'attribute',
          attributeName: 'kind',
          nameBase: false,
        },
        {
          text: 'code_location:',
          displayText: 'code_location:',
          type: 'attribute',
          attributeName: 'code_location',
          nameBase: false,
        },
        {text: 'sinks()', displayText: 'sinks()', type: 'function'},
        {text: 'roots()', displayText: 'roots()', type: 'function'},
        {text: 'not ', displayText: 'not', type: 'logical_operator'},
        {text: '+', displayText: '+', type: 'up-traversal'},
        {text: '()', displayText: '(', type: 'parenthesis'},
      ],
      from: 71, // cursor position
      to: 71, // cursor position
    });
  });

  it('suggestions inside parenthesized expression', () => {
    expect(testAutocomplete('(|)')).toEqual({
      list: [
        {
          text: 'key:',
          displayText: 'key:',
          type: 'attribute',
          attributeName: 'key',
          nameBase: true,
        },
        {
          text: 'tag:',
          displayText: 'tag:',
          type: 'attribute',
          attributeName: 'tag',
          nameBase: false,
        },
        {
          text: 'owner:',
          displayText: 'owner:',
          type: 'attribute',
          attributeName: 'owner',
          nameBase: false,
        },
        {
          text: 'group:',
          displayText: 'group:',
          type: 'attribute',
          attributeName: 'group',
          nameBase: false,
        },
        {
          text: 'kind:',
          displayText: 'kind:',
          type: 'attribute',
          attributeName: 'kind',
          nameBase: false,
        },
        {
          text: 'code_location:',
          displayText: 'code_location:',
          type: 'attribute',
          attributeName: 'code_location',
          nameBase: false,
        },
        {text: 'sinks()', displayText: 'sinks()', type: 'function'},
        {text: 'roots()', displayText: 'roots()', type: 'function'},
        {text: 'not ', displayText: 'not', type: 'logical_operator'},
        {text: '+', displayText: '+', type: 'up-traversal'},
        {text: '()', displayText: '(', type: 'parenthesis'},
      ],
      from: 1, // cursor location
      to: 1, // cursor location
    });
  });

  it('suggestions outside parenthesized expression before', () => {
    expect(testAutocomplete('|()')).toEqual({
      list: [
        {
          text: 'key:',
          displayText: 'key:',
          type: 'attribute',
          attributeName: 'key',
          nameBase: true,
        },
        {
          text: 'tag:',
          displayText: 'tag:',
          type: 'attribute',
          attributeName: 'tag',
          nameBase: false,
        },
        {
          text: 'owner:',
          displayText: 'owner:',
          type: 'attribute',
          attributeName: 'owner',
          nameBase: false,
        },
        {
          text: 'group:',
          displayText: 'group:',
          type: 'attribute',
          attributeName: 'group',
          nameBase: false,
        },
        {
          text: 'kind:',
          displayText: 'kind:',
          type: 'attribute',
          attributeName: 'kind',
          nameBase: false,
        },
        {
          text: 'code_location:',
          displayText: 'code_location:',
          type: 'attribute',
          attributeName: 'code_location',
          nameBase: false,
        },
        {text: 'sinks()', displayText: 'sinks()', type: 'function'},
        {text: 'roots()', displayText: 'roots()', type: 'function'},
        {text: 'not ', displayText: 'not', type: 'logical_operator'},
        {text: '+', displayText: '+', type: 'up-traversal'},
        {text: '()', displayText: '(', type: 'parenthesis'},
      ],
      from: 0, // cursor position
      to: 0, // cursor position
    });
  });

  it('suggestions outside parenthesized expression after', () => {
    expect(testAutocomplete('()|')).toEqual({
      list: [
        {text: ' and ', displayText: 'and', type: 'logical_operator'},
        {text: ' or ', displayText: 'or', type: 'logical_operator'},
        {text: '+', displayText: '+', type: 'down-traversal'},
      ],
      from: 2, // cursor position
      to: 2, // cursor position
    });
  });

  it('suggestions within parenthesized expression', () => {
    expect(testAutocomplete('(tag:"dagster/kind/dlt"|)')).toEqual({
      list: [
        {text: ' and ', displayText: 'and', type: 'logical_operator'},
        {text: ' or ', displayText: 'or', type: 'logical_operator'},
        {text: '+', displayText: '+', type: 'down-traversal'},
      ],
      from: 23, // cursor position
      to: 23, // cursor position
    });

    expect(testAutocomplete('sinks(key_substring:"set" or key_substring:"asset"|)')).toEqual({
      list: [
        {text: ' and ', displayText: 'and', type: 'logical_operator'},
        {text: ' or ', displayText: 'or', type: 'logical_operator'},
        {text: '+', displayText: '+', type: 'down-traversal'},
      ],
      from: 50, // cursor position
      to: 50, // cursor position
    });

    expect(testAutocomplete('sinks(key_substring:"asset" or key_substring:"s|et2")')).toEqual({
      list: [
        {
          text: '"asset2"',
          displayText: 'asset2',
          type: 'attribute-value',
          attributeName: 'key_substring',
        },
      ],
      from: 45, // start of value
      to: 51, // end of value
    });

    expect(testAutocomplete('sinks(key_substring:"sset1"| or key_substring:"set")')).toEqual({
      list: [
        {text: ' and ', displayText: 'and', type: 'logical_operator'},
        {text: ' or ', displayText: 'or', type: 'logical_operator'},
        {text: '+', displayText: '+', type: 'down-traversal'},
      ],
      from: 27, // cursor position
      to: 27, // cursor position
    });
  });

  it('makes suggestions around traversals', () => {
    expect(testAutocomplete('sinks()+2|')).toEqual({
      list: [
        {text: ' and ', displayText: 'and', type: 'logical_operator'},
        {text: ' or ', displayText: 'or', type: 'logical_operator'},
      ],
      from: 9, // start of value
      to: 9, // end of value
    });

    expect(testAutocomplete('sinks()+|+')).toEqual({
      list: [
        {text: ' and ', displayText: 'and', type: 'logical_operator'},
        {text: ' or ', displayText: 'or', type: 'logical_operator'},
      ],
      from: 8, // start of value
      to: 8, // end of value
    });

    expect(testAutocomplete('|2+sinks()+2')).toEqual({
      list: [{text: '()', displayText: '(', type: 'parenthesis'}],
      from: 0, // start of value
      to: 0, // end of value
    });

    expect(testAutocomplete('2|+sinks()+2')).toEqual({
      list: [{text: '()', displayText: '(', type: 'parenthesis'}],
      from: 1, // start of value
      to: 1, // end of value
    });
  });

  it('makes suggestions for IncompleteExpression inside of the ParenthesizedExpression', () => {
    expect(testAutocomplete('(key:tag and |)')).toEqual({
      list: [
        {
          displayText: 'key:',
          text: 'key:',
          type: 'attribute',
          attributeName: 'key',
          nameBase: true,
        },
        {
          displayText: 'tag:',
          text: 'tag:',
          type: 'attribute',
          attributeName: 'tag',
          nameBase: false,
        },
        {
          displayText: 'owner:',
          text: 'owner:',
          type: 'attribute',
          attributeName: 'owner',
          nameBase: false,
        },
        {
          displayText: 'group:',
          text: 'group:',
          type: 'attribute',
          attributeName: 'group',
          nameBase: false,
        },
        {
          displayText: 'kind:',
          text: 'kind:',
          type: 'attribute',
          attributeName: 'kind',
          nameBase: false,
        },
        {
          displayText: 'code_location:',
          text: 'code_location:',
          type: 'attribute',
          attributeName: 'code_location',
          nameBase: false,
        },
        {displayText: 'sinks()', text: 'sinks()', type: 'function'},
        {displayText: 'roots()', text: 'roots()', type: 'function'},
        {displayText: 'not', text: 'not ', type: 'logical_operator'},
        {displayText: '+', text: '+', type: 'up-traversal'},
        {displayText: '(', text: '()', type: 'parenthesis'},
      ],
      from: 13,
      to: 13,
    });

    expect(testAutocomplete('(key:tag and|)')).toEqual({
      list: [
        {
          displayText: 'key:',
          text: ' key:',
          type: 'attribute',
          attributeName: 'key',
          nameBase: true,
        },
        {
          displayText: 'tag:',
          text: ' tag:',
          type: 'attribute',
          attributeName: 'tag',
          nameBase: false,
        },
        {
          displayText: 'owner:',
          text: ' owner:',
          type: 'attribute',
          attributeName: 'owner',
          nameBase: false,
        },
        {
          displayText: 'group:',
          text: ' group:',
          type: 'attribute',
          attributeName: 'group',
          nameBase: false,
        },
        {
          displayText: 'kind:',
          text: ' kind:',
          type: 'attribute',
          attributeName: 'kind',
          nameBase: false,
        },
        {
          displayText: 'code_location:',
          text: ' code_location:',
          type: 'attribute',
          attributeName: 'code_location',
          nameBase: false,
        },
        {displayText: 'sinks()', text: ' sinks()', type: 'function'},
        {displayText: 'roots()', text: ' roots()', type: 'function'},
        {displayText: 'not', text: ' not ', type: 'logical_operator'},
        {displayText: '+', text: ' +', type: 'up-traversal'},
        {displayText: '(', text: ' ()', type: 'parenthesis'},
      ],
      from: 12,
      to: 12,
    });

    expect(testAutocomplete('(key:tag and| )')).toEqual({
      list: [
        {
          displayText: 'key:',
          text: ' key:',
          type: 'attribute',
          attributeName: 'key',
          nameBase: true,
        },
        {
          displayText: 'tag:',
          text: ' tag:',
          type: 'attribute',
          attributeName: 'tag',
          nameBase: false,
        },
        {
          displayText: 'owner:',
          text: ' owner:',
          type: 'attribute',
          attributeName: 'owner',
          nameBase: false,
        },
        {
          displayText: 'group:',
          text: ' group:',
          type: 'attribute',
          attributeName: 'group',
          nameBase: false,
        },
        {
          displayText: 'kind:',
          text: ' kind:',
          type: 'attribute',
          attributeName: 'kind',
          nameBase: false,
        },
        {
          displayText: 'code_location:',
          text: ' code_location:',
          type: 'attribute',
          attributeName: 'code_location',
          nameBase: false,
        },
        {displayText: 'sinks()', text: ' sinks()', type: 'function'},
        {displayText: 'roots()', text: ' roots()', type: 'function'},
        {displayText: 'not', text: ' not ', type: 'logical_operator'},
        {displayText: '+', text: ' +', type: 'up-traversal'},
        {displayText: '(', text: ' ()', type: 'parenthesis'},
      ],
      from: 12,
      to: 12,
    });
  });

  it('suggestions within incomplete function call expression', () => {
    expect(
      testAutocomplete('(sinks(key:"value"+2 or (key_substring:"aws_cost_report"+2)|'),
    ).toEqual({
      from: 59,
      list: [
        {displayText: 'and', text: ' and ', type: 'logical_operator'},
        {displayText: 'or', text: ' or ', type: 'logical_operator'},
        {displayText: '+', text: '+', type: 'down-traversal'},
        {displayText: ')', text: ')', type: 'parenthesis'},
      ],
      to: 59,
    });
  });

  it('makes suggestion in whitespace after or token in between two incomplete or expressions', () => {
    expect(
      testAutocomplete('key_substring:"aws_cost_report" or |or key_substring:"aws_cost_report"'),
    ).toEqual({
      from: 35,
      list: [
        {
          displayText: 'key:',
          text: 'key:',
          type: 'attribute',
          attributeName: 'key',
          nameBase: true,
        },
        {
          displayText: 'tag:',
          text: 'tag:',
          type: 'attribute',
          attributeName: 'tag',
          nameBase: false,
        },
        {
          displayText: 'owner:',
          text: 'owner:',
          type: 'attribute',
          attributeName: 'owner',
          nameBase: false,
        },
        {
          displayText: 'group:',
          text: 'group:',
          type: 'attribute',
          attributeName: 'group',
          nameBase: false,
        },
        {
          displayText: 'kind:',
          text: 'kind:',
          type: 'attribute',
          attributeName: 'kind',
          nameBase: false,
        },
        {
          displayText: 'code_location:',
          text: 'code_location:',
          type: 'attribute',
          attributeName: 'code_location',
          nameBase: false,
        },
        {displayText: 'sinks()', text: 'sinks()', type: 'function'},
        {displayText: 'roots()', text: 'roots()', type: 'function'},
        {displayText: 'not', text: 'not ', type: 'logical_operator'},
        {displayText: '+', text: '+', type: 'up-traversal'},
        {displayText: '(', text: '()', type: 'parenthesis'},
      ],
      to: 35,
    });
  });

  it('suggests and/or logical operators', () => {
    expect(
      testAutocomplete('key_substring:"aws_cost_report" o|r and key_substring:"aws_cost_report"'),
    ).toEqual({
      from: 32,
      list: [
        {
          displayText: 'or',
          text: 'or',
          type: 'logical_operator',
        },
        {
          displayText: 'and',
          text: 'and',
          type: 'logical_operator',
        },
      ],
      to: 34,
    });

    expect(
      testAutocomplete('key_substring:"aws_cost_report" a|nd and key_substring:"aws_cost_report"'),
    ).toEqual({
      from: 32,
      list: [
        {
          displayText: 'and',
          text: 'and',
          type: 'logical_operator',
        },
        {
          displayText: 'or',
          text: 'or',
          type: 'logical_operator',
        },
      ],
      to: 35,
    });
  });

  it('suggests attribute names when cursor left of the colon', () => {
    expect(testAutocomplete('tag:"dagster/kind/fivetran" or t|:"a"')).toEqual({
      from: 31,
      list: [
        {
          displayText: 'tag:',
          text: 'tag:',
          type: 'attribute',
          attributeName: 'tag',
          nameBase: false,
        },
      ],
      to: 33,
    });
  });

  it('suggests attribute values when cursor left of the double quote', () => {
    expect(testAutocomplete('tag:"tag|"')).toEqual({
      from: 4,
      list: [
        {text: '"tag1"', displayText: 'tag1', type: 'attribute-value', attributeName: 'tag'},
        {text: '"tag2"', displayText: 'tag2', type: 'attribute-value', attributeName: 'tag'},
        {text: '"tag3"', displayText: 'tag3', type: 'attribute-value', attributeName: 'tag'},
      ],
      to: 9,
    });
  });

  it('handles malformed input in the middle of the selection', () => {
    expect(
      testAutocomplete(
        'owner:"marco@dagsterlabs.com" or aiufhaifuhaguihaiugh k|ey:"column_schema_asset_2"',
      ),
    ).toEqual({
      from: 54,
      list: [
        {
          displayText: 'key:',
          text: 'key:',
          type: 'attribute',
          attributeName: 'key',
          nameBase: true,
        },
      ],
      to: 58,
    });

    expect(
      testAutocomplete('owner:"marco@dagsterlabs.com" or aiufhaifuhaguihaiugh key:"|"'),
    ).toEqual({
      from: 58,
      list: [
        {text: '"asset1"', displayText: 'asset1', type: 'attribute-value', attributeName: 'key'},
        {text: '"asset2"', displayText: 'asset2', type: 'attribute-value', attributeName: 'key'},
        {text: '"asset3"', displayText: 'asset3', type: 'attribute-value', attributeName: 'key'},
      ],
      to: 60,
    });
  });

  it('handles complex ands/ors', () => {
    expect(testAutocomplete('key:"value"+ or tag:"value"+ and owner:"owner" and |')).toEqual({
      from: 51,
      list: [
        {
          displayText: 'key:',
          text: 'key:',
          type: 'attribute',
          attributeName: 'key',
          nameBase: true,
        },
        {
          displayText: 'tag:',
          text: 'tag:',
          type: 'attribute',
          attributeName: 'tag',
          nameBase: false,
        },
        {
          displayText: 'owner:',
          text: 'owner:',
          type: 'attribute',
          attributeName: 'owner',
          nameBase: false,
        },
        {
          displayText: 'group:',
          text: 'group:',
          type: 'attribute',
          attributeName: 'group',
          nameBase: false,
        },
        {
          displayText: 'kind:',
          text: 'kind:',
          type: 'attribute',
          attributeName: 'kind',
          nameBase: false,
        },
        {
          displayText: 'code_location:',
          text: 'code_location:',
          type: 'attribute',
          attributeName: 'code_location',
          nameBase: false,
        },
        {
          displayText: 'sinks()',
          text: 'sinks()',
          type: 'function',
        },
        {
          displayText: 'roots()',
          text: 'roots()',
          type: 'function',
        },
        {
          displayText: 'not',
          text: 'not ',
          type: 'logical_operator',
        },
        {
          displayText: '+',
          text: '+',
          type: 'up-traversal',
        },
        {
          displayText: '(',
          text: '()',
          type: 'parenthesis',
        },
      ],
      to: 51,
    });
  });

  it('does not suggest + after +', () => {
    expect(testAutocomplete('key:"value"+|')).toEqual({
      from: 12,
      list: [
        {text: ' and ', displayText: 'and', type: 'logical_operator'},
        {text: ' or ', displayText: 'or', type: 'logical_operator'},
      ],
      to: 12,
    });
  });
});
