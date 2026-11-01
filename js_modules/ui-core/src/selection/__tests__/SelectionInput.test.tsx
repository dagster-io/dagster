import {act, fireEvent, render, screen, waitFor} from '@testing-library/react';
import {Editor} from 'codemirror';
import {ComponentProps} from 'react';
import {MemoryRouter} from 'react-router-dom';

import {AssetSelectionLexer} from '../../asset-selection/generated/AssetSelectionLexer';
import {AssetSelectionParser} from '../../asset-selection/generated/AssetSelectionParser';
import {
  createSelectionAutoComplete,
  useSelectionAutoCompleteResults,
} from '../SelectionAutoComplete';
import {SelectionAutoCompleteProvider, createProvider} from '../SelectionAutoCompleteProvider';
import {SelectionAutoCompleteInput} from '../SelectionInput';
import {createSelectionLinter} from '../createSelectionLinter';

// jsdom has no layout APIs, and CodeMirror measures text with ranges and focuses the window.
Range.prototype.getBoundingClientRect = () =>
  ({top: 0, right: 0, bottom: 0, left: 0, width: 0, height: 0, x: 0, y: 0}) as DOMRect;
Range.prototype.getClientRects = () => [] as unknown as DOMRectList;
window.focus = jest.fn();

type EditorElement = HTMLElement & {
  CodeMirror: Editor;
};

const useAutoComplete = () => ({
  autoCompleteResults: {from: 0, to: 0, list: []},
  loading: false,
});

const ownerHint = createSelectionAutoComplete(
  createProvider({
    attributesMap: {owner: ['ben@dagsterlabs.com']},
    attributeToIcon: {owner: 'magnify_glass'},
  }),
);

const useOwnerAutoComplete: SelectionAutoCompleteProvider['useAutoComplete'] = ({
  line,
  cursorIndex,
}) => ({
  autoCompleteResults: useSelectionAutoCompleteResults(ownerHint, line, cursorIndex),
  loading: false,
});

const linter = () => [];

const assetLinter = createSelectionLinter({
  Lexer: AssetSelectionLexer,
  Parser: AssetSelectionParser,
  supportedAttributes: ['key'],
});

type InputOptions = Partial<
  Pick<
    ComponentProps<typeof SelectionAutoCompleteInput>,
    'linter' | 'wildcardAttributeName' | 'useAutoComplete' | 'onFocus'
  >
>;

const renderInput = (value: string, options: InputOptions = {}) => {
  const onChange = jest.fn();
  const buildInput = (nextValue: string, nextOptions: InputOptions = options) => (
    <MemoryRouter>
      <SelectionAutoCompleteInput
        id="test"
        placeholder="Search and filter things"
        value={nextValue}
        onChange={onChange}
        linter={nextOptions.linter ?? linter}
        wildcardAttributeName={nextOptions.wildcardAttributeName}
        useAutoComplete={nextOptions.useAutoComplete ?? useAutoComplete}
        onFocus={nextOptions.onFocus}
      />
    </MemoryRouter>
  );
  const result = render(buildInput(value));
  const editorElement = result.container.querySelector<EditorElement>('.CodeMirror');
  if (!editorElement) {
    throw new Error('CodeMirror did not render');
  }
  const editor = editorElement.CodeMirror;
  return {
    ...result,
    editor,
    onChange,
    rerenderWithValue: (nextValue: string) => result.rerender(buildInput(nextValue)),
    rerenderWithOptions: (nextOptions: InputOptions) =>
      result.rerender(buildInput(value, nextOptions)),
  };
};

const pressEnter = () => fireEvent.keyDown(screen.getByRole('textbox'), {key: 'Enter'});

describe('SelectionAutoCompleteInput', () => {
  it('keeps repeated spaces inside quotes when typed', () => {
    const {editor, onChange} = renderInput('');
    act(() => {
      editor.replaceRange('tag:team="data  science"', {line: 0, ch: 0}, undefined, '+input');
    });
    pressEnter();
    expect(onChange).toHaveBeenCalledWith('tag:team="data  science"');
  });

  it('shows a value with repeated spaces as given and does not mark it uncommitted', async () => {
    const value = 'tag:team="data  science"';
    const {container, editor, onChange, rerenderWithValue} = renderInput('a');
    rerenderWithValue(value);
    await waitFor(() => expect(editor.getValue()).toBe(value));
    expect(container.querySelector('.uncommitted')).toBeNull();
    pressEnter();
    expect(onChange).toHaveBeenCalledWith(value);
  });

  it.each([
    {lineBreak: 'LF', text: 'a\nb'},
    {lineBreak: 'CRLF', text: 'a\r\nb'},
    {lineBreak: 'CR', text: 'a\rb'},
  ])(
    'joins a multi-line $lineBreak paste into one line and keeps the cursor after it',
    ({text}) => {
      const {editor} = renderInput('xy');
      act(() => {
        editor.setCursor({line: 0, ch: 1});
        editor.replaceSelection(text, 'end', 'paste');
      });
      expect(editor.lineCount()).toBe(1);
      expect(editor.getValue()).toBe('xa by');
      expect(editor.getCursor()).toEqual(expect.objectContaining({line: 0, ch: 4}));
    },
  );

  it.each([
    {lineBreak: 'LF', value: 'a\nb'},
    {lineBreak: 'CRLF', value: 'a\r\nb'},
    {lineBreak: 'CR', value: 'a\rb'},
  ])('shows a multi-line $lineBreak initial value on one line', ({value}) => {
    const {editor} = renderInput(value);
    expect(editor.lineCount()).toBe(1);
    expect(editor.getValue()).toBe('a b');
  });

  it('commits the upgraded text when it passes the linter', () => {
    const {editor, onChange} = renderInput('', {
      linter: assetLinter,
      wildcardAttributeName: 'key',
    });
    act(() => {
      editor.replaceRange('foo bar', {line: 0, ch: 0}, undefined, '+input');
    });
    pressEnter();
    expect(onChange).toHaveBeenCalledWith('key:"*foo*"  or key:"*bar*"');
  });

  it('commits the typed text when the upgraded text fails the linter', () => {
    const {editor, onChange} = renderInput('', {
      linter: assetLinter,
      wildcardAttributeName: 'key',
    });
    act(() => {
      editor.replaceRange('(a-b', {line: 0, ch: 0}, undefined, '+input');
    });
    pressEnter();
    expect(onChange).toHaveBeenCalledWith('(a-b');
  });

  it('replaces the value with its quoted form when the quoted suggestion is chosen', () => {
    const {editor} = renderInput('', {useAutoComplete: useOwnerAutoComplete});
    act(() => {
      editor.replaceRange('owner:zzz@q', {line: 0, ch: 0}, undefined, '+input');
    });
    fireEvent.keyDown(screen.getByRole('textbox'), {key: 'ArrowDown'});
    pressEnter();
    expect(editor.getValue()).toBe('owner:"zzz@q" ');
  });

  it('calls the latest onFocus each time the editor gains focus', () => {
    const onFocus = jest.fn();
    const {editor, rerenderWithOptions} = renderInput('', {onFocus});
    act(() => editor.focus());
    expect(onFocus).toHaveBeenCalledTimes(1);

    const nextOnFocus = jest.fn();
    rerenderWithOptions({onFocus: nextOnFocus});
    act(() => editor.getInputField().blur());
    act(() => editor.focus());
    expect(nextOnFocus).toHaveBeenCalledTimes(1);
    expect(onFocus).toHaveBeenCalledTimes(1);
  });

  it('names the editor after its placeholder', () => {
    renderInput('');
    expect(screen.getByRole('textbox', {name: 'Search and filter things'})).toBeInTheDocument();
  });
});
