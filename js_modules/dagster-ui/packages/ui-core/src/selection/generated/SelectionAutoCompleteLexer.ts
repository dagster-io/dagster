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
  public static readonly DIGITS = 6;
  public static readonly COLON = 7;
  public static readonly LPAREN = 8;
  public static readonly RPAREN = 9;
  public static readonly QUOTED_STRING = 10;
  public static readonly INCOMPLETE_LEFT_QUOTED_STRING = 11;
  public static readonly INCOMPLETE_RIGHT_QUOTED_STRING = 12;
  public static readonly EQUAL = 13;
  public static readonly IDENTIFIER = 14;
  public static readonly WS = 15;
  public static readonly COMMA = 16;

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
    'QUOTED_STRING',
    'INCOMPLETE_LEFT_QUOTED_STRING',
    'INCOMPLETE_RIGHT_QUOTED_STRING',
    'EQUAL',
    'IDENTIFIER',
    'WS',
    'COMMA',
  ];

  private static readonly _LITERAL_NAMES: Array<string | undefined> = [
    undefined,
    undefined,
    undefined,
    undefined,
    "'*'",
    "'+'",
    undefined,
    "':'",
    "'('",
    "')'",
    undefined,
    undefined,
    undefined,
    "'='",
    undefined,
    undefined,
    "','",
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
    'QUOTED_STRING',
    'INCOMPLETE_LEFT_QUOTED_STRING',
    'INCOMPLETE_RIGHT_QUOTED_STRING',
    'EQUAL',
    'IDENTIFIER',
    'WS',
    'COMMA',
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
    '\x03\uC91D\uCABA\u058D\uAFBA\u4F53\u0607\uEA8B\uC241\x02\x12p\b\x01\x04' +
    '\x02\t\x02\x04\x03\t\x03\x04\x04\t\x04\x04\x05\t\x05\x04\x06\t\x06\x04' +
    '\x07\t\x07\x04\b\t\b\x04\t\t\t\x04\n\t\n\x04\v\t\v\x04\f\t\f\x04\r\t\r' +
    '\x04\x0E\t\x0E\x04\x0F\t\x0F\x04\x10\t\x10\x04\x11\t\x11\x03\x02\x03\x02' +
    '\x03\x02\x03\x02\x03\x02\x03\x02\x05\x02*\n\x02\x03\x03\x03\x03\x03\x03' +
    '\x03\x03\x05\x030\n\x03\x03\x04\x03\x04\x03\x04\x03\x04\x03\x04\x03\x04' +
    '\x05\x048\n\x04\x03\x05\x03\x05\x03\x06\x03\x06\x03\x07\x06\x07?\n\x07' +
    '\r\x07\x0E\x07@\x03\b\x03\b\x03\t\x03\t\x03\n\x03\n\x03\v\x03\v\x07\v' +
    'K\n\v\f\v\x0E\vN\v\v\x03\v\x03\v\x03\f\x03\f\x07\fT\n\f\f\f\x0E\fW\v\f' +
    '\x03\r\x07\rZ\n\r\f\r\x0E\r]\v\r\x03\r\x03\r\x03\x0E\x03\x0E\x03\x0F\x03' +
    '\x0F\x07\x0Fe\n\x0F\f\x0F\x0E\x0Fh\v\x0F\x03\x10\x06\x10k\n\x10\r\x10' +
    '\x0E\x10l\x03\x11\x03\x11\x02\x02\x02\x12\x03\x02\x03\x05\x02\x04\x07' +
    '\x02\x05\t\x02\x06\v\x02\x07\r\x02\b\x0F\x02\t\x11\x02\n\x13\x02\v\x15' +
    '\x02\f\x17\x02\r\x19\x02\x0E\x1B\x02\x0F\x1D\x02\x10\x1F\x02\x11!\x02' +
    '\x12\x03\x02\b\x03\x022;\x06\x02\f\f\x0F\x0F$$^^\t\x02\f\f\x0F\x0F$$*' +
    '+<<??^^\x07\x02,,2;C\\aac|\x07\x02,,1;C\\aac|\x05\x02\v\f\x0F\x0F""' +
    '\x02x\x02\x03\x03\x02\x02\x02\x02\x05\x03\x02\x02\x02\x02\x07\x03\x02' +
    '\x02\x02\x02\t\x03\x02\x02\x02\x02\v\x03\x02\x02\x02\x02\r\x03\x02\x02' +
    '\x02\x02\x0F\x03\x02\x02\x02\x02\x11\x03\x02\x02\x02\x02\x13\x03\x02\x02' +
    '\x02\x02\x15\x03\x02\x02\x02\x02\x17\x03\x02\x02\x02\x02\x19\x03\x02\x02' +
    '\x02\x02\x1B\x03\x02\x02\x02\x02\x1D\x03\x02\x02\x02\x02\x1F\x03\x02\x02' +
    '\x02\x02!\x03\x02\x02\x02\x03)\x03\x02\x02\x02\x05/\x03\x02\x02\x02\x07' +
    '7\x03\x02\x02\x02\t9\x03\x02\x02\x02\v;\x03\x02\x02\x02\r>\x03\x02\x02' +
    '\x02\x0FB\x03\x02\x02\x02\x11D\x03\x02\x02\x02\x13F\x03\x02\x02\x02\x15' +
    'H\x03\x02\x02\x02\x17Q\x03\x02\x02\x02\x19[\x03\x02\x02\x02\x1B`\x03\x02' +
    '\x02\x02\x1Db\x03\x02\x02\x02\x1Fj\x03\x02\x02\x02!n\x03\x02\x02\x02#' +
    "$\x07c\x02\x02$%\x07p\x02\x02%*\x07f\x02\x02&'\x07C\x02\x02'(\x07P\x02" +
    '\x02(*\x07F\x02\x02)#\x03\x02\x02\x02)&\x03\x02\x02\x02*\x04\x03\x02\x02' +
    '\x02+,\x07q\x02\x02,0\x07t\x02\x02-.\x07Q\x02\x02.0\x07T\x02\x02/+\x03' +
    '\x02\x02\x02/-\x03\x02\x02\x020\x06\x03\x02\x02\x0212\x07p\x02\x0223\x07' +
    'q\x02\x0238\x07v\x02\x0245\x07P\x02\x0256\x07Q\x02\x0268\x07V\x02\x02' +
    '71\x03\x02\x02\x0274\x03\x02\x02\x028\b\x03\x02\x02\x029:\x07,\x02\x02' +
    ':\n\x03\x02\x02\x02;<\x07-\x02\x02<\f\x03\x02\x02\x02=?\t\x02\x02\x02' +
    '>=\x03\x02\x02\x02?@\x03\x02\x02\x02@>\x03\x02\x02\x02@A\x03\x02\x02\x02' +
    'A\x0E\x03\x02\x02\x02BC\x07<\x02\x02C\x10\x03\x02\x02\x02DE\x07*\x02\x02' +
    'E\x12\x03\x02\x02\x02FG\x07+\x02\x02G\x14\x03\x02\x02\x02HL\x07$\x02\x02' +
    'IK\n\x03\x02\x02JI\x03\x02\x02\x02KN\x03\x02\x02\x02LJ\x03\x02\x02\x02' +
    'LM\x03\x02\x02\x02MO\x03\x02\x02\x02NL\x03\x02\x02\x02OP\x07$\x02\x02' +
    'P\x16\x03\x02\x02\x02QU\x07$\x02\x02RT\n\x04\x02\x02SR\x03\x02\x02\x02' +
    'TW\x03\x02\x02\x02US\x03\x02\x02\x02UV\x03\x02\x02\x02V\x18\x03\x02\x02' +
    '\x02WU\x03\x02\x02\x02XZ\n\x04\x02\x02YX\x03\x02\x02\x02Z]\x03\x02\x02' +
    '\x02[Y\x03\x02\x02\x02[\\\x03\x02\x02\x02\\^\x03\x02\x02\x02][\x03\x02' +
    '\x02\x02^_\x07$\x02\x02_\x1A\x03\x02\x02\x02`a\x07?\x02\x02a\x1C\x03\x02' +
    '\x02\x02bf\t\x05\x02\x02ce\t\x06\x02\x02dc\x03\x02\x02\x02eh\x03\x02\x02' +
    '\x02fd\x03\x02\x02\x02fg\x03\x02\x02\x02g\x1E\x03\x02\x02\x02hf\x03\x02' +
    '\x02\x02ik\t\x07\x02\x02ji\x03\x02\x02\x02kl\x03\x02\x02\x02lj\x03\x02' +
    '\x02\x02lm\x03\x02\x02\x02m \x03\x02\x02\x02no\x07.\x02\x02o"\x03\x02' +
    '\x02\x02\f\x02)/7@LU[fl\x02';
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
