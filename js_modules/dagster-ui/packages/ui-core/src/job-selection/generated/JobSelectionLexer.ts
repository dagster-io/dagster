// Generated from /home/user/dagster/js_modules/dagster-ui/packages/ui-core/src/job-selection/JobSelection.g4 by ANTLR 4.13.1

import * as antlr from 'antlr4ng';
import {Token} from 'antlr4ng';

export class JobSelectionLexer extends antlr.Lexer {
  public static readonly AND = 1;
  public static readonly OR = 2;
  public static readonly NOT = 3;
  public static readonly COLON = 4;
  public static readonly STAR = 5;
  public static readonly LPAREN = 6;
  public static readonly RPAREN = 7;
  public static readonly NAME = 8;
  public static readonly CODE_LOCATION = 9;
  public static readonly QUOTED_STRING = 10;
  public static readonly UNQUOTED_STRING = 11;
  public static readonly UNQUOTED_WILDCARD_STRING = 12;
  public static readonly WS = 13;

  public static readonly channelNames = ['DEFAULT_TOKEN_CHANNEL', 'HIDDEN'];

  public static readonly literalNames = [
    null,
    null,
    null,
    null,
    "':'",
    "'*'",
    "'('",
    "')'",
    "'name'",
    "'code_location'",
  ];

  public static readonly symbolicNames = [
    null,
    'AND',
    'OR',
    'NOT',
    'COLON',
    'STAR',
    'LPAREN',
    'RPAREN',
    'NAME',
    'CODE_LOCATION',
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
    'COLON',
    'STAR',
    'LPAREN',
    'RPAREN',
    'NAME',
    'CODE_LOCATION',
    'QUOTED_STRING',
    'UNQUOTED_STRING',
    'UNQUOTED_WILDCARD_STRING',
    'WS',
  ];

  public constructor(input: antlr.CharStream) {
    super(input);
    this.interpreter = new antlr.LexerATNSimulator(
      this,
      JobSelectionLexer._ATN,
      JobSelectionLexer.decisionsToDFA,
      new antlr.PredictionContextCache(),
    );
  }

  public get grammarFileName(): string {
    return 'JobSelection.g4';
  }

  public get literalNames(): (string | null)[] {
    return JobSelectionLexer.literalNames;
  }
  public get symbolicNames(): (string | null)[] {
    return JobSelectionLexer.symbolicNames;
  }
  public get ruleNames(): string[] {
    return JobSelectionLexer.ruleNames;
  }

  public get serializedATN(): number[] {
    return JobSelectionLexer._serializedATN;
  }

  public get channelNames(): string[] {
    return JobSelectionLexer.channelNames;
  }

  public get modeNames(): string[] {
    return JobSelectionLexer.modeNames;
  }

  public static readonly _serializedATN: number[] = [
    4, 0, 13, 106, 6, -1, 2, 0, 7, 0, 2, 1, 7, 1, 2, 2, 7, 2, 2, 3, 7, 3, 2, 4, 7, 4, 2, 5, 7, 5, 2,
    6, 7, 6, 2, 7, 7, 7, 2, 8, 7, 8, 2, 9, 7, 9, 2, 10, 7, 10, 2, 11, 7, 11, 2, 12, 7, 12, 1, 0, 1,
    0, 1, 0, 1, 0, 1, 0, 1, 0, 3, 0, 34, 8, 0, 1, 1, 1, 1, 1, 1, 1, 1, 3, 1, 40, 8, 1, 1, 2, 1, 2,
    1, 2, 1, 2, 1, 2, 1, 2, 3, 2, 48, 8, 2, 1, 3, 1, 3, 1, 4, 1, 4, 1, 5, 1, 5, 1, 6, 1, 6, 1, 7, 1,
    7, 1, 7, 1, 7, 1, 7, 1, 8, 1, 8, 1, 8, 1, 8, 1, 8, 1, 8, 1, 8, 1, 8, 1, 8, 1, 8, 1, 8, 1, 8, 1,
    8, 1, 8, 1, 9, 1, 9, 5, 9, 79, 8, 9, 10, 9, 12, 9, 82, 9, 9, 1, 9, 1, 9, 1, 10, 1, 10, 5, 10,
    88, 8, 10, 10, 10, 12, 10, 91, 9, 10, 1, 11, 1, 11, 5, 11, 95, 8, 11, 10, 11, 12, 11, 98, 9, 11,
    1, 12, 4, 12, 101, 8, 12, 11, 12, 12, 12, 102, 1, 12, 1, 12, 0, 0, 13, 1, 1, 3, 2, 5, 3, 7, 4,
    9, 5, 11, 6, 13, 7, 15, 8, 17, 9, 19, 10, 21, 11, 23, 12, 25, 13, 1, 0, 6, 4, 0, 10, 10, 13, 13,
    34, 34, 92, 92, 3, 0, 65, 90, 95, 95, 97, 122, 4, 0, 48, 57, 64, 90, 95, 95, 97, 122, 4, 0, 42,
    42, 65, 90, 95, 95, 97, 122, 5, 0, 42, 42, 48, 57, 64, 90, 95, 95, 97, 122, 3, 0, 9, 10, 13, 13,
    32, 32, 112, 0, 1, 1, 0, 0, 0, 0, 3, 1, 0, 0, 0, 0, 5, 1, 0, 0, 0, 0, 7, 1, 0, 0, 0, 0, 9, 1, 0,
    0, 0, 0, 11, 1, 0, 0, 0, 0, 13, 1, 0, 0, 0, 0, 15, 1, 0, 0, 0, 0, 17, 1, 0, 0, 0, 0, 19, 1, 0,
    0, 0, 0, 21, 1, 0, 0, 0, 0, 23, 1, 0, 0, 0, 0, 25, 1, 0, 0, 0, 1, 33, 1, 0, 0, 0, 3, 39, 1, 0,
    0, 0, 5, 47, 1, 0, 0, 0, 7, 49, 1, 0, 0, 0, 9, 51, 1, 0, 0, 0, 11, 53, 1, 0, 0, 0, 13, 55, 1, 0,
    0, 0, 15, 57, 1, 0, 0, 0, 17, 62, 1, 0, 0, 0, 19, 76, 1, 0, 0, 0, 21, 85, 1, 0, 0, 0, 23, 92, 1,
    0, 0, 0, 25, 100, 1, 0, 0, 0, 27, 28, 5, 97, 0, 0, 28, 29, 5, 110, 0, 0, 29, 34, 5, 100, 0, 0,
    30, 31, 5, 65, 0, 0, 31, 32, 5, 78, 0, 0, 32, 34, 5, 68, 0, 0, 33, 27, 1, 0, 0, 0, 33, 30, 1, 0,
    0, 0, 34, 2, 1, 0, 0, 0, 35, 36, 5, 111, 0, 0, 36, 40, 5, 114, 0, 0, 37, 38, 5, 79, 0, 0, 38,
    40, 5, 82, 0, 0, 39, 35, 1, 0, 0, 0, 39, 37, 1, 0, 0, 0, 40, 4, 1, 0, 0, 0, 41, 42, 5, 110, 0,
    0, 42, 43, 5, 111, 0, 0, 43, 48, 5, 116, 0, 0, 44, 45, 5, 78, 0, 0, 45, 46, 5, 79, 0, 0, 46, 48,
    5, 84, 0, 0, 47, 41, 1, 0, 0, 0, 47, 44, 1, 0, 0, 0, 48, 6, 1, 0, 0, 0, 49, 50, 5, 58, 0, 0, 50,
    8, 1, 0, 0, 0, 51, 52, 5, 42, 0, 0, 52, 10, 1, 0, 0, 0, 53, 54, 5, 40, 0, 0, 54, 12, 1, 0, 0, 0,
    55, 56, 5, 41, 0, 0, 56, 14, 1, 0, 0, 0, 57, 58, 5, 110, 0, 0, 58, 59, 5, 97, 0, 0, 59, 60, 5,
    109, 0, 0, 60, 61, 5, 101, 0, 0, 61, 16, 1, 0, 0, 0, 62, 63, 5, 99, 0, 0, 63, 64, 5, 111, 0, 0,
    64, 65, 5, 100, 0, 0, 65, 66, 5, 101, 0, 0, 66, 67, 5, 95, 0, 0, 67, 68, 5, 108, 0, 0, 68, 69,
    5, 111, 0, 0, 69, 70, 5, 99, 0, 0, 70, 71, 5, 97, 0, 0, 71, 72, 5, 116, 0, 0, 72, 73, 5, 105, 0,
    0, 73, 74, 5, 111, 0, 0, 74, 75, 5, 110, 0, 0, 75, 18, 1, 0, 0, 0, 76, 80, 5, 34, 0, 0, 77, 79,
    8, 0, 0, 0, 78, 77, 1, 0, 0, 0, 79, 82, 1, 0, 0, 0, 80, 78, 1, 0, 0, 0, 80, 81, 1, 0, 0, 0, 81,
    83, 1, 0, 0, 0, 82, 80, 1, 0, 0, 0, 83, 84, 5, 34, 0, 0, 84, 20, 1, 0, 0, 0, 85, 89, 7, 1, 0, 0,
    86, 88, 7, 2, 0, 0, 87, 86, 1, 0, 0, 0, 88, 91, 1, 0, 0, 0, 89, 87, 1, 0, 0, 0, 89, 90, 1, 0, 0,
    0, 90, 22, 1, 0, 0, 0, 91, 89, 1, 0, 0, 0, 92, 96, 7, 3, 0, 0, 93, 95, 7, 4, 0, 0, 94, 93, 1, 0,
    0, 0, 95, 98, 1, 0, 0, 0, 96, 94, 1, 0, 0, 0, 96, 97, 1, 0, 0, 0, 97, 24, 1, 0, 0, 0, 98, 96, 1,
    0, 0, 0, 99, 101, 7, 5, 0, 0, 100, 99, 1, 0, 0, 0, 101, 102, 1, 0, 0, 0, 102, 100, 1, 0, 0, 0,
    102, 103, 1, 0, 0, 0, 103, 104, 1, 0, 0, 0, 104, 105, 6, 12, 0, 0, 105, 26, 1, 0, 0, 0, 8, 0,
    33, 39, 47, 80, 89, 96, 102, 1, 6, 0, 0,
  ];

  private static __ATN: antlr.ATN;
  public static get _ATN(): antlr.ATN {
    if (!JobSelectionLexer.__ATN) {
      JobSelectionLexer.__ATN = new antlr.ATNDeserializer().deserialize(
        JobSelectionLexer._serializedATN,
      );
    }

    return JobSelectionLexer.__ATN;
  }

  private static readonly vocabulary = new antlr.Vocabulary(
    JobSelectionLexer.literalNames,
    JobSelectionLexer.symbolicNames,
    [],
  );

  public override get vocabulary(): antlr.Vocabulary {
    return JobSelectionLexer.vocabulary;
  }

  private static readonly decisionsToDFA = JobSelectionLexer._ATN.decisionToState.map(
    (ds: antlr.DecisionState, index: number) => new antlr.DFA(ds, index),
  );
}
