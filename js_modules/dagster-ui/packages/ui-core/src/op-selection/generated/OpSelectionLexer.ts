// Generated from /Users/briantu/repos/dagster/js_modules/dagster-ui/packages/ui-core/src/op-selection/OpSelection.g4 by ANTLR 4.9.0-SNAPSHOT

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
  public static readonly COLON = 6;
  public static readonly LPAREN = 7;
  public static readonly RPAREN = 8;
  public static readonly NAME = 9;
  public static readonly NAME_SUBSTRING = 10;
  public static readonly QUOTED_STRING = 11;
  public static readonly UNQUOTED_STRING = 12;
  public static readonly WS = 13;

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
    'COLON',
    'LPAREN',
    'RPAREN',
    'NAME',
    'NAME_SUBSTRING',
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
    "':'",
    "'('",
    "')'",
    "'name'",
    "'name_substring'",
  ];
  private static readonly _SYMBOLIC_NAMES: Array<string | undefined> = [
    undefined,
    'AND',
    'OR',
    'NOT',
    'STAR',
    'PLUS',
    'COLON',
    'LPAREN',
    'RPAREN',
    'NAME',
    'NAME_SUBSTRING',
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
    '\x03\uC91D\uCABA\u058D\uAFBA\u4F53\u0607\uEA8B\uC241\x02\x0F]\b\x01\x04' +
    '\x02\t\x02\x04\x03\t\x03\x04\x04\t\x04\x04\x05\t\x05\x04\x06\t\x06\x04' +
    '\x07\t\x07\x04\b\t\b\x04\t\t\t\x04\n\t\n\x04\v\t\v\x04\f\t\f\x04\r\t\r' +
    '\x04\x0E\t\x0E\x03\x02\x03\x02\x03\x02\x03\x02\x03\x03\x03\x03\x03\x03' +
    '\x03\x04\x03\x04\x03\x04\x03\x04\x03\x05\x03\x05\x03\x06\x03\x06\x03\x07' +
    '\x03\x07\x03\b\x03\b\x03\t\x03\t\x03\n\x03\n\x03\n\x03\n\x03\n\x03\v\x03' +
    '\v\x03\v\x03\v\x03\v\x03\v\x03\v\x03\v\x03\v\x03\v\x03\v\x03\v\x03\v\x03' +
    '\v\x03\v\x03\f\x03\f\x07\fI\n\f\f\f\x0E\fL\v\f\x03\f\x03\f\x03\r\x03\r' +
    '\x07\rR\n\r\f\r\x0E\rU\v\r\x03\x0E\x06\x0EX\n\x0E\r\x0E\x0E\x0EY\x03\x0E' +
    '\x03\x0E\x02\x02\x02\x0F\x03\x02\x03\x05\x02\x04\x07\x02\x05\t\x02\x06' +
    '\v\x02\x07\r\x02\b\x0F\x02\t\x11\x02\n\x13\x02\v\x15\x02\f\x17\x02\r\x19' +
    '\x02\x0E\x1B\x02\x0F\x03\x02\x06\x06\x02\f\f\x0F\x0F$$^^\x05\x02C\\aa' +
    'c|\x06\x022;C\\aac|\x05\x02\v\f\x0F\x0F""\x02_\x02\x03\x03\x02\x02\x02' +
    '\x02\x05\x03\x02\x02\x02\x02\x07\x03\x02\x02\x02\x02\t\x03\x02\x02\x02' +
    '\x02\v\x03\x02\x02\x02\x02\r\x03\x02\x02\x02\x02\x0F\x03\x02\x02\x02\x02' +
    '\x11\x03\x02\x02\x02\x02\x13\x03\x02\x02\x02\x02\x15\x03\x02\x02\x02\x02' +
    '\x17\x03\x02\x02\x02\x02\x19\x03\x02\x02\x02\x02\x1B\x03\x02\x02\x02\x03' +
    '\x1D\x03\x02\x02\x02\x05!\x03\x02\x02\x02\x07$\x03\x02\x02\x02\t(\x03' +
    '\x02\x02\x02\v*\x03\x02\x02\x02\r,\x03\x02\x02\x02\x0F.\x03\x02\x02\x02' +
    '\x110\x03\x02\x02\x02\x132\x03\x02\x02\x02\x157\x03\x02\x02\x02\x17F\x03' +
    '\x02\x02\x02\x19O\x03\x02\x02\x02\x1BW\x03\x02\x02\x02\x1D\x1E\x07c\x02' +
    '\x02\x1E\x1F\x07p\x02\x02\x1F \x07f\x02\x02 \x04\x03\x02\x02\x02!"\x07' +
    'q\x02\x02"#\x07t\x02\x02#\x06\x03\x02\x02\x02$%\x07p\x02\x02%&\x07q\x02' +
    "\x02&'\x07v\x02\x02'\b\x03\x02\x02\x02()\x07,\x02\x02)\n\x03\x02\x02" +
    '\x02*+\x07-\x02\x02+\f\x03\x02\x02\x02,-\x07<\x02\x02-\x0E\x03\x02\x02' +
    '\x02./\x07*\x02\x02/\x10\x03\x02\x02\x0201\x07+\x02\x021\x12\x03\x02\x02' +
    '\x0223\x07p\x02\x0234\x07c\x02\x0245\x07o\x02\x0256\x07g\x02\x026\x14' +
    '\x03\x02\x02\x0278\x07p\x02\x0289\x07c\x02\x029:\x07o\x02\x02:;\x07g\x02' +
    '\x02;<\x07a\x02\x02<=\x07u\x02\x02=>\x07w\x02\x02>?\x07d\x02\x02?@\x07' +
    'u\x02\x02@A\x07v\x02\x02AB\x07t\x02\x02BC\x07k\x02\x02CD\x07p\x02\x02' +
    'DE\x07i\x02\x02E\x16\x03\x02\x02\x02FJ\x07$\x02\x02GI\n\x02\x02\x02HG' +
    '\x03\x02\x02\x02IL\x03\x02\x02\x02JH\x03\x02\x02\x02JK\x03\x02\x02\x02' +
    'KM\x03\x02\x02\x02LJ\x03\x02\x02\x02MN\x07$\x02\x02N\x18\x03\x02\x02\x02' +
    'OS\t\x03\x02\x02PR\t\x04\x02\x02QP\x03\x02\x02\x02RU\x03\x02\x02\x02S' +
    'Q\x03\x02\x02\x02ST\x03\x02\x02\x02T\x1A\x03\x02\x02\x02US\x03\x02\x02' +
    '\x02VX\t\x05\x02\x02WV\x03\x02\x02\x02XY\x03\x02\x02\x02YW\x03\x02\x02' +
    '\x02YZ\x03\x02\x02\x02Z[\x03\x02\x02\x02[\\\b\x0E\x02\x02\\\x1C\x03\x02' +
    '\x02\x02\x06\x02JSY\x03\b\x02\x02';
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
