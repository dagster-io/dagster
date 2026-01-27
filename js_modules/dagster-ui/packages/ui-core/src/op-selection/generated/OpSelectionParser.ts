// Generated from /home/user/dagster/js_modules/dagster-ui/packages/ui-core/src/op-selection/OpSelection.g4 by ANTLR 4.13.1

import * as antlr from 'antlr4ng';
import {Token} from 'antlr4ng';

import {OpSelectionListener} from './OpSelectionListener.js';
import {OpSelectionVisitor} from './OpSelectionVisitor.js';

// for running tests with parameters, TODO: discuss strategy for typed parameters in CI
// eslint-disable-next-line no-unused-vars
type int = number;

export class OpSelectionParser extends antlr.Parser {
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
  public static readonly SINKS = 11;
  public static readonly ROOTS = 12;
  public static readonly QUOTED_STRING = 13;
  public static readonly UNQUOTED_STRING = 14;
  public static readonly UNQUOTED_WILDCARD_STRING = 15;
  public static readonly WS = 16;
  public static readonly RULE_start = 0;
  public static readonly RULE_expr = 1;
  public static readonly RULE_traversalAllowedExpr = 2;
  public static readonly RULE_upTraversal = 3;
  public static readonly RULE_downTraversal = 4;
  public static readonly RULE_functionName = 5;
  public static readonly RULE_attributeExpr = 6;
  public static readonly RULE_value = 7;
  public static readonly RULE_keyValue = 8;

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
    "'name'",
    "'sinks'",
    "'roots'",
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
    'NAME',
    'SINKS',
    'ROOTS',
    'QUOTED_STRING',
    'UNQUOTED_STRING',
    'UNQUOTED_WILDCARD_STRING',
    'WS',
  ];
  public static readonly ruleNames = [
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

  public get grammarFileName(): string {
    return 'OpSelection.g4';
  }
  public get literalNames(): (string | null)[] {
    return OpSelectionParser.literalNames;
  }
  public get symbolicNames(): (string | null)[] {
    return OpSelectionParser.symbolicNames;
  }
  public get ruleNames(): string[] {
    return OpSelectionParser.ruleNames;
  }
  public get serializedATN(): number[] {
    return OpSelectionParser._serializedATN;
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
      OpSelectionParser._ATN,
      OpSelectionParser.decisionsToDFA,
      new antlr.PredictionContextCache(),
    );
  }
  public start(): StartContext {
    let localContext = new StartContext(this.context, this.state);
    this.enterRule(localContext, 0, OpSelectionParser.RULE_start);
    try {
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 18;
        this.expr(0);
        this.state = 19;
        this.match(OpSelectionParser.EOF);
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
    this.enterRecursionRule(localContext, 2, OpSelectionParser.RULE_expr, _p);
    try {
      let alternative: number;
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 36;
        this.errorHandler.sync(this);
        switch (this.interpreter.adaptivePredict(this.tokenStream, 0, this.context)) {
          case 1:
            {
              localContext = new TraversalAllowedExpressionContext(localContext);
              this.context = localContext;
              previousContext = localContext;

              this.state = 22;
              this.traversalAllowedExpr();
            }
            break;
          case 2:
            {
              localContext = new UpAndDownTraversalExpressionContext(localContext);
              this.context = localContext;
              previousContext = localContext;
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
              localContext = new UpTraversalExpressionContext(localContext);
              this.context = localContext;
              previousContext = localContext;
              this.state = 27;
              this.upTraversal();
              this.state = 28;
              this.traversalAllowedExpr();
            }
            break;
          case 4:
            {
              localContext = new DownTraversalExpressionContext(localContext);
              this.context = localContext;
              previousContext = localContext;
              this.state = 30;
              this.traversalAllowedExpr();
              this.state = 31;
              this.downTraversal();
            }
            break;
          case 5:
            {
              localContext = new NotExpressionContext(localContext);
              this.context = localContext;
              previousContext = localContext;
              this.state = 33;
              this.match(OpSelectionParser.NOT);
              this.state = 34;
              this.expr(4);
            }
            break;
          case 6:
            {
              localContext = new AllExpressionContext(localContext);
              this.context = localContext;
              previousContext = localContext;
              this.state = 35;
              this.match(OpSelectionParser.STAR);
            }
            break;
        }
        this.context!.stop = this.tokenStream.LT(-1);
        this.state = 46;
        this.errorHandler.sync(this);
        alternative = this.interpreter.adaptivePredict(this.tokenStream, 2, this.context);
        while (alternative !== 2 && alternative !== antlr.ATN.INVALID_ALT_NUMBER) {
          if (alternative === 1) {
            if (this.parseListeners != null) {
              this.triggerExitRuleEvent();
            }
            previousContext = localContext;
            {
              this.state = 44;
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
                      OpSelectionParser.RULE_expr,
                    );
                    this.state = 38;
                    if (!this.precpred(this.context, 3)) {
                      throw this.createFailedPredicateException('this.precpred(this.context, 3)');
                    }
                    this.state = 39;
                    this.match(OpSelectionParser.AND);
                    this.state = 40;
                    this.expr(4);
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
                      OpSelectionParser.RULE_expr,
                    );
                    this.state = 41;
                    if (!this.precpred(this.context, 2)) {
                      throw this.createFailedPredicateException('this.precpred(this.context, 2)');
                    }
                    this.state = 42;
                    this.match(OpSelectionParser.OR);
                    this.state = 43;
                    this.expr(3);
                  }
                  break;
              }
            }
          }
          this.state = 48;
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
    this.enterRule(localContext, 4, OpSelectionParser.RULE_traversalAllowedExpr);
    try {
      this.state = 59;
      this.errorHandler.sync(this);
      switch (this.tokenStream.LA(1)) {
        case OpSelectionParser.NAME:
          localContext = new AttributeExpressionContext(localContext);
          this.enterOuterAlt(localContext, 1);
          {
            this.state = 49;
            this.attributeExpr();
          }
          break;
        case OpSelectionParser.SINKS:
        case OpSelectionParser.ROOTS:
          localContext = new FunctionCallExpressionContext(localContext);
          this.enterOuterAlt(localContext, 2);
          {
            this.state = 50;
            this.functionName();
            this.state = 51;
            this.match(OpSelectionParser.LPAREN);
            this.state = 52;
            this.expr(0);
            this.state = 53;
            this.match(OpSelectionParser.RPAREN);
          }
          break;
        case OpSelectionParser.LPAREN:
          localContext = new ParenthesizedExpressionContext(localContext);
          this.enterOuterAlt(localContext, 3);
          {
            this.state = 55;
            this.match(OpSelectionParser.LPAREN);
            this.state = 56;
            this.expr(0);
            this.state = 57;
            this.match(OpSelectionParser.RPAREN);
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
  public upTraversal(): UpTraversalContext {
    let localContext = new UpTraversalContext(this.context, this.state);
    this.enterRule(localContext, 6, OpSelectionParser.RULE_upTraversal);
    let _la: number;
    try {
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 62;
        this.errorHandler.sync(this);
        _la = this.tokenStream.LA(1);
        if (_la === 6) {
          {
            this.state = 61;
            this.match(OpSelectionParser.DIGITS);
          }
        }

        this.state = 64;
        this.match(OpSelectionParser.PLUS);
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
  public downTraversal(): DownTraversalContext {
    let localContext = new DownTraversalContext(this.context, this.state);
    this.enterRule(localContext, 8, OpSelectionParser.RULE_downTraversal);
    try {
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 66;
        this.match(OpSelectionParser.PLUS);
        this.state = 68;
        this.errorHandler.sync(this);
        switch (this.interpreter.adaptivePredict(this.tokenStream, 5, this.context)) {
          case 1:
            {
              this.state = 67;
              this.match(OpSelectionParser.DIGITS);
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
  public functionName(): FunctionNameContext {
    let localContext = new FunctionNameContext(this.context, this.state);
    this.enterRule(localContext, 10, OpSelectionParser.RULE_functionName);
    let _la: number;
    try {
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 70;
        _la = this.tokenStream.LA(1);
        if (!(_la === 11 || _la === 12)) {
          this.errorHandler.recoverInline(this);
        } else {
          this.errorHandler.reportMatch(this);
          this.consume();
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
  public attributeExpr(): AttributeExprContext {
    let localContext = new AttributeExprContext(this.context, this.state);
    this.enterRule(localContext, 12, OpSelectionParser.RULE_attributeExpr);
    try {
      localContext = new NameExprContext(localContext);
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 72;
        this.match(OpSelectionParser.NAME);
        this.state = 73;
        this.match(OpSelectionParser.COLON);
        this.state = 74;
        this.keyValue();
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
    this.enterRule(localContext, 14, OpSelectionParser.RULE_value);
    let _la: number;
    try {
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 76;
        _la = this.tokenStream.LA(1);
        if (!(_la === 13 || _la === 14)) {
          this.errorHandler.recoverInline(this);
        } else {
          this.errorHandler.reportMatch(this);
          this.consume();
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
  public keyValue(): KeyValueContext {
    let localContext = new KeyValueContext(this.context, this.state);
    this.enterRule(localContext, 16, OpSelectionParser.RULE_keyValue);
    let _la: number;
    try {
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 78;
        _la = this.tokenStream.LA(1);
        if (!((_la & ~0x1f) === 0 && ((1 << _la) & 57344) !== 0)) {
          this.errorHandler.recoverInline(this);
        } else {
          this.errorHandler.reportMatch(this);
          this.consume();
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
        return this.precpred(this.context, 3);
      case 1:
        return this.precpred(this.context, 2);
    }
    return true;
  }

  public static readonly _serializedATN: number[] = [
    4, 1, 16, 81, 2, 0, 7, 0, 2, 1, 7, 1, 2, 2, 7, 2, 2, 3, 7, 3, 2, 4, 7, 4, 2, 5, 7, 5, 2, 6, 7,
    6, 2, 7, 7, 7, 2, 8, 7, 8, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3, 1, 37, 8, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 5, 1,
    45, 8, 1, 10, 1, 12, 1, 48, 9, 1, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 3,
    2, 60, 8, 2, 1, 3, 3, 3, 63, 8, 3, 1, 3, 1, 3, 1, 4, 1, 4, 3, 4, 69, 8, 4, 1, 5, 1, 5, 1, 6, 1,
    6, 1, 6, 1, 6, 1, 7, 1, 7, 1, 8, 1, 8, 1, 8, 0, 1, 2, 9, 0, 2, 4, 6, 8, 10, 12, 14, 16, 0, 3, 1,
    0, 11, 12, 1, 0, 13, 14, 1, 0, 13, 15, 82, 0, 18, 1, 0, 0, 0, 2, 36, 1, 0, 0, 0, 4, 59, 1, 0, 0,
    0, 6, 62, 1, 0, 0, 0, 8, 66, 1, 0, 0, 0, 10, 70, 1, 0, 0, 0, 12, 72, 1, 0, 0, 0, 14, 76, 1, 0,
    0, 0, 16, 78, 1, 0, 0, 0, 18, 19, 3, 2, 1, 0, 19, 20, 5, 0, 0, 1, 20, 1, 1, 0, 0, 0, 21, 22, 6,
    1, -1, 0, 22, 37, 3, 4, 2, 0, 23, 24, 3, 6, 3, 0, 24, 25, 3, 4, 2, 0, 25, 26, 3, 8, 4, 0, 26,
    37, 1, 0, 0, 0, 27, 28, 3, 6, 3, 0, 28, 29, 3, 4, 2, 0, 29, 37, 1, 0, 0, 0, 30, 31, 3, 4, 2, 0,
    31, 32, 3, 8, 4, 0, 32, 37, 1, 0, 0, 0, 33, 34, 5, 3, 0, 0, 34, 37, 3, 2, 1, 4, 35, 37, 5, 4, 0,
    0, 36, 21, 1, 0, 0, 0, 36, 23, 1, 0, 0, 0, 36, 27, 1, 0, 0, 0, 36, 30, 1, 0, 0, 0, 36, 33, 1, 0,
    0, 0, 36, 35, 1, 0, 0, 0, 37, 46, 1, 0, 0, 0, 38, 39, 10, 3, 0, 0, 39, 40, 5, 1, 0, 0, 40, 45,
    3, 2, 1, 4, 41, 42, 10, 2, 0, 0, 42, 43, 5, 2, 0, 0, 43, 45, 3, 2, 1, 3, 44, 38, 1, 0, 0, 0, 44,
    41, 1, 0, 0, 0, 45, 48, 1, 0, 0, 0, 46, 44, 1, 0, 0, 0, 46, 47, 1, 0, 0, 0, 47, 3, 1, 0, 0, 0,
    48, 46, 1, 0, 0, 0, 49, 60, 3, 12, 6, 0, 50, 51, 3, 10, 5, 0, 51, 52, 5, 8, 0, 0, 52, 53, 3, 2,
    1, 0, 53, 54, 5, 9, 0, 0, 54, 60, 1, 0, 0, 0, 55, 56, 5, 8, 0, 0, 56, 57, 3, 2, 1, 0, 57, 58, 5,
    9, 0, 0, 58, 60, 1, 0, 0, 0, 59, 49, 1, 0, 0, 0, 59, 50, 1, 0, 0, 0, 59, 55, 1, 0, 0, 0, 60, 5,
    1, 0, 0, 0, 61, 63, 5, 6, 0, 0, 62, 61, 1, 0, 0, 0, 62, 63, 1, 0, 0, 0, 63, 64, 1, 0, 0, 0, 64,
    65, 5, 5, 0, 0, 65, 7, 1, 0, 0, 0, 66, 68, 5, 5, 0, 0, 67, 69, 5, 6, 0, 0, 68, 67, 1, 0, 0, 0,
    68, 69, 1, 0, 0, 0, 69, 9, 1, 0, 0, 0, 70, 71, 7, 0, 0, 0, 71, 11, 1, 0, 0, 0, 72, 73, 5, 10, 0,
    0, 73, 74, 5, 7, 0, 0, 74, 75, 3, 16, 8, 0, 75, 13, 1, 0, 0, 0, 76, 77, 7, 1, 0, 0, 77, 15, 1,
    0, 0, 0, 78, 79, 7, 2, 0, 0, 79, 17, 1, 0, 0, 0, 6, 36, 44, 46, 59, 62, 68,
  ];

  private static __ATN: antlr.ATN;
  public static get _ATN(): antlr.ATN {
    if (!OpSelectionParser.__ATN) {
      OpSelectionParser.__ATN = new antlr.ATNDeserializer().deserialize(
        OpSelectionParser._serializedATN,
      );
    }

    return OpSelectionParser.__ATN;
  }

  private static readonly vocabulary = new antlr.Vocabulary(
    OpSelectionParser.literalNames,
    OpSelectionParser.symbolicNames,
    [],
  );

  public override get vocabulary(): antlr.Vocabulary {
    return OpSelectionParser.vocabulary;
  }

  private static readonly decisionsToDFA = OpSelectionParser._ATN.decisionToState.map(
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
    return this.getToken(OpSelectionParser.EOF, 0)!;
  }
  public override get ruleIndex(): number {
    return OpSelectionParser.RULE_start;
  }
  public override enterRule(listener: OpSelectionListener): void {
    if (listener.enterStart) {
      listener.enterStart(this);
    }
  }
  public override exitRule(listener: OpSelectionListener): void {
    if (listener.exitStart) {
      listener.exitStart(this);
    }
  }
  public override accept<Result>(visitor: OpSelectionVisitor<Result>): Result | null {
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
    return OpSelectionParser.RULE_expr;
  }
  public override copyFrom(ctx: ExprContext): void {
    super.copyFrom(ctx);
  }
}
export class UpTraversalExpressionContext extends ExprContext {
  public constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public upTraversal(): UpTraversalContext {
    return this.getRuleContext(0, UpTraversalContext)!;
  }
  public traversalAllowedExpr(): TraversalAllowedExprContext {
    return this.getRuleContext(0, TraversalAllowedExprContext)!;
  }
  public override enterRule(listener: OpSelectionListener): void {
    if (listener.enterUpTraversalExpression) {
      listener.enterUpTraversalExpression(this);
    }
  }
  public override exitRule(listener: OpSelectionListener): void {
    if (listener.exitUpTraversalExpression) {
      listener.exitUpTraversalExpression(this);
    }
  }
  public override accept<Result>(visitor: OpSelectionVisitor<Result>): Result | null {
    if (visitor.visitUpTraversalExpression) {
      return visitor.visitUpTraversalExpression(this);
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
  public AND(): antlr.TerminalNode {
    return this.getToken(OpSelectionParser.AND, 0)!;
  }
  public override enterRule(listener: OpSelectionListener): void {
    if (listener.enterAndExpression) {
      listener.enterAndExpression(this);
    }
  }
  public override exitRule(listener: OpSelectionListener): void {
    if (listener.exitAndExpression) {
      listener.exitAndExpression(this);
    }
  }
  public override accept<Result>(visitor: OpSelectionVisitor<Result>): Result | null {
    if (visitor.visitAndExpression) {
      return visitor.visitAndExpression(this);
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
    return this.getToken(OpSelectionParser.STAR, 0)!;
  }
  public override enterRule(listener: OpSelectionListener): void {
    if (listener.enterAllExpression) {
      listener.enterAllExpression(this);
    }
  }
  public override exitRule(listener: OpSelectionListener): void {
    if (listener.exitAllExpression) {
      listener.exitAllExpression(this);
    }
  }
  public override accept<Result>(visitor: OpSelectionVisitor<Result>): Result | null {
    if (visitor.visitAllExpression) {
      return visitor.visitAllExpression(this);
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
  public override enterRule(listener: OpSelectionListener): void {
    if (listener.enterTraversalAllowedExpression) {
      listener.enterTraversalAllowedExpression(this);
    }
  }
  public override exitRule(listener: OpSelectionListener): void {
    if (listener.exitTraversalAllowedExpression) {
      listener.exitTraversalAllowedExpression(this);
    }
  }
  public override accept<Result>(visitor: OpSelectionVisitor<Result>): Result | null {
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
  public downTraversal(): DownTraversalContext {
    return this.getRuleContext(0, DownTraversalContext)!;
  }
  public override enterRule(listener: OpSelectionListener): void {
    if (listener.enterDownTraversalExpression) {
      listener.enterDownTraversalExpression(this);
    }
  }
  public override exitRule(listener: OpSelectionListener): void {
    if (listener.exitDownTraversalExpression) {
      listener.exitDownTraversalExpression(this);
    }
  }
  public override accept<Result>(visitor: OpSelectionVisitor<Result>): Result | null {
    if (visitor.visitDownTraversalExpression) {
      return visitor.visitDownTraversalExpression(this);
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
  public NOT(): antlr.TerminalNode {
    return this.getToken(OpSelectionParser.NOT, 0)!;
  }
  public expr(): ExprContext {
    return this.getRuleContext(0, ExprContext)!;
  }
  public override enterRule(listener: OpSelectionListener): void {
    if (listener.enterNotExpression) {
      listener.enterNotExpression(this);
    }
  }
  public override exitRule(listener: OpSelectionListener): void {
    if (listener.exitNotExpression) {
      listener.exitNotExpression(this);
    }
  }
  public override accept<Result>(visitor: OpSelectionVisitor<Result>): Result | null {
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
  public OR(): antlr.TerminalNode {
    return this.getToken(OpSelectionParser.OR, 0)!;
  }
  public override enterRule(listener: OpSelectionListener): void {
    if (listener.enterOrExpression) {
      listener.enterOrExpression(this);
    }
  }
  public override exitRule(listener: OpSelectionListener): void {
    if (listener.exitOrExpression) {
      listener.exitOrExpression(this);
    }
  }
  public override accept<Result>(visitor: OpSelectionVisitor<Result>): Result | null {
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
  public upTraversal(): UpTraversalContext {
    return this.getRuleContext(0, UpTraversalContext)!;
  }
  public traversalAllowedExpr(): TraversalAllowedExprContext {
    return this.getRuleContext(0, TraversalAllowedExprContext)!;
  }
  public downTraversal(): DownTraversalContext {
    return this.getRuleContext(0, DownTraversalContext)!;
  }
  public override enterRule(listener: OpSelectionListener): void {
    if (listener.enterUpAndDownTraversalExpression) {
      listener.enterUpAndDownTraversalExpression(this);
    }
  }
  public override exitRule(listener: OpSelectionListener): void {
    if (listener.exitUpAndDownTraversalExpression) {
      listener.exitUpAndDownTraversalExpression(this);
    }
  }
  public override accept<Result>(visitor: OpSelectionVisitor<Result>): Result | null {
    if (visitor.visitUpAndDownTraversalExpression) {
      return visitor.visitUpAndDownTraversalExpression(this);
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
    return OpSelectionParser.RULE_traversalAllowedExpr;
  }
  public override copyFrom(ctx: TraversalAllowedExprContext): void {
    super.copyFrom(ctx);
  }
}
export class ParenthesizedExpressionContext extends TraversalAllowedExprContext {
  public constructor(ctx: TraversalAllowedExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public LPAREN(): antlr.TerminalNode {
    return this.getToken(OpSelectionParser.LPAREN, 0)!;
  }
  public expr(): ExprContext {
    return this.getRuleContext(0, ExprContext)!;
  }
  public RPAREN(): antlr.TerminalNode {
    return this.getToken(OpSelectionParser.RPAREN, 0)!;
  }
  public override enterRule(listener: OpSelectionListener): void {
    if (listener.enterParenthesizedExpression) {
      listener.enterParenthesizedExpression(this);
    }
  }
  public override exitRule(listener: OpSelectionListener): void {
    if (listener.exitParenthesizedExpression) {
      listener.exitParenthesizedExpression(this);
    }
  }
  public override accept<Result>(visitor: OpSelectionVisitor<Result>): Result | null {
    if (visitor.visitParenthesizedExpression) {
      return visitor.visitParenthesizedExpression(this);
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
  public attributeExpr(): AttributeExprContext {
    return this.getRuleContext(0, AttributeExprContext)!;
  }
  public override enterRule(listener: OpSelectionListener): void {
    if (listener.enterAttributeExpression) {
      listener.enterAttributeExpression(this);
    }
  }
  public override exitRule(listener: OpSelectionListener): void {
    if (listener.exitAttributeExpression) {
      listener.exitAttributeExpression(this);
    }
  }
  public override accept<Result>(visitor: OpSelectionVisitor<Result>): Result | null {
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
  public LPAREN(): antlr.TerminalNode {
    return this.getToken(OpSelectionParser.LPAREN, 0)!;
  }
  public expr(): ExprContext {
    return this.getRuleContext(0, ExprContext)!;
  }
  public RPAREN(): antlr.TerminalNode {
    return this.getToken(OpSelectionParser.RPAREN, 0)!;
  }
  public override enterRule(listener: OpSelectionListener): void {
    if (listener.enterFunctionCallExpression) {
      listener.enterFunctionCallExpression(this);
    }
  }
  public override exitRule(listener: OpSelectionListener): void {
    if (listener.exitFunctionCallExpression) {
      listener.exitFunctionCallExpression(this);
    }
  }
  public override accept<Result>(visitor: OpSelectionVisitor<Result>): Result | null {
    if (visitor.visitFunctionCallExpression) {
      return visitor.visitFunctionCallExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class UpTraversalContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public PLUS(): antlr.TerminalNode {
    return this.getToken(OpSelectionParser.PLUS, 0)!;
  }
  public DIGITS(): antlr.TerminalNode | null {
    return this.getToken(OpSelectionParser.DIGITS, 0);
  }
  public override get ruleIndex(): number {
    return OpSelectionParser.RULE_upTraversal;
  }
  public override enterRule(listener: OpSelectionListener): void {
    if (listener.enterUpTraversal) {
      listener.enterUpTraversal(this);
    }
  }
  public override exitRule(listener: OpSelectionListener): void {
    if (listener.exitUpTraversal) {
      listener.exitUpTraversal(this);
    }
  }
  public override accept<Result>(visitor: OpSelectionVisitor<Result>): Result | null {
    if (visitor.visitUpTraversal) {
      return visitor.visitUpTraversal(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class DownTraversalContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public PLUS(): antlr.TerminalNode {
    return this.getToken(OpSelectionParser.PLUS, 0)!;
  }
  public DIGITS(): antlr.TerminalNode | null {
    return this.getToken(OpSelectionParser.DIGITS, 0);
  }
  public override get ruleIndex(): number {
    return OpSelectionParser.RULE_downTraversal;
  }
  public override enterRule(listener: OpSelectionListener): void {
    if (listener.enterDownTraversal) {
      listener.enterDownTraversal(this);
    }
  }
  public override exitRule(listener: OpSelectionListener): void {
    if (listener.exitDownTraversal) {
      listener.exitDownTraversal(this);
    }
  }
  public override accept<Result>(visitor: OpSelectionVisitor<Result>): Result | null {
    if (visitor.visitDownTraversal) {
      return visitor.visitDownTraversal(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class FunctionNameContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public SINKS(): antlr.TerminalNode | null {
    return this.getToken(OpSelectionParser.SINKS, 0);
  }
  public ROOTS(): antlr.TerminalNode | null {
    return this.getToken(OpSelectionParser.ROOTS, 0);
  }
  public override get ruleIndex(): number {
    return OpSelectionParser.RULE_functionName;
  }
  public override enterRule(listener: OpSelectionListener): void {
    if (listener.enterFunctionName) {
      listener.enterFunctionName(this);
    }
  }
  public override exitRule(listener: OpSelectionListener): void {
    if (listener.exitFunctionName) {
      listener.exitFunctionName(this);
    }
  }
  public override accept<Result>(visitor: OpSelectionVisitor<Result>): Result | null {
    if (visitor.visitFunctionName) {
      return visitor.visitFunctionName(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class AttributeExprContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public override get ruleIndex(): number {
    return OpSelectionParser.RULE_attributeExpr;
  }
  public override copyFrom(ctx: AttributeExprContext): void {
    super.copyFrom(ctx);
  }
}
export class NameExprContext extends AttributeExprContext {
  public constructor(ctx: AttributeExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public NAME(): antlr.TerminalNode {
    return this.getToken(OpSelectionParser.NAME, 0)!;
  }
  public COLON(): antlr.TerminalNode {
    return this.getToken(OpSelectionParser.COLON, 0)!;
  }
  public keyValue(): KeyValueContext {
    return this.getRuleContext(0, KeyValueContext)!;
  }
  public override enterRule(listener: OpSelectionListener): void {
    if (listener.enterNameExpr) {
      listener.enterNameExpr(this);
    }
  }
  public override exitRule(listener: OpSelectionListener): void {
    if (listener.exitNameExpr) {
      listener.exitNameExpr(this);
    }
  }
  public override accept<Result>(visitor: OpSelectionVisitor<Result>): Result | null {
    if (visitor.visitNameExpr) {
      return visitor.visitNameExpr(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class ValueContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public QUOTED_STRING(): antlr.TerminalNode | null {
    return this.getToken(OpSelectionParser.QUOTED_STRING, 0);
  }
  public UNQUOTED_STRING(): antlr.TerminalNode | null {
    return this.getToken(OpSelectionParser.UNQUOTED_STRING, 0);
  }
  public override get ruleIndex(): number {
    return OpSelectionParser.RULE_value;
  }
  public override enterRule(listener: OpSelectionListener): void {
    if (listener.enterValue) {
      listener.enterValue(this);
    }
  }
  public override exitRule(listener: OpSelectionListener): void {
    if (listener.exitValue) {
      listener.exitValue(this);
    }
  }
  public override accept<Result>(visitor: OpSelectionVisitor<Result>): Result | null {
    if (visitor.visitValue) {
      return visitor.visitValue(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class KeyValueContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public QUOTED_STRING(): antlr.TerminalNode | null {
    return this.getToken(OpSelectionParser.QUOTED_STRING, 0);
  }
  public UNQUOTED_STRING(): antlr.TerminalNode | null {
    return this.getToken(OpSelectionParser.UNQUOTED_STRING, 0);
  }
  public UNQUOTED_WILDCARD_STRING(): antlr.TerminalNode | null {
    return this.getToken(OpSelectionParser.UNQUOTED_WILDCARD_STRING, 0);
  }
  public override get ruleIndex(): number {
    return OpSelectionParser.RULE_keyValue;
  }
  public override enterRule(listener: OpSelectionListener): void {
    if (listener.enterKeyValue) {
      listener.enterKeyValue(this);
    }
  }
  public override exitRule(listener: OpSelectionListener): void {
    if (listener.exitKeyValue) {
      listener.exitKeyValue(this);
    }
  }
  public override accept<Result>(visitor: OpSelectionVisitor<Result>): Result | null {
    if (visitor.visitKeyValue) {
      return visitor.visitKeyValue(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
