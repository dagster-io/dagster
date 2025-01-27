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
  public static readonly NAME_SUBSTRING = 11;
  public static readonly SINKS = 12;
  public static readonly ROOTS = 13;
  public static readonly QUOTED_STRING = 14;
  public static readonly UNQUOTED_STRING = 15;
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
    'NAME_SUBSTRING',
    'SINKS',
    'ROOTS',
    'QUOTED_STRING',
    'UNQUOTED_STRING',
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
    "'name_substring'",
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
    'NAME_SUBSTRING',
    'SINKS',
    'ROOTS',
    'QUOTED_STRING',
    'UNQUOTED_STRING',
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
    '\x03\uC91D\uCABA\u058D\uAFBA\u4F53\u0607\uEA8B\uC241\x02\x12t\b\x01\x04' +
    '\x02\t\x02\x04\x03\t\x03\x04\x04\t\x04\x04\x05\t\x05\x04\x06\t\x06\x04' +
    '\x07\t\x07\x04\b\t\b\x04\t\t\t\x04\n\t\n\x04\v\t\v\x04\f\t\f\x04\r\t\r' +
    '\x04\x0E\t\x0E\x04\x0F\t\x0F\x04\x10\t\x10\x04\x11\t\x11\x03\x02\x03\x02' +
    '\x03\x02\x03\x02\x03\x03\x03\x03\x03\x03\x03\x04\x03\x04\x03\x04\x03\x04' +
    '\x03\x05\x03\x05\x03\x06\x03\x06\x03\x07\x06\x074\n\x07\r\x07\x0E\x07' +
    '5\x03\b\x03\b\x03\t\x03\t\x03\n\x03\n\x03\v\x03\v\x03\v\x03\v\x03\v\x03' +
    '\f\x03\f\x03\f\x03\f\x03\f\x03\f\x03\f\x03\f\x03\f\x03\f\x03\f\x03\f\x03' +
    '\f\x03\f\x03\f\x03\r\x03\r\x03\r\x03\r\x03\r\x03\r\x03\x0E\x03\x0E\x03' +
    '\x0E\x03\x0E\x03\x0E\x03\x0E\x03\x0F\x03\x0F\x07\x0F`\n\x0F\f\x0F\x0E' +
    '\x0Fc\v\x0F\x03\x0F\x03\x0F\x03\x10\x03\x10\x07\x10i\n\x10\f\x10\x0E\x10' +
    'l\v\x10\x03\x11\x06\x11o\n\x11\r\x11\x0E\x11p\x03\x11\x03\x11\x02\x02' +
    '\x02\x12\x03\x02\x03\x05\x02\x04\x07\x02\x05\t\x02\x06\v\x02\x07\r\x02' +
    '\b\x0F\x02\t\x11\x02\n\x13\x02\v\x15\x02\f\x17\x02\r\x19\x02\x0E\x1B\x02' +
    '\x0F\x1D\x02\x10\x1F\x02\x11!\x02\x12\x03\x02\x07\x03\x022;\x06\x02\f' +
    '\f\x0F\x0F$$^^\x05\x02C\\aac|\x06\x022;C\\aac|\x05\x02\v\f\x0F\x0F""' +
    '\x02w\x02\x03\x03\x02\x02\x02\x02\x05\x03\x02\x02\x02\x02\x07\x03\x02' +
    '\x02\x02\x02\t\x03\x02\x02\x02\x02\v\x03\x02\x02\x02\x02\r\x03\x02\x02' +
    '\x02\x02\x0F\x03\x02\x02\x02\x02\x11\x03\x02\x02\x02\x02\x13\x03\x02\x02' +
    '\x02\x02\x15\x03\x02\x02\x02\x02\x17\x03\x02\x02\x02\x02\x19\x03\x02\x02' +
    '\x02\x02\x1B\x03\x02\x02\x02\x02\x1D\x03\x02\x02\x02\x02\x1F\x03\x02\x02' +
    "\x02\x02!\x03\x02\x02\x02\x03#\x03\x02\x02\x02\x05'\x03\x02\x02\x02\x07" +
    '*\x03\x02\x02\x02\t.\x03\x02\x02\x02\v0\x03\x02\x02\x02\r3\x03\x02\x02' +
    '\x02\x0F7\x03\x02\x02\x02\x119\x03\x02\x02\x02\x13;\x03\x02\x02\x02\x15' +
    '=\x03\x02\x02\x02\x17B\x03\x02\x02\x02\x19Q\x03\x02\x02\x02\x1BW\x03\x02' +
    '\x02\x02\x1D]\x03\x02\x02\x02\x1Ff\x03\x02\x02\x02!n\x03\x02\x02\x02#' +
    "$\x07c\x02\x02$%\x07p\x02\x02%&\x07f\x02\x02&\x04\x03\x02\x02\x02'(\x07" +
    'q\x02\x02()\x07t\x02\x02)\x06\x03\x02\x02\x02*+\x07p\x02\x02+,\x07q\x02' +
    '\x02,-\x07v\x02\x02-\b\x03\x02\x02\x02./\x07,\x02\x02/\n\x03\x02\x02\x02' +
    '01\x07-\x02\x021\f\x03\x02\x02\x0224\t\x02\x02\x0232\x03\x02\x02\x024' +
    '5\x03\x02\x02\x0253\x03\x02\x02\x0256\x03\x02\x02\x026\x0E\x03\x02\x02' +
    '\x0278\x07<\x02\x028\x10\x03\x02\x02\x029:\x07*\x02\x02:\x12\x03\x02\x02' +
    '\x02;<\x07+\x02\x02<\x14\x03\x02\x02\x02=>\x07p\x02\x02>?\x07c\x02\x02' +
    '?@\x07o\x02\x02@A\x07g\x02\x02A\x16\x03\x02\x02\x02BC\x07p\x02\x02CD\x07' +
    'c\x02\x02DE\x07o\x02\x02EF\x07g\x02\x02FG\x07a\x02\x02GH\x07u\x02\x02' +
    'HI\x07w\x02\x02IJ\x07d\x02\x02JK\x07u\x02\x02KL\x07v\x02\x02LM\x07t\x02' +
    '\x02MN\x07k\x02\x02NO\x07p\x02\x02OP\x07i\x02\x02P\x18\x03\x02\x02\x02' +
    'QR\x07u\x02\x02RS\x07k\x02\x02ST\x07p\x02\x02TU\x07m\x02\x02UV\x07u\x02' +
    '\x02V\x1A\x03\x02\x02\x02WX\x07t\x02\x02XY\x07q\x02\x02YZ\x07q\x02\x02' +
    'Z[\x07v\x02\x02[\\\x07u\x02\x02\\\x1C\x03\x02\x02\x02]a\x07$\x02\x02^' +
    '`\n\x03\x02\x02_^\x03\x02\x02\x02`c\x03\x02\x02\x02a_\x03\x02\x02\x02' +
    'ab\x03\x02\x02\x02bd\x03\x02\x02\x02ca\x03\x02\x02\x02de\x07$\x02\x02' +
    'e\x1E\x03\x02\x02\x02fj\t\x04\x02\x02gi\t\x05\x02\x02hg\x03\x02\x02\x02' +
    'il\x03\x02\x02\x02jh\x03\x02\x02\x02jk\x03\x02\x02\x02k \x03\x02\x02\x02' +
    'lj\x03\x02\x02\x02mo\t\x06\x02\x02nm\x03\x02\x02\x02op\x03\x02\x02\x02' +
    'pn\x03\x02\x02\x02pq\x03\x02\x02\x02qr\x03\x02\x02\x02rs\b\x11\x02\x02' +
    's"\x03\x02\x02\x02\x07\x025ajp\x03\b\x02\x02';
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
