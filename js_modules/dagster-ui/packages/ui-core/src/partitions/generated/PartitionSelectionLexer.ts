// Generated from /home/user/dagster/js_modules/dagster-ui/packages/ui-core/src/partitions/PartitionSelection.g4 by ANTLR 4.9.0-SNAPSHOT

import {CharStream} from 'antlr4ts/CharStream';
import {Lexer} from 'antlr4ts/Lexer';
import {Vocabulary} from 'antlr4ts/Vocabulary';
import {VocabularyImpl} from 'antlr4ts/VocabularyImpl';
import {ATN} from 'antlr4ts/atn/ATN';
import {ATNDeserializer} from 'antlr4ts/atn/ATNDeserializer';
import {LexerATNSimulator} from 'antlr4ts/atn/LexerATNSimulator';
import * as Utils from 'antlr4ts/misc/Utils';

export class PartitionSelectionLexer extends Lexer {
  public static readonly LBRACKET = 1;
  public static readonly RBRACKET = 2;
  public static readonly RANGE_DELIM = 3;
  public static readonly COMMA = 4;
  public static readonly QUOTED_STRING = 5;
  public static readonly WILDCARD_PATTERN = 6;
  public static readonly UNQUOTED_STRING = 7;
  public static readonly WS = 8;

  // tslint:disable:no-trailing-whitespace
  public static readonly channelNames: string[] = ['DEFAULT_TOKEN_CHANNEL', 'HIDDEN'];

  // tslint:disable:no-trailing-whitespace
  public static readonly modeNames: string[] = ['DEFAULT_MODE'];

  public static readonly ruleNames: string[] = [
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

  private static readonly _LITERAL_NAMES: Array<string | undefined> = [
    undefined,
    "'['",
    "']'",
    "'...'",
    "','",
  ];
  private static readonly _SYMBOLIC_NAMES: Array<string | undefined> = [
    undefined,
    'LBRACKET',
    'RBRACKET',
    'RANGE_DELIM',
    'COMMA',
    'QUOTED_STRING',
    'WILDCARD_PATTERN',
    'UNQUOTED_STRING',
    'WS',
  ];
  public static readonly VOCABULARY: Vocabulary = new VocabularyImpl(
    PartitionSelectionLexer._LITERAL_NAMES,
    PartitionSelectionLexer._SYMBOLIC_NAMES,
    [],
  );

  // @Override
  // @NotNull
  public get vocabulary(): Vocabulary {
    return PartitionSelectionLexer.VOCABULARY;
  }
  // tslint:enable:no-trailing-whitespace

  constructor(input: CharStream) {
    super(input);
    this._interp = new LexerATNSimulator(PartitionSelectionLexer._ATN, this);
  }

  // @Override
  public get grammarFileName(): string {
    return 'PartitionSelection.g4';
  }

  // @Override
  public get ruleNames(): string[] {
    return PartitionSelectionLexer.ruleNames;
  }

  // @Override
  public get serializedATN(): string {
    return PartitionSelectionLexer._serializedATN;
  }

  // @Override
  public get channelNames(): string[] {
    return PartitionSelectionLexer.channelNames;
  }

  // @Override
  public get modeNames(): string[] {
    return PartitionSelectionLexer.modeNames;
  }

  public static readonly _serializedATN: string =
    '\x03\uC91D\uCABA\u058D\uAFBA\u4F53\u0607\uEA8B\uC241\x02\nI\b\x01\x04' +
    '\x02\t\x02\x04\x03\t\x03\x04\x04\t\x04\x04\x05\t\x05\x04\x06\t\x06\x04' +
    '\x07\t\x07\x04\b\t\b\x04\t\t\t\x04\n\t\n\x04\v\t\v\x03\x02\x03\x02\x03' +
    '\x03\x03\x03\x03\x04\x03\x04\x03\x04\x03\x04\x03\x05\x03\x05\x03\x06\x03' +
    '\x06\x03\x06\x07\x06%\n\x06\f\x06\x0E\x06(\v\x06\x03\x06\x03\x06\x03\x07' +
    '\x03\x07\x03\x07\x03\b\x07\b0\n\b\f\b\x0E\b3\v\b\x03\b\x03\b\x07\b7\n' +
    '\b\f\b\x0E\b:\v\b\x03\t\x06\t=\n\t\r\t\x0E\t>\x03\n\x03\n\x03\v\x06\v' +
    'D\n\v\r\v\x0E\vE\x03\v\x03\v\x02\x02\x02\f\x03\x02\x03\x05\x02\x04\x07' +
    '\x02\x05\t\x02\x06\v\x02\x07\r\x02\x02\x0F\x02\b\x11\x02\t\x13\x02\x02' +
    '\x15\x02\n\x03\x02\x06\x06\x02\f\f\x0F\x0F$$^^\x05\x02$$11^^\x06\x02/' +
    '<B\\aac|\x05\x02\v\f\x0F\x0F""\x02L\x02\x03\x03\x02\x02\x02\x02\x05' +
    '\x03\x02\x02\x02\x02\x07\x03\x02\x02\x02\x02\t\x03\x02\x02\x02\x02\v\x03' +
    '\x02\x02\x02\x02\x0F\x03\x02\x02\x02\x02\x11\x03\x02\x02\x02\x02\x15\x03' +
    '\x02\x02\x02\x03\x17\x03\x02\x02\x02\x05\x19\x03\x02\x02\x02\x07\x1B\x03' +
    '\x02\x02\x02\t\x1F\x03\x02\x02\x02\v!\x03\x02\x02\x02\r+\x03\x02\x02\x02' +
    '\x0F1\x03\x02\x02\x02\x11<\x03\x02\x02\x02\x13@\x03\x02\x02\x02\x15C\x03' +
    '\x02\x02\x02\x17\x18\x07]\x02\x02\x18\x04\x03\x02\x02\x02\x19\x1A\x07' +
    '_\x02\x02\x1A\x06\x03\x02\x02\x02\x1B\x1C\x070\x02\x02\x1C\x1D\x070\x02' +
    '\x02\x1D\x1E\x070\x02\x02\x1E\b\x03\x02\x02\x02\x1F \x07.\x02\x02 \n\x03' +
    '\x02\x02\x02!&\x07$\x02\x02"%\x05\r\x07\x02#%\n\x02\x02\x02$"\x03\x02' +
    "\x02\x02$#\x03\x02\x02\x02%(\x03\x02\x02\x02&$\x03\x02\x02\x02&\'\x03" +
    "\x02\x02\x02\')\x03\x02\x02\x02(&\x03\x02\x02\x02)*\x07$\x02\x02*\f\x03" +
    '\x02\x02\x02+,\x07^\x02\x02,-\t\x03\x02\x02-\x0E\x03\x02\x02\x02.0\x05' +
    '\x13\n\x02/.\x03\x02\x02\x0203\x03\x02\x02\x021/\x03\x02\x02\x0212\x03' +
    '\x02\x02\x0224\x03\x02\x02\x0231\x03\x02\x02\x0248\x07,\x02\x0257\x05' +
    '\x13\n\x0265\x03\x02\x02\x027:\x03\x02\x02\x0286\x03\x02\x02\x0289\x03' +
    '\x02\x02\x029\x10\x03\x02\x02\x02:8\x03\x02\x02\x02;=\x05\x13\n\x02<;' +
    '\x03\x02\x02\x02=>\x03\x02\x02\x02><\x03\x02\x02\x02>?\x03\x02\x02\x02' +
    '?\x12\x03\x02\x02\x02@A\t\x04\x02\x02A\x14\x03\x02\x02\x02BD\t\x05\x02' +
    '\x02CB\x03\x02\x02\x02DE\x03\x02\x02\x02EC\x03\x02\x02\x02EF\x03\x02\x02' +
    '\x02FG\x03\x02\x02\x02GH\b\v\x02\x02H\x16\x03\x02\x02\x02\t\x02$&18>E' +
    '\x03\b\x02\x02';
  public static __ATN: ATN;
  public static get _ATN(): ATN {
    if (!PartitionSelectionLexer.__ATN) {
      PartitionSelectionLexer.__ATN = new ATNDeserializer().deserialize(
        Utils.toCharArray(PartitionSelectionLexer._serializedATN),
      );
    }

    return PartitionSelectionLexer.__ATN;
  }
}
