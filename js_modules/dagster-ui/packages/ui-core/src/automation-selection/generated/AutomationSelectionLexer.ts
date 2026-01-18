// Generated from /home/user/dagster/js_modules/dagster-ui/packages/ui-core/src/automation-selection/AutomationSelection.g4 by ANTLR 4.13.1

import * as antlr from 'antlr4ng';
import {Token} from 'antlr4ng';

export class AutomationSelectionLexer extends antlr.Lexer {
  public static readonly AND = 1;
  public static readonly OR = 2;
  public static readonly NOT = 3;
  public static readonly EQUAL = 4;
  public static readonly COLON = 5;
  public static readonly STAR = 6;
  public static readonly LPAREN = 7;
  public static readonly RPAREN = 8;
  public static readonly NAME = 9;
  public static readonly CODE_LOCATION = 10;
  public static readonly TAG = 11;
  public static readonly STATUS = 12;
  public static readonly TYPE = 13;
  public static readonly QUOTED_STRING = 14;
  public static readonly UNQUOTED_STRING = 15;
  public static readonly UNQUOTED_WILDCARD_STRING = 16;
  public static readonly NULL_STRING = 17;
  public static readonly WS = 18;

  public static readonly channelNames = ['DEFAULT_TOKEN_CHANNEL', 'HIDDEN'];

  public static readonly literalNames = [
    null,
    null,
    null,
    null,
    "'='",
    "':'",
    "'*'",
    "'('",
    "')'",
    "'name'",
    "'code_location'",
    "'tag'",
    "'status'",
    "'type'",
    null,
    null,
    null,
    "'<null>'",
  ];

  public static readonly symbolicNames = [
    null,
    'AND',
    'OR',
    'NOT',
    'EQUAL',
    'COLON',
    'STAR',
    'LPAREN',
    'RPAREN',
    'NAME',
    'CODE_LOCATION',
    'TAG',
    'STATUS',
    'TYPE',
    'QUOTED_STRING',
    'UNQUOTED_STRING',
    'UNQUOTED_WILDCARD_STRING',
    'NULL_STRING',
    'WS',
  ];

  public static readonly modeNames = ['DEFAULT_MODE'];

  public static readonly ruleNames = [
    'AND',
    'OR',
    'NOT',
    'EQUAL',
    'COLON',
    'STAR',
    'LPAREN',
    'RPAREN',
    'NAME',
    'CODE_LOCATION',
    'TAG',
    'STATUS',
    'TYPE',
    'QUOTED_STRING',
    'UNQUOTED_STRING',
    'UNQUOTED_WILDCARD_STRING',
    'NULL_STRING',
    'WS',
  ];

  public constructor(input: antlr.CharStream) {
    super(input);
    this.interpreter = new antlr.LexerATNSimulator(
      this,
      AutomationSelectionLexer._ATN,
      AutomationSelectionLexer.decisionsToDFA,
      new antlr.PredictionContextCache(),
    );
  }

  public get grammarFileName(): string {
    return 'AutomationSelection.g4';
  }

  public get literalNames(): (string | null)[] {
    return AutomationSelectionLexer.literalNames;
  }
  public get symbolicNames(): (string | null)[] {
    return AutomationSelectionLexer.symbolicNames;
  }
  public get ruleNames(): string[] {
    return AutomationSelectionLexer.ruleNames;
  }

  public get serializedATN(): number[] {
    return AutomationSelectionLexer._serializedATN;
  }

  public get channelNames(): string[] {
    return AutomationSelectionLexer.channelNames;
  }

  public get modeNames(): string[] {
    return AutomationSelectionLexer.modeNames;
  }

  public static readonly _serializedATN: number[] = [
    4, 0, 18, 141, 6, -1, 2, 0, 7, 0, 2, 1, 7, 1, 2, 2, 7, 2, 2, 3, 7, 3, 2, 4, 7, 4, 2, 5, 7, 5, 2,
    6, 7, 6, 2, 7, 7, 7, 2, 8, 7, 8, 2, 9, 7, 9, 2, 10, 7, 10, 2, 11, 7, 11, 2, 12, 7, 12, 2, 13, 7,
    13, 2, 14, 7, 14, 2, 15, 7, 15, 2, 16, 7, 16, 2, 17, 7, 17, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0,
    3, 0, 44, 8, 0, 1, 1, 1, 1, 1, 1, 1, 1, 3, 1, 50, 8, 1, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 3,
    2, 58, 8, 2, 1, 3, 1, 3, 1, 4, 1, 4, 1, 5, 1, 5, 1, 6, 1, 6, 1, 7, 1, 7, 1, 8, 1, 8, 1, 8, 1, 8,
    1, 8, 1, 9, 1, 9, 1, 9, 1, 9, 1, 9, 1, 9, 1, 9, 1, 9, 1, 9, 1, 9, 1, 9, 1, 9, 1, 9, 1, 9, 1, 10,
    1, 10, 1, 10, 1, 10, 1, 11, 1, 11, 1, 11, 1, 11, 1, 11, 1, 11, 1, 11, 1, 12, 1, 12, 1, 12, 1,
    12, 1, 12, 1, 13, 1, 13, 5, 13, 107, 8, 13, 10, 13, 12, 13, 110, 9, 13, 1, 13, 1, 13, 1, 14, 1,
    14, 5, 14, 116, 8, 14, 10, 14, 12, 14, 119, 9, 14, 1, 15, 1, 15, 5, 15, 123, 8, 15, 10, 15, 12,
    15, 126, 9, 15, 1, 16, 1, 16, 1, 16, 1, 16, 1, 16, 1, 16, 1, 16, 1, 17, 4, 17, 136, 8, 17, 11,
    17, 12, 17, 137, 1, 17, 1, 17, 0, 0, 18, 1, 1, 3, 2, 5, 3, 7, 4, 9, 5, 11, 6, 13, 7, 15, 8, 17,
    9, 19, 10, 21, 11, 23, 12, 25, 13, 27, 14, 29, 15, 31, 16, 33, 17, 35, 18, 1, 0, 6, 4, 0, 10,
    10, 13, 13, 34, 34, 92, 92, 3, 0, 65, 90, 95, 95, 97, 122, 4, 0, 48, 57, 64, 90, 95, 95, 97,
    122, 4, 0, 42, 42, 65, 90, 95, 95, 97, 122, 5, 0, 42, 42, 48, 57, 64, 90, 95, 95, 97, 122, 3, 0,
    9, 10, 13, 13, 32, 32, 147, 0, 1, 1, 0, 0, 0, 0, 3, 1, 0, 0, 0, 0, 5, 1, 0, 0, 0, 0, 7, 1, 0, 0,
    0, 0, 9, 1, 0, 0, 0, 0, 11, 1, 0, 0, 0, 0, 13, 1, 0, 0, 0, 0, 15, 1, 0, 0, 0, 0, 17, 1, 0, 0, 0,
    0, 19, 1, 0, 0, 0, 0, 21, 1, 0, 0, 0, 0, 23, 1, 0, 0, 0, 0, 25, 1, 0, 0, 0, 0, 27, 1, 0, 0, 0,
    0, 29, 1, 0, 0, 0, 0, 31, 1, 0, 0, 0, 0, 33, 1, 0, 0, 0, 0, 35, 1, 0, 0, 0, 1, 43, 1, 0, 0, 0,
    3, 49, 1, 0, 0, 0, 5, 57, 1, 0, 0, 0, 7, 59, 1, 0, 0, 0, 9, 61, 1, 0, 0, 0, 11, 63, 1, 0, 0, 0,
    13, 65, 1, 0, 0, 0, 15, 67, 1, 0, 0, 0, 17, 69, 1, 0, 0, 0, 19, 74, 1, 0, 0, 0, 21, 88, 1, 0, 0,
    0, 23, 92, 1, 0, 0, 0, 25, 99, 1, 0, 0, 0, 27, 104, 1, 0, 0, 0, 29, 113, 1, 0, 0, 0, 31, 120, 1,
    0, 0, 0, 33, 127, 1, 0, 0, 0, 35, 135, 1, 0, 0, 0, 37, 38, 5, 97, 0, 0, 38, 39, 5, 110, 0, 0,
    39, 44, 5, 100, 0, 0, 40, 41, 5, 65, 0, 0, 41, 42, 5, 78, 0, 0, 42, 44, 5, 68, 0, 0, 43, 37, 1,
    0, 0, 0, 43, 40, 1, 0, 0, 0, 44, 2, 1, 0, 0, 0, 45, 46, 5, 111, 0, 0, 46, 50, 5, 114, 0, 0, 47,
    48, 5, 79, 0, 0, 48, 50, 5, 82, 0, 0, 49, 45, 1, 0, 0, 0, 49, 47, 1, 0, 0, 0, 50, 4, 1, 0, 0, 0,
    51, 52, 5, 110, 0, 0, 52, 53, 5, 111, 0, 0, 53, 58, 5, 116, 0, 0, 54, 55, 5, 78, 0, 0, 55, 56,
    5, 79, 0, 0, 56, 58, 5, 84, 0, 0, 57, 51, 1, 0, 0, 0, 57, 54, 1, 0, 0, 0, 58, 6, 1, 0, 0, 0, 59,
    60, 5, 61, 0, 0, 60, 8, 1, 0, 0, 0, 61, 62, 5, 58, 0, 0, 62, 10, 1, 0, 0, 0, 63, 64, 5, 42, 0,
    0, 64, 12, 1, 0, 0, 0, 65, 66, 5, 40, 0, 0, 66, 14, 1, 0, 0, 0, 67, 68, 5, 41, 0, 0, 68, 16, 1,
    0, 0, 0, 69, 70, 5, 110, 0, 0, 70, 71, 5, 97, 0, 0, 71, 72, 5, 109, 0, 0, 72, 73, 5, 101, 0, 0,
    73, 18, 1, 0, 0, 0, 74, 75, 5, 99, 0, 0, 75, 76, 5, 111, 0, 0, 76, 77, 5, 100, 0, 0, 77, 78, 5,
    101, 0, 0, 78, 79, 5, 95, 0, 0, 79, 80, 5, 108, 0, 0, 80, 81, 5, 111, 0, 0, 81, 82, 5, 99, 0, 0,
    82, 83, 5, 97, 0, 0, 83, 84, 5, 116, 0, 0, 84, 85, 5, 105, 0, 0, 85, 86, 5, 111, 0, 0, 86, 87,
    5, 110, 0, 0, 87, 20, 1, 0, 0, 0, 88, 89, 5, 116, 0, 0, 89, 90, 5, 97, 0, 0, 90, 91, 5, 103, 0,
    0, 91, 22, 1, 0, 0, 0, 92, 93, 5, 115, 0, 0, 93, 94, 5, 116, 0, 0, 94, 95, 5, 97, 0, 0, 95, 96,
    5, 116, 0, 0, 96, 97, 5, 117, 0, 0, 97, 98, 5, 115, 0, 0, 98, 24, 1, 0, 0, 0, 99, 100, 5, 116,
    0, 0, 100, 101, 5, 121, 0, 0, 101, 102, 5, 112, 0, 0, 102, 103, 5, 101, 0, 0, 103, 26, 1, 0, 0,
    0, 104, 108, 5, 34, 0, 0, 105, 107, 8, 0, 0, 0, 106, 105, 1, 0, 0, 0, 107, 110, 1, 0, 0, 0, 108,
    106, 1, 0, 0, 0, 108, 109, 1, 0, 0, 0, 109, 111, 1, 0, 0, 0, 110, 108, 1, 0, 0, 0, 111, 112, 5,
    34, 0, 0, 112, 28, 1, 0, 0, 0, 113, 117, 7, 1, 0, 0, 114, 116, 7, 2, 0, 0, 115, 114, 1, 0, 0, 0,
    116, 119, 1, 0, 0, 0, 117, 115, 1, 0, 0, 0, 117, 118, 1, 0, 0, 0, 118, 30, 1, 0, 0, 0, 119, 117,
    1, 0, 0, 0, 120, 124, 7, 3, 0, 0, 121, 123, 7, 4, 0, 0, 122, 121, 1, 0, 0, 0, 123, 126, 1, 0, 0,
    0, 124, 122, 1, 0, 0, 0, 124, 125, 1, 0, 0, 0, 125, 32, 1, 0, 0, 0, 126, 124, 1, 0, 0, 0, 127,
    128, 5, 60, 0, 0, 128, 129, 5, 110, 0, 0, 129, 130, 5, 117, 0, 0, 130, 131, 5, 108, 0, 0, 131,
    132, 5, 108, 0, 0, 132, 133, 5, 62, 0, 0, 133, 34, 1, 0, 0, 0, 134, 136, 7, 5, 0, 0, 135, 134,
    1, 0, 0, 0, 136, 137, 1, 0, 0, 0, 137, 135, 1, 0, 0, 0, 137, 138, 1, 0, 0, 0, 138, 139, 1, 0, 0,
    0, 139, 140, 6, 17, 0, 0, 140, 36, 1, 0, 0, 0, 8, 0, 43, 49, 57, 108, 117, 124, 137, 1, 6, 0, 0,
  ];

  private static __ATN: antlr.ATN;
  public static get _ATN(): antlr.ATN {
    if (!AutomationSelectionLexer.__ATN) {
      AutomationSelectionLexer.__ATN = new antlr.ATNDeserializer().deserialize(
        AutomationSelectionLexer._serializedATN,
      );
    }

    return AutomationSelectionLexer.__ATN;
  }

  private static readonly vocabulary = new antlr.Vocabulary(
    AutomationSelectionLexer.literalNames,
    AutomationSelectionLexer.symbolicNames,
    [],
  );

  public override get vocabulary(): antlr.Vocabulary {
    return AutomationSelectionLexer.vocabulary;
  }

  private static readonly decisionsToDFA = AutomationSelectionLexer._ATN.decisionToState.map(
    (ds: antlr.DecisionState, index: number) => new antlr.DFA(ds, index),
  );
}
