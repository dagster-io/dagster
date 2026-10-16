import {getNextSelectableIndex} from '../SelectionInput';
import {ResultItem} from '../SelectionInputAutoCompleteResults';

const suggestion = (text: string): ResultItem => ({text, jsx: text});
const recent = (text: string): ResultItem => ({type: 'recent', text, jsx: text});
const divider: ResultItem = {type: 'divider'};
const noMatch: ResultItem = {type: 'no-match', text: '', jsx: 'No match'};

// What the dropdown looks like with recent searches showing.
const withRecents: ResultItem[] = [
  recent('key:"a"'),
  recent('key:"b"'),
  divider,
  suggestion('key:'),
  suggestion('tag:'),
];

describe('getNextSelectableIndex', () => {
  it('starts at the first row when moving down from nothing selected', () => {
    expect(getNextSelectableIndex(withRecents, -1, 1)).toEqual(0);
  });

  it('starts at the last row when moving up from nothing selected', () => {
    expect(getNextSelectableIndex(withRecents, -1, -1)).toEqual(4);
  });

  it('skips the divider in both directions', () => {
    expect(getNextSelectableIndex(withRecents, 1, 1)).toEqual(3);
    expect(getNextSelectableIndex(withRecents, 3, -1)).toEqual(1);
  });

  it('wraps around the ends', () => {
    expect(getNextSelectableIndex(withRecents, 4, 1)).toEqual(0);
    expect(getNextSelectableIndex(withRecents, 0, -1)).toEqual(4);
  });

  it('skips a trailing divider when wrapping upward', () => {
    const list = [suggestion('key:'), divider];
    expect(getNextSelectableIndex(list, -1, -1)).toEqual(0);
  });

  it('skips "no match" rows, which would otherwise clear the current token', () => {
    const list = [suggestion('key:'), noMatch, suggestion('tag:')];
    expect(getNextSelectableIndex(list, 0, 1)).toEqual(2);
  });

  it('returns -1 when the list is empty or has nothing selectable', () => {
    expect(getNextSelectableIndex([], -1, 1)).toEqual(-1);
    expect(getNextSelectableIndex([divider, noMatch], -1, 1)).toEqual(-1);
  });
});
