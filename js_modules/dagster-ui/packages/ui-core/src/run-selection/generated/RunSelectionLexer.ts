// Generated from /home/user/dagster/js_modules/dagster-ui/packages/ui-core/src/run-selection/RunSelection.g4 by ANTLR 4.13.1

import * as antlr from 'antlr4ng';
import {Token} from 'antlr4ng';

export class RunSelectionLexer extends antlr.Lexer {
  public static readonly AND = 1;
  public static readonly OR = 2;
  public static readonly NOT = 3;
  public static readonly STAR = 4;
  public static readonly PLUS = 5;
  public static readonly DIGITS = 6;
  public static readonly COLON = 7;
  public static readonly LPAREN = 8;
  public static readonly RPAREN = 9;
  public static readonly NAME = 10;
  public static readonly STATUS = 11;
  public static readonly SINKS = 12;
  public static readonly ROOTS = 13;
  public static readonly QUOTED_STRING = 14;
  public static readonly UNQUOTED_STRING = 15;
  public static readonly UNQUOTED_WILDCARD_STRING = 16;
  public static readonly WS = 17;

  public static readonly channelNames = ['DEFAULT_TOKEN_CHANNEL', 'HIDDEN'];

  public static readonly literalNames = [
    null,
    null,
    null,
    null,
    "'*'",
    "'+'",
    null,
    "':'",
    "'('",
    "')'",
    "'name'",
    "'status'",
    "'sinks'",
    "'roots'",
  ];

  public static readonly symbolicNames = [
    null,
    'AND',
    'OR',
    'NOT',
    'STAR',
    'PLUS',
    'DIGITS',
    'COLON',
    'LPAREN',
    'RPAREN',
    'NAME',
    'STATUS',
    'SINKS',
    'ROOTS',
    'QUOTED_STRING',
    'UNQUOTED_STRING',
    'UNQUOTED_WILDCARD_STRING',
    'WS',
  ];

  public static readonly modeNames = ['DEFAULT_MODE'];

  public static readonly ruleNames = [
    'AND',
    'OR',
    'NOT',
    'STAR',
    'PLUS',
    'DIGITS',
    'COLON',
    'LPAREN',
    'RPAREN',
    'NAME',
    'STATUS',
    'SINKS',
    'ROOTS',
    'QUOTED_STRING',
    'UNQUOTED_STRING',
    'UNQUOTED_WILDCARD_STRING',
    'WS',
  ];

  public constructor(input: antlr.CharStream) {
    super(input);
    this.interpreter = new antlr.LexerATNSimulator(
      this,
      RunSelectionLexer._ATN,
      RunSelectionLexer.decisionsToDFA,
      new antlr.PredictionContextCache(),
    );
  }

  public get grammarFileName(): string {
    return 'RunSelection.g4';
  }

  public get literalNames(): (string | null)[] {
    return RunSelectionLexer.literalNames;
  }
  public get symbolicNames(): (string | null)[] {
    return RunSelectionLexer.symbolicNames;
  }
  public get ruleNames(): string[] {
    return RunSelectionLexer.ruleNames;
  }

  public get serializedATN(): number[] {
    return RunSelectionLexer._serializedATN;
  }

  public get channelNames(): string[] {
    return RunSelectionLexer.channelNames;
  }

  public get modeNames(): string[] {
    return RunSelectionLexer.modeNames;
  }

  public static readonly _serializedATN: number[] = [
    4, 0, 17, 126, 6, -1, 2, 0, 7, 0, 2, 1, 7, 1, 2, 2, 7, 2, 2, 3, 7, 3, 2, 4, 7, 4, 2, 5, 7, 5, 2,
    6, 7, 6, 2, 7, 7, 7, 2, 8, 7, 8, 2, 9, 7, 9, 2, 10, 7, 10, 2, 11, 7, 11, 2, 12, 7, 12, 2, 13, 7,
    13, 2, 14, 7, 14, 2, 15, 7, 15, 2, 16, 7, 16, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 3, 0, 42, 8,
    0, 1, 1, 1, 1, 1, 1, 1, 1, 3, 1, 48, 8, 1, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 3, 2, 56, 8, 2,
    1, 3, 1, 3, 1, 4, 1, 4, 1, 5, 4, 5, 63, 8, 5, 11, 5, 12, 5, 64, 1, 6, 1, 6, 1, 7, 1, 7, 1, 8, 1,
    8, 1, 9, 1, 9, 1, 9, 1, 9, 1, 9, 1, 10, 1, 10, 1, 10, 1, 10, 1, 10, 1, 10, 1, 10, 1, 11, 1, 11,
    1, 11, 1, 11, 1, 11, 1, 11, 1, 12, 1, 12, 1, 12, 1, 12, 1, 12, 1, 12, 1, 13, 1, 13, 5, 13, 99,
    8, 13, 10, 13, 12, 13, 102, 9, 13, 1, 13, 1, 13, 1, 14, 1, 14, 5, 14, 108, 8, 14, 10, 14, 12,
    14, 111, 9, 14, 1, 15, 1, 15, 5, 15, 115, 8, 15, 10, 15, 12, 15, 118, 9, 15, 1, 16, 4, 16, 121,
    8, 16, 11, 16, 12, 16, 122, 1, 16, 1, 16, 0, 0, 17, 1, 1, 3, 2, 5, 3, 7, 4, 9, 5, 11, 6, 13, 7,
    15, 8, 17, 9, 19, 10, 21, 11, 23, 12, 25, 13, 27, 14, 29, 15, 31, 16, 33, 17, 1, 0, 7, 1, 0, 48,
    57, 4, 0, 10, 10, 13, 13, 34, 34, 92, 92, 3, 0, 65, 90, 95, 95, 97, 122, 4, 0, 48, 57, 65, 90,
    95, 95, 97, 122, 4, 0, 42, 42, 65, 90, 95, 95, 97, 122, 5, 0, 42, 42, 48, 57, 65, 90, 95, 95,
    97, 122, 3, 0, 9, 10, 13, 13, 32, 32, 133, 0, 1, 1, 0, 0, 0, 0, 3, 1, 0, 0, 0, 0, 5, 1, 0, 0, 0,
    0, 7, 1, 0, 0, 0, 0, 9, 1, 0, 0, 0, 0, 11, 1, 0, 0, 0, 0, 13, 1, 0, 0, 0, 0, 15, 1, 0, 0, 0, 0,
    17, 1, 0, 0, 0, 0, 19, 1, 0, 0, 0, 0, 21, 1, 0, 0, 0, 0, 23, 1, 0, 0, 0, 0, 25, 1, 0, 0, 0, 0,
    27, 1, 0, 0, 0, 0, 29, 1, 0, 0, 0, 0, 31, 1, 0, 0, 0, 0, 33, 1, 0, 0, 0, 1, 41, 1, 0, 0, 0, 3,
    47, 1, 0, 0, 0, 5, 55, 1, 0, 0, 0, 7, 57, 1, 0, 0, 0, 9, 59, 1, 0, 0, 0, 11, 62, 1, 0, 0, 0, 13,
    66, 1, 0, 0, 0, 15, 68, 1, 0, 0, 0, 17, 70, 1, 0, 0, 0, 19, 72, 1, 0, 0, 0, 21, 77, 1, 0, 0, 0,
    23, 84, 1, 0, 0, 0, 25, 90, 1, 0, 0, 0, 27, 96, 1, 0, 0, 0, 29, 105, 1, 0, 0, 0, 31, 112, 1, 0,
    0, 0, 33, 120, 1, 0, 0, 0, 35, 36, 5, 97, 0, 0, 36, 37, 5, 110, 0, 0, 37, 42, 5, 100, 0, 0, 38,
    39, 5, 65, 0, 0, 39, 40, 5, 78, 0, 0, 40, 42, 5, 68, 0, 0, 41, 35, 1, 0, 0, 0, 41, 38, 1, 0, 0,
    0, 42, 2, 1, 0, 0, 0, 43, 44, 5, 111, 0, 0, 44, 48, 5, 114, 0, 0, 45, 46, 5, 79, 0, 0, 46, 48,
    5, 82, 0, 0, 47, 43, 1, 0, 0, 0, 47, 45, 1, 0, 0, 0, 48, 4, 1, 0, 0, 0, 49, 50, 5, 110, 0, 0,
    50, 51, 5, 111, 0, 0, 51, 56, 5, 116, 0, 0, 52, 53, 5, 78, 0, 0, 53, 54, 5, 79, 0, 0, 54, 56, 5,
    84, 0, 0, 55, 49, 1, 0, 0, 0, 55, 52, 1, 0, 0, 0, 56, 6, 1, 0, 0, 0, 57, 58, 5, 42, 0, 0, 58, 8,
    1, 0, 0, 0, 59, 60, 5, 43, 0, 0, 60, 10, 1, 0, 0, 0, 61, 63, 7, 0, 0, 0, 62, 61, 1, 0, 0, 0, 63,
    64, 1, 0, 0, 0, 64, 62, 1, 0, 0, 0, 64, 65, 1, 0, 0, 0, 65, 12, 1, 0, 0, 0, 66, 67, 5, 58, 0, 0,
    67, 14, 1, 0, 0, 0, 68, 69, 5, 40, 0, 0, 69, 16, 1, 0, 0, 0, 70, 71, 5, 41, 0, 0, 71, 18, 1, 0,
    0, 0, 72, 73, 5, 110, 0, 0, 73, 74, 5, 97, 0, 0, 74, 75, 5, 109, 0, 0, 75, 76, 5, 101, 0, 0, 76,
    20, 1, 0, 0, 0, 77, 78, 5, 115, 0, 0, 78, 79, 5, 116, 0, 0, 79, 80, 5, 97, 0, 0, 80, 81, 5, 116,
    0, 0, 81, 82, 5, 117, 0, 0, 82, 83, 5, 115, 0, 0, 83, 22, 1, 0, 0, 0, 84, 85, 5, 115, 0, 0, 85,
    86, 5, 105, 0, 0, 86, 87, 5, 110, 0, 0, 87, 88, 5, 107, 0, 0, 88, 89, 5, 115, 0, 0, 89, 24, 1,
    0, 0, 0, 90, 91, 5, 114, 0, 0, 91, 92, 5, 111, 0, 0, 92, 93, 5, 111, 0, 0, 93, 94, 5, 116, 0, 0,
    94, 95, 5, 115, 0, 0, 95, 26, 1, 0, 0, 0, 96, 100, 5, 34, 0, 0, 97, 99, 8, 1, 0, 0, 98, 97, 1,
    0, 0, 0, 99, 102, 1, 0, 0, 0, 100, 98, 1, 0, 0, 0, 100, 101, 1, 0, 0, 0, 101, 103, 1, 0, 0, 0,
    102, 100, 1, 0, 0, 0, 103, 104, 5, 34, 0, 0, 104, 28, 1, 0, 0, 0, 105, 109, 7, 2, 0, 0, 106,
    108, 7, 3, 0, 0, 107, 106, 1, 0, 0, 0, 108, 111, 1, 0, 0, 0, 109, 107, 1, 0, 0, 0, 109, 110, 1,
    0, 0, 0, 110, 30, 1, 0, 0, 0, 111, 109, 1, 0, 0, 0, 112, 116, 7, 4, 0, 0, 113, 115, 7, 5, 0, 0,
    114, 113, 1, 0, 0, 0, 115, 118, 1, 0, 0, 0, 116, 114, 1, 0, 0, 0, 116, 117, 1, 0, 0, 0, 117, 32,
    1, 0, 0, 0, 118, 116, 1, 0, 0, 0, 119, 121, 7, 6, 0, 0, 120, 119, 1, 0, 0, 0, 121, 122, 1, 0, 0,
    0, 122, 120, 1, 0, 0, 0, 122, 123, 1, 0, 0, 0, 123, 124, 1, 0, 0, 0, 124, 125, 6, 16, 0, 0, 125,
    34, 1, 0, 0, 0, 9, 0, 41, 47, 55, 64, 100, 109, 116, 122, 1, 6, 0, 0,
  ];

  private static __ATN: antlr.ATN;
  public static get _ATN(): antlr.ATN {
    if (!RunSelectionLexer.__ATN) {
      RunSelectionLexer.__ATN = new antlr.ATNDeserializer().deserialize(
        RunSelectionLexer._serializedATN,
      );
    }

    return RunSelectionLexer.__ATN;
  }

  private static readonly vocabulary = new antlr.Vocabulary(
    RunSelectionLexer.literalNames,
    RunSelectionLexer.symbolicNames,
    [],
  );

  public override get vocabulary(): antlr.Vocabulary {
    return RunSelectionLexer.vocabulary;
  }

  private static readonly decisionsToDFA = RunSelectionLexer._ATN.decisionToState.map(
    (ds: antlr.DecisionState, index: number) => new antlr.DFA(ds, index),
  );
}
