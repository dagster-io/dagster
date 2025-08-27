// Generated from /Users/salazarm/code/dagster/python_modules/dagster/dagster/_core/definitions/antlr_asset_selection/AssetSelection.g4 by ANTLR 4.9.0-SNAPSHOT

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
  public static readonly DIGITS = 7;
  public static readonly COLON = 8;
  public static readonly LPAREN = 9;
  public static readonly RPAREN = 10;
  public static readonly COMMA = 11;
  public static readonly KEY = 12;
  public static readonly OWNER = 13;
  public static readonly GROUP = 14;
  public static readonly TAG = 15;
  public static readonly KIND = 16;
  public static readonly CODE_LOCATION = 17;
  public static readonly STATUS = 18;
  public static readonly COLUMN = 19;
  public static readonly TABLE_NAME = 20;
  public static readonly COLUMN_TAG = 21;
  public static readonly CHANGED_IN_BRANCH = 22;
  public static readonly SINKS = 23;
  public static readonly ROOTS = 24;
  public static readonly QUOTED_STRING = 25;
  public static readonly UNQUOTED_STRING = 26;
  public static readonly UNQUOTED_WILDCARD_STRING = 27;
  public static readonly NULL_STRING = 28;
  public static readonly WS = 29;
  public static readonly RULE_start = 0;
  public static readonly RULE_expr = 1;
  public static readonly RULE_traversalAllowedExpr = 2;
  public static readonly RULE_upTraversal = 3;
  public static readonly RULE_downTraversal = 4;
  public static readonly RULE_functionName = 5;
  public static readonly RULE_attributeExpr = 6;
  public static readonly RULE_value = 7;
  public static readonly RULE_keyValue = 8;
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
    'keyValue',
  ];

  private static readonly _LITERAL_NAMES: Array<string | undefined> = [
    undefined,
    "'='",
    undefined,
    undefined,
    undefined,
    "'*'",
    "'+'",
    undefined,
    "':'",
    "'('",
    "')'",
    "','",
    "'key'",
    "'owner'",
    "'group'",
    "'tag'",
    "'kind'",
    "'code_location'",
    "'status'",
    "'column'",
    "'table_name'",
    "'column_tag'",
    "'changed_in_branch'",
    "'sinks'",
    "'roots'",
    undefined,
    undefined,
    undefined,
    "'<null>'",
  ];
  private static readonly _SYMBOLIC_NAMES: Array<string | undefined> = [
    undefined,
    'EQUAL',
    'AND',
    'OR',
    'NOT',
    'STAR',
    'PLUS',
    'DIGITS',
    'COLON',
    'LPAREN',
    'RPAREN',
    'COMMA',
    'KEY',
    'OWNER',
    'GROUP',
    'TAG',
    'KIND',
    'CODE_LOCATION',
    'STATUS',
    'COLUMN',
    'TABLE_NAME',
    'COLUMN_TAG',
    'CHANGED_IN_BRANCH',
    'SINKS',
    'ROOTS',
    'QUOTED_STRING',
    'UNQUOTED_STRING',
    'UNQUOTED_WILDCARD_STRING',
    'NULL_STRING',
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
        this.state = 18;
        this.expr(0);
        this.state = 19;
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
        this.state = 36;
        this._errHandler.sync(this);
        switch (this.interpreter.adaptivePredict(this._input, 0, this._ctx)) {
          case 1:
            {
              _localctx = new TraversalAllowedExpressionContext(_localctx);
              this._ctx = _localctx;
              _prevctx = _localctx;

              this.state = 22;
              this.traversalAllowedExpr();
            }
            break;

          case 2:
            {
              _localctx = new UpAndDownTraversalExpressionContext(_localctx);
              this._ctx = _localctx;
              _prevctx = _localctx;
              this.state = 23;
              this.upTraversal();
              this.state = 24;
              this.traversalAllowedExpr();
              this.state = 25;
              this.downTraversal();
            }
            break;

          case 3:
            {
              _localctx = new UpTraversalExpressionContext(_localctx);
              this._ctx = _localctx;
              _prevctx = _localctx;
              this.state = 27;
              this.upTraversal();
              this.state = 28;
              this.traversalAllowedExpr();
            }
            break;

          case 4:
            {
              _localctx = new DownTraversalExpressionContext(_localctx);
              this._ctx = _localctx;
              _prevctx = _localctx;
              this.state = 30;
              this.traversalAllowedExpr();
              this.state = 31;
              this.downTraversal();
            }
            break;

          case 5:
            {
              _localctx = new NotExpressionContext(_localctx);
              this._ctx = _localctx;
              _prevctx = _localctx;
              this.state = 33;
              this.match(AssetSelectionParser.NOT);
              this.state = 34;
              this.expr(4);
            }
            break;

          case 6:
            {
              _localctx = new AllExpressionContext(_localctx);
              this._ctx = _localctx;
              _prevctx = _localctx;
              this.state = 35;
              this.match(AssetSelectionParser.STAR);
            }
            break;
        }
        this._ctx._stop = this._input.tryLT(-1);
        this.state = 46;
        this._errHandler.sync(this);
        _alt = this.interpreter.adaptivePredict(this._input, 2, this._ctx);
        while (_alt !== 2 && _alt !== ATN.INVALID_ALT_NUMBER) {
          if (_alt === 1) {
            if (this._parseListeners != null) {
              this.triggerExitRuleEvent();
            }
            _prevctx = _localctx;
            {
              this.state = 44;
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
                    this.state = 38;
                    if (!this.precpred(this._ctx, 3)) {
                      throw this.createFailedPredicateException('this.precpred(this._ctx, 3)');
                    }
                    this.state = 39;
                    this.match(AssetSelectionParser.AND);
                    this.state = 40;
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
                    this.state = 41;
                    if (!this.precpred(this._ctx, 2)) {
                      throw this.createFailedPredicateException('this.precpred(this._ctx, 2)');
                    }
                    this.state = 42;
                    this.match(AssetSelectionParser.OR);
                    this.state = 43;
                    this.expr(3);
                  }
                  break;
              }
            }
          }
          this.state = 48;
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
      this.state = 59;
      this._errHandler.sync(this);
      switch (this._input.LA(1)) {
        case AssetSelectionParser.KEY:
        case AssetSelectionParser.OWNER:
        case AssetSelectionParser.GROUP:
        case AssetSelectionParser.TAG:
        case AssetSelectionParser.KIND:
        case AssetSelectionParser.CODE_LOCATION:
        case AssetSelectionParser.STATUS:
        case AssetSelectionParser.COLUMN:
        case AssetSelectionParser.TABLE_NAME:
        case AssetSelectionParser.COLUMN_TAG:
        case AssetSelectionParser.CHANGED_IN_BRANCH:
          _localctx = new AttributeExpressionContext(_localctx);
          this.enterOuterAlt(_localctx, 1);
          {
            this.state = 49;
            this.attributeExpr();
          }
          break;
        case AssetSelectionParser.SINKS:
        case AssetSelectionParser.ROOTS:
          _localctx = new FunctionCallExpressionContext(_localctx);
          this.enterOuterAlt(_localctx, 2);
          {
            this.state = 50;
            this.functionName();
            this.state = 51;
            this.match(AssetSelectionParser.LPAREN);
            this.state = 52;
            this.expr(0);
            this.state = 53;
            this.match(AssetSelectionParser.RPAREN);
          }
          break;
        case AssetSelectionParser.LPAREN:
          _localctx = new ParenthesizedExpressionContext(_localctx);
          this.enterOuterAlt(_localctx, 3);
          {
            this.state = 55;
            this.match(AssetSelectionParser.LPAREN);
            this.state = 56;
            this.expr(0);
            this.state = 57;
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
  public upTraversal(): UpTraversalContext {
    const _localctx: UpTraversalContext = new UpTraversalContext(this._ctx, this.state);
    this.enterRule(_localctx, 6, AssetSelectionParser.RULE_upTraversal);
    let _la: number;
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 62;
        this._errHandler.sync(this);
        _la = this._input.LA(1);
        if (_la === AssetSelectionParser.DIGITS) {
          {
            this.state = 61;
            this.match(AssetSelectionParser.DIGITS);
          }
        }

        this.state = 64;
        this.match(AssetSelectionParser.PLUS);
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
    this.enterRule(_localctx, 8, AssetSelectionParser.RULE_downTraversal);
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 66;
        this.match(AssetSelectionParser.PLUS);
        this.state = 68;
        this._errHandler.sync(this);
        switch (this.interpreter.adaptivePredict(this._input, 5, this._ctx)) {
          case 1:
            {
              this.state = 67;
              this.match(AssetSelectionParser.DIGITS);
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
    this.enterRule(_localctx, 10, AssetSelectionParser.RULE_functionName);
    let _la: number;
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 70;
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
    this.enterRule(_localctx, 12, AssetSelectionParser.RULE_attributeExpr);
    try {
      this.state = 113;
      this._errHandler.sync(this);
      switch (this._input.LA(1)) {
        case AssetSelectionParser.KEY:
          _localctx = new KeyExprContext(_localctx);
          this.enterOuterAlt(_localctx, 1);
          {
            this.state = 72;
            this.match(AssetSelectionParser.KEY);
            this.state = 73;
            this.match(AssetSelectionParser.COLON);
            this.state = 74;
            this.keyValue();
          }
          break;
        case AssetSelectionParser.TAG:
          _localctx = new TagAttributeExprContext(_localctx);
          this.enterOuterAlt(_localctx, 2);
          {
            this.state = 75;
            this.match(AssetSelectionParser.TAG);
            this.state = 76;
            this.match(AssetSelectionParser.COLON);
            this.state = 77;
            this.value();
            this.state = 80;
            this._errHandler.sync(this);
            switch (this.interpreter.adaptivePredict(this._input, 6, this._ctx)) {
              case 1:
                {
                  this.state = 78;
                  this.match(AssetSelectionParser.EQUAL);
                  this.state = 79;
                  this.value();
                }
                break;
            }
          }
          break;
        case AssetSelectionParser.OWNER:
          _localctx = new OwnerAttributeExprContext(_localctx);
          this.enterOuterAlt(_localctx, 3);
          {
            this.state = 82;
            this.match(AssetSelectionParser.OWNER);
            this.state = 83;
            this.match(AssetSelectionParser.COLON);
            this.state = 84;
            this.value();
          }
          break;
        case AssetSelectionParser.GROUP:
          _localctx = new GroupAttributeExprContext(_localctx);
          this.enterOuterAlt(_localctx, 4);
          {
            this.state = 85;
            this.match(AssetSelectionParser.GROUP);
            this.state = 86;
            this.match(AssetSelectionParser.COLON);
            this.state = 87;
            this.value();
          }
          break;
        case AssetSelectionParser.KIND:
          _localctx = new KindAttributeExprContext(_localctx);
          this.enterOuterAlt(_localctx, 5);
          {
            this.state = 88;
            this.match(AssetSelectionParser.KIND);
            this.state = 89;
            this.match(AssetSelectionParser.COLON);
            this.state = 90;
            this.value();
          }
          break;
        case AssetSelectionParser.STATUS:
          _localctx = new StatusAttributeExprContext(_localctx);
          this.enterOuterAlt(_localctx, 6);
          {
            this.state = 91;
            this.match(AssetSelectionParser.STATUS);
            this.state = 92;
            this.match(AssetSelectionParser.COLON);
            this.state = 93;
            this.value();
          }
          break;
        case AssetSelectionParser.COLUMN:
          _localctx = new ColumnAttributeExprContext(_localctx);
          this.enterOuterAlt(_localctx, 7);
          {
            this.state = 94;
            this.match(AssetSelectionParser.COLUMN);
            this.state = 95;
            this.match(AssetSelectionParser.COLON);
            this.state = 96;
            this.value();
          }
          break;
        case AssetSelectionParser.TABLE_NAME:
          _localctx = new TableNameAttributeExprContext(_localctx);
          this.enterOuterAlt(_localctx, 8);
          {
            this.state = 97;
            this.match(AssetSelectionParser.TABLE_NAME);
            this.state = 98;
            this.match(AssetSelectionParser.COLON);
            this.state = 99;
            this.value();
          }
          break;
        case AssetSelectionParser.COLUMN_TAG:
          _localctx = new ColumnTagAttributeExprContext(_localctx);
          this.enterOuterAlt(_localctx, 9);
          {
            this.state = 100;
            this.match(AssetSelectionParser.COLUMN_TAG);
            this.state = 101;
            this.match(AssetSelectionParser.COLON);
            this.state = 102;
            this.value();
            this.state = 105;
            this._errHandler.sync(this);
            switch (this.interpreter.adaptivePredict(this._input, 7, this._ctx)) {
              case 1:
                {
                  this.state = 103;
                  this.match(AssetSelectionParser.EQUAL);
                  this.state = 104;
                  this.value();
                }
                break;
            }
          }
          break;
        case AssetSelectionParser.CODE_LOCATION:
          _localctx = new CodeLocationAttributeExprContext(_localctx);
          this.enterOuterAlt(_localctx, 10);
          {
            this.state = 107;
            this.match(AssetSelectionParser.CODE_LOCATION);
            this.state = 108;
            this.match(AssetSelectionParser.COLON);
            this.state = 109;
            this.value();
          }
          break;
        case AssetSelectionParser.CHANGED_IN_BRANCH:
          _localctx = new ChangedInBranchAttributeExprContext(_localctx);
          this.enterOuterAlt(_localctx, 11);
          {
            this.state = 110;
            this.match(AssetSelectionParser.CHANGED_IN_BRANCH);
            this.state = 111;
            this.match(AssetSelectionParser.COLON);
            this.state = 112;
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
    this.enterRule(_localctx, 14, AssetSelectionParser.RULE_value);
    let _la: number;
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 115;
        _la = this._input.LA(1);
        if (
          !(
            (_la & ~0x1f) === 0 &&
            ((1 << _la) &
              ((1 << AssetSelectionParser.QUOTED_STRING) |
                (1 << AssetSelectionParser.UNQUOTED_STRING) |
                (1 << AssetSelectionParser.NULL_STRING))) !==
              0
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
  // @RuleVersion(0)
  public keyValue(): KeyValueContext {
    const _localctx: KeyValueContext = new KeyValueContext(this._ctx, this.state);
    this.enterRule(_localctx, 16, AssetSelectionParser.RULE_keyValue);
    let _la: number;
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 117;
        _la = this._input.LA(1);
        if (
          !(
            (_la & ~0x1f) === 0 &&
            ((1 << _la) &
              ((1 << AssetSelectionParser.QUOTED_STRING) |
                (1 << AssetSelectionParser.UNQUOTED_STRING) |
                (1 << AssetSelectionParser.UNQUOTED_WILDCARD_STRING))) !==
              0
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
    '\x03\uC91D\uCABA\u058D\uAFBA\u4F53\u0607\uEA8B\uC241\x03\x1Fz\x04\x02' +
    '\t\x02\x04\x03\t\x03\x04\x04\t\x04\x04\x05\t\x05\x04\x06\t\x06\x04\x07' +
    '\t\x07\x04\b\t\b\x04\t\t\t\x04\n\t\n\x03\x02\x03\x02\x03\x02\x03\x03\x03' +
    '\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03' +
    "\x03\x03\x03\x03\x03\x03\x03\x03\x03\x05\x03'\n\x03\x03\x03\x03\x03\x03" +
    '\x03\x03\x03\x03\x03\x03\x03\x07\x03/\n\x03\f\x03\x0E\x032\v\x03\x03\x04' +
    '\x03\x04\x03\x04\x03\x04\x03\x04\x03\x04\x03\x04\x03\x04\x03\x04\x03\x04' +
    '\x05\x04>\n\x04\x03\x05\x05\x05A\n\x05\x03\x05\x03\x05\x03\x06\x03\x06' +
    '\x05\x06G\n\x06\x03\x07\x03\x07\x03\b\x03\b\x03\b\x03\b\x03\b\x03\b\x03' +
    '\b\x03\b\x05\bS\n\b\x03\b\x03\b\x03\b\x03\b\x03\b\x03\b\x03\b\x03\b\x03' +
    '\b\x03\b\x03\b\x03\b\x03\b\x03\b\x03\b\x03\b\x03\b\x03\b\x03\b\x03\b\x03' +
    '\b\x03\b\x03\b\x05\bl\n\b\x03\b\x03\b\x03\b\x03\b\x03\b\x03\b\x05\bt\n' +
    '\b\x03\t\x03\t\x03\n\x03\n\x03\n\x02\x02\x03\x04\v\x02\x02\x04\x02\x06' +
    '\x02\b\x02\n\x02\f\x02\x0E\x02\x10\x02\x12\x02\x02\x05\x03\x02\x19\x1A' +
    '\x04\x02\x1B\x1C\x1E\x1E\x03\x02\x1B\x1D\x02\x87\x02\x14\x03\x02\x02\x02' +
    '\x04&\x03\x02\x02\x02\x06=\x03\x02\x02\x02\b@\x03\x02\x02\x02\nD\x03\x02' +
    '\x02\x02\fH\x03\x02\x02\x02\x0Es\x03\x02\x02\x02\x10u\x03\x02\x02\x02' +
    '\x12w\x03\x02\x02\x02\x14\x15\x05\x04\x03\x02\x15\x16\x07\x02\x02\x03' +
    "\x16\x03\x03\x02\x02\x02\x17\x18\b\x03\x01\x02\x18'\x05\x06\x04\x02\x19" +
    "\x1A\x05\b\x05\x02\x1A\x1B\x05\x06\x04\x02\x1B\x1C\x05\n\x06\x02\x1C'" +
    "\x03\x02\x02\x02\x1D\x1E\x05\b\x05\x02\x1E\x1F\x05\x06\x04\x02\x1F'\x03" +
    '\x02\x02\x02 !\x05\x06\x04\x02!"\x05\n\x06\x02"\'\x03\x02\x02\x02#$' +
    "\x07\x06\x02\x02$'\x05\x04\x03\x06%'\x07\x07\x02\x02&\x17\x03\x02\x02" +
    '\x02&\x19\x03\x02\x02\x02&\x1D\x03\x02\x02\x02& \x03\x02\x02\x02&#\x03' +
    "\x02\x02\x02&%\x03\x02\x02\x02'0\x03\x02\x02\x02()\f\x05\x02\x02)*\x07" +
    '\x04\x02\x02*/\x05\x04\x03\x06+,\f\x04\x02\x02,-\x07\x05\x02\x02-/\x05' +
    '\x04\x03\x05.(\x03\x02\x02\x02.+\x03\x02\x02\x02/2\x03\x02\x02\x020.\x03' +
    '\x02\x02\x0201\x03\x02\x02\x021\x05\x03\x02\x02\x0220\x03\x02\x02\x02' +
    '3>\x05\x0E\b\x0245\x05\f\x07\x0256\x07\v\x02\x0267\x05\x04\x03\x0278\x07' +
    '\f\x02\x028>\x03\x02\x02\x029:\x07\v\x02\x02:;\x05\x04\x03\x02;<\x07\f' +
    '\x02\x02<>\x03\x02\x02\x02=3\x03\x02\x02\x02=4\x03\x02\x02\x02=9\x03\x02' +
    '\x02\x02>\x07\x03\x02\x02\x02?A\x07\t\x02\x02@?\x03\x02\x02\x02@A\x03' +
    '\x02\x02\x02AB\x03\x02\x02\x02BC\x07\b\x02\x02C\t\x03\x02\x02\x02DF\x07' +
    '\b\x02\x02EG\x07\t\x02\x02FE\x03\x02\x02\x02FG\x03\x02\x02\x02G\v\x03' +
    '\x02\x02\x02HI\t\x02\x02\x02I\r\x03\x02\x02\x02JK\x07\x0E\x02\x02KL\x07' +
    '\n\x02\x02Lt\x05\x12\n\x02MN\x07\x11\x02\x02NO\x07\n\x02\x02OR\x05\x10' +
    '\t\x02PQ\x07\x03\x02\x02QS\x05\x10\t\x02RP\x03\x02\x02\x02RS\x03\x02\x02' +
    '\x02St\x03\x02\x02\x02TU\x07\x0F\x02\x02UV\x07\n\x02\x02Vt\x05\x10\t\x02' +
    'WX\x07\x10\x02\x02XY\x07\n\x02\x02Yt\x05\x10\t\x02Z[\x07\x12\x02\x02[' +
    '\\\x07\n\x02\x02\\t\x05\x10\t\x02]^\x07\x14\x02\x02^_\x07\n\x02\x02_t' +
    '\x05\x10\t\x02`a\x07\x15\x02\x02ab\x07\n\x02\x02bt\x05\x10\t\x02cd\x07' +
    '\x16\x02\x02de\x07\n\x02\x02et\x05\x10\t\x02fg\x07\x17\x02\x02gh\x07\n' +
    '\x02\x02hk\x05\x10\t\x02ij\x07\x03\x02\x02jl\x05\x10\t\x02ki\x03\x02\x02' +
    '\x02kl\x03\x02\x02\x02lt\x03\x02\x02\x02mn\x07\x13\x02\x02no\x07\n\x02' +
    '\x02ot\x05\x10\t\x02pq\x07\x18\x02\x02qr\x07\n\x02\x02rt\x05\x10\t\x02' +
    'sJ\x03\x02\x02\x02sM\x03\x02\x02\x02sT\x03\x02\x02\x02sW\x03\x02\x02\x02' +
    'sZ\x03\x02\x02\x02s]\x03\x02\x02\x02s`\x03\x02\x02\x02sc\x03\x02\x02\x02' +
    'sf\x03\x02\x02\x02sm\x03\x02\x02\x02sp\x03\x02\x02\x02t\x0F\x03\x02\x02' +
    '\x02uv\t\x03\x02\x02v\x11\x03\x02\x02\x02wx\t\x04\x02\x02x\x13\x03\x02' +
    '\x02\x02\v&.0=@FRks';
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
  public downTraversal(): DownTraversalContext {
    return this.getRuleContext(0, DownTraversalContext);
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

export class UpTraversalContext extends ParserRuleContext {
  public PLUS(): TerminalNode {
    return this.getToken(AssetSelectionParser.PLUS, 0);
  }
  public DIGITS(): TerminalNode | undefined {
    return this.tryGetToken(AssetSelectionParser.DIGITS, 0);
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return AssetSelectionParser.RULE_upTraversal;
  }
  // @Override
  public enterRule(listener: AssetSelectionListener): void {
    if (listener.enterUpTraversal) {
      listener.enterUpTraversal(this);
    }
  }
  // @Override
  public exitRule(listener: AssetSelectionListener): void {
    if (listener.exitUpTraversal) {
      listener.exitUpTraversal(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AssetSelectionVisitor<Result>): Result {
    if (visitor.visitUpTraversal) {
      return visitor.visitUpTraversal(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class DownTraversalContext extends ParserRuleContext {
  public PLUS(): TerminalNode {
    return this.getToken(AssetSelectionParser.PLUS, 0);
  }
  public DIGITS(): TerminalNode | undefined {
    return this.tryGetToken(AssetSelectionParser.DIGITS, 0);
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return AssetSelectionParser.RULE_downTraversal;
  }
  // @Override
  public enterRule(listener: AssetSelectionListener): void {
    if (listener.enterDownTraversal) {
      listener.enterDownTraversal(this);
    }
  }
  // @Override
  public exitRule(listener: AssetSelectionListener): void {
    if (listener.exitDownTraversal) {
      listener.exitDownTraversal(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AssetSelectionVisitor<Result>): Result {
    if (visitor.visitDownTraversal) {
      return visitor.visitDownTraversal(this);
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
  public keyValue(): KeyValueContext {
    return this.getRuleContext(0, KeyValueContext);
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
export class StatusAttributeExprContext extends AttributeExprContext {
  public STATUS(): TerminalNode {
    return this.getToken(AssetSelectionParser.STATUS, 0);
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
    if (listener.enterStatusAttributeExpr) {
      listener.enterStatusAttributeExpr(this);
    }
  }
  // @Override
  public exitRule(listener: AssetSelectionListener): void {
    if (listener.exitStatusAttributeExpr) {
      listener.exitStatusAttributeExpr(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AssetSelectionVisitor<Result>): Result {
    if (visitor.visitStatusAttributeExpr) {
      return visitor.visitStatusAttributeExpr(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class ColumnAttributeExprContext extends AttributeExprContext {
  public COLUMN(): TerminalNode {
    return this.getToken(AssetSelectionParser.COLUMN, 0);
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
    if (listener.enterColumnAttributeExpr) {
      listener.enterColumnAttributeExpr(this);
    }
  }
  // @Override
  public exitRule(listener: AssetSelectionListener): void {
    if (listener.exitColumnAttributeExpr) {
      listener.exitColumnAttributeExpr(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AssetSelectionVisitor<Result>): Result {
    if (visitor.visitColumnAttributeExpr) {
      return visitor.visitColumnAttributeExpr(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class TableNameAttributeExprContext extends AttributeExprContext {
  public TABLE_NAME(): TerminalNode {
    return this.getToken(AssetSelectionParser.TABLE_NAME, 0);
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
    if (listener.enterTableNameAttributeExpr) {
      listener.enterTableNameAttributeExpr(this);
    }
  }
  // @Override
  public exitRule(listener: AssetSelectionListener): void {
    if (listener.exitTableNameAttributeExpr) {
      listener.exitTableNameAttributeExpr(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AssetSelectionVisitor<Result>): Result {
    if (visitor.visitTableNameAttributeExpr) {
      return visitor.visitTableNameAttributeExpr(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class ColumnTagAttributeExprContext extends AttributeExprContext {
  public COLUMN_TAG(): TerminalNode {
    return this.getToken(AssetSelectionParser.COLUMN_TAG, 0);
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
    if (listener.enterColumnTagAttributeExpr) {
      listener.enterColumnTagAttributeExpr(this);
    }
  }
  // @Override
  public exitRule(listener: AssetSelectionListener): void {
    if (listener.exitColumnTagAttributeExpr) {
      listener.exitColumnTagAttributeExpr(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AssetSelectionVisitor<Result>): Result {
    if (visitor.visitColumnTagAttributeExpr) {
      return visitor.visitColumnTagAttributeExpr(this);
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
export class ChangedInBranchAttributeExprContext extends AttributeExprContext {
  public CHANGED_IN_BRANCH(): TerminalNode {
    return this.getToken(AssetSelectionParser.CHANGED_IN_BRANCH, 0);
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
    if (listener.enterChangedInBranchAttributeExpr) {
      listener.enterChangedInBranchAttributeExpr(this);
    }
  }
  // @Override
  public exitRule(listener: AssetSelectionListener): void {
    if (listener.exitChangedInBranchAttributeExpr) {
      listener.exitChangedInBranchAttributeExpr(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AssetSelectionVisitor<Result>): Result {
    if (visitor.visitChangedInBranchAttributeExpr) {
      return visitor.visitChangedInBranchAttributeExpr(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class ValueContext extends ParserRuleContext {
  public NULL_STRING(): TerminalNode | undefined {
    return this.tryGetToken(AssetSelectionParser.NULL_STRING, 0);
  }
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

export class KeyValueContext extends ParserRuleContext {
  public QUOTED_STRING(): TerminalNode | undefined {
    return this.tryGetToken(AssetSelectionParser.QUOTED_STRING, 0);
  }
  public UNQUOTED_STRING(): TerminalNode | undefined {
    return this.tryGetToken(AssetSelectionParser.UNQUOTED_STRING, 0);
  }
  public UNQUOTED_WILDCARD_STRING(): TerminalNode | undefined {
    return this.tryGetToken(AssetSelectionParser.UNQUOTED_WILDCARD_STRING, 0);
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return AssetSelectionParser.RULE_keyValue;
  }
  // @Override
  public enterRule(listener: AssetSelectionListener): void {
    if (listener.enterKeyValue) {
      listener.enterKeyValue(this);
    }
  }
  // @Override
  public exitRule(listener: AssetSelectionListener): void {
    if (listener.exitKeyValue) {
      listener.exitKeyValue(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AssetSelectionVisitor<Result>): Result {
    if (visitor.visitKeyValue) {
      return visitor.visitKeyValue(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
