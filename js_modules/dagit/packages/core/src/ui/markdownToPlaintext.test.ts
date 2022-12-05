import {markdownToPlaintext} from './markdownToPlaintext';

describe('markdownToPlaintext', () => {
  it('correctly converts markdown to plaintext', () => {
    expect(markdownToPlaintext('lorem ipsum')).toBe('lorem ipsum');
    expect(markdownToPlaintext('## lorem ipsum')).toBe('lorem ipsum');
    expect(markdownToPlaintext('- lorem ipsum')).toBe('lorem ipsum');
    expect(
      markdownToPlaintext(
        `# Hello World
- a list of things
  - with indentation`,
      ),
    ).toBe(
      `Hello World
a list of things
with indentation`,
    );
  });

  it('does not leave any escaping charaters lying around', () => {
    expect(markdownToPlaintext('The S&P 500')).toBe('The S&P 500');
    expect(markdownToPlaintext('"Don\'t quote me on that"')).toBe('"Don\'t quote me on that"');
    expect(markdownToPlaintext('underscore _ and _ stuff')).toBe('underscore _ and _ stuff');
  });
});
