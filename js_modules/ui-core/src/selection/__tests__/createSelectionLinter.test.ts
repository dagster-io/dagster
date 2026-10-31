import {AssetSelectionLexer} from '../../asset-selection/generated/AssetSelectionLexer';
import {AssetSelectionParser} from '../../asset-selection/generated/AssetSelectionParser';
import {createSelectionLinter} from '../createSelectionLinter';

const supportedAttributes = ['key', 'kind'];
const unsupportedAttributeMessages = {
  tag: 'tag filtering is not supported in this test',
  column: 'column filtering is not supported in this test',
};

const linter = createSelectionLinter({
  Lexer: AssetSelectionLexer,
  Parser: AssetSelectionParser,
  supportedAttributes,
  unsupportedAttributeMessages,
});

describe('createSelectionLinter', () => {
  it('returns a linter function', () => {
    expect(typeof linter).toBe('function');
  });

  it('handles empty input', () => {
    const errors = linter('');
    expect(errors).toEqual([]);
  });

  it('handles valid input with supported attributes', () => {
    const input = 'key:value';
    const errors = linter(input);
    expect(errors).toEqual([]);
  });

  it('handles multiple unsupported attributes', () => {
    const input = 'tag:value or column:value or table_name:value';
    const errors = linter(input);
    expect(errors).toEqual([
      {
        message: 'tag filtering is not supported in this test',
        from: 0,
        to: 'tag'.length,
      },
      {
        message: 'column filtering is not supported in this test',
        from: 'tag:value or '.length,
        to: 'tag:value or column'.length,
      },
      {
        message: 'Unsupported attribute: "table_name"', // default message
        from: 'tag:value or column:value or '.length,
        to: 'tag:value or column:value or table_name'.length,
      },
    ]);
  });

  it('does not report unsupported attributes when they overlap with syntax errors', () => {
    const mockLinter = createSelectionLinter({
      Lexer: AssetSelectionLexer,
      Parser: AssetSelectionParser,
      supportedAttributes,
    });

    const input = 'fake:value';
    const errors = mockLinter(input);

    // Only expect syntax errors, not attribute errors
    expect(errors).toEqual([
      expect.objectContaining({
        from: 0,
        offendingSymbol: 'fake',
        to: Infinity,
      }),
    ]);
  });

  it.each([
    {input: 'key:ben@', character: '@', from: 7},
    {input: 'key:a$', character: '$', from: 5},
    {input: 'key:😀a', character: '😀', from: 4},
  ])('reports the character the lexer rejects in $input', ({input, character, from}) => {
    expect(linter(input)).toEqual([
      {message: `token recognition error at: '${character}'`, from, to: Infinity},
    ]);
  });

  it.each([
    {
      input: 'key:😀😀',
      errors: [
        {character: '😀', from: 4},
        {character: '😀', from: 6},
      ],
    },
    {input: 'key:𝒜', errors: [{character: '𝒜', from: 4}]},
    {input: 'key:\ud83d', errors: [{character: '\ud83d', from: 4}]},
  ])('reports one error per rejected character in $input', ({input, errors}) => {
    expect(linter(input)).toEqual([
      ...errors.map(({character, from}) => ({
        message: `token recognition error at: '${character}'`,
        from,
        to: Infinity,
      })),
      {
        message: "no viable alternative at input 'key:'",
        offendingSymbol: '<EOF>',
        from: 0,
        to: Infinity,
      },
    ]);
  });

  // Error columns restart on each line, so a later error can share a column with an emoji's half.
  it.each([
    {above: 'a rejected emoji', input: 'key:😀a\nkey:b$', characters: ['😀', '$']},
    {above: 'a quoted emoji', input: 'key:"😀"\nkey:a$$', characters: ['$', '$']},
  ])('keeps each error on a line below $above', ({input, characters}) => {
    expect(linter(input).map(({message}) => message)).toEqual([
      ...characters.map((character) => `token recognition error at: '${character}'`),
      "mismatched input 'key' expecting <EOF>",
    ]);
  });
});
