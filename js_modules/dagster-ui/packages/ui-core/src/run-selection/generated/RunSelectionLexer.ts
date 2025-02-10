// Generated from /Users/marcosalazar/code/dagster/js_modules/dagster-ui/packages/ui-core/src/run-selection/RunSelection.g4 by ANTLR 4.9.0-SNAPSHOT

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
  public static readonly DIGITS = 6;
  public static readonly COLON = 7;
  public static readonly LPAREN = 8;
  public static readonly RPAREN = 9;
  public static readonly NAME = 10;
  public static readonly STATUS = 11;
  public static readonly SINKS = 12;
  public static readonly ROOTS = 13;
  public static readonly QUOTED_STRING = 14;
  public static readonly UNQUOTED_STRING = 15;
  public static readonly UNQUOTED_REGEX_STRING = 16;
  public static readonly WS = 17;

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
    'STATUS',
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
    'DIGITS',
    'COLON',
    'LPAREN',
    'RPAREN',
    'NAME',
    'STATUS',
    'SINKS',
    'ROOTS',
    'QUOTED_STRING',
    'UNQUOTED_STRING',
    'UNQUOTED_REGEX_STRING',
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
    '\x03\uC91D\uCABA\u058D\uAFBA\u4F53\u0607\uEA8B\uC241\x02\x13u\b\x01\x04' +
    '\x02\t\x02\x04\x03\t\x03\x04\x04\t\x04\x04\x05\t\x05\x04\x06\t\x06\x04' +
    '\x07\t\x07\x04\b\t\b\x04\t\t\t\x04\n\t\n\x04\v\t\v\x04\f\t\f\x04\r\t\r' +
    '\x04\x0E\t\x0E\x04\x0F\t\x0F\x04\x10\t\x10\x04\x11\t\x11\x04\x12\t\x12' +
    '\x03\x02\x03\x02\x03\x02\x03\x02\x03\x03\x03\x03\x03\x03\x03\x04\x03\x04' +
    '\x03\x04\x03\x04\x03\x05\x03\x05\x03\x06\x03\x06\x03\x07\x06\x076\n\x07' +
    '\r\x07\x0E\x077\x03\b\x03\b\x03\t\x03\t\x03\n\x03\n\x03\v\x03\v\x03\v' +
    '\x03\v\x03\v\x03\f\x03\f\x03\f\x03\f\x03\f\x03\f\x03\f\x03\r\x03\r\x03' +
    '\r\x03\r\x03\r\x03\r\x03\x0E\x03\x0E\x03\x0E\x03\x0E\x03\x0E\x03\x0E\x03' +
    '\x0F\x03\x0F\x07\x0FZ\n\x0F\f\x0F\x0E\x0F]\v\x0F\x03\x0F\x03\x0F\x03\x10' +
    '\x03\x10\x07\x10c\n\x10\f\x10\x0E\x10f\v\x10\x03\x11\x03\x11\x07\x11j' +
    '\n\x11\f\x11\x0E\x11m\v\x11\x03\x12\x06\x12p\n\x12\r\x12\x0E\x12q\x03' +
    '\x12\x03\x12\x02\x02\x02\x13\x03\x02\x03\x05\x02\x04\x07\x02\x05\t\x02' +
    '\x06\v\x02\x07\r\x02\b\x0F\x02\t\x11\x02\n\x13\x02\v\x15\x02\f\x17\x02' +
    '\r\x19\x02\x0E\x1B\x02\x0F\x1D\x02\x10\x1F\x02\x11!\x02\x12#\x02\x13\x03' +
    '\x02\t\x03\x022;\x06\x02\f\f\x0F\x0F$$^^\x05\x02C\\aac|\x06\x022;C\\a' +
    'ac|\x06\x02,,C\\aac|\x07\x02,,2;C\\aac|\x05\x02\v\f\x0F\x0F""\x02y\x02' +
    '\x03\x03\x02\x02\x02\x02\x05\x03\x02\x02\x02\x02\x07\x03\x02\x02\x02\x02' +
    '\t\x03\x02\x02\x02\x02\v\x03\x02\x02\x02\x02\r\x03\x02\x02\x02\x02\x0F' +
    '\x03\x02\x02\x02\x02\x11\x03\x02\x02\x02\x02\x13\x03\x02\x02\x02\x02\x15' +
    '\x03\x02\x02\x02\x02\x17\x03\x02\x02\x02\x02\x19\x03\x02\x02\x02\x02\x1B' +
    '\x03\x02\x02\x02\x02\x1D\x03\x02\x02\x02\x02\x1F\x03\x02\x02\x02\x02!' +
    '\x03\x02\x02\x02\x02#\x03\x02\x02\x02\x03%\x03\x02\x02\x02\x05)\x03\x02' +
    '\x02\x02\x07,\x03\x02\x02\x02\t0\x03\x02\x02\x02\v2\x03\x02\x02\x02\r' +
    '5\x03\x02\x02\x02\x0F9\x03\x02\x02\x02\x11;\x03\x02\x02\x02\x13=\x03\x02' +
    '\x02\x02\x15?\x03\x02\x02\x02\x17D\x03\x02\x02\x02\x19K\x03\x02\x02\x02' +
    '\x1BQ\x03\x02\x02\x02\x1DW\x03\x02\x02\x02\x1F`\x03\x02\x02\x02!g\x03' +
    "\x02\x02\x02#o\x03\x02\x02\x02%&\x07c\x02\x02&'\x07p\x02\x02'(\x07f" +
    '\x02\x02(\x04\x03\x02\x02\x02)*\x07q\x02\x02*+\x07t\x02\x02+\x06\x03\x02' +
    '\x02\x02,-\x07p\x02\x02-.\x07q\x02\x02./\x07v\x02\x02/\b\x03\x02\x02\x02' +
    '01\x07,\x02\x021\n\x03\x02\x02\x0223\x07-\x02\x023\f\x03\x02\x02\x024' +
    '6\t\x02\x02\x0254\x03\x02\x02\x0267\x03\x02\x02\x0275\x03\x02\x02\x02' +
    '78\x03\x02\x02\x028\x0E\x03\x02\x02\x029:\x07<\x02\x02:\x10\x03\x02\x02' +
    '\x02;<\x07*\x02\x02<\x12\x03\x02\x02\x02=>\x07+\x02\x02>\x14\x03\x02\x02' +
    '\x02?@\x07p\x02\x02@A\x07c\x02\x02AB\x07o\x02\x02BC\x07g\x02\x02C\x16' +
    '\x03\x02\x02\x02DE\x07u\x02\x02EF\x07v\x02\x02FG\x07c\x02\x02GH\x07v\x02' +
    '\x02HI\x07w\x02\x02IJ\x07u\x02\x02J\x18\x03\x02\x02\x02KL\x07u\x02\x02' +
    'LM\x07k\x02\x02MN\x07p\x02\x02NO\x07m\x02\x02OP\x07u\x02\x02P\x1A\x03' +
    '\x02\x02\x02QR\x07t\x02\x02RS\x07q\x02\x02ST\x07q\x02\x02TU\x07v\x02\x02' +
    'UV\x07u\x02\x02V\x1C\x03\x02\x02\x02W[\x07$\x02\x02XZ\n\x03\x02\x02YX' +
    '\x03\x02\x02\x02Z]\x03\x02\x02\x02[Y\x03\x02\x02\x02[\\\x03\x02\x02\x02' +
    '\\^\x03\x02\x02\x02][\x03\x02\x02\x02^_\x07$\x02\x02_\x1E\x03\x02\x02' +
    '\x02`d\t\x04\x02\x02ac\t\x05\x02\x02ba\x03\x02\x02\x02cf\x03\x02\x02\x02' +
    'db\x03\x02\x02\x02de\x03\x02\x02\x02e \x03\x02\x02\x02fd\x03\x02\x02\x02' +
    'gk\t\x06\x02\x02hj\t\x07\x02\x02ih\x03\x02\x02\x02jm\x03\x02\x02\x02k' +
    'i\x03\x02\x02\x02kl\x03\x02\x02\x02l"\x03\x02\x02\x02mk\x03\x02\x02\x02' +
    'np\t\b\x02\x02on\x03\x02\x02\x02pq\x03\x02\x02\x02qo\x03\x02\x02\x02q' +
    'r\x03\x02\x02\x02rs\x03\x02\x02\x02st\b\x12\x02\x02t$\x03\x02\x02\x02' +
    '\b\x027[dkq\x03\b\x02\x02';
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
