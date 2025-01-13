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
  public static readonly QUOTED_STRING = 12;
  public static readonly UNQUOTED_STRING = 13;
  public static readonly WS = 14;

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
    '\x03\uC91D\uCABA\u058D\uAFBA\u4F53\u0607\uEA8B\uC241\x02\x10d\b\x01\x04' +
    '\x02\t\x02\x04\x03\t\x03\x04\x04\t\x04\x04\x05\t\x05\x04\x06\t\x06\x04' +
    '\x07\t\x07\x04\b\t\b\x04\t\t\t\x04\n\t\n\x04\v\t\v\x04\f\t\f\x04\r\t\r' +
    '\x04\x0E\t\x0E\x04\x0F\t\x0F\x03\x02\x03\x02\x03\x02\x03\x02\x03\x03\x03' +
    '\x03\x03\x03\x03\x04\x03\x04\x03\x04\x03\x04\x03\x05\x03\x05\x03\x06\x03' +
    '\x06\x03\x07\x06\x070\n\x07\r\x07\x0E\x071\x03\b\x03\b\x03\t\x03\t\x03' +
    '\n\x03\n\x03\v\x03\v\x03\v\x03\v\x03\v\x03\f\x03\f\x03\f\x03\f\x03\f\x03' +
    '\f\x03\f\x03\f\x03\f\x03\f\x03\f\x03\f\x03\f\x03\f\x03\f\x03\r\x03\r\x07' +
    '\rP\n\r\f\r\x0E\rS\v\r\x03\r\x03\r\x03\x0E\x03\x0E\x07\x0EY\n\x0E\f\x0E' +
    '\x0E\x0E\\\v\x0E\x03\x0F\x06\x0F_\n\x0F\r\x0F\x0E\x0F`\x03\x0F\x03\x0F' +
    '\x02\x02\x02\x10\x03\x02\x03\x05\x02\x04\x07\x02\x05\t\x02\x06\v\x02\x07' +
    '\r\x02\b\x0F\x02\t\x11\x02\n\x13\x02\v\x15\x02\f\x17\x02\r\x19\x02\x0E' +
    '\x1B\x02\x0F\x1D\x02\x10\x03\x02\x07\x03\x022;\x06\x02\f\f\x0F\x0F$$^' +
    '^\x05\x02C\\aac|\x06\x022;C\\aac|\x05\x02\v\f\x0F\x0F""\x02g\x02\x03' +
    '\x03\x02\x02\x02\x02\x05\x03\x02\x02\x02\x02\x07\x03\x02\x02\x02\x02\t' +
    '\x03\x02\x02\x02\x02\v\x03\x02\x02\x02\x02\r\x03\x02\x02\x02\x02\x0F\x03' +
    '\x02\x02\x02\x02\x11\x03\x02\x02\x02\x02\x13\x03\x02\x02\x02\x02\x15\x03' +
    '\x02\x02\x02\x02\x17\x03\x02\x02\x02\x02\x19\x03\x02\x02\x02\x02\x1B\x03' +
    '\x02\x02\x02\x02\x1D\x03\x02\x02\x02\x03\x1F\x03\x02\x02\x02\x05#\x03' +
    '\x02\x02\x02\x07&\x03\x02\x02\x02\t*\x03\x02\x02\x02\v,\x03\x02\x02\x02' +
    '\r/\x03\x02\x02\x02\x0F3\x03\x02\x02\x02\x115\x03\x02\x02\x02\x137\x03' +
    '\x02\x02\x02\x159\x03\x02\x02\x02\x17>\x03\x02\x02\x02\x19M\x03\x02\x02' +
    '\x02\x1BV\x03\x02\x02\x02\x1D^\x03\x02\x02\x02\x1F \x07c\x02\x02 !\x07' +
    'p\x02\x02!"\x07f\x02\x02"\x04\x03\x02\x02\x02#$\x07q\x02\x02$%\x07t' +
    "\x02\x02%\x06\x03\x02\x02\x02&'\x07p\x02\x02'(\x07q\x02\x02()\x07v\x02" +
    '\x02)\b\x03\x02\x02\x02*+\x07,\x02\x02+\n\x03\x02\x02\x02,-\x07-\x02\x02' +
    '-\f\x03\x02\x02\x02.0\t\x02\x02\x02/.\x03\x02\x02\x0201\x03\x02\x02\x02' +
    '1/\x03\x02\x02\x0212\x03\x02\x02\x022\x0E\x03\x02\x02\x0234\x07<\x02\x02' +
    '4\x10\x03\x02\x02\x0256\x07*\x02\x026\x12\x03\x02\x02\x0278\x07+\x02\x02' +
    '8\x14\x03\x02\x02\x029:\x07p\x02\x02:;\x07c\x02\x02;<\x07o\x02\x02<=\x07' +
    'g\x02\x02=\x16\x03\x02\x02\x02>?\x07p\x02\x02?@\x07c\x02\x02@A\x07o\x02' +
    '\x02AB\x07g\x02\x02BC\x07a\x02\x02CD\x07u\x02\x02DE\x07w\x02\x02EF\x07' +
    'd\x02\x02FG\x07u\x02\x02GH\x07v\x02\x02HI\x07t\x02\x02IJ\x07k\x02\x02' +
    'JK\x07p\x02\x02KL\x07i\x02\x02L\x18\x03\x02\x02\x02MQ\x07$\x02\x02NP\n' +
    '\x03\x02\x02ON\x03\x02\x02\x02PS\x03\x02\x02\x02QO\x03\x02\x02\x02QR\x03' +
    '\x02\x02\x02RT\x03\x02\x02\x02SQ\x03\x02\x02\x02TU\x07$\x02\x02U\x1A\x03' +
    '\x02\x02\x02VZ\t\x04\x02\x02WY\t\x05\x02\x02XW\x03\x02\x02\x02Y\\\x03' +
    '\x02\x02\x02ZX\x03\x02\x02\x02Z[\x03\x02\x02\x02[\x1C\x03\x02\x02\x02' +
    '\\Z\x03\x02\x02\x02]_\t\x06\x02\x02^]\x03\x02\x02\x02_`\x03\x02\x02\x02' +
    '`^\x03\x02\x02\x02`a\x03\x02\x02\x02ab\x03\x02\x02\x02bc\b\x0F\x02\x02' +
    'c\x1E\x03\x02\x02\x02\x07\x021QZ`\x03\b\x02\x02';
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
