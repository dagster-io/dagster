// Generated from /Users/salazarm/code/dagster/js_modules/dagster-ui/packages/ui-core/src/job-selection/JobSelection.g4 by ANTLR 4.9.0-SNAPSHOT

import {CharStream} from 'antlr4ts/CharStream';
import {Lexer} from 'antlr4ts/Lexer';
import {Vocabulary} from 'antlr4ts/Vocabulary';
import {VocabularyImpl} from 'antlr4ts/VocabularyImpl';
import {ATN} from 'antlr4ts/atn/ATN';
import {ATNDeserializer} from 'antlr4ts/atn/ATNDeserializer';
import {LexerATNSimulator} from 'antlr4ts/atn/LexerATNSimulator';
import * as Utils from 'antlr4ts/misc/Utils';

export class JobSelectionLexer extends Lexer {
  public static readonly AND = 1;
  public static readonly OR = 2;
  public static readonly NOT = 3;
  public static readonly COLON = 4;
  public static readonly STAR = 5;
  public static readonly LPAREN = 6;
  public static readonly RPAREN = 7;
  public static readonly NAME = 8;
  public static readonly CODE_LOCATION = 9;
  public static readonly QUOTED_STRING = 10;
  public static readonly UNQUOTED_STRING = 11;
  public static readonly UNQUOTED_WILDCARD_STRING = 12;
  public static readonly WS = 13;

  // tslint:disable:no-trailing-whitespace
  public static readonly channelNames: string[] = ['DEFAULT_TOKEN_CHANNEL', 'HIDDEN'];

  // tslint:disable:no-trailing-whitespace
  public static readonly modeNames: string[] = ['DEFAULT_MODE'];

  public static readonly ruleNames: string[] = [
    'AND',
    'OR',
    'NOT',
    'COLON',
    'STAR',
    'LPAREN',
    'RPAREN',
    'NAME',
    'CODE_LOCATION',
    'QUOTED_STRING',
    'UNQUOTED_STRING',
    'UNQUOTED_WILDCARD_STRING',
    'WS',
  ];

  private static readonly _LITERAL_NAMES: Array<string | undefined> = [
    undefined,
    undefined,
    undefined,
    undefined,
    "':'",
    "'*'",
    "'('",
    "')'",
    "'name'",
    "'code_location'",
  ];
  private static readonly _SYMBOLIC_NAMES: Array<string | undefined> = [
    undefined,
    'AND',
    'OR',
    'NOT',
    'COLON',
    'STAR',
    'LPAREN',
    'RPAREN',
    'NAME',
    'CODE_LOCATION',
    'QUOTED_STRING',
    'UNQUOTED_STRING',
    'UNQUOTED_WILDCARD_STRING',
    'WS',
  ];
  public static readonly VOCABULARY: Vocabulary = new VocabularyImpl(
    JobSelectionLexer._LITERAL_NAMES,
    JobSelectionLexer._SYMBOLIC_NAMES,
    [],
  );

  // @Override
  // @NotNull
  public get vocabulary(): Vocabulary {
    return JobSelectionLexer.VOCABULARY;
  }
  // tslint:enable:no-trailing-whitespace

  constructor(input: CharStream) {
    super(input);
    this._interp = new LexerATNSimulator(JobSelectionLexer._ATN, this);
  }

  // @Override
  public get grammarFileName(): string {
    return 'JobSelection.g4';
  }

  // @Override
  public get ruleNames(): string[] {
    return JobSelectionLexer.ruleNames;
  }

  // @Override
  public get serializedATN(): string {
    return JobSelectionLexer._serializedATN;
  }

  // @Override
  public get channelNames(): string[] {
    return JobSelectionLexer.channelNames;
  }

  // @Override
  public get modeNames(): string[] {
    return JobSelectionLexer.modeNames;
  }

  public static readonly _serializedATN: string =
    '\x03\uC91D\uCABA\u058D\uAFBA\u4F53\u0607\uEA8B\uC241\x02\x0Fl\b\x01\x04' +
    '\x02\t\x02\x04\x03\t\x03\x04\x04\t\x04\x04\x05\t\x05\x04\x06\t\x06\x04' +
    '\x07\t\x07\x04\b\t\b\x04\t\t\t\x04\n\t\n\x04\v\t\v\x04\f\t\f\x04\r\t\r' +
    '\x04\x0E\t\x0E\x03\x02\x03\x02\x03\x02\x03\x02\x03\x02\x03\x02\x05\x02' +
    '$\n\x02\x03\x03\x03\x03\x03\x03\x03\x03\x05\x03*\n\x03\x03\x04\x03\x04' +
    '\x03\x04\x03\x04\x03\x04\x03\x04\x05\x042\n\x04\x03\x05\x03\x05\x03\x06' +
    '\x03\x06\x03\x07\x03\x07\x03\b\x03\b\x03\t\x03\t\x03\t\x03\t\x03\t\x03' +
    '\n\x03\n\x03\n\x03\n\x03\n\x03\n\x03\n\x03\n\x03\n\x03\n\x03\n\x03\n\x03' +
    '\n\x03\n\x03\v\x03\v\x07\vQ\n\v\f\v\x0E\vT\v\v\x03\v\x03\v\x03\f\x03\f' +
    '\x07\fZ\n\f\f\f\x0E\f]\v\f\x03\r\x03\r\x07\ra\n\r\f\r\x0E\rd\v\r\x03\x0E' +
    '\x06\x0Eg\n\x0E\r\x0E\x0E\x0Eh\x03\x0E\x03\x0E\x02\x02\x02\x0F\x03\x02' +
    '\x03\x05\x02\x04\x07\x02\x05\t\x02\x06\v\x02\x07\r\x02\b\x0F\x02\t\x11' +
    '\x02\n\x13\x02\v\x15\x02\f\x17\x02\r\x19\x02\x0E\x1B\x02\x0F\x03\x02\b' +
    '\x06\x02\f\f\x0F\x0F$$^^\x05\x02C\\aac|\x06\x022;B\\aac|\x06\x02,,C\\' +
    'aac|\x07\x02,,2;B\\aac|\x05\x02\v\f\x0F\x0F""\x02r\x02\x03\x03\x02\x02' +
    '\x02\x02\x05\x03\x02\x02\x02\x02\x07\x03\x02\x02\x02\x02\t\x03\x02\x02' +
    '\x02\x02\v\x03\x02\x02\x02\x02\r\x03\x02\x02\x02\x02\x0F\x03\x02\x02\x02' +
    '\x02\x11\x03\x02\x02\x02\x02\x13\x03\x02\x02\x02\x02\x15\x03\x02\x02\x02' +
    '\x02\x17\x03\x02\x02\x02\x02\x19\x03\x02\x02\x02\x02\x1B\x03\x02\x02\x02' +
    '\x03#\x03\x02\x02\x02\x05)\x03\x02\x02\x02\x071\x03\x02\x02\x02\t3\x03' +
    '\x02\x02\x02\v5\x03\x02\x02\x02\r7\x03\x02\x02\x02\x0F9\x03\x02\x02\x02' +
    '\x11;\x03\x02\x02\x02\x13@\x03\x02\x02\x02\x15N\x03\x02\x02\x02\x17W\x03' +
    '\x02\x02\x02\x19^\x03\x02\x02\x02\x1Bf\x03\x02\x02\x02\x1D\x1E\x07c\x02' +
    '\x02\x1E\x1F\x07p\x02\x02\x1F$\x07f\x02\x02 !\x07C\x02\x02!"\x07P\x02' +
    '\x02"$\x07F\x02\x02#\x1D\x03\x02\x02\x02# \x03\x02\x02\x02$\x04\x03\x02' +
    "\x02\x02%&\x07q\x02\x02&*\x07t\x02\x02'(\x07Q\x02\x02(*\x07T\x02\x02" +
    ")%\x03\x02\x02\x02)'\x03\x02\x02\x02*\x06\x03\x02\x02\x02+,\x07p\x02" +
    '\x02,-\x07q\x02\x02-2\x07v\x02\x02./\x07P\x02\x02/0\x07Q\x02\x0202\x07' +
    'V\x02\x021+\x03\x02\x02\x021.\x03\x02\x02\x022\b\x03\x02\x02\x0234\x07' +
    '<\x02\x024\n\x03\x02\x02\x0256\x07,\x02\x026\f\x03\x02\x02\x0278\x07*' +
    '\x02\x028\x0E\x03\x02\x02\x029:\x07+\x02\x02:\x10\x03\x02\x02\x02;<\x07' +
    'p\x02\x02<=\x07c\x02\x02=>\x07o\x02\x02>?\x07g\x02\x02?\x12\x03\x02\x02' +
    '\x02@A\x07e\x02\x02AB\x07q\x02\x02BC\x07f\x02\x02CD\x07g\x02\x02DE\x07' +
    'a\x02\x02EF\x07n\x02\x02FG\x07q\x02\x02GH\x07e\x02\x02HI\x07c\x02\x02' +
    'IJ\x07v\x02\x02JK\x07k\x02\x02KL\x07q\x02\x02LM\x07p\x02\x02M\x14\x03' +
    '\x02\x02\x02NR\x07$\x02\x02OQ\n\x02\x02\x02PO\x03\x02\x02\x02QT\x03\x02' +
    '\x02\x02RP\x03\x02\x02\x02RS\x03\x02\x02\x02SU\x03\x02\x02\x02TR\x03\x02' +
    '\x02\x02UV\x07$\x02\x02V\x16\x03\x02\x02\x02W[\t\x03\x02\x02XZ\t\x04\x02' +
    '\x02YX\x03\x02\x02\x02Z]\x03\x02\x02\x02[Y\x03\x02\x02\x02[\\\x03\x02' +
    '\x02\x02\\\x18\x03\x02\x02\x02][\x03\x02\x02\x02^b\t\x05\x02\x02_a\t\x06' +
    '\x02\x02`_\x03\x02\x02\x02ad\x03\x02\x02\x02b`\x03\x02\x02\x02bc\x03\x02' +
    '\x02\x02c\x1A\x03\x02\x02\x02db\x03\x02\x02\x02eg\t\x07\x02\x02fe\x03' +
    '\x02\x02\x02gh\x03\x02\x02\x02hf\x03\x02\x02\x02hi\x03\x02\x02\x02ij\x03' +
    '\x02\x02\x02jk\b\x0E\x02\x02k\x1C\x03\x02\x02\x02\n\x02#)1R[bh\x03\b\x02' +
    '\x02';
  public static __ATN: ATN;
  public static get _ATN(): ATN {
    if (!JobSelectionLexer.__ATN) {
      JobSelectionLexer.__ATN = new ATNDeserializer().deserialize(
        Utils.toCharArray(JobSelectionLexer._serializedATN),
      );
    }

    return JobSelectionLexer.__ATN;
  }
}
