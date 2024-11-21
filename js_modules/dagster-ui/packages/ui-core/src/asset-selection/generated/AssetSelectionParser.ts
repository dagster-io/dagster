// Generated from /Users/briantu/repos/dagster/python_modules/dagster/dagster/_core/definitions/antlr_asset_selection/AssetSelection.g4 by ANTLR 4.9.0-SNAPSHOT

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

import {AssetSelectionListener} from './AssetSelectionListener';
import {AssetSelectionVisitor} from './AssetSelectionVisitor';

export class AssetSelectionParser extends Parser {
  public static readonly EQUAL = 1;
  public static readonly AND = 2;
  public static readonly OR = 3;
  public static readonly NOT = 4;
  public static readonly STAR = 5;
  public static readonly PLUS = 6;
  public static readonly COLON = 7;
  public static readonly LPAREN = 8;
  public static readonly RPAREN = 9;
  public static readonly COMMA = 10;
  public static readonly KEY = 11;
  public static readonly KEY_SUBSTRING = 12;
  public static readonly OWNER = 13;
  public static readonly GROUP = 14;
  public static readonly TAG = 15;
  public static readonly KIND = 16;
  public static readonly CODE_LOCATION = 17;
  public static readonly SINKS = 18;
  public static readonly ROOTS = 19;
  public static readonly QUOTED_STRING = 20;
  public static readonly UNQUOTED_STRING = 21;
  public static readonly WS = 22;
  public static readonly RULE_start = 0;
  public static readonly RULE_expr = 1;
  public static readonly RULE_traversalAllowedExpr = 2;
  public static readonly RULE_traversal = 3;
  public static readonly RULE_functionName = 4;
  public static readonly RULE_attributeExpr = 5;
  public static readonly RULE_value = 6;
  // tslint:disable:no-trailing-whitespace
  public static readonly ruleNames: string[] = [
    'start',
    'expr',
    'traversalAllowedExpr',
    'traversal',
    'functionName',
    'attributeExpr',
    'value',
  ];

  private static readonly _LITERAL_NAMES: Array<string | undefined> = [
    undefined,
    "'='",
    "'and'",
    "'or'",
    "'not'",
    "'*'",
    "'+'",
    "':'",
    "'('",
    "')'",
    "','",
    "'key'",
    "'key_substring'",
    "'owner'",
    "'group'",
    "'tag'",
    "'kind'",
    "'code_location'",
    "'sinks'",
    "'roots'",
  ];
  private static readonly _SYMBOLIC_NAMES: Array<string | undefined> = [
    undefined,
    'EQUAL',
    'AND',
    'OR',
    'NOT',
    'STAR',
    'PLUS',
    'COLON',
    'LPAREN',
    'RPAREN',
    'COMMA',
    'KEY',
    'KEY_SUBSTRING',
    'OWNER',
    'GROUP',
    'TAG',
    'KIND',
    'CODE_LOCATION',
    'SINKS',
    'ROOTS',
    'QUOTED_STRING',
    'UNQUOTED_STRING',
    'WS',
  ];
  public static readonly VOCABULARY: Vocabulary = new VocabularyImpl(
    AssetSelectionParser._LITERAL_NAMES,
    AssetSelectionParser._SYMBOLIC_NAMES,
    [],
  );

  // @Override
  // @NotNull
  public get vocabulary(): Vocabulary {
    return AssetSelectionParser.VOCABULARY;
  }
  // tslint:enable:no-trailing-whitespace

  // @Override
  public get grammarFileName(): string {
    return 'AssetSelection.g4';
  }

  // @Override
  public get ruleNames(): string[] {
    return AssetSelectionParser.ruleNames;
  }

  // @Override
  public get serializedATN(): string {
    return AssetSelectionParser._serializedATN;
  }

  protected createFailedPredicateException(
    predicate?: string,
    message?: string,
  ): FailedPredicateException {
    return new FailedPredicateException(this, predicate, message);
  }

  constructor(input: TokenStream) {
    super(input);
    this._interp = new ParserATNSimulator(AssetSelectionParser._ATN, this);
  }
  // @RuleVersion(0)
  public start(): StartContext {
    const _localctx: StartContext = new StartContext(this._ctx, this.state);
    this.enterRule(_localctx, 0, AssetSelectionParser.RULE_start);
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 14;
        this.expr(0);
        this.state = 15;
        this.match(AssetSelectionParser.EOF);
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
    this.enterRecursionRule(_localctx, 2, AssetSelectionParser.RULE_expr, _p);
    try {
      let _alt: number;
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 32;
        this._errHandler.sync(this);
        switch (this.interpreter.adaptivePredict(this._input, 0, this._ctx)) {
          case 1:
            {
              _localctx = new TraversalAllowedExpressionContext(_localctx);
              this._ctx = _localctx;
              _prevctx = _localctx;

              this.state = 18;
              this.traversalAllowedExpr();
            }
            break;

          case 2:
            {
              _localctx = new UpAndDownTraversalExpressionContext(_localctx);
              this._ctx = _localctx;
              _prevctx = _localctx;
              this.state = 19;
              this.traversal();
              this.state = 20;
              this.traversalAllowedExpr();
              this.state = 21;
              this.traversal();
            }
            break;

          case 3:
            {
              _localctx = new UpTraversalExpressionContext(_localctx);
              this._ctx = _localctx;
              _prevctx = _localctx;
              this.state = 23;
              this.traversal();
              this.state = 24;
              this.traversalAllowedExpr();
            }
            break;

          case 4:
            {
              _localctx = new DownTraversalExpressionContext(_localctx);
              this._ctx = _localctx;
              _prevctx = _localctx;
              this.state = 26;
              this.traversalAllowedExpr();
              this.state = 27;
              this.traversal();
            }
            break;

          case 5:
            {
              _localctx = new NotExpressionContext(_localctx);
              this._ctx = _localctx;
              _prevctx = _localctx;
              this.state = 29;
              this.match(AssetSelectionParser.NOT);
              this.state = 30;
              this.expr(4);
            }
            break;

          case 6:
            {
              _localctx = new AllExpressionContext(_localctx);
              this._ctx = _localctx;
              _prevctx = _localctx;
              this.state = 31;
              this.match(AssetSelectionParser.STAR);
            }
            break;
        }
        this._ctx._stop = this._input.tryLT(-1);
        this.state = 42;
        this._errHandler.sync(this);
        _alt = this.interpreter.adaptivePredict(this._input, 2, this._ctx);
        while (_alt !== 2 && _alt !== ATN.INVALID_ALT_NUMBER) {
          if (_alt === 1) {
            if (this._parseListeners != null) {
              this.triggerExitRuleEvent();
            }
            _prevctx = _localctx;
            {
              this.state = 40;
              this._errHandler.sync(this);
              switch (this.interpreter.adaptivePredict(this._input, 1, this._ctx)) {
                case 1:
                  {
                    _localctx = new AndExpressionContext(new ExprContext(_parentctx, _parentState));
                    this.pushNewRecursionContext(
                      _localctx,
                      _startState,
                      AssetSelectionParser.RULE_expr,
                    );
                    this.state = 34;
                    if (!this.precpred(this._ctx, 3)) {
                      throw this.createFailedPredicateException('this.precpred(this._ctx, 3)');
                    }
                    this.state = 35;
                    this.match(AssetSelectionParser.AND);
                    this.state = 36;
                    this.expr(4);
                  }
                  break;

                case 2:
                  {
                    _localctx = new OrExpressionContext(new ExprContext(_parentctx, _parentState));
                    this.pushNewRecursionContext(
                      _localctx,
                      _startState,
                      AssetSelectionParser.RULE_expr,
                    );
                    this.state = 37;
                    if (!this.precpred(this._ctx, 2)) {
                      throw this.createFailedPredicateException('this.precpred(this._ctx, 2)');
                    }
                    this.state = 38;
                    this.match(AssetSelectionParser.OR);
                    this.state = 39;
                    this.expr(3);
                  }
                  break;
              }
            }
          }
          this.state = 44;
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
    this.enterRule(_localctx, 4, AssetSelectionParser.RULE_traversalAllowedExpr);
    try {
      this.state = 55;
      this._errHandler.sync(this);
      switch (this._input.LA(1)) {
        case AssetSelectionParser.KEY:
        case AssetSelectionParser.KEY_SUBSTRING:
        case AssetSelectionParser.OWNER:
        case AssetSelectionParser.GROUP:
        case AssetSelectionParser.TAG:
        case AssetSelectionParser.KIND:
        case AssetSelectionParser.CODE_LOCATION:
          _localctx = new AttributeExpressionContext(_localctx);
          this.enterOuterAlt(_localctx, 1);
          {
            this.state = 45;
            this.attributeExpr();
          }
          break;
        case AssetSelectionParser.SINKS:
        case AssetSelectionParser.ROOTS:
          _localctx = new FunctionCallExpressionContext(_localctx);
          this.enterOuterAlt(_localctx, 2);
          {
            this.state = 46;
            this.functionName();
            this.state = 47;
            this.match(AssetSelectionParser.LPAREN);
            this.state = 48;
            this.expr(0);
            this.state = 49;
            this.match(AssetSelectionParser.RPAREN);
          }
          break;
        case AssetSelectionParser.LPAREN:
          _localctx = new ParenthesizedExpressionContext(_localctx);
          this.enterOuterAlt(_localctx, 3);
          {
            this.state = 51;
            this.match(AssetSelectionParser.LPAREN);
            this.state = 52;
            this.expr(0);
            this.state = 53;
            this.match(AssetSelectionParser.RPAREN);
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
  public traversal(): TraversalContext {
    const _localctx: TraversalContext = new TraversalContext(this._ctx, this.state);
    this.enterRule(_localctx, 6, AssetSelectionParser.RULE_traversal);
    try {
      let _alt: number;
      this.state = 63;
      this._errHandler.sync(this);
      switch (this._input.LA(1)) {
        case AssetSelectionParser.STAR:
          this.enterOuterAlt(_localctx, 1);
          {
            this.state = 57;
            this.match(AssetSelectionParser.STAR);
          }
          break;
        case AssetSelectionParser.PLUS:
          this.enterOuterAlt(_localctx, 2);
          {
            this.state = 59;
            this._errHandler.sync(this);
            _alt = 1;
            do {
              switch (_alt) {
                case 1:
                  {
                    {
                      this.state = 58;
                      this.match(AssetSelectionParser.PLUS);
                    }
                  }
                  break;
                default:
                  throw new NoViableAltException(this);
              }
              this.state = 61;
              this._errHandler.sync(this);
              _alt = this.interpreter.adaptivePredict(this._input, 4, this._ctx);
            } while (_alt !== 2 && _alt !== ATN.INVALID_ALT_NUMBER);
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
  public functionName(): FunctionNameContext {
    const _localctx: FunctionNameContext = new FunctionNameContext(this._ctx, this.state);
    this.enterRule(_localctx, 8, AssetSelectionParser.RULE_functionName);
    let _la: number;
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 65;
        _la = this._input.LA(1);
        if (!(_la === AssetSelectionParser.SINKS || _la === AssetSelectionParser.ROOTS)) {
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
    this.enterRule(_localctx, 10, AssetSelectionParser.RULE_attributeExpr);
    try {
      this.state = 92;
      this._errHandler.sync(this);
      switch (this._input.LA(1)) {
        case AssetSelectionParser.KEY:
          _localctx = new KeyExprContext(_localctx);
          this.enterOuterAlt(_localctx, 1);
          {
            this.state = 67;
            this.match(AssetSelectionParser.KEY);
            this.state = 68;
            this.match(AssetSelectionParser.COLON);
            this.state = 69;
            this.value();
          }
          break;
        case AssetSelectionParser.KEY_SUBSTRING:
          _localctx = new KeySubstringExprContext(_localctx);
          this.enterOuterAlt(_localctx, 2);
          {
            this.state = 70;
            this.match(AssetSelectionParser.KEY_SUBSTRING);
            this.state = 71;
            this.match(AssetSelectionParser.COLON);
            this.state = 72;
            this.value();
          }
          break;
        case AssetSelectionParser.TAG:
          _localctx = new TagAttributeExprContext(_localctx);
          this.enterOuterAlt(_localctx, 3);
          {
            this.state = 73;
            this.match(AssetSelectionParser.TAG);
            this.state = 74;
            this.match(AssetSelectionParser.COLON);
            this.state = 75;
            this.value();
            this.state = 78;
            this._errHandler.sync(this);
            switch (this.interpreter.adaptivePredict(this._input, 6, this._ctx)) {
              case 1:
                {
                  this.state = 76;
                  this.match(AssetSelectionParser.EQUAL);
                  this.state = 77;
                  this.value();
                }
                break;
            }
          }
          break;
        case AssetSelectionParser.OWNER:
          _localctx = new OwnerAttributeExprContext(_localctx);
          this.enterOuterAlt(_localctx, 4);
          {
            this.state = 80;
            this.match(AssetSelectionParser.OWNER);
            this.state = 81;
            this.match(AssetSelectionParser.COLON);
            this.state = 82;
            this.value();
          }
          break;
        case AssetSelectionParser.GROUP:
          _localctx = new GroupAttributeExprContext(_localctx);
          this.enterOuterAlt(_localctx, 5);
          {
            this.state = 83;
            this.match(AssetSelectionParser.GROUP);
            this.state = 84;
            this.match(AssetSelectionParser.COLON);
            this.state = 85;
            this.value();
          }
          break;
        case AssetSelectionParser.KIND:
          _localctx = new KindAttributeExprContext(_localctx);
          this.enterOuterAlt(_localctx, 6);
          {
            this.state = 86;
            this.match(AssetSelectionParser.KIND);
            this.state = 87;
            this.match(AssetSelectionParser.COLON);
            this.state = 88;
            this.value();
          }
          break;
        case AssetSelectionParser.CODE_LOCATION:
          _localctx = new CodeLocationAttributeExprContext(_localctx);
          this.enterOuterAlt(_localctx, 7);
          {
            this.state = 89;
            this.match(AssetSelectionParser.CODE_LOCATION);
            this.state = 90;
            this.match(AssetSelectionParser.COLON);
            this.state = 91;
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
    this.enterRule(_localctx, 12, AssetSelectionParser.RULE_value);
    let _la: number;
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 94;
        _la = this._input.LA(1);
        if (
          !(
            _la === AssetSelectionParser.QUOTED_STRING ||
            _la === AssetSelectionParser.UNQUOTED_STRING
          )
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
    '\x03\uC91D\uCABA\u058D\uAFBA\u4F53\u0607\uEA8B\uC241\x03\x18c\x04\x02' +
    '\t\x02\x04\x03\t\x03\x04\x04\t\x04\x04\x05\t\x05\x04\x06\t\x06\x04\x07' +
    '\t\x07\x04\b\t\b\x03\x02\x03\x02\x03\x02\x03\x03\x03\x03\x03\x03\x03\x03' +
    '\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03' +
    '\x03\x03\x03\x03\x05\x03#\n\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03' +
    '\x03\x03\x07\x03+\n\x03\f\x03\x0E\x03.\v\x03\x03\x04\x03\x04\x03\x04\x03' +
    '\x04\x03\x04\x03\x04\x03\x04\x03\x04\x03\x04\x03\x04\x05\x04:\n\x04\x03' +
    '\x05\x03\x05\x06\x05>\n\x05\r\x05\x0E\x05?\x05\x05B\n\x05\x03\x06\x03' +
    '\x06\x03\x07\x03\x07\x03\x07\x03\x07\x03\x07\x03\x07\x03\x07\x03\x07\x03' +
    '\x07\x03\x07\x03\x07\x05\x07Q\n\x07\x03\x07\x03\x07\x03\x07\x03\x07\x03' +
    '\x07\x03\x07\x03\x07\x03\x07\x03\x07\x03\x07\x03\x07\x03\x07\x05\x07_' +
    '\n\x07\x03\b\x03\b\x03\b\x02\x02\x03\x04\t\x02\x02\x04\x02\x06\x02\b\x02' +
    '\n\x02\f\x02\x0E\x02\x02\x04\x03\x02\x14\x15\x03\x02\x16\x17\x02m\x02' +
    '\x10\x03\x02\x02\x02\x04"\x03\x02\x02\x02\x069\x03\x02\x02\x02\bA\x03' +
    '\x02\x02\x02\nC\x03\x02\x02\x02\f^\x03\x02\x02\x02\x0E`\x03\x02\x02\x02' +
    '\x10\x11\x05\x04\x03\x02\x11\x12\x07\x02\x02\x03\x12\x03\x03\x02\x02\x02' +
    '\x13\x14\b\x03\x01\x02\x14#\x05\x06\x04\x02\x15\x16\x05\b\x05\x02\x16' +
    '\x17\x05\x06\x04\x02\x17\x18\x05\b\x05\x02\x18#\x03\x02\x02\x02\x19\x1A' +
    '\x05\b\x05\x02\x1A\x1B\x05\x06\x04\x02\x1B#\x03\x02\x02\x02\x1C\x1D\x05' +
    '\x06\x04\x02\x1D\x1E\x05\b\x05\x02\x1E#\x03\x02\x02\x02\x1F \x07\x06\x02' +
    '\x02 #\x05\x04\x03\x06!#\x07\x07\x02\x02"\x13\x03\x02\x02\x02"\x15\x03' +
    '\x02\x02\x02"\x19\x03\x02\x02\x02"\x1C\x03\x02\x02\x02"\x1F\x03\x02' +
    '\x02\x02"!\x03\x02\x02\x02#,\x03\x02\x02\x02$%\f\x05\x02\x02%&\x07\x04' +
    "\x02\x02&+\x05\x04\x03\x06'(\f\x04\x02\x02()\x07\x05\x02\x02)+\x05\x04" +
    "\x03\x05*$\x03\x02\x02\x02*'\x03\x02\x02\x02+.\x03\x02\x02\x02,*\x03" +
    '\x02\x02\x02,-\x03\x02\x02\x02-\x05\x03\x02\x02\x02.,\x03\x02\x02\x02' +
    '/:\x05\f\x07\x0201\x05\n\x06\x0212\x07\n\x02\x0223\x05\x04\x03\x0234\x07' +
    '\v\x02\x024:\x03\x02\x02\x0256\x07\n\x02\x0267\x05\x04\x03\x0278\x07\v' +
    '\x02\x028:\x03\x02\x02\x029/\x03\x02\x02\x0290\x03\x02\x02\x0295\x03\x02' +
    '\x02\x02:\x07\x03\x02\x02\x02;B\x07\x07\x02\x02<>\x07\b\x02\x02=<\x03' +
    '\x02\x02\x02>?\x03\x02\x02\x02?=\x03\x02\x02\x02?@\x03\x02\x02\x02@B\x03' +
    '\x02\x02\x02A;\x03\x02\x02\x02A=\x03\x02\x02\x02B\t\x03\x02\x02\x02CD' +
    '\t\x02\x02\x02D\v\x03\x02\x02\x02EF\x07\r\x02\x02FG\x07\t\x02\x02G_\x05' +
    '\x0E\b\x02HI\x07\x0E\x02\x02IJ\x07\t\x02\x02J_\x05\x0E\b\x02KL\x07\x11' +
    '\x02\x02LM\x07\t\x02\x02MP\x05\x0E\b\x02NO\x07\x03\x02\x02OQ\x05\x0E\b' +
    '\x02PN\x03\x02\x02\x02PQ\x03\x02\x02\x02Q_\x03\x02\x02\x02RS\x07\x0F\x02' +
    '\x02ST\x07\t\x02\x02T_\x05\x0E\b\x02UV\x07\x10\x02\x02VW\x07\t\x02\x02' +
    'W_\x05\x0E\b\x02XY\x07\x12\x02\x02YZ\x07\t\x02\x02Z_\x05\x0E\b\x02[\\' +
    '\x07\x13\x02\x02\\]\x07\t\x02\x02]_\x05\x0E\b\x02^E\x03\x02\x02\x02^H' +
    '\x03\x02\x02\x02^K\x03\x02\x02\x02^R\x03\x02\x02\x02^U\x03\x02\x02\x02' +
    '^X\x03\x02\x02\x02^[\x03\x02\x02\x02_\r\x03\x02\x02\x02`a\t\x03\x02\x02' +
    'a\x0F\x03\x02\x02\x02\n"*,9?AP^';
  public static __ATN: ATN;
  public static get _ATN(): ATN {
    if (!AssetSelectionParser.__ATN) {
      AssetSelectionParser.__ATN = new ATNDeserializer().deserialize(
        Utils.toCharArray(AssetSelectionParser._serializedATN),
      );
    }

    return AssetSelectionParser.__ATN;
  }
}

export class StartContext extends ParserRuleContext {
  public expr(): ExprContext {
    return this.getRuleContext(0, ExprContext);
  }
  public EOF(): TerminalNode {
    return this.getToken(AssetSelectionParser.EOF, 0);
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return AssetSelectionParser.RULE_start;
  }
  // @Override
  public enterRule(listener: AssetSelectionListener): void {
    if (listener.enterStart) {
      listener.enterStart(this);
    }
  }
  // @Override
  public exitRule(listener: AssetSelectionListener): void {
    if (listener.exitStart) {
      listener.exitStart(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AssetSelectionVisitor<Result>): Result {
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
    return AssetSelectionParser.RULE_expr;
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
  public enterRule(listener: AssetSelectionListener): void {
    if (listener.enterTraversalAllowedExpression) {
      listener.enterTraversalAllowedExpression(this);
    }
  }
  // @Override
  public exitRule(listener: AssetSelectionListener): void {
    if (listener.exitTraversalAllowedExpression) {
      listener.exitTraversalAllowedExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AssetSelectionVisitor<Result>): Result {
    if (visitor.visitTraversalAllowedExpression) {
      return visitor.visitTraversalAllowedExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class UpAndDownTraversalExpressionContext extends ExprContext {
  public traversal(): TraversalContext[];
  public traversal(i: number): TraversalContext;
  public traversal(i?: number): TraversalContext | TraversalContext[] {
    if (i === undefined) {
      return this.getRuleContexts(TraversalContext);
    } else {
      return this.getRuleContext(i, TraversalContext);
    }
  }
  public traversalAllowedExpr(): TraversalAllowedExprContext {
    return this.getRuleContext(0, TraversalAllowedExprContext);
  }
  constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: AssetSelectionListener): void {
    if (listener.enterUpAndDownTraversalExpression) {
      listener.enterUpAndDownTraversalExpression(this);
    }
  }
  // @Override
  public exitRule(listener: AssetSelectionListener): void {
    if (listener.exitUpAndDownTraversalExpression) {
      listener.exitUpAndDownTraversalExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AssetSelectionVisitor<Result>): Result {
    if (visitor.visitUpAndDownTraversalExpression) {
      return visitor.visitUpAndDownTraversalExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class UpTraversalExpressionContext extends ExprContext {
  public traversal(): TraversalContext {
    return this.getRuleContext(0, TraversalContext);
  }
  public traversalAllowedExpr(): TraversalAllowedExprContext {
    return this.getRuleContext(0, TraversalAllowedExprContext);
  }
  constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: AssetSelectionListener): void {
    if (listener.enterUpTraversalExpression) {
      listener.enterUpTraversalExpression(this);
    }
  }
  // @Override
  public exitRule(listener: AssetSelectionListener): void {
    if (listener.exitUpTraversalExpression) {
      listener.exitUpTraversalExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AssetSelectionVisitor<Result>): Result {
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
  public traversal(): TraversalContext {
    return this.getRuleContext(0, TraversalContext);
  }
  constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: AssetSelectionListener): void {
    if (listener.enterDownTraversalExpression) {
      listener.enterDownTraversalExpression(this);
    }
  }
  // @Override
  public exitRule(listener: AssetSelectionListener): void {
    if (listener.exitDownTraversalExpression) {
      listener.exitDownTraversalExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AssetSelectionVisitor<Result>): Result {
    if (visitor.visitDownTraversalExpression) {
      return visitor.visitDownTraversalExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class NotExpressionContext extends ExprContext {
  public NOT(): TerminalNode {
    return this.getToken(AssetSelectionParser.NOT, 0);
  }
  public expr(): ExprContext {
    return this.getRuleContext(0, ExprContext);
  }
  constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: AssetSelectionListener): void {
    if (listener.enterNotExpression) {
      listener.enterNotExpression(this);
    }
  }
  // @Override
  public exitRule(listener: AssetSelectionListener): void {
    if (listener.exitNotExpression) {
      listener.exitNotExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AssetSelectionVisitor<Result>): Result {
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
    return this.getToken(AssetSelectionParser.AND, 0);
  }
  constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: AssetSelectionListener): void {
    if (listener.enterAndExpression) {
      listener.enterAndExpression(this);
    }
  }
  // @Override
  public exitRule(listener: AssetSelectionListener): void {
    if (listener.exitAndExpression) {
      listener.exitAndExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AssetSelectionVisitor<Result>): Result {
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
    return this.getToken(AssetSelectionParser.OR, 0);
  }
  constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: AssetSelectionListener): void {
    if (listener.enterOrExpression) {
      listener.enterOrExpression(this);
    }
  }
  // @Override
  public exitRule(listener: AssetSelectionListener): void {
    if (listener.exitOrExpression) {
      listener.exitOrExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AssetSelectionVisitor<Result>): Result {
    if (visitor.visitOrExpression) {
      return visitor.visitOrExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class AllExpressionContext extends ExprContext {
  public STAR(): TerminalNode {
    return this.getToken(AssetSelectionParser.STAR, 0);
  }
  constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: AssetSelectionListener): void {
    if (listener.enterAllExpression) {
      listener.enterAllExpression(this);
    }
  }
  // @Override
  public exitRule(listener: AssetSelectionListener): void {
    if (listener.exitAllExpression) {
      listener.exitAllExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AssetSelectionVisitor<Result>): Result {
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
    return AssetSelectionParser.RULE_traversalAllowedExpr;
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
  public enterRule(listener: AssetSelectionListener): void {
    if (listener.enterAttributeExpression) {
      listener.enterAttributeExpression(this);
    }
  }
  // @Override
  public exitRule(listener: AssetSelectionListener): void {
    if (listener.exitAttributeExpression) {
      listener.exitAttributeExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AssetSelectionVisitor<Result>): Result {
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
    return this.getToken(AssetSelectionParser.LPAREN, 0);
  }
  public expr(): ExprContext {
    return this.getRuleContext(0, ExprContext);
  }
  public RPAREN(): TerminalNode {
    return this.getToken(AssetSelectionParser.RPAREN, 0);
  }
  constructor(ctx: TraversalAllowedExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: AssetSelectionListener): void {
    if (listener.enterFunctionCallExpression) {
      listener.enterFunctionCallExpression(this);
    }
  }
  // @Override
  public exitRule(listener: AssetSelectionListener): void {
    if (listener.exitFunctionCallExpression) {
      listener.exitFunctionCallExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AssetSelectionVisitor<Result>): Result {
    if (visitor.visitFunctionCallExpression) {
      return visitor.visitFunctionCallExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class ParenthesizedExpressionContext extends TraversalAllowedExprContext {
  public LPAREN(): TerminalNode {
    return this.getToken(AssetSelectionParser.LPAREN, 0);
  }
  public expr(): ExprContext {
    return this.getRuleContext(0, ExprContext);
  }
  public RPAREN(): TerminalNode {
    return this.getToken(AssetSelectionParser.RPAREN, 0);
  }
  constructor(ctx: TraversalAllowedExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: AssetSelectionListener): void {
    if (listener.enterParenthesizedExpression) {
      listener.enterParenthesizedExpression(this);
    }
  }
  // @Override
  public exitRule(listener: AssetSelectionListener): void {
    if (listener.exitParenthesizedExpression) {
      listener.exitParenthesizedExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AssetSelectionVisitor<Result>): Result {
    if (visitor.visitParenthesizedExpression) {
      return visitor.visitParenthesizedExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class TraversalContext extends ParserRuleContext {
  public STAR(): TerminalNode | undefined {
    return this.tryGetToken(AssetSelectionParser.STAR, 0);
  }
  public PLUS(): TerminalNode[];
  public PLUS(i: number): TerminalNode;
  public PLUS(i?: number): TerminalNode | TerminalNode[] {
    if (i === undefined) {
      return this.getTokens(AssetSelectionParser.PLUS);
    } else {
      return this.getToken(AssetSelectionParser.PLUS, i);
    }
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return AssetSelectionParser.RULE_traversal;
  }
  // @Override
  public enterRule(listener: AssetSelectionListener): void {
    if (listener.enterTraversal) {
      listener.enterTraversal(this);
    }
  }
  // @Override
  public exitRule(listener: AssetSelectionListener): void {
    if (listener.exitTraversal) {
      listener.exitTraversal(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AssetSelectionVisitor<Result>): Result {
    if (visitor.visitTraversal) {
      return visitor.visitTraversal(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class FunctionNameContext extends ParserRuleContext {
  public SINKS(): TerminalNode | undefined {
    return this.tryGetToken(AssetSelectionParser.SINKS, 0);
  }
  public ROOTS(): TerminalNode | undefined {
    return this.tryGetToken(AssetSelectionParser.ROOTS, 0);
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return AssetSelectionParser.RULE_functionName;
  }
  // @Override
  public enterRule(listener: AssetSelectionListener): void {
    if (listener.enterFunctionName) {
      listener.enterFunctionName(this);
    }
  }
  // @Override
  public exitRule(listener: AssetSelectionListener): void {
    if (listener.exitFunctionName) {
      listener.exitFunctionName(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AssetSelectionVisitor<Result>): Result {
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
    return AssetSelectionParser.RULE_attributeExpr;
  }
  public copyFrom(ctx: AttributeExprContext): void {
    super.copyFrom(ctx);
  }
}
export class KeyExprContext extends AttributeExprContext {
  public KEY(): TerminalNode {
    return this.getToken(AssetSelectionParser.KEY, 0);
  }
  public COLON(): TerminalNode {
    return this.getToken(AssetSelectionParser.COLON, 0);
  }
  public value(): ValueContext {
    return this.getRuleContext(0, ValueContext);
  }
  constructor(ctx: AttributeExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: AssetSelectionListener): void {
    if (listener.enterKeyExpr) {
      listener.enterKeyExpr(this);
    }
  }
  // @Override
  public exitRule(listener: AssetSelectionListener): void {
    if (listener.exitKeyExpr) {
      listener.exitKeyExpr(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AssetSelectionVisitor<Result>): Result {
    if (visitor.visitKeyExpr) {
      return visitor.visitKeyExpr(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class KeySubstringExprContext extends AttributeExprContext {
  public KEY_SUBSTRING(): TerminalNode {
    return this.getToken(AssetSelectionParser.KEY_SUBSTRING, 0);
  }
  public COLON(): TerminalNode {
    return this.getToken(AssetSelectionParser.COLON, 0);
  }
  public value(): ValueContext {
    return this.getRuleContext(0, ValueContext);
  }
  constructor(ctx: AttributeExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: AssetSelectionListener): void {
    if (listener.enterKeySubstringExpr) {
      listener.enterKeySubstringExpr(this);
    }
  }
  // @Override
  public exitRule(listener: AssetSelectionListener): void {
    if (listener.exitKeySubstringExpr) {
      listener.exitKeySubstringExpr(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AssetSelectionVisitor<Result>): Result {
    if (visitor.visitKeySubstringExpr) {
      return visitor.visitKeySubstringExpr(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class TagAttributeExprContext extends AttributeExprContext {
  public TAG(): TerminalNode {
    return this.getToken(AssetSelectionParser.TAG, 0);
  }
  public COLON(): TerminalNode {
    return this.getToken(AssetSelectionParser.COLON, 0);
  }
  public value(): ValueContext[];
  public value(i: number): ValueContext;
  public value(i?: number): ValueContext | ValueContext[] {
    if (i === undefined) {
      return this.getRuleContexts(ValueContext);
    } else {
      return this.getRuleContext(i, ValueContext);
    }
  }
  public EQUAL(): TerminalNode | undefined {
    return this.tryGetToken(AssetSelectionParser.EQUAL, 0);
  }
  constructor(ctx: AttributeExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: AssetSelectionListener): void {
    if (listener.enterTagAttributeExpr) {
      listener.enterTagAttributeExpr(this);
    }
  }
  // @Override
  public exitRule(listener: AssetSelectionListener): void {
    if (listener.exitTagAttributeExpr) {
      listener.exitTagAttributeExpr(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AssetSelectionVisitor<Result>): Result {
    if (visitor.visitTagAttributeExpr) {
      return visitor.visitTagAttributeExpr(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class OwnerAttributeExprContext extends AttributeExprContext {
  public OWNER(): TerminalNode {
    return this.getToken(AssetSelectionParser.OWNER, 0);
  }
  public COLON(): TerminalNode {
    return this.getToken(AssetSelectionParser.COLON, 0);
  }
  public value(): ValueContext {
    return this.getRuleContext(0, ValueContext);
  }
  constructor(ctx: AttributeExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: AssetSelectionListener): void {
    if (listener.enterOwnerAttributeExpr) {
      listener.enterOwnerAttributeExpr(this);
    }
  }
  // @Override
  public exitRule(listener: AssetSelectionListener): void {
    if (listener.exitOwnerAttributeExpr) {
      listener.exitOwnerAttributeExpr(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AssetSelectionVisitor<Result>): Result {
    if (visitor.visitOwnerAttributeExpr) {
      return visitor.visitOwnerAttributeExpr(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class GroupAttributeExprContext extends AttributeExprContext {
  public GROUP(): TerminalNode {
    return this.getToken(AssetSelectionParser.GROUP, 0);
  }
  public COLON(): TerminalNode {
    return this.getToken(AssetSelectionParser.COLON, 0);
  }
  public value(): ValueContext {
    return this.getRuleContext(0, ValueContext);
  }
  constructor(ctx: AttributeExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: AssetSelectionListener): void {
    if (listener.enterGroupAttributeExpr) {
      listener.enterGroupAttributeExpr(this);
    }
  }
  // @Override
  public exitRule(listener: AssetSelectionListener): void {
    if (listener.exitGroupAttributeExpr) {
      listener.exitGroupAttributeExpr(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AssetSelectionVisitor<Result>): Result {
    if (visitor.visitGroupAttributeExpr) {
      return visitor.visitGroupAttributeExpr(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class KindAttributeExprContext extends AttributeExprContext {
  public KIND(): TerminalNode {
    return this.getToken(AssetSelectionParser.KIND, 0);
  }
  public COLON(): TerminalNode {
    return this.getToken(AssetSelectionParser.COLON, 0);
  }
  public value(): ValueContext {
    return this.getRuleContext(0, ValueContext);
  }
  constructor(ctx: AttributeExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: AssetSelectionListener): void {
    if (listener.enterKindAttributeExpr) {
      listener.enterKindAttributeExpr(this);
    }
  }
  // @Override
  public exitRule(listener: AssetSelectionListener): void {
    if (listener.exitKindAttributeExpr) {
      listener.exitKindAttributeExpr(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AssetSelectionVisitor<Result>): Result {
    if (visitor.visitKindAttributeExpr) {
      return visitor.visitKindAttributeExpr(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class CodeLocationAttributeExprContext extends AttributeExprContext {
  public CODE_LOCATION(): TerminalNode {
    return this.getToken(AssetSelectionParser.CODE_LOCATION, 0);
  }
  public COLON(): TerminalNode {
    return this.getToken(AssetSelectionParser.COLON, 0);
  }
  public value(): ValueContext {
    return this.getRuleContext(0, ValueContext);
  }
  constructor(ctx: AttributeExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: AssetSelectionListener): void {
    if (listener.enterCodeLocationAttributeExpr) {
      listener.enterCodeLocationAttributeExpr(this);
    }
  }
  // @Override
  public exitRule(listener: AssetSelectionListener): void {
    if (listener.exitCodeLocationAttributeExpr) {
      listener.exitCodeLocationAttributeExpr(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AssetSelectionVisitor<Result>): Result {
    if (visitor.visitCodeLocationAttributeExpr) {
      return visitor.visitCodeLocationAttributeExpr(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class ValueContext extends ParserRuleContext {
  public QUOTED_STRING(): TerminalNode | undefined {
    return this.tryGetToken(AssetSelectionParser.QUOTED_STRING, 0);
  }
  public UNQUOTED_STRING(): TerminalNode | undefined {
    return this.tryGetToken(AssetSelectionParser.UNQUOTED_STRING, 0);
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return AssetSelectionParser.RULE_value;
  }
  // @Override
  public enterRule(listener: AssetSelectionListener): void {
    if (listener.enterValue) {
      listener.enterValue(this);
    }
  }
  // @Override
  public exitRule(listener: AssetSelectionListener): void {
    if (listener.exitValue) {
      listener.exitValue(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AssetSelectionVisitor<Result>): Result {
    if (visitor.visitValue) {
      return visitor.visitValue(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
