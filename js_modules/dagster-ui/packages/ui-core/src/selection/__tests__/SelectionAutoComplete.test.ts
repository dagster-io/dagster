import {Hint, Hints, Position} from 'codemirror';

import {createSelectionHint} from '../SelectionAutoComplete';

describe('createAssetSelectionHint', () => {
  const selectionHint = createSelectionHint({
    nameBase: 'key',
    attributesMap: {
      key: ['asset1', 'asset2', 'asset3'],
      tag: ['tag1', 'tag2', 'tag3'],
      owner: ['marco@dagsterlabs.com', 'team:frontend'],
      group: ['group1', 'group2'],
      kind: ['kind1', 'kind2'],
      code_location: ['repo1@location1', 'repo2@location2'],
    },
    functions: ['sinks', 'roots'],
  });

  type HintsModified = Omit<Hints, 'list'> & {
    list: Array<Hint>;
  };

  function testAutocomplete(testString: string) {
    const cursorIndex = testString.indexOf('|');
    const string = testString.split('|').join('');

    mockEditor.getCursor.mockReturnValue({ch: cursorIndex});
    mockEditor.getLine.mockReturnValue(string);

    const hints = selectionHint(mockEditor, {}) as HintsModified;

    return {
      list: hints.list,
      from: hints.from.ch,
      to: hints.to.ch,
    };
  }

  const mockEditor = {
    getCursor: jest.fn(),
    getLine: jest.fn(),
    posFromIndex: (index: number) =>
      ({
        ch: index,
        line: 0,
      }) as Position,
  } as any;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should suggest asset names after typing key_substring:', () => {
    // cursorIndex 14
    expect(testAutocomplete('key_substring:|')).toEqual({
      list: [
        {text: '"asset1"', displayText: 'asset1'},
        {text: '"asset2"', displayText: 'asset2'},
        {text: '"asset3"', displayText: 'asset3'},
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
        },
        {
          text: '"team:frontend"',
          displayText: 'team:frontend',
        },
      ],
      from: 6, // cursor location
      to: 6, // cursor location
    });
  });

  it('should suggest tag names after typing tag:', () => {
    expect(testAutocomplete('tag:|')).toEqual({
      list: [
        {text: '"tag1"', displayText: 'tag1'},
        {text: '"tag2"', displayText: 'tag2'},
        {text: '"tag3"', displayText: 'tag3'},
      ],
      from: 4, // cursor location
      to: 4, // cursor location
    });

    expect(testAutocomplete('tag:"|"')).toEqual({
      list: [
        {text: '"tag1"', displayText: 'tag1'},
        {text: '"tag2"', displayText: 'tag2'},
        {text: '"tag3"', displayText: 'tag3'},
      ],
      from: 4, // cursor location
      to: 6, // cursor location
    });
  });

  it('should suggest logical operators after an expression', () => {
    expect(testAutocomplete('key:"asset1" |')).toEqual({
      list: [
        {text: ' and ', displayText: 'and'},
        {text: ' or ', displayText: 'or'},
        {text: '+', displayText: '+'},
      ],
      from: 13, // cursor location
      to: 13, // cursor location
    });

    expect(testAutocomplete('key:"asset1"|')).toEqual({
      list: [
        {text: ' and ', displayText: 'and'},
        {text: ' or ', displayText: 'or'},
        {text: '+', displayText: '+'},
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
        {displayText: 'key_substring:', text: 'key_substring:'},
        {displayText: 'key:', text: 'key:'},
        {displayText: 'tag:', text: 'tag:'},
        {displayText: 'owner:', text: 'owner:'},
        {displayText: 'group:', text: 'group:'},
        {displayText: 'kind:', text: 'kind:'},
        {displayText: 'code_location:', text: 'code_location:'},
        {displayText: 'sinks()', text: 'sinks()'},
        {displayText: 'roots()', text: 'roots()'},
        {displayText: 'not', text: 'not '},
        {displayText: '+', text: '+'},
        {displayText: '(', text: '()'},
      ],
      from: 0, // cursor location
      to: 0, // cursor location
    });

    // filtered case
    expect(testAutocomplete('o|')).toEqual({
      list: [
        {displayText: 'key_substring:o', text: 'key_substring:"o"'},
        {displayText: 'owner:', text: 'owner:'},
        {displayText: 'owner:marco@dagsterlabs.com', text: 'owner:"marco@dagsterlabs.com"'},
        {displayText: 'owner:team:frontend', text: 'owner:"team:frontend"'},
        {displayText: 'group:group1', text: 'group:"group1"'},
        {displayText: 'group:group2', text: 'group:"group2"'},
        {displayText: 'code_location:repo1@location1', text: 'code_location:"repo1@location1"'},
        {displayText: 'code_location:repo2@location2', text: 'code_location:"repo2@location2"'},
      ],
      from: 0, // start of input
      to: 1, // cursor location
    });
  });

  it('should handle traversal operators correctly', () => {
    expect(testAutocomplete('*|')).toEqual({
      list: [
        {displayText: 'key_substring:', text: 'key_substring:'},
        {displayText: 'key:', text: 'key:'},
        {displayText: 'tag:', text: 'tag:'},
        {displayText: 'owner:', text: 'owner:'},
        {displayText: 'group:', text: 'group:'},
        {displayText: 'kind:', text: 'kind:'},
        {displayText: 'code_location:', text: 'code_location:'},
        {displayText: 'sinks()', text: 'sinks()'},
        {displayText: 'roots()', text: 'roots()'},
        {displayText: 'not', text: 'not '},
        {displayText: '(', text: '()'},
      ],
      from: 1, // cursor location
      to: 1, // cursor location
    });

    expect(testAutocomplete('* |')).toEqual({
      from: 2,
      list: [
        {displayText: 'and', text: ' and '},
        {displayText: 'or', text: ' or '},
        {displayText: '+', text: '+'},
      ],
      to: 2,
    });

    expect(testAutocomplete('+ |')).toEqual({
      from: 2,
      list: [
        {displayText: 'key_substring:', text: 'key_substring:'},
        {displayText: 'key:', text: 'key:'},
        {displayText: 'tag:', text: 'tag:'},
        {displayText: 'owner:', text: 'owner:'},
        {displayText: 'group:', text: 'group:'},
        {displayText: 'kind:', text: 'kind:'},
        {displayText: 'code_location:', text: 'code_location:'},
        {displayText: 'sinks()', text: 'sinks()'},
        {displayText: 'roots()', text: 'roots()'},
        {displayText: 'not', text: 'not '},
        {displayText: '+', text: '+'},
        {displayText: '(', text: '()'},
      ],
      to: 2,
    });

    expect(testAutocomplete('+|')).toEqual({
      from: 1,
      list: [
        {displayText: 'key_substring:', text: 'key_substring:'},
        {displayText: 'key:', text: 'key:'},
        {displayText: 'tag:', text: 'tag:'},
        {displayText: 'owner:', text: 'owner:'},
        {displayText: 'group:', text: 'group:'},
        {displayText: 'kind:', text: 'kind:'},
        {displayText: 'code_location:', text: 'code_location:'},
        {displayText: 'sinks()', text: 'sinks()'},
        {displayText: 'roots()', text: 'roots()'},
        {displayText: '+', text: '+'},
        {displayText: '(', text: '()'},
      ],
      to: 1,
    });
  });

  it('should suggest code locations after typing code_location:', () => {
    expect(testAutocomplete('code_location:|')).toEqual({
      list: [
        {text: '"repo1@location1"', displayText: 'repo1@location1'},
        {text: '"repo2@location2"', displayText: 'repo2@location2'},
      ],
      from: 14,
      to: 14,
    });
  });

  it('should handle incomplete "not" expressions', () => {
    expect(testAutocomplete('not|')).toEqual({
      list: [
        {text: ' key_substring:', displayText: 'key_substring:'},
        {text: ' key:', displayText: 'key:'},
        {text: ' tag:', displayText: 'tag:'},
        {text: ' owner:', displayText: 'owner:'},
        {text: ' group:', displayText: 'group:'},
        {text: ' kind:', displayText: 'kind:'},
        {text: ' code_location:', displayText: 'code_location:'},
        {text: ' sinks()', displayText: 'sinks()'},
        {text: ' roots()', displayText: 'roots()'},
        {text: ' +', displayText: '+'},
        {text: ' ()', displayText: '('},
      ],
      from: 3, // cursor location
      to: 3, // cursor location
    });

    expect(testAutocomplete('not |')).toEqual({
      list: [
        {text: 'key_substring:', displayText: 'key_substring:'},
        {text: 'key:', displayText: 'key:'},
        {text: 'tag:', displayText: 'tag:'},
        {text: 'owner:', displayText: 'owner:'},
        {text: 'group:', displayText: 'group:'},
        {text: 'kind:', displayText: 'kind:'},
        {text: 'code_location:', displayText: 'code_location:'},
        {text: 'sinks()', displayText: 'sinks()'},
        {text: 'roots()', displayText: 'roots()'},
        {text: '+', displayText: '+'},
        {text: '()', displayText: '('},
      ],
      from: 4, // cursor location
      to: 4, // cursor location
    });
  });

  it('should handle incomplete and expressions', () => {
    expect(testAutocomplete('key:"asset1" and |')).toEqual({
      list: [
        {text: 'key_substring:', displayText: 'key_substring:'},
        {text: 'key:', displayText: 'key:'},
        {text: 'tag:', displayText: 'tag:'},
        {text: 'owner:', displayText: 'owner:'},
        {text: 'group:', displayText: 'group:'},
        {text: 'kind:', displayText: 'kind:'},
        {text: 'code_location:', displayText: 'code_location:'},
        {text: 'sinks()', displayText: 'sinks()'},
        {text: 'roots()', displayText: 'roots()'},
        {text: 'not ', displayText: 'not'},
        {text: '+', displayText: '+'},
        {text: '()', displayText: '('},
      ],
      from: 17, // cursor location
      to: 17, // cursor location
    });
  });

  it('should handle incomplete or expressions', () => {
    expect(testAutocomplete('key:"asset1" or |')).toEqual({
      list: [
        {text: 'key_substring:', displayText: 'key_substring:'},
        {text: 'key:', displayText: 'key:'},
        {text: 'tag:', displayText: 'tag:'},
        {text: 'owner:', displayText: 'owner:'},
        {text: 'group:', displayText: 'group:'},
        {text: 'kind:', displayText: 'kind:'},
        {text: 'code_location:', displayText: 'code_location:'},
        {text: 'sinks()', displayText: 'sinks()'},
        {text: 'roots()', displayText: 'roots()'},
        {text: 'not ', displayText: 'not'},
        {text: '+', displayText: '+'},
        {text: '()', displayText: '('},
      ],
      from: 16, // cursor location
      to: 16, // cursor location
    });
  });

  it('should handle incomplete quoted strings gracefully', () => {
    expect(testAutocomplete('key:"asse|')).toEqual({
      list: [
        {displayText: 'asset1', text: '"asset1"'},
        {displayText: 'asset2', text: '"asset2"'},
        {displayText: 'asset3', text: '"asset3"'},
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
        {text: 'key_substring:', displayText: 'key_substring:'},
        {text: 'key:', displayText: 'key:'},
        {text: 'tag:', displayText: 'tag:'},
        {text: 'owner:', displayText: 'owner:'},
        {text: 'group:', displayText: 'group:'},
        {text: 'kind:', displayText: 'kind:'},
        {text: 'code_location:', displayText: 'code_location:'},
        {text: 'sinks()', displayText: 'sinks()'},
        {text: 'roots()', displayText: 'roots()'},
        {text: 'not ', displayText: 'not'},
        {text: '+', displayText: '+'},
        {text: '()', displayText: '('},
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
        {text: ' key_substring:', displayText: 'key_substring:'},
        {text: ' key:', displayText: 'key:'},
        {text: ' tag:', displayText: 'tag:'},
        {text: ' owner:', displayText: 'owner:'},
        {text: ' group:', displayText: 'group:'},
        {text: ' kind:', displayText: 'kind:'},
        {text: ' code_location:', displayText: 'code_location:'},
        {text: ' sinks()', displayText: 'sinks()'},
        {text: ' roots()', displayText: 'roots()'},
        {text: ' not ', displayText: 'not'},
        {text: ' +', displayText: '+'},
        {text: ' ()', displayText: '('},
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
        },
        {
          text: '"asset2"',
          displayText: 'asset2',
        },
        {
          text: '"asset3"',
          displayText: 'asset3',
        },
      ],
      from: 76, // cursor location
      to: 76, // cursor location
    });
  });

  it('suggestions after downtraversal "+"', () => {
    expect(testAutocomplete('key:"value"+|')).toEqual({
      list: [
        {text: ' and ', displayText: 'and'},
        {text: ' or ', displayText: 'or'},
        {text: '+', displayText: '+'},
      ],
      from: 12, // cursor location
      to: 12, // cursor location
    });

    // UpAndDownTraversal
    expect(testAutocomplete('+key:"value"|+')).toEqual({
      list: [
        {text: ' and ', displayText: 'and'},
        {text: ' or ', displayText: 'or'},
        {text: '+', displayText: '+'},
      ],
      from: 12, // cursor location
      to: 12, // cursor location
    });

    // DownTraversal
    expect(testAutocomplete('key:"value"|+')).toEqual({
      list: [
        {text: ' and ', displayText: 'and'},
        {text: ' or ', displayText: 'or'},
        {text: '+', displayText: '+'},
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
        // Inserts a space before the string
        {text: 'key_substring:', displayText: 'key_substring:'},
        {text: 'key:', displayText: 'key:'},
        {text: 'tag:', displayText: 'tag:'},
        {text: 'owner:', displayText: 'owner:'},
        {text: 'group:', displayText: 'group:'},
        {text: 'kind:', displayText: 'kind:'},
        {text: 'code_location:', displayText: 'code_location:'},
        {text: 'sinks()', displayText: 'sinks()'},
        {text: 'roots()', displayText: 'roots()'},
        {text: 'not ', displayText: 'not'},
        {text: '+', displayText: '+'},
        {text: '()', displayText: '('},
      ],
      from: 71, // cursor position
      to: 71, // cursor position
    });
  });

  it('suggestions inside parenthesized expression', () => {
    expect(testAutocomplete('(|)')).toEqual({
      list: [
        // Inserts a space before the string
        {text: 'key_substring:', displayText: 'key_substring:'},
        {text: 'key:', displayText: 'key:'},
        {text: 'tag:', displayText: 'tag:'},
        {text: 'owner:', displayText: 'owner:'},
        {text: 'group:', displayText: 'group:'},
        {text: 'kind:', displayText: 'kind:'},
        {text: 'code_location:', displayText: 'code_location:'},
        {text: 'sinks()', displayText: 'sinks()'},
        {text: 'roots()', displayText: 'roots()'},
        {text: 'not ', displayText: 'not'},
        {text: '+', displayText: '+'},
        {text: '()', displayText: '('},
      ],
      from: 1, // cursor location
      to: 1, // cursor location
    });
  });

  it('suggestions outside parenthesized expression before', () => {
    expect(testAutocomplete('|()')).toEqual({
      list: [
        {text: 'key_substring:', displayText: 'key_substring:'},
        {text: 'key:', displayText: 'key:'},
        {text: 'tag:', displayText: 'tag:'},
        {text: 'owner:', displayText: 'owner:'},
        {text: 'group:', displayText: 'group:'},
        {text: 'kind:', displayText: 'kind:'},
        {text: 'code_location:', displayText: 'code_location:'},
        {text: 'sinks()', displayText: 'sinks()'},
        {text: 'roots()', displayText: 'roots()'},
        {text: 'not ', displayText: 'not'},
        {text: '+', displayText: '+'},
        {text: '()', displayText: '('},
      ],
      from: 0, // cursor position
      to: 0, // cursor position
    });
  });

  it('suggestions outside parenthesized expression after', () => {
    expect(testAutocomplete('()|')).toEqual({
      list: [
        {text: ' and ', displayText: 'and'},
        {text: ' or ', displayText: 'or'},
        {text: '+', displayText: '+'},
      ],
      from: 2, // cursor position
      to: 2, // cursor position
    });
  });

  it('suggestions within parenthesized expression', () => {
    expect(testAutocomplete('(tag:"dagster/kind/dlt"|)')).toEqual({
      list: [
        {text: ' and ', displayText: 'and'},
        {text: ' or ', displayText: 'or'},
        {text: '+', displayText: '+'},
      ],
      from: 23, // cursor position
      to: 23, // cursor position
    });

    expect(testAutocomplete('sinks(key_substring:"set" or key_substring:"asset"|)')).toEqual({
      list: [
        {text: ' and ', displayText: 'and'},
        {text: ' or ', displayText: 'or'},
        {text: '+', displayText: '+'},
      ],
      from: 50, // cursor position
      to: 50, // cursor position
    });

    expect(testAutocomplete('sinks(key_substring:"asset" or key_substring:"s|et2")')).toEqual({
      list: [{text: '"asset2"', displayText: 'asset2'}],
      from: 45, // start of value
      to: 51, // end of value
    });

    expect(testAutocomplete('sinks(key_substring:"sset1"| or key_substring:"set")')).toEqual({
      list: [
        {text: ' and ', displayText: 'and'},
        {text: ' or ', displayText: 'or'},
        {text: '+', displayText: '+'},
      ],
      from: 27, // cursor position
      to: 27, // cursor position
    });
  });

  it('makes suggestions around traversals', () => {
    expect(testAutocomplete('sinks()+2|')).toEqual({
      list: [
        {text: ' and ', displayText: 'and'},
        {text: ' or ', displayText: 'or'},
        {text: '+', displayText: '+'},
      ],
      from: 9, // start of value
      to: 9, // end of value
    });

    expect(testAutocomplete('sinks()+|+')).toEqual({
      list: [
        {text: ' and ', displayText: 'and'},
        {text: ' or ', displayText: 'or'},
        {text: '+', displayText: '+'},
      ],
      from: 8, // start of value
      to: 8, // end of value
    });

    expect(testAutocomplete('|2+sinks()+2')).toEqual({
      list: [
        {text: '+', displayText: '+'},
        {text: '()', displayText: '('},
      ],
      from: 0, // start of value
      to: 0, // end of value
    });

    expect(testAutocomplete('2|+sinks()+2')).toEqual({
      list: [
        {text: '+', displayText: '+'},
        {text: '()', displayText: '('},
      ],
      from: 1, // start of value
      to: 1, // end of value
    });
  });

  it('makes suggestions for IncompleteExpression inside of the ParenthesizedExpression', () => {
    expect(testAutocomplete('(key:tag and |)')).toEqual({
      list: [
        {displayText: 'key_substring:', text: 'key_substring:'},
        {displayText: 'key:', text: 'key:'},
        {displayText: 'tag:', text: 'tag:'},
        {displayText: 'owner:', text: 'owner:'},
        {displayText: 'group:', text: 'group:'},
        {displayText: 'kind:', text: 'kind:'},
        {displayText: 'code_location:', text: 'code_location:'},
        {displayText: 'sinks()', text: 'sinks()'},
        {displayText: 'roots()', text: 'roots()'},
        {displayText: 'not', text: 'not '},
        {displayText: '+', text: '+'},
        {displayText: '(', text: '()'},
      ],
      from: 13,
      to: 13,
    });

    expect(testAutocomplete('(key:tag and|)')).toEqual({
      list: [
        {displayText: 'key_substring:', text: ' key_substring:'},
        {displayText: 'key:', text: ' key:'},
        {displayText: 'tag:', text: ' tag:'},
        {displayText: 'owner:', text: ' owner:'},
        {displayText: 'group:', text: ' group:'},
        {displayText: 'kind:', text: ' kind:'},
        {displayText: 'code_location:', text: ' code_location:'},
        {displayText: 'sinks()', text: ' sinks()'},
        {displayText: 'roots()', text: ' roots()'},
        {displayText: 'not', text: ' not '},
        {displayText: '+', text: ' +'},
        {displayText: '(', text: ' ()'},
      ],
      from: 12,
      to: 12,
    });

    expect(testAutocomplete('(key:tag and| )')).toEqual({
      list: [
        {displayText: 'key_substring:', text: ' key_substring:'},
        {displayText: 'key:', text: ' key:'},
        {displayText: 'tag:', text: ' tag:'},
        {displayText: 'owner:', text: ' owner:'},
        {displayText: 'group:', text: ' group:'},
        {displayText: 'kind:', text: ' kind:'},
        {displayText: 'code_location:', text: ' code_location:'},
        {displayText: 'sinks()', text: ' sinks()'},
        {displayText: 'roots()', text: ' roots()'},
        {displayText: 'not', text: ' not '},
        {displayText: '+', text: ' +'},
        {displayText: '(', text: ' ()'},
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
        {displayText: 'and', text: ' and '},
        {displayText: 'or', text: ' or '},
        {displayText: '+', text: '+'},
        {displayText: ')', text: ')'},
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
        {displayText: 'key_substring:', text: 'key_substring:'},
        {displayText: 'key:', text: 'key:'},
        {displayText: 'tag:', text: 'tag:'},
        {displayText: 'owner:', text: 'owner:'},
        {displayText: 'group:', text: 'group:'},
        {displayText: 'kind:', text: 'kind:'},
        {displayText: 'code_location:', text: 'code_location:'},
        {displayText: 'sinks()', text: 'sinks()'},
        {displayText: 'roots()', text: 'roots()'},
        {displayText: 'not', text: 'not '},
        {displayText: '+', text: '+'},
        {displayText: '(', text: '()'},
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
        },
        {
          displayText: 'and',
          text: 'and',
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
        },
        {
          displayText: 'or',
          text: 'or',
        },
      ],
      to: 35,
    });
  });

  it('suggests attribute names when cursor left of the colon', () => {
    expect(testAutocomplete('tag:"dagster/kind/fivetran" or t|:"a"')).toEqual({
      from: 31,
      list: [{displayText: 'tag:', text: 'tag:'}],
      to: 33,
    });
  });

  it('suggests attribute values when cursor left of the double quote', () => {
    expect(testAutocomplete('tag:"tag|"')).toEqual({
      from: 4,
      list: [
        {text: '"tag1"', displayText: 'tag1'},
        {text: '"tag2"', displayText: 'tag2'},
        {text: '"tag3"', displayText: 'tag3'},
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
          displayText: 'key_substring:',
          text: 'key_substring:',
        },
        {
          displayText: 'key:',
          text: 'key:',
        },
      ],
      to: 58,
    });

    expect(
      testAutocomplete('owner:"marco@dagsterlabs.com" or aiufhaifuhaguihaiugh key:"|"'),
    ).toEqual({
      from: 58,
      list: [
        {text: '"asset1"', displayText: 'asset1'},
        {text: '"asset2"', displayText: 'asset2'},
        {text: '"asset3"', displayText: 'asset3'},
      ],
      to: 60,
    });
  });

  it('handles complex ands/ors', () => {
    expect(testAutocomplete('key:"value"+ or tag:"value"+ and owner:"owner" and |')).toEqual({
      from: 51,
      list: [
        {
          displayText: 'key_substring:',
          text: 'key_substring:',
        },
        {
          displayText: 'key:',
          text: 'key:',
        },
        {
          displayText: 'tag:',
          text: 'tag:',
        },
        {
          displayText: 'owner:',
          text: 'owner:',
        },
        {
          displayText: 'group:',
          text: 'group:',
        },
        {
          displayText: 'kind:',
          text: 'kind:',
        },
        {
          displayText: 'code_location:',
          text: 'code_location:',
        },
        {
          displayText: 'sinks()',
          text: 'sinks()',
        },
        {
          displayText: 'roots()',
          text: 'roots()',
        },
        {
          displayText: 'not',
          text: 'not ',
        },
        {
          displayText: '+',
          text: '+',
        },
        {
          displayText: '(',
          text: '()',
        },
      ],
      to: 51,
    });
  });
});
