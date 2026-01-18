// Generated from /home/user/dagster/js_modules/dagster-ui/packages/ui-core/src/selection/SelectionAutoComplete.g4 by ANTLR 4.13.1

import * as antlr from 'antlr4ng';
import {Token} from 'antlr4ng';

import {SelectionAutoCompleteListener} from './SelectionAutoCompleteListener.js';
import {SelectionAutoCompleteVisitor} from './SelectionAutoCompleteVisitor.js';

// for running tests with parameters, TODO: discuss strategy for typed parameters in CI
// eslint-disable-next-line no-unused-vars
type int = number;

export class SelectionAutoCompleteParser extends antlr.Parser {
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
  public static readonly NULL_STRING = 13;
  public static readonly EQUAL = 14;
  public static readonly IDENTIFIER = 15;
  public static readonly WS = 16;
  public static readonly COMMA = 17;
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
  public static readonly RULE_commaToken = 13;
  public static readonly RULE_orToken = 14;
  public static readonly RULE_andToken = 15;
  public static readonly RULE_notToken = 16;
  public static readonly RULE_colonToken = 17;
  public static readonly RULE_leftParenToken = 18;
  public static readonly RULE_rightParenToken = 19;
  public static readonly RULE_attributeValueWhitespace = 20;
  public static readonly RULE_postAttributeValueWhitespace = 21;
  public static readonly RULE_postExpressionWhitespace = 22;
  public static readonly RULE_postNotOperatorWhitespace = 23;
  public static readonly RULE_postLogicalOperatorWhitespace = 24;
  public static readonly RULE_postNeighborTraversalWhitespace = 25;
  public static readonly RULE_postUpwardTraversalWhitespace = 26;
  public static readonly RULE_postDownwardTraversalWhitespace = 27;
  public static readonly RULE_postDigitsWhitespace = 28;
  public static readonly RULE_value = 29;

  public static readonly literalNames = [
    null,
    null,
    null,
    null,
    "'*'",
    "'+'",
    null,
    "':'",
    "'('",
    "')'",
    null,
    null,
    null,
    "'<null>'",
    "'='",
    null,
    null,
    "','",
  ];

  public static readonly symbolicNames = [
    null,
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
    'NULL_STRING',
    'EQUAL',
    'IDENTIFIER',
    'WS',
    'COMMA',
  ];
  public static readonly ruleNames = [
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
    'commaToken',
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

  public get grammarFileName(): string {
    return 'SelectionAutoComplete.g4';
  }
  public get literalNames(): (string | null)[] {
    return SelectionAutoCompleteParser.literalNames;
  }
  public get symbolicNames(): (string | null)[] {
    return SelectionAutoCompleteParser.symbolicNames;
  }
  public get ruleNames(): string[] {
    return SelectionAutoCompleteParser.ruleNames;
  }
  public get serializedATN(): number[] {
    return SelectionAutoCompleteParser._serializedATN;
  }

  protected createFailedPredicateException(
    predicate?: string,
    message?: string,
  ): antlr.FailedPredicateException {
    return new antlr.FailedPredicateException(this, predicate, message);
  }

  public constructor(input: antlr.TokenStream) {
    super(input);
    this.interpreter = new antlr.ParserATNSimulator(
      this,
      SelectionAutoCompleteParser._ATN,
      SelectionAutoCompleteParser.decisionsToDFA,
      new antlr.PredictionContextCache(),
    );
  }
  public start(): StartContext {
    let localContext = new StartContext(this.context, this.state);
    this.enterRule(localContext, 0, SelectionAutoCompleteParser.RULE_start);
    try {
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 60;
        this.expr(0);
        this.state = 61;
        this.match(SelectionAutoCompleteParser.EOF);
      }
    } catch (re) {
      if (re instanceof antlr.RecognitionException) {
        this.errorHandler.reportError(this, re);
        this.errorHandler.recover(this, re);
      } else {
        throw re;
      }
    } finally {
      this.exitRule();
    }
    return localContext;
  }

  public expr(): ExprContext;
  public expr(_p: number): ExprContext;
  public expr(_p?: number): ExprContext {
    if (_p === undefined) {
      _p = 0;
    }

    let parentContext = this.context;
    let parentState = this.state;
    let localContext = new ExprContext(this.context, parentState);
    let previousContext = localContext;
    let _startState = 2;
    this.enterRecursionRule(localContext, 2, SelectionAutoCompleteParser.RULE_expr, _p);
    try {
      let alternative: number;
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 88;
        this.errorHandler.sync(this);
        switch (this.interpreter.adaptivePredict(this.tokenStream, 0, this.context)) {
          case 1:
            {
              localContext = new TraversalAllowedExpressionContext(localContext);
              this.context = localContext;
              previousContext = localContext;

              this.state = 64;
              this.traversalAllowedExpr();
            }
            break;
          case 2:
            {
              localContext = new UpAndDownTraversalExpressionContext(localContext);
              this.context = localContext;
              previousContext = localContext;
              this.state = 65;
              this.upTraversalExpr();
              this.state = 66;
              this.traversalAllowedExpr();
              this.state = 67;
              this.downTraversalExpr();
            }
            break;
          case 3:
            {
              localContext = new UpTraversalExpressionContext(localContext);
              this.context = localContext;
              previousContext = localContext;
              this.state = 69;
              this.upTraversalExpr();
              this.state = 70;
              this.traversalAllowedExpr();
            }
            break;
          case 4:
            {
              localContext = new DownTraversalExpressionContext(localContext);
              this.context = localContext;
              previousContext = localContext;
              this.state = 72;
              this.traversalAllowedExpr();
              this.state = 73;
              this.downTraversalExpr();
            }
            break;
          case 5:
            {
              localContext = new NotExpressionContext(localContext);
              this.context = localContext;
              previousContext = localContext;
              this.state = 75;
              this.notToken();
              this.state = 76;
              this.postNotOperatorWhitespace();
              this.state = 77;
              this.expr(11);
            }
            break;
          case 6:
            {
              localContext = new IncompleteNotExpressionContext(localContext);
              this.context = localContext;
              previousContext = localContext;
              this.state = 79;
              this.notToken();
              this.state = 80;
              this.postNotOperatorWhitespace();
            }
            break;
          case 7:
            {
              localContext = new AllExpressionContext(localContext);
              this.context = localContext;
              previousContext = localContext;
              this.state = 82;
              this.match(SelectionAutoCompleteParser.STAR);
              this.state = 83;
              this.postExpressionWhitespace();
            }
            break;
          case 8:
            {
              localContext = new UnmatchedValueContext(localContext);
              this.context = localContext;
              previousContext = localContext;
              this.state = 84;
              this.value();
              this.state = 85;
              this.postExpressionWhitespace();
            }
            break;
          case 9:
            {
              localContext = new CommaExpressionWrapper3Context(localContext);
              this.context = localContext;
              previousContext = localContext;
              this.state = 87;
              this.commaToken();
            }
            break;
        }
        this.context!.stop = this.tokenStream.LT(-1);
        this.state = 116;
        this.errorHandler.sync(this);
        alternative = this.interpreter.adaptivePredict(this.tokenStream, 2, this.context);
        while (alternative !== 2 && alternative !== antlr.ATN.INVALID_ALT_NUMBER) {
          if (alternative === 1) {
            if (this.parseListeners != null) {
              this.triggerExitRuleEvent();
            }
            previousContext = localContext;
            {
              this.state = 114;
              this.errorHandler.sync(this);
              switch (this.interpreter.adaptivePredict(this.tokenStream, 1, this.context)) {
                case 1:
                  {
                    localContext = new AndExpressionContext(
                      new ExprContext(parentContext, parentState),
                    );
                    this.pushNewRecursionContext(
                      localContext,
                      _startState,
                      SelectionAutoCompleteParser.RULE_expr,
                    );
                    this.state = 90;
                    if (!this.precpred(this.context, 10)) {
                      throw this.createFailedPredicateException('this.precpred(this.context, 10)');
                    }
                    this.state = 91;
                    this.andToken();
                    this.state = 92;
                    this.postLogicalOperatorWhitespace();
                    this.state = 93;
                    this.expr(11);
                  }
                  break;
                case 2:
                  {
                    localContext = new OrExpressionContext(
                      new ExprContext(parentContext, parentState),
                    );
                    this.pushNewRecursionContext(
                      localContext,
                      _startState,
                      SelectionAutoCompleteParser.RULE_expr,
                    );
                    this.state = 95;
                    if (!this.precpred(this.context, 9)) {
                      throw this.createFailedPredicateException('this.precpred(this.context, 9)');
                    }
                    this.state = 96;
                    this.orToken();
                    this.state = 97;
                    this.postLogicalOperatorWhitespace();
                    this.state = 98;
                    this.expr(10);
                  }
                  break;
                case 3:
                  {
                    localContext = new CommaExpressionWrapper1Context(
                      new ExprContext(parentContext, parentState),
                    );
                    this.pushNewRecursionContext(
                      localContext,
                      _startState,
                      SelectionAutoCompleteParser.RULE_expr,
                    );
                    this.state = 100;
                    if (!this.precpred(this.context, 8)) {
                      throw this.createFailedPredicateException('this.precpred(this.context, 8)');
                    }
                    this.state = 101;
                    this.commaToken();
                    this.state = 102;
                    this.expr(9);
                  }
                  break;
                case 4:
                  {
                    localContext = new IncompleteAndExpressionContext(
                      new ExprContext(parentContext, parentState),
                    );
                    this.pushNewRecursionContext(
                      localContext,
                      _startState,
                      SelectionAutoCompleteParser.RULE_expr,
                    );
                    this.state = 104;
                    if (!this.precpred(this.context, 7)) {
                      throw this.createFailedPredicateException('this.precpred(this.context, 7)');
                    }
                    this.state = 105;
                    this.andToken();
                    this.state = 106;
                    this.postLogicalOperatorWhitespace();
                  }
                  break;
                case 5:
                  {
                    localContext = new IncompleteOrExpressionContext(
                      new ExprContext(parentContext, parentState),
                    );
                    this.pushNewRecursionContext(
                      localContext,
                      _startState,
                      SelectionAutoCompleteParser.RULE_expr,
                    );
                    this.state = 108;
                    if (!this.precpred(this.context, 6)) {
                      throw this.createFailedPredicateException('this.precpred(this.context, 6)');
                    }
                    this.state = 109;
                    this.orToken();
                    this.state = 110;
                    this.postLogicalOperatorWhitespace();
                  }
                  break;
                case 6:
                  {
                    localContext = new CommaExpressionWrapper2Context(
                      new ExprContext(parentContext, parentState),
                    );
                    this.pushNewRecursionContext(
                      localContext,
                      _startState,
                      SelectionAutoCompleteParser.RULE_expr,
                    );
                    this.state = 112;
                    if (!this.precpred(this.context, 5)) {
                      throw this.createFailedPredicateException('this.precpred(this.context, 5)');
                    }
                    this.state = 113;
                    this.commaToken();
                  }
                  break;
              }
            }
          }
          this.state = 118;
          this.errorHandler.sync(this);
          alternative = this.interpreter.adaptivePredict(this.tokenStream, 2, this.context);
        }
      }
    } catch (re) {
      if (re instanceof antlr.RecognitionException) {
        this.errorHandler.reportError(this, re);
        this.errorHandler.recover(this, re);
      } else {
        throw re;
      }
    } finally {
      this.unrollRecursionContexts(parentContext);
    }
    return localContext;
  }
  public traversalAllowedExpr(): TraversalAllowedExprContext {
    let localContext = new TraversalAllowedExprContext(this.context, this.state);
    this.enterRule(localContext, 4, SelectionAutoCompleteParser.RULE_traversalAllowedExpr);
    try {
      this.state = 133;
      this.errorHandler.sync(this);
      switch (this.interpreter.adaptivePredict(this.tokenStream, 4, this.context)) {
        case 1:
          localContext = new AttributeExpressionContext(localContext);
          this.enterOuterAlt(localContext, 1);
          {
            this.state = 119;
            this.attributeName();
            this.state = 120;
            this.colonToken();
            this.state = 121;
            this.attributeValue();
            this.state = 124;
            this.errorHandler.sync(this);
            switch (this.interpreter.adaptivePredict(this.tokenStream, 3, this.context)) {
              case 1:
                {
                  this.state = 122;
                  this.match(SelectionAutoCompleteParser.EQUAL);
                  this.state = 123;
                  this.attributeValue();
                }
                break;
            }
            this.state = 126;
            this.postAttributeValueWhitespace();
          }
          break;
        case 2:
          localContext = new FunctionCallExpressionContext(localContext);
          this.enterOuterAlt(localContext, 2);
          {
            this.state = 128;
            this.functionName();
            this.state = 129;
            this.parenthesizedExpr();
          }
          break;
        case 3:
          localContext = new TraversalAllowedParenthesizedExpressionContext(localContext);
          this.enterOuterAlt(localContext, 3);
          {
            this.state = 131;
            this.parenthesizedExpr();
          }
          break;
        case 4:
          localContext = new IncompleteExpressionContext(localContext);
          this.enterOuterAlt(localContext, 4);
          {
            this.state = 132;
            this.incompleteExpr();
          }
          break;
      }
    } catch (re) {
      if (re instanceof antlr.RecognitionException) {
        this.errorHandler.reportError(this, re);
        this.errorHandler.recover(this, re);
      } else {
        throw re;
      }
    } finally {
      this.exitRule();
    }
    return localContext;
  }
  public parenthesizedExpr(): ParenthesizedExprContext {
    let localContext = new ParenthesizedExprContext(this.context, this.state);
    this.enterRule(localContext, 6, SelectionAutoCompleteParser.RULE_parenthesizedExpr);
    try {
      localContext = new ParenthesizedExpressionContext(localContext);
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 135;
        this.leftParenToken();
        this.state = 136;
        this.postLogicalOperatorWhitespace();
        this.state = 137;
        this.expr(0);
        this.state = 138;
        this.rightParenToken();
        this.state = 139;
        this.postExpressionWhitespace();
      }
    } catch (re) {
      if (re instanceof antlr.RecognitionException) {
        this.errorHandler.reportError(this, re);
        this.errorHandler.recover(this, re);
      } else {
        throw re;
      }
    } finally {
      this.exitRule();
    }
    return localContext;
  }
  public incompleteExpr(): IncompleteExprContext {
    let localContext = new IncompleteExprContext(this.context, this.state);
    this.enterRule(localContext, 8, SelectionAutoCompleteParser.RULE_incompleteExpr);
    let _la: number;
    try {
      this.state = 183;
      this.errorHandler.sync(this);
      switch (this.interpreter.adaptivePredict(this.tokenStream, 6, this.context)) {
        case 1:
          localContext = new IncompleteAttributeExpressionMissingSecondValueContext(localContext);
          this.enterOuterAlt(localContext, 1);
          {
            this.state = 141;
            this.attributeName();
            this.state = 142;
            this.colonToken();
            this.state = 143;
            this.attributeValue();
            this.state = 144;
            this.match(SelectionAutoCompleteParser.EQUAL);
            this.state = 145;
            this.attributeValueWhitespace();
          }
          break;
        case 2:
          localContext = new IncompleteAttributeExpressionMissingValueContext(localContext);
          this.enterOuterAlt(localContext, 2);
          {
            this.state = 147;
            this.attributeName();
            this.state = 148;
            this.colonToken();
            this.state = 149;
            this.attributeValueWhitespace();
          }
          break;
        case 3:
          localContext = new ExpressionlessFunctionExpressionContext(localContext);
          this.enterOuterAlt(localContext, 3);
          {
            this.state = 151;
            this.functionName();
            this.state = 152;
            this.expressionLessParenthesizedExpr();
          }
          break;
        case 4:
          localContext = new UnclosedExpressionlessFunctionExpressionContext(localContext);
          this.enterOuterAlt(localContext, 4);
          {
            this.state = 154;
            this.functionName();
            this.state = 155;
            this.leftParenToken();
            this.state = 156;
            this.postLogicalOperatorWhitespace();
          }
          break;
        case 5:
          localContext = new UnclosedFunctionExpressionContext(localContext);
          this.enterOuterAlt(localContext, 5);
          {
            this.state = 158;
            this.functionName();
            this.state = 159;
            this.leftParenToken();
            this.state = 160;
            this.expr(0);
          }
          break;
        case 6:
          localContext = new UnclosedParenthesizedExpressionContext(localContext);
          this.enterOuterAlt(localContext, 6);
          {
            this.state = 162;
            this.leftParenToken();
            this.state = 163;
            this.postLogicalOperatorWhitespace();
            this.state = 164;
            this.expr(0);
          }
          break;
        case 7:
          localContext = new ExpressionlessParenthesizedExpressionWrapperContext(localContext);
          this.enterOuterAlt(localContext, 7);
          {
            this.state = 166;
            this.expressionLessParenthesizedExpr();
          }
          break;
        case 8:
          localContext = new UnclosedExpressionlessParenthesizedExpressionContext(localContext);
          this.enterOuterAlt(localContext, 8);
          {
            this.state = 167;
            this.leftParenToken();
            this.state = 168;
            this.postLogicalOperatorWhitespace();
          }
          break;
        case 9:
          localContext = new IncompletePlusTraversalExpressionContext(localContext);
          this.enterOuterAlt(localContext, 9);
          {
            this.state = 171;
            this.errorHandler.sync(this);
            _la = this.tokenStream.LA(1);
            if (_la === 6) {
              {
                this.state = 170;
                this.match(SelectionAutoCompleteParser.DIGITS);
              }
            }

            this.state = 173;
            this.match(SelectionAutoCompleteParser.PLUS);
            this.state = 174;
            this.postNeighborTraversalWhitespace();
          }
          break;
        case 10:
          localContext = new IncompletePlusTraversalExpressionMissingValueContext(localContext);
          this.enterOuterAlt(localContext, 10);
          {
            this.state = 175;
            this.match(SelectionAutoCompleteParser.PLUS);
            this.state = 176;
            this.value();
            this.state = 177;
            this.postExpressionWhitespace();
          }
          break;
        case 11:
          localContext = new IncompleteAttributeExpressionMissingKeyContext(localContext);
          this.enterOuterAlt(localContext, 11);
          {
            this.state = 179;
            this.colonToken();
            this.state = 180;
            this.attributeValue();
            this.state = 181;
            this.postExpressionWhitespace();
          }
          break;
      }
    } catch (re) {
      if (re instanceof antlr.RecognitionException) {
        this.errorHandler.reportError(this, re);
        this.errorHandler.recover(this, re);
      } else {
        throw re;
      }
    } finally {
      this.exitRule();
    }
    return localContext;
  }
  public expressionLessParenthesizedExpr(): ExpressionLessParenthesizedExprContext {
    let localContext = new ExpressionLessParenthesizedExprContext(this.context, this.state);
    this.enterRule(
      localContext,
      10,
      SelectionAutoCompleteParser.RULE_expressionLessParenthesizedExpr,
    );
    try {
      localContext = new ExpressionlessParenthesizedExpressionContext(localContext);
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 185;
        this.leftParenToken();
        this.state = 186;
        this.postLogicalOperatorWhitespace();
        this.state = 187;
        this.rightParenToken();
        this.state = 188;
        this.postExpressionWhitespace();
      }
    } catch (re) {
      if (re instanceof antlr.RecognitionException) {
        this.errorHandler.reportError(this, re);
        this.errorHandler.recover(this, re);
      } else {
        throw re;
      }
    } finally {
      this.exitRule();
    }
    return localContext;
  }
  public upTraversalExpr(): UpTraversalExprContext {
    let localContext = new UpTraversalExprContext(this.context, this.state);
    this.enterRule(localContext, 12, SelectionAutoCompleteParser.RULE_upTraversalExpr);
    try {
      localContext = new UpTraversalContext(localContext);
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 190;
        this.upTraversalToken();
        this.state = 191;
        this.postUpwardTraversalWhitespace();
      }
    } catch (re) {
      if (re instanceof antlr.RecognitionException) {
        this.errorHandler.reportError(this, re);
        this.errorHandler.recover(this, re);
      } else {
        throw re;
      }
    } finally {
      this.exitRule();
    }
    return localContext;
  }
  public downTraversalExpr(): DownTraversalExprContext {
    let localContext = new DownTraversalExprContext(this.context, this.state);
    this.enterRule(localContext, 14, SelectionAutoCompleteParser.RULE_downTraversalExpr);
    try {
      localContext = new DownTraversalContext(localContext);
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 193;
        this.downTraversalToken();
        this.state = 194;
        this.postDownwardTraversalWhitespace();
      }
    } catch (re) {
      if (re instanceof antlr.RecognitionException) {
        this.errorHandler.reportError(this, re);
        this.errorHandler.recover(this, re);
      } else {
        throw re;
      }
    } finally {
      this.exitRule();
    }
    return localContext;
  }
  public upTraversalToken(): UpTraversalTokenContext {
    let localContext = new UpTraversalTokenContext(this.context, this.state);
    this.enterRule(localContext, 16, SelectionAutoCompleteParser.RULE_upTraversalToken);
    let _la: number;
    try {
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 197;
        this.errorHandler.sync(this);
        _la = this.tokenStream.LA(1);
        if (_la === 6) {
          {
            this.state = 196;
            this.match(SelectionAutoCompleteParser.DIGITS);
          }
        }

        this.state = 199;
        this.match(SelectionAutoCompleteParser.PLUS);
      }
    } catch (re) {
      if (re instanceof antlr.RecognitionException) {
        this.errorHandler.reportError(this, re);
        this.errorHandler.recover(this, re);
      } else {
        throw re;
      }
    } finally {
      this.exitRule();
    }
    return localContext;
  }
  public downTraversalToken(): DownTraversalTokenContext {
    let localContext = new DownTraversalTokenContext(this.context, this.state);
    this.enterRule(localContext, 18, SelectionAutoCompleteParser.RULE_downTraversalToken);
    try {
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 201;
        this.match(SelectionAutoCompleteParser.PLUS);
        this.state = 203;
        this.errorHandler.sync(this);
        switch (this.interpreter.adaptivePredict(this.tokenStream, 8, this.context)) {
          case 1:
            {
              this.state = 202;
              this.match(SelectionAutoCompleteParser.DIGITS);
            }
            break;
        }
      }
    } catch (re) {
      if (re instanceof antlr.RecognitionException) {
        this.errorHandler.reportError(this, re);
        this.errorHandler.recover(this, re);
      } else {
        throw re;
      }
    } finally {
      this.exitRule();
    }
    return localContext;
  }
  public attributeName(): AttributeNameContext {
    let localContext = new AttributeNameContext(this.context, this.state);
    this.enterRule(localContext, 20, SelectionAutoCompleteParser.RULE_attributeName);
    try {
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 205;
        this.match(SelectionAutoCompleteParser.IDENTIFIER);
      }
    } catch (re) {
      if (re instanceof antlr.RecognitionException) {
        this.errorHandler.reportError(this, re);
        this.errorHandler.recover(this, re);
      } else {
        throw re;
      }
    } finally {
      this.exitRule();
    }
    return localContext;
  }
  public attributeValue(): AttributeValueContext {
    let localContext = new AttributeValueContext(this.context, this.state);
    this.enterRule(localContext, 22, SelectionAutoCompleteParser.RULE_attributeValue);
    try {
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 207;
        this.value();
      }
    } catch (re) {
      if (re instanceof antlr.RecognitionException) {
        this.errorHandler.reportError(this, re);
        this.errorHandler.recover(this, re);
      } else {
        throw re;
      }
    } finally {
      this.exitRule();
    }
    return localContext;
  }
  public functionName(): FunctionNameContext {
    let localContext = new FunctionNameContext(this.context, this.state);
    this.enterRule(localContext, 24, SelectionAutoCompleteParser.RULE_functionName);
    try {
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 209;
        this.match(SelectionAutoCompleteParser.IDENTIFIER);
      }
    } catch (re) {
      if (re instanceof antlr.RecognitionException) {
        this.errorHandler.reportError(this, re);
        this.errorHandler.recover(this, re);
      } else {
        throw re;
      }
    } finally {
      this.exitRule();
    }
    return localContext;
  }
  public commaToken(): CommaTokenContext {
    let localContext = new CommaTokenContext(this.context, this.state);
    this.enterRule(localContext, 26, SelectionAutoCompleteParser.RULE_commaToken);
    try {
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 211;
        this.match(SelectionAutoCompleteParser.COMMA);
        this.state = 212;
        this.postLogicalOperatorWhitespace();
      }
    } catch (re) {
      if (re instanceof antlr.RecognitionException) {
        this.errorHandler.reportError(this, re);
        this.errorHandler.recover(this, re);
      } else {
        throw re;
      }
    } finally {
      this.exitRule();
    }
    return localContext;
  }
  public orToken(): OrTokenContext {
    let localContext = new OrTokenContext(this.context, this.state);
    this.enterRule(localContext, 28, SelectionAutoCompleteParser.RULE_orToken);
    try {
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 214;
        this.match(SelectionAutoCompleteParser.OR);
      }
    } catch (re) {
      if (re instanceof antlr.RecognitionException) {
        this.errorHandler.reportError(this, re);
        this.errorHandler.recover(this, re);
      } else {
        throw re;
      }
    } finally {
      this.exitRule();
    }
    return localContext;
  }
  public andToken(): AndTokenContext {
    let localContext = new AndTokenContext(this.context, this.state);
    this.enterRule(localContext, 30, SelectionAutoCompleteParser.RULE_andToken);
    try {
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 216;
        this.match(SelectionAutoCompleteParser.AND);
      }
    } catch (re) {
      if (re instanceof antlr.RecognitionException) {
        this.errorHandler.reportError(this, re);
        this.errorHandler.recover(this, re);
      } else {
        throw re;
      }
    } finally {
      this.exitRule();
    }
    return localContext;
  }
  public notToken(): NotTokenContext {
    let localContext = new NotTokenContext(this.context, this.state);
    this.enterRule(localContext, 32, SelectionAutoCompleteParser.RULE_notToken);
    try {
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 218;
        this.match(SelectionAutoCompleteParser.NOT);
      }
    } catch (re) {
      if (re instanceof antlr.RecognitionException) {
        this.errorHandler.reportError(this, re);
        this.errorHandler.recover(this, re);
      } else {
        throw re;
      }
    } finally {
      this.exitRule();
    }
    return localContext;
  }
  public colonToken(): ColonTokenContext {
    let localContext = new ColonTokenContext(this.context, this.state);
    this.enterRule(localContext, 34, SelectionAutoCompleteParser.RULE_colonToken);
    try {
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 220;
        this.match(SelectionAutoCompleteParser.COLON);
      }
    } catch (re) {
      if (re instanceof antlr.RecognitionException) {
        this.errorHandler.reportError(this, re);
        this.errorHandler.recover(this, re);
      } else {
        throw re;
      }
    } finally {
      this.exitRule();
    }
    return localContext;
  }
  public leftParenToken(): LeftParenTokenContext {
    let localContext = new LeftParenTokenContext(this.context, this.state);
    this.enterRule(localContext, 36, SelectionAutoCompleteParser.RULE_leftParenToken);
    try {
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 222;
        this.match(SelectionAutoCompleteParser.LPAREN);
      }
    } catch (re) {
      if (re instanceof antlr.RecognitionException) {
        this.errorHandler.reportError(this, re);
        this.errorHandler.recover(this, re);
      } else {
        throw re;
      }
    } finally {
      this.exitRule();
    }
    return localContext;
  }
  public rightParenToken(): RightParenTokenContext {
    let localContext = new RightParenTokenContext(this.context, this.state);
    this.enterRule(localContext, 38, SelectionAutoCompleteParser.RULE_rightParenToken);
    try {
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 224;
        this.match(SelectionAutoCompleteParser.RPAREN);
      }
    } catch (re) {
      if (re instanceof antlr.RecognitionException) {
        this.errorHandler.reportError(this, re);
        this.errorHandler.recover(this, re);
      } else {
        throw re;
      }
    } finally {
      this.exitRule();
    }
    return localContext;
  }
  public attributeValueWhitespace(): AttributeValueWhitespaceContext {
    let localContext = new AttributeValueWhitespaceContext(this.context, this.state);
    this.enterRule(localContext, 40, SelectionAutoCompleteParser.RULE_attributeValueWhitespace);
    try {
      let alternative: number;
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 229;
        this.errorHandler.sync(this);
        alternative = this.interpreter.adaptivePredict(this.tokenStream, 9, this.context);
        while (alternative !== 2 && alternative !== antlr.ATN.INVALID_ALT_NUMBER) {
          if (alternative === 1) {
            {
              {
                this.state = 226;
                this.match(SelectionAutoCompleteParser.WS);
              }
            }
          }
          this.state = 231;
          this.errorHandler.sync(this);
          alternative = this.interpreter.adaptivePredict(this.tokenStream, 9, this.context);
        }
      }
    } catch (re) {
      if (re instanceof antlr.RecognitionException) {
        this.errorHandler.reportError(this, re);
        this.errorHandler.recover(this, re);
      } else {
        throw re;
      }
    } finally {
      this.exitRule();
    }
    return localContext;
  }
  public postAttributeValueWhitespace(): PostAttributeValueWhitespaceContext {
    let localContext = new PostAttributeValueWhitespaceContext(this.context, this.state);
    this.enterRule(localContext, 42, SelectionAutoCompleteParser.RULE_postAttributeValueWhitespace);
    try {
      let alternative: number;
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 235;
        this.errorHandler.sync(this);
        alternative = this.interpreter.adaptivePredict(this.tokenStream, 10, this.context);
        while (alternative !== 2 && alternative !== antlr.ATN.INVALID_ALT_NUMBER) {
          if (alternative === 1) {
            {
              {
                this.state = 232;
                this.match(SelectionAutoCompleteParser.WS);
              }
            }
          }
          this.state = 237;
          this.errorHandler.sync(this);
          alternative = this.interpreter.adaptivePredict(this.tokenStream, 10, this.context);
        }
      }
    } catch (re) {
      if (re instanceof antlr.RecognitionException) {
        this.errorHandler.reportError(this, re);
        this.errorHandler.recover(this, re);
      } else {
        throw re;
      }
    } finally {
      this.exitRule();
    }
    return localContext;
  }
  public postExpressionWhitespace(): PostExpressionWhitespaceContext {
    let localContext = new PostExpressionWhitespaceContext(this.context, this.state);
    this.enterRule(localContext, 44, SelectionAutoCompleteParser.RULE_postExpressionWhitespace);
    try {
      let alternative: number;
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 241;
        this.errorHandler.sync(this);
        alternative = this.interpreter.adaptivePredict(this.tokenStream, 11, this.context);
        while (alternative !== 2 && alternative !== antlr.ATN.INVALID_ALT_NUMBER) {
          if (alternative === 1) {
            {
              {
                this.state = 238;
                this.match(SelectionAutoCompleteParser.WS);
              }
            }
          }
          this.state = 243;
          this.errorHandler.sync(this);
          alternative = this.interpreter.adaptivePredict(this.tokenStream, 11, this.context);
        }
      }
    } catch (re) {
      if (re instanceof antlr.RecognitionException) {
        this.errorHandler.reportError(this, re);
        this.errorHandler.recover(this, re);
      } else {
        throw re;
      }
    } finally {
      this.exitRule();
    }
    return localContext;
  }
  public postNotOperatorWhitespace(): PostNotOperatorWhitespaceContext {
    let localContext = new PostNotOperatorWhitespaceContext(this.context, this.state);
    this.enterRule(localContext, 46, SelectionAutoCompleteParser.RULE_postNotOperatorWhitespace);
    try {
      let alternative: number;
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 247;
        this.errorHandler.sync(this);
        alternative = this.interpreter.adaptivePredict(this.tokenStream, 12, this.context);
        while (alternative !== 2 && alternative !== antlr.ATN.INVALID_ALT_NUMBER) {
          if (alternative === 1) {
            {
              {
                this.state = 244;
                this.match(SelectionAutoCompleteParser.WS);
              }
            }
          }
          this.state = 249;
          this.errorHandler.sync(this);
          alternative = this.interpreter.adaptivePredict(this.tokenStream, 12, this.context);
        }
      }
    } catch (re) {
      if (re instanceof antlr.RecognitionException) {
        this.errorHandler.reportError(this, re);
        this.errorHandler.recover(this, re);
      } else {
        throw re;
      }
    } finally {
      this.exitRule();
    }
    return localContext;
  }
  public postLogicalOperatorWhitespace(): PostLogicalOperatorWhitespaceContext {
    let localContext = new PostLogicalOperatorWhitespaceContext(this.context, this.state);
    this.enterRule(
      localContext,
      48,
      SelectionAutoCompleteParser.RULE_postLogicalOperatorWhitespace,
    );
    try {
      let alternative: number;
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 253;
        this.errorHandler.sync(this);
        alternative = this.interpreter.adaptivePredict(this.tokenStream, 13, this.context);
        while (alternative !== 2 && alternative !== antlr.ATN.INVALID_ALT_NUMBER) {
          if (alternative === 1) {
            {
              {
                this.state = 250;
                this.match(SelectionAutoCompleteParser.WS);
              }
            }
          }
          this.state = 255;
          this.errorHandler.sync(this);
          alternative = this.interpreter.adaptivePredict(this.tokenStream, 13, this.context);
        }
      }
    } catch (re) {
      if (re instanceof antlr.RecognitionException) {
        this.errorHandler.reportError(this, re);
        this.errorHandler.recover(this, re);
      } else {
        throw re;
      }
    } finally {
      this.exitRule();
    }
    return localContext;
  }
  public postNeighborTraversalWhitespace(): PostNeighborTraversalWhitespaceContext {
    let localContext = new PostNeighborTraversalWhitespaceContext(this.context, this.state);
    this.enterRule(
      localContext,
      50,
      SelectionAutoCompleteParser.RULE_postNeighborTraversalWhitespace,
    );
    try {
      let alternative: number;
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 259;
        this.errorHandler.sync(this);
        alternative = this.interpreter.adaptivePredict(this.tokenStream, 14, this.context);
        while (alternative !== 2 && alternative !== antlr.ATN.INVALID_ALT_NUMBER) {
          if (alternative === 1) {
            {
              {
                this.state = 256;
                this.match(SelectionAutoCompleteParser.WS);
              }
            }
          }
          this.state = 261;
          this.errorHandler.sync(this);
          alternative = this.interpreter.adaptivePredict(this.tokenStream, 14, this.context);
        }
      }
    } catch (re) {
      if (re instanceof antlr.RecognitionException) {
        this.errorHandler.reportError(this, re);
        this.errorHandler.recover(this, re);
      } else {
        throw re;
      }
    } finally {
      this.exitRule();
    }
    return localContext;
  }
  public postUpwardTraversalWhitespace(): PostUpwardTraversalWhitespaceContext {
    let localContext = new PostUpwardTraversalWhitespaceContext(this.context, this.state);
    this.enterRule(
      localContext,
      52,
      SelectionAutoCompleteParser.RULE_postUpwardTraversalWhitespace,
    );
    let _la: number;
    try {
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 265;
        this.errorHandler.sync(this);
        _la = this.tokenStream.LA(1);
        while (_la === 16) {
          {
            {
              this.state = 262;
              this.match(SelectionAutoCompleteParser.WS);
            }
          }
          this.state = 267;
          this.errorHandler.sync(this);
          _la = this.tokenStream.LA(1);
        }
      }
    } catch (re) {
      if (re instanceof antlr.RecognitionException) {
        this.errorHandler.reportError(this, re);
        this.errorHandler.recover(this, re);
      } else {
        throw re;
      }
    } finally {
      this.exitRule();
    }
    return localContext;
  }
  public postDownwardTraversalWhitespace(): PostDownwardTraversalWhitespaceContext {
    let localContext = new PostDownwardTraversalWhitespaceContext(this.context, this.state);
    this.enterRule(
      localContext,
      54,
      SelectionAutoCompleteParser.RULE_postDownwardTraversalWhitespace,
    );
    try {
      let alternative: number;
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 271;
        this.errorHandler.sync(this);
        alternative = this.interpreter.adaptivePredict(this.tokenStream, 16, this.context);
        while (alternative !== 2 && alternative !== antlr.ATN.INVALID_ALT_NUMBER) {
          if (alternative === 1) {
            {
              {
                this.state = 268;
                this.match(SelectionAutoCompleteParser.WS);
              }
            }
          }
          this.state = 273;
          this.errorHandler.sync(this);
          alternative = this.interpreter.adaptivePredict(this.tokenStream, 16, this.context);
        }
      }
    } catch (re) {
      if (re instanceof antlr.RecognitionException) {
        this.errorHandler.reportError(this, re);
        this.errorHandler.recover(this, re);
      } else {
        throw re;
      }
    } finally {
      this.exitRule();
    }
    return localContext;
  }
  public postDigitsWhitespace(): PostDigitsWhitespaceContext {
    let localContext = new PostDigitsWhitespaceContext(this.context, this.state);
    this.enterRule(localContext, 56, SelectionAutoCompleteParser.RULE_postDigitsWhitespace);
    let _la: number;
    try {
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 277;
        this.errorHandler.sync(this);
        _la = this.tokenStream.LA(1);
        while (_la === 16) {
          {
            {
              this.state = 274;
              this.match(SelectionAutoCompleteParser.WS);
            }
          }
          this.state = 279;
          this.errorHandler.sync(this);
          _la = this.tokenStream.LA(1);
        }
      }
    } catch (re) {
      if (re instanceof antlr.RecognitionException) {
        this.errorHandler.reportError(this, re);
        this.errorHandler.recover(this, re);
      } else {
        throw re;
      }
    } finally {
      this.exitRule();
    }
    return localContext;
  }
  public value(): ValueContext {
    let localContext = new ValueContext(this.context, this.state);
    this.enterRule(localContext, 58, SelectionAutoCompleteParser.RULE_value);
    try {
      this.state = 286;
      this.errorHandler.sync(this);
      switch (this.tokenStream.LA(1)) {
        case SelectionAutoCompleteParser.QUOTED_STRING:
          localContext = new QuotedStringValueContext(localContext);
          this.enterOuterAlt(localContext, 1);
          {
            this.state = 280;
            this.match(SelectionAutoCompleteParser.QUOTED_STRING);
          }
          break;
        case SelectionAutoCompleteParser.INCOMPLETE_LEFT_QUOTED_STRING:
          localContext = new IncompleteLeftQuotedStringValueContext(localContext);
          this.enterOuterAlt(localContext, 2);
          {
            this.state = 281;
            this.match(SelectionAutoCompleteParser.INCOMPLETE_LEFT_QUOTED_STRING);
          }
          break;
        case SelectionAutoCompleteParser.INCOMPLETE_RIGHT_QUOTED_STRING:
          localContext = new IncompleteRightQuotedStringValueContext(localContext);
          this.enterOuterAlt(localContext, 3);
          {
            this.state = 282;
            this.match(SelectionAutoCompleteParser.INCOMPLETE_RIGHT_QUOTED_STRING);
          }
          break;
        case SelectionAutoCompleteParser.IDENTIFIER:
          localContext = new UnquotedStringValueContext(localContext);
          this.enterOuterAlt(localContext, 4);
          {
            this.state = 283;
            this.match(SelectionAutoCompleteParser.IDENTIFIER);
          }
          break;
        case SelectionAutoCompleteParser.NULL_STRING:
          localContext = new NullStringValueContext(localContext);
          this.enterOuterAlt(localContext, 5);
          {
            this.state = 284;
            this.match(SelectionAutoCompleteParser.NULL_STRING);
          }
          break;
        case SelectionAutoCompleteParser.DIGITS:
          localContext = new DigitsValueContext(localContext);
          this.enterOuterAlt(localContext, 6);
          {
            this.state = 285;
            this.match(SelectionAutoCompleteParser.DIGITS);
          }
          break;
        default:
          throw new antlr.NoViableAltException(this);
      }
    } catch (re) {
      if (re instanceof antlr.RecognitionException) {
        this.errorHandler.reportError(this, re);
        this.errorHandler.recover(this, re);
      } else {
        throw re;
      }
    } finally {
      this.exitRule();
    }
    return localContext;
  }

  public override sempred(
    localContext: antlr.ParserRuleContext | null,
    ruleIndex: number,
    predIndex: number,
  ): boolean {
    switch (ruleIndex) {
      case 1:
        return this.expr_sempred(localContext as ExprContext, predIndex);
    }
    return true;
  }
  private expr_sempred(localContext: ExprContext | null, predIndex: number): boolean {
    switch (predIndex) {
      case 0:
        return this.precpred(this.context, 10);
      case 1:
        return this.precpred(this.context, 9);
      case 2:
        return this.precpred(this.context, 8);
      case 3:
        return this.precpred(this.context, 7);
      case 4:
        return this.precpred(this.context, 6);
      case 5:
        return this.precpred(this.context, 5);
    }
    return true;
  }

  public static readonly _serializedATN: number[] = [
    4, 1, 17, 289, 2, 0, 7, 0, 2, 1, 7, 1, 2, 2, 7, 2, 2, 3, 7, 3, 2, 4, 7, 4, 2, 5, 7, 5, 2, 6, 7,
    6, 2, 7, 7, 7, 2, 8, 7, 8, 2, 9, 7, 9, 2, 10, 7, 10, 2, 11, 7, 11, 2, 12, 7, 12, 2, 13, 7, 13,
    2, 14, 7, 14, 2, 15, 7, 15, 2, 16, 7, 16, 2, 17, 7, 17, 2, 18, 7, 18, 2, 19, 7, 19, 2, 20, 7,
    20, 2, 21, 7, 21, 2, 22, 7, 22, 2, 23, 7, 23, 2, 24, 7, 24, 2, 25, 7, 25, 2, 26, 7, 26, 2, 27,
    7, 27, 2, 28, 7, 28, 2, 29, 7, 29, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 3, 1, 89, 8, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 5, 1, 115, 8, 1, 10,
    1, 12, 1, 118, 9, 1, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 3, 2, 125, 8, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1,
    2, 1, 2, 1, 2, 3, 2, 134, 8, 2, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 4, 1, 4, 1, 4, 1, 4, 1,
    4, 1, 4, 1, 4, 1, 4, 1, 4, 1, 4, 1, 4, 1, 4, 1, 4, 1, 4, 1, 4, 1, 4, 1, 4, 1, 4, 1, 4, 1, 4, 1,
    4, 1, 4, 1, 4, 1, 4, 1, 4, 1, 4, 1, 4, 1, 4, 1, 4, 1, 4, 3, 4, 172, 8, 4, 1, 4, 1, 4, 1, 4, 1,
    4, 1, 4, 1, 4, 1, 4, 1, 4, 1, 4, 1, 4, 3, 4, 184, 8, 4, 1, 5, 1, 5, 1, 5, 1, 5, 1, 5, 1, 6, 1,
    6, 1, 6, 1, 7, 1, 7, 1, 7, 1, 8, 3, 8, 198, 8, 8, 1, 8, 1, 8, 1, 9, 1, 9, 3, 9, 204, 8, 9, 1,
    10, 1, 10, 1, 11, 1, 11, 1, 12, 1, 12, 1, 13, 1, 13, 1, 13, 1, 14, 1, 14, 1, 15, 1, 15, 1, 16,
    1, 16, 1, 17, 1, 17, 1, 18, 1, 18, 1, 19, 1, 19, 1, 20, 5, 20, 228, 8, 20, 10, 20, 12, 20, 231,
    9, 20, 1, 21, 5, 21, 234, 8, 21, 10, 21, 12, 21, 237, 9, 21, 1, 22, 5, 22, 240, 8, 22, 10, 22,
    12, 22, 243, 9, 22, 1, 23, 5, 23, 246, 8, 23, 10, 23, 12, 23, 249, 9, 23, 1, 24, 5, 24, 252, 8,
    24, 10, 24, 12, 24, 255, 9, 24, 1, 25, 5, 25, 258, 8, 25, 10, 25, 12, 25, 261, 9, 25, 1, 26, 5,
    26, 264, 8, 26, 10, 26, 12, 26, 267, 9, 26, 1, 27, 5, 27, 270, 8, 27, 10, 27, 12, 27, 273, 9,
    27, 1, 28, 5, 28, 276, 8, 28, 10, 28, 12, 28, 279, 9, 28, 1, 29, 1, 29, 1, 29, 1, 29, 1, 29, 1,
    29, 3, 29, 287, 8, 29, 1, 29, 0, 1, 2, 30, 0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26,
    28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 50, 52, 54, 56, 58, 0, 0, 303, 0, 60, 1, 0, 0, 0, 2,
    88, 1, 0, 0, 0, 4, 133, 1, 0, 0, 0, 6, 135, 1, 0, 0, 0, 8, 183, 1, 0, 0, 0, 10, 185, 1, 0, 0, 0,
    12, 190, 1, 0, 0, 0, 14, 193, 1, 0, 0, 0, 16, 197, 1, 0, 0, 0, 18, 201, 1, 0, 0, 0, 20, 205, 1,
    0, 0, 0, 22, 207, 1, 0, 0, 0, 24, 209, 1, 0, 0, 0, 26, 211, 1, 0, 0, 0, 28, 214, 1, 0, 0, 0, 30,
    216, 1, 0, 0, 0, 32, 218, 1, 0, 0, 0, 34, 220, 1, 0, 0, 0, 36, 222, 1, 0, 0, 0, 38, 224, 1, 0,
    0, 0, 40, 229, 1, 0, 0, 0, 42, 235, 1, 0, 0, 0, 44, 241, 1, 0, 0, 0, 46, 247, 1, 0, 0, 0, 48,
    253, 1, 0, 0, 0, 50, 259, 1, 0, 0, 0, 52, 265, 1, 0, 0, 0, 54, 271, 1, 0, 0, 0, 56, 277, 1, 0,
    0, 0, 58, 286, 1, 0, 0, 0, 60, 61, 3, 2, 1, 0, 61, 62, 5, 0, 0, 1, 62, 1, 1, 0, 0, 0, 63, 64, 6,
    1, -1, 0, 64, 89, 3, 4, 2, 0, 65, 66, 3, 12, 6, 0, 66, 67, 3, 4, 2, 0, 67, 68, 3, 14, 7, 0, 68,
    89, 1, 0, 0, 0, 69, 70, 3, 12, 6, 0, 70, 71, 3, 4, 2, 0, 71, 89, 1, 0, 0, 0, 72, 73, 3, 4, 2, 0,
    73, 74, 3, 14, 7, 0, 74, 89, 1, 0, 0, 0, 75, 76, 3, 32, 16, 0, 76, 77, 3, 46, 23, 0, 77, 78, 3,
    2, 1, 11, 78, 89, 1, 0, 0, 0, 79, 80, 3, 32, 16, 0, 80, 81, 3, 46, 23, 0, 81, 89, 1, 0, 0, 0,
    82, 83, 5, 4, 0, 0, 83, 89, 3, 44, 22, 0, 84, 85, 3, 58, 29, 0, 85, 86, 3, 44, 22, 0, 86, 89, 1,
    0, 0, 0, 87, 89, 3, 26, 13, 0, 88, 63, 1, 0, 0, 0, 88, 65, 1, 0, 0, 0, 88, 69, 1, 0, 0, 0, 88,
    72, 1, 0, 0, 0, 88, 75, 1, 0, 0, 0, 88, 79, 1, 0, 0, 0, 88, 82, 1, 0, 0, 0, 88, 84, 1, 0, 0, 0,
    88, 87, 1, 0, 0, 0, 89, 116, 1, 0, 0, 0, 90, 91, 10, 10, 0, 0, 91, 92, 3, 30, 15, 0, 92, 93, 3,
    48, 24, 0, 93, 94, 3, 2, 1, 11, 94, 115, 1, 0, 0, 0, 95, 96, 10, 9, 0, 0, 96, 97, 3, 28, 14, 0,
    97, 98, 3, 48, 24, 0, 98, 99, 3, 2, 1, 10, 99, 115, 1, 0, 0, 0, 100, 101, 10, 8, 0, 0, 101, 102,
    3, 26, 13, 0, 102, 103, 3, 2, 1, 9, 103, 115, 1, 0, 0, 0, 104, 105, 10, 7, 0, 0, 105, 106, 3,
    30, 15, 0, 106, 107, 3, 48, 24, 0, 107, 115, 1, 0, 0, 0, 108, 109, 10, 6, 0, 0, 109, 110, 3, 28,
    14, 0, 110, 111, 3, 48, 24, 0, 111, 115, 1, 0, 0, 0, 112, 113, 10, 5, 0, 0, 113, 115, 3, 26, 13,
    0, 114, 90, 1, 0, 0, 0, 114, 95, 1, 0, 0, 0, 114, 100, 1, 0, 0, 0, 114, 104, 1, 0, 0, 0, 114,
    108, 1, 0, 0, 0, 114, 112, 1, 0, 0, 0, 115, 118, 1, 0, 0, 0, 116, 114, 1, 0, 0, 0, 116, 117, 1,
    0, 0, 0, 117, 3, 1, 0, 0, 0, 118, 116, 1, 0, 0, 0, 119, 120, 3, 20, 10, 0, 120, 121, 3, 34, 17,
    0, 121, 124, 3, 22, 11, 0, 122, 123, 5, 14, 0, 0, 123, 125, 3, 22, 11, 0, 124, 122, 1, 0, 0, 0,
    124, 125, 1, 0, 0, 0, 125, 126, 1, 0, 0, 0, 126, 127, 3, 42, 21, 0, 127, 134, 1, 0, 0, 0, 128,
    129, 3, 24, 12, 0, 129, 130, 3, 6, 3, 0, 130, 134, 1, 0, 0, 0, 131, 134, 3, 6, 3, 0, 132, 134,
    3, 8, 4, 0, 133, 119, 1, 0, 0, 0, 133, 128, 1, 0, 0, 0, 133, 131, 1, 0, 0, 0, 133, 132, 1, 0, 0,
    0, 134, 5, 1, 0, 0, 0, 135, 136, 3, 36, 18, 0, 136, 137, 3, 48, 24, 0, 137, 138, 3, 2, 1, 0,
    138, 139, 3, 38, 19, 0, 139, 140, 3, 44, 22, 0, 140, 7, 1, 0, 0, 0, 141, 142, 3, 20, 10, 0, 142,
    143, 3, 34, 17, 0, 143, 144, 3, 22, 11, 0, 144, 145, 5, 14, 0, 0, 145, 146, 3, 40, 20, 0, 146,
    184, 1, 0, 0, 0, 147, 148, 3, 20, 10, 0, 148, 149, 3, 34, 17, 0, 149, 150, 3, 40, 20, 0, 150,
    184, 1, 0, 0, 0, 151, 152, 3, 24, 12, 0, 152, 153, 3, 10, 5, 0, 153, 184, 1, 0, 0, 0, 154, 155,
    3, 24, 12, 0, 155, 156, 3, 36, 18, 0, 156, 157, 3, 48, 24, 0, 157, 184, 1, 0, 0, 0, 158, 159, 3,
    24, 12, 0, 159, 160, 3, 36, 18, 0, 160, 161, 3, 2, 1, 0, 161, 184, 1, 0, 0, 0, 162, 163, 3, 36,
    18, 0, 163, 164, 3, 48, 24, 0, 164, 165, 3, 2, 1, 0, 165, 184, 1, 0, 0, 0, 166, 184, 3, 10, 5,
    0, 167, 168, 3, 36, 18, 0, 168, 169, 3, 48, 24, 0, 169, 184, 1, 0, 0, 0, 170, 172, 5, 6, 0, 0,
    171, 170, 1, 0, 0, 0, 171, 172, 1, 0, 0, 0, 172, 173, 1, 0, 0, 0, 173, 174, 5, 5, 0, 0, 174,
    184, 3, 50, 25, 0, 175, 176, 5, 5, 0, 0, 176, 177, 3, 58, 29, 0, 177, 178, 3, 44, 22, 0, 178,
    184, 1, 0, 0, 0, 179, 180, 3, 34, 17, 0, 180, 181, 3, 22, 11, 0, 181, 182, 3, 44, 22, 0, 182,
    184, 1, 0, 0, 0, 183, 141, 1, 0, 0, 0, 183, 147, 1, 0, 0, 0, 183, 151, 1, 0, 0, 0, 183, 154, 1,
    0, 0, 0, 183, 158, 1, 0, 0, 0, 183, 162, 1, 0, 0, 0, 183, 166, 1, 0, 0, 0, 183, 167, 1, 0, 0, 0,
    183, 171, 1, 0, 0, 0, 183, 175, 1, 0, 0, 0, 183, 179, 1, 0, 0, 0, 184, 9, 1, 0, 0, 0, 185, 186,
    3, 36, 18, 0, 186, 187, 3, 48, 24, 0, 187, 188, 3, 38, 19, 0, 188, 189, 3, 44, 22, 0, 189, 11,
    1, 0, 0, 0, 190, 191, 3, 16, 8, 0, 191, 192, 3, 52, 26, 0, 192, 13, 1, 0, 0, 0, 193, 194, 3, 18,
    9, 0, 194, 195, 3, 54, 27, 0, 195, 15, 1, 0, 0, 0, 196, 198, 5, 6, 0, 0, 197, 196, 1, 0, 0, 0,
    197, 198, 1, 0, 0, 0, 198, 199, 1, 0, 0, 0, 199, 200, 5, 5, 0, 0, 200, 17, 1, 0, 0, 0, 201, 203,
    5, 5, 0, 0, 202, 204, 5, 6, 0, 0, 203, 202, 1, 0, 0, 0, 203, 204, 1, 0, 0, 0, 204, 19, 1, 0, 0,
    0, 205, 206, 5, 15, 0, 0, 206, 21, 1, 0, 0, 0, 207, 208, 3, 58, 29, 0, 208, 23, 1, 0, 0, 0, 209,
    210, 5, 15, 0, 0, 210, 25, 1, 0, 0, 0, 211, 212, 5, 17, 0, 0, 212, 213, 3, 48, 24, 0, 213, 27,
    1, 0, 0, 0, 214, 215, 5, 2, 0, 0, 215, 29, 1, 0, 0, 0, 216, 217, 5, 1, 0, 0, 217, 31, 1, 0, 0,
    0, 218, 219, 5, 3, 0, 0, 219, 33, 1, 0, 0, 0, 220, 221, 5, 7, 0, 0, 221, 35, 1, 0, 0, 0, 222,
    223, 5, 8, 0, 0, 223, 37, 1, 0, 0, 0, 224, 225, 5, 9, 0, 0, 225, 39, 1, 0, 0, 0, 226, 228, 5,
    16, 0, 0, 227, 226, 1, 0, 0, 0, 228, 231, 1, 0, 0, 0, 229, 227, 1, 0, 0, 0, 229, 230, 1, 0, 0,
    0, 230, 41, 1, 0, 0, 0, 231, 229, 1, 0, 0, 0, 232, 234, 5, 16, 0, 0, 233, 232, 1, 0, 0, 0, 234,
    237, 1, 0, 0, 0, 235, 233, 1, 0, 0, 0, 235, 236, 1, 0, 0, 0, 236, 43, 1, 0, 0, 0, 237, 235, 1,
    0, 0, 0, 238, 240, 5, 16, 0, 0, 239, 238, 1, 0, 0, 0, 240, 243, 1, 0, 0, 0, 241, 239, 1, 0, 0,
    0, 241, 242, 1, 0, 0, 0, 242, 45, 1, 0, 0, 0, 243, 241, 1, 0, 0, 0, 244, 246, 5, 16, 0, 0, 245,
    244, 1, 0, 0, 0, 246, 249, 1, 0, 0, 0, 247, 245, 1, 0, 0, 0, 247, 248, 1, 0, 0, 0, 248, 47, 1,
    0, 0, 0, 249, 247, 1, 0, 0, 0, 250, 252, 5, 16, 0, 0, 251, 250, 1, 0, 0, 0, 252, 255, 1, 0, 0,
    0, 253, 251, 1, 0, 0, 0, 253, 254, 1, 0, 0, 0, 254, 49, 1, 0, 0, 0, 255, 253, 1, 0, 0, 0, 256,
    258, 5, 16, 0, 0, 257, 256, 1, 0, 0, 0, 258, 261, 1, 0, 0, 0, 259, 257, 1, 0, 0, 0, 259, 260, 1,
    0, 0, 0, 260, 51, 1, 0, 0, 0, 261, 259, 1, 0, 0, 0, 262, 264, 5, 16, 0, 0, 263, 262, 1, 0, 0, 0,
    264, 267, 1, 0, 0, 0, 265, 263, 1, 0, 0, 0, 265, 266, 1, 0, 0, 0, 266, 53, 1, 0, 0, 0, 267, 265,
    1, 0, 0, 0, 268, 270, 5, 16, 0, 0, 269, 268, 1, 0, 0, 0, 270, 273, 1, 0, 0, 0, 271, 269, 1, 0,
    0, 0, 271, 272, 1, 0, 0, 0, 272, 55, 1, 0, 0, 0, 273, 271, 1, 0, 0, 0, 274, 276, 5, 16, 0, 0,
    275, 274, 1, 0, 0, 0, 276, 279, 1, 0, 0, 0, 277, 275, 1, 0, 0, 0, 277, 278, 1, 0, 0, 0, 278, 57,
    1, 0, 0, 0, 279, 277, 1, 0, 0, 0, 280, 287, 5, 10, 0, 0, 281, 287, 5, 11, 0, 0, 282, 287, 5, 12,
    0, 0, 283, 287, 5, 15, 0, 0, 284, 287, 5, 13, 0, 0, 285, 287, 5, 6, 0, 0, 286, 280, 1, 0, 0, 0,
    286, 281, 1, 0, 0, 0, 286, 282, 1, 0, 0, 0, 286, 283, 1, 0, 0, 0, 286, 284, 1, 0, 0, 0, 286,
    285, 1, 0, 0, 0, 287, 59, 1, 0, 0, 0, 19, 88, 114, 116, 124, 133, 171, 183, 197, 203, 229, 235,
    241, 247, 253, 259, 265, 271, 277, 286,
  ];

  private static __ATN: antlr.ATN;
  public static get _ATN(): antlr.ATN {
    if (!SelectionAutoCompleteParser.__ATN) {
      SelectionAutoCompleteParser.__ATN = new antlr.ATNDeserializer().deserialize(
        SelectionAutoCompleteParser._serializedATN,
      );
    }

    return SelectionAutoCompleteParser.__ATN;
  }

  private static readonly vocabulary = new antlr.Vocabulary(
    SelectionAutoCompleteParser.literalNames,
    SelectionAutoCompleteParser.symbolicNames,
    [],
  );

  public override get vocabulary(): antlr.Vocabulary {
    return SelectionAutoCompleteParser.vocabulary;
  }

  private static readonly decisionsToDFA = SelectionAutoCompleteParser._ATN.decisionToState.map(
    (ds: antlr.DecisionState, index: number) => new antlr.DFA(ds, index),
  );
}

export class StartContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public expr(): ExprContext {
    return this.getRuleContext(0, ExprContext)!;
  }
  public EOF(): antlr.TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.EOF, 0)!;
  }
  public override get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_start;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterStart) {
      listener.enterStart(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitStart) {
      listener.exitStart(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitStart) {
      return visitor.visitStart(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class ExprContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public override get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_expr;
  }
  public override copyFrom(ctx: ExprContext): void {
    super.copyFrom(ctx);
  }
}
export class CommaExpressionWrapper3Context extends ExprContext {
  public constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public commaToken(): CommaTokenContext {
    return this.getRuleContext(0, CommaTokenContext)!;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterCommaExpressionWrapper3) {
      listener.enterCommaExpressionWrapper3(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitCommaExpressionWrapper3) {
      listener.exitCommaExpressionWrapper3(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitCommaExpressionWrapper3) {
      return visitor.visitCommaExpressionWrapper3(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class UpTraversalExpressionContext extends ExprContext {
  public constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public upTraversalExpr(): UpTraversalExprContext {
    return this.getRuleContext(0, UpTraversalExprContext)!;
  }
  public traversalAllowedExpr(): TraversalAllowedExprContext {
    return this.getRuleContext(0, TraversalAllowedExprContext)!;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterUpTraversalExpression) {
      listener.enterUpTraversalExpression(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitUpTraversalExpression) {
      listener.exitUpTraversalExpression(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitUpTraversalExpression) {
      return visitor.visitUpTraversalExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class CommaExpressionWrapper2Context extends ExprContext {
  public constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public expr(): ExprContext {
    return this.getRuleContext(0, ExprContext)!;
  }
  public commaToken(): CommaTokenContext {
    return this.getRuleContext(0, CommaTokenContext)!;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterCommaExpressionWrapper2) {
      listener.enterCommaExpressionWrapper2(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitCommaExpressionWrapper2) {
      listener.exitCommaExpressionWrapper2(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitCommaExpressionWrapper2) {
      return visitor.visitCommaExpressionWrapper2(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class CommaExpressionWrapper1Context extends ExprContext {
  public constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public expr(): ExprContext[];
  public expr(i: number): ExprContext | null;
  public expr(i?: number): ExprContext[] | ExprContext | null {
    if (i === undefined) {
      return this.getRuleContexts(ExprContext);
    }

    return this.getRuleContext(i, ExprContext);
  }
  public commaToken(): CommaTokenContext {
    return this.getRuleContext(0, CommaTokenContext)!;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterCommaExpressionWrapper1) {
      listener.enterCommaExpressionWrapper1(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitCommaExpressionWrapper1) {
      listener.exitCommaExpressionWrapper1(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitCommaExpressionWrapper1) {
      return visitor.visitCommaExpressionWrapper1(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class AllExpressionContext extends ExprContext {
  public constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public STAR(): antlr.TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.STAR, 0)!;
  }
  public postExpressionWhitespace(): PostExpressionWhitespaceContext {
    return this.getRuleContext(0, PostExpressionWhitespaceContext)!;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterAllExpression) {
      listener.enterAllExpression(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitAllExpression) {
      listener.exitAllExpression(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitAllExpression) {
      return visitor.visitAllExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class NotExpressionContext extends ExprContext {
  public constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public notToken(): NotTokenContext {
    return this.getRuleContext(0, NotTokenContext)!;
  }
  public postNotOperatorWhitespace(): PostNotOperatorWhitespaceContext {
    return this.getRuleContext(0, PostNotOperatorWhitespaceContext)!;
  }
  public expr(): ExprContext {
    return this.getRuleContext(0, ExprContext)!;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterNotExpression) {
      listener.enterNotExpression(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitNotExpression) {
      listener.exitNotExpression(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitNotExpression) {
      return visitor.visitNotExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class OrExpressionContext extends ExprContext {
  public constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public expr(): ExprContext[];
  public expr(i: number): ExprContext | null;
  public expr(i?: number): ExprContext[] | ExprContext | null {
    if (i === undefined) {
      return this.getRuleContexts(ExprContext);
    }

    return this.getRuleContext(i, ExprContext);
  }
  public orToken(): OrTokenContext {
    return this.getRuleContext(0, OrTokenContext)!;
  }
  public postLogicalOperatorWhitespace(): PostLogicalOperatorWhitespaceContext {
    return this.getRuleContext(0, PostLogicalOperatorWhitespaceContext)!;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterOrExpression) {
      listener.enterOrExpression(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitOrExpression) {
      listener.exitOrExpression(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitOrExpression) {
      return visitor.visitOrExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class UpAndDownTraversalExpressionContext extends ExprContext {
  public constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public upTraversalExpr(): UpTraversalExprContext {
    return this.getRuleContext(0, UpTraversalExprContext)!;
  }
  public traversalAllowedExpr(): TraversalAllowedExprContext {
    return this.getRuleContext(0, TraversalAllowedExprContext)!;
  }
  public downTraversalExpr(): DownTraversalExprContext {
    return this.getRuleContext(0, DownTraversalExprContext)!;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterUpAndDownTraversalExpression) {
      listener.enterUpAndDownTraversalExpression(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitUpAndDownTraversalExpression) {
      listener.exitUpAndDownTraversalExpression(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitUpAndDownTraversalExpression) {
      return visitor.visitUpAndDownTraversalExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class UnmatchedValueContext extends ExprContext {
  public constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public value(): ValueContext {
    return this.getRuleContext(0, ValueContext)!;
  }
  public postExpressionWhitespace(): PostExpressionWhitespaceContext {
    return this.getRuleContext(0, PostExpressionWhitespaceContext)!;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterUnmatchedValue) {
      listener.enterUnmatchedValue(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitUnmatchedValue) {
      listener.exitUnmatchedValue(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitUnmatchedValue) {
      return visitor.visitUnmatchedValue(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class AndExpressionContext extends ExprContext {
  public constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public expr(): ExprContext[];
  public expr(i: number): ExprContext | null;
  public expr(i?: number): ExprContext[] | ExprContext | null {
    if (i === undefined) {
      return this.getRuleContexts(ExprContext);
    }

    return this.getRuleContext(i, ExprContext);
  }
  public andToken(): AndTokenContext {
    return this.getRuleContext(0, AndTokenContext)!;
  }
  public postLogicalOperatorWhitespace(): PostLogicalOperatorWhitespaceContext {
    return this.getRuleContext(0, PostLogicalOperatorWhitespaceContext)!;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterAndExpression) {
      listener.enterAndExpression(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitAndExpression) {
      listener.exitAndExpression(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitAndExpression) {
      return visitor.visitAndExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class TraversalAllowedExpressionContext extends ExprContext {
  public constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public traversalAllowedExpr(): TraversalAllowedExprContext {
    return this.getRuleContext(0, TraversalAllowedExprContext)!;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterTraversalAllowedExpression) {
      listener.enterTraversalAllowedExpression(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitTraversalAllowedExpression) {
      listener.exitTraversalAllowedExpression(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitTraversalAllowedExpression) {
      return visitor.visitTraversalAllowedExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class DownTraversalExpressionContext extends ExprContext {
  public constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public traversalAllowedExpr(): TraversalAllowedExprContext {
    return this.getRuleContext(0, TraversalAllowedExprContext)!;
  }
  public downTraversalExpr(): DownTraversalExprContext {
    return this.getRuleContext(0, DownTraversalExprContext)!;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterDownTraversalExpression) {
      listener.enterDownTraversalExpression(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitDownTraversalExpression) {
      listener.exitDownTraversalExpression(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitDownTraversalExpression) {
      return visitor.visitDownTraversalExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class IncompleteOrExpressionContext extends ExprContext {
  public constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public expr(): ExprContext {
    return this.getRuleContext(0, ExprContext)!;
  }
  public orToken(): OrTokenContext {
    return this.getRuleContext(0, OrTokenContext)!;
  }
  public postLogicalOperatorWhitespace(): PostLogicalOperatorWhitespaceContext {
    return this.getRuleContext(0, PostLogicalOperatorWhitespaceContext)!;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterIncompleteOrExpression) {
      listener.enterIncompleteOrExpression(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitIncompleteOrExpression) {
      listener.exitIncompleteOrExpression(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitIncompleteOrExpression) {
      return visitor.visitIncompleteOrExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class IncompleteNotExpressionContext extends ExprContext {
  public constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public notToken(): NotTokenContext {
    return this.getRuleContext(0, NotTokenContext)!;
  }
  public postNotOperatorWhitespace(): PostNotOperatorWhitespaceContext {
    return this.getRuleContext(0, PostNotOperatorWhitespaceContext)!;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterIncompleteNotExpression) {
      listener.enterIncompleteNotExpression(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitIncompleteNotExpression) {
      listener.exitIncompleteNotExpression(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitIncompleteNotExpression) {
      return visitor.visitIncompleteNotExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class IncompleteAndExpressionContext extends ExprContext {
  public constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public expr(): ExprContext {
    return this.getRuleContext(0, ExprContext)!;
  }
  public andToken(): AndTokenContext {
    return this.getRuleContext(0, AndTokenContext)!;
  }
  public postLogicalOperatorWhitespace(): PostLogicalOperatorWhitespaceContext {
    return this.getRuleContext(0, PostLogicalOperatorWhitespaceContext)!;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterIncompleteAndExpression) {
      listener.enterIncompleteAndExpression(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitIncompleteAndExpression) {
      listener.exitIncompleteAndExpression(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitIncompleteAndExpression) {
      return visitor.visitIncompleteAndExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class TraversalAllowedExprContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public override get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_traversalAllowedExpr;
  }
  public override copyFrom(ctx: TraversalAllowedExprContext): void {
    super.copyFrom(ctx);
  }
}
export class TraversalAllowedParenthesizedExpressionContext extends TraversalAllowedExprContext {
  public constructor(ctx: TraversalAllowedExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public parenthesizedExpr(): ParenthesizedExprContext {
    return this.getRuleContext(0, ParenthesizedExprContext)!;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterTraversalAllowedParenthesizedExpression) {
      listener.enterTraversalAllowedParenthesizedExpression(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitTraversalAllowedParenthesizedExpression) {
      listener.exitTraversalAllowedParenthesizedExpression(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitTraversalAllowedParenthesizedExpression) {
      return visitor.visitTraversalAllowedParenthesizedExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class IncompleteExpressionContext extends TraversalAllowedExprContext {
  public constructor(ctx: TraversalAllowedExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public incompleteExpr(): IncompleteExprContext {
    return this.getRuleContext(0, IncompleteExprContext)!;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterIncompleteExpression) {
      listener.enterIncompleteExpression(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitIncompleteExpression) {
      listener.exitIncompleteExpression(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitIncompleteExpression) {
      return visitor.visitIncompleteExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class AttributeExpressionContext extends TraversalAllowedExprContext {
  public constructor(ctx: TraversalAllowedExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public attributeName(): AttributeNameContext {
    return this.getRuleContext(0, AttributeNameContext)!;
  }
  public colonToken(): ColonTokenContext {
    return this.getRuleContext(0, ColonTokenContext)!;
  }
  public attributeValue(): AttributeValueContext[];
  public attributeValue(i: number): AttributeValueContext | null;
  public attributeValue(i?: number): AttributeValueContext[] | AttributeValueContext | null {
    if (i === undefined) {
      return this.getRuleContexts(AttributeValueContext);
    }

    return this.getRuleContext(i, AttributeValueContext);
  }
  public postAttributeValueWhitespace(): PostAttributeValueWhitespaceContext {
    return this.getRuleContext(0, PostAttributeValueWhitespaceContext)!;
  }
  public EQUAL(): antlr.TerminalNode | null {
    return this.getToken(SelectionAutoCompleteParser.EQUAL, 0);
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterAttributeExpression) {
      listener.enterAttributeExpression(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitAttributeExpression) {
      listener.exitAttributeExpression(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitAttributeExpression) {
      return visitor.visitAttributeExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class FunctionCallExpressionContext extends TraversalAllowedExprContext {
  public constructor(ctx: TraversalAllowedExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public functionName(): FunctionNameContext {
    return this.getRuleContext(0, FunctionNameContext)!;
  }
  public parenthesizedExpr(): ParenthesizedExprContext {
    return this.getRuleContext(0, ParenthesizedExprContext)!;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterFunctionCallExpression) {
      listener.enterFunctionCallExpression(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitFunctionCallExpression) {
      listener.exitFunctionCallExpression(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitFunctionCallExpression) {
      return visitor.visitFunctionCallExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class ParenthesizedExprContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public override get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_parenthesizedExpr;
  }
  public override copyFrom(ctx: ParenthesizedExprContext): void {
    super.copyFrom(ctx);
  }
}
export class ParenthesizedExpressionContext extends ParenthesizedExprContext {
  public constructor(ctx: ParenthesizedExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public leftParenToken(): LeftParenTokenContext {
    return this.getRuleContext(0, LeftParenTokenContext)!;
  }
  public postLogicalOperatorWhitespace(): PostLogicalOperatorWhitespaceContext {
    return this.getRuleContext(0, PostLogicalOperatorWhitespaceContext)!;
  }
  public expr(): ExprContext {
    return this.getRuleContext(0, ExprContext)!;
  }
  public rightParenToken(): RightParenTokenContext {
    return this.getRuleContext(0, RightParenTokenContext)!;
  }
  public postExpressionWhitespace(): PostExpressionWhitespaceContext {
    return this.getRuleContext(0, PostExpressionWhitespaceContext)!;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterParenthesizedExpression) {
      listener.enterParenthesizedExpression(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitParenthesizedExpression) {
      listener.exitParenthesizedExpression(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitParenthesizedExpression) {
      return visitor.visitParenthesizedExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class IncompleteExprContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public override get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_incompleteExpr;
  }
  public override copyFrom(ctx: IncompleteExprContext): void {
    super.copyFrom(ctx);
  }
}
export class ExpressionlessFunctionExpressionContext extends IncompleteExprContext {
  public constructor(ctx: IncompleteExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public functionName(): FunctionNameContext {
    return this.getRuleContext(0, FunctionNameContext)!;
  }
  public expressionLessParenthesizedExpr(): ExpressionLessParenthesizedExprContext {
    return this.getRuleContext(0, ExpressionLessParenthesizedExprContext)!;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterExpressionlessFunctionExpression) {
      listener.enterExpressionlessFunctionExpression(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitExpressionlessFunctionExpression) {
      listener.exitExpressionlessFunctionExpression(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitExpressionlessFunctionExpression) {
      return visitor.visitExpressionlessFunctionExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class UnclosedExpressionlessFunctionExpressionContext extends IncompleteExprContext {
  public constructor(ctx: IncompleteExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public functionName(): FunctionNameContext {
    return this.getRuleContext(0, FunctionNameContext)!;
  }
  public leftParenToken(): LeftParenTokenContext {
    return this.getRuleContext(0, LeftParenTokenContext)!;
  }
  public postLogicalOperatorWhitespace(): PostLogicalOperatorWhitespaceContext {
    return this.getRuleContext(0, PostLogicalOperatorWhitespaceContext)!;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterUnclosedExpressionlessFunctionExpression) {
      listener.enterUnclosedExpressionlessFunctionExpression(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitUnclosedExpressionlessFunctionExpression) {
      listener.exitUnclosedExpressionlessFunctionExpression(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitUnclosedExpressionlessFunctionExpression) {
      return visitor.visitUnclosedExpressionlessFunctionExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class UnclosedExpressionlessParenthesizedExpressionContext extends IncompleteExprContext {
  public constructor(ctx: IncompleteExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public leftParenToken(): LeftParenTokenContext {
    return this.getRuleContext(0, LeftParenTokenContext)!;
  }
  public postLogicalOperatorWhitespace(): PostLogicalOperatorWhitespaceContext {
    return this.getRuleContext(0, PostLogicalOperatorWhitespaceContext)!;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterUnclosedExpressionlessParenthesizedExpression) {
      listener.enterUnclosedExpressionlessParenthesizedExpression(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitUnclosedExpressionlessParenthesizedExpression) {
      listener.exitUnclosedExpressionlessParenthesizedExpression(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitUnclosedExpressionlessParenthesizedExpression) {
      return visitor.visitUnclosedExpressionlessParenthesizedExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class IncompletePlusTraversalExpressionMissingValueContext extends IncompleteExprContext {
  public constructor(ctx: IncompleteExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public PLUS(): antlr.TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.PLUS, 0)!;
  }
  public value(): ValueContext {
    return this.getRuleContext(0, ValueContext)!;
  }
  public postExpressionWhitespace(): PostExpressionWhitespaceContext {
    return this.getRuleContext(0, PostExpressionWhitespaceContext)!;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterIncompletePlusTraversalExpressionMissingValue) {
      listener.enterIncompletePlusTraversalExpressionMissingValue(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitIncompletePlusTraversalExpressionMissingValue) {
      listener.exitIncompletePlusTraversalExpressionMissingValue(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitIncompletePlusTraversalExpressionMissingValue) {
      return visitor.visitIncompletePlusTraversalExpressionMissingValue(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class IncompleteAttributeExpressionMissingKeyContext extends IncompleteExprContext {
  public constructor(ctx: IncompleteExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public colonToken(): ColonTokenContext {
    return this.getRuleContext(0, ColonTokenContext)!;
  }
  public attributeValue(): AttributeValueContext {
    return this.getRuleContext(0, AttributeValueContext)!;
  }
  public postExpressionWhitespace(): PostExpressionWhitespaceContext {
    return this.getRuleContext(0, PostExpressionWhitespaceContext)!;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterIncompleteAttributeExpressionMissingKey) {
      listener.enterIncompleteAttributeExpressionMissingKey(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitIncompleteAttributeExpressionMissingKey) {
      listener.exitIncompleteAttributeExpressionMissingKey(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitIncompleteAttributeExpressionMissingKey) {
      return visitor.visitIncompleteAttributeExpressionMissingKey(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class UnclosedParenthesizedExpressionContext extends IncompleteExprContext {
  public constructor(ctx: IncompleteExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public leftParenToken(): LeftParenTokenContext {
    return this.getRuleContext(0, LeftParenTokenContext)!;
  }
  public postLogicalOperatorWhitespace(): PostLogicalOperatorWhitespaceContext {
    return this.getRuleContext(0, PostLogicalOperatorWhitespaceContext)!;
  }
  public expr(): ExprContext {
    return this.getRuleContext(0, ExprContext)!;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterUnclosedParenthesizedExpression) {
      listener.enterUnclosedParenthesizedExpression(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitUnclosedParenthesizedExpression) {
      listener.exitUnclosedParenthesizedExpression(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitUnclosedParenthesizedExpression) {
      return visitor.visitUnclosedParenthesizedExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class IncompleteAttributeExpressionMissingValueContext extends IncompleteExprContext {
  public constructor(ctx: IncompleteExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public attributeName(): AttributeNameContext {
    return this.getRuleContext(0, AttributeNameContext)!;
  }
  public colonToken(): ColonTokenContext {
    return this.getRuleContext(0, ColonTokenContext)!;
  }
  public attributeValueWhitespace(): AttributeValueWhitespaceContext {
    return this.getRuleContext(0, AttributeValueWhitespaceContext)!;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterIncompleteAttributeExpressionMissingValue) {
      listener.enterIncompleteAttributeExpressionMissingValue(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitIncompleteAttributeExpressionMissingValue) {
      listener.exitIncompleteAttributeExpressionMissingValue(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitIncompleteAttributeExpressionMissingValue) {
      return visitor.visitIncompleteAttributeExpressionMissingValue(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class UnclosedFunctionExpressionContext extends IncompleteExprContext {
  public constructor(ctx: IncompleteExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public functionName(): FunctionNameContext {
    return this.getRuleContext(0, FunctionNameContext)!;
  }
  public leftParenToken(): LeftParenTokenContext {
    return this.getRuleContext(0, LeftParenTokenContext)!;
  }
  public expr(): ExprContext {
    return this.getRuleContext(0, ExprContext)!;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterUnclosedFunctionExpression) {
      listener.enterUnclosedFunctionExpression(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitUnclosedFunctionExpression) {
      listener.exitUnclosedFunctionExpression(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitUnclosedFunctionExpression) {
      return visitor.visitUnclosedFunctionExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class ExpressionlessParenthesizedExpressionWrapperContext extends IncompleteExprContext {
  public constructor(ctx: IncompleteExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public expressionLessParenthesizedExpr(): ExpressionLessParenthesizedExprContext {
    return this.getRuleContext(0, ExpressionLessParenthesizedExprContext)!;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterExpressionlessParenthesizedExpressionWrapper) {
      listener.enterExpressionlessParenthesizedExpressionWrapper(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitExpressionlessParenthesizedExpressionWrapper) {
      listener.exitExpressionlessParenthesizedExpressionWrapper(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitExpressionlessParenthesizedExpressionWrapper) {
      return visitor.visitExpressionlessParenthesizedExpressionWrapper(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class IncompletePlusTraversalExpressionContext extends IncompleteExprContext {
  public constructor(ctx: IncompleteExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public PLUS(): antlr.TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.PLUS, 0)!;
  }
  public postNeighborTraversalWhitespace(): PostNeighborTraversalWhitespaceContext {
    return this.getRuleContext(0, PostNeighborTraversalWhitespaceContext)!;
  }
  public DIGITS(): antlr.TerminalNode | null {
    return this.getToken(SelectionAutoCompleteParser.DIGITS, 0);
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterIncompletePlusTraversalExpression) {
      listener.enterIncompletePlusTraversalExpression(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitIncompletePlusTraversalExpression) {
      listener.exitIncompletePlusTraversalExpression(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitIncompletePlusTraversalExpression) {
      return visitor.visitIncompletePlusTraversalExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class IncompleteAttributeExpressionMissingSecondValueContext extends IncompleteExprContext {
  public constructor(ctx: IncompleteExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public attributeName(): AttributeNameContext {
    return this.getRuleContext(0, AttributeNameContext)!;
  }
  public colonToken(): ColonTokenContext {
    return this.getRuleContext(0, ColonTokenContext)!;
  }
  public attributeValue(): AttributeValueContext {
    return this.getRuleContext(0, AttributeValueContext)!;
  }
  public EQUAL(): antlr.TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.EQUAL, 0)!;
  }
  public attributeValueWhitespace(): AttributeValueWhitespaceContext {
    return this.getRuleContext(0, AttributeValueWhitespaceContext)!;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterIncompleteAttributeExpressionMissingSecondValue) {
      listener.enterIncompleteAttributeExpressionMissingSecondValue(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitIncompleteAttributeExpressionMissingSecondValue) {
      listener.exitIncompleteAttributeExpressionMissingSecondValue(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitIncompleteAttributeExpressionMissingSecondValue) {
      return visitor.visitIncompleteAttributeExpressionMissingSecondValue(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class ExpressionLessParenthesizedExprContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public override get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_expressionLessParenthesizedExpr;
  }
  public override copyFrom(ctx: ExpressionLessParenthesizedExprContext): void {
    super.copyFrom(ctx);
  }
}
export class ExpressionlessParenthesizedExpressionContext extends ExpressionLessParenthesizedExprContext {
  public constructor(ctx: ExpressionLessParenthesizedExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public leftParenToken(): LeftParenTokenContext {
    return this.getRuleContext(0, LeftParenTokenContext)!;
  }
  public postLogicalOperatorWhitespace(): PostLogicalOperatorWhitespaceContext {
    return this.getRuleContext(0, PostLogicalOperatorWhitespaceContext)!;
  }
  public rightParenToken(): RightParenTokenContext {
    return this.getRuleContext(0, RightParenTokenContext)!;
  }
  public postExpressionWhitespace(): PostExpressionWhitespaceContext {
    return this.getRuleContext(0, PostExpressionWhitespaceContext)!;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterExpressionlessParenthesizedExpression) {
      listener.enterExpressionlessParenthesizedExpression(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitExpressionlessParenthesizedExpression) {
      listener.exitExpressionlessParenthesizedExpression(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitExpressionlessParenthesizedExpression) {
      return visitor.visitExpressionlessParenthesizedExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class UpTraversalExprContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public override get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_upTraversalExpr;
  }
  public override copyFrom(ctx: UpTraversalExprContext): void {
    super.copyFrom(ctx);
  }
}
export class UpTraversalContext extends UpTraversalExprContext {
  public constructor(ctx: UpTraversalExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public upTraversalToken(): UpTraversalTokenContext {
    return this.getRuleContext(0, UpTraversalTokenContext)!;
  }
  public postUpwardTraversalWhitespace(): PostUpwardTraversalWhitespaceContext {
    return this.getRuleContext(0, PostUpwardTraversalWhitespaceContext)!;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterUpTraversal) {
      listener.enterUpTraversal(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitUpTraversal) {
      listener.exitUpTraversal(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitUpTraversal) {
      return visitor.visitUpTraversal(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class DownTraversalExprContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public override get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_downTraversalExpr;
  }
  public override copyFrom(ctx: DownTraversalExprContext): void {
    super.copyFrom(ctx);
  }
}
export class DownTraversalContext extends DownTraversalExprContext {
  public constructor(ctx: DownTraversalExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public downTraversalToken(): DownTraversalTokenContext {
    return this.getRuleContext(0, DownTraversalTokenContext)!;
  }
  public postDownwardTraversalWhitespace(): PostDownwardTraversalWhitespaceContext {
    return this.getRuleContext(0, PostDownwardTraversalWhitespaceContext)!;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterDownTraversal) {
      listener.enterDownTraversal(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitDownTraversal) {
      listener.exitDownTraversal(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitDownTraversal) {
      return visitor.visitDownTraversal(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class UpTraversalTokenContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public PLUS(): antlr.TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.PLUS, 0)!;
  }
  public DIGITS(): antlr.TerminalNode | null {
    return this.getToken(SelectionAutoCompleteParser.DIGITS, 0);
  }
  public override get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_upTraversalToken;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterUpTraversalToken) {
      listener.enterUpTraversalToken(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitUpTraversalToken) {
      listener.exitUpTraversalToken(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitUpTraversalToken) {
      return visitor.visitUpTraversalToken(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class DownTraversalTokenContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public PLUS(): antlr.TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.PLUS, 0)!;
  }
  public DIGITS(): antlr.TerminalNode | null {
    return this.getToken(SelectionAutoCompleteParser.DIGITS, 0);
  }
  public override get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_downTraversalToken;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterDownTraversalToken) {
      listener.enterDownTraversalToken(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitDownTraversalToken) {
      listener.exitDownTraversalToken(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitDownTraversalToken) {
      return visitor.visitDownTraversalToken(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class AttributeNameContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public IDENTIFIER(): antlr.TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.IDENTIFIER, 0)!;
  }
  public override get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_attributeName;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterAttributeName) {
      listener.enterAttributeName(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitAttributeName) {
      listener.exitAttributeName(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitAttributeName) {
      return visitor.visitAttributeName(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class AttributeValueContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public value(): ValueContext {
    return this.getRuleContext(0, ValueContext)!;
  }
  public override get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_attributeValue;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterAttributeValue) {
      listener.enterAttributeValue(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitAttributeValue) {
      listener.exitAttributeValue(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitAttributeValue) {
      return visitor.visitAttributeValue(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class FunctionNameContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public IDENTIFIER(): antlr.TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.IDENTIFIER, 0)!;
  }
  public override get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_functionName;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterFunctionName) {
      listener.enterFunctionName(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitFunctionName) {
      listener.exitFunctionName(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitFunctionName) {
      return visitor.visitFunctionName(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class CommaTokenContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public COMMA(): antlr.TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.COMMA, 0)!;
  }
  public postLogicalOperatorWhitespace(): PostLogicalOperatorWhitespaceContext {
    return this.getRuleContext(0, PostLogicalOperatorWhitespaceContext)!;
  }
  public override get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_commaToken;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterCommaToken) {
      listener.enterCommaToken(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitCommaToken) {
      listener.exitCommaToken(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitCommaToken) {
      return visitor.visitCommaToken(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class OrTokenContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public OR(): antlr.TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.OR, 0)!;
  }
  public override get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_orToken;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterOrToken) {
      listener.enterOrToken(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitOrToken) {
      listener.exitOrToken(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitOrToken) {
      return visitor.visitOrToken(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class AndTokenContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public AND(): antlr.TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.AND, 0)!;
  }
  public override get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_andToken;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterAndToken) {
      listener.enterAndToken(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitAndToken) {
      listener.exitAndToken(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitAndToken) {
      return visitor.visitAndToken(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class NotTokenContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public NOT(): antlr.TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.NOT, 0)!;
  }
  public override get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_notToken;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterNotToken) {
      listener.enterNotToken(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitNotToken) {
      listener.exitNotToken(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitNotToken) {
      return visitor.visitNotToken(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class ColonTokenContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public COLON(): antlr.TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.COLON, 0)!;
  }
  public override get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_colonToken;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterColonToken) {
      listener.enterColonToken(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitColonToken) {
      listener.exitColonToken(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitColonToken) {
      return visitor.visitColonToken(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class LeftParenTokenContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public LPAREN(): antlr.TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.LPAREN, 0)!;
  }
  public override get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_leftParenToken;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterLeftParenToken) {
      listener.enterLeftParenToken(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitLeftParenToken) {
      listener.exitLeftParenToken(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitLeftParenToken) {
      return visitor.visitLeftParenToken(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class RightParenTokenContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public RPAREN(): antlr.TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.RPAREN, 0)!;
  }
  public override get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_rightParenToken;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterRightParenToken) {
      listener.enterRightParenToken(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitRightParenToken) {
      listener.exitRightParenToken(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitRightParenToken) {
      return visitor.visitRightParenToken(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class AttributeValueWhitespaceContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public WS(): antlr.TerminalNode[];
  public WS(i: number): antlr.TerminalNode | null;
  public WS(i?: number): antlr.TerminalNode | null | antlr.TerminalNode[] {
    if (i === undefined) {
      return this.getTokens(SelectionAutoCompleteParser.WS);
    } else {
      return this.getToken(SelectionAutoCompleteParser.WS, i);
    }
  }
  public override get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_attributeValueWhitespace;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterAttributeValueWhitespace) {
      listener.enterAttributeValueWhitespace(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitAttributeValueWhitespace) {
      listener.exitAttributeValueWhitespace(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitAttributeValueWhitespace) {
      return visitor.visitAttributeValueWhitespace(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class PostAttributeValueWhitespaceContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public WS(): antlr.TerminalNode[];
  public WS(i: number): antlr.TerminalNode | null;
  public WS(i?: number): antlr.TerminalNode | null | antlr.TerminalNode[] {
    if (i === undefined) {
      return this.getTokens(SelectionAutoCompleteParser.WS);
    } else {
      return this.getToken(SelectionAutoCompleteParser.WS, i);
    }
  }
  public override get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_postAttributeValueWhitespace;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterPostAttributeValueWhitespace) {
      listener.enterPostAttributeValueWhitespace(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitPostAttributeValueWhitespace) {
      listener.exitPostAttributeValueWhitespace(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitPostAttributeValueWhitespace) {
      return visitor.visitPostAttributeValueWhitespace(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class PostExpressionWhitespaceContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public WS(): antlr.TerminalNode[];
  public WS(i: number): antlr.TerminalNode | null;
  public WS(i?: number): antlr.TerminalNode | null | antlr.TerminalNode[] {
    if (i === undefined) {
      return this.getTokens(SelectionAutoCompleteParser.WS);
    } else {
      return this.getToken(SelectionAutoCompleteParser.WS, i);
    }
  }
  public override get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_postExpressionWhitespace;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterPostExpressionWhitespace) {
      listener.enterPostExpressionWhitespace(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitPostExpressionWhitespace) {
      listener.exitPostExpressionWhitespace(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitPostExpressionWhitespace) {
      return visitor.visitPostExpressionWhitespace(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class PostNotOperatorWhitespaceContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public WS(): antlr.TerminalNode[];
  public WS(i: number): antlr.TerminalNode | null;
  public WS(i?: number): antlr.TerminalNode | null | antlr.TerminalNode[] {
    if (i === undefined) {
      return this.getTokens(SelectionAutoCompleteParser.WS);
    } else {
      return this.getToken(SelectionAutoCompleteParser.WS, i);
    }
  }
  public override get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_postNotOperatorWhitespace;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterPostNotOperatorWhitespace) {
      listener.enterPostNotOperatorWhitespace(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitPostNotOperatorWhitespace) {
      listener.exitPostNotOperatorWhitespace(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitPostNotOperatorWhitespace) {
      return visitor.visitPostNotOperatorWhitespace(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class PostLogicalOperatorWhitespaceContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public WS(): antlr.TerminalNode[];
  public WS(i: number): antlr.TerminalNode | null;
  public WS(i?: number): antlr.TerminalNode | null | antlr.TerminalNode[] {
    if (i === undefined) {
      return this.getTokens(SelectionAutoCompleteParser.WS);
    } else {
      return this.getToken(SelectionAutoCompleteParser.WS, i);
    }
  }
  public override get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_postLogicalOperatorWhitespace;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterPostLogicalOperatorWhitespace) {
      listener.enterPostLogicalOperatorWhitespace(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitPostLogicalOperatorWhitespace) {
      listener.exitPostLogicalOperatorWhitespace(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitPostLogicalOperatorWhitespace) {
      return visitor.visitPostLogicalOperatorWhitespace(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class PostNeighborTraversalWhitespaceContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public WS(): antlr.TerminalNode[];
  public WS(i: number): antlr.TerminalNode | null;
  public WS(i?: number): antlr.TerminalNode | null | antlr.TerminalNode[] {
    if (i === undefined) {
      return this.getTokens(SelectionAutoCompleteParser.WS);
    } else {
      return this.getToken(SelectionAutoCompleteParser.WS, i);
    }
  }
  public override get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_postNeighborTraversalWhitespace;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterPostNeighborTraversalWhitespace) {
      listener.enterPostNeighborTraversalWhitespace(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitPostNeighborTraversalWhitespace) {
      listener.exitPostNeighborTraversalWhitespace(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitPostNeighborTraversalWhitespace) {
      return visitor.visitPostNeighborTraversalWhitespace(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class PostUpwardTraversalWhitespaceContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public WS(): antlr.TerminalNode[];
  public WS(i: number): antlr.TerminalNode | null;
  public WS(i?: number): antlr.TerminalNode | null | antlr.TerminalNode[] {
    if (i === undefined) {
      return this.getTokens(SelectionAutoCompleteParser.WS);
    } else {
      return this.getToken(SelectionAutoCompleteParser.WS, i);
    }
  }
  public override get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_postUpwardTraversalWhitespace;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterPostUpwardTraversalWhitespace) {
      listener.enterPostUpwardTraversalWhitespace(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitPostUpwardTraversalWhitespace) {
      listener.exitPostUpwardTraversalWhitespace(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitPostUpwardTraversalWhitespace) {
      return visitor.visitPostUpwardTraversalWhitespace(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class PostDownwardTraversalWhitespaceContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public WS(): antlr.TerminalNode[];
  public WS(i: number): antlr.TerminalNode | null;
  public WS(i?: number): antlr.TerminalNode | null | antlr.TerminalNode[] {
    if (i === undefined) {
      return this.getTokens(SelectionAutoCompleteParser.WS);
    } else {
      return this.getToken(SelectionAutoCompleteParser.WS, i);
    }
  }
  public override get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_postDownwardTraversalWhitespace;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterPostDownwardTraversalWhitespace) {
      listener.enterPostDownwardTraversalWhitespace(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitPostDownwardTraversalWhitespace) {
      listener.exitPostDownwardTraversalWhitespace(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitPostDownwardTraversalWhitespace) {
      return visitor.visitPostDownwardTraversalWhitespace(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class PostDigitsWhitespaceContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public WS(): antlr.TerminalNode[];
  public WS(i: number): antlr.TerminalNode | null;
  public WS(i?: number): antlr.TerminalNode | null | antlr.TerminalNode[] {
    if (i === undefined) {
      return this.getTokens(SelectionAutoCompleteParser.WS);
    } else {
      return this.getToken(SelectionAutoCompleteParser.WS, i);
    }
  }
  public override get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_postDigitsWhitespace;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterPostDigitsWhitespace) {
      listener.enterPostDigitsWhitespace(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitPostDigitsWhitespace) {
      listener.exitPostDigitsWhitespace(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitPostDigitsWhitespace) {
      return visitor.visitPostDigitsWhitespace(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class ValueContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public override get ruleIndex(): number {
    return SelectionAutoCompleteParser.RULE_value;
  }
  public override copyFrom(ctx: ValueContext): void {
    super.copyFrom(ctx);
  }
}
export class IncompleteRightQuotedStringValueContext extends ValueContext {
  public constructor(ctx: ValueContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public INCOMPLETE_RIGHT_QUOTED_STRING(): antlr.TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.INCOMPLETE_RIGHT_QUOTED_STRING, 0)!;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterIncompleteRightQuotedStringValue) {
      listener.enterIncompleteRightQuotedStringValue(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitIncompleteRightQuotedStringValue) {
      listener.exitIncompleteRightQuotedStringValue(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitIncompleteRightQuotedStringValue) {
      return visitor.visitIncompleteRightQuotedStringValue(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class UnquotedStringValueContext extends ValueContext {
  public constructor(ctx: ValueContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public IDENTIFIER(): antlr.TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.IDENTIFIER, 0)!;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterUnquotedStringValue) {
      listener.enterUnquotedStringValue(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitUnquotedStringValue) {
      listener.exitUnquotedStringValue(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitUnquotedStringValue) {
      return visitor.visitUnquotedStringValue(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class NullStringValueContext extends ValueContext {
  public constructor(ctx: ValueContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public NULL_STRING(): antlr.TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.NULL_STRING, 0)!;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterNullStringValue) {
      listener.enterNullStringValue(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitNullStringValue) {
      listener.exitNullStringValue(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitNullStringValue) {
      return visitor.visitNullStringValue(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class QuotedStringValueContext extends ValueContext {
  public constructor(ctx: ValueContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public QUOTED_STRING(): antlr.TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.QUOTED_STRING, 0)!;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterQuotedStringValue) {
      listener.enterQuotedStringValue(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitQuotedStringValue) {
      listener.exitQuotedStringValue(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitQuotedStringValue) {
      return visitor.visitQuotedStringValue(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class DigitsValueContext extends ValueContext {
  public constructor(ctx: ValueContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public DIGITS(): antlr.TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.DIGITS, 0)!;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterDigitsValue) {
      listener.enterDigitsValue(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitDigitsValue) {
      listener.exitDigitsValue(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitDigitsValue) {
      return visitor.visitDigitsValue(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class IncompleteLeftQuotedStringValueContext extends ValueContext {
  public constructor(ctx: ValueContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public INCOMPLETE_LEFT_QUOTED_STRING(): antlr.TerminalNode {
    return this.getToken(SelectionAutoCompleteParser.INCOMPLETE_LEFT_QUOTED_STRING, 0)!;
  }
  public override enterRule(listener: SelectionAutoCompleteListener): void {
    if (listener.enterIncompleteLeftQuotedStringValue) {
      listener.enterIncompleteLeftQuotedStringValue(this);
    }
  }
  public override exitRule(listener: SelectionAutoCompleteListener): void {
    if (listener.exitIncompleteLeftQuotedStringValue) {
      listener.exitIncompleteLeftQuotedStringValue(this);
    }
  }
  public override accept<Result>(visitor: SelectionAutoCompleteVisitor<Result>): Result | null {
    if (visitor.visitIncompleteLeftQuotedStringValue) {
      return visitor.visitIncompleteLeftQuotedStringValue(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
