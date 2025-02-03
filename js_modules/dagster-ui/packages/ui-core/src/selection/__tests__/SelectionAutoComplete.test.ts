import {createSelectionAutoComplete} from '../SelectionAutoComplete';
import {createProvider} from '../SelectionAutoCompleteProvider';

describe('createAssetSelectionHint', () => {
  const attributesMap = {
    key: ['asset1', 'asset2', 'asset3'],
    tag: ['tag1', 'tag2', 'tag3'],
    owner: ['marco@dagsterlabs.com', 'team:frontend'],
    group: ['group1', 'group2'],
    kind: ['kind1', 'kind2'],
    code_location: ['repo1@location1', 'repo2@location2'],
  };
  const provider = createProvider({
    attributesMap,
    primaryAttributeKey: 'key',
    attributeToIcon: {
      key: 'magnify_glass',
      tag: 'magnify_glass',
      owner: 'magnify_glass',
      group: 'magnify_glass',
      kind: 'magnify_glass',
      code_location: 'magnify_glass',
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
        expect.objectContaining({
          text: '"asset1"',
        }),
        expect.objectContaining({
          text: '"asset2"',
        }),
        expect.objectContaining({
          text: '"asset3"',
        }),
      ],
      from: 14, // cursor location
      to: 14, // cursor location
    });
  });

  it('should suggest owners after typing owner:', () => {
    expect(testAutocomplete('owner:|')).toEqual({
      list: [
        expect.objectContaining({
          text: '"marco@dagsterlabs.com"',
        }),
        expect.objectContaining({
          text: '"team:frontend"',
        }),
      ],
      from: 6, // cursor location
      to: 6, // cursor location
    });
  });

  it('should suggest tag names after typing tag:', () => {
    expect(testAutocomplete('tag:|')).toEqual({
      list: [
        expect.objectContaining({
          text: '"tag1"',
        }),
        expect.objectContaining({
          text: '"tag2"',
        }),
        expect.objectContaining({
          text: '"tag3"',
        }),
      ],
      from: 4, // cursor location
      to: 4, // cursor location
    });

    expect(testAutocomplete('tag:"|"')).toEqual({
      list: [
        expect.objectContaining({
          text: '"tag1"',
        }),
        expect.objectContaining({
          text: '"tag2"',
        }),
        expect.objectContaining({
          text: '"tag3"',
        }),
      ],
      from: 4, // cursor location
      to: 6, // cursor location
    });
  });

  it('should suggest logical operators after an expression', () => {
    expect(testAutocomplete('key:"asset1" |')).toEqual({
      list: [
        expect.objectContaining({
          text: ' and ',
        }),
        expect.objectContaining({
          text: ' or ',
        }),
        expect.objectContaining({
          text: '+',
        }),
      ],
      from: 13, // cursor location
      to: 13, // cursor location
    });

    expect(testAutocomplete('key:"asset1"|')).toEqual({
      list: [
        expect.objectContaining({
          text: ' and ',
        }),
        expect.objectContaining({
          text: ' or ',
        }),
        expect.objectContaining({
          text: '+',
        }),
      ],
      from: 12, // cursor location
      to: 12, // cursor location
    });
  });

  it('should filter suggestions based on partial input', () => {
    expect(testAutocomplete('owner:marco|')).toEqual({
      list: [
        expect.objectContaining({
          text: '"marco@dagsterlabs.com"',
        }),
      ],
      from: 6, // start of value "marco"
      to: 11, // end of value
    });
  });

  it('should suggest possible keywords', () => {
    // empty case
    expect(testAutocomplete('|')).toEqual({
      list: [
        expect.objectContaining({
          text: 'key:',
        }),
        expect.objectContaining({
          text: 'tag:',
        }),
        expect.objectContaining({
          text: 'owner:',
        }),
        expect.objectContaining({
          text: 'group:',
        }),
        expect.objectContaining({
          text: 'kind:',
        }),
        expect.objectContaining({
          text: 'code_location:',
        }),
        expect.objectContaining({
          text: 'sinks()',
        }),
        expect.objectContaining({
          text: 'roots()',
        }),
        expect.objectContaining({
          text: 'not ',
        }),
        expect.objectContaining({
          text: '+',
        }),

        expect.objectContaining({
          text: '()',
        }),
      ],
      from: 0, // cursor location
      to: 0, // cursor location
    });

    // filtered case
    expect(testAutocomplete('o|')).toEqual({
      list: [
        expect.objectContaining({
          text: 'key_substring:"o"',
        }),
        expect.objectContaining({
          text: 'owner:',
        }),
        expect.objectContaining({
          text: 'owner:"marco@dagsterlabs.com"',
        }),
        expect.objectContaining({
          text: 'owner:"team:frontend"',
        }),
        expect.objectContaining({
          text: 'group:"group1"',
        }),
        expect.objectContaining({
          text: 'group:"group2"',
        }),
        expect.objectContaining({
          text: 'code_location:"repo1@location1"',
        }),
        expect.objectContaining({
          text: 'code_location:"repo2@location2"',
        }),
      ],
      from: 0, // start of input
      to: 1, // cursor location
    });
  });

  it('should handle traversal operators correctly', () => {
    expect(testAutocomplete('+|')).toEqual({
      list: [
        expect.objectContaining({
          text: 'key:',
        }),
        expect.objectContaining({
          text: 'tag:',
        }),
        expect.objectContaining({
          text: 'owner:',
        }),
        expect.objectContaining({
          text: 'group:',
        }),
        expect.objectContaining({
          text: 'kind:',
        }),
        expect.objectContaining({
          text: 'code_location:',
        }),
        expect.objectContaining({text: 'sinks()'}),
        expect.objectContaining({text: 'roots()'}),
        expect.objectContaining({text: '()'}),
      ],
      from: 1, // cursor location
      to: 1, // cursor location
    });

    expect(testAutocomplete('* |')).toEqual({
      from: 2,
      list: [
        expect.objectContaining({
          text: ' and ',
        }),
        expect.objectContaining({
          text: ' or ',
        }),
      ],
      to: 2,
    });

    expect(testAutocomplete('+ |')).toEqual({
      from: 2,
      list: [
        expect.objectContaining({
          text: 'key:',
        }),
        expect.objectContaining({
          text: 'tag:',
        }),
        expect.objectContaining({
          text: 'owner:',
        }),
        expect.objectContaining({
          text: 'group:',
        }),
        expect.objectContaining({
          text: 'kind:',
        }),
        expect.objectContaining({
          text: 'code_location:',
        }),
        expect.objectContaining({text: 'sinks()'}),
        expect.objectContaining({text: 'roots()'}),
        expect.objectContaining({text: 'not '}),
        expect.objectContaining({text: '()'}),
      ],
      to: 2,
    });

    expect(testAutocomplete('+|')).toEqual({
      from: 1,
      list: [
        expect.objectContaining({
          text: 'key:',
        }),
        expect.objectContaining({
          text: 'tag:',
        }),
        expect.objectContaining({
          text: 'owner:',
        }),
        expect.objectContaining({
          text: 'group:',
        }),
        expect.objectContaining({
          text: 'kind:',
        }),
        expect.objectContaining({
          text: 'code_location:',
        }),
        expect.objectContaining({text: 'sinks()'}),
        expect.objectContaining({text: 'roots()'}),
        expect.objectContaining({text: '()'}),
      ],
      to: 1,
    });
  });

  it('should suggest code locations after typing code_location:', () => {
    expect(testAutocomplete('code_location:|')).toEqual({
      list: [
        expect.objectContaining({
          text: '"repo1@location1"',
        }),
        expect.objectContaining({
          text: '"repo2@location2"',
        }),
      ],
      from: 14,
      to: 14,
    });
  });

  it('should handle incomplete "not" expressions', () => {
    expect(testAutocomplete('not|')).toEqual({
      list: [
        expect.objectContaining({
          text: ' key:',
        }),
        expect.objectContaining({
          text: ' tag:',
        }),
        expect.objectContaining({
          text: ' owner:',
        }),
        expect.objectContaining({
          text: ' group:',
        }),
        expect.objectContaining({
          text: ' kind:',
        }),
        expect.objectContaining({
          text: ' code_location:',
        }),
        expect.objectContaining({text: ' sinks()'}),
        expect.objectContaining({text: ' roots()'}),
        expect.objectContaining({text: ' +'}),
        expect.objectContaining({text: ' ()'}),
      ],
      from: 3, // cursor location
      to: 3, // cursor location
    });

    expect(testAutocomplete('not |')).toEqual({
      list: [
        expect.objectContaining({
          text: 'key:',
        }),
        expect.objectContaining({
          text: 'tag:',
        }),
        expect.objectContaining({
          text: 'owner:',
        }),
        expect.objectContaining({
          text: 'group:',
        }),
        expect.objectContaining({
          text: 'kind:',
        }),
        expect.objectContaining({
          text: 'code_location:',
        }),
        expect.objectContaining({text: 'sinks()'}),
        expect.objectContaining({text: 'roots()'}),
        expect.objectContaining({text: '+'}),
        expect.objectContaining({text: '()'}),
      ],
      from: 4, // cursor location
      to: 4, // cursor location
    });
  });

  it('should handle incomplete and expressions', () => {
    expect(testAutocomplete('key:"asset1" and |')).toEqual({
      list: [
        expect.objectContaining({
          text: 'key:',
        }),
        expect.objectContaining({
          text: 'tag:',
        }),
        expect.objectContaining({
          text: 'owner:',
        }),
        expect.objectContaining({
          text: 'group:',
        }),
        expect.objectContaining({
          text: 'kind:',
        }),
        expect.objectContaining({
          text: 'code_location:',
        }),
        expect.objectContaining({text: 'sinks()'}),
        expect.objectContaining({text: 'roots()'}),
        expect.objectContaining({text: 'not '}),
        expect.objectContaining({text: '+'}),
        expect.objectContaining({text: '()'}),
      ],
      from: 17, // cursor location
      to: 17, // cursor location
    });
  });

  it('should handle incomplete or expressions', () => {
    expect(testAutocomplete('key:"asset1" or |')).toEqual({
      list: [
        expect.objectContaining({
          text: 'key:',
        }),
        expect.objectContaining({
          text: 'tag:',
        }),
        expect.objectContaining({
          text: 'owner:',
        }),
        expect.objectContaining({
          text: 'group:',
        }),
        expect.objectContaining({
          text: 'kind:',
        }),
        expect.objectContaining({
          text: 'code_location:',
        }),
        expect.objectContaining({text: 'sinks()'}),
        expect.objectContaining({text: 'roots()'}),
        expect.objectContaining({text: 'not '}),
        expect.objectContaining({text: '+'}),
        expect.objectContaining({text: '()'}),
      ],
      from: 16, // cursor location
      to: 16, // cursor location
    });
  });

  it('should handle incomplete quoted strings gracefully', () => {
    expect(testAutocomplete('key:"asse|')).toEqual({
      list: [
        expect.objectContaining({
          text: '"asset1"',
        }),
        expect.objectContaining({
          text: '"asset2"',
        }),
        expect.objectContaining({
          text: '"asset3"',
        }),
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
        expect.objectContaining({
          text: 'key:',
        }),
        expect.objectContaining({
          text: 'tag:',
        }),
        expect.objectContaining({
          text: 'owner:',
        }),
        expect.objectContaining({
          text: 'group:',
        }),
        expect.objectContaining({
          text: 'kind:',
        }),
        expect.objectContaining({
          text: 'code_location:',
        }),
        expect.objectContaining({text: 'sinks()'}),
        expect.objectContaining({text: 'roots()'}),
        expect.objectContaining({text: 'not '}),
        expect.objectContaining({text: '+'}),
        expect.objectContaining({text: '()'}),
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
        expect.objectContaining({
          text: ' key:',
        }),
        expect.objectContaining({
          text: ' tag:',
        }),
        expect.objectContaining({
          text: ' owner:',
        }),
        expect.objectContaining({
          text: ' group:',
        }),
        expect.objectContaining({
          text: ' kind:',
        }),
        expect.objectContaining({
          text: ' code_location:',
        }),
        expect.objectContaining({text: ' sinks()'}),
        expect.objectContaining({text: ' roots()'}),
        expect.objectContaining({text: ' not '}),
        expect.objectContaining({text: ' +'}),
        expect.objectContaining({text: ' ()'}),
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
        expect.objectContaining({
          text: '"asset1"',
        }),
        expect.objectContaining({
          text: '"asset2"',
        }),
        expect.objectContaining({
          text: '"asset3"',
        }),
      ],
      from: 76, // cursor location
      to: 76, // cursor location
    });
  });

  it('suggestions after downtraversal "+"', () => {
    expect(testAutocomplete('key:"value"+|')).toEqual({
      list: [expect.objectContaining({text: ' and '}), expect.objectContaining({text: ' or '})],
      from: 12, // cursor location
      to: 12, // cursor location
    });

    // UpAndDownTraversal
    expect(testAutocomplete('+key:"value"|+')).toEqual({
      list: [
        expect.objectContaining({text: ' and '}),
        expect.objectContaining({text: ' or '}),
        expect.objectContaining({text: '+'}),
      ],
      from: 12, // cursor location
      to: 12, // cursor location
    });

    // DownTraversal
    expect(testAutocomplete('key:"value"|+')).toEqual({
      list: [
        expect.objectContaining({text: ' and '}),
        expect.objectContaining({text: ' or '}),
        expect.objectContaining({text: '+'}),
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
        expect.objectContaining({
          text: 'key:',
        }),
        expect.objectContaining({
          text: 'tag:',
        }),
        expect.objectContaining({
          text: 'owner:',
        }),
        expect.objectContaining({
          text: 'group:',
        }),
        expect.objectContaining({
          text: 'kind:',
        }),
        expect.objectContaining({
          text: 'code_location:',
        }),
        expect.objectContaining({text: 'sinks()'}),
        expect.objectContaining({text: 'roots()'}),
        expect.objectContaining({text: 'not '}),
        expect.objectContaining({text: '+'}),
        expect.objectContaining({text: '()'}),
      ],
      from: 71, // cursor position
      to: 71, // cursor position
    });
  });

  it('suggestions inside parenthesized expression', () => {
    expect(testAutocomplete('(|)')).toEqual({
      list: [
        expect.objectContaining({
          text: 'key:',
        }),
        expect.objectContaining({
          text: 'tag:',
        }),
        expect.objectContaining({
          text: 'owner:',
        }),
        expect.objectContaining({
          text: 'group:',
        }),
        expect.objectContaining({
          text: 'kind:',
        }),
        expect.objectContaining({
          text: 'code_location:',
        }),
        expect.objectContaining({text: 'sinks()'}),
        expect.objectContaining({text: 'roots()'}),
        expect.objectContaining({text: 'not '}),
        expect.objectContaining({text: '+'}),
        expect.objectContaining({text: '()'}),
      ],
      from: 1, // cursor location
      to: 1, // cursor location
    });
  });

  it('suggestions outside parenthesized expression before', () => {
    expect(testAutocomplete('|()')).toEqual({
      list: [
        expect.objectContaining({
          text: 'key:',
        }),
        expect.objectContaining({
          text: 'tag:',
        }),
        expect.objectContaining({
          text: 'owner:',
        }),
        expect.objectContaining({
          text: 'group:',
        }),
        expect.objectContaining({
          text: 'kind:',
        }),
        expect.objectContaining({
          text: 'code_location:',
        }),
        expect.objectContaining({text: 'sinks()'}),
        expect.objectContaining({text: 'roots()'}),
        expect.objectContaining({text: 'not '}),
        expect.objectContaining({text: '+'}),
        expect.objectContaining({text: '()'}),
      ],
      from: 0, // cursor position
      to: 0, // cursor position
    });
  });

  it('suggestions outside parenthesized expression after', () => {
    expect(testAutocomplete('()|')).toEqual({
      list: [
        expect.objectContaining({text: ' and '}),
        expect.objectContaining({text: ' or '}),
        expect.objectContaining({text: '+'}),
      ],
      from: 2, // cursor position
      to: 2, // cursor position
    });
  });

  it('suggestions within parenthesized expression', () => {
    expect(testAutocomplete('(tag:"dagster/kind/dlt"|)')).toEqual({
      list: [
        expect.objectContaining({
          text: ' and ',
        }),
        expect.objectContaining({
          text: ' or ',
        }),
        expect.objectContaining({text: '+'}),
      ],
      from: 23, // cursor position
      to: 23, // cursor position
    });

    expect(testAutocomplete('sinks(key_substring:"set" or key_substring:"asset"|)')).toEqual({
      list: [
        expect.objectContaining({
          text: ' and ',
        }),
        expect.objectContaining({
          text: ' or ',
        }),
        expect.objectContaining({text: '+'}),
      ],
      from: 50, // cursor position
      to: 50, // cursor position
    });

    expect(testAutocomplete('sinks(key_substring:"asset" or key_substring:"s|et2")')).toEqual({
      list: [
        expect.objectContaining({
          text: '"asset2"',
        }),
      ],
      from: 45, // start of value
      to: 51, // end of value
    });

    expect(testAutocomplete('sinks(key_substring:"sset1"| or key_substring:"set")')).toEqual({
      list: [
        expect.objectContaining({
          text: ' and ',
        }),
        expect.objectContaining({
          text: ' or ',
        }),
        expect.objectContaining({text: '+'}),
      ],
      from: 27, // cursor position
      to: 27, // cursor position
    });
  });

  it('makes suggestions around traversals', () => {
    expect(testAutocomplete('sinks()+2|')).toEqual({
      list: [expect.objectContaining({text: ' and '}), expect.objectContaining({text: ' or '})],
      from: 9, // start of value
      to: 9, // end of value
    });

    expect(testAutocomplete('sinks()+|+')).toEqual({
      list: [expect.objectContaining({text: ' and '}), expect.objectContaining({text: ' or '})],
      from: 8, // start of value
      to: 8, // end of value
    });

    expect(testAutocomplete('|2+sinks()+2')).toEqual({
      list: [
        expect.objectContaining({
          text: '()',
        }),
      ],
      from: 0, // start of value
      to: 0, // end of value
    });

    expect(testAutocomplete('2|+sinks()+2')).toEqual({
      list: [
        expect.objectContaining({
          text: '()',
        }),
      ],
      from: 1, // start of value
      to: 1, // end of value
    });
  });

  it('makes suggestions for IncompleteExpression inside of the ParenthesizedExpression', () => {
    expect(testAutocomplete('(key:tag and |)')).toEqual({
      list: [
        expect.objectContaining({
          text: 'key:',
        }),
        expect.objectContaining({
          text: 'tag:',
        }),
        expect.objectContaining({
          text: 'owner:',
        }),
        expect.objectContaining({
          text: 'group:',
        }),
        expect.objectContaining({
          text: 'kind:',
        }),
        expect.objectContaining({
          text: 'code_location:',
        }),
        expect.objectContaining({text: 'sinks()'}),
        expect.objectContaining({text: 'roots()'}),
        expect.objectContaining({
          text: 'not ',
        }),
        expect.objectContaining({text: '+'}),
        expect.objectContaining({
          text: '()',
        }),
      ],
      from: 13,
      to: 13,
    });

    expect(testAutocomplete('(key:tag and|)')).toEqual({
      list: [
        expect.objectContaining({
          text: ' key:',
        }),
        expect.objectContaining({
          text: ' tag:',
        }),
        expect.objectContaining({
          text: ' owner:',
        }),
        expect.objectContaining({
          text: ' group:',
        }),
        expect.objectContaining({
          text: ' kind:',
        }),
        expect.objectContaining({
          text: ' code_location:',
        }),
        expect.objectContaining({text: ' sinks()'}),
        expect.objectContaining({text: ' roots()'}),
        expect.objectContaining({
          text: ' not ',
        }),
        expect.objectContaining({text: ' +'}),
        expect.objectContaining({
          text: ' ()',
        }),
      ],
      from: 12,
      to: 12,
    });

    expect(testAutocomplete('(key:tag and| )')).toEqual({
      list: [
        expect.objectContaining({
          text: ' key:',
        }),
        expect.objectContaining({
          text: ' tag:',
        }),
        expect.objectContaining({
          text: ' owner:',
        }),
        expect.objectContaining({
          text: ' group:',
        }),
        expect.objectContaining({
          text: ' kind:',
        }),
        expect.objectContaining({
          text: ' code_location:',
        }),
        expect.objectContaining({text: ' sinks()'}),
        expect.objectContaining({text: ' roots()'}),
        expect.objectContaining({
          text: ' not ',
        }),
        expect.objectContaining({text: ' +'}),
        expect.objectContaining({
          text: ' ()',
        }),
      ],
      from: 12,
      to: 12,
    });
  });

  it('suggestions within incomplete function call expression', () => {
    expect(
      testAutocomplete(
        '(sinks(key_substring:"FIVETRAN/google_ads/ad_group_history" or (key_substring:"aws_cost_report"+2)|',
      ),
    ).toEqual({
      from: 98,
      list: [
        expect.objectContaining({
          text: ' and ',
        }),
        expect.objectContaining({
          text: ' or ',
        }),
        expect.objectContaining({text: '+'}),
        expect.objectContaining({text: ')'}),
      ],
      to: 98,
    });
  });

  it('makes suggestion in whitespace after or token in between two incomplete or expressions', () => {
    expect(
      testAutocomplete('key_substring:"aws_cost_report" or |or key_substring:"aws_cost_report"'),
    ).toEqual({
      from: 35,
      list: [
        expect.objectContaining({
          text: 'key:',
        }),
        expect.objectContaining({
          text: 'tag:',
        }),
        expect.objectContaining({
          text: 'owner:',
        }),
        expect.objectContaining({
          text: 'group:',
        }),
        expect.objectContaining({
          text: 'kind:',
        }),
        expect.objectContaining({
          text: 'code_location:',
        }),
        expect.objectContaining({text: 'sinks()'}),
        expect.objectContaining({text: 'roots()'}),
        expect.objectContaining({
          text: 'not ',
        }),
        expect.objectContaining({text: '+'}),
        expect.objectContaining({
          text: '()',
        }),
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
        expect.objectContaining({
          text: 'or',
        }),
        expect.objectContaining({
          text: 'and',
        }),
      ],
      to: 34,
    });

    expect(
      testAutocomplete('key_substring:"aws_cost_report" a|nd and key_substring:"aws_cost_report"'),
    ).toEqual({
      from: 32,
      list: [
        expect.objectContaining({
          text: 'and',
        }),
        expect.objectContaining({
          text: 'or',
        }),
      ],
      to: 35,
    });
  });

  it('suggests attribute names when cursor left of the colon', () => {
    expect(testAutocomplete('tag:"dagster/kind/fivetran" or t|:"a"')).toEqual({
      from: 31,
      list: [
        expect.objectContaining({
          text: 'tag:',
        }),
      ],
      to: 33,
    });
  });

  it('suggests attribute values when cursor left of the double quote', () => {
    expect(testAutocomplete('tag:"tag|"')).toEqual({
      from: 4,
      list: [
        expect.objectContaining({text: '"tag1"'}),
        expect.objectContaining({text: '"tag2"'}),
        expect.objectContaining({text: '"tag3"'}),
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
        expect.objectContaining({
          text: 'key:',
        }),
      ],
      to: 58,
    });

    expect(
      testAutocomplete('owner:"marco@dagsterlabs.com" or aiufhaifuhaguihaiugh key:"|"'),
    ).toEqual({
      from: 58,
      list: [
        expect.objectContaining({text: '"asset1"'}),
        expect.objectContaining({text: '"asset2"'}),
        expect.objectContaining({text: '"asset3"'}),
      ],
      to: 60,
    });
  });

  it('handles complex ands/ors', () => {
    expect(testAutocomplete('key:"value"+ or tag:"value"+ and owner:"owner" and |')).toEqual({
      from: 51,
      list: [
        expect.objectContaining({
          text: 'key:',
        }),
        expect.objectContaining({
          text: 'tag:',
        }),
        expect.objectContaining({
          text: 'owner:',
        }),
        expect.objectContaining({
          text: 'group:',
        }),
        expect.objectContaining({
          text: 'kind:',
        }),
        expect.objectContaining({
          text: 'code_location:',
        }),
        expect.objectContaining({
          text: 'sinks()',
        }),
        expect.objectContaining({
          text: 'roots()',
        }),
        expect.objectContaining({
          text: 'not ',
        }),
        expect.objectContaining({
          text: '+',
        }),
        expect.objectContaining({
          text: '()',
        }),
      ],
      to: 51,
    });
  });

  it('does not suggest + after +', () => {
    expect(testAutocomplete('key:"value"+|')).toEqual({
      from: 12,
      list: [expect.objectContaining({text: ' and '}), expect.objectContaining({text: ' or '})],
      to: 12,
    });
  });
});
