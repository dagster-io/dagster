// Generated from /Users/marcosalazar/code/dagster/js_modules/dagster-ui/packages/ui-core/src/run-selection/RunSelection.g4 by ANTLR 4.9.0-SNAPSHOT

import {FailedPredicateException} from 'antlr4ts/FailedPredicateException';
import {NoViableAltException} from 'antlr4ts/NoViableAltException';
import {Parser} from 'antlr4ts/Parser';
import {ParserRuleContext} from 'antlr4ts/ParserRuleContext';
import {RecognitionException} from 'antlr4ts/RecognitionException';
import {RuleContext} from 'antlr4ts/RuleContext';
//import { RuleVersion } from "antlr4ts/RuleVersion";
import {Token} from 'antlr4ts/Token';
import {TokenStream} from 'antlr4ts/TokenStream';
import {Vocabulary} from 'antlr4ts/Vocabulary';
import {VocabularyImpl} from 'antlr4ts/VocabularyImpl';
import {ATN} from 'antlr4ts/atn/ATN';
import {ATNDeserializer} from 'antlr4ts/atn/ATNDeserializer';
import {ParserATNSimulator} from 'antlr4ts/atn/ParserATNSimulator';
import * as Utils from 'antlr4ts/misc/Utils';
import {TerminalNode} from 'antlr4ts/tree/TerminalNode';

import {RunSelectionListener} from './RunSelectionListener';
import {RunSelectionVisitor} from './RunSelectionVisitor';

export class RunSelectionParser extends Parser {
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
  public static readonly STATUS = 12;
  public static readonly SINKS = 13;
  public static readonly ROOTS = 14;
  public static readonly QUOTED_STRING = 15;
  public static readonly UNQUOTED_STRING = 16;
  public static readonly WS = 17;
  public static readonly RULE_start = 0;
  public static readonly RULE_expr = 1;
  public static readonly RULE_traversalAllowedExpr = 2;
  public static readonly RULE_upTraversal = 3;
  public static readonly RULE_downTraversal = 4;
  public static readonly RULE_functionName = 5;
  public static readonly RULE_attributeExpr = 6;
  public static readonly RULE_value = 7;
  // tslint:disable:no-trailing-whitespace
  public static readonly ruleNames: string[] = [
    'start',
    'expr',
    'traversalAllowedExpr',
    'upTraversal',
    'downTraversal',
    'functionName',
    'attributeExpr',
    'value',
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
    'NAME_SUBSTRING',
    'STATUS',
    'SINKS',
    'ROOTS',
    'QUOTED_STRING',
    'UNQUOTED_STRING',
    'WS',
  ];
  public static readonly VOCABULARY: Vocabulary = new VocabularyImpl(
    RunSelectionParser._LITERAL_NAMES,
    RunSelectionParser._SYMBOLIC_NAMES,
    [],
  );

  // @Override
  // @NotNull
  public get vocabulary(): Vocabulary {
    return RunSelectionParser.VOCABULARY;
  }
  // tslint:enable:no-trailing-whitespace

  // @Override
  public get grammarFileName(): string {
    return 'RunSelection.g4';
  }

  // @Override
  public get ruleNames(): string[] {
    return RunSelectionParser.ruleNames;
  }

  // @Override
  public get serializedATN(): string {
    return RunSelectionParser._serializedATN;
  }

  protected createFailedPredicateException(
    predicate?: string,
    message?: string,
  ): FailedPredicateException {
    return new FailedPredicateException(this, predicate, message);
  }

  constructor(input: TokenStream) {
    super(input);
    this._interp = new ParserATNSimulator(RunSelectionParser._ATN, this);
  }
  // @RuleVersion(0)
  public start(): StartContext {
    const _localctx: StartContext = new StartContext(this._ctx, this.state);
    this.enterRule(_localctx, 0, RunSelectionParser.RULE_start);
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 16;
        this.expr(0);
        this.state = 17;
        this.match(RunSelectionParser.EOF);
      }
    } catch (re) {
      if (re instanceof RecognitionException) {
        _localctx.exception = re;
        this._errHandler.reportError(this, re);
        this._errHandler.recover(this, re);
      } else {
        throw re;
      }
    } finally {
      this.exitRule();
    }
    return _localctx;
  }

  public expr(): ExprContext;
  public expr(_p: number): ExprContext;
  // @RuleVersion(0)
  public expr(_p?: number): ExprContext {
    if (_p === undefined) {
      _p = 0;
    }

    const _parentctx: ParserRuleContext = this._ctx;
    const _parentState: number = this.state;
    let _localctx: ExprContext = new ExprContext(this._ctx, _parentState);
    let _prevctx: ExprContext = _localctx;
    const _startState: number = 2;
    this.enterRecursionRule(_localctx, 2, RunSelectionParser.RULE_expr, _p);
    try {
      let _alt: number;
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 34;
        this._errHandler.sync(this);
        switch (this.interpreter.adaptivePredict(this._input, 0, this._ctx)) {
          case 1:
            {
              _localctx = new TraversalAllowedExpressionContext(_localctx);
              this._ctx = _localctx;
              _prevctx = _localctx;

              this.state = 20;
              this.traversalAllowedExpr();
            }
            break;

          case 2:
            {
              _localctx = new UpAndDownTraversalExpressionContext(_localctx);
              this._ctx = _localctx;
              _prevctx = _localctx;
              this.state = 21;
              this.upTraversal();
              this.state = 22;
              this.traversalAllowedExpr();
              this.state = 23;
              this.downTraversal();
            }
            break;

          case 3:
            {
              _localctx = new UpTraversalExpressionContext(_localctx);
              this._ctx = _localctx;
              _prevctx = _localctx;
              this.state = 25;
              this.upTraversal();
              this.state = 26;
              this.traversalAllowedExpr();
            }
            break;

          case 4:
            {
              _localctx = new DownTraversalExpressionContext(_localctx);
              this._ctx = _localctx;
              _prevctx = _localctx;
              this.state = 28;
              this.traversalAllowedExpr();
              this.state = 29;
              this.downTraversal();
            }
            break;

          case 5:
            {
              _localctx = new NotExpressionContext(_localctx);
              this._ctx = _localctx;
              _prevctx = _localctx;
              this.state = 31;
              this.match(RunSelectionParser.NOT);
              this.state = 32;
              this.expr(4);
            }
            break;

          case 6:
            {
              _localctx = new AllExpressionContext(_localctx);
              this._ctx = _localctx;
              _prevctx = _localctx;
              this.state = 33;
              this.match(RunSelectionParser.STAR);
            }
            break;
        }
        this._ctx._stop = this._input.tryLT(-1);
        this.state = 44;
        this._errHandler.sync(this);
        _alt = this.interpreter.adaptivePredict(this._input, 2, this._ctx);
        while (_alt !== 2 && _alt !== ATN.INVALID_ALT_NUMBER) {
          if (_alt === 1) {
            if (this._parseListeners != null) {
              this.triggerExitRuleEvent();
            }
            _prevctx = _localctx;
            {
              this.state = 42;
              this._errHandler.sync(this);
              switch (this.interpreter.adaptivePredict(this._input, 1, this._ctx)) {
                case 1:
                  {
                    _localctx = new AndExpressionContext(new ExprContext(_parentctx, _parentState));
                    this.pushNewRecursionContext(
                      _localctx,
                      _startState,
                      RunSelectionParser.RULE_expr,
                    );
                    this.state = 36;
                    if (!this.precpred(this._ctx, 3)) {
                      throw this.createFailedPredicateException('this.precpred(this._ctx, 3)');
                    }
                    this.state = 37;
                    this.match(RunSelectionParser.AND);
                    this.state = 38;
                    this.expr(4);
                  }
                  break;

                case 2:
                  {
                    _localctx = new OrExpressionContext(new ExprContext(_parentctx, _parentState));
                    this.pushNewRecursionContext(
                      _localctx,
                      _startState,
                      RunSelectionParser.RULE_expr,
                    );
                    this.state = 39;
                    if (!this.precpred(this._ctx, 2)) {
                      throw this.createFailedPredicateException('this.precpred(this._ctx, 2)');
                    }
                    this.state = 40;
                    this.match(RunSelectionParser.OR);
                    this.state = 41;
                    this.expr(3);
                  }
                  break;
              }
            }
          }
          this.state = 46;
          this._errHandler.sync(this);
          _alt = this.interpreter.adaptivePredict(this._input, 2, this._ctx);
        }
      }
    } catch (re) {
      if (re instanceof RecognitionException) {
        _localctx.exception = re;
        this._errHandler.reportError(this, re);
        this._errHandler.recover(this, re);
      } else {
        throw re;
      }
    } finally {
      this.unrollRecursionContexts(_parentctx);
    }
    return _localctx;
  }
  // @RuleVersion(0)
  public traversalAllowedExpr(): TraversalAllowedExprContext {
    let _localctx: TraversalAllowedExprContext = new TraversalAllowedExprContext(
      this._ctx,
      this.state,
    );
    this.enterRule(_localctx, 4, RunSelectionParser.RULE_traversalAllowedExpr);
    try {
      this.state = 57;
      this._errHandler.sync(this);
      switch (this._input.LA(1)) {
        case RunSelectionParser.NAME:
        case RunSelectionParser.NAME_SUBSTRING:
        case RunSelectionParser.STATUS:
          _localctx = new AttributeExpressionContext(_localctx);
          this.enterOuterAlt(_localctx, 1);
          {
            this.state = 47;
            this.attributeExpr();
          }
          break;
        case RunSelectionParser.SINKS:
        case RunSelectionParser.ROOTS:
          _localctx = new FunctionCallExpressionContext(_localctx);
          this.enterOuterAlt(_localctx, 2);
          {
            this.state = 48;
            this.functionName();
            this.state = 49;
            this.match(RunSelectionParser.LPAREN);
            this.state = 50;
            this.expr(0);
            this.state = 51;
            this.match(RunSelectionParser.RPAREN);
          }
          break;
        case RunSelectionParser.LPAREN:
          _localctx = new ParenthesizedExpressionContext(_localctx);
          this.enterOuterAlt(_localctx, 3);
          {
            this.state = 53;
            this.match(RunSelectionParser.LPAREN);
            this.state = 54;
            this.expr(0);
            this.state = 55;
            this.match(RunSelectionParser.RPAREN);
          }
          break;
        default:
          throw new NoViableAltException(this);
      }
    } catch (re) {
      if (re instanceof RecognitionException) {
        _localctx.exception = re;
        this._errHandler.reportError(this, re);
        this._errHandler.recover(this, re);
      } else {
        throw re;
      }
    } finally {
      this.exitRule();
    }
    return _localctx;
  }
  // @RuleVersion(0)
  public upTraversal(): UpTraversalContext {
    const _localctx: UpTraversalContext = new UpTraversalContext(this._ctx, this.state);
    this.enterRule(_localctx, 6, RunSelectionParser.RULE_upTraversal);
    let _la: number;
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 60;
        this._errHandler.sync(this);
        _la = this._input.LA(1);
        if (_la === RunSelectionParser.DIGITS) {
          {
            this.state = 59;
            this.match(RunSelectionParser.DIGITS);
          }
        }

        this.state = 62;
        this.match(RunSelectionParser.PLUS);
      }
    } catch (re) {
      if (re instanceof RecognitionException) {
        _localctx.exception = re;
        this._errHandler.reportError(this, re);
        this._errHandler.recover(this, re);
      } else {
        throw re;
      }
    } finally {
      this.exitRule();
    }
    return _localctx;
  }
  // @RuleVersion(0)
  public downTraversal(): DownTraversalContext {
    const _localctx: DownTraversalContext = new DownTraversalContext(this._ctx, this.state);
    this.enterRule(_localctx, 8, RunSelectionParser.RULE_downTraversal);
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 64;
        this.match(RunSelectionParser.PLUS);
        this.state = 66;
        this._errHandler.sync(this);
        switch (this.interpreter.adaptivePredict(this._input, 5, this._ctx)) {
          case 1:
            {
              this.state = 65;
              this.match(RunSelectionParser.DIGITS);
            }
            break;
        }
      }
    } catch (re) {
      if (re instanceof RecognitionException) {
        _localctx.exception = re;
        this._errHandler.reportError(this, re);
        this._errHandler.recover(this, re);
      } else {
        throw re;
      }
    } finally {
      this.exitRule();
    }
    return _localctx;
  }
  // @RuleVersion(0)
  public functionName(): FunctionNameContext {
    const _localctx: FunctionNameContext = new FunctionNameContext(this._ctx, this.state);
    this.enterRule(_localctx, 10, RunSelectionParser.RULE_functionName);
    let _la: number;
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 68;
        _la = this._input.LA(1);
        if (!(_la === RunSelectionParser.SINKS || _la === RunSelectionParser.ROOTS)) {
          this._errHandler.recoverInline(this);
        } else {
          if (this._input.LA(1) === Token.EOF) {
            this.matchedEOF = true;
          }

          this._errHandler.reportMatch(this);
          this.consume();
        }
      }
    } catch (re) {
      if (re instanceof RecognitionException) {
        _localctx.exception = re;
        this._errHandler.reportError(this, re);
        this._errHandler.recover(this, re);
      } else {
        throw re;
      }
    } finally {
      this.exitRule();
    }
    return _localctx;
  }
  // @RuleVersion(0)
  public attributeExpr(): AttributeExprContext {
    let _localctx: AttributeExprContext = new AttributeExprContext(this._ctx, this.state);
    this.enterRule(_localctx, 12, RunSelectionParser.RULE_attributeExpr);
    try {
      this.state = 79;
      this._errHandler.sync(this);
      switch (this._input.LA(1)) {
        case RunSelectionParser.NAME:
          _localctx = new NameExprContext(_localctx);
          this.enterOuterAlt(_localctx, 1);
          {
            this.state = 70;
            this.match(RunSelectionParser.NAME);
            this.state = 71;
            this.match(RunSelectionParser.COLON);
            this.state = 72;
            this.value();
          }
          break;
        case RunSelectionParser.NAME_SUBSTRING:
          _localctx = new NameSubstringExprContext(_localctx);
          this.enterOuterAlt(_localctx, 2);
          {
            this.state = 73;
            this.match(RunSelectionParser.NAME_SUBSTRING);
            this.state = 74;
            this.match(RunSelectionParser.COLON);
            this.state = 75;
            this.value();
          }
          break;
        case RunSelectionParser.STATUS:
          _localctx = new StatusAttributeExprContext(_localctx);
          this.enterOuterAlt(_localctx, 3);
          {
            this.state = 76;
            this.match(RunSelectionParser.STATUS);
            this.state = 77;
            this.match(RunSelectionParser.COLON);
            this.state = 78;
            this.value();
          }
          break;
        default:
          throw new NoViableAltException(this);
      }
    } catch (re) {
      if (re instanceof RecognitionException) {
        _localctx.exception = re;
        this._errHandler.reportError(this, re);
        this._errHandler.recover(this, re);
      } else {
        throw re;
      }
    } finally {
      this.exitRule();
    }
    return _localctx;
  }
  // @RuleVersion(0)
  public value(): ValueContext {
    const _localctx: ValueContext = new ValueContext(this._ctx, this.state);
    this.enterRule(_localctx, 14, RunSelectionParser.RULE_value);
    let _la: number;
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 81;
        _la = this._input.LA(1);
        if (
          !(_la === RunSelectionParser.QUOTED_STRING || _la === RunSelectionParser.UNQUOTED_STRING)
        ) {
          this._errHandler.recoverInline(this);
        } else {
          if (this._input.LA(1) === Token.EOF) {
            this.matchedEOF = true;
          }

          this._errHandler.reportMatch(this);
          this.consume();
        }
      }
    } catch (re) {
      if (re instanceof RecognitionException) {
        _localctx.exception = re;
        this._errHandler.reportError(this, re);
        this._errHandler.recover(this, re);
      } else {
        throw re;
      }
    } finally {
      this.exitRule();
    }
    return _localctx;
  }

  public sempred(_localctx: RuleContext, ruleIndex: number, predIndex: number): boolean {
    switch (ruleIndex) {
      case 1:
        return this.expr_sempred(_localctx as ExprContext, predIndex);
    }
    return true;
  }
  private expr_sempred(_localctx: ExprContext, predIndex: number): boolean {
    switch (predIndex) {
      case 0:
        return this.precpred(this._ctx, 3);

      case 1:
        return this.precpred(this._ctx, 2);
    }
    return true;
  }

  public static readonly _serializedATN: string =
    '\x03\uC91D\uCABA\u058D\uAFBA\u4F53\u0607\uEA8B\uC241\x03\x13V\x04\x02' +
    '\t\x02\x04\x03\t\x03\x04\x04\t\x04\x04\x05\t\x05\x04\x06\t\x06\x04\x07' +
    '\t\x07\x04\b\t\b\x04\t\t\t\x03\x02\x03\x02\x03\x02\x03\x03\x03\x03\x03' +
    '\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03' +
    '\x03\x03\x03\x03\x03\x03\x03\x05\x03%\n\x03\x03\x03\x03\x03\x03\x03\x03' +
    '\x03\x03\x03\x03\x03\x07\x03-\n\x03\f\x03\x0E\x030\v\x03\x03\x04\x03\x04' +
    '\x03\x04\x03\x04\x03\x04\x03\x04\x03\x04\x03\x04\x03\x04\x03\x04\x05\x04' +
    '<\n\x04\x03\x05\x05\x05?\n\x05\x03\x05\x03\x05\x03\x06\x03\x06\x05\x06' +
    'E\n\x06\x03\x07\x03\x07\x03\b\x03\b\x03\b\x03\b\x03\b\x03\b\x03\b\x03' +
    '\b\x03\b\x05\bR\n\b\x03\t\x03\t\x03\t\x02\x02\x03\x04\n\x02\x02\x04\x02' +
    '\x06\x02\b\x02\n\x02\f\x02\x0E\x02\x10\x02\x02\x04\x03\x02\x0F\x10\x03' +
    '\x02\x11\x12\x02Z\x02\x12\x03\x02\x02\x02\x04$\x03\x02\x02\x02\x06;\x03' +
    '\x02\x02\x02\b>\x03\x02\x02\x02\nB\x03\x02\x02\x02\fF\x03\x02\x02\x02' +
    '\x0EQ\x03\x02\x02\x02\x10S\x03\x02\x02\x02\x12\x13\x05\x04\x03\x02\x13' +
    '\x14\x07\x02\x02\x03\x14\x03\x03\x02\x02\x02\x15\x16\b\x03\x01\x02\x16' +
    '%\x05\x06\x04\x02\x17\x18\x05\b\x05\x02\x18\x19\x05\x06\x04\x02\x19\x1A' +
    '\x05\n\x06\x02\x1A%\x03\x02\x02\x02\x1B\x1C\x05\b\x05\x02\x1C\x1D\x05' +
    '\x06\x04\x02\x1D%\x03\x02\x02\x02\x1E\x1F\x05\x06\x04\x02\x1F \x05\n\x06' +
    '\x02 %\x03\x02\x02\x02!"\x07\x05\x02\x02"%\x05\x04\x03\x06#%\x07\x06' +
    '\x02\x02$\x15\x03\x02\x02\x02$\x17\x03\x02\x02\x02$\x1B\x03\x02\x02\x02' +
    '$\x1E\x03\x02\x02\x02$!\x03\x02\x02\x02$#\x03\x02\x02\x02%.\x03\x02\x02' +
    "\x02&'\f\x05\x02\x02'(\x07\x03\x02\x02(-\x05\x04\x03\x06)*\f\x04\x02" +
    '\x02*+\x07\x04\x02\x02+-\x05\x04\x03\x05,&\x03\x02\x02\x02,)\x03\x02\x02' +
    '\x02-0\x03\x02\x02\x02.,\x03\x02\x02\x02./\x03\x02\x02\x02/\x05\x03\x02' +
    '\x02\x020.\x03\x02\x02\x021<\x05\x0E\b\x0223\x05\f\x07\x0234\x07\n\x02' +
    '\x0245\x05\x04\x03\x0256\x07\v\x02\x026<\x03\x02\x02\x0278\x07\n\x02\x02' +
    '89\x05\x04\x03\x029:\x07\v\x02\x02:<\x03\x02\x02\x02;1\x03\x02\x02\x02' +
    ';2\x03\x02\x02\x02;7\x03\x02\x02\x02<\x07\x03\x02\x02\x02=?\x07\b\x02' +
    '\x02>=\x03\x02\x02\x02>?\x03\x02\x02\x02?@\x03\x02\x02\x02@A\x07\x07\x02' +
    '\x02A\t\x03\x02\x02\x02BD\x07\x07\x02\x02CE\x07\b\x02\x02DC\x03\x02\x02' +
    '\x02DE\x03\x02\x02\x02E\v\x03\x02\x02\x02FG\t\x02\x02\x02G\r\x03\x02\x02' +
    '\x02HI\x07\f\x02\x02IJ\x07\t\x02\x02JR\x05\x10\t\x02KL\x07\r\x02\x02L' +
    'M\x07\t\x02\x02MR\x05\x10\t\x02NO\x07\x0E\x02\x02OP\x07\t\x02\x02PR\x05' +
    '\x10\t\x02QH\x03\x02\x02\x02QK\x03\x02\x02\x02QN\x03\x02\x02\x02R\x0F' +
    '\x03\x02\x02\x02ST\t\x03\x02\x02T\x11\x03\x02\x02\x02\t$,.;>DQ';
  public static __ATN: ATN;
  public static get _ATN(): ATN {
    if (!RunSelectionParser.__ATN) {
      RunSelectionParser.__ATN = new ATNDeserializer().deserialize(
        Utils.toCharArray(RunSelectionParser._serializedATN),
      );
    }

    return RunSelectionParser.__ATN;
  }
}

export class StartContext extends ParserRuleContext {
  public expr(): ExprContext {
    return this.getRuleContext(0, ExprContext);
  }
  public EOF(): TerminalNode {
    return this.getToken(RunSelectionParser.EOF, 0);
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return RunSelectionParser.RULE_start;
  }
  // @Override
  public enterRule(listener: RunSelectionListener): void {
    if (listener.enterStart) {
      listener.enterStart(this);
    }
  }
  // @Override
  public exitRule(listener: RunSelectionListener): void {
    if (listener.exitStart) {
      listener.exitStart(this);
    }
  }
  // @Override
  public accept<Result>(visitor: RunSelectionVisitor<Result>): Result {
    if (visitor.visitStart) {
      return visitor.visitStart(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class ExprContext extends ParserRuleContext {
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return RunSelectionParser.RULE_expr;
  }
  public copyFrom(ctx: ExprContext): void {
    super.copyFrom(ctx);
  }
}
export class TraversalAllowedExpressionContext extends ExprContext {
  public traversalAllowedExpr(): TraversalAllowedExprContext {
    return this.getRuleContext(0, TraversalAllowedExprContext);
  }
  constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: RunSelectionListener): void {
    if (listener.enterTraversalAllowedExpression) {
      listener.enterTraversalAllowedExpression(this);
    }
  }
  // @Override
  public exitRule(listener: RunSelectionListener): void {
    if (listener.exitTraversalAllowedExpression) {
      listener.exitTraversalAllowedExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: RunSelectionVisitor<Result>): Result {
    if (visitor.visitTraversalAllowedExpression) {
      return visitor.visitTraversalAllowedExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class UpAndDownTraversalExpressionContext extends ExprContext {
  public upTraversal(): UpTraversalContext {
    return this.getRuleContext(0, UpTraversalContext);
  }
  public traversalAllowedExpr(): TraversalAllowedExprContext {
    return this.getRuleContext(0, TraversalAllowedExprContext);
  }
  public downTraversal(): DownTraversalContext {
    return this.getRuleContext(0, DownTraversalContext);
  }
  constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: RunSelectionListener): void {
    if (listener.enterUpAndDownTraversalExpression) {
      listener.enterUpAndDownTraversalExpression(this);
    }
  }
  // @Override
  public exitRule(listener: RunSelectionListener): void {
    if (listener.exitUpAndDownTraversalExpression) {
      listener.exitUpAndDownTraversalExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: RunSelectionVisitor<Result>): Result {
    if (visitor.visitUpAndDownTraversalExpression) {
      return visitor.visitUpAndDownTraversalExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class UpTraversalExpressionContext extends ExprContext {
  public upTraversal(): UpTraversalContext {
    return this.getRuleContext(0, UpTraversalContext);
  }
  public traversalAllowedExpr(): TraversalAllowedExprContext {
    return this.getRuleContext(0, TraversalAllowedExprContext);
  }
  constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: RunSelectionListener): void {
    if (listener.enterUpTraversalExpression) {
      listener.enterUpTraversalExpression(this);
    }
  }
  // @Override
  public exitRule(listener: RunSelectionListener): void {
    if (listener.exitUpTraversalExpression) {
      listener.exitUpTraversalExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: RunSelectionVisitor<Result>): Result {
    if (visitor.visitUpTraversalExpression) {
      return visitor.visitUpTraversalExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class DownTraversalExpressionContext extends ExprContext {
  public traversalAllowedExpr(): TraversalAllowedExprContext {
    return this.getRuleContext(0, TraversalAllowedExprContext);
  }
  public downTraversal(): DownTraversalContext {
    return this.getRuleContext(0, DownTraversalContext);
  }
  constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: RunSelectionListener): void {
    if (listener.enterDownTraversalExpression) {
      listener.enterDownTraversalExpression(this);
    }
  }
  // @Override
  public exitRule(listener: RunSelectionListener): void {
    if (listener.exitDownTraversalExpression) {
      listener.exitDownTraversalExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: RunSelectionVisitor<Result>): Result {
    if (visitor.visitDownTraversalExpression) {
      return visitor.visitDownTraversalExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class NotExpressionContext extends ExprContext {
  public NOT(): TerminalNode {
    return this.getToken(RunSelectionParser.NOT, 0);
  }
  public expr(): ExprContext {
    return this.getRuleContext(0, ExprContext);
  }
  constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: RunSelectionListener): void {
    if (listener.enterNotExpression) {
      listener.enterNotExpression(this);
    }
  }
  // @Override
  public exitRule(listener: RunSelectionListener): void {
    if (listener.exitNotExpression) {
      listener.exitNotExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: RunSelectionVisitor<Result>): Result {
    if (visitor.visitNotExpression) {
      return visitor.visitNotExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class AndExpressionContext extends ExprContext {
  public expr(): ExprContext[];
  public expr(i: number): ExprContext;
  public expr(i?: number): ExprContext | ExprContext[] {
    if (i === undefined) {
      return this.getRuleContexts(ExprContext);
    } else {
      return this.getRuleContext(i, ExprContext);
    }
  }
  public AND(): TerminalNode {
    return this.getToken(RunSelectionParser.AND, 0);
  }
  constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: RunSelectionListener): void {
    if (listener.enterAndExpression) {
      listener.enterAndExpression(this);
    }
  }
  // @Override
  public exitRule(listener: RunSelectionListener): void {
    if (listener.exitAndExpression) {
      listener.exitAndExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: RunSelectionVisitor<Result>): Result {
    if (visitor.visitAndExpression) {
      return visitor.visitAndExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class OrExpressionContext extends ExprContext {
  public expr(): ExprContext[];
  public expr(i: number): ExprContext;
  public expr(i?: number): ExprContext | ExprContext[] {
    if (i === undefined) {
      return this.getRuleContexts(ExprContext);
    } else {
      return this.getRuleContext(i, ExprContext);
    }
  }
  public OR(): TerminalNode {
    return this.getToken(RunSelectionParser.OR, 0);
  }
  constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: RunSelectionListener): void {
    if (listener.enterOrExpression) {
      listener.enterOrExpression(this);
    }
  }
  // @Override
  public exitRule(listener: RunSelectionListener): void {
    if (listener.exitOrExpression) {
      listener.exitOrExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: RunSelectionVisitor<Result>): Result {
    if (visitor.visitOrExpression) {
      return visitor.visitOrExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class AllExpressionContext extends ExprContext {
  public STAR(): TerminalNode {
    return this.getToken(RunSelectionParser.STAR, 0);
  }
  constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: RunSelectionListener): void {
    if (listener.enterAllExpression) {
      listener.enterAllExpression(this);
    }
  }
  // @Override
  public exitRule(listener: RunSelectionListener): void {
    if (listener.exitAllExpression) {
      listener.exitAllExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: RunSelectionVisitor<Result>): Result {
    if (visitor.visitAllExpression) {
      return visitor.visitAllExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class TraversalAllowedExprContext extends ParserRuleContext {
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return RunSelectionParser.RULE_traversalAllowedExpr;
  }
  public copyFrom(ctx: TraversalAllowedExprContext): void {
    super.copyFrom(ctx);
  }
}
export class AttributeExpressionContext extends TraversalAllowedExprContext {
  public attributeExpr(): AttributeExprContext {
    return this.getRuleContext(0, AttributeExprContext);
  }
  constructor(ctx: TraversalAllowedExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: RunSelectionListener): void {
    if (listener.enterAttributeExpression) {
      listener.enterAttributeExpression(this);
    }
  }
  // @Override
  public exitRule(listener: RunSelectionListener): void {
    if (listener.exitAttributeExpression) {
      listener.exitAttributeExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: RunSelectionVisitor<Result>): Result {
    if (visitor.visitAttributeExpression) {
      return visitor.visitAttributeExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class FunctionCallExpressionContext extends TraversalAllowedExprContext {
  public functionName(): FunctionNameContext {
    return this.getRuleContext(0, FunctionNameContext);
  }
  public LPAREN(): TerminalNode {
    return this.getToken(RunSelectionParser.LPAREN, 0);
  }
  public expr(): ExprContext {
    return this.getRuleContext(0, ExprContext);
  }
  public RPAREN(): TerminalNode {
    return this.getToken(RunSelectionParser.RPAREN, 0);
  }
  constructor(ctx: TraversalAllowedExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: RunSelectionListener): void {
    if (listener.enterFunctionCallExpression) {
      listener.enterFunctionCallExpression(this);
    }
  }
  // @Override
  public exitRule(listener: RunSelectionListener): void {
    if (listener.exitFunctionCallExpression) {
      listener.exitFunctionCallExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: RunSelectionVisitor<Result>): Result {
    if (visitor.visitFunctionCallExpression) {
      return visitor.visitFunctionCallExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class ParenthesizedExpressionContext extends TraversalAllowedExprContext {
  public LPAREN(): TerminalNode {
    return this.getToken(RunSelectionParser.LPAREN, 0);
  }
  public expr(): ExprContext {
    return this.getRuleContext(0, ExprContext);
  }
  public RPAREN(): TerminalNode {
    return this.getToken(RunSelectionParser.RPAREN, 0);
  }
  constructor(ctx: TraversalAllowedExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: RunSelectionListener): void {
    if (listener.enterParenthesizedExpression) {
      listener.enterParenthesizedExpression(this);
    }
  }
  // @Override
  public exitRule(listener: RunSelectionListener): void {
    if (listener.exitParenthesizedExpression) {
      listener.exitParenthesizedExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: RunSelectionVisitor<Result>): Result {
    if (visitor.visitParenthesizedExpression) {
      return visitor.visitParenthesizedExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class UpTraversalContext extends ParserRuleContext {
  public PLUS(): TerminalNode {
    return this.getToken(RunSelectionParser.PLUS, 0);
  }
  public DIGITS(): TerminalNode | undefined {
    return this.tryGetToken(RunSelectionParser.DIGITS, 0);
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return RunSelectionParser.RULE_upTraversal;
  }
  // @Override
  public enterRule(listener: RunSelectionListener): void {
    if (listener.enterUpTraversal) {
      listener.enterUpTraversal(this);
    }
  }
  // @Override
  public exitRule(listener: RunSelectionListener): void {
    if (listener.exitUpTraversal) {
      listener.exitUpTraversal(this);
    }
  }
  // @Override
  public accept<Result>(visitor: RunSelectionVisitor<Result>): Result {
    if (visitor.visitUpTraversal) {
      return visitor.visitUpTraversal(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class DownTraversalContext extends ParserRuleContext {
  public PLUS(): TerminalNode {
    return this.getToken(RunSelectionParser.PLUS, 0);
  }
  public DIGITS(): TerminalNode | undefined {
    return this.tryGetToken(RunSelectionParser.DIGITS, 0);
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return RunSelectionParser.RULE_downTraversal;
  }
  // @Override
  public enterRule(listener: RunSelectionListener): void {
    if (listener.enterDownTraversal) {
      listener.enterDownTraversal(this);
    }
  }
  // @Override
  public exitRule(listener: RunSelectionListener): void {
    if (listener.exitDownTraversal) {
      listener.exitDownTraversal(this);
    }
  }
  // @Override
  public accept<Result>(visitor: RunSelectionVisitor<Result>): Result {
    if (visitor.visitDownTraversal) {
      return visitor.visitDownTraversal(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class FunctionNameContext extends ParserRuleContext {
  public SINKS(): TerminalNode | undefined {
    return this.tryGetToken(RunSelectionParser.SINKS, 0);
  }
  public ROOTS(): TerminalNode | undefined {
    return this.tryGetToken(RunSelectionParser.ROOTS, 0);
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return RunSelectionParser.RULE_functionName;
  }
  // @Override
  public enterRule(listener: RunSelectionListener): void {
    if (listener.enterFunctionName) {
      listener.enterFunctionName(this);
    }
  }
  // @Override
  public exitRule(listener: RunSelectionListener): void {
    if (listener.exitFunctionName) {
      listener.exitFunctionName(this);
    }
  }
  // @Override
  public accept<Result>(visitor: RunSelectionVisitor<Result>): Result {
    if (visitor.visitFunctionName) {
      return visitor.visitFunctionName(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class AttributeExprContext extends ParserRuleContext {
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return RunSelectionParser.RULE_attributeExpr;
  }
  public copyFrom(ctx: AttributeExprContext): void {
    super.copyFrom(ctx);
  }
}
export class NameExprContext extends AttributeExprContext {
  public NAME(): TerminalNode {
    return this.getToken(RunSelectionParser.NAME, 0);
  }
  public COLON(): TerminalNode {
    return this.getToken(RunSelectionParser.COLON, 0);
  }
  public value(): ValueContext {
    return this.getRuleContext(0, ValueContext);
  }
  constructor(ctx: AttributeExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: RunSelectionListener): void {
    if (listener.enterNameExpr) {
      listener.enterNameExpr(this);
    }
  }
  // @Override
  public exitRule(listener: RunSelectionListener): void {
    if (listener.exitNameExpr) {
      listener.exitNameExpr(this);
    }
  }
  // @Override
  public accept<Result>(visitor: RunSelectionVisitor<Result>): Result {
    if (visitor.visitNameExpr) {
      return visitor.visitNameExpr(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class NameSubstringExprContext extends AttributeExprContext {
  public NAME_SUBSTRING(): TerminalNode {
    return this.getToken(RunSelectionParser.NAME_SUBSTRING, 0);
  }
  public COLON(): TerminalNode {
    return this.getToken(RunSelectionParser.COLON, 0);
  }
  public value(): ValueContext {
    return this.getRuleContext(0, ValueContext);
  }
  constructor(ctx: AttributeExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: RunSelectionListener): void {
    if (listener.enterNameSubstringExpr) {
      listener.enterNameSubstringExpr(this);
    }
  }
  // @Override
  public exitRule(listener: RunSelectionListener): void {
    if (listener.exitNameSubstringExpr) {
      listener.exitNameSubstringExpr(this);
    }
  }
  // @Override
  public accept<Result>(visitor: RunSelectionVisitor<Result>): Result {
    if (visitor.visitNameSubstringExpr) {
      return visitor.visitNameSubstringExpr(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class StatusAttributeExprContext extends AttributeExprContext {
  public STATUS(): TerminalNode {
    return this.getToken(RunSelectionParser.STATUS, 0);
  }
  public COLON(): TerminalNode {
    return this.getToken(RunSelectionParser.COLON, 0);
  }
  public value(): ValueContext {
    return this.getRuleContext(0, ValueContext);
  }
  constructor(ctx: AttributeExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: RunSelectionListener): void {
    if (listener.enterStatusAttributeExpr) {
      listener.enterStatusAttributeExpr(this);
    }
  }
  // @Override
  public exitRule(listener: RunSelectionListener): void {
    if (listener.exitStatusAttributeExpr) {
      listener.exitStatusAttributeExpr(this);
    }
  }
  // @Override
  public accept<Result>(visitor: RunSelectionVisitor<Result>): Result {
    if (visitor.visitStatusAttributeExpr) {
      return visitor.visitStatusAttributeExpr(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class ValueContext extends ParserRuleContext {
  public QUOTED_STRING(): TerminalNode | undefined {
    return this.tryGetToken(RunSelectionParser.QUOTED_STRING, 0);
  }
  public UNQUOTED_STRING(): TerminalNode | undefined {
    return this.tryGetToken(RunSelectionParser.UNQUOTED_STRING, 0);
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return RunSelectionParser.RULE_value;
  }
  // @Override
  public enterRule(listener: RunSelectionListener): void {
    if (listener.enterValue) {
      listener.enterValue(this);
    }
  }
  // @Override
  public exitRule(listener: RunSelectionListener): void {
    if (listener.exitValue) {
      listener.exitValue(this);
    }
  }
  // @Override
  public accept<Result>(visitor: RunSelectionVisitor<Result>): Result {
    if (visitor.visitValue) {
      return visitor.visitValue(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
