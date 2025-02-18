import CodeMirror from 'codemirror';

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
        severity: 'error',
        from: CodeMirror.Pos(0, 0),
        to: CodeMirror.Pos(0, 'tag'.length),
      },
      {
        message: 'column filtering is not supported in this test',
        severity: 'error',
        from: CodeMirror.Pos(0, 'tag:value or '.length),
        to: CodeMirror.Pos(0, 'tag:value or column'.length),
      },
      {
        message: 'Unsupported attribute: table_name', // default message
        severity: 'error',
        from: CodeMirror.Pos(0, 'tag:value or column:value or '.length),
        to: CodeMirror.Pos(0, 'tag:value or column:value or table_name'.length),
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
        from: CodeMirror.Pos(0, 0),
        message: expect.stringContaining("mismatched input 'fake'"),
        severity: 'error',
        to: CodeMirror.Pos(0, 10),
      }),
    ]);
  });
});
