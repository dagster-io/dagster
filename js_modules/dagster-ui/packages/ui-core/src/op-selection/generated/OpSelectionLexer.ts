// Generated from /Users/marcosalazar/code/dagster/js_modules/dagster-ui/packages/ui-core/src/op-selection/OpSelection.g4 by ANTLR 4.9.0-SNAPSHOT

import {CharStream} from 'antlr4ts/CharStream';
import {Lexer} from 'antlr4ts/Lexer';
import {Vocabulary} from 'antlr4ts/Vocabulary';
import {VocabularyImpl} from 'antlr4ts/VocabularyImpl';
import {ATN} from 'antlr4ts/atn/ATN';
import {ATNDeserializer} from 'antlr4ts/atn/ATNDeserializer';
import {LexerATNSimulator} from 'antlr4ts/atn/LexerATNSimulator';
import * as Utils from 'antlr4ts/misc/Utils';

export class OpSelectionLexer extends Lexer {
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
  public static readonly SINKS = 11;
  public static readonly ROOTS = 12;
  public static readonly QUOTED_STRING = 13;
  public static readonly UNQUOTED_STRING = 14;
  public static readonly UNQUOTED_REGEX_STRING = 15;
  public static readonly WS = 16;

  // tslint:disable:no-trailing-whitespace
  public static readonly channelNames: string[] = ['DEFAULT_TOKEN_CHANNEL', 'HIDDEN'];

  // tslint:disable:no-trailing-whitespace
  public static readonly modeNames: string[] = ['DEFAULT_MODE'];

  public static readonly ruleNames: string[] = [
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
    'SINKS',
    'ROOTS',
    'QUOTED_STRING',
    'UNQUOTED_STRING',
    'UNQUOTED_REGEX_STRING',
    'WS',
  ];

  private static readonly _LITERAL_NAMES: Array<string | undefined> = [
    undefined,
    "'and'",
    "'or'",
    "'not'",
    "'*'",
    "'+'",
    undefined,
    "':'",
    "'('",
    "')'",
    "'name'",
    "'sinks'",
    "'roots'",
  ];
  private static readonly _SYMBOLIC_NAMES: Array<string | undefined> = [
    undefined,
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
    'SINKS',
    'ROOTS',
    'QUOTED_STRING',
    'UNQUOTED_STRING',
    'UNQUOTED_REGEX_STRING',
    'WS',
  ];
  public static readonly VOCABULARY: Vocabulary = new VocabularyImpl(
    OpSelectionLexer._LITERAL_NAMES,
    OpSelectionLexer._SYMBOLIC_NAMES,
    [],
  );

  // @Override
  // @NotNull
  public get vocabulary(): Vocabulary {
    return OpSelectionLexer.VOCABULARY;
  }
  // tslint:enable:no-trailing-whitespace

  constructor(input: CharStream) {
    super(input);
    this._interp = new LexerATNSimulator(OpSelectionLexer._ATN, this);
  }

  // @Override
  public get grammarFileName(): string {
    return 'OpSelection.g4';
  }

  // @Override
  public get ruleNames(): string[] {
    return OpSelectionLexer.ruleNames;
  }

  // @Override
  public get serializedATN(): string {
    return OpSelectionLexer._serializedATN;
  }

  // @Override
  public get channelNames(): string[] {
    return OpSelectionLexer.channelNames;
  }

  // @Override
  public get modeNames(): string[] {
    return OpSelectionLexer.modeNames;
  }

  public static readonly _serializedATN: string =
    '\x03\uC91D\uCABA\u058D\uAFBA\u4F53\u0607\uEA8B\uC241\x02\x12l\b\x01\x04' +
    '\x02\t\x02\x04\x03\t\x03\x04\x04\t\x04\x04\x05\t\x05\x04\x06\t\x06\x04' +
    '\x07\t\x07\x04\b\t\b\x04\t\t\t\x04\n\t\n\x04\v\t\v\x04\f\t\f\x04\r\t\r' +
    '\x04\x0E\t\x0E\x04\x0F\t\x0F\x04\x10\t\x10\x04\x11\t\x11\x03\x02\x03\x02' +
    '\x03\x02\x03\x02\x03\x03\x03\x03\x03\x03\x03\x04\x03\x04\x03\x04\x03\x04' +
    '\x03\x05\x03\x05\x03\x06\x03\x06\x03\x07\x06\x074\n\x07\r\x07\x0E\x07' +
    '5\x03\b\x03\b\x03\t\x03\t\x03\n\x03\n\x03\v\x03\v\x03\v\x03\v\x03\v\x03' +
    '\f\x03\f\x03\f\x03\f\x03\f\x03\f\x03\r\x03\r\x03\r\x03\r\x03\r\x03\r\x03' +
    '\x0E\x03\x0E\x07\x0EQ\n\x0E\f\x0E\x0E\x0ET\v\x0E\x03\x0E\x03\x0E\x03\x0F' +
    '\x03\x0F\x07\x0FZ\n\x0F\f\x0F\x0E\x0F]\v\x0F\x03\x10\x03\x10\x07\x10a' +
    '\n\x10\f\x10\x0E\x10d\v\x10\x03\x11\x06\x11g\n\x11\r\x11\x0E\x11h\x03' +
    '\x11\x03\x11\x02\x02\x02\x12\x03\x02\x03\x05\x02\x04\x07\x02\x05\t\x02' +
    '\x06\v\x02\x07\r\x02\b\x0F\x02\t\x11\x02\n\x13\x02\v\x15\x02\f\x17\x02' +
    '\r\x19\x02\x0E\x1B\x02\x0F\x1D\x02\x10\x1F\x02\x11!\x02\x12\x03\x02\t' +
    '\x03\x022;\x06\x02\f\f\x0F\x0F$$^^\x05\x02C\\aac|\x06\x022;C\\aac|\x06' +
    '\x02,,C\\aac|\x07\x02,,2;C\\aac|\x05\x02\v\f\x0F\x0F""\x02p\x02\x03' +
    '\x03\x02\x02\x02\x02\x05\x03\x02\x02\x02\x02\x07\x03\x02\x02\x02\x02\t' +
    '\x03\x02\x02\x02\x02\v\x03\x02\x02\x02\x02\r\x03\x02\x02\x02\x02\x0F\x03' +
    '\x02\x02\x02\x02\x11\x03\x02\x02\x02\x02\x13\x03\x02\x02\x02\x02\x15\x03' +
    '\x02\x02\x02\x02\x17\x03\x02\x02\x02\x02\x19\x03\x02\x02\x02\x02\x1B\x03' +
    '\x02\x02\x02\x02\x1D\x03\x02\x02\x02\x02\x1F\x03\x02\x02\x02\x02!\x03' +
    "\x02\x02\x02\x03#\x03\x02\x02\x02\x05'\x03\x02\x02\x02\x07*\x03\x02\x02" +
    '\x02\t.\x03\x02\x02\x02\v0\x03\x02\x02\x02\r3\x03\x02\x02\x02\x0F7\x03' +
    '\x02\x02\x02\x119\x03\x02\x02\x02\x13;\x03\x02\x02\x02\x15=\x03\x02\x02' +
    '\x02\x17B\x03\x02\x02\x02\x19H\x03\x02\x02\x02\x1BN\x03\x02\x02\x02\x1D' +
    'W\x03\x02\x02\x02\x1F^\x03\x02\x02\x02!f\x03\x02\x02\x02#$\x07c\x02\x02' +
    "$%\x07p\x02\x02%&\x07f\x02\x02&\x04\x03\x02\x02\x02'(\x07q\x02\x02()" +
    '\x07t\x02\x02)\x06\x03\x02\x02\x02*+\x07p\x02\x02+,\x07q\x02\x02,-\x07' +
    'v\x02\x02-\b\x03\x02\x02\x02./\x07,\x02\x02/\n\x03\x02\x02\x0201\x07-' +
    '\x02\x021\f\x03\x02\x02\x0224\t\x02\x02\x0232\x03\x02\x02\x0245\x03\x02' +
    '\x02\x0253\x03\x02\x02\x0256\x03\x02\x02\x026\x0E\x03\x02\x02\x0278\x07' +
    '<\x02\x028\x10\x03\x02\x02\x029:\x07*\x02\x02:\x12\x03\x02\x02\x02;<\x07' +
    '+\x02\x02<\x14\x03\x02\x02\x02=>\x07p\x02\x02>?\x07c\x02\x02?@\x07o\x02' +
    '\x02@A\x07g\x02\x02A\x16\x03\x02\x02\x02BC\x07u\x02\x02CD\x07k\x02\x02' +
    'DE\x07p\x02\x02EF\x07m\x02\x02FG\x07u\x02\x02G\x18\x03\x02\x02\x02HI\x07' +
    't\x02\x02IJ\x07q\x02\x02JK\x07q\x02\x02KL\x07v\x02\x02LM\x07u\x02\x02' +
    'M\x1A\x03\x02\x02\x02NR\x07$\x02\x02OQ\n\x03\x02\x02PO\x03\x02\x02\x02' +
    'QT\x03\x02\x02\x02RP\x03\x02\x02\x02RS\x03\x02\x02\x02SU\x03\x02\x02\x02' +
    'TR\x03\x02\x02\x02UV\x07$\x02\x02V\x1C\x03\x02\x02\x02W[\t\x04\x02\x02' +
    'XZ\t\x05\x02\x02YX\x03\x02\x02\x02Z]\x03\x02\x02\x02[Y\x03\x02\x02\x02' +
    '[\\\x03\x02\x02\x02\\\x1E\x03\x02\x02\x02][\x03\x02\x02\x02^b\t\x06\x02' +
    '\x02_a\t\x07\x02\x02`_\x03\x02\x02\x02ad\x03\x02\x02\x02b`\x03\x02\x02' +
    '\x02bc\x03\x02\x02\x02c \x03\x02\x02\x02db\x03\x02\x02\x02eg\t\b\x02\x02' +
    'fe\x03\x02\x02\x02gh\x03\x02\x02\x02hf\x03\x02\x02\x02hi\x03\x02\x02\x02' +
    'ij\x03\x02\x02\x02jk\b\x11\x02\x02k"\x03\x02\x02\x02\b\x025R[bh\x03\b' +
    '\x02\x02';
  public static __ATN: ATN;
  public static get _ATN(): ATN {
    if (!OpSelectionLexer.__ATN) {
      OpSelectionLexer.__ATN = new ATNDeserializer().deserialize(
        Utils.toCharArray(OpSelectionLexer._serializedATN),
      );
    }

    return OpSelectionLexer.__ATN;
  }
}
