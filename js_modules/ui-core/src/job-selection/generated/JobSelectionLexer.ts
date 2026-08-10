// Generated from /home/lucas/Documents/dagster/js_modules/ui-core/src/job-selection/JobSelection.g4 by ANTLR 4.13.1

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
  public static readonly GROUP = 9;
  public static readonly CODE_LOCATION = 10;
  public static readonly QUOTED_STRING = 11;
  public static readonly UNQUOTED_STRING = 12;
  public static readonly UNQUOTED_WILDCARD_STRING = 13;
  public static readonly WS = 14;

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
    "'group'",
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
    'GROUP',
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
    'GROUP',
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
    4, 0, 14, 114, 6, -1, 2, 0, 7, 0, 2, 1, 7, 1, 2, 2, 7, 2, 2, 3, 7, 3, 2, 4, 7, 4, 2, 5, 7, 5, 2,
    6, 7, 6, 2, 7, 7, 7, 2, 8, 7, 8, 2, 9, 7, 9, 2, 10, 7, 10, 2, 11, 7, 11, 2, 12, 7, 12, 2, 13, 7,
    13, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 3, 0, 36, 8, 0, 1, 1, 1, 1, 1, 1, 1, 1, 3, 1, 42, 8, 1,
    1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 3, 2, 50, 8, 2, 1, 3, 1, 3, 1, 4, 1, 4, 1, 5, 1, 5, 1, 6, 1,
    6, 1, 7, 1, 7, 1, 7, 1, 7, 1, 7, 1, 8, 1, 8, 1, 8, 1, 8, 1, 8, 1, 8, 1, 9, 1, 9, 1, 9, 1, 9, 1,
    9, 1, 9, 1, 9, 1, 9, 1, 9, 1, 9, 1, 9, 1, 9, 1, 9, 1, 9, 1, 10, 1, 10, 5, 10, 87, 8, 10, 10, 10,
    12, 10, 90, 9, 10, 1, 10, 1, 10, 1, 11, 1, 11, 5, 11, 96, 8, 11, 10, 11, 12, 11, 99, 9, 11, 1,
    12, 1, 12, 5, 12, 103, 8, 12, 10, 12, 12, 12, 106, 9, 12, 1, 13, 4, 13, 109, 8, 13, 11, 13, 12,
    13, 110, 1, 13, 1, 13, 0, 0, 14, 1, 1, 3, 2, 5, 3, 7, 4, 9, 5, 11, 6, 13, 7, 15, 8, 17, 9, 19,
    10, 21, 11, 23, 12, 25, 13, 27, 14, 1, 0, 6, 4, 0, 10, 10, 13, 13, 34, 34, 92, 92, 3, 0, 65, 90,
    95, 95, 97, 122, 4, 0, 48, 57, 64, 90, 95, 95, 97, 122, 4, 0, 42, 42, 65, 90, 95, 95, 97, 122,
    5, 0, 42, 42, 48, 57, 64, 90, 95, 95, 97, 122, 3, 0, 9, 10, 13, 13, 32, 32, 120, 0, 1, 1, 0, 0,
    0, 0, 3, 1, 0, 0, 0, 0, 5, 1, 0, 0, 0, 0, 7, 1, 0, 0, 0, 0, 9, 1, 0, 0, 0, 0, 11, 1, 0, 0, 0, 0,
    13, 1, 0, 0, 0, 0, 15, 1, 0, 0, 0, 0, 17, 1, 0, 0, 0, 0, 19, 1, 0, 0, 0, 0, 21, 1, 0, 0, 0, 0,
    23, 1, 0, 0, 0, 0, 25, 1, 0, 0, 0, 0, 27, 1, 0, 0, 0, 1, 35, 1, 0, 0, 0, 3, 41, 1, 0, 0, 0, 5,
    49, 1, 0, 0, 0, 7, 51, 1, 0, 0, 0, 9, 53, 1, 0, 0, 0, 11, 55, 1, 0, 0, 0, 13, 57, 1, 0, 0, 0,
    15, 59, 1, 0, 0, 0, 17, 64, 1, 0, 0, 0, 19, 70, 1, 0, 0, 0, 21, 84, 1, 0, 0, 0, 23, 93, 1, 0, 0,
    0, 25, 100, 1, 0, 0, 0, 27, 108, 1, 0, 0, 0, 29, 30, 5, 97, 0, 0, 30, 31, 5, 110, 0, 0, 31, 36,
    5, 100, 0, 0, 32, 33, 5, 65, 0, 0, 33, 34, 5, 78, 0, 0, 34, 36, 5, 68, 0, 0, 35, 29, 1, 0, 0, 0,
    35, 32, 1, 0, 0, 0, 36, 2, 1, 0, 0, 0, 37, 38, 5, 111, 0, 0, 38, 42, 5, 114, 0, 0, 39, 40, 5,
    79, 0, 0, 40, 42, 5, 82, 0, 0, 41, 37, 1, 0, 0, 0, 41, 39, 1, 0, 0, 0, 42, 4, 1, 0, 0, 0, 43,
    44, 5, 110, 0, 0, 44, 45, 5, 111, 0, 0, 45, 50, 5, 116, 0, 0, 46, 47, 5, 78, 0, 0, 47, 48, 5,
    79, 0, 0, 48, 50, 5, 84, 0, 0, 49, 43, 1, 0, 0, 0, 49, 46, 1, 0, 0, 0, 50, 6, 1, 0, 0, 0, 51,
    52, 5, 58, 0, 0, 52, 8, 1, 0, 0, 0, 53, 54, 5, 42, 0, 0, 54, 10, 1, 0, 0, 0, 55, 56, 5, 40, 0,
    0, 56, 12, 1, 0, 0, 0, 57, 58, 5, 41, 0, 0, 58, 14, 1, 0, 0, 0, 59, 60, 5, 110, 0, 0, 60, 61, 5,
    97, 0, 0, 61, 62, 5, 109, 0, 0, 62, 63, 5, 101, 0, 0, 63, 16, 1, 0, 0, 0, 64, 65, 5, 103, 0, 0,
    65, 66, 5, 114, 0, 0, 66, 67, 5, 111, 0, 0, 67, 68, 5, 117, 0, 0, 68, 69, 5, 112, 0, 0, 69, 18,
    1, 0, 0, 0, 70, 71, 5, 99, 0, 0, 71, 72, 5, 111, 0, 0, 72, 73, 5, 100, 0, 0, 73, 74, 5, 101, 0,
    0, 74, 75, 5, 95, 0, 0, 75, 76, 5, 108, 0, 0, 76, 77, 5, 111, 0, 0, 77, 78, 5, 99, 0, 0, 78, 79,
    5, 97, 0, 0, 79, 80, 5, 116, 0, 0, 80, 81, 5, 105, 0, 0, 81, 82, 5, 111, 0, 0, 82, 83, 5, 110,
    0, 0, 83, 20, 1, 0, 0, 0, 84, 88, 5, 34, 0, 0, 85, 87, 8, 0, 0, 0, 86, 85, 1, 0, 0, 0, 87, 90,
    1, 0, 0, 0, 88, 86, 1, 0, 0, 0, 88, 89, 1, 0, 0, 0, 89, 91, 1, 0, 0, 0, 90, 88, 1, 0, 0, 0, 91,
    92, 5, 34, 0, 0, 92, 22, 1, 0, 0, 0, 93, 97, 7, 1, 0, 0, 94, 96, 7, 2, 0, 0, 95, 94, 1, 0, 0, 0,
    96, 99, 1, 0, 0, 0, 97, 95, 1, 0, 0, 0, 97, 98, 1, 0, 0, 0, 98, 24, 1, 0, 0, 0, 99, 97, 1, 0, 0,
    0, 100, 104, 7, 3, 0, 0, 101, 103, 7, 4, 0, 0, 102, 101, 1, 0, 0, 0, 103, 106, 1, 0, 0, 0, 104,
    102, 1, 0, 0, 0, 104, 105, 1, 0, 0, 0, 105, 26, 1, 0, 0, 0, 106, 104, 1, 0, 0, 0, 107, 109, 7,
    5, 0, 0, 108, 107, 1, 0, 0, 0, 109, 110, 1, 0, 0, 0, 110, 108, 1, 0, 0, 0, 110, 111, 1, 0, 0, 0,
    111, 112, 1, 0, 0, 0, 112, 113, 6, 13, 0, 0, 113, 28, 1, 0, 0, 0, 8, 0, 35, 41, 49, 88, 97, 104,
    110, 1, 6, 0, 0,
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
