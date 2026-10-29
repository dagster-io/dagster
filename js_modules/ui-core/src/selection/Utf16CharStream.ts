import {CharStream, IntStream, Interval, Token} from 'antlr4ng';

/**
 * A `CharStream` that feeds the lexer one UTF-16 code unit at a time.
 *
 * - **Why:** antlr4ng's `CharStream.fromString` indexes by code point, but token offsets are used
 *   to slice JS strings and to place CodeMirror marks, and both count UTF-16 units. With code
 *   points, each emoji earlier in the input shifts every later offset by one.
 * - **How:** `LA` returns `charCodeAt`, so an emoji arrives as two surrogate halves. Every other
 *   method matches antlr4ng's `CharStreamImpl`.
 * - **Grammar constraint:** lexer rules only see code units, so they must stick to ASCII sets and
 *   negated sets (as all selection grammars do today). A negated set like `~["\r\n]` matches both
 *   surrogate halves, which keeps emoji inside quoted values working. A rule naming a character
 *   above U+FFFF would never match.
 */
export class Utf16CharStream implements CharStream {
  name = '';
  index = 0;

  constructor(private readonly text: string) {}

  get size() {
    return this.text.length;
  }

  reset() {
    this.index = 0;
  }

  consume() {
    if (this.index >= this.text.length) {
      throw new Error('cannot consume EOF');
    }
    this.index += 1;
  }

  LA(offset: number) {
    if (offset === 0) {
      return 0;
    }
    const pos = this.index + (offset < 0 ? offset : offset - 1);
    return pos < 0 || pos >= this.text.length ? Token.EOF : this.text.charCodeAt(pos);
  }

  mark() {
    return -1;
  }

  release() {}

  seek(index: number) {
    this.index = Math.min(index, this.text.length);
  }

  getTextFromRange(start: number, stop = this.text.length - 1) {
    return this.text.slice(start, stop + 1);
  }

  getTextFromInterval(interval: Interval) {
    return this.getTextFromRange(interval.start, interval.stop);
  }

  getSourceName() {
    return this.name || IntStream.UNKNOWN_SOURCE_NAME;
  }

  toString() {
    return this.text;
  }
}
