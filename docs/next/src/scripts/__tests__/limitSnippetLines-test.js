const limitSnippetLines = require('../limitSnippetLines');

const TEST_CONTENT_LINES = ['line 1', 'indistinguishable', 'line 3', 'line 4', 'line 5', 'indistinguishable',];
const TEST_CONTENT_STR = TEST_CONTENT_LINES.join('\n');

const TEST_CONTENT_STR_INDENTED = TEST_CONTENT_LINES.map(line => `    ${line}`).join('\n');

expect.extend({
    toMatchTestContentForLines(observed, ...lineNumbers) {
        let expected = lineNumbers.map(i => TEST_CONTENT_LINES[i - 1]).join('\n');
        expect(observed).toEqual(expected);
        return { pass: !this.isNot }
    }
})

test('returns the content unchanged by default', () => {
    expect(limitSnippetLines(TEST_CONTENT_STR)).toBe(TEST_CONTENT_STR);
});

test('works will all options in use', () => {
    expect(limitSnippetLines(TEST_CONTENT_STR_INDENTED, '2', 4, 'indistinguishable', 'line 5')).toMatchTestContentForLines(4)
})

test('works with simple fromTo', () => {
    expect(limitSnippetLines(TEST_CONTENT_STR, '2-3')).toMatchTestContentForLines(2, 3);
});

test('works with fromTo specifying open ended ranges', () => {
    expect(limitSnippetLines(TEST_CONTENT_STR, '2-')).toMatchTestContentForLines(2, 3, 4, 5, 6);
    expect(limitSnippetLines(TEST_CONTENT_STR, '-2')).toMatchTestContentForLines(1, 2);
});

test('works with fromTo specifying individual lines', () => {
    expect(limitSnippetLines(TEST_CONTENT_STR, '2,4')).toMatchTestContentForLines(2, 4);
});

test('works with fromTo specifying combination of individual lines and ranges', () => {
    expect(limitSnippetLines(TEST_CONTENT_STR, '1-2,4')).toMatchTestContentForLines(1, 2, 4);
});

test('dedents correctly', () => {
    expect(limitSnippetLines(TEST_CONTENT_STR_INDENTED, null, 4)).toBe(TEST_CONTENT_STR);
});

test('selects only lines after first instance of `startAfter`', () => {
    expect(limitSnippetLines(TEST_CONTENT_STR, null, 0, 'line 3')).toMatchTestContentForLines(4, 5, 6);
    expect(limitSnippetLines(TEST_CONTENT_STR, null, 0, 'indistinguishable')).toMatchTestContentForLines(3, 4, 5, 6);
});

test('selects only lines before first instance of `endBefore`', () => {
    expect(limitSnippetLines(TEST_CONTENT_STR, null, 0, null, 'indistinguishable')).toMatchTestContentForLines(1);
    expect(limitSnippetLines(TEST_CONTENT_STR, null, 0, null, 'line 4')).toMatchTestContentForLines(1, 2, 3);
});

test('selects only lines between `startAfter` and `endBefore`', () => {
    expect(limitSnippetLines(TEST_CONTENT_STR, null, 0, 'line 1', 'line 4')).toMatchTestContentForLines(2, 3);
    expect(limitSnippetLines(TEST_CONTENT_STR, null, 0, 'line 3', 'line 5')).toMatchTestContentForLines(4);
});

test('select lines ending before the next instance of `endBefore` after `startAfter` (applies `startAfter` first)', () => {
    expect(limitSnippetLines(TEST_CONTENT_STR, null, 0, 'line 4', 'indistinguishable')).toMatchTestContentForLines(5);
})

test('fails when `startAfter` or `endBefore` value does not appear in content', () => {
    expect(() => limitSnippetLines(TEST_CONTENT_STR, null, 0, '<not in content>')).toThrowError(/No match for startAfter value/);
    expect(() => limitSnippetLines(TEST_CONTENT_STR, null, 0, null, '<not in content>')).toThrowError(/No match for endBefore value/);
});

test('fails when `endBefore` occurs before `startAfter`', () => {
    expect(() => limitSnippetLines(TEST_CONTENT_STR, null, 0, 'line 4', 'line 1')).toThrowError(/No match for endBefore value/);
});

test('selects lines ranges relative to `startAfter` and `endBefore`', () => {
    expect(limitSnippetLines(TEST_CONTENT_STR, '1', 0, 'line 1', 'line 4')).toMatchTestContentForLines(2);
    expect(limitSnippetLines(TEST_CONTENT_STR, '2-3', 0, 'line 1', 'line 5')).toMatchTestContentForLines(3, 4);
});