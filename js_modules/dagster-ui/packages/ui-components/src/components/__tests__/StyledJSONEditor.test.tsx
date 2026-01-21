import {render, renderHook, screen} from '@testing-library/react';
import CodeMirror from 'codemirror';

import {StyledJSONEditor} from '../StyledJSONEditor';
import {useJsonValidator} from '../configeditor/codemirror-json/hooks/useJsonValidator';
import {createJsonExtraKeys} from '../configeditor/codemirror-json/utils/codeMirrorJsonUtils';

// --- Mocks ---

// Mock CodeMirror to avoid issues in test environment
jest.mock('codemirror/addon/edit/closebrackets', () => {});
jest.mock('codemirror/addon/edit/matchbrackets', () => {});
jest.mock('codemirror/addon/fold/brace-fold', () => {});
jest.mock('codemirror/addon/fold/foldcode', () => {});
jest.mock('codemirror/addon/fold/foldgutter', () => {});
jest.mock('codemirror/addon/fold/foldgutter.css', () => {});
jest.mock('codemirror/addon/lint/lint', () => {});
jest.mock('codemirror/addon/lint/lint.css', () => {});
jest.mock('codemirror/mode/javascript/javascript', () => {});

jest.mock('codemirror', () => {
  const mockEditor = {
    getCursor: jest.fn(() => ({line: 0, ch: 0})),
    getRange: jest.fn(() => ''),
    getLine: jest.fn(() => ''),
    getTokenAt: jest.fn(() => ({type: null, string: ''})),
    replaceSelection: jest.fn(),
    replaceRange: jest.fn(),
    setCursor: jest.fn(),
    execCommand: jest.fn(),
    getValue: jest.fn(() => ''),
    on: jest.fn(),
    off: jest.fn(),
    setValue: jest.fn(),
    somethingSelected: jest.fn(() => false),
    getSelection: jest.fn(() => ''),
  };

  const CM = jest.fn((_el, options) => {
    if (options && options.value) {
      mockEditor.getValue.mockReturnValue(options.value);
    }
    return mockEditor;
  });

  (CM as any).fromTextArea = jest.fn((_el, options) => {
    if (options && options.value) {
      mockEditor.getValue.mockReturnValue(options.value);
    }
    return mockEditor;
  });

  (CM as any).Pass = 'CodeMirror.Pass';

  return CM;
});

// Mock RawCodeMirror to focus testing on StyledJSONEditor logic (props passing)
jest.mock('../RawCodeMirror', () => ({
  RawCodeMirror: (props: any) => {
    return (
      <div
        data-testid="raw-codemirror"
        ref={(el) => {
          if (el) {
            (el as any)._options = props.options;
          }
        }}
        data-value={props.value}
      />
    );
  },
}));

// --- Tests ---

describe('useJsonValidator', () => {
  const ERROR_MESSAGES = {
    MUST_BE_OBJECT: 'JSON body must be an object {} or array [], not a primitive value',
    TRAILING_COMMA: 'Trailing comma is not allowed',
  };

  it('returns empty array for valid object JSON', () => {
    const {result} = renderHook(() => useJsonValidator());
    const validate = result.current;
    const errors = validate('{"a": 1}');
    expect(errors).toEqual([]);
  });

  it('returns empty array for valid array JSON', () => {
    const {result} = renderHook(() => useJsonValidator());
    const validate = result.current;
    const errors = validate('[1, 2]');
    expect(errors).toEqual([]);
  });

  it('returns empty array for empty string (handled by not validating)', () => {
    const {result} = renderHook(() => useJsonValidator());
    const validate = result.current;
    const errors = validate('   ');
    expect(errors).toEqual([]);
  });

  it('returns error for primitive values', () => {
    const {result} = renderHook(() => useJsonValidator());
    const validate = result.current;
    const errors = validate('123');
    expect(errors).toHaveLength(1);
    expect(errors?.[0]?.message).toBe(ERROR_MESSAGES.MUST_BE_OBJECT);
  });

  it('returns error for null', () => {
    const {result} = renderHook(() => useJsonValidator());
    const validate = result.current;
    const errors = validate('null');
    expect(errors).toHaveLength(1);
    expect(errors[0]?.message).toBe(ERROR_MESSAGES.MUST_BE_OBJECT);
  });

  it('detects trailing commas', () => {
    const {result} = renderHook(() => useJsonValidator());
    const validate = result.current;
    const errors = validate('{"a": 1,}');
    expect(errors).toHaveLength(1);
    expect(errors[0]?.message).toBe(ERROR_MESSAGES.TRAILING_COMMA);
    // Check approximate position if possible, but mainly message
    expect(errors[0]?.severity).toBe('error');
  });

  it('parses standard JSON.parse errors with position', () => {
    const {result} = renderHook(() => useJsonValidator());
    const validate = result.current;
    // Missing closing brace
    const errors = validate('{"a": 1');
    expect(errors.length).toBeGreaterThan(0);
    expect(errors[0]?.severity).toBe('error');
    // We expect some message about unexpected end or similar
  });

  it('provides smart suggestion for unquoted keys', () => {
    const {result} = renderHook(() => useJsonValidator());
    const validate = result.current;
    // Unquoted key 'a'
    const errors = validate('{a: 1}');
    expect(errors).toHaveLength(1);
    expect(errors[0]?.message).toContain("Unexpected token 'a'. Keys must be double-quoted.");
  });

  it('cleans up error messages', () => {
    const {result} = renderHook(() => useJsonValidator());
    const validate = result.current;
    // Intentionally bad syntax to trigger catch block
    const errors = validate('{');
    expect(errors).toHaveLength(1);
    expect(errors[0]?.message).not.toMatch(/^JSON\.parse:/);
    expect(errors[0]?.message).not.toMatch(/at position \d+/);
  });
});

describe('createJsonExtraKeys', () => {
  const extraKeys = createJsonExtraKeys();
  let mockCm: any;

  beforeEach(() => {
    // @ts-expect-error - Mock call
    mockCm = CodeMirror();
    jest.clearAllMocks();
    // Reset default behaviors that might have been changed by tests
    mockCm.somethingSelected.mockReturnValue(false);
    mockCm.getCursor.mockReturnValue({line: 0, ch: 0});
    mockCm.getLine.mockReturnValue('');
    mockCm.getTokenAt.mockReturnValue({type: null, string: ''});
    mockCm.getSelection.mockReturnValue('');
    mockCm.getRange.mockReturnValue('');
  });

  describe('Enter key', () => {
    it('handles Enter between braces { | }', () => {
      mockCm.getCursor.mockReturnValue({line: 0, ch: 1});
      mockCm.getLine.mockReturnValue('{}');

      const enterHandler = extraKeys.Enter as (cm: CodeMirror.Editor) => void;
      enterHandler(mockCm);

      expect(mockCm.replaceSelection).toHaveBeenCalledWith('\n  \n');
      expect(mockCm.setCursor).toHaveBeenCalledWith({line: 1, ch: 2});
    });

    it('handles Enter between brackets [ | ]', () => {
      mockCm.getCursor.mockReturnValue({line: 0, ch: 1});
      mockCm.getLine.mockReturnValue('[]');

      const enterHandler = extraKeys.Enter as (cm: CodeMirror.Editor) => void;
      enterHandler(mockCm);

      expect(mockCm.replaceSelection).toHaveBeenCalledWith('\n  \n');
    });

    it('handles Enter after opening brace { |', () => {
      mockCm.getCursor.mockReturnValue({line: 0, ch: 1});
      // The logic checks BEFORE cursor, so line content matters
      mockCm.getLine.mockReturnValue('{');

      const enterHandler = extraKeys.Enter as (cm: CodeMirror.Editor) => void;
      enterHandler(mockCm);

      expect(mockCm.replaceSelection).toHaveBeenCalledWith('\n  ');
      expect(mockCm.setCursor).toHaveBeenCalledWith({line: 1, ch: 2});
    });

    it('handles Enter normally otherwise', () => {
      mockCm.getCursor.mockReturnValue({line: 0, ch: 5});
      mockCm.getLine.mockReturnValue('"abc"');

      const enterHandler = extraKeys.Enter as (cm: CodeMirror.Editor) => void;
      enterHandler(mockCm);

      expect(mockCm.execCommand).toHaveBeenCalledWith('newlineAndIndent');
    });
  });

  describe('Backspace key', () => {
    it('deletes pair if cursor is between matching characters', () => {
      mockCm.somethingSelected.mockReturnValue(false);
      mockCm.getCursor.mockReturnValue({line: 0, ch: 1});
      // Mock getRange to return before/after chars
      mockCm.getRange
        .mockReturnValueOnce('{') // before
        .mockReturnValueOnce('}'); // after

      const backspaceHandler = extraKeys.Backspace as (cm: CodeMirror.Editor) => void;
      const result = backspaceHandler(mockCm);

      expect(mockCm.replaceRange).toHaveBeenCalledWith('', {line: 0, ch: 1}, {line: 0, ch: 2});
      expect(result).toBe('CodeMirror.Pass'); // Should still return Pass to let CM handle other things?
      // Actually code returns Pass, but we check side effect replaceRange
    });

    it('does nothing special if characters do not match', () => {
      mockCm.somethingSelected.mockReturnValue(false);
      mockCm.getCursor.mockReturnValue({line: 0, ch: 1});
      mockCm.getRange.mockReturnValueOnce('{').mockReturnValueOnce(' ');

      const backspaceHandler = extraKeys.Backspace as (cm: CodeMirror.Editor) => void;
      backspaceHandler(mockCm);

      expect(mockCm.replaceRange).not.toHaveBeenCalled();
    });

    it('does nothing special if selection exists', () => {
      mockCm.somethingSelected.mockReturnValue(true);
      const backspaceHandler = extraKeys.Backspace as (cm: CodeMirror.Editor) => void;
      backspaceHandler(mockCm);
      expect(mockCm.replaceRange).not.toHaveBeenCalled();
    });
  });

  describe('Auto-close characters', () => {
    it('auto-closes {', () => {
      mockCm.getCursor.mockReturnValue({line: 0, ch: 0});
      mockCm.getTokenAt.mockReturnValue({type: null});

      const handler = extraKeys["'{'"] as (cm: CodeMirror.Editor) => void;
      handler(mockCm);

      expect(mockCm.replaceSelection).toHaveBeenCalledWith('{}');
      expect(mockCm.execCommand).toHaveBeenCalledWith('goCharLeft');
    });

    it('wraps selection with { }', () => {
      mockCm.somethingSelected.mockReturnValue(true);
      mockCm.getSelection.mockReturnValue('foo');
      mockCm.getTokenAt.mockReturnValue({type: null});

      const handler = extraKeys["'{'"] as (cm: CodeMirror.Editor) => void;
      handler(mockCm);

      expect(mockCm.replaceSelection).toHaveBeenCalledWith('{foo}');
      expect(mockCm.execCommand).not.toHaveBeenCalledWith('goCharLeft');
    });

    it('overwrites if typing closing char } when next char is }', () => {
      // This is for handleClose '}'
      mockCm.getCursor.mockReturnValue({line: 0, ch: 0});
      mockCm.getRange.mockReturnValue('}'); // Next char is }

      const handler = extraKeys["'}'"] as (cm: CodeMirror.Editor) => void;
      handler(mockCm);

      expect(mockCm.execCommand).toHaveBeenCalledWith('goCharRight');
      expect(mockCm.replaceSelection).not.toHaveBeenCalled();
    });

    it('inserts closing char } if next char is NOT }', () => {
      mockCm.getCursor.mockReturnValue({line: 0, ch: 0});
      mockCm.getRange.mockReturnValue(' ');

      const handler = extraKeys["'}'"] as (cm: CodeMirror.Editor) => void;
      handler(mockCm);

      expect(mockCm.replaceSelection).toHaveBeenCalledWith('}');
    });

    it('does NOT auto-close if in string', () => {
      mockCm.getCursor.mockReturnValue({line: 0, ch: 5});
      mockCm.getTokenAt.mockReturnValue({type: 'string'});

      const handler = extraKeys["'{'"] as (cm: CodeMirror.Editor) => void;
      handler(mockCm);

      expect(mockCm.replaceSelection).toHaveBeenCalledWith('{'); // Just insert, no auto-close pair
    });

    it('overwrites quote " if next char is "', () => {
      // handleOpen for quotes has specific overwrite logic
      mockCm.getCursor.mockReturnValue({line: 0, ch: 0});
      mockCm.getRange.mockReturnValue('"');

      const handler = extraKeys["'\"'"] as (cm: CodeMirror.Editor) => void; // Key for "
      handler(mockCm);

      expect(mockCm.execCommand).toHaveBeenCalledWith('goCharRight');
    });
  });

  describe('Navigation', () => {
    it('handles Tab as indentMore', () => {
      const handler = extraKeys.Tab as (cm: CodeMirror.Editor) => void;
      handler(mockCm);
      expect(mockCm.execCommand).toHaveBeenCalledWith('indentMore');
    });

    it('handles Shift-Tab as indentLess', () => {
      const handler = extraKeys['Shift-Tab'] as (cm: CodeMirror.Editor) => void;
      handler(mockCm);
      expect(mockCm.execCommand).toHaveBeenCalledWith('indentLess');
    });
  });
});

describe('StyledJSONEditor', () => {
  it('renders with default options', () => {
    render(<StyledJSONEditor value="{}" />);
    const editor = screen.getByTestId('raw-codemirror');
    expect(editor).toBeInTheDocument();

    const options = (editor as any)._options;
    expect(options).toMatchObject({
      mode: {name: 'javascript', json: true},
      lineNumbers: true,
      smartIndent: true,
      indentUnit: 2,
    });
  });

  it('merges custom extraKeys', () => {
    const customFn = jest.fn();
    render(<StyledJSONEditor value="" options={{extraKeys: {Enter: customFn}} as any} />);
    const editor = screen.getByTestId('raw-codemirror');
    const options = (editor as any)._options;

    // Check that our default keys exist (like Tab) AND custom key matches
    expect(options.extraKeys).toHaveProperty('Tab');

    // Note: Since we merge defaultExtraKeys and propExtraKeys, the 'Enter' key in options
    // should ideally overwrite the one in defaultExtraKeys.
    // Let's verify it matches the custom one we passed.
    expect(options.extraKeys.Enter).toBe(customFn);
  });

  it('handles string theme', () => {
    render(<StyledJSONEditor value="" theme="my-theme" />);
    const editor = screen.getByTestId('raw-codemirror');
    const options = (editor as any)._options;
    expect(options.theme).toBe('my-theme dagster');
  });

  it('handles array theme', () => {
    render(<StyledJSONEditor value="" theme={['foo', 'bar']} />);
    const editor = screen.getByTestId('raw-codemirror');
    const options = (editor as any)._options;
    expect(options.theme).toBe('foo bar dagster');
  });

  it('passes handlers (onChange, onReady)', () => {
    const changeFn = jest.fn();
    const readyFn = jest.fn();
    render(<StyledJSONEditor value="" onChange={changeFn} onReady={readyFn} />);

    // We can't strictly assert internal handler creation with this mock structure
    // without exposing more internals, but we can verify component renders without error
    const editor = screen.getByTestId('raw-codemirror');
    expect(editor).toBeInTheDocument();
  });
});
