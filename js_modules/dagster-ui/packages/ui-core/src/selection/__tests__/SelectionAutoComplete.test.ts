import {createSelectionAutoComplete} from '../SelectionAutoComplete';
import {createProvider} from '../SelectionAutoCompleteProvider';

describe('createAssetSelectionHint', () => {
  const attributesMap = {
    key: ['asset1', 'asset2', 'asset3', 'prefix/thing1', 'prefix/thing2'],
    tag: ['tag1', 'tag2', 'tag3', 'key=value1', 'key=value2'],
    owner: ['marco@dagsterlabs.com', 'team:frontend'],
    group: ['group1', 'group2'],
    kind: ['kind1', 'kind2'],
    code_location: ['repo1@location1', 'repo2@location2', 'assumptions@location3'],
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

  function testAutocomplete(testString: string, hintFn = selectionHint) {
    const cursorIndex = testString.indexOf('|');
    const string = testString.replace('|', '');

    const hints = hintFn(string, cursorIndex);

    return {
      list: hints?.list,
      from: hints?.from,
      to: hints?.to,
    };
  }

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
        expect.objectContaining({
          text: '"key=value1"',
        }),
        expect.objectContaining({
          text: '"key=value2"',
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
        expect.objectContaining({
          text: '"key=value1"',
        }),
        expect.objectContaining({
          text: '"key=value2"',
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
          text: 'key:"*o*"',
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
        expect.objectContaining({
          text: 'code_location:"assumptions@location3"',
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
        expect.objectContaining({
          text: '"assumptions@location3"',
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
    expect(testAutocomplete('sinks(key:"FIVETRAN/google_ads/ad_group_history" or |)')).toEqual({
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
      from: 52, // cursor location
      to: 52, // cursor location
    });
  });

  it('should handle incomplete or expression within function with cursor right after the "or"', () => {
    expect(testAutocomplete('sinks(key:"FIVETRAN/google_ads/ad_group_history" or|)')).toEqual({
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
      from: 51, // cursor location
      to: 51, // cursor location
    });
  });

  it('should suggest tag values to the right of colon of an attribute expression inside of an IncompleteAttributeExpression, OrExpression, and ParenthesizedExpression', () => {
    expect(testAutocomplete('sinks(key:"FIVETRAN/google_ads/ad_group_history" or key:|)')).toEqual({
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
        expect.objectContaining({
          text: '"prefix/thing1"',
        }),
        expect.objectContaining({
          text: '"prefix/thing2"',
        }),
      ],
      from: 56, // cursor location
      to: 56, // cursor location
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
      testAutocomplete('key:"test" or key:"FIVETRAN/google_ads/ad_group_history"+ or |'),
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
      from: 61, // cursor position
      to: 61, // cursor position
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

    expect(testAutocomplete('sinks(key:"set" or key:"asset"|)')).toEqual({
      list: [
        expect.objectContaining({
          text: ' and ',
        }),
        expect.objectContaining({
          text: ' or ',
        }),
        expect.objectContaining({text: '+'}),
      ],
      from: 30, // cursor position
      to: 30, // cursor position
    });

    expect(testAutocomplete('sinks(key:"asset" or key:"s|et2")')).toEqual({
      list: [
        expect.objectContaining({
          text: '"asset2"',
        }),
      ],
      from: 25, // start of value
      to: 31, // end of value
    });

    expect(testAutocomplete('sinks(key:"sset1"| or key:"set")')).toEqual({
      list: [
        expect.objectContaining({
          text: ' and ',
        }),
        expect.objectContaining({
          text: ' or ',
        }),
        expect.objectContaining({text: '+'}),
      ],
      from: 17, // cursor position
      to: 17, // cursor position
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
        '(sinks(key:"FIVETRAN/google_ads/ad_group_history" or (key:"aws_cost_report"+2)|',
      ),
    ).toEqual({
      from: 78,
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
      to: 78,
    });
  });

  it('makes suggestion in whitespace after or token in between two incomplete or expressions', () => {
    expect(testAutocomplete('key:"aws_cost_report" or |or key:"aws_cost_report"')).toEqual({
      from: 25,
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
      to: 25,
    });
  });

  it('suggests and/or logical operators', () => {
    expect(testAutocomplete('key:"aws_cost_report" o|r and key:"aws_cost_report"')).toEqual({
      from: 22,
      list: [
        expect.objectContaining({
          text: 'or',
        }),
        expect.objectContaining({
          text: 'and',
        }),
      ],
      to: 24,
    });

    expect(testAutocomplete('key:"aws_cost_report" a|nd and key:"aws_cost_report"')).toEqual({
      from: 22,
      list: [
        expect.objectContaining({
          text: 'and',
        }),
        expect.objectContaining({
          text: 'or',
        }),
      ],
      to: 25,
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
        expect.objectContaining({text: '"prefix/thing1"'}),
        expect.objectContaining({text: '"prefix/thing2"'}),
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

  it('suggests things for the value after an upstream traversal', () => {
    expect(testAutocomplete('+ass|')).toEqual({
      from: 1,
      list: [
        expect.objectContaining({text: 'key:"*ass*"'}),
        expect.objectContaining({text: 'key:"asset1"'}),
        expect.objectContaining({text: 'key:"asset2"'}),
        expect.objectContaining({text: 'key:"asset3"'}),
        expect.objectContaining({text: 'code_location:"assumptions@location3"'}),
      ],
      to: 4,
    });
  });

  it('value suggestions should replace entire key=value segment in tag:key=value', () => {
    expect(testAutocomplete('tag:k|ey=value or key:"test"')).toEqual({
      from: 4,
      list: [
        expect.objectContaining({text: '"key=value1"'}),
        expect.objectContaining({text: '"key=value2"'}),
      ],
      to: 13,
    });

    expect(testAutocomplete('tag:key|=value or key:"test"')).toEqual({
      from: 4,
      list: [
        expect.objectContaining({text: '"key=value1"'}),
        expect.objectContaining({text: '"key=value2"'}),
      ],
      to: 13,
    });

    expect(testAutocomplete('tag:key=|value or key:"test"')).toEqual({
      from: 4,
      list: [
        expect.objectContaining({text: '"key=value1"'}),
        expect.objectContaining({text: '"key=value2"'}),
      ],
      to: 13,
    });
    expect(testAutocomplete('tag:key=val|ue or key:"test"')).toEqual({
      from: 4,
      list: [
        expect.objectContaining({text: '"key=value1"'}),
        expect.objectContaining({text: '"key=value2"'}),
      ],
      to: 13,
    });
  });

  it('should be case insensitive', () => {
    expect(testAutocomplete('REPO|')).toEqual({
      from: 0,
      list: [
        expect.objectContaining({text: 'key:"*REPO*"'}),
        expect.objectContaining({text: 'code_location:"repo1@location1"'}),
        expect.objectContaining({text: 'code_location:"repo2@location2"'}),
      ],
      to: 4,
    });
  });

  it('Allows slashes in identifiers', () => {
    expect(testAutocomplete('prefix/th|ing')).toEqual({
      from: 0,
      list: [
        expect.objectContaining({text: 'key:"*prefix/thing*"'}),
        expect.objectContaining({text: 'key:"prefix/thing1"'}),
        expect.objectContaining({text: 'key:"prefix/thing2"'}),
      ],
      to: 12,
    });
  });

  it('Allows numbers in identifiers', () => {
    expect(testAutocomplete('1|')).toEqual({
      from: 0,
      list: [
        expect.objectContaining({text: 'key:"*1*"'}),
        expect.objectContaining({text: 'key:"asset1"'}),
        expect.objectContaining({text: 'key:"prefix/thing1"'}),
        expect.objectContaining({text: 'tag:"tag1"'}),
        expect.objectContaining({text: 'tag:"key=value1"'}),
        expect.objectContaining({text: 'group:"group1"'}),
        expect.objectContaining({text: 'kind:"kind1"'}),
        expect.objectContaining({text: 'code_location:"repo1@location1"'}),
      ],
      to: 1,
    });
  });

  it('uses primary attribute key for substring suggestions', () => {
    const attributesMap = {
      key: [],
      tag: [],
      owner: [],
      group: [],
      kind: [],
      code_location: [],
    };
    const provider = createProvider({
      attributesMap,
      primaryAttributeKey: 'tag',
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

    expect(testAutocomplete('test|', selectionHint)).toEqual({
      from: 0,
      list: [expect.objectContaining({text: 'tag:"*test*"'})],
      to: 4,
    });
  });
});
