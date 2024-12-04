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
  public static readonly COLON = 6;
  public static readonly LPAREN = 7;
  public static readonly RPAREN = 8;
  public static readonly EQUAL = 9;
  public static readonly QUOTED_STRING = 10;
  public static readonly INCOMPLETE_LEFT_QUOTED_STRING = 11;
  public static readonly INCOMPLETE_RIGHT_QUOTED_STRING = 12;
  public static readonly IDENTIFIER = 13;
  public static readonly WS = 14;
  public static readonly RULE_start = 0;
  public static readonly RULE_expr = 1;
  public static readonly RULE_traversalAllowedExpr = 2;
  public static readonly RULE_parenthesizedExpr = 3;
  public static readonly RULE_incompleteExpressionsWrapper = 4;
  public static readonly RULE_expressionLessParenthesizedExpr = 5;
  public static readonly RULE_upTraversalExp = 6;
  public static readonly RULE_downTraversalExp = 7;
  public static readonly RULE_traversal = 8;
  public static readonly RULE_attributeName = 9;
  public static readonly RULE_attributeValue = 10;
  public static readonly RULE_functionName = 11;
  public static readonly RULE_orToken = 12;
  public static readonly RULE_andToken = 13;
  public static readonly RULE_notToken = 14;
  public static readonly RULE_colonToken = 15;
  public static readonly RULE_leftParenToken = 16;
  public static readonly RULE_rightParenToken = 17;
  public static readonly RULE_afterExpressionWhitespace = 18;
  public static readonly RULE_afterLogicalOperatorWhitespace = 19;
  public static readonly RULE_value = 20;
  // tslint:disable:no-trailing-whitespace
  public static readonly ruleNames: string[] = [
    'start',
    'expr',
    'traversalAllowedExpr',
    'parenthesizedExpr',
    'incompleteExpressionsWrapper',
    'expressionLessParenthesizedExpr',
    'upTraversalExp',
    'downTraversalExp',
    'traversal',
    'attributeName',
    'attributeValue',
    'functionName',
    'orToken',
    'andToken',
    'notToken',
    'colonToken',
    'leftParenToken',
    'rightParenToken',
    'afterExpressionWhitespace',
    'afterLogicalOperatorWhitespace',
    'value',
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
        this.state = 42;
        this.expr(0);
        this.state = 43;
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
        this.state = 75;
        this._errHandler.sync(this);
        switch (this.interpreter.adaptivePredict(this._input, 0, this._ctx)) {
          case 1:
            {
              _localctx = new TraversalAllowedExpressionContext(_localctx);
              this._ctx = _localctx;
              _prevctx = _localctx;

              this.state = 46;
              this.traversalAllowedExpr();
              this.state = 47;
              this.afterExpressionWhitespace();
            }
            break;

          case 2:
            {
              _localctx = new UpAndDownTraversalExpressionContext(_localctx);
              this._ctx = _localctx;
              _prevctx = _localctx;
              this.state = 49;
              this.upTraversalExp();
              this.state = 50;
              this.traversalAllowedExpr();
              this.state = 51;
              this.downTraversalExp();
              this.state = 52;
              this.afterExpressionWhitespace();
            }
            break;

          case 3:
            {
              _localctx = new UpTraversalExpressionContext(_localctx);
              this._ctx = _localctx;
              _prevctx = _localctx;
              this.state = 54;
              this.upTraversalExp();
              this.state = 55;
              this.traversalAllowedExpr();
              this.state = 56;
              this.afterExpressionWhitespace();
            }
            break;

          case 4:
            {
              _localctx = new DownTraversalExpressionContext(_localctx);
              this._ctx = _localctx;
              _prevctx = _localctx;
              this.state = 58;
              this.traversalAllowedExpr();
              this.state = 59;
              this.downTraversalExp();
              this.state = 60;
              this.afterExpressionWhitespace();
            }
            break;

          case 5:
            {
              _localctx = new NotExpressionContext(_localctx);
              this._ctx = _localctx;
              _prevctx = _localctx;
              this.state = 62;
              this.notToken();
              this.state = 63;
              this.afterLogicalOperatorWhitespace();
              this.state = 64;
              this.expr(0);
              this.state = 65;
              this.afterExpressionWhitespace();
            }
            break;

          case 6:
            {
              _localctx = new IncompleteNotExpressionContext(_localctx);
              this._ctx = _localctx;
              _prevctx = _localctx;
              this.state = 67;
              this.notToken();
              this.state = 68;
              this.afterLogicalOperatorWhitespace();
            }
            break;

          case 7:
            {
              _localctx = new AllExpressionContext(_localctx);
              this._ctx = _localctx;
              _prevctx = _localctx;
              this.state = 70;
              this.match(SelectionAutoCompleteParser.STAR);
              this.state = 71;
              this.afterExpressionWhitespace();
            }
            break;

          case 8:
            {
              _localctx = new UnmatchedValueContext(_localctx);
              this._ctx = _localctx;
              _prevctx = _localctx;
              this.state = 72;
              this.value();
              this.state = 73;
              this.afterExpressionWhitespace();
            }
            break;
        }
        this._ctx._stop = this._input.tryLT(-1);
        this.state = 108;
        this._errHandler.sync(this);
        _alt = this.interpreter.adaptivePredict(this._input, 2, this._ctx);
        while (_alt !== 2 && _alt !== ATN.INVALID_ALT_NUMBER) {
          if (_alt === 1) {
            if (this._parseListeners != null) {
              this.triggerExitRuleEvent();
            }
            _prevctx = _localctx;
            {
              this.state = 106;
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
                    this.state = 77;
                    if (!this.precpred(this._ctx, 8)) {
                      throw this.createFailedPredicateException('this.precpred(this._ctx, 8)');
                    }
                    this.state = 78;
                    this.afterExpressionWhitespace();
                    this.state = 79;
                    this.andToken();
                    this.state = 80;
                    this.afterLogicalOperatorWhitespace();
                    this.state = 81;
                    this.expr(0);
                    this.state = 82;
                    this.afterExpressionWhitespace();
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
                    this.state = 84;
                    if (!this.precpred(this._ctx, 7)) {
                      throw this.createFailedPredicateException('this.precpred(this._ctx, 7)');
                    }
                    this.state = 85;
                    this.afterExpressionWhitespace();
                    this.state = 86;
                    this.orToken();
                    this.state = 87;
                    this.afterLogicalOperatorWhitespace();
                    this.state = 88;
                    this.expr(0);
                    this.state = 89;
                    this.afterExpressionWhitespace();
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
                    this.state = 91;
                    if (!this.precpred(this._ctx, 6)) {
                      throw this.createFailedPredicateException('this.precpred(this._ctx, 6)');
                    }
                    this.state = 92;
                    this.afterExpressionWhitespace();
                    this.state = 93;
                    this.andToken();
                    this.state = 94;
                    this.afterLogicalOperatorWhitespace();
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
                    this.state = 96;
                    if (!this.precpred(this._ctx, 5)) {
                      throw this.createFailedPredicateException('this.precpred(this._ctx, 5)');
                    }
                    this.state = 97;
                    this.afterExpressionWhitespace();
                    this.state = 98;
                    this.orToken();
                    this.state = 99;
                    this.afterLogicalOperatorWhitespace();
                  }
                  break;

                case 5:
                  {
                    _localctx = new UnmatchedExpressionContinuationContext(
                      new ExprContext(_parentctx, _parentState),
                    );
                    this.pushNewRecursionContext(
                      _localctx,
                      _startState,
                      SelectionAutoCompleteParser.RULE_expr,
                    );
                    this.state = 101;
                    if (!this.precpred(this._ctx, 3)) {
                      throw this.createFailedPredicateException('this.precpred(this._ctx, 3)');
                    }
                    this.state = 102;
                    this.afterExpressionWhitespace();
                    this.state = 103;
                    this.value();
                    this.state = 104;
                    this.afterLogicalOperatorWhitespace();
                  }
                  break;
              }
            }
          }
          this.state = 110;
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
      this.state = 120;
      this._errHandler.sync(this);
      switch (this.interpreter.adaptivePredict(this._input, 3, this._ctx)) {
        case 1:
          _localctx = new AttributeExpressionContext(_localctx);
          this.enterOuterAlt(_localctx, 1);
          {
            this.state = 111;
            this.attributeName();
            this.state = 112;
            this.colonToken();
            this.state = 113;
            this.attributeValue();
          }
          break;

        case 2:
          _localctx = new FunctionCallExpressionContext(_localctx);
          this.enterOuterAlt(_localctx, 2);
          {
            this.state = 115;
            this.functionName();
            this.state = 116;
            this.parenthesizedExpr();
          }
          break;

        case 3:
          _localctx = new ParenthesizedExpressionWrapperContext(_localctx);
          this.enterOuterAlt(_localctx, 3);
          {
            this.state = 118;
            this.parenthesizedExpr();
          }
          break;

        case 4:
          _localctx = new IncompleteExpressionContext(_localctx);
          this.enterOuterAlt(_localctx, 4);
          {
            this.state = 119;
            this.incompleteExpressionsWrapper();
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
        this.state = 122;
        this.leftParenToken();
        this.state = 123;
        this.expr(0);
        this.state = 124;
        this.rightParenToken();
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
  public incompleteExpressionsWrapper(): IncompleteExpressionsWrapperContext {
    let _localctx: IncompleteExpressionsWrapperContext = new IncompleteExpressionsWrapperContext(
      this._ctx,
      this.state,
    );
    this.enterRule(_localctx, 8, SelectionAutoCompleteParser.RULE_incompleteExpressionsWrapper);
    try {
      let _alt: number;
      this.state = 152;
      this._errHandler.sync(this);
      switch (this.interpreter.adaptivePredict(this._input, 5, this._ctx)) {
        case 1:
          _localctx = new IncompleteAttributeExpressionMissingValueContext(_localctx);
          this.enterOuterAlt(_localctx, 1);
          {
            this.state = 126;
            this.attributeName();
            this.state = 127;
            this.colonToken();
          }
          break;

        case 2:
          _localctx = new ExpressionlessFunctionExpressionContext(_localctx);
          this.enterOuterAlt(_localctx, 2);
          {
            this.state = 129;
            this.functionName();
            this.state = 130;
            this.expressionLessParenthesizedExpr();
          }
          break;

        case 3:
          _localctx = new UnclosedExpressionlessFunctionExpressionContext(_localctx);
          this.enterOuterAlt(_localctx, 3);
          {
            this.state = 132;
            this.functionName();
            this.state = 133;
            this.leftParenToken();
          }
          break;

        case 4:
          _localctx = new UnclosedFunctionExpressionContext(_localctx);
          this.enterOuterAlt(_localctx, 4);
          {
            this.state = 135;
            this.functionName();
            this.state = 136;
            this.leftParenToken();
            this.state = 137;
            this.expr(0);
          }
          break;

        case 5:
          _localctx = new UnclosedParenthesizedExpressionContext(_localctx);
          this.enterOuterAlt(_localctx, 5);
          {
            this.state = 139;
            this.leftParenToken();
            this.state = 140;
            this.expr(0);
          }
          break;

        case 6:
          _localctx = new ExpressionlessParenthesizedExpressionWrapperContext(_localctx);
          this.enterOuterAlt(_localctx, 6);
          {
            this.state = 142;
            this.expressionLessParenthesizedExpr();
          }
          break;

        case 7:
          _localctx = new UnclosedExpressionlessParenthesizedExpressionContext(_localctx);
          this.enterOuterAlt(_localctx, 7);
          {
            this.state = 143;
            this.leftParenToken();
          }
          break;

        case 8:
          _localctx = new IncompleteTraversalExpressionContext(_localctx);
          this.enterOuterAlt(_localctx, 8);
          {
            this.state = 145;
            this._errHandler.sync(this);
            _alt = 1;
            do {
              switch (_alt) {
                case 1:
                  {
                    {
                      this.state = 144;
                      this.match(SelectionAutoCompleteParser.PLUS);
                    }
                  }
                  break;
                default:
                  throw new NoViableAltException(this);
              }
              this.state = 147;
              this._errHandler.sync(this);
              _alt = this.interpreter.adaptivePredict(this._input, 4, this._ctx);
            } while (_alt !== 2 && _alt !== ATN.INVALID_ALT_NUMBER);
          }
          break;

        case 9:
          _localctx = new IncompleteAttributeExpressionMissingKeyContext(_localctx);
          this.enterOuterAlt(_localctx, 9);
          {
            this.state = 149;
            this.colonToken();
            this.state = 150;
            this.attributeValue();
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
        this.state = 154;
        this.leftParenToken();
        this.state = 155;
        this.rightParenToken();
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
  public upTraversalExp(): UpTraversalExpContext {
    let _localctx: UpTraversalExpContext = new UpTraversalExpContext(this._ctx, this.state);
    this.enterRule(_localctx, 12, SelectionAutoCompleteParser.RULE_upTraversalExp);
    try {
      _localctx = new UpTraversalContext(_localctx);
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 157;
        this.traversal();
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
  public downTraversalExp(): DownTraversalExpContext {
    let _localctx: DownTraversalExpContext = new DownTraversalExpContext(this._ctx, this.state);
    this.enterRule(_localctx, 14, SelectionAutoCompleteParser.RULE_downTraversalExp);
    try {
      _localctx = new DownTraversalContext(_localctx);
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 159;
        this.traversal();
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
    this.enterRule(_localctx, 16, SelectionAutoCompleteParser.RULE_traversal);
    try {
      let _alt: number;
      this.state = 167;
      this._errHandler.sync(this);
      switch (this._input.LA(1)) {
        case SelectionAutoCompleteParser.STAR:
          this.enterOuterAlt(_localctx, 1);
          {
            this.state = 161;
            this.match(SelectionAutoCompleteParser.STAR);
          }
          break;
        case SelectionAutoCompleteParser.PLUS:
          this.enterOuterAlt(_localctx, 2);
          {
            this.state = 163;
            this._errHandler.sync(this);
            _alt = 1;
            do {
              switch (_alt) {
                case 1:
                  {
                    {
                      this.state = 162;
                      this.match(SelectionAutoCompleteParser.PLUS);
                    }
                  }
                  break;
                default:
                  throw new NoViableAltException(this);
              }
              this.state = 165;
              this._errHandler.sync(this);
              _alt = this.interpreter.adaptivePredict(this._input, 6, this._ctx);
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
  public attributeName(): AttributeNameContext {
    const _localctx: AttributeNameContext = new AttributeNameContext(this._ctx, this.state);
    this.enterRule(_localctx, 18, SelectionAutoCompleteParser.RULE_attributeName);
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 169;
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
    this.enterRule(_localctx, 20, SelectionAutoCompleteParser.RULE_attributeValue);
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 171;
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
    this.enterRule(_localctx, 22, SelectionAutoCompleteParser.RULE_functionName);
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 173;
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
    this.enterRule(_localctx, 24, SelectionAutoCompleteParser.RULE_orToken);
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 175;
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
    this.enterRule(_localctx, 26, SelectionAutoCompleteParser.RULE_andToken);
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 177;
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
    this.enterRule(_localctx, 28, SelectionAutoCompleteParser.RULE_notToken);
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 179;
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
    this.enterRule(_localctx, 30, SelectionAutoCompleteParser.RULE_colonToken);
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 181;
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
    this.enterRule(_localctx, 32, SelectionAutoCompleteParser.RULE_leftParenToken);
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 183;
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
    this.enterRule(_localctx, 34, SelectionAutoCompleteParser.RULE_rightParenToken);
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 185;
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
  public afterExpressionWhitespace(): AfterExpressionWhitespaceContext {
    const _localctx: AfterExpressionWhitespaceContext = new AfterExpressionWhitespaceContext(
      this._ctx,
      this.state,
    );
    this.enterRule(_localctx, 36, SelectionAutoCompleteParser.RULE_afterExpressionWhitespace);
    try {
      let _alt: number;
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 190;
        this._errHandler.sync(this);
        _alt = this.interpreter.adaptivePredict(this._input, 8, this._ctx);
        while (_alt !== 2 && _alt !== ATN.INVALID_ALT_NUMBER) {
          if (_alt === 1) {
            {
              {
                this.state = 187;
                this.match(SelectionAutoCompleteParser.WS);
              }
            }
          }
          this.state = 192;
          this._errHandler.sync(this);
          _alt = this.interpreter.adaptivePredict(this._input, 8, this._ctx);
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
  public afterLogicalOperatorWhitespace(): AfterLogicalOperatorWhitespaceContext {
    const _localctx: AfterLogicalOperatorWhitespaceContext =
      new AfterLogicalOperatorWhitespaceContext(this._ctx, this.state);
    this.enterRule(_localctx, 38, SelectionAutoCompleteParser.RULE_afterLogicalOperatorWhitespace);
    try {
      let _alt: number;
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 196;
        this._errHandler.sync(this);
        _alt = this.interpreter.adaptivePredict(this._input, 9, this._ctx);
        while (_alt !== 2 && _alt !== ATN.INVALID_ALT_NUMBER) {
          if (_alt === 1) {
            {
              {
                this.state = 193;
                this.match(SelectionAutoCompleteParser.WS);
              }
            }
          }
          this.state = 198;
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
  public value(): ValueContext {
    let _localctx: ValueContext = new ValueContext(this._ctx, this.state);
    this.enterRule(_localctx, 40, SelectionAutoCompleteParser.RULE_value);
    try {
      this.state = 203;
      this._errHandler.sync(this);
      switch (this._input.LA(1)) {
        case SelectionAutoCompleteParser.QUOTED_STRING:
          _localctx = new QuotedStringValueContext(_localctx);
          this.enterOuterAlt(_localctx, 1);
          {
            this.state = 199;
            this.match(SelectionAutoCompleteParser.QUOTED_STRING);
          }
          break;
        case SelectionAutoCompleteParser.INCOMPLETE_LEFT_QUOTED_STRING:
          _localctx = new IncompleteLeftQuotedStringValueContext(_localctx);
          this.enterOuterAlt(_localctx, 2);
          {
            this.state = 200;
            this.match(SelectionAutoCompleteParser.INCOMPLETE_LEFT_QUOTED_STRING);
          }
          break;
        case SelectionAutoCompleteParser.INCOMPLETE_RIGHT_QUOTED_STRING:
          _localctx = new IncompleteRightQuotedStringValueContext(_localctx);
          this.enterOuterAlt(_localctx, 3);
          {
            this.state = 201;
            this.match(SelectionAutoCompleteParser.INCOMPLETE_RIGHT_QUOTED_STRING);
          }
          break;
        case SelectionAutoCompleteParser.IDENTIFIER:
          _localctx = new UnquotedStringValueContext(_localctx);
          this.enterOuterAlt(_localctx, 4);
          {
            this.state = 202;
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
        return this.precpred(this._ctx, 8);

      case 1:
        return this.precpred(this._ctx, 7);

      case 2:
        return this.precpred(this._ctx, 6);

      case 3:
        return this.precpred(this._ctx, 5);

      case 4:
        return this.precpred(this._ctx, 3);
    }
    return true;
  }

  public static readonly _serializedATN: string =
    '\x03\uC91D\uCABA\u058D\uAFBA\u4F53\u0607\uEA8B\uC241\x03\x10\xD0\x04\x02' +
    '\t\x02\x04\x03\t\x03\x04\x04\t\x04\x04\x05\t\x05\x04\x06\t\x06\x04\x07' +
    '\t\x07\x04\b\t\b\x04\t\t\t\x04\n\t\n\x04\v\t\v\x04\f\t\f\x04\r\t\r\x04' +
    '\x0E\t\x0E\x04\x0F\t\x0F\x04\x10\t\x10\x04\x11\t\x11\x04\x12\t\x12\x04' +
    '\x13\t\x13\x04\x14\t\x14\x04\x15\t\x15\x04\x16\t\x16\x03\x02\x03\x02\x03' +
    '\x02\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03' +
    '\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03' +
    '\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03' +
    '\x03\x03\x03\x03\x03\x03\x03\x05\x03N\n\x03\x03\x03\x03\x03\x03\x03\x03' +
    '\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03' +
    '\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03' +
    '\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x07\x03m' +
    '\n\x03\f\x03\x0E\x03p\v\x03\x03\x04\x03\x04\x03\x04\x03\x04\x03\x04\x03' +
    '\x04\x03\x04\x03\x04\x03\x04\x05\x04{\n\x04\x03\x05\x03\x05\x03\x05\x03' +
    '\x05\x03\x06\x03\x06\x03\x06\x03\x06\x03\x06\x03\x06\x03\x06\x03\x06\x03' +
    '\x06\x03\x06\x03\x06\x03\x06\x03\x06\x03\x06\x03\x06\x03\x06\x03\x06\x03' +
    '\x06\x03\x06\x06\x06\x94\n\x06\r\x06\x0E\x06\x95\x03\x06\x03\x06\x03\x06' +
    '\x05\x06\x9B\n\x06\x03\x07\x03\x07\x03\x07\x03\b\x03\b\x03\t\x03\t\x03' +
    '\n\x03\n\x06\n\xA6\n\n\r\n\x0E\n\xA7\x05\n\xAA\n\n\x03\v\x03\v\x03\f\x03' +
    '\f\x03\r\x03\r\x03\x0E\x03\x0E\x03\x0F\x03\x0F\x03\x10\x03\x10\x03\x11' +
    '\x03\x11\x03\x12\x03\x12\x03\x13\x03\x13\x03\x14\x07\x14\xBF\n\x14\f\x14' +
    '\x0E\x14\xC2\v\x14\x03\x15\x07\x15\xC5\n\x15\f\x15\x0E\x15\xC8\v\x15\x03' +
    '\x16\x03\x16\x03\x16\x03\x16\x05\x16\xCE\n\x16\x03\x16\x02\x02\x03\x04' +
    '\x17\x02\x02\x04\x02\x06\x02\b\x02\n\x02\f\x02\x0E\x02\x10\x02\x12\x02' +
    '\x14\x02\x16\x02\x18\x02\x1A\x02\x1C\x02\x1E\x02 \x02"\x02$\x02&\x02' +
    '(\x02*\x02\x02\x02\x02\xD9\x02,\x03\x02\x02\x02\x04M\x03\x02\x02\x02\x06' +
    'z\x03\x02\x02\x02\b|\x03\x02\x02\x02\n\x9A\x03\x02\x02\x02\f\x9C\x03\x02' +
    '\x02\x02\x0E\x9F\x03\x02\x02\x02\x10\xA1\x03\x02\x02\x02\x12\xA9\x03\x02' +
    '\x02\x02\x14\xAB\x03\x02\x02\x02\x16\xAD\x03\x02\x02\x02\x18\xAF\x03\x02' +
    '\x02\x02\x1A\xB1\x03\x02\x02\x02\x1C\xB3\x03\x02\x02\x02\x1E\xB5\x03\x02' +
    '\x02\x02 \xB7\x03\x02\x02\x02"\xB9\x03\x02\x02\x02$\xBB\x03\x02\x02\x02' +
    '&\xC0\x03\x02\x02\x02(\xC6\x03\x02\x02\x02*\xCD\x03\x02\x02\x02,-\x05' +
    '\x04\x03\x02-.\x07\x02\x02\x03.\x03\x03\x02\x02\x02/0\b\x03\x01\x0201' +
    '\x05\x06\x04\x0212\x05&\x14\x022N\x03\x02\x02\x0234\x05\x0E\b\x0245\x05' +
    '\x06\x04\x0256\x05\x10\t\x0267\x05&\x14\x027N\x03\x02\x02\x0289\x05\x0E' +
    '\b\x029:\x05\x06\x04\x02:;\x05&\x14\x02;N\x03\x02\x02\x02<=\x05\x06\x04' +
    '\x02=>\x05\x10\t\x02>?\x05&\x14\x02?N\x03\x02\x02\x02@A\x05\x1E\x10\x02' +
    'AB\x05(\x15\x02BC\x05\x04\x03\x02CD\x05&\x14\x02DN\x03\x02\x02\x02EF\x05' +
    '\x1E\x10\x02FG\x05(\x15\x02GN\x03\x02\x02\x02HI\x07\x06\x02\x02IN\x05' +
    '&\x14\x02JK\x05*\x16\x02KL\x05&\x14\x02LN\x03\x02\x02\x02M/\x03\x02\x02' +
    '\x02M3\x03\x02\x02\x02M8\x03\x02\x02\x02M<\x03\x02\x02\x02M@\x03\x02\x02' +
    '\x02ME\x03\x02\x02\x02MH\x03\x02\x02\x02MJ\x03\x02\x02\x02Nn\x03\x02\x02' +
    '\x02OP\f\n\x02\x02PQ\x05&\x14\x02QR\x05\x1C\x0F\x02RS\x05(\x15\x02ST\x05' +
    '\x04\x03\x02TU\x05&\x14\x02Um\x03\x02\x02\x02VW\f\t\x02\x02WX\x05&\x14' +
    '\x02XY\x05\x1A\x0E\x02YZ\x05(\x15\x02Z[\x05\x04\x03\x02[\\\x05&\x14\x02' +
    '\\m\x03\x02\x02\x02]^\f\b\x02\x02^_\x05&\x14\x02_`\x05\x1C\x0F\x02`a\x05' +
    '(\x15\x02am\x03\x02\x02\x02bc\f\x07\x02\x02cd\x05&\x14\x02de\x05\x1A\x0E' +
    '\x02ef\x05(\x15\x02fm\x03\x02\x02\x02gh\f\x05\x02\x02hi\x05&\x14\x02i' +
    'j\x05*\x16\x02jk\x05(\x15\x02km\x03\x02\x02\x02lO\x03\x02\x02\x02lV\x03' +
    '\x02\x02\x02l]\x03\x02\x02\x02lb\x03\x02\x02\x02lg\x03\x02\x02\x02mp\x03' +
    '\x02\x02\x02nl\x03\x02\x02\x02no\x03\x02\x02\x02o\x05\x03\x02\x02\x02' +
    'pn\x03\x02\x02\x02qr\x05\x14\v\x02rs\x05 \x11\x02st\x05\x16\f\x02t{\x03' +
    '\x02\x02\x02uv\x05\x18\r\x02vw\x05\b\x05\x02w{\x03\x02\x02\x02x{\x05\b' +
    '\x05\x02y{\x05\n\x06\x02zq\x03\x02\x02\x02zu\x03\x02\x02\x02zx\x03\x02' +
    '\x02\x02zy\x03\x02\x02\x02{\x07\x03\x02\x02\x02|}\x05"\x12\x02}~\x05' +
    '\x04\x03\x02~\x7F\x05$\x13\x02\x7F\t\x03\x02\x02\x02\x80\x81\x05\x14\v' +
    '\x02\x81\x82\x05 \x11\x02\x82\x9B\x03\x02\x02\x02\x83\x84\x05\x18\r\x02' +
    '\x84\x85\x05\f\x07\x02\x85\x9B\x03\x02\x02\x02\x86\x87\x05\x18\r\x02\x87' +
    '\x88\x05"\x12\x02\x88\x9B\x03\x02\x02\x02\x89\x8A\x05\x18\r\x02\x8A\x8B' +
    '\x05"\x12\x02\x8B\x8C\x05\x04\x03\x02\x8C\x9B\x03\x02\x02\x02\x8D\x8E' +
    '\x05"\x12\x02\x8E\x8F\x05\x04\x03\x02\x8F\x9B\x03\x02\x02\x02\x90\x9B' +
    '\x05\f\x07\x02\x91\x9B\x05"\x12\x02\x92\x94\x07\x07\x02\x02\x93\x92\x03' +
    '\x02\x02\x02\x94\x95\x03\x02\x02\x02\x95\x93\x03\x02\x02\x02\x95\x96\x03' +
    '\x02\x02\x02\x96\x9B\x03\x02\x02\x02\x97\x98\x05 \x11\x02\x98\x99\x05' +
    '\x16\f\x02\x99\x9B\x03\x02\x02\x02\x9A\x80\x03\x02\x02\x02\x9A\x83\x03' +
    '\x02\x02\x02\x9A\x86\x03\x02\x02\x02\x9A\x89\x03\x02\x02\x02\x9A\x8D\x03' +
    '\x02\x02\x02\x9A\x90\x03\x02\x02\x02\x9A\x91\x03\x02\x02\x02\x9A\x93\x03' +
    '\x02\x02\x02\x9A\x97\x03\x02\x02\x02\x9B\v\x03\x02\x02\x02\x9C\x9D\x05' +
    '"\x12\x02\x9D\x9E\x05$\x13\x02\x9E\r\x03\x02\x02\x02\x9F\xA0\x05\x12' +
    '\n\x02\xA0\x0F\x03\x02\x02\x02\xA1\xA2\x05\x12\n\x02\xA2\x11\x03\x02\x02' +
    '\x02\xA3\xAA\x07\x06\x02\x02\xA4\xA6\x07\x07\x02\x02\xA5\xA4\x03\x02\x02' +
    '\x02\xA6\xA7\x03\x02\x02\x02\xA7\xA5\x03\x02\x02\x02\xA7\xA8\x03\x02\x02' +
    '\x02\xA8\xAA\x03\x02\x02\x02\xA9\xA3\x03\x02\x02\x02\xA9\xA5\x03\x02\x02' +
    '\x02\xAA\x13\x03\x02\x02\x02\xAB\xAC\x07\x0F\x02\x02\xAC\x15\x03\x02\x02' +
    '\x02\xAD\xAE\x05*\x16\x02\xAE\x17\x03\x02\x02\x02\xAF\xB0\x07\x0F\x02' +
    '\x02\xB0\x19\x03\x02\x02\x02\xB1\xB2\x07\x04\x02\x02\xB2\x1B\x03\x02\x02' +
    '\x02\xB3\xB4\x07\x03\x02\x02\xB4\x1D\x03\x02\x02\x02\xB5\xB6\x07\x05\x02' +
    '\x02\xB6\x1F\x03\x02\x02\x02\xB7\xB8\x07\b\x02\x02\xB8!\x03\x02\x02\x02' +
    '\xB9\xBA\x07\t\x02\x02\xBA#\x03\x02\x02\x02\xBB\xBC\x07\n\x02\x02\xBC' +
    '%\x03\x02\x02\x02\xBD\xBF\x07\x10\x02\x02\xBE\xBD\x03\x02\x02\x02\xBF' +
    '\xC2\x03\x02\x02\x02\xC0\xBE\x03\x02\x02\x02\xC0\xC1\x03\x02\x02\x02\xC1' +
    "'\x03\x02\x02\x02\xC2\xC0\x03\x02\x02\x02\xC3\xC5\x07\x10\x02\x02\xC4" +
    '\xC3\x03\x02\x02\x02\xC5\xC8\x03\x02\x02\x02\xC6\xC4\x03\x02\x02\x02\xC6' +
    '\xC7\x03\x02\x02\x02\xC7)\x03\x02\x02\x02\xC8\xC6\x03\x02\x02\x02\xC9' +
    '\xCE\x07\f\x02\x02\xCA\xCE\x07\r\x02\x02\xCB\xCE\x07\x0E\x02\x02\xCC\xCE' +
    '\x07\x0F\x02\x02\xCD\xC9\x03\x02\x02\x02\xCD\xCA\x03\x02\x02\x02\xCD\xCB' +
    '\x03\x02\x02\x02\xCD\xCC\x03\x02\x02\x02\xCE+\x03\x02\x02\x02\rMlnz\x95' +
    '\x9A\xA7\xA9\xC0\xC6\xCD';
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
  public afterExpressionWhitespace(): AfterExpressionWhitespaceContext {
    return this.getRuleContext(0, AfterExpressionWhitespaceContext);
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
  public upTraversalExp(): UpTraversalExpContext {
    return this.getRuleContext(0, UpTraversalExpContext);
  }
  public traversalAllowedExpr(): TraversalAllowedExprContext {
    return this.getRuleContext(0, TraversalAllowedExprContext);
  }
  public downTraversalExp(): DownTraversalExpContext {
    return this.getRuleContext(0, DownTraversalExpContext);
  }
  public afterExpressionWhitespace(): AfterExpressionWhitespaceContext {
    return this.getRuleContext(0, AfterExpressionWhitespaceContext);
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
  public upTraversalExp(): UpTraversalExpContext {
    return this.getRuleContext(0, UpTraversalExpContext);
  }
  public traversalAllowedExpr(): TraversalAllowedExprContext {
    return this.getRuleContext(0, TraversalAllowedExprContext);
  }
  public afterExpressionWhitespace(): AfterExpressionWhitespaceContext {
    return this.getRuleContext(0, AfterExpressionWhitespaceContext);
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
  public downTraversalExp(): DownTraversalExpContext {
    return this.getRuleContext(0, DownTraversalExpContext);
  }
  public afterExpressionWhitespace(): AfterExpressionWhitespaceContext {
    return this.getRuleContext(0, AfterExpressionWhitespaceContext);
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
  public afterLogicalOperatorWhitespace(): AfterLogicalOperatorWhitespaceContext {
    return this.getRuleContext(0, AfterLogicalOperatorWhitespaceContext);
  }
  public expr(): ExprContext {
    return this.getRuleContext(0, ExprContext);
  }
  public afterExpressionWhitespace(): AfterExpressionWhitespaceContext {
    return this.getRuleContext(0, AfterExpressionWhitespaceContext);
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
  public afterExpressionWhitespace(): AfterExpressionWhitespaceContext[];
  public afterExpressionWhitespace(i: number): AfterExpressionWhitespaceContext;
  public afterExpressionWhitespace(
    i?: number,
  ): AfterExpressionWhitespaceContext | AfterExpressionWhitespaceContext[] {
    if (i === undefined) {
      return this.getRuleContexts(AfterExpressionWhitespaceContext);
    } else {
      return this.getRuleContext(i, AfterExpressionWhitespaceContext);
    }
  }
  public andToken(): AndTokenContext {
    return this.getRuleContext(0, AndTokenContext);
  }
  public afterLogicalOperatorWhitespace(): AfterLogicalOperatorWhitespaceContext {
    return this.getRuleContext(0, AfterLogicalOperatorWhitespaceContext);
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
  public afterExpressionWhitespace(): AfterExpressionWhitespaceContext[];
  public afterExpressionWhitespace(i: number): AfterExpressionWhitespaceContext;
  public afterExpressionWhitespace(
    i?: number,
  ): AfterExpressionWhitespaceContext | AfterExpressionWhitespaceContext[] {
    if (i === undefined) {
      return this.getRuleContexts(AfterExpressionWhitespaceContext);
    } else {
      return this.getRuleContext(i, AfterExpressionWhitespaceContext);
    }
  }
  public orToken(): OrTokenContext {
    return this.getRuleContext(0, OrTokenContext);
  }
  public afterLogicalOperatorWhitespace(): AfterLogicalOperatorWhitespaceContext {
    return this.getRuleContext(0, AfterLogicalOperatorWhitespaceContext);
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
  public afterExpressionWhitespace(): AfterExpressionWhitespaceContext {
    return this.getRuleContext(0, AfterExpressionWhitespaceContext);
  }
  public andToken(): AndTokenContext {
    return this.getRuleContext(0, AndTokenContext);
  }
  public afterLogicalOperatorWhitespace(): AfterLogicalOperatorWhitespaceContext {
    return this.getRuleContext(0, AfterLogicalOperatorWhitespaceContext);
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
  public afterExpressionWhitespace(): AfterExpressionWhitespaceContext {
    return this.getRuleContext(0, AfterExpressionWhitespaceContext);
  }
  public orToken(): OrTokenContext {
    return this.getRuleContext(0, OrTokenContext);
  }
  public afterLogicalOperatorWhitespace(): AfterLogicalOperatorWhitespaceContext {
    return this.getRuleContext(0, AfterLogicalOperatorWhitespaceContext);
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
  public afterLogicalOperatorWhitespace(): AfterLogicalOperatorWhitespaceContext {
    return this.getRuleContext(0, AfterLogicalOperatorWhitespaceContext);
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
export class UnmatchedExpressionContinuationContext extends ExprContext {
  public expr(): ExprContext {
    return this.getRuleContext(0, ExprContext);
  }
  public afterExpressionWhitespace(): AfterExpressionWhitespaceContext {
    return this.getRuleContext(0, AfterExpressionWhitespaceContext);
  }
  public value(): ValueContext {
    return this.getRuleContext(0, ValueContext);
  }
  public afterLogicalOperatorWhitespace(): AfterLogicalOperatorWhitespaceContext {
    return this.getRuleContext(0, AfterLogicalOperatorWhitespaceContext);
  }
  constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterUnmatchedExpressionContinuation) {
      listener.enterUnmatchedExpressionContinuation(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitUnmatchedExpressionContinuation) {
      listener.exitUnmatchedExpressionContinuation(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitUnmatchedExpressionContinuation) {
      return visitor.visitUnmatchedExpressionContinuation(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class AllExpressionContext extends ExprContext {
  public STAR(): TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.STAR, 0);
  }
  public afterExpressionWhitespace(): AfterExpressionWhitespaceContext {
    return this.getRuleContext(0, AfterExpressionWhitespaceContext);
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
  public afterExpressionWhitespace(): AfterExpressionWhitespaceContext {
    return this.getRuleContext(0, AfterExpressionWhitespaceContext);
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
  public attributeValue(): AttributeValueContext {
    return this.getRuleContext(0, AttributeValueContext);
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
export class ParenthesizedExpressionWrapperContext extends TraversalAllowedExprContext {
  public parenthesizedExpr(): ParenthesizedExprContext {
    return this.getRuleContext(0, ParenthesizedExprContext);
  }
  constructor(ctx: TraversalAllowedExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterParenthesizedExpressionWrapper) {
      listener.enterParenthesizedExpressionWrapper(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitParenthesizedExpressionWrapper) {
      listener.exitParenthesizedExpressionWrapper(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitParenthesizedExpressionWrapper) {
      return visitor.visitParenthesizedExpressionWrapper(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class IncompleteExpressionContext extends TraversalAllowedExprContext {
  public incompleteExpressionsWrapper(): IncompleteExpressionsWrapperContext {
    return this.getRuleContext(0, IncompleteExpressionsWrapperContext);
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
  public expr(): ExprContext {
    return this.getRuleContext(0, ExprContext);
  }
  public rightParenToken(): RightParenTokenContext {
    return this.getRuleContext(0, RightParenTokenContext);
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

export class IncompleteExpressionsWrapperContext extends ParserRuleContext {
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_incompleteExpressionsWrapper;
  }
  public copyFrom(ctx: IncompleteExpressionsWrapperContext): void {
    super.copyFrom(ctx);
  }
}
export class IncompleteAttributeExpressionMissingValueContext extends IncompleteExpressionsWrapperContext {
  public attributeName(): AttributeNameContext {
    return this.getRuleContext(0, AttributeNameContext);
  }
  public colonToken(): ColonTokenContext {
    return this.getRuleContext(0, ColonTokenContext);
  }
  constructor(ctx: IncompleteExpressionsWrapperContext) {
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
export class ExpressionlessFunctionExpressionContext extends IncompleteExpressionsWrapperContext {
  public functionName(): FunctionNameContext {
    return this.getRuleContext(0, FunctionNameContext);
  }
  public expressionLessParenthesizedExpr(): ExpressionLessParenthesizedExprContext {
    return this.getRuleContext(0, ExpressionLessParenthesizedExprContext);
  }
  constructor(ctx: IncompleteExpressionsWrapperContext) {
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
export class UnclosedExpressionlessFunctionExpressionContext extends IncompleteExpressionsWrapperContext {
  public functionName(): FunctionNameContext {
    return this.getRuleContext(0, FunctionNameContext);
  }
  public leftParenToken(): LeftParenTokenContext {
    return this.getRuleContext(0, LeftParenTokenContext);
  }
  constructor(ctx: IncompleteExpressionsWrapperContext) {
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
export class UnclosedFunctionExpressionContext extends IncompleteExpressionsWrapperContext {
  public functionName(): FunctionNameContext {
    return this.getRuleContext(0, FunctionNameContext);
  }
  public leftParenToken(): LeftParenTokenContext {
    return this.getRuleContext(0, LeftParenTokenContext);
  }
  public expr(): ExprContext {
    return this.getRuleContext(0, ExprContext);
  }
  constructor(ctx: IncompleteExpressionsWrapperContext) {
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
export class UnclosedParenthesizedExpressionContext extends IncompleteExpressionsWrapperContext {
  public leftParenToken(): LeftParenTokenContext {
    return this.getRuleContext(0, LeftParenTokenContext);
  }
  public expr(): ExprContext {
    return this.getRuleContext(0, ExprContext);
  }
  constructor(ctx: IncompleteExpressionsWrapperContext) {
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
export class ExpressionlessParenthesizedExpressionWrapperContext extends IncompleteExpressionsWrapperContext {
  public expressionLessParenthesizedExpr(): ExpressionLessParenthesizedExprContext {
    return this.getRuleContext(0, ExpressionLessParenthesizedExprContext);
  }
  constructor(ctx: IncompleteExpressionsWrapperContext) {
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
export class UnclosedExpressionlessParenthesizedExpressionContext extends IncompleteExpressionsWrapperContext {
  public leftParenToken(): LeftParenTokenContext {
    return this.getRuleContext(0, LeftParenTokenContext);
  }
  constructor(ctx: IncompleteExpressionsWrapperContext) {
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
export class IncompleteTraversalExpressionContext extends IncompleteExpressionsWrapperContext {
  public PLUS(): TerminalNode[];
  public PLUS(i: number): TerminalNode;
  public PLUS(i?: number): TerminalNode | TerminalNode[] {
    if (i === undefined) {
      return this.getTokens(SelectionAutoCompleteParser.PLUS);
    } else {
      return this.getToken(SelectionAutoCompleteParser.PLUS, i);
    }
  }
  constructor(ctx: IncompleteExpressionsWrapperContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterIncompleteTraversalExpression) {
      listener.enterIncompleteTraversalExpression(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitIncompleteTraversalExpression) {
      listener.exitIncompleteTraversalExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitIncompleteTraversalExpression) {
      return visitor.visitIncompleteTraversalExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class IncompleteAttributeExpressionMissingKeyContext extends IncompleteExpressionsWrapperContext {
  public colonToken(): ColonTokenContext {
    return this.getRuleContext(0, ColonTokenContext);
  }
  public attributeValue(): AttributeValueContext {
    return this.getRuleContext(0, AttributeValueContext);
  }
  constructor(ctx: IncompleteExpressionsWrapperContext) {
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
  public rightParenToken(): RightParenTokenContext {
    return this.getRuleContext(0, RightParenTokenContext);
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

export class UpTraversalExpContext extends ParserRuleContext {
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_upTraversalExp;
  }
  public copyFrom(ctx: UpTraversalExpContext): void {
    super.copyFrom(ctx);
  }
}
export class UpTraversalContext extends UpTraversalExpContext {
  public traversal(): TraversalContext {
    return this.getRuleContext(0, TraversalContext);
  }
  constructor(ctx: UpTraversalExpContext) {
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

export class DownTraversalExpContext extends ParserRuleContext {
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_downTraversalExp;
  }
  public copyFrom(ctx: DownTraversalExpContext): void {
    super.copyFrom(ctx);
  }
}
export class DownTraversalContext extends DownTraversalExpContext {
  public traversal(): TraversalContext {
    return this.getRuleContext(0, TraversalContext);
  }
  constructor(ctx: DownTraversalExpContext) {
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

export class TraversalContext extends ParserRuleContext {
  public STAR(): TerminalNode | undefined {
    return this.tryGetToken(SelectionAutoCompleteParser.STAR, 0);
  }
  public PLUS(): TerminalNode[];
  public PLUS(i: number): TerminalNode;
  public PLUS(i?: number): TerminalNode | TerminalNode[] {
    if (i === undefined) {
      return this.getTokens(SelectionAutoCompleteParser.PLUS);
    } else {
      return this.getToken(SelectionAutoCompleteParser.PLUS, i);
    }
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_traversal;
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterTraversal) {
      listener.enterTraversal(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitTraversal) {
      listener.exitTraversal(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitTraversal) {
      return visitor.visitTraversal(this);
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

export class AfterExpressionWhitespaceContext extends ParserRuleContext {
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
    return SelectionAutoCompleteParser.RULE_afterExpressionWhitespace;
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterAfterExpressionWhitespace) {
      listener.enterAfterExpressionWhitespace(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitAfterExpressionWhitespace) {
      listener.exitAfterExpressionWhitespace(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitAfterExpressionWhitespace) {
      return visitor.visitAfterExpressionWhitespace(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class AfterLogicalOperatorWhitespaceContext extends ParserRuleContext {
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
    return SelectionAutoCompleteParser.RULE_afterLogicalOperatorWhitespace;
  }
  // @Override
  public enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterAfterLogicalOperatorWhitespace) {
      listener.enterAfterLogicalOperatorWhitespace(this);
    }
  }
  // @Override
  public exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitAfterLogicalOperatorWhitespace) {
      listener.exitAfterLogicalOperatorWhitespace(this);
    }
  }
  // @Override
  public accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result {
    if (visitor.visitAfterLogicalOperatorWhitespace) {
      return visitor.visitAfterLogicalOperatorWhitespace(this);
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
