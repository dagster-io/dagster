// Generated from /Users/briantu/repos/dagster/js_modules/dagster-ui/packages/ui-core/src/run-selection/RunSelection.g4 by ANTLR 4.9.0-SNAPSHOT

import {CharStream} from 'antlr4ts/CharStream';
import {Lexer} from 'antlr4ts/Lexer';
import {Vocabulary} from 'antlr4ts/Vocabulary';
import {VocabularyImpl} from 'antlr4ts/VocabularyImpl';
import {ATN} from 'antlr4ts/atn/ATN';
import {ATNDeserializer} from 'antlr4ts/atn/ATNDeserializer';
import {LexerATNSimulator} from 'antlr4ts/atn/LexerATNSimulator';
import * as Utils from 'antlr4ts/misc/Utils';

export class RunSelectionLexer extends Lexer {
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
  public static readonly STATUS = 11;
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
    'COLON',
    'LPAREN',
    'RPAREN',
    'NAME',
    'NAME_SUBSTRING',
    'STATUS',
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
    "':'",
    "'('",
    "')'",
    "'name'",
    "'name_substring'",
    "'status'",
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
    'COLON',
    'LPAREN',
    'RPAREN',
    'NAME',
    'NAME_SUBSTRING',
    'STATUS',
    'SINKS',
    'ROOTS',
    'QUOTED_STRING',
    'UNQUOTED_STRING',
    'WS',
  ];
  public static readonly VOCABULARY: Vocabulary = new VocabularyImpl(
    RunSelectionLexer._LITERAL_NAMES,
    RunSelectionLexer._SYMBOLIC_NAMES,
    [],
  );

  // @Override
  // @NotNull
  public get vocabulary(): Vocabulary {
    return RunSelectionLexer.VOCABULARY;
  }
  // tslint:enable:no-trailing-whitespace

  constructor(input: CharStream) {
    super(input);
    this._interp = new LexerATNSimulator(RunSelectionLexer._ATN, this);
  }

  // @Override
  public get grammarFileName(): string {
    return 'RunSelection.g4';
  }

  // @Override
  public get ruleNames(): string[] {
    return RunSelectionLexer.ruleNames;
  }

  // @Override
  public get serializedATN(): string {
    return RunSelectionLexer._serializedATN;
  }

  // @Override
  public get channelNames(): string[] {
    return RunSelectionLexer.channelNames;
  }

  // @Override
  public get modeNames(): string[] {
    return RunSelectionLexer.modeNames;
  }

  public static readonly _serializedATN: string =
    '\x03\uC91D\uCABA\u058D\uAFBA\u4F53\u0607\uEA8B\uC241\x02\x12v\b\x01\x04' +
    '\x02\t\x02\x04\x03\t\x03\x04\x04\t\x04\x04\x05\t\x05\x04\x06\t\x06\x04' +
    '\x07\t\x07\x04\b\t\b\x04\t\t\t\x04\n\t\n\x04\v\t\v\x04\f\t\f\x04\r\t\r' +
    '\x04\x0E\t\x0E\x04\x0F\t\x0F\x04\x10\t\x10\x04\x11\t\x11\x03\x02\x03\x02' +
    '\x03\x02\x03\x02\x03\x03\x03\x03\x03\x03\x03\x04\x03\x04\x03\x04\x03\x04' +
    '\x03\x05\x03\x05\x03\x06\x03\x06\x03\x07\x03\x07\x03\b\x03\b\x03\t\x03' +
    '\t\x03\n\x03\n\x03\n\x03\n\x03\n\x03\v\x03\v\x03\v\x03\v\x03\v\x03\v\x03' +
    '\v\x03\v\x03\v\x03\v\x03\v\x03\v\x03\v\x03\v\x03\v\x03\f\x03\f\x03\f\x03' +
    '\f\x03\f\x03\f\x03\f\x03\r\x03\r\x03\r\x03\r\x03\r\x03\r\x03\x0E\x03\x0E' +
    '\x03\x0E\x03\x0E\x03\x0E\x03\x0E\x03\x0F\x03\x0F\x07\x0Fb\n\x0F\f\x0F' +
    '\x0E\x0Fe\v\x0F\x03\x0F\x03\x0F\x03\x10\x03\x10\x07\x10k\n\x10\f\x10\x0E' +
    '\x10n\v\x10\x03\x11\x06\x11q\n\x11\r\x11\x0E\x11r\x03\x11\x03\x11\x02' +
    '\x02\x02\x12\x03\x02\x03\x05\x02\x04\x07\x02\x05\t\x02\x06\v\x02\x07\r' +
    '\x02\b\x0F\x02\t\x11\x02\n\x13\x02\v\x15\x02\f\x17\x02\r\x19\x02\x0E\x1B' +
    '\x02\x0F\x1D\x02\x10\x1F\x02\x11!\x02\x12\x03\x02\x06\x06\x02\f\f\x0F' +
    '\x0F$$^^\x05\x02C\\aac|\x06\x022;C\\aac|\x05\x02\v\f\x0F\x0F""\x02x' +
    '\x02\x03\x03\x02\x02\x02\x02\x05\x03\x02\x02\x02\x02\x07\x03\x02\x02\x02' +
    '\x02\t\x03\x02\x02\x02\x02\v\x03\x02\x02\x02\x02\r\x03\x02\x02\x02\x02' +
    '\x0F\x03\x02\x02\x02\x02\x11\x03\x02\x02\x02\x02\x13\x03\x02\x02\x02\x02' +
    '\x15\x03\x02\x02\x02\x02\x17\x03\x02\x02\x02\x02\x19\x03\x02\x02\x02\x02' +
    '\x1B\x03\x02\x02\x02\x02\x1D\x03\x02\x02\x02\x02\x1F\x03\x02\x02\x02\x02' +
    "!\x03\x02\x02\x02\x03#\x03\x02\x02\x02\x05'\x03\x02\x02\x02\x07*\x03" +
    '\x02\x02\x02\t.\x03\x02\x02\x02\v0\x03\x02\x02\x02\r2\x03\x02\x02\x02' +
    '\x0F4\x03\x02\x02\x02\x116\x03\x02\x02\x02\x138\x03\x02\x02\x02\x15=\x03' +
    '\x02\x02\x02\x17L\x03\x02\x02\x02\x19S\x03\x02\x02\x02\x1BY\x03\x02\x02' +
    '\x02\x1D_\x03\x02\x02\x02\x1Fh\x03\x02\x02\x02!p\x03\x02\x02\x02#$\x07' +
    "c\x02\x02$%\x07p\x02\x02%&\x07f\x02\x02&\x04\x03\x02\x02\x02'(\x07q\x02" +
    '\x02()\x07t\x02\x02)\x06\x03\x02\x02\x02*+\x07p\x02\x02+,\x07q\x02\x02' +
    ',-\x07v\x02\x02-\b\x03\x02\x02\x02./\x07,\x02\x02/\n\x03\x02\x02\x020' +
    '1\x07-\x02\x021\f\x03\x02\x02\x0223\x07<\x02\x023\x0E\x03\x02\x02\x02' +
    '45\x07*\x02\x025\x10\x03\x02\x02\x0267\x07+\x02\x027\x12\x03\x02\x02\x02' +
    '89\x07p\x02\x029:\x07c\x02\x02:;\x07o\x02\x02;<\x07g\x02\x02<\x14\x03' +
    '\x02\x02\x02=>\x07p\x02\x02>?\x07c\x02\x02?@\x07o\x02\x02@A\x07g\x02\x02' +
    'AB\x07a\x02\x02BC\x07u\x02\x02CD\x07w\x02\x02DE\x07d\x02\x02EF\x07u\x02' +
    '\x02FG\x07v\x02\x02GH\x07t\x02\x02HI\x07k\x02\x02IJ\x07p\x02\x02JK\x07' +
    'i\x02\x02K\x16\x03\x02\x02\x02LM\x07u\x02\x02MN\x07v\x02\x02NO\x07c\x02' +
    '\x02OP\x07v\x02\x02PQ\x07w\x02\x02QR\x07u\x02\x02R\x18\x03\x02\x02\x02' +
    'ST\x07u\x02\x02TU\x07k\x02\x02UV\x07p\x02\x02VW\x07m\x02\x02WX\x07u\x02' +
    '\x02X\x1A\x03\x02\x02\x02YZ\x07t\x02\x02Z[\x07q\x02\x02[\\\x07q\x02\x02' +
    '\\]\x07v\x02\x02]^\x07u\x02\x02^\x1C\x03\x02\x02\x02_c\x07$\x02\x02`b' +
    '\n\x02\x02\x02a`\x03\x02\x02\x02be\x03\x02\x02\x02ca\x03\x02\x02\x02c' +
    'd\x03\x02\x02\x02df\x03\x02\x02\x02ec\x03\x02\x02\x02fg\x07$\x02\x02g' +
    '\x1E\x03\x02\x02\x02hl\t\x03\x02\x02ik\t\x04\x02\x02ji\x03\x02\x02\x02' +
    'kn\x03\x02\x02\x02lj\x03\x02\x02\x02lm\x03\x02\x02\x02m \x03\x02\x02\x02' +
    'nl\x03\x02\x02\x02oq\t\x05\x02\x02po\x03\x02\x02\x02qr\x03\x02\x02\x02' +
    'rp\x03\x02\x02\x02rs\x03\x02\x02\x02st\x03\x02\x02\x02tu\b\x11\x02\x02' +
    'u"\x03\x02\x02\x02\x06\x02clr\x03\b\x02\x02';
  public static __ATN: ATN;
  public static get _ATN(): ATN {
    if (!RunSelectionLexer.__ATN) {
      RunSelectionLexer.__ATN = new ATNDeserializer().deserialize(
        Utils.toCharArray(RunSelectionLexer._serializedATN),
      );
    }

    return RunSelectionLexer.__ATN;
  }
}
