// Generated from /Users/marcosalazar/code/dagster/js_modules/dagster-ui/packages/ui-core/src/selection/SelectionAutoComplete.g4 by ANTLR 4.9.0-SNAPSHOT

import {CharStream} from 'antlr4ts/CharStream';
import {Lexer} from 'antlr4ts/Lexer';
import {Vocabulary} from 'antlr4ts/Vocabulary';
import {VocabularyImpl} from 'antlr4ts/VocabularyImpl';
import {ATN} from 'antlr4ts/atn/ATN';
import {ATNDeserializer} from 'antlr4ts/atn/ATNDeserializer';
import {LexerATNSimulator} from 'antlr4ts/atn/LexerATNSimulator';
import * as Utils from 'antlr4ts/misc/Utils';

export class SelectionAutoCompleteLexer extends Lexer {
  public static readonly AND = 1;
  public static readonly OR = 2;
  public static readonly NOT = 3;
  public static readonly STAR = 4;
  public static readonly PLUS = 5;
  public static readonly COLON = 6;
  public static readonly LPAREN = 7;
  public static readonly RPAREN = 8;
  public static readonly EQUAL = 9;
  public static readonly QUOTED_STRING = 10;
  public static readonly INCOMPLETE_LEFT_QUOTED_STRING = 11;
  public static readonly INCOMPLETE_RIGHT_QUOTED_STRING = 12;
  public static readonly IDENTIFIER = 13;
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
    'COLON',
    'LPAREN',
    'RPAREN',
    'EQUAL',
    'QUOTED_STRING',
    'INCOMPLETE_LEFT_QUOTED_STRING',
    'INCOMPLETE_RIGHT_QUOTED_STRING',
    'IDENTIFIER',
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
    "'='",
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
    'EQUAL',
    'QUOTED_STRING',
    'INCOMPLETE_LEFT_QUOTED_STRING',
    'INCOMPLETE_RIGHT_QUOTED_STRING',
    'IDENTIFIER',
    'WS',
  ];
  public static readonly VOCABULARY: Vocabulary = new VocabularyImpl(
    SelectionAutoCompleteLexer._LITERAL_NAMES,
    SelectionAutoCompleteLexer._SYMBOLIC_NAMES,
    [],
  );

  // @Override
  // @NotNull
  public get vocabulary(): Vocabulary {
    return SelectionAutoCompleteLexer.VOCABULARY;
  }
  // tslint:enable:no-trailing-whitespace

  constructor(input: CharStream) {
    super(input);
    this._interp = new LexerATNSimulator(SelectionAutoCompleteLexer._ATN, this);
  }

  // @Override
  public get grammarFileName(): string {
    return 'SelectionAutoComplete.g4';
  }

  // @Override
  public get ruleNames(): string[] {
    return SelectionAutoCompleteLexer.ruleNames;
  }

  // @Override
  public get serializedATN(): string {
    return SelectionAutoCompleteLexer._serializedATN;
  }

  // @Override
  public get channelNames(): string[] {
    return SelectionAutoCompleteLexer.channelNames;
  }

  // @Override
  public get modeNames(): string[] {
    return SelectionAutoCompleteLexer.modeNames;
  }

  public static readonly _serializedATN: string =
    '\x03\uC91D\uCABA\u058D\uAFBA\u4F53\u0607\uEA8B\uC241\x02\x10Z\b\x01\x04' +
    '\x02\t\x02\x04\x03\t\x03\x04\x04\t\x04\x04\x05\t\x05\x04\x06\t\x06\x04' +
    '\x07\t\x07\x04\b\t\b\x04\t\t\t\x04\n\t\n\x04\v\t\v\x04\f\t\f\x04\r\t\r' +
    '\x04\x0E\t\x0E\x04\x0F\t\x0F\x03\x02\x03\x02\x03\x02\x03\x02\x03\x03\x03' +
    '\x03\x03\x03\x03\x04\x03\x04\x03\x04\x03\x04\x03\x05\x03\x05\x03\x06\x03' +
    '\x06\x03\x07\x03\x07\x03\b\x03\b\x03\t\x03\t\x03\n\x03\n\x03\v\x03\v\x07' +
    '\v9\n\v\f\v\x0E\v<\v\v\x03\v\x03\v\x03\f\x03\f\x07\fB\n\f\f\f\x0E\fE\v' +
    '\f\x03\r\x07\rH\n\r\f\r\x0E\rK\v\r\x03\r\x03\r\x03\x0E\x03\x0E\x07\x0E' +
    'Q\n\x0E\f\x0E\x0E\x0ET\v\x0E\x03\x0F\x06\x0FW\n\x0F\r\x0F\x0E\x0FX\x02' +
    '\x02\x02\x10\x03\x02\x03\x05\x02\x04\x07\x02\x05\t\x02\x06\v\x02\x07\r' +
    '\x02\b\x0F\x02\t\x11\x02\n\x13\x02\v\x15\x02\f\x17\x02\r\x19\x02\x0E\x1B' +
    '\x02\x0F\x1D\x02\x10\x03\x02\x07\x06\x02\f\f\x0F\x0F$$^^\b\x02\f\f\x0F' +
    '\x0F$$*+<<^^\x05\x02C\\aac|\x06\x022;C\\aac|\x05\x02\v\f\x0F\x0F""\x02' +
    '^\x02\x03\x03\x02\x02\x02\x02\x05\x03\x02\x02\x02\x02\x07\x03\x02\x02' +
    '\x02\x02\t\x03\x02\x02\x02\x02\v\x03\x02\x02\x02\x02\r\x03\x02\x02\x02' +
    '\x02\x0F\x03\x02\x02\x02\x02\x11\x03\x02\x02\x02\x02\x13\x03\x02\x02\x02' +
    '\x02\x15\x03\x02\x02\x02\x02\x17\x03\x02\x02\x02\x02\x19\x03\x02\x02\x02' +
    '\x02\x1B\x03\x02\x02\x02\x02\x1D\x03\x02\x02\x02\x03\x1F\x03\x02\x02\x02' +
    '\x05#\x03\x02\x02\x02\x07&\x03\x02\x02\x02\t*\x03\x02\x02\x02\v,\x03\x02' +
    '\x02\x02\r.\x03\x02\x02\x02\x0F0\x03\x02\x02\x02\x112\x03\x02\x02\x02' +
    '\x134\x03\x02\x02\x02\x156\x03\x02\x02\x02\x17?\x03\x02\x02\x02\x19I\x03' +
    '\x02\x02\x02\x1BN\x03\x02\x02\x02\x1DV\x03\x02\x02\x02\x1F \x07c\x02\x02' +
    ' !\x07p\x02\x02!"\x07f\x02\x02"\x04\x03\x02\x02\x02#$\x07q\x02\x02$' +
    "%\x07t\x02\x02%\x06\x03\x02\x02\x02&'\x07p\x02\x02'(\x07q\x02\x02()" +
    '\x07v\x02\x02)\b\x03\x02\x02\x02*+\x07,\x02\x02+\n\x03\x02\x02\x02,-\x07' +
    '-\x02\x02-\f\x03\x02\x02\x02./\x07<\x02\x02/\x0E\x03\x02\x02\x0201\x07' +
    '*\x02\x021\x10\x03\x02\x02\x0223\x07+\x02\x023\x12\x03\x02\x02\x0245\x07' +
    '?\x02\x025\x14\x03\x02\x02\x026:\x07$\x02\x0279\n\x02\x02\x0287\x03\x02' +
    '\x02\x029<\x03\x02\x02\x02:8\x03\x02\x02\x02:;\x03\x02\x02\x02;=\x03\x02' +
    '\x02\x02<:\x03\x02\x02\x02=>\x07$\x02\x02>\x16\x03\x02\x02\x02?C\x07$' +
    '\x02\x02@B\n\x03\x02\x02A@\x03\x02\x02\x02BE\x03\x02\x02\x02CA\x03\x02' +
    '\x02\x02CD\x03\x02\x02\x02D\x18\x03\x02\x02\x02EC\x03\x02\x02\x02FH\n' +
    '\x03\x02\x02GF\x03\x02\x02\x02HK\x03\x02\x02\x02IG\x03\x02\x02\x02IJ\x03' +
    '\x02\x02\x02JL\x03\x02\x02\x02KI\x03\x02\x02\x02LM\x07$\x02\x02M\x1A\x03' +
    '\x02\x02\x02NR\t\x04\x02\x02OQ\t\x05\x02\x02PO\x03\x02\x02\x02QT\x03\x02' +
    '\x02\x02RP\x03\x02\x02\x02RS\x03\x02\x02\x02S\x1C\x03\x02\x02\x02TR\x03' +
    '\x02\x02\x02UW\t\x06\x02\x02VU\x03\x02\x02\x02WX\x03\x02\x02\x02XV\x03' +
    '\x02\x02\x02XY\x03\x02\x02\x02Y\x1E\x03\x02\x02\x02\b\x02:CIRX\x02';
  public static __ATN: ATN;
  public static get _ATN(): ATN {
    if (!SelectionAutoCompleteLexer.__ATN) {
      SelectionAutoCompleteLexer.__ATN = new ATNDeserializer().deserialize(
        Utils.toCharArray(SelectionAutoCompleteLexer._serializedATN),
      );
    }

    return SelectionAutoCompleteLexer.__ATN;
  }
}
