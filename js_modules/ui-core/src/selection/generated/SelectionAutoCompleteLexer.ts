// Generated from dagster-oss/js_modules/ui-core/src/selection/SelectionAutoComplete.g4 by ANTLR 4.13.1

import * as antlr from 'antlr4ng';
import {Token} from 'antlr4ng';

export class SelectionAutoCompleteLexer extends antlr.Lexer {
  public static readonly AND = 1;
  public static readonly OR = 2;
  public static readonly NOT = 3;
  public static readonly STAR = 4;
  public static readonly PLUS = 5;
  public static readonly DIGITS = 6;
  public static readonly COLON = 7;
  public static readonly LPAREN = 8;
  public static readonly RPAREN = 9;
  public static readonly QUOTED_STRING = 10;
  public static readonly INCOMPLETE_LEFT_QUOTED_STRING = 11;
  public static readonly INCOMPLETE_RIGHT_QUOTED_STRING = 12;
  public static readonly NULL_STRING = 13;
  public static readonly EQUAL = 14;
  public static readonly IDENTIFIER = 15;
  public static readonly UNQUOTED_REJECTED_STRING = 16;
  public static readonly WS = 17;
  public static readonly COMMA = 18;

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
    null,
    null,
    null,
    "'<null>'",
    "'='",
    null,
    null,
    null,
    "','",
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
    'QUOTED_STRING',
    'INCOMPLETE_LEFT_QUOTED_STRING',
    'INCOMPLETE_RIGHT_QUOTED_STRING',
    'NULL_STRING',
    'EQUAL',
    'IDENTIFIER',
    'UNQUOTED_REJECTED_STRING',
    'WS',
    'COMMA',
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
    'QUOTED_STRING',
    'INCOMPLETE_LEFT_QUOTED_STRING',
    'INCOMPLETE_RIGHT_QUOTED_STRING',
    'NULL_STRING',
    'EQUAL',
    'IDENTIFIER',
    'UNQUOTED_REJECTED_STRING',
    'WS',
    'COMMA',
  ];

  public constructor(input: antlr.CharStream) {
    super(input);
    this.interpreter = new antlr.LexerATNSimulator(
      this,
      SelectionAutoCompleteLexer._ATN,
      SelectionAutoCompleteLexer.decisionsToDFA,
      new antlr.PredictionContextCache(),
    );
  }

  public get grammarFileName(): string {
    return 'SelectionAutoComplete.g4';
  }

  public get literalNames(): (string | null)[] {
    return SelectionAutoCompleteLexer.literalNames;
  }
  public get symbolicNames(): (string | null)[] {
    return SelectionAutoCompleteLexer.symbolicNames;
  }
  public get ruleNames(): string[] {
    return SelectionAutoCompleteLexer.ruleNames;
  }

  public get serializedATN(): number[] {
    return SelectionAutoCompleteLexer._serializedATN;
  }

  public get channelNames(): string[] {
    return SelectionAutoCompleteLexer.channelNames;
  }

  public get modeNames(): string[] {
    return SelectionAutoCompleteLexer.modeNames;
  }

  public static readonly _serializedATN: number[] = [
    4, 0, 18, 126, 6, -1, 2, 0, 7, 0, 2, 1, 7, 1, 2, 2, 7, 2, 2, 3, 7, 3, 2, 4, 7, 4, 2, 5, 7, 5, 2,
    6, 7, 6, 2, 7, 7, 7, 2, 8, 7, 8, 2, 9, 7, 9, 2, 10, 7, 10, 2, 11, 7, 11, 2, 12, 7, 12, 2, 13, 7,
    13, 2, 14, 7, 14, 2, 15, 7, 15, 2, 16, 7, 16, 2, 17, 7, 17, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0,
    3, 0, 44, 8, 0, 1, 1, 1, 1, 1, 1, 1, 1, 3, 1, 50, 8, 1, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 3,
    2, 58, 8, 2, 1, 3, 1, 3, 1, 4, 1, 4, 1, 5, 4, 5, 65, 8, 5, 11, 5, 12, 5, 66, 1, 6, 1, 6, 1, 7,
    1, 7, 1, 8, 1, 8, 1, 9, 1, 9, 5, 9, 77, 8, 9, 10, 9, 12, 9, 80, 9, 9, 1, 9, 1, 9, 1, 10, 1, 10,
    5, 10, 86, 8, 10, 10, 10, 12, 10, 89, 9, 10, 1, 11, 5, 11, 92, 8, 11, 10, 11, 12, 11, 95, 9, 11,
    1, 11, 1, 11, 1, 12, 1, 12, 1, 12, 1, 12, 1, 12, 1, 12, 1, 12, 1, 13, 1, 13, 1, 14, 1, 14, 5,
    14, 110, 8, 14, 10, 14, 12, 14, 113, 9, 14, 1, 15, 4, 15, 116, 8, 15, 11, 15, 12, 15, 117, 1,
    16, 4, 16, 121, 8, 16, 11, 16, 12, 16, 122, 1, 17, 1, 17, 0, 0, 18, 1, 1, 3, 2, 5, 3, 7, 4, 9,
    5, 11, 6, 13, 7, 15, 8, 17, 9, 19, 10, 21, 11, 23, 12, 25, 13, 27, 14, 29, 15, 31, 16, 33, 17,
    35, 18, 1, 0, 7, 1, 0, 48, 57, 4, 0, 10, 10, 13, 13, 34, 34, 92, 92, 7, 0, 10, 10, 13, 13, 34,
    34, 40, 41, 58, 58, 61, 61, 92, 92, 5, 0, 42, 42, 48, 57, 65, 90, 95, 95, 97, 122, 5, 0, 42, 42,
    47, 57, 65, 90, 95, 95, 97, 122, 8, 0, 9, 10, 13, 13, 32, 32, 34, 34, 40, 41, 43, 44, 58, 58,
    61, 61, 3, 0, 9, 10, 13, 13, 32, 32, 135, 0, 1, 1, 0, 0, 0, 0, 3, 1, 0, 0, 0, 0, 5, 1, 0, 0, 0,
    0, 7, 1, 0, 0, 0, 0, 9, 1, 0, 0, 0, 0, 11, 1, 0, 0, 0, 0, 13, 1, 0, 0, 0, 0, 15, 1, 0, 0, 0, 0,
    17, 1, 0, 0, 0, 0, 19, 1, 0, 0, 0, 0, 21, 1, 0, 0, 0, 0, 23, 1, 0, 0, 0, 0, 25, 1, 0, 0, 0, 0,
    27, 1, 0, 0, 0, 0, 29, 1, 0, 0, 0, 0, 31, 1, 0, 0, 0, 0, 33, 1, 0, 0, 0, 0, 35, 1, 0, 0, 0, 1,
    43, 1, 0, 0, 0, 3, 49, 1, 0, 0, 0, 5, 57, 1, 0, 0, 0, 7, 59, 1, 0, 0, 0, 9, 61, 1, 0, 0, 0, 11,
    64, 1, 0, 0, 0, 13, 68, 1, 0, 0, 0, 15, 70, 1, 0, 0, 0, 17, 72, 1, 0, 0, 0, 19, 74, 1, 0, 0, 0,
    21, 83, 1, 0, 0, 0, 23, 93, 1, 0, 0, 0, 25, 98, 1, 0, 0, 0, 27, 105, 1, 0, 0, 0, 29, 107, 1, 0,
    0, 0, 31, 115, 1, 0, 0, 0, 33, 120, 1, 0, 0, 0, 35, 124, 1, 0, 0, 0, 37, 38, 5, 97, 0, 0, 38,
    39, 5, 110, 0, 0, 39, 44, 5, 100, 0, 0, 40, 41, 5, 65, 0, 0, 41, 42, 5, 78, 0, 0, 42, 44, 5, 68,
    0, 0, 43, 37, 1, 0, 0, 0, 43, 40, 1, 0, 0, 0, 44, 2, 1, 0, 0, 0, 45, 46, 5, 111, 0, 0, 46, 50,
    5, 114, 0, 0, 47, 48, 5, 79, 0, 0, 48, 50, 5, 82, 0, 0, 49, 45, 1, 0, 0, 0, 49, 47, 1, 0, 0, 0,
    50, 4, 1, 0, 0, 0, 51, 52, 5, 110, 0, 0, 52, 53, 5, 111, 0, 0, 53, 58, 5, 116, 0, 0, 54, 55, 5,
    78, 0, 0, 55, 56, 5, 79, 0, 0, 56, 58, 5, 84, 0, 0, 57, 51, 1, 0, 0, 0, 57, 54, 1, 0, 0, 0, 58,
    6, 1, 0, 0, 0, 59, 60, 5, 42, 0, 0, 60, 8, 1, 0, 0, 0, 61, 62, 5, 43, 0, 0, 62, 10, 1, 0, 0, 0,
    63, 65, 7, 0, 0, 0, 64, 63, 1, 0, 0, 0, 65, 66, 1, 0, 0, 0, 66, 64, 1, 0, 0, 0, 66, 67, 1, 0, 0,
    0, 67, 12, 1, 0, 0, 0, 68, 69, 5, 58, 0, 0, 69, 14, 1, 0, 0, 0, 70, 71, 5, 40, 0, 0, 71, 16, 1,
    0, 0, 0, 72, 73, 5, 41, 0, 0, 73, 18, 1, 0, 0, 0, 74, 78, 5, 34, 0, 0, 75, 77, 8, 1, 0, 0, 76,
    75, 1, 0, 0, 0, 77, 80, 1, 0, 0, 0, 78, 76, 1, 0, 0, 0, 78, 79, 1, 0, 0, 0, 79, 81, 1, 0, 0, 0,
    80, 78, 1, 0, 0, 0, 81, 82, 5, 34, 0, 0, 82, 20, 1, 0, 0, 0, 83, 87, 5, 34, 0, 0, 84, 86, 8, 2,
    0, 0, 85, 84, 1, 0, 0, 0, 86, 89, 1, 0, 0, 0, 87, 85, 1, 0, 0, 0, 87, 88, 1, 0, 0, 0, 88, 22, 1,
    0, 0, 0, 89, 87, 1, 0, 0, 0, 90, 92, 8, 2, 0, 0, 91, 90, 1, 0, 0, 0, 92, 95, 1, 0, 0, 0, 93, 91,
    1, 0, 0, 0, 93, 94, 1, 0, 0, 0, 94, 96, 1, 0, 0, 0, 95, 93, 1, 0, 0, 0, 96, 97, 5, 34, 0, 0, 97,
    24, 1, 0, 0, 0, 98, 99, 5, 60, 0, 0, 99, 100, 5, 110, 0, 0, 100, 101, 5, 117, 0, 0, 101, 102, 5,
    108, 0, 0, 102, 103, 5, 108, 0, 0, 103, 104, 5, 62, 0, 0, 104, 26, 1, 0, 0, 0, 105, 106, 5, 61,
    0, 0, 106, 28, 1, 0, 0, 0, 107, 111, 7, 3, 0, 0, 108, 110, 7, 4, 0, 0, 109, 108, 1, 0, 0, 0,
    110, 113, 1, 0, 0, 0, 111, 109, 1, 0, 0, 0, 111, 112, 1, 0, 0, 0, 112, 30, 1, 0, 0, 0, 113, 111,
    1, 0, 0, 0, 114, 116, 8, 5, 0, 0, 115, 114, 1, 0, 0, 0, 116, 117, 1, 0, 0, 0, 117, 115, 1, 0, 0,
    0, 117, 118, 1, 0, 0, 0, 118, 32, 1, 0, 0, 0, 119, 121, 7, 6, 0, 0, 120, 119, 1, 0, 0, 0, 121,
    122, 1, 0, 0, 0, 122, 120, 1, 0, 0, 0, 122, 123, 1, 0, 0, 0, 123, 34, 1, 0, 0, 0, 124, 125, 5,
    44, 0, 0, 125, 36, 1, 0, 0, 0, 11, 0, 43, 49, 57, 66, 78, 87, 93, 111, 117, 122, 0,
  ];

  private static __ATN: antlr.ATN;
  public static get _ATN(): antlr.ATN {
    if (!SelectionAutoCompleteLexer.__ATN) {
      SelectionAutoCompleteLexer.__ATN = new antlr.ATNDeserializer().deserialize(
        SelectionAutoCompleteLexer._serializedATN,
      );
    }

    return SelectionAutoCompleteLexer.__ATN;
  }

  private static readonly vocabulary = new antlr.Vocabulary(
    SelectionAutoCompleteLexer.literalNames,
    SelectionAutoCompleteLexer.symbolicNames,
    [],
  );

  public override get vocabulary(): antlr.Vocabulary {
    return SelectionAutoCompleteLexer.vocabulary;
  }

  private static readonly decisionsToDFA = SelectionAutoCompleteLexer._ATN.decisionToState.map(
    (ds: antlr.DecisionState, index: number) => new antlr.DFA(ds, index),
  );
}
