// Generated from /Users/marcosalazar/code/dagster/js_modules/dagster-ui/packages/ui-core/src/selection/SelectionAutoComplete.g4 by ANTLR 4.9.0-SNAPSHOT

import {FailedPredicateException} from 'antlr4ts/FailedPredicateException';
import {NoViableAltException} from 'antlr4ts/NoViableAltException';
import {Parser} from 'antlr4ts/Parser';
import {ParserRuleContext} from 'antlr4ts/ParserRuleContext';
import {RecognitionException} from 'antlr4ts/RecognitionException';
import {RuleContext} from 'antlr4ts/RuleContext';
//import { RuleVersion } from "antlr4ts/RuleVersion";
import {TokenStream} from 'antlr4ts/TokenStream';
import {Vocabulary} from 'antlr4ts/Vocabulary';
import {VocabularyImpl} from 'antlr4ts/VocabularyImpl';
import {ATN} from 'antlr4ts/atn/ATN';
import {ATNDeserializer} from 'antlr4ts/atn/ATNDeserializer';
import {ParserATNSimulator} from 'antlr4ts/atn/ParserATNSimulator';
import * as Utils from 'antlr4ts/misc/Utils';
import {TerminalNode} from 'antlr4ts/tree/TerminalNode';

import {SelectionAutoCompleteListener} from './SelectionAutoCompleteListener';
import {SelectionAutoCompleteVisitor} from './SelectionAutoCompleteVisitor';

export class SelectionAutoCompleteParser extends Parser {
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
  public static readonly RULE_start = 0;
  public static readonly RULE_expr = 1;
  public static readonly RULE_traversalAllowedExpr = 2;
  public static readonly RULE_parenthesizedExpr = 3;
  public static readonly RULE_incompleteExpr = 4;
  public static readonly RULE_expressionLessParenthesizedExpr = 5;
  public static readonly RULE_upTraversalExpr = 6;
  public static readonly RULE_downTraversalExpr = 7;
  public static readonly RULE_upTraversalToken = 8;
  public static readonly RULE_downTraversalToken = 9;
  public static readonly RULE_attributeName = 10;
  public static readonly RULE_attributeValue = 11;
  public static readonly RULE_functionName = 12;
  public static readonly RULE_orToken = 13;
  public static readonly RULE_andToken = 14;
  public static readonly RULE_notToken = 15;
  public static readonly RULE_colonToken = 16;
  public static readonly RULE_leftParenToken = 17;
  public static readonly RULE_rightParenToken = 18;
  public static readonly RULE_attributeValueWhitespace = 19;
  public static readonly RULE_postAttributeValueWhitespace = 20;
  public static readonly RULE_postExpressionWhitespace = 21;
  public static readonly RULE_postNotOperatorWhitespace = 22;
  public static readonly RULE_postLogicalOperatorWhitespace = 23;
  public static readonly RULE_postNeighborTraversalWhitespace = 24;
  public static readonly RULE_postUpwardTraversalWhitespace = 25;
  public static readonly RULE_postDownwardTraversalWhitespace = 26;
  public static readonly RULE_postDigitsWhitespace = 27;
  public static readonly RULE_value = 28;
  // tslint:disable:no-trailing-whitespace
  public static readonly ruleNames: string[] = [
    'start',
    'expr',
    'traversalAllowedExpr',
    'parenthesizedExpr',
    'incompleteExpr',
    'expressionLessParenthesizedExpr',
    'upTraversalExpr',
    'downTraversalExpr',
    'upTraversalToken',
    'downTraversalToken',
    'attributeName',
    'attributeValue',
    'functionName',
    'orToken',
    'andToken',
    'notToken',
    'colonToken',
    'leftParenToken',
    'rightParenToken',
    'attributeValueWhitespace',
    'postAttributeValueWhitespace',
    'postExpressionWhitespace',
    'postNotOperatorWhitespace',
    'postLogicalOperatorWhitespace',
    'postNeighborTraversalWhitespace',
    'postUpwardTraversalWhitespace',
    'postDownwardTraversalWhitespace',
    'postDigitsWhitespace',
    'value',
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
  ];
  public static readonly VOCABULARY: Vocabulary = new VocabularyImpl(
    SelectionAutoCompleteParser._LITERAL_NAMES,
    SelectionAutoCompleteParser._SYMBOLIC_NAMES,
    [],
  );

  // @Override
  // @NotNull
  public get vocabulary(): Vocabulary {
    return SelectionAutoCompleteParser.VOCABULARY;
  }
  // tslint:enable:no-trailing-whitespace

  // @Override
  public get grammarFileName(): string {
    return 'SelectionAutoComplete.g4';
  }

  // @Override
  public get ruleNames(): string[] {
    return SelectionAutoCompleteParser.ruleNames;
  }

  // @Override
  public get serializedATN(): string {
    return SelectionAutoCompleteParser._serializedATN;
  }

  protected createFailedPredicateException(
    predicate?: string,
    message?: string,
  ): FailedPredicateException {
    return new FailedPredicateException(this, predicate, message);
  }

  constructor(input: TokenStream) {
    super(input);
    this._interp = new ParserATNSimulator(SelectionAutoCompleteParser._ATN, this);
  }
  // @RuleVersion(0)
  public start(): StartContext {
    const _localctx: StartContext = new StartContext(this._ctx, this.state);
    this.enterRule(_localctx, 0, SelectionAutoCompleteParser.RULE_start);
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 58;
        this.expr(0);
        this.state = 59;
        this.match(SelectionAutoCompleteParser.EOF);
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
    this.enterRecursionRule(_localctx, 2, SelectionAutoCompleteParser.RULE_expr, _p);
    try {
      let _alt: number;
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 85;
        this._errHandler.sync(this);
        switch (this.interpreter.adaptivePredict(this._input, 0, this._ctx)) {
          case 1:
            {
              _localctx = new TraversalAllowedExpressionContext(_localctx);
              this._ctx = _localctx;
              _prevctx = _localctx;

              this.state = 62;
              this.traversalAllowedExpr();
            }
            break;

          case 2:
            {
              _localctx = new UpAndDownTraversalExpressionContext(_localctx);
              this._ctx = _localctx;
              _prevctx = _localctx;
              this.state = 63;
              this.upTraversalExpr();
              this.state = 64;
              this.traversalAllowedExpr();
              this.state = 65;
              this.downTraversalExpr();
            }
            break;

          case 3:
            {
              _localctx = new UpTraversalExpressionContext(_localctx);
              this._ctx = _localctx;
              _prevctx = _localctx;
              this.state = 67;
              this.upTraversalExpr();
              this.state = 68;
              this.traversalAllowedExpr();
            }
            break;

          case 4:
            {
              _localctx = new DownTraversalExpressionContext(_localctx);
              this._ctx = _localctx;
              _prevctx = _localctx;
              this.state = 70;
              this.traversalAllowedExpr();
              this.state = 71;
              this.downTraversalExpr();
            }
            break;

          case 5:
            {
              _localctx = new NotExpressionContext(_localctx);
              this._ctx = _localctx;
              _prevctx = _localctx;
              this.state = 73;
              this.notToken();
              this.state = 74;
              this.postNotOperatorWhitespace();
              this.state = 75;
              this.expr(8);
            }
            break;

          case 6:
            {
              _localctx = new IncompleteNotExpressionContext(_localctx);
              this._ctx = _localctx;
              _prevctx = _localctx;
              this.state = 77;
              this.notToken();
              this.state = 78;
              this.postNotOperatorWhitespace();
            }
            break;

          case 7:
            {
              _localctx = new AllExpressionContext(_localctx);
              this._ctx = _localctx;
              _prevctx = _localctx;
              this.state = 80;
              this.match(SelectionAutoCompleteParser.STAR);
              this.state = 81;
              this.postExpressionWhitespace();
            }
            break;

          case 8:
            {
              _localctx = new UnmatchedValueContext(_localctx);
              this._ctx = _localctx;
              _prevctx = _localctx;
              this.state = 82;
              this.value();
              this.state = 83;
              this.postExpressionWhitespace();
            }
            break;
        }
        this._ctx._stop = this._input.tryLT(-1);
        this.state = 107;
        this._errHandler.sync(this);
        _alt = this.interpreter.adaptivePredict(this._input, 2, this._ctx);
        while (_alt !== 2 && _alt !== ATN.INVALID_ALT_NUMBER) {
          if (_alt === 1) {
            if (this._parseListeners != null) {
              this.triggerExitRuleEvent();
            }
            _prevctx = _localctx;
            {
              this.state = 105;
              this._errHandler.sync(this);
              switch (this.interpreter.adaptivePredict(this._input, 1, this._ctx)) {
                case 1:
                  {
                    _localctx = new AndExpressionContext(new ExprContext(_parentctx, _parentState));
                    this.pushNewRecursionContext(
                      _localctx,
                      _startState,
                      SelectionAutoCompleteParser.RULE_expr,
                    );
                    this.state = 87;
                    if (!this.precpred(this._ctx, 7)) {
                      throw this.createFailedPredicateException('this.precpred(this._ctx, 7)');
                    }
                    this.state = 88;
                    this.andToken();
                    this.state = 89;
                    this.postLogicalOperatorWhitespace();
                    this.state = 90;
                    this.expr(8);
                  }
                  break;

                case 2:
                  {
                    _localctx = new OrExpressionContext(new ExprContext(_parentctx, _parentState));
                    this.pushNewRecursionContext(
                      _localctx,
                      _startState,
                      SelectionAutoCompleteParser.RULE_expr,
                    );
                    this.state = 92;
                    if (!this.precpred(this._ctx, 6)) {
                      throw this.createFailedPredicateException('this.precpred(this._ctx, 6)');
                    }
                    this.state = 93;
                    this.orToken();
                    this.state = 94;
                    this.postLogicalOperatorWhitespace();
                    this.state = 95;
                    this.expr(7);
                  }
                  break;

                case 3:
                  {
                    _localctx = new IncompleteAndExpressionContext(
                      new ExprContext(_parentctx, _parentState),
                    );
                    this.pushNewRecursionContext(
                      _localctx,
                      _startState,
                      SelectionAutoCompleteParser.RULE_expr,
                    );
                    this.state = 97;
                    if (!this.precpred(this._ctx, 5)) {
                      throw this.createFailedPredicateException('this.precpred(this._ctx, 5)');
                    }
                    this.state = 98;
                    this.andToken();
                    this.state = 99;
                    this.postLogicalOperatorWhitespace();
                  }
                  break;

                case 4:
                  {
                    _localctx = new IncompleteOrExpressionContext(
                      new ExprContext(_parentctx, _parentState),
                    );
                    this.pushNewRecursionContext(
                      _localctx,
                      _startState,
                      SelectionAutoCompleteParser.RULE_expr,
                    );
                    this.state = 101;
                    if (!this.precpred(this._ctx, 4)) {
                      throw this.createFailedPredicateException('this.precpred(this._ctx, 4)');
                    }
                    this.state = 102;
                    this.orToken();
                    this.state = 103;
                    this.postLogicalOperatorWhitespace();
                  }
                  break;
              }
            }
          }
          this.state = 109;
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
    this.enterRule(_localctx, 4, SelectionAutoCompleteParser.RULE_traversalAllowedExpr);
    try {
      this.state = 124;
      this._errHandler.sync(this);
      switch (this.interpreter.adaptivePredict(this._input, 4, this._ctx)) {
        case 1:
          _localctx = new AttributeExpressionContext(_localctx);
          this.enterOuterAlt(_localctx, 1);
          {
            this.state = 110;
            this.attributeName();
            this.state = 111;
            this.colonToken();
            this.state = 112;
            this.attributeValue();
            this.state = 115;
            this._errHandler.sync(this);
            switch (this.interpreter.adaptivePredict(this._input, 3, this._ctx)) {
              case 1:
                {
                  this.state = 113;
                  this.match(SelectionAutoCompleteParser.EQUAL);
                  this.state = 114;
                  this.attributeValue();
                }
                break;
            }
            this.state = 117;
            this.postAttributeValueWhitespace();
          }
          break;

        case 2:
          _localctx = new FunctionCallExpressionContext(_localctx);
          this.enterOuterAlt(_localctx, 2);
          {
            this.state = 119;
            this.functionName();
            this.state = 120;
            this.parenthesizedExpr();
          }
          break;

        case 3:
          _localctx = new TraversalAllowedParenthesizedExpressionContext(_localctx);
          this.enterOuterAlt(_localctx, 3);
          {
            this.state = 122;
            this.parenthesizedExpr();
          }
          break;

        case 4:
          _localctx = new IncompleteExpressionContext(_localctx);
          this.enterOuterAlt(_localctx, 4);
          {
            this.state = 123;
            this.incompleteExpr();
          }
          break;
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
  public parenthesizedExpr(): ParenthesizedExprContext {
    let _localctx: ParenthesizedExprContext = new ParenthesizedExprContext(this._ctx, this.state);
    this.enterRule(_localctx, 6, SelectionAutoCompleteParser.RULE_parenthesizedExpr);
    try {
      _localctx = new ParenthesizedExpressionContext(_localctx);
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 126;
        this.leftParenToken();
        this.state = 127;
        this.postLogicalOperatorWhitespace();
        this.state = 128;
        this.expr(0);
        this.state = 129;
        this.rightParenToken();
        this.state = 130;
        this.postExpressionWhitespace();
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
  public incompleteExpr(): IncompleteExprContext {
    let _localctx: IncompleteExprContext = new IncompleteExprContext(this._ctx, this.state);
    this.enterRule(_localctx, 8, SelectionAutoCompleteParser.RULE_incompleteExpr);
    let _la: number;
    try {
      this.state = 176;
      this._errHandler.sync(this);
      switch (this.interpreter.adaptivePredict(this._input, 6, this._ctx)) {
        case 1:
          _localctx = new IncompleteAttributeExpressionMissingSecondValueContext(_localctx);
          this.enterOuterAlt(_localctx, 1);
          {
            this.state = 132;
            this.attributeName();
            this.state = 133;
            this.colonToken();
            this.state = 134;
            this.attributeValue();
            this.state = 135;
            this.match(SelectionAutoCompleteParser.EQUAL);
            this.state = 136;
            this.attributeValueWhitespace();
          }
          break;

        case 2:
          _localctx = new IncompleteAttributeExpressionMissingValueContext(_localctx);
          this.enterOuterAlt(_localctx, 2);
          {
            this.state = 138;
            this.attributeName();
            this.state = 139;
            this.colonToken();
            this.state = 140;
            this.attributeValueWhitespace();
          }
          break;

        case 3:
          _localctx = new ExpressionlessFunctionExpressionContext(_localctx);
          this.enterOuterAlt(_localctx, 3);
          {
            this.state = 142;
            this.functionName();
            this.state = 143;
            this.expressionLessParenthesizedExpr();
          }
          break;

        case 4:
          _localctx = new UnclosedExpressionlessFunctionExpressionContext(_localctx);
          this.enterOuterAlt(_localctx, 4);
          {
            this.state = 145;
            this.functionName();
            this.state = 146;
            this.leftParenToken();
            this.state = 147;
            this.postLogicalOperatorWhitespace();
          }
          break;

        case 5:
          _localctx = new UnclosedFunctionExpressionContext(_localctx);
          this.enterOuterAlt(_localctx, 5);
          {
            this.state = 149;
            this.functionName();
            this.state = 150;
            this.leftParenToken();
            this.state = 151;
            this.expr(0);
          }
          break;

        case 6:
          _localctx = new UnclosedParenthesizedExpressionContext(_localctx);
          this.enterOuterAlt(_localctx, 6);
          {
            this.state = 153;
            this.leftParenToken();
            this.state = 154;
            this.postLogicalOperatorWhitespace();
            this.state = 155;
            this.expr(0);
          }
          break;

        case 7:
          _localctx = new ExpressionlessParenthesizedExpressionWrapperContext(_localctx);
          this.enterOuterAlt(_localctx, 7);
          {
            this.state = 157;
            this.expressionLessParenthesizedExpr();
          }
          break;

        case 8:
          _localctx = new UnclosedExpressionlessParenthesizedExpressionContext(_localctx);
          this.enterOuterAlt(_localctx, 8);
          {
            this.state = 158;
            this.leftParenToken();
            this.state = 159;
            this.postLogicalOperatorWhitespace();
          }
          break;

        case 9:
          _localctx = new IncompletePlusTraversalExpressionContext(_localctx);
          this.enterOuterAlt(_localctx, 9);
          {
            this.state = 162;
            this._errHandler.sync(this);
            _la = this._input.LA(1);
            if (_la === SelectionAutoCompleteParser.DIGITS) {
              {
                this.state = 161;
                this.match(SelectionAutoCompleteParser.DIGITS);
              }
            }

            this.state = 164;
            this.match(SelectionAutoCompleteParser.PLUS);
            this.state = 165;
            this.postNeighborTraversalWhitespace();
          }
          break;

        case 10:
          _localctx = new IncompleteUpTraversalExpressionContext(_localctx);
          this.enterOuterAlt(_localctx, 10);
          {
            this.state = 166;
            this.match(SelectionAutoCompleteParser.DIGITS);
            this.state = 167;
            this.postDigitsWhitespace();
          }
          break;

        case 11:
          _localctx = new IncompletePlusTraversalExpressionMissingValueContext(_localctx);
          this.enterOuterAlt(_localctx, 11);
          {
            this.state = 168;
            this.match(SelectionAutoCompleteParser.PLUS);
            this.state = 169;
            this.value();
            this.state = 170;
            this.postExpressionWhitespace();
          }
          break;

        case 12:
          _localctx = new IncompleteAttributeExpressionMissingKeyContext(_localctx);
          this.enterOuterAlt(_localctx, 12);
          {
            this.state = 172;
            this.colonToken();
            this.state = 173;
            this.attributeValue();
            this.state = 174;
            this.postExpressionWhitespace();
          }
          break;
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
  public expressionLessParenthesizedExpr(): ExpressionLessParenthesizedExprContext {
    let _localctx: ExpressionLessParenthesizedExprContext =
      new ExpressionLessParenthesizedExprContext(this._ctx, this.state);
    this.enterRule(_localctx, 10, SelectionAutoCompleteParser.RULE_expressionLessParenthesizedExpr);
    try {
      _localctx = new ExpressionlessParenthesizedExpressionContext(_localctx);
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 178;
        this.leftParenToken();
        this.state = 179;
        this.postLogicalOperatorWhitespace();
        this.state = 180;
        this.rightParenToken();
        this.state = 181;
        this.postExpressionWhitespace();
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
  public upTraversalExpr(): UpTraversalExprContext {
    let _localctx: UpTraversalExprContext = new UpTraversalExprContext(this._ctx, this.state);
    this.enterRule(_localctx, 12, SelectionAutoCompleteParser.RULE_upTraversalExpr);
    try {
      _localctx = new UpTraversalContext(_localctx);
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 183;
        this.upTraversalToken();
        this.state = 184;
        this.postUpwardTraversalWhitespace();
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
  public downTraversalExpr(): DownTraversalExprContext {
    let _localctx: DownTraversalExprContext = new DownTraversalExprContext(this._ctx, this.state);
    this.enterRule(_localctx, 14, SelectionAutoCompleteParser.RULE_downTraversalExpr);
    try {
      _localctx = new DownTraversalContext(_localctx);
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 186;
        this.downTraversalToken();
        this.state = 187;
        this.postDownwardTraversalWhitespace();
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
  public upTraversalToken(): UpTraversalTokenContext {
    const _localctx: UpTraversalTokenContext = new UpTraversalTokenContext(this._ctx, this.state);
    this.enterRule(_localctx, 16, SelectionAutoCompleteParser.RULE_upTraversalToken);
    let _la: number;
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 190;
        this._errHandler.sync(this);
        _la = this._input.LA(1);
        if (_la === SelectionAutoCompleteParser.DIGITS) {
          {
            this.state = 189;
            this.match(SelectionAutoCompleteParser.DIGITS);
          }
        }

        this.state = 192;
        this.match(SelectionAutoCompleteParser.PLUS);
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
  public downTraversalToken(): DownTraversalTokenContext {
    const _localctx: DownTraversalTokenContext = new DownTraversalTokenContext(
      this._ctx,
      this.state,
    );
    this.enterRule(_localctx, 18, SelectionAutoCompleteParser.RULE_downTraversalToken);
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 194;
        this.match(SelectionAutoCompleteParser.PLUS);
        this.state = 196;
        this._errHandler.sync(this);
        switch (this.interpreter.adaptivePredict(this._input, 8, this._ctx)) {
          case 1:
            {
              this.state = 195;
              this.match(SelectionAutoCompleteParser.DIGITS);
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
  public attributeName(): AttributeNameContext {
    const _localctx: AttributeNameContext = new AttributeNameContext(this._ctx, this.state);
    this.enterRule(_localctx, 20, SelectionAutoCompleteParser.RULE_attributeName);
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 198;
        this.match(SelectionAutoCompleteParser.IDENTIFIER);
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
  public attributeValue(): AttributeValueContext {
    const _localctx: AttributeValueContext = new AttributeValueContext(this._ctx, this.state);
    this.enterRule(_localctx, 22, SelectionAutoCompleteParser.RULE_attributeValue);
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 200;
        this.value();
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
    this.enterRule(_localctx, 24, SelectionAutoCompleteParser.RULE_functionName);
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 202;
        this.match(SelectionAutoCompleteParser.IDENTIFIER);
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
  public orToken(): OrTokenContext {
    const _localctx: OrTokenContext = new OrTokenContext(this._ctx, this.state);
    this.enterRule(_localctx, 26, SelectionAutoCompleteParser.RULE_orToken);
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 204;
        this.match(SelectionAutoCompleteParser.OR);
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
  public andToken(): AndTokenContext {
    const _localctx: AndTokenContext = new AndTokenContext(this._ctx, this.state);
    this.enterRule(_localctx, 28, SelectionAutoCompleteParser.RULE_andToken);
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 206;
        this.match(SelectionAutoCompleteParser.AND);
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
  public notToken(): NotTokenContext {
    const _localctx: NotTokenContext = new NotTokenContext(this._ctx, this.state);
    this.enterRule(_localctx, 30, SelectionAutoCompleteParser.RULE_notToken);
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 208;
        this.match(SelectionAutoCompleteParser.NOT);
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
  public colonToken(): ColonTokenContext {
    const _localctx: ColonTokenContext = new ColonTokenContext(this._ctx, this.state);
    this.enterRule(_localctx, 32, SelectionAutoCompleteParser.RULE_colonToken);
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 210;
        this.match(SelectionAutoCompleteParser.COLON);
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
  public leftParenToken(): LeftParenTokenContext {
    const _localctx: LeftParenTokenContext = new LeftParenTokenContext(this._ctx, this.state);
    this.enterRule(_localctx, 34, SelectionAutoCompleteParser.RULE_leftParenToken);
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 212;
        this.match(SelectionAutoCompleteParser.LPAREN);
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
  public rightParenToken(): RightParenTokenContext {
    const _localctx: RightParenTokenContext = new RightParenTokenContext(this._ctx, this.state);
    this.enterRule(_localctx, 36, SelectionAutoCompleteParser.RULE_rightParenToken);
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 214;
        this.match(SelectionAutoCompleteParser.RPAREN);
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
  public attributeValueWhitespace(): AttributeValueWhitespaceContext {
    const _localctx: AttributeValueWhitespaceContext = new AttributeValueWhitespaceContext(
      this._ctx,
      this.state,
    );
    this.enterRule(_localctx, 38, SelectionAutoCompleteParser.RULE_attributeValueWhitespace);
    try {
      let _alt: number;
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 219;
        this._errHandler.sync(this);
        _alt = this.interpreter.adaptivePredict(this._input, 9, this._ctx);
        while (_alt !== 2 && _alt !== ATN.INVALID_ALT_NUMBER) {
          if (_alt === 1) {
            {
              {
                this.state = 216;
                this.match(SelectionAutoCompleteParser.WS);
              }
            }
          }
          this.state = 221;
          this._errHandler.sync(this);
          _alt = this.interpreter.adaptivePredict(this._input, 9, this._ctx);
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
  public postAttributeValueWhitespace(): PostAttributeValueWhitespaceContext {
    const _localctx: PostAttributeValueWhitespaceContext = new PostAttributeValueWhitespaceContext(
      this._ctx,
      this.state,
    );
    this.enterRule(_localctx, 40, SelectionAutoCompleteParser.RULE_postAttributeValueWhitespace);
    try {
      let _alt: number;
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 225;
        this._errHandler.sync(this);
        _alt = this.interpreter.adaptivePredict(this._input, 10, this._ctx);
        while (_alt !== 2 && _alt !== ATN.INVALID_ALT_NUMBER) {
          if (_alt === 1) {
            {
              {
                this.state = 222;
                this.match(SelectionAutoCompleteParser.WS);
              }
            }
          }
          this.state = 227;
          this._errHandler.sync(this);
          _alt = this.interpreter.adaptivePredict(this._input, 10, this._ctx);
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
  public postExpressionWhitespace(): PostExpressionWhitespaceContext {
    const _localctx: PostExpressionWhitespaceContext = new PostExpressionWhitespaceContext(
      this._ctx,
      this.state,
    );
    this.enterRule(_localctx, 42, SelectionAutoCompleteParser.RULE_postExpressionWhitespace);
    try {
      let _alt: number;
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 231;
        this._errHandler.sync(this);
        _alt = this.interpreter.adaptivePredict(this._input, 11, this._ctx);
        while (_alt !== 2 && _alt !== ATN.INVALID_ALT_NUMBER) {
          if (_alt === 1) {
            {
              {
                this.state = 228;
                this.match(SelectionAutoCompleteParser.WS);
              }
            }
          }
          this.state = 233;
          this._errHandler.sync(this);
          _alt = this.interpreter.adaptivePredict(this._input, 11, this._ctx);
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
  public postNotOperatorWhitespace(): PostNotOperatorWhitespaceContext {
    const _localctx: PostNotOperatorWhitespaceContext = new PostNotOperatorWhitespaceContext(
      this._ctx,
      this.state,
    );
    this.enterRule(_localctx, 44, SelectionAutoCompleteParser.RULE_postNotOperatorWhitespace);
    try {
      let _alt: number;
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 237;
        this._errHandler.sync(this);
        _alt = this.interpreter.adaptivePredict(this._input, 12, this._ctx);
        while (_alt !== 2 && _alt !== ATN.INVALID_ALT_NUMBER) {
          if (_alt === 1) {
            {
              {
                this.state = 234;
                this.match(SelectionAutoCompleteParser.WS);
              }
            }
          }
          this.state = 239;
          this._errHandler.sync(this);
          _alt = this.interpreter.adaptivePredict(this._input, 12, this._ctx);
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
  public postLogicalOperatorWhitespace(): PostLogicalOperatorWhitespaceContext {
    const _localctx: PostLogicalOperatorWhitespaceContext =
      new PostLogicalOperatorWhitespaceContext(this._ctx, this.state);
    this.enterRule(_localctx, 46, SelectionAutoCompleteParser.RULE_postLogicalOperatorWhitespace);
    try {
      let _alt: number;
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 243;
        this._errHandler.sync(this);
        _alt = this.interpreter.adaptivePredict(this._input, 13, this._ctx);
        while (_alt !== 2 && _alt !== ATN.INVALID_ALT_NUMBER) {
          if (_alt === 1) {
            {
              {
                this.state = 240;
                this.match(SelectionAutoCompleteParser.WS);
              }
            }
          }
          this.state = 245;
          this._errHandler.sync(this);
          _alt = this.interpreter.adaptivePredict(this._input, 13, this._ctx);
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
  public postNeighborTraversalWhitespace(): PostNeighborTraversalWhitespaceContext {
    const _localctx: PostNeighborTraversalWhitespaceContext =
      new PostNeighborTraversalWhitespaceContext(this._ctx, this.state);
    this.enterRule(_localctx, 48, SelectionAutoCompleteParser.RULE_postNeighborTraversalWhitespace);
    try {
      let _alt: number;
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 249;
        this._errHandler.sync(this);
        _alt = this.interpreter.adaptivePredict(this._input, 14, this._ctx);
        while (_alt !== 2 && _alt !== ATN.INVALID_ALT_NUMBER) {
          if (_alt === 1) {
            {
              {
                this.state = 246;
                this.match(SelectionAutoCompleteParser.WS);
              }
            }
          }
          this.state = 251;
          this._errHandler.sync(this);
          _alt = this.interpreter.adaptivePredict(this._input, 14, this._ctx);
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
  public postUpwardTraversalWhitespace(): PostUpwardTraversalWhitespaceContext {
    const _localctx: PostUpwardTraversalWhitespaceContext =
      new PostUpwardTraversalWhitespaceContext(this._ctx, this.state);
    this.enterRule(_localctx, 50, SelectionAutoCompleteParser.RULE_postUpwardTraversalWhitespace);
    let _la: number;
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 255;
        this._errHandler.sync(this);
        _la = this._input.LA(1);
        while (_la === SelectionAutoCompleteParser.WS) {
          {
            {
              this.state = 252;
              this.match(SelectionAutoCompleteParser.WS);
            }
          }
          this.state = 257;
          this._errHandler.sync(this);
          _la = this._input.LA(1);
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
  public postDownwardTraversalWhitespace(): PostDownwardTraversalWhitespaceContext {
    const _localctx: PostDownwardTraversalWhitespaceContext =
      new PostDownwardTraversalWhitespaceContext(this._ctx, this.state);
    this.enterRule(_localctx, 52, SelectionAutoCompleteParser.RULE_postDownwardTraversalWhitespace);
    try {
      let _alt: number;
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 261;
        this._errHandler.sync(this);
        _alt = this.interpreter.adaptivePredict(this._input, 16, this._ctx);
        while (_alt !== 2 && _alt !== ATN.INVALID_ALT_NUMBER) {
          if (_alt === 1) {
            {
              {
                this.state = 258;
                this.match(SelectionAutoCompleteParser.WS);
              }
            }
          }
          this.state = 263;
          this._errHandler.sync(this);
          _alt = this.interpreter.adaptivePredict(this._input, 16, this._ctx);
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
  public postDigitsWhitespace(): PostDigitsWhitespaceContext {
    const _localctx: PostDigitsWhitespaceContext = new PostDigitsWhitespaceContext(
      this._ctx,
      this.state,
    );
    this.enterRule(_localctx, 54, SelectionAutoCompleteParser.RULE_postDigitsWhitespace);
    try {
      let _alt: number;
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 267;
        this._errHandler.sync(this);
        _alt = this.interpreter.adaptivePredict(this._input, 17, this._ctx);
        while (_alt !== 2 && _alt !== ATN.INVALID_ALT_NUMBER) {
          if (_alt === 1) {
            {
              {
                this.state = 264;
                this.match(SelectionAutoCompleteParser.WS);
              }
            }
          }
          this.state = 269;
          this._errHandler.sync(this);
          _alt = this.interpreter.adaptivePredict(this._input, 17, this._ctx);
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
  public value(): ValueContext {
    let _localctx: ValueContext = new ValueContext(this._ctx, this.state);
    this.enterRule(_localctx, 56, SelectionAutoCompleteParser.RULE_value);
    try {
      this.state = 274;
      this._errHandler.sync(this);
      switch (this._input.LA(1)) {
        case SelectionAutoCompleteParser.QUOTED_STRING:
          _localctx = new QuotedStringValueContext(_localctx);
          this.enterOuterAlt(_localctx, 1);
          {
            this.state = 270;
            this.match(SelectionAutoCompleteParser.QUOTED_STRING);
          }
          break;
        case SelectionAutoCompleteParser.INCOMPLETE_LEFT_QUOTED_STRING:
          _localctx = new IncompleteLeftQuotedStringValueContext(_localctx);
          this.enterOuterAlt(_localctx, 2);
          {
            this.state = 271;
            this.match(SelectionAutoCompleteParser.INCOMPLETE_LEFT_QUOTED_STRING);
          }
          break;
        case SelectionAutoCompleteParser.INCOMPLETE_RIGHT_QUOTED_STRING:
          _localctx = new IncompleteRightQuotedStringValueContext(_localctx);
          this.enterOuterAlt(_localctx, 3);
          {
            this.state = 272;
            this.match(SelectionAutoCompleteParser.INCOMPLETE_RIGHT_QUOTED_STRING);
          }
          break;
        case SelectionAutoCompleteParser.IDENTIFIER:
          _localctx = new UnquotedStringValueContext(_localctx);
          this.enterOuterAlt(_localctx, 4);
          {
            this.state = 273;
            this.match(SelectionAutoCompleteParser.IDENTIFIER);
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
        return this.precpred(this._ctx, 7);

      case 1:
        return this.precpred(this._ctx, 6);

      case 2:
        return this.precpred(this._ctx, 5);

      case 3:
        return this.precpred(this._ctx, 4);
    }
    return true;
  }

  public static readonly _serializedATN: string =
    '\x03\uC91D\uCABA\u058D\uAFBA\u4F53\u0607\uEA8B\uC241\x03\x11\u0117\x04' +
    '\x02\t\x02\x04\x03\t\x03\x04\x04\t\x04\x04\x05\t\x05\x04\x06\t\x06\x04' +
    '\x07\t\x07\x04\b\t\b\x04\t\t\t\x04\n\t\n\x04\v\t\v\x04\f\t\f\x04\r\t\r' +
    '\x04\x0E\t\x0E\x04\x0F\t\x0F\x04\x10\t\x10\x04\x11\t\x11\x04\x12\t\x12' +
    '\x04\x13\t\x13\x04\x14\t\x14\x04\x15\t\x15\x04\x16\t\x16\x04\x17\t\x17' +
    '\x04\x18\t\x18\x04\x19\t\x19\x04\x1A\t\x1A\x04\x1B\t\x1B\x04\x1C\t\x1C' +
    '\x04\x1D\t\x1D\x04\x1E\t\x1E\x03\x02\x03\x02\x03\x02\x03\x03\x03\x03\x03' +
    '\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03' +
    '\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03' +
    '\x03\x03\x03\x03\x03\x03\x03\x05\x03X\n\x03\x03\x03\x03\x03\x03\x03\x03' +
    '\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03' +
    '\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x07\x03l\n\x03\f\x03\x0E' +
    '\x03o\v\x03\x03\x04\x03\x04\x03\x04\x03\x04\x03\x04\x05\x04v\n\x04\x03' +
    '\x04\x03\x04\x03\x04\x03\x04\x03\x04\x03\x04\x03\x04\x05\x04\x7F\n\x04' +
    '\x03\x05\x03\x05\x03\x05\x03\x05\x03\x05\x03\x05\x03\x06\x03\x06\x03\x06' +
    '\x03\x06\x03\x06\x03\x06\x03\x06\x03\x06\x03\x06\x03\x06\x03\x06\x03\x06' +
    '\x03\x06\x03\x06\x03\x06\x03\x06\x03\x06\x03\x06\x03\x06\x03\x06\x03\x06' +
    '\x03\x06\x03\x06\x03\x06\x03\x06\x03\x06\x03\x06\x03\x06\x03\x06\x03\x06' +
    '\x05\x06\xA5\n\x06\x03\x06\x03\x06\x03\x06\x03\x06\x03\x06\x03\x06\x03' +
    '\x06\x03\x06\x03\x06\x03\x06\x03\x06\x03\x06\x05\x06\xB3\n\x06\x03\x07' +
    '\x03\x07\x03\x07\x03\x07\x03\x07\x03\b\x03\b\x03\b\x03\t\x03\t\x03\t\x03' +
    '\n\x05\n\xC1\n\n\x03\n\x03\n\x03\v\x03\v\x05\v\xC7\n\v\x03\f\x03\f\x03' +
    '\r\x03\r\x03\x0E\x03\x0E\x03\x0F\x03\x0F\x03\x10\x03\x10\x03\x11\x03\x11' +
    '\x03\x12\x03\x12\x03\x13\x03\x13\x03\x14\x03\x14\x03\x15\x07\x15\xDC\n' +
    '\x15\f\x15\x0E\x15\xDF\v\x15\x03\x16\x07\x16\xE2\n\x16\f\x16\x0E\x16\xE5' +
    '\v\x16\x03\x17\x07\x17\xE8\n\x17\f\x17\x0E\x17\xEB\v\x17\x03\x18\x07\x18' +
    '\xEE\n\x18\f\x18\x0E\x18\xF1\v\x18\x03\x19\x07\x19\xF4\n\x19\f\x19\x0E' +
    '\x19\xF7\v\x19\x03\x1A\x07\x1A\xFA\n\x1A\f\x1A\x0E\x1A\xFD\v\x1A\x03\x1B' +
    '\x07\x1B\u0100\n\x1B\f\x1B\x0E\x1B\u0103\v\x1B\x03\x1C\x07\x1C\u0106\n' +
    '\x1C\f\x1C\x0E\x1C\u0109\v\x1C\x03\x1D\x07\x1D\u010C\n\x1D\f\x1D\x0E\x1D' +
    '\u010F\v\x1D\x03\x1E\x03\x1E\x03\x1E\x03\x1E\x05\x1E\u0115\n\x1E\x03\x1E' +
    '\x02\x02\x03\x04\x1F\x02\x02\x04\x02\x06\x02\b\x02\n\x02\f\x02\x0E\x02' +
    '\x10\x02\x12\x02\x14\x02\x16\x02\x18\x02\x1A\x02\x1C\x02\x1E\x02 \x02' +
    '"\x02$\x02&\x02(\x02*\x02,\x02.\x020\x022\x024\x026\x028\x02:\x02\x02' +
    '\x02\x02\u0122\x02<\x03\x02\x02\x02\x04W\x03\x02\x02\x02\x06~\x03\x02' +
    '\x02\x02\b\x80\x03\x02\x02\x02\n\xB2\x03\x02\x02\x02\f\xB4\x03\x02\x02' +
    '\x02\x0E\xB9\x03\x02\x02\x02\x10\xBC\x03\x02\x02\x02\x12\xC0\x03\x02\x02' +
    '\x02\x14\xC4\x03\x02\x02\x02\x16\xC8\x03\x02\x02\x02\x18\xCA\x03\x02\x02' +
    '\x02\x1A\xCC\x03\x02\x02\x02\x1C\xCE\x03\x02\x02\x02\x1E\xD0\x03\x02\x02' +
    '\x02 \xD2\x03\x02\x02\x02"\xD4\x03\x02\x02\x02$\xD6\x03\x02\x02\x02&' +
    '\xD8\x03\x02\x02\x02(\xDD\x03\x02\x02\x02*\xE3\x03\x02\x02\x02,\xE9\x03' +
    '\x02\x02\x02.\xEF\x03\x02\x02\x020\xF5\x03\x02\x02\x022\xFB\x03\x02\x02' +
    '\x024\u0101\x03\x02\x02\x026\u0107\x03\x02\x02\x028\u010D\x03\x02\x02' +
    '\x02:\u0114\x03\x02\x02\x02<=\x05\x04\x03\x02=>\x07\x02\x02\x03>\x03\x03' +
    '\x02\x02\x02?@\b\x03\x01\x02@X\x05\x06\x04\x02AB\x05\x0E\b\x02BC\x05\x06' +
    '\x04\x02CD\x05\x10\t\x02DX\x03\x02\x02\x02EF\x05\x0E\b\x02FG\x05\x06\x04' +
    '\x02GX\x03\x02\x02\x02HI\x05\x06\x04\x02IJ\x05\x10\t\x02JX\x03\x02\x02' +
    '\x02KL\x05 \x11\x02LM\x05.\x18\x02MN\x05\x04\x03\nNX\x03\x02\x02\x02O' +
    'P\x05 \x11\x02PQ\x05.\x18\x02QX\x03\x02\x02\x02RS\x07\x06\x02\x02SX\x05' +
    ',\x17\x02TU\x05:\x1E\x02UV\x05,\x17\x02VX\x03\x02\x02\x02W?\x03\x02\x02' +
    '\x02WA\x03\x02\x02\x02WE\x03\x02\x02\x02WH\x03\x02\x02\x02WK\x03\x02\x02' +
    '\x02WO\x03\x02\x02\x02WR\x03\x02\x02\x02WT\x03\x02\x02\x02Xm\x03\x02\x02' +
    '\x02YZ\f\t\x02\x02Z[\x05\x1E\x10\x02[\\\x050\x19\x02\\]\x05\x04\x03\n' +
    ']l\x03\x02\x02\x02^_\f\b\x02\x02_`\x05\x1C\x0F\x02`a\x050\x19\x02ab\x05' +
    '\x04\x03\tbl\x03\x02\x02\x02cd\f\x07\x02\x02de\x05\x1E\x10\x02ef\x050' +
    '\x19\x02fl\x03\x02\x02\x02gh\f\x06\x02\x02hi\x05\x1C\x0F\x02ij\x050\x19' +
    '\x02jl\x03\x02\x02\x02kY\x03\x02\x02\x02k^\x03\x02\x02\x02kc\x03\x02\x02' +
    '\x02kg\x03\x02\x02\x02lo\x03\x02\x02\x02mk\x03\x02\x02\x02mn\x03\x02\x02' +
    '\x02n\x05\x03\x02\x02\x02om\x03\x02\x02\x02pq\x05\x16\f\x02qr\x05"\x12' +
    '\x02ru\x05\x18\r\x02st\x07\x0F\x02\x02tv\x05\x18\r\x02us\x03\x02\x02\x02' +
    'uv\x03\x02\x02\x02vw\x03\x02\x02\x02wx\x05*\x16\x02x\x7F\x03\x02\x02\x02' +
    'yz\x05\x1A\x0E\x02z{\x05\b\x05\x02{\x7F\x03\x02\x02\x02|\x7F\x05\b\x05' +
    '\x02}\x7F\x05\n\x06\x02~p\x03\x02\x02\x02~y\x03\x02\x02\x02~|\x03\x02' +
    '\x02\x02~}\x03\x02\x02\x02\x7F\x07\x03\x02\x02\x02\x80\x81\x05$\x13\x02' +
    '\x81\x82\x050\x19\x02\x82\x83\x05\x04\x03\x02\x83\x84\x05&\x14\x02\x84' +
    '\x85\x05,\x17\x02\x85\t\x03\x02\x02\x02\x86\x87\x05\x16\f\x02\x87\x88' +
    '\x05"\x12\x02\x88\x89\x05\x18\r\x02\x89\x8A\x07\x0F\x02\x02\x8A\x8B\x05' +
    '(\x15\x02\x8B\xB3\x03\x02\x02\x02\x8C\x8D\x05\x16\f\x02\x8D\x8E\x05"' +
    '\x12\x02\x8E\x8F\x05(\x15\x02\x8F\xB3\x03\x02\x02\x02\x90\x91\x05\x1A' +
    '\x0E\x02\x91\x92\x05\f\x07\x02\x92\xB3\x03\x02\x02\x02\x93\x94\x05\x1A' +
    '\x0E\x02\x94\x95\x05$\x13\x02\x95\x96\x050\x19\x02\x96\xB3\x03\x02\x02' +
    '\x02\x97\x98\x05\x1A\x0E\x02\x98\x99\x05$\x13\x02\x99\x9A\x05\x04\x03' +
    '\x02\x9A\xB3\x03\x02\x02\x02\x9B\x9C\x05$\x13\x02\x9C\x9D\x050\x19\x02' +
    '\x9D\x9E\x05\x04\x03\x02\x9E\xB3\x03\x02\x02\x02\x9F\xB3\x05\f\x07\x02' +
    '\xA0\xA1\x05$\x13\x02\xA1\xA2\x050\x19\x02\xA2\xB3\x03\x02\x02\x02\xA3' +
    '\xA5\x07\b\x02\x02\xA4\xA3\x03\x02\x02\x02\xA4\xA5\x03\x02\x02\x02\xA5' +
    '\xA6\x03\x02\x02\x02\xA6\xA7\x07\x07\x02\x02\xA7\xB3\x052\x1A\x02\xA8' +
    '\xA9\x07\b\x02\x02\xA9\xB3\x058\x1D\x02\xAA\xAB\x07\x07\x02\x02\xAB\xAC' +
    '\x05:\x1E\x02\xAC\xAD\x05,\x17\x02\xAD\xB3\x03\x02\x02\x02\xAE\xAF\x05' +
    '"\x12\x02\xAF\xB0\x05\x18\r\x02\xB0\xB1\x05,\x17\x02\xB1\xB3\x03\x02' +
    '\x02\x02\xB2\x86\x03\x02\x02\x02\xB2\x8C\x03\x02\x02\x02\xB2\x90\x03\x02' +
    '\x02\x02\xB2\x93\x03\x02\x02\x02\xB2\x97\x03\x02\x02\x02\xB2\x9B\x03\x02' +
    '\x02\x02\xB2\x9F\x03\x02\x02\x02\xB2\xA0\x03\x02\x02\x02\xB2\xA4\x03\x02' +
    '\x02\x02\xB2\xA8\x03\x02\x02\x02\xB2\xAA\x03\x02\x02\x02\xB2\xAE\x03\x02' +
    '\x02\x02\xB3\v\x03\x02\x02\x02\xB4\xB5\x05$\x13\x02\xB5\xB6\x050\x19\x02' +
    '\xB6\xB7\x05&\x14\x02\xB7\xB8\x05,\x17\x02\xB8\r\x03\x02\x02\x02\xB9\xBA' +
    '\x05\x12\n\x02\xBA\xBB\x054\x1B\x02\xBB\x0F\x03\x02\x02\x02\xBC\xBD\x05' +
    '\x14\v\x02\xBD\xBE\x056\x1C\x02\xBE\x11\x03\x02\x02\x02\xBF\xC1\x07\b' +
    '\x02\x02\xC0\xBF\x03\x02\x02\x02\xC0\xC1\x03\x02\x02\x02\xC1\xC2\x03\x02' +
    '\x02\x02\xC2\xC3\x07\x07\x02\x02\xC3\x13\x03\x02\x02\x02\xC4\xC6\x07\x07' +
    '\x02\x02\xC5\xC7\x07\b\x02\x02\xC6\xC5\x03\x02\x02\x02\xC6\xC7\x03\x02' +
    '\x02\x02\xC7\x15\x03\x02\x02\x02\xC8\xC9\x07\x10\x02\x02\xC9\x17\x03\x02' +
    '\x02\x02\xCA\xCB\x05:\x1E\x02\xCB\x19\x03\x02\x02\x02\xCC\xCD\x07\x10' +
    '\x02\x02\xCD\x1B\x03\x02\x02\x02\xCE\xCF\x07\x04\x02\x02\xCF\x1D\x03\x02' +
    '\x02\x02\xD0\xD1\x07\x03\x02\x02\xD1\x1F\x03\x02\x02\x02\xD2\xD3\x07\x05' +
    '\x02\x02\xD3!\x03\x02\x02\x02\xD4\xD5\x07\t\x02\x02\xD5#\x03\x02\x02\x02' +
    '\xD6\xD7\x07\n\x02\x02\xD7%\x03\x02\x02\x02\xD8\xD9\x07\v\x02\x02\xD9' +
    "'\x03\x02\x02\x02\xDA\xDC\x07\x11\x02\x02\xDB\xDA\x03\x02\x02\x02\xDC" +
    '\xDF\x03\x02\x02\x02\xDD\xDB\x03\x02\x02\x02\xDD\xDE\x03\x02\x02\x02\xDE' +
    ')\x03\x02\x02\x02\xDF\xDD\x03\x02\x02\x02\xE0\xE2\x07\x11\x02\x02\xE1' +
    '\xE0\x03\x02\x02\x02\xE2\xE5\x03\x02\x02\x02\xE3\xE1\x03\x02\x02\x02\xE3' +
    '\xE4\x03\x02\x02\x02\xE4+\x03\x02\x02\x02\xE5\xE3\x03\x02\x02\x02\xE6' +
    '\xE8\x07\x11\x02\x02\xE7\xE6\x03\x02\x02\x02\xE8\xEB\x03\x02\x02\x02\xE9' +
    '\xE7\x03\x02\x02\x02\xE9\xEA\x03\x02\x02\x02\xEA-\x03\x02\x02\x02\xEB' +
    '\xE9\x03\x02\x02\x02\xEC\xEE\x07\x11\x02\x02\xED\xEC\x03\x02\x02\x02\xEE' +
    '\xF1\x03\x02\x02\x02\xEF\xED\x03\x02\x02\x02\xEF\xF0\x03\x02\x02\x02\xF0' +
    '/\x03\x02\x02\x02\xF1\xEF\x03\x02\x02\x02\xF2\xF4\x07\x11\x02\x02\xF3' +
    '\xF2\x03\x02\x02\x02\xF4\xF7\x03\x02\x02\x02\xF5\xF3\x03\x02\x02\x02\xF5' +
    '\xF6\x03\x02\x02\x02\xF61\x03\x02\x02\x02\xF7\xF5\x03\x02\x02\x02\xF8' +
    '\xFA\x07\x11\x02\x02\xF9\xF8\x03\x02\x02\x02\xFA\xFD\x03\x02\x02\x02\xFB' +
    '\xF9\x03\x02\x02\x02\xFB\xFC\x03\x02\x02\x02\xFC3\x03\x02\x02\x02\xFD' +
    '\xFB\x03\x02\x02\x02\xFE\u0100\x07\x11\x02\x02\xFF\xFE\x03\x02\x02\x02' +
    '\u0100\u0103\x03\x02\x02\x02\u0101\xFF\x03\x02\x02\x02\u0101\u0102\x03' +
    '\x02\x02\x02\u01025\x03\x02\x02\x02\u0103\u0101\x03\x02\x02\x02\u0104' +
    '\u0106\x07\x11\x02\x02\u0105\u0104\x03\x02\x02\x02\u0106\u0109\x03\x02' +
    '\x02\x02\u0107\u0105\x03\x02\x02\x02\u0107\u0108\x03\x02\x02\x02\u0108' +
    '7\x03\x02\x02\x02\u0109\u0107\x03\x02\x02\x02\u010A\u010C\x07\x11\x02' +
    '\x02\u010B\u010A\x03\x02\x02\x02\u010C\u010F\x03\x02\x02\x02\u010D\u010B' +
    '\x03\x02\x02\x02\u010D\u010E\x03\x02\x02\x02\u010E9\x03\x02\x02\x02\u010F' +
    '\u010D\x03\x02\x02\x02\u0110\u0115\x07\f\x02\x02\u0111\u0115\x07\r\x02' +
    '\x02\u0112\u0115\x07\x0E\x02\x02\u0113\u0115\x07\x10\x02\x02\u0114\u0110' +
    '\x03\x02\x02\x02\u0114\u0111\x03\x02\x02\x02\u0114\u0112\x03\x02\x02\x02' +
    '\u0114\u0113\x03\x02\x02\x02\u0115;\x03\x02\x02\x02\x15Wkmu~\xA4\xB2\xC0' +
    '\xC6\xDD\xE3\xE9\xEF\xF5\xFB\u0101\u0107\u010D\u0114';
  public static __ATN: ATN;
  public static get _ATN(): ATN {
    if (!SelectionAutoCompleteParser.__ATN) {
      SelectionAutoCompleteParser.__ATN = new ATNDeserializer().deserialize(
        Utils.toCharArray(SelectionAutoCompleteParser._serializedATN),
      );
    }

    return SelectionAutoCompleteParser.__ATN;
  }
}

export class StartContext extends ParserRuleContext {
  public expr(): ExprContext {
    return this.getRuleContext(0, ExprContext);
  }
  public EOF(): TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.EOF, 0);
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_start;
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterStart) {
      listener.enterStart(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitStart) {
      listener.exitStart(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
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
    return SelectionAutoCompleteParser.RULE_expr;
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
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterTraversalAllowedExpression) {
      listener.enterTraversalAllowedExpression(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitTraversalAllowedExpression) {
      listener.exitTraversalAllowedExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitTraversalAllowedExpression) {
      return visitor.visitTraversalAllowedExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class UpAndDownTraversalExpressionContext extends ExprContext {
  public upTraversalExpr(): UpTraversalExprContext {
    return this.getRuleContext(0, UpTraversalExprContext);
  }
  public traversalAllowedExpr(): TraversalAllowedExprContext {
    return this.getRuleContext(0, TraversalAllowedExprContext);
  }
  public downTraversalExpr(): DownTraversalExprContext {
    return this.getRuleContext(0, DownTraversalExprContext);
  }
  constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterUpAndDownTraversalExpression) {
      listener.enterUpAndDownTraversalExpression(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitUpAndDownTraversalExpression) {
      listener.exitUpAndDownTraversalExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitUpAndDownTraversalExpression) {
      return visitor.visitUpAndDownTraversalExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class UpTraversalExpressionContext extends ExprContext {
  public upTraversalExpr(): UpTraversalExprContext {
    return this.getRuleContext(0, UpTraversalExprContext);
  }
  public traversalAllowedExpr(): TraversalAllowedExprContext {
    return this.getRuleContext(0, TraversalAllowedExprContext);
  }
  constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterUpTraversalExpression) {
      listener.enterUpTraversalExpression(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitUpTraversalExpression) {
      listener.exitUpTraversalExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
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
  public downTraversalExpr(): DownTraversalExprContext {
    return this.getRuleContext(0, DownTraversalExprContext);
  }
  constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterDownTraversalExpression) {
      listener.enterDownTraversalExpression(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitDownTraversalExpression) {
      listener.exitDownTraversalExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitDownTraversalExpression) {
      return visitor.visitDownTraversalExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class NotExpressionContext extends ExprContext {
  public notToken(): NotTokenContext {
    return this.getRuleContext(0, NotTokenContext);
  }
  public postNotOperatorWhitespace(): PostNotOperatorWhitespaceContext {
    return this.getRuleContext(0, PostNotOperatorWhitespaceContext);
  }
  public expr(): ExprContext {
    return this.getRuleContext(0, ExprContext);
  }
  constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterNotExpression) {
      listener.enterNotExpression(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitNotExpression) {
      listener.exitNotExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
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
  public andToken(): AndTokenContext {
    return this.getRuleContext(0, AndTokenContext);
  }
  public postLogicalOperatorWhitespace(): PostLogicalOperatorWhitespaceContext {
    return this.getRuleContext(0, PostLogicalOperatorWhitespaceContext);
  }
  constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterAndExpression) {
      listener.enterAndExpression(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitAndExpression) {
      listener.exitAndExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
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
  public orToken(): OrTokenContext {
    return this.getRuleContext(0, OrTokenContext);
  }
  public postLogicalOperatorWhitespace(): PostLogicalOperatorWhitespaceContext {
    return this.getRuleContext(0, PostLogicalOperatorWhitespaceContext);
  }
  constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterOrExpression) {
      listener.enterOrExpression(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitOrExpression) {
      listener.exitOrExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitOrExpression) {
      return visitor.visitOrExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class IncompleteAndExpressionContext extends ExprContext {
  public expr(): ExprContext {
    return this.getRuleContext(0, ExprContext);
  }
  public andToken(): AndTokenContext {
    return this.getRuleContext(0, AndTokenContext);
  }
  public postLogicalOperatorWhitespace(): PostLogicalOperatorWhitespaceContext {
    return this.getRuleContext(0, PostLogicalOperatorWhitespaceContext);
  }
  constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterIncompleteAndExpression) {
      listener.enterIncompleteAndExpression(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitIncompleteAndExpression) {
      listener.exitIncompleteAndExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitIncompleteAndExpression) {
      return visitor.visitIncompleteAndExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class IncompleteOrExpressionContext extends ExprContext {
  public expr(): ExprContext {
    return this.getRuleContext(0, ExprContext);
  }
  public orToken(): OrTokenContext {
    return this.getRuleContext(0, OrTokenContext);
  }
  public postLogicalOperatorWhitespace(): PostLogicalOperatorWhitespaceContext {
    return this.getRuleContext(0, PostLogicalOperatorWhitespaceContext);
  }
  constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterIncompleteOrExpression) {
      listener.enterIncompleteOrExpression(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitIncompleteOrExpression) {
      listener.exitIncompleteOrExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitIncompleteOrExpression) {
      return visitor.visitIncompleteOrExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class IncompleteNotExpressionContext extends ExprContext {
  public notToken(): NotTokenContext {
    return this.getRuleContext(0, NotTokenContext);
  }
  public postNotOperatorWhitespace(): PostNotOperatorWhitespaceContext {
    return this.getRuleContext(0, PostNotOperatorWhitespaceContext);
  }
  constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterIncompleteNotExpression) {
      listener.enterIncompleteNotExpression(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitIncompleteNotExpression) {
      listener.exitIncompleteNotExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitIncompleteNotExpression) {
      return visitor.visitIncompleteNotExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class AllExpressionContext extends ExprContext {
  public STAR(): TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.STAR, 0);
  }
  public postExpressionWhitespace(): PostExpressionWhitespaceContext {
    return this.getRuleContext(0, PostExpressionWhitespaceContext);
  }
  constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterAllExpression) {
      listener.enterAllExpression(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitAllExpression) {
      listener.exitAllExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitAllExpression) {
      return visitor.visitAllExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class UnmatchedValueContext extends ExprContext {
  public value(): ValueContext {
    return this.getRuleContext(0, ValueContext);
  }
  public postExpressionWhitespace(): PostExpressionWhitespaceContext {
    return this.getRuleContext(0, PostExpressionWhitespaceContext);
  }
  constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterUnmatchedValue) {
      listener.enterUnmatchedValue(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitUnmatchedValue) {
      listener.exitUnmatchedValue(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitUnmatchedValue) {
      return visitor.visitUnmatchedValue(this);
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
    return SelectionAutoCompleteParser.RULE_traversalAllowedExpr;
  }
  public copyFrom(ctx: TraversalAllowedExprContext): void {
    super.copyFrom(ctx);
  }
}
export class AttributeExpressionContext extends TraversalAllowedExprContext {
  public attributeName(): AttributeNameContext {
    return this.getRuleContext(0, AttributeNameContext);
  }
  public colonToken(): ColonTokenContext {
    return this.getRuleContext(0, ColonTokenContext);
  }
  public attributeValue(): AttributeValueContext[];
  public attributeValue(i: number): AttributeValueContext;
  public attributeValue(i?: number): AttributeValueContext | AttributeValueContext[] {
    if (i === undefined) {
      return this.getRuleContexts(AttributeValueContext);
    } else {
      return this.getRuleContext(i, AttributeValueContext);
    }
  }
  public postAttributeValueWhitespace(): PostAttributeValueWhitespaceContext {
    return this.getRuleContext(0, PostAttributeValueWhitespaceContext);
  }
  public EQUAL(): TerminalNode | undefined {
    return this.tryGetToken(SelectionAutoCompleteParser.EQUAL, 0);
  }
  constructor(ctx: TraversalAllowedExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterAttributeExpression) {
      listener.enterAttributeExpression(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitAttributeExpression) {
      listener.exitAttributeExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
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
  public parenthesizedExpr(): ParenthesizedExprContext {
    return this.getRuleContext(0, ParenthesizedExprContext);
  }
  constructor(ctx: TraversalAllowedExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterFunctionCallExpression) {
      listener.enterFunctionCallExpression(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitFunctionCallExpression) {
      listener.exitFunctionCallExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitFunctionCallExpression) {
      return visitor.visitFunctionCallExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class TraversalAllowedParenthesizedExpressionContext extends TraversalAllowedExprContext {
  public parenthesizedExpr(): ParenthesizedExprContext {
    return this.getRuleContext(0, ParenthesizedExprContext);
  }
  constructor(ctx: TraversalAllowedExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterTraversalAllowedParenthesizedExpression) {
      listener.enterTraversalAllowedParenthesizedExpression(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitTraversalAllowedParenthesizedExpression) {
      listener.exitTraversalAllowedParenthesizedExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitTraversalAllowedParenthesizedExpression) {
      return visitor.visitTraversalAllowedParenthesizedExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class IncompleteExpressionContext extends TraversalAllowedExprContext {
  public incompleteExpr(): IncompleteExprContext {
    return this.getRuleContext(0, IncompleteExprContext);
  }
  constructor(ctx: TraversalAllowedExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterIncompleteExpression) {
      listener.enterIncompleteExpression(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitIncompleteExpression) {
      listener.exitIncompleteExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitIncompleteExpression) {
      return visitor.visitIncompleteExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class ParenthesizedExprContext extends ParserRuleContext {
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_parenthesizedExpr;
  }
  public copyFrom(ctx: ParenthesizedExprContext): void {
    super.copyFrom(ctx);
  }
}
export class ParenthesizedExpressionContext extends ParenthesizedExprContext {
  public leftParenToken(): LeftParenTokenContext {
    return this.getRuleContext(0, LeftParenTokenContext);
  }
  public postLogicalOperatorWhitespace(): PostLogicalOperatorWhitespaceContext {
    return this.getRuleContext(0, PostLogicalOperatorWhitespaceContext);
  }
  public expr(): ExprContext {
    return this.getRuleContext(0, ExprContext);
  }
  public rightParenToken(): RightParenTokenContext {
    return this.getRuleContext(0, RightParenTokenContext);
  }
  public postExpressionWhitespace(): PostExpressionWhitespaceContext {
    return this.getRuleContext(0, PostExpressionWhitespaceContext);
  }
  constructor(ctx: ParenthesizedExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterParenthesizedExpression) {
      listener.enterParenthesizedExpression(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitParenthesizedExpression) {
      listener.exitParenthesizedExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitParenthesizedExpression) {
      return visitor.visitParenthesizedExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class IncompleteExprContext extends ParserRuleContext {
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_incompleteExpr;
  }
  public copyFrom(ctx: IncompleteExprContext): void {
    super.copyFrom(ctx);
  }
}
export class IncompleteAttributeExpressionMissingSecondValueContext extends IncompleteExprContext {
  public attributeName(): AttributeNameContext {
    return this.getRuleContext(0, AttributeNameContext);
  }
  public colonToken(): ColonTokenContext {
    return this.getRuleContext(0, ColonTokenContext);
  }
  public attributeValue(): AttributeValueContext {
    return this.getRuleContext(0, AttributeValueContext);
  }
  public EQUAL(): TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.EQUAL, 0);
  }
  public attributeValueWhitespace(): AttributeValueWhitespaceContext {
    return this.getRuleContext(0, AttributeValueWhitespaceContext);
  }
  constructor(ctx: IncompleteExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterIncompleteAttributeExpressionMissingSecondValue) {
      listener.enterIncompleteAttributeExpressionMissingSecondValue(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitIncompleteAttributeExpressionMissingSecondValue) {
      listener.exitIncompleteAttributeExpressionMissingSecondValue(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitIncompleteAttributeExpressionMissingSecondValue) {
      return visitor.visitIncompleteAttributeExpressionMissingSecondValue(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class IncompleteAttributeExpressionMissingValueContext extends IncompleteExprContext {
  public attributeName(): AttributeNameContext {
    return this.getRuleContext(0, AttributeNameContext);
  }
  public colonToken(): ColonTokenContext {
    return this.getRuleContext(0, ColonTokenContext);
  }
  public attributeValueWhitespace(): AttributeValueWhitespaceContext {
    return this.getRuleContext(0, AttributeValueWhitespaceContext);
  }
  constructor(ctx: IncompleteExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterIncompleteAttributeExpressionMissingValue) {
      listener.enterIncompleteAttributeExpressionMissingValue(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitIncompleteAttributeExpressionMissingValue) {
      listener.exitIncompleteAttributeExpressionMissingValue(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitIncompleteAttributeExpressionMissingValue) {
      return visitor.visitIncompleteAttributeExpressionMissingValue(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class ExpressionlessFunctionExpressionContext extends IncompleteExprContext {
  public functionName(): FunctionNameContext {
    return this.getRuleContext(0, FunctionNameContext);
  }
  public expressionLessParenthesizedExpr(): ExpressionLessParenthesizedExprContext {
    return this.getRuleContext(0, ExpressionLessParenthesizedExprContext);
  }
  constructor(ctx: IncompleteExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterExpressionlessFunctionExpression) {
      listener.enterExpressionlessFunctionExpression(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitExpressionlessFunctionExpression) {
      listener.exitExpressionlessFunctionExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitExpressionlessFunctionExpression) {
      return visitor.visitExpressionlessFunctionExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class UnclosedExpressionlessFunctionExpressionContext extends IncompleteExprContext {
  public functionName(): FunctionNameContext {
    return this.getRuleContext(0, FunctionNameContext);
  }
  public leftParenToken(): LeftParenTokenContext {
    return this.getRuleContext(0, LeftParenTokenContext);
  }
  public postLogicalOperatorWhitespace(): PostLogicalOperatorWhitespaceContext {
    return this.getRuleContext(0, PostLogicalOperatorWhitespaceContext);
  }
  constructor(ctx: IncompleteExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterUnclosedExpressionlessFunctionExpression) {
      listener.enterUnclosedExpressionlessFunctionExpression(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitUnclosedExpressionlessFunctionExpression) {
      listener.exitUnclosedExpressionlessFunctionExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitUnclosedExpressionlessFunctionExpression) {
      return visitor.visitUnclosedExpressionlessFunctionExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class UnclosedFunctionExpressionContext extends IncompleteExprContext {
  public functionName(): FunctionNameContext {
    return this.getRuleContext(0, FunctionNameContext);
  }
  public leftParenToken(): LeftParenTokenContext {
    return this.getRuleContext(0, LeftParenTokenContext);
  }
  public expr(): ExprContext {
    return this.getRuleContext(0, ExprContext);
  }
  constructor(ctx: IncompleteExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterUnclosedFunctionExpression) {
      listener.enterUnclosedFunctionExpression(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitUnclosedFunctionExpression) {
      listener.exitUnclosedFunctionExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitUnclosedFunctionExpression) {
      return visitor.visitUnclosedFunctionExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class UnclosedParenthesizedExpressionContext extends IncompleteExprContext {
  public leftParenToken(): LeftParenTokenContext {
    return this.getRuleContext(0, LeftParenTokenContext);
  }
  public postLogicalOperatorWhitespace(): PostLogicalOperatorWhitespaceContext {
    return this.getRuleContext(0, PostLogicalOperatorWhitespaceContext);
  }
  public expr(): ExprContext {
    return this.getRuleContext(0, ExprContext);
  }
  constructor(ctx: IncompleteExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterUnclosedParenthesizedExpression) {
      listener.enterUnclosedParenthesizedExpression(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitUnclosedParenthesizedExpression) {
      listener.exitUnclosedParenthesizedExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitUnclosedParenthesizedExpression) {
      return visitor.visitUnclosedParenthesizedExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class ExpressionlessParenthesizedExpressionWrapperContext extends IncompleteExprContext {
  public expressionLessParenthesizedExpr(): ExpressionLessParenthesizedExprContext {
    return this.getRuleContext(0, ExpressionLessParenthesizedExprContext);
  }
  constructor(ctx: IncompleteExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterExpressionlessParenthesizedExpressionWrapper) {
      listener.enterExpressionlessParenthesizedExpressionWrapper(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitExpressionlessParenthesizedExpressionWrapper) {
      listener.exitExpressionlessParenthesizedExpressionWrapper(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitExpressionlessParenthesizedExpressionWrapper) {
      return visitor.visitExpressionlessParenthesizedExpressionWrapper(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class UnclosedExpressionlessParenthesizedExpressionContext extends IncompleteExprContext {
  public leftParenToken(): LeftParenTokenContext {
    return this.getRuleContext(0, LeftParenTokenContext);
  }
  public postLogicalOperatorWhitespace(): PostLogicalOperatorWhitespaceContext {
    return this.getRuleContext(0, PostLogicalOperatorWhitespaceContext);
  }
  constructor(ctx: IncompleteExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterUnclosedExpressionlessParenthesizedExpression) {
      listener.enterUnclosedExpressionlessParenthesizedExpression(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitUnclosedExpressionlessParenthesizedExpression) {
      listener.exitUnclosedExpressionlessParenthesizedExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitUnclosedExpressionlessParenthesizedExpression) {
      return visitor.visitUnclosedExpressionlessParenthesizedExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class IncompletePlusTraversalExpressionContext extends IncompleteExprContext {
  public PLUS(): TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.PLUS, 0);
  }
  public postNeighborTraversalWhitespace(): PostNeighborTraversalWhitespaceContext {
    return this.getRuleContext(0, PostNeighborTraversalWhitespaceContext);
  }
  public DIGITS(): TerminalNode | undefined {
    return this.tryGetToken(SelectionAutoCompleteParser.DIGITS, 0);
  }
  constructor(ctx: IncompleteExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterIncompletePlusTraversalExpression) {
      listener.enterIncompletePlusTraversalExpression(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitIncompletePlusTraversalExpression) {
      listener.exitIncompletePlusTraversalExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitIncompletePlusTraversalExpression) {
      return visitor.visitIncompletePlusTraversalExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class IncompleteUpTraversalExpressionContext extends IncompleteExprContext {
  public DIGITS(): TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.DIGITS, 0);
  }
  public postDigitsWhitespace(): PostDigitsWhitespaceContext {
    return this.getRuleContext(0, PostDigitsWhitespaceContext);
  }
  constructor(ctx: IncompleteExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterIncompleteUpTraversalExpression) {
      listener.enterIncompleteUpTraversalExpression(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitIncompleteUpTraversalExpression) {
      listener.exitIncompleteUpTraversalExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitIncompleteUpTraversalExpression) {
      return visitor.visitIncompleteUpTraversalExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class IncompletePlusTraversalExpressionMissingValueContext extends IncompleteExprContext {
  public PLUS(): TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.PLUS, 0);
  }
  public value(): ValueContext {
    return this.getRuleContext(0, ValueContext);
  }
  public postExpressionWhitespace(): PostExpressionWhitespaceContext {
    return this.getRuleContext(0, PostExpressionWhitespaceContext);
  }
  constructor(ctx: IncompleteExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterIncompletePlusTraversalExpressionMissingValue) {
      listener.enterIncompletePlusTraversalExpressionMissingValue(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitIncompletePlusTraversalExpressionMissingValue) {
      listener.exitIncompletePlusTraversalExpressionMissingValue(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitIncompletePlusTraversalExpressionMissingValue) {
      return visitor.visitIncompletePlusTraversalExpressionMissingValue(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class IncompleteAttributeExpressionMissingKeyContext extends IncompleteExprContext {
  public colonToken(): ColonTokenContext {
    return this.getRuleContext(0, ColonTokenContext);
  }
  public attributeValue(): AttributeValueContext {
    return this.getRuleContext(0, AttributeValueContext);
  }
  public postExpressionWhitespace(): PostExpressionWhitespaceContext {
    return this.getRuleContext(0, PostExpressionWhitespaceContext);
  }
  constructor(ctx: IncompleteExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterIncompleteAttributeExpressionMissingKey) {
      listener.enterIncompleteAttributeExpressionMissingKey(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitIncompleteAttributeExpressionMissingKey) {
      listener.exitIncompleteAttributeExpressionMissingKey(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitIncompleteAttributeExpressionMissingKey) {
      return visitor.visitIncompleteAttributeExpressionMissingKey(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class ExpressionLessParenthesizedExprContext extends ParserRuleContext {
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_expressionLessParenthesizedExpr;
  }
  public copyFrom(ctx: ExpressionLessParenthesizedExprContext): void {
    super.copyFrom(ctx);
  }
}
export class ExpressionlessParenthesizedExpressionContext extends ExpressionLessParenthesizedExprContext {
  public leftParenToken(): LeftParenTokenContext {
    return this.getRuleContext(0, LeftParenTokenContext);
  }
  public postLogicalOperatorWhitespace(): PostLogicalOperatorWhitespaceContext {
    return this.getRuleContext(0, PostLogicalOperatorWhitespaceContext);
  }
  public rightParenToken(): RightParenTokenContext {
    return this.getRuleContext(0, RightParenTokenContext);
  }
  public postExpressionWhitespace(): PostExpressionWhitespaceContext {
    return this.getRuleContext(0, PostExpressionWhitespaceContext);
  }
  constructor(ctx: ExpressionLessParenthesizedExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterExpressionlessParenthesizedExpression) {
      listener.enterExpressionlessParenthesizedExpression(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitExpressionlessParenthesizedExpression) {
      listener.exitExpressionlessParenthesizedExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitExpressionlessParenthesizedExpression) {
      return visitor.visitExpressionlessParenthesizedExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class UpTraversalExprContext extends ParserRuleContext {
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_upTraversalExpr;
  }
  public copyFrom(ctx: UpTraversalExprContext): void {
    super.copyFrom(ctx);
  }
}
export class UpTraversalContext extends UpTraversalExprContext {
  public upTraversalToken(): UpTraversalTokenContext {
    return this.getRuleContext(0, UpTraversalTokenContext);
  }
  public postUpwardTraversalWhitespace(): PostUpwardTraversalWhitespaceContext {
    return this.getRuleContext(0, PostUpwardTraversalWhitespaceContext);
  }
  constructor(ctx: UpTraversalExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterUpTraversal) {
      listener.enterUpTraversal(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitUpTraversal) {
      listener.exitUpTraversal(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitUpTraversal) {
      return visitor.visitUpTraversal(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class DownTraversalExprContext extends ParserRuleContext {
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_downTraversalExpr;
  }
  public copyFrom(ctx: DownTraversalExprContext): void {
    super.copyFrom(ctx);
  }
}
export class DownTraversalContext extends DownTraversalExprContext {
  public downTraversalToken(): DownTraversalTokenContext {
    return this.getRuleContext(0, DownTraversalTokenContext);
  }
  public postDownwardTraversalWhitespace(): PostDownwardTraversalWhitespaceContext {
    return this.getRuleContext(0, PostDownwardTraversalWhitespaceContext);
  }
  constructor(ctx: DownTraversalExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterDownTraversal) {
      listener.enterDownTraversal(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitDownTraversal) {
      listener.exitDownTraversal(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitDownTraversal) {
      return visitor.visitDownTraversal(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class UpTraversalTokenContext extends ParserRuleContext {
  public PLUS(): TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.PLUS, 0);
  }
  public DIGITS(): TerminalNode | undefined {
    return this.tryGetToken(SelectionAutoCompleteParser.DIGITS, 0);
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_upTraversalToken;
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterUpTraversalToken) {
      listener.enterUpTraversalToken(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitUpTraversalToken) {
      listener.exitUpTraversalToken(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitUpTraversalToken) {
      return visitor.visitUpTraversalToken(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class DownTraversalTokenContext extends ParserRuleContext {
  public PLUS(): TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.PLUS, 0);
  }
  public DIGITS(): TerminalNode | undefined {
    return this.tryGetToken(SelectionAutoCompleteParser.DIGITS, 0);
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_downTraversalToken;
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterDownTraversalToken) {
      listener.enterDownTraversalToken(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitDownTraversalToken) {
      listener.exitDownTraversalToken(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitDownTraversalToken) {
      return visitor.visitDownTraversalToken(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class AttributeNameContext extends ParserRuleContext {
  public IDENTIFIER(): TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.IDENTIFIER, 0);
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_attributeName;
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterAttributeName) {
      listener.enterAttributeName(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitAttributeName) {
      listener.exitAttributeName(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitAttributeName) {
      return visitor.visitAttributeName(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class AttributeValueContext extends ParserRuleContext {
  public value(): ValueContext {
    return this.getRuleContext(0, ValueContext);
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_attributeValue;
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterAttributeValue) {
      listener.enterAttributeValue(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitAttributeValue) {
      listener.exitAttributeValue(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitAttributeValue) {
      return visitor.visitAttributeValue(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class FunctionNameContext extends ParserRuleContext {
  public IDENTIFIER(): TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.IDENTIFIER, 0);
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_functionName;
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterFunctionName) {
      listener.enterFunctionName(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitFunctionName) {
      listener.exitFunctionName(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitFunctionName) {
      return visitor.visitFunctionName(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class OrTokenContext extends ParserRuleContext {
  public OR(): TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.OR, 0);
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_orToken;
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterOrToken) {
      listener.enterOrToken(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitOrToken) {
      listener.exitOrToken(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitOrToken) {
      return visitor.visitOrToken(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class AndTokenContext extends ParserRuleContext {
  public AND(): TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.AND, 0);
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_andToken;
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterAndToken) {
      listener.enterAndToken(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitAndToken) {
      listener.exitAndToken(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitAndToken) {
      return visitor.visitAndToken(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class NotTokenContext extends ParserRuleContext {
  public NOT(): TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.NOT, 0);
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_notToken;
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterNotToken) {
      listener.enterNotToken(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitNotToken) {
      listener.exitNotToken(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitNotToken) {
      return visitor.visitNotToken(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class ColonTokenContext extends ParserRuleContext {
  public COLON(): TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.COLON, 0);
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_colonToken;
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterColonToken) {
      listener.enterColonToken(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitColonToken) {
      listener.exitColonToken(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitColonToken) {
      return visitor.visitColonToken(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class LeftParenTokenContext extends ParserRuleContext {
  public LPAREN(): TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.LPAREN, 0);
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_leftParenToken;
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterLeftParenToken) {
      listener.enterLeftParenToken(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitLeftParenToken) {
      listener.exitLeftParenToken(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitLeftParenToken) {
      return visitor.visitLeftParenToken(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class RightParenTokenContext extends ParserRuleContext {
  public RPAREN(): TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.RPAREN, 0);
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_rightParenToken;
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterRightParenToken) {
      listener.enterRightParenToken(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitRightParenToken) {
      listener.exitRightParenToken(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitRightParenToken) {
      return visitor.visitRightParenToken(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class AttributeValueWhitespaceContext extends ParserRuleContext {
  public WS(): TerminalNode[];
  public WS(i: number): TerminalNode;
  public WS(i?: number): TerminalNode | TerminalNode[] {
    if (i === undefined) {
      return this.getTokens(SelectionAutoCompleteParser.WS);
    } else {
      return this.getToken(SelectionAutoCompleteParser.WS, i);
    }
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_attributeValueWhitespace;
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterAttributeValueWhitespace) {
      listener.enterAttributeValueWhitespace(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitAttributeValueWhitespace) {
      listener.exitAttributeValueWhitespace(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitAttributeValueWhitespace) {
      return visitor.visitAttributeValueWhitespace(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class PostAttributeValueWhitespaceContext extends ParserRuleContext {
  public WS(): TerminalNode[];
  public WS(i: number): TerminalNode;
  public WS(i?: number): TerminalNode | TerminalNode[] {
    if (i === undefined) {
      return this.getTokens(SelectionAutoCompleteParser.WS);
    } else {
      return this.getToken(SelectionAutoCompleteParser.WS, i);
    }
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_postAttributeValueWhitespace;
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterPostAttributeValueWhitespace) {
      listener.enterPostAttributeValueWhitespace(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitPostAttributeValueWhitespace) {
      listener.exitPostAttributeValueWhitespace(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitPostAttributeValueWhitespace) {
      return visitor.visitPostAttributeValueWhitespace(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class PostExpressionWhitespaceContext extends ParserRuleContext {
  public WS(): TerminalNode[];
  public WS(i: number): TerminalNode;
  public WS(i?: number): TerminalNode | TerminalNode[] {
    if (i === undefined) {
      return this.getTokens(SelectionAutoCompleteParser.WS);
    } else {
      return this.getToken(SelectionAutoCompleteParser.WS, i);
    }
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_postExpressionWhitespace;
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterPostExpressionWhitespace) {
      listener.enterPostExpressionWhitespace(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitPostExpressionWhitespace) {
      listener.exitPostExpressionWhitespace(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitPostExpressionWhitespace) {
      return visitor.visitPostExpressionWhitespace(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class PostNotOperatorWhitespaceContext extends ParserRuleContext {
  public WS(): TerminalNode[];
  public WS(i: number): TerminalNode;
  public WS(i?: number): TerminalNode | TerminalNode[] {
    if (i === undefined) {
      return this.getTokens(SelectionAutoCompleteParser.WS);
    } else {
      return this.getToken(SelectionAutoCompleteParser.WS, i);
    }
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_postNotOperatorWhitespace;
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterPostNotOperatorWhitespace) {
      listener.enterPostNotOperatorWhitespace(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitPostNotOperatorWhitespace) {
      listener.exitPostNotOperatorWhitespace(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitPostNotOperatorWhitespace) {
      return visitor.visitPostNotOperatorWhitespace(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class PostLogicalOperatorWhitespaceContext extends ParserRuleContext {
  public WS(): TerminalNode[];
  public WS(i: number): TerminalNode;
  public WS(i?: number): TerminalNode | TerminalNode[] {
    if (i === undefined) {
      return this.getTokens(SelectionAutoCompleteParser.WS);
    } else {
      return this.getToken(SelectionAutoCompleteParser.WS, i);
    }
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_postLogicalOperatorWhitespace;
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterPostLogicalOperatorWhitespace) {
      listener.enterPostLogicalOperatorWhitespace(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitPostLogicalOperatorWhitespace) {
      listener.exitPostLogicalOperatorWhitespace(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitPostLogicalOperatorWhitespace) {
      return visitor.visitPostLogicalOperatorWhitespace(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class PostNeighborTraversalWhitespaceContext extends ParserRuleContext {
  public WS(): TerminalNode[];
  public WS(i: number): TerminalNode;
  public WS(i?: number): TerminalNode | TerminalNode[] {
    if (i === undefined) {
      return this.getTokens(SelectionAutoCompleteParser.WS);
    } else {
      return this.getToken(SelectionAutoCompleteParser.WS, i);
    }
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_postNeighborTraversalWhitespace;
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterPostNeighborTraversalWhitespace) {
      listener.enterPostNeighborTraversalWhitespace(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitPostNeighborTraversalWhitespace) {
      listener.exitPostNeighborTraversalWhitespace(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitPostNeighborTraversalWhitespace) {
      return visitor.visitPostNeighborTraversalWhitespace(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class PostUpwardTraversalWhitespaceContext extends ParserRuleContext {
  public WS(): TerminalNode[];
  public WS(i: number): TerminalNode;
  public WS(i?: number): TerminalNode | TerminalNode[] {
    if (i === undefined) {
      return this.getTokens(SelectionAutoCompleteParser.WS);
    } else {
      return this.getToken(SelectionAutoCompleteParser.WS, i);
    }
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_postUpwardTraversalWhitespace;
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterPostUpwardTraversalWhitespace) {
      listener.enterPostUpwardTraversalWhitespace(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitPostUpwardTraversalWhitespace) {
      listener.exitPostUpwardTraversalWhitespace(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitPostUpwardTraversalWhitespace) {
      return visitor.visitPostUpwardTraversalWhitespace(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class PostDownwardTraversalWhitespaceContext extends ParserRuleContext {
  public WS(): TerminalNode[];
  public WS(i: number): TerminalNode;
  public WS(i?: number): TerminalNode | TerminalNode[] {
    if (i === undefined) {
      return this.getTokens(SelectionAutoCompleteParser.WS);
    } else {
      return this.getToken(SelectionAutoCompleteParser.WS, i);
    }
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_postDownwardTraversalWhitespace;
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterPostDownwardTraversalWhitespace) {
      listener.enterPostDownwardTraversalWhitespace(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitPostDownwardTraversalWhitespace) {
      listener.exitPostDownwardTraversalWhitespace(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitPostDownwardTraversalWhitespace) {
      return visitor.visitPostDownwardTraversalWhitespace(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class PostDigitsWhitespaceContext extends ParserRuleContext {
  public WS(): TerminalNode[];
  public WS(i: number): TerminalNode;
  public WS(i?: number): TerminalNode | TerminalNode[] {
    if (i === undefined) {
      return this.getTokens(SelectionAutoCompleteParser.WS);
    } else {
      return this.getToken(SelectionAutoCompleteParser.WS, i);
    }
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_postDigitsWhitespace;
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterPostDigitsWhitespace) {
      listener.enterPostDigitsWhitespace(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitPostDigitsWhitespace) {
      listener.exitPostDigitsWhitespace(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitPostDigitsWhitespace) {
      return visitor.visitPostDigitsWhitespace(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class ValueContext extends ParserRuleContext {
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_value;
  }
  public copyFrom(ctx: ValueContext): void {
    super.copyFrom(ctx);
  }
}
export class QuotedStringValueContext extends ValueContext {
  public QUOTED_STRING(): TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.QUOTED_STRING, 0);
  }
  constructor(ctx: ValueContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterQuotedStringValue) {
      listener.enterQuotedStringValue(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitQuotedStringValue) {
      listener.exitQuotedStringValue(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitQuotedStringValue) {
      return visitor.visitQuotedStringValue(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class IncompleteLeftQuotedStringValueContext extends ValueContext {
  public INCOMPLETE_LEFT_QUOTED_STRING(): TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.INCOMPLETE_LEFT_QUOTED_STRING, 0);
  }
  constructor(ctx: ValueContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterIncompleteLeftQuotedStringValue) {
      listener.enterIncompleteLeftQuotedStringValue(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitIncompleteLeftQuotedStringValue) {
      listener.exitIncompleteLeftQuotedStringValue(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitIncompleteLeftQuotedStringValue) {
      return visitor.visitIncompleteLeftQuotedStringValue(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class IncompleteRightQuotedStringValueContext extends ValueContext {
  public INCOMPLETE_RIGHT_QUOTED_STRING(): TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.INCOMPLETE_RIGHT_QUOTED_STRING, 0);
  }
  constructor(ctx: ValueContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterIncompleteRightQuotedStringValue) {
      listener.enterIncompleteRightQuotedStringValue(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitIncompleteRightQuotedStringValue) {
      listener.exitIncompleteRightQuotedStringValue(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitIncompleteRightQuotedStringValue) {
      return visitor.visitIncompleteRightQuotedStringValue(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class UnquotedStringValueContext extends ValueContext {
  public IDENTIFIER(): TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.IDENTIFIER, 0);
  }
  constructor(ctx: ValueContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterUnquotedStringValue) {
      listener.enterUnquotedStringValue(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitUnquotedStringValue) {
      listener.exitUnquotedStringValue(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitUnquotedStringValue) {
      return visitor.visitUnquotedStringValue(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
