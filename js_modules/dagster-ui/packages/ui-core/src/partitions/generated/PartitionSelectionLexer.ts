// Generated from /home/user/dagster/js_modules/dagster-ui/packages/ui-core/src/partitions/PartitionSelection.g4 by ANTLR 4.13.1

import * as antlr from 'antlr4ng';
import {Token} from 'antlr4ng';

export class PartitionSelectionLexer extends antlr.Lexer {
  public static readonly LBRACKET = 1;
  public static readonly RBRACKET = 2;
  public static readonly RANGE_DELIM = 3;
  public static readonly COMMA = 4;
  public static readonly QUOTED_STRING = 5;
  public static readonly WILDCARD_PATTERN = 6;
  public static readonly UNQUOTED_STRING = 7;
  public static readonly WS = 8;

  public static readonly channelNames = ['DEFAULT_TOKEN_CHANNEL', 'HIDDEN'];

  public static readonly literalNames = [null, "'['", "']'", "'...'", "','"];

  public static readonly symbolicNames = [
    null,
    'LBRACKET',
    'RBRACKET',
    'RANGE_DELIM',
    'COMMA',
    'QUOTED_STRING',
    'WILDCARD_PATTERN',
    'UNQUOTED_STRING',
    'WS',
  ];

  public static readonly modeNames = ['DEFAULT_MODE'];

  public static readonly ruleNames = [
    'LBRACKET',
    'RBRACKET',
    'RANGE_DELIM',
    'COMMA',
    'QUOTED_STRING',
    'ESCAPE_SEQ',
    'WILDCARD_PATTERN',
    'UNQUOTED_STRING',
    'UNQUOTED_CHAR',
    'WS',
  ];

  public constructor(input: antlr.CharStream) {
    super(input);
    this.interpreter = new antlr.LexerATNSimulator(
      this,
      PartitionSelectionLexer._ATN,
      PartitionSelectionLexer.decisionsToDFA,
      new antlr.PredictionContextCache(),
    );
  }

  public get grammarFileName(): string {
    return 'PartitionSelection.g4';
  }

  public get literalNames(): (string | null)[] {
    return PartitionSelectionLexer.literalNames;
  }
  public get symbolicNames(): (string | null)[] {
    return PartitionSelectionLexer.symbolicNames;
  }
  public get ruleNames(): string[] {
    return PartitionSelectionLexer.ruleNames;
  }

  public get serializedATN(): number[] {
    return PartitionSelectionLexer._serializedATN;
  }

  public get channelNames(): string[] {
    return PartitionSelectionLexer.channelNames;
  }

  public get modeNames(): string[] {
    return PartitionSelectionLexer.modeNames;
  }

  public static readonly _serializedATN: number[] = [
    4, 0, 8, 71, 6, -1, 2, 0, 7, 0, 2, 1, 7, 1, 2, 2, 7, 2, 2, 3, 7, 3, 2, 4, 7, 4, 2, 5, 7, 5, 2,
    6, 7, 6, 2, 7, 7, 7, 2, 8, 7, 8, 2, 9, 7, 9, 1, 0, 1, 0, 1, 1, 1, 1, 1, 2, 1, 2, 1, 2, 1, 2, 1,
    3, 1, 3, 1, 4, 1, 4, 1, 4, 5, 4, 35, 8, 4, 10, 4, 12, 4, 38, 9, 4, 1, 4, 1, 4, 1, 5, 1, 5, 1, 5,
    1, 6, 5, 6, 46, 8, 6, 10, 6, 12, 6, 49, 9, 6, 1, 6, 1, 6, 5, 6, 53, 8, 6, 10, 6, 12, 6, 56, 9,
    6, 1, 7, 4, 7, 59, 8, 7, 11, 7, 12, 7, 60, 1, 8, 1, 8, 1, 9, 4, 9, 66, 8, 9, 11, 9, 12, 9, 67,
    1, 9, 1, 9, 0, 0, 10, 1, 1, 3, 2, 5, 3, 7, 4, 9, 5, 11, 0, 13, 6, 15, 7, 17, 0, 19, 8, 1, 0, 4,
    4, 0, 10, 10, 13, 13, 34, 34, 92, 92, 3, 0, 34, 34, 47, 47, 92, 92, 5, 0, 45, 45, 47, 58, 64,
    90, 95, 95, 97, 122, 3, 0, 9, 10, 13, 13, 32, 32, 74, 0, 1, 1, 0, 0, 0, 0, 3, 1, 0, 0, 0, 0, 5,
    1, 0, 0, 0, 0, 7, 1, 0, 0, 0, 0, 9, 1, 0, 0, 0, 0, 13, 1, 0, 0, 0, 0, 15, 1, 0, 0, 0, 0, 19, 1,
    0, 0, 0, 1, 21, 1, 0, 0, 0, 3, 23, 1, 0, 0, 0, 5, 25, 1, 0, 0, 0, 7, 29, 1, 0, 0, 0, 9, 31, 1,
    0, 0, 0, 11, 41, 1, 0, 0, 0, 13, 47, 1, 0, 0, 0, 15, 58, 1, 0, 0, 0, 17, 62, 1, 0, 0, 0, 19, 65,
    1, 0, 0, 0, 21, 22, 5, 91, 0, 0, 22, 2, 1, 0, 0, 0, 23, 24, 5, 93, 0, 0, 24, 4, 1, 0, 0, 0, 25,
    26, 5, 46, 0, 0, 26, 27, 5, 46, 0, 0, 27, 28, 5, 46, 0, 0, 28, 6, 1, 0, 0, 0, 29, 30, 5, 44, 0,
    0, 30, 8, 1, 0, 0, 0, 31, 36, 5, 34, 0, 0, 32, 35, 3, 11, 5, 0, 33, 35, 8, 0, 0, 0, 34, 32, 1,
    0, 0, 0, 34, 33, 1, 0, 0, 0, 35, 38, 1, 0, 0, 0, 36, 34, 1, 0, 0, 0, 36, 37, 1, 0, 0, 0, 37, 39,
    1, 0, 0, 0, 38, 36, 1, 0, 0, 0, 39, 40, 5, 34, 0, 0, 40, 10, 1, 0, 0, 0, 41, 42, 5, 92, 0, 0,
    42, 43, 7, 1, 0, 0, 43, 12, 1, 0, 0, 0, 44, 46, 3, 17, 8, 0, 45, 44, 1, 0, 0, 0, 46, 49, 1, 0,
    0, 0, 47, 45, 1, 0, 0, 0, 47, 48, 1, 0, 0, 0, 48, 50, 1, 0, 0, 0, 49, 47, 1, 0, 0, 0, 50, 54, 5,
    42, 0, 0, 51, 53, 3, 17, 8, 0, 52, 51, 1, 0, 0, 0, 53, 56, 1, 0, 0, 0, 54, 52, 1, 0, 0, 0, 54,
    55, 1, 0, 0, 0, 55, 14, 1, 0, 0, 0, 56, 54, 1, 0, 0, 0, 57, 59, 3, 17, 8, 0, 58, 57, 1, 0, 0, 0,
    59, 60, 1, 0, 0, 0, 60, 58, 1, 0, 0, 0, 60, 61, 1, 0, 0, 0, 61, 16, 1, 0, 0, 0, 62, 63, 7, 2, 0,
    0, 63, 18, 1, 0, 0, 0, 64, 66, 7, 3, 0, 0, 65, 64, 1, 0, 0, 0, 66, 67, 1, 0, 0, 0, 67, 65, 1, 0,
    0, 0, 67, 68, 1, 0, 0, 0, 68, 69, 1, 0, 0, 0, 69, 70, 6, 9, 0, 0, 70, 20, 1, 0, 0, 0, 7, 0, 34,
    36, 47, 54, 60, 67, 1, 6, 0, 0,
  ];

  private static __ATN: antlr.ATN;
  public static get _ATN(): antlr.ATN {
    if (!PartitionSelectionLexer.__ATN) {
      PartitionSelectionLexer.__ATN = new antlr.ATNDeserializer().deserialize(
        PartitionSelectionLexer._serializedATN,
      );
    }

    return PartitionSelectionLexer.__ATN;
  }

  private static readonly vocabulary = new antlr.Vocabulary(
    PartitionSelectionLexer.literalNames,
    PartitionSelectionLexer.symbolicNames,
    [],
  );

  public override get vocabulary(): antlr.Vocabulary {
    return PartitionSelectionLexer.vocabulary;
  }

  private static readonly decisionsToDFA = PartitionSelectionLexer._ATN.decisionToState.map(
    (ds: antlr.DecisionState, index: number) => new antlr.DFA(ds, index),
  );
}
