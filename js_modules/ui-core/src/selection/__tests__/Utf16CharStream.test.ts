import {AssetSelectionLexer} from '../../asset-selection/generated/AssetSelectionLexer';
import {AutomationSelectionLexer} from '../../automation-selection/generated/AutomationSelectionLexer';
import {JobSelectionLexer} from '../../job-selection/generated/JobSelectionLexer';
import {OpSelectionLexer} from '../../op-selection/generated/OpSelectionLexer';
import {RunSelectionLexer} from '../../run-selection/generated/RunSelectionLexer';
import {Utf16CharStream} from '../Utf16CharStream';
import {SelectionAutoCompleteLexer} from '../generated/SelectionAutoCompleteLexer';

describe('Utf16CharStream', () => {
  it('indexes by UTF-16 code unit', () => {
    const stream = new Utf16CharStream('a😀b');
    expect(stream.size).toBe(4);
    expect(stream.getTextFromRange(1, 2)).toBe('😀');
  });

  it('reads to the end when no stop is given', () => {
    expect(new Utf16CharStream('abc').getTextFromRange(1)).toBe('bc');
  });

  // The stream feeds lexers one code unit at a time, so a rule naming a character above U+FFFF
  // would never match.
  it.each([
    ['SelectionAutoComplete', SelectionAutoCompleteLexer],
    ['AssetSelection', AssetSelectionLexer],
    ['AutomationSelection', AutomationSelectionLexer],
    ['JobSelection', JobSelectionLexer],
    ['OpSelection', OpSelectionLexer],
    ['RunSelection', RunSelectionLexer],
  ])('%s lexer only names characters that fit in one code unit', (_, lexer) => {
    const labels = lexer._ATN.states.flatMap((state) =>
      (state?.transitions ?? []).flatMap(({label}) => (label ? [label.maxElement] : [])),
    );
    expect(Math.max(...labels)).toBeLessThanOrEqual(0xffff);
  });
});
