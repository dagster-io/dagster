// Generated from /home/user/dagster/js_modules/dagster-ui/packages/ui-core/src/automation-selection/AutomationSelection.g4 by ANTLR 4.13.1

import * as antlr from 'antlr4ng';
import {Token} from 'antlr4ng';

import {AutomationSelectionListener} from './AutomationSelectionListener.js';
import {AutomationSelectionVisitor} from './AutomationSelectionVisitor.js';

// for running tests with parameters, TODO: discuss strategy for typed parameters in CI
// eslint-disable-next-line no-unused-vars
type int = number;

export class AutomationSelectionParser extends antlr.Parser {
  public static readonly AND = 1;
  public static readonly OR = 2;
  public static readonly NOT = 3;
  public static readonly EQUAL = 4;
  public static readonly COLON = 5;
  public static readonly STAR = 6;
  public static readonly LPAREN = 7;
  public static readonly RPAREN = 8;
  public static readonly NAME = 9;
  public static readonly CODE_LOCATION = 10;
  public static readonly TAG = 11;
  public static readonly STATUS = 12;
  public static readonly TYPE = 13;
  public static readonly QUOTED_STRING = 14;
  public static readonly UNQUOTED_STRING = 15;
  public static readonly UNQUOTED_WILDCARD_STRING = 16;
  public static readonly NULL_STRING = 17;
  public static readonly WS = 18;
  public static readonly RULE_start = 0;
  public static readonly RULE_expr = 1;
  public static readonly RULE_traversalAllowedExpr = 2;
  public static readonly RULE_attributeExpr = 3;
  public static readonly RULE_value = 4;
  public static readonly RULE_keyValue = 5;

  public static readonly literalNames = [
    null,
    null,
    null,
    null,
    "'='",
    "':'",
    "'*'",
    "'('",
    "')'",
    "'name'",
    "'code_location'",
    "'tag'",
    "'status'",
    "'type'",
    null,
    null,
    null,
    "'<null>'",
  ];

  public static readonly symbolicNames = [
    null,
    'AND',
    'OR',
    'NOT',
    'EQUAL',
    'COLON',
    'STAR',
    'LPAREN',
    'RPAREN',
    'NAME',
    'CODE_LOCATION',
    'TAG',
    'STATUS',
    'TYPE',
    'QUOTED_STRING',
    'UNQUOTED_STRING',
    'UNQUOTED_WILDCARD_STRING',
    'NULL_STRING',
    'WS',
  ];
  public static readonly ruleNames = [
    'start',
    'expr',
    'traversalAllowedExpr',
    'attributeExpr',
    'value',
    'keyValue',
  ];

  public get grammarFileName(): string {
    return 'AutomationSelection.g4';
  }
  public get literalNames(): (string | null)[] {
    return AutomationSelectionParser.literalNames;
  }
  public get symbolicNames(): (string | null)[] {
    return AutomationSelectionParser.symbolicNames;
  }
  public get ruleNames(): string[] {
    return AutomationSelectionParser.ruleNames;
  }
  public get serializedATN(): number[] {
    return AutomationSelectionParser._serializedATN;
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
      AutomationSelectionParser._ATN,
      AutomationSelectionParser.decisionsToDFA,
      new antlr.PredictionContextCache(),
    );
  }
  public start(): StartContext {
    let localContext = new StartContext(this.context, this.state);
    this.enterRule(localContext, 0, AutomationSelectionParser.RULE_start);
    try {
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 12;
        this.expr(0);
        this.state = 13;
        this.match(AutomationSelectionParser.EOF);
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
    this.enterRecursionRule(localContext, 2, AutomationSelectionParser.RULE_expr, _p);
    try {
      let alternative: number;
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 20;
        this.errorHandler.sync(this);
        switch (this.tokenStream.LA(1)) {
          case AutomationSelectionParser.LPAREN:
          case AutomationSelectionParser.NAME:
          case AutomationSelectionParser.CODE_LOCATION:
          case AutomationSelectionParser.TAG:
          case AutomationSelectionParser.STATUS:
          case AutomationSelectionParser.TYPE:
            {
              localContext = new TraversalAllowedExpressionContext(localContext);
              this.context = localContext;
              previousContext = localContext;

              this.state = 16;
              this.traversalAllowedExpr();
            }
            break;
          case AutomationSelectionParser.NOT:
            {
              localContext = new NotExpressionContext(localContext);
              this.context = localContext;
              previousContext = localContext;
              this.state = 17;
              this.match(AutomationSelectionParser.NOT);
              this.state = 18;
              this.expr(4);
            }
            break;
          case AutomationSelectionParser.STAR:
            {
              localContext = new AllExpressionContext(localContext);
              this.context = localContext;
              previousContext = localContext;
              this.state = 19;
              this.match(AutomationSelectionParser.STAR);
            }
            break;
          default:
            throw new antlr.NoViableAltException(this);
        }
        this.context!.stop = this.tokenStream.LT(-1);
        this.state = 30;
        this.errorHandler.sync(this);
        alternative = this.interpreter.adaptivePredict(this.tokenStream, 2, this.context);
        while (alternative !== 2 && alternative !== antlr.ATN.INVALID_ALT_NUMBER) {
          if (alternative === 1) {
            if (this.parseListeners != null) {
              this.triggerExitRuleEvent();
            }
            previousContext = localContext;
            {
              this.state = 28;
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
                      AutomationSelectionParser.RULE_expr,
                    );
                    this.state = 22;
                    if (!this.precpred(this.context, 3)) {
                      throw this.createFailedPredicateException('this.precpred(this.context, 3)');
                    }
                    this.state = 23;
                    this.match(AutomationSelectionParser.AND);
                    this.state = 24;
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
                      AutomationSelectionParser.RULE_expr,
                    );
                    this.state = 25;
                    if (!this.precpred(this.context, 2)) {
                      throw this.createFailedPredicateException('this.precpred(this.context, 2)');
                    }
                    this.state = 26;
                    this.match(AutomationSelectionParser.OR);
                    this.state = 27;
                    this.expr(3);
                  }
                  break;
              }
            }
          }
          this.state = 32;
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
    this.enterRule(localContext, 4, AutomationSelectionParser.RULE_traversalAllowedExpr);
    try {
      this.state = 38;
      this.errorHandler.sync(this);
      switch (this.tokenStream.LA(1)) {
        case AutomationSelectionParser.NAME:
        case AutomationSelectionParser.CODE_LOCATION:
        case AutomationSelectionParser.TAG:
        case AutomationSelectionParser.STATUS:
        case AutomationSelectionParser.TYPE:
          localContext = new AttributeExpressionContext(localContext);
          this.enterOuterAlt(localContext, 1);
          {
            this.state = 33;
            this.attributeExpr();
          }
          break;
        case AutomationSelectionParser.LPAREN:
          localContext = new ParenthesizedExpressionContext(localContext);
          this.enterOuterAlt(localContext, 2);
          {
            this.state = 34;
            this.match(AutomationSelectionParser.LPAREN);
            this.state = 35;
            this.expr(0);
            this.state = 36;
            this.match(AutomationSelectionParser.RPAREN);
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
  public attributeExpr(): AttributeExprContext {
    let localContext = new AttributeExprContext(this.context, this.state);
    this.enterRule(localContext, 6, AutomationSelectionParser.RULE_attributeExpr);
    try {
      this.state = 59;
      this.errorHandler.sync(this);
      switch (this.tokenStream.LA(1)) {
        case AutomationSelectionParser.NAME:
          localContext = new NameExprContext(localContext);
          this.enterOuterAlt(localContext, 1);
          {
            this.state = 40;
            this.match(AutomationSelectionParser.NAME);
            this.state = 41;
            this.match(AutomationSelectionParser.COLON);
            this.state = 42;
            this.keyValue();
          }
          break;
        case AutomationSelectionParser.TAG:
          localContext = new TagExprContext(localContext);
          this.enterOuterAlt(localContext, 2);
          {
            this.state = 43;
            this.match(AutomationSelectionParser.TAG);
            this.state = 44;
            this.match(AutomationSelectionParser.COLON);
            this.state = 45;
            this.value();
            this.state = 48;
            this.errorHandler.sync(this);
            switch (this.interpreter.adaptivePredict(this.tokenStream, 4, this.context)) {
              case 1:
                {
                  this.state = 46;
                  this.match(AutomationSelectionParser.EQUAL);
                  this.state = 47;
                  this.value();
                }
                break;
            }
          }
          break;
        case AutomationSelectionParser.TYPE:
          localContext = new TypeExprContext(localContext);
          this.enterOuterAlt(localContext, 3);
          {
            this.state = 50;
            this.match(AutomationSelectionParser.TYPE);
            this.state = 51;
            this.match(AutomationSelectionParser.COLON);
            this.state = 52;
            this.value();
          }
          break;
        case AutomationSelectionParser.STATUS:
          localContext = new StatusExprContext(localContext);
          this.enterOuterAlt(localContext, 4);
          {
            this.state = 53;
            this.match(AutomationSelectionParser.STATUS);
            this.state = 54;
            this.match(AutomationSelectionParser.COLON);
            this.state = 55;
            this.value();
          }
          break;
        case AutomationSelectionParser.CODE_LOCATION:
          localContext = new CodeLocationExprContext(localContext);
          this.enterOuterAlt(localContext, 5);
          {
            this.state = 56;
            this.match(AutomationSelectionParser.CODE_LOCATION);
            this.state = 57;
            this.match(AutomationSelectionParser.COLON);
            this.state = 58;
            this.value();
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
  public value(): ValueContext {
    let localContext = new ValueContext(this.context, this.state);
    this.enterRule(localContext, 8, AutomationSelectionParser.RULE_value);
    let _la: number;
    try {
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 61;
        _la = this.tokenStream.LA(1);
        if (!((_la & ~0x1f) === 0 && ((1 << _la) & 180224) !== 0)) {
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
    this.enterRule(localContext, 10, AutomationSelectionParser.RULE_keyValue);
    let _la: number;
    try {
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 63;
        _la = this.tokenStream.LA(1);
        if (!((_la & ~0x1f) === 0 && ((1 << _la) & 114688) !== 0)) {
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
    4, 1, 18, 66, 2, 0, 7, 0, 2, 1, 7, 1, 2, 2, 7, 2, 2, 3, 7, 3, 2, 4, 7, 4, 2, 5, 7, 5, 1, 0, 1,
    0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3, 1, 21, 8, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 5, 1,
    29, 8, 1, 10, 1, 12, 1, 32, 9, 1, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 3, 2, 39, 8, 2, 1, 3, 1, 3, 1,
    3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 3, 3, 49, 8, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3,
    1, 3, 3, 3, 60, 8, 3, 1, 4, 1, 4, 1, 5, 1, 5, 1, 5, 0, 1, 2, 6, 0, 2, 4, 6, 8, 10, 0, 2, 2, 0,
    14, 15, 17, 17, 1, 0, 14, 16, 69, 0, 12, 1, 0, 0, 0, 2, 20, 1, 0, 0, 0, 4, 38, 1, 0, 0, 0, 6,
    59, 1, 0, 0, 0, 8, 61, 1, 0, 0, 0, 10, 63, 1, 0, 0, 0, 12, 13, 3, 2, 1, 0, 13, 14, 5, 0, 0, 1,
    14, 1, 1, 0, 0, 0, 15, 16, 6, 1, -1, 0, 16, 21, 3, 4, 2, 0, 17, 18, 5, 3, 0, 0, 18, 21, 3, 2, 1,
    4, 19, 21, 5, 6, 0, 0, 20, 15, 1, 0, 0, 0, 20, 17, 1, 0, 0, 0, 20, 19, 1, 0, 0, 0, 21, 30, 1, 0,
    0, 0, 22, 23, 10, 3, 0, 0, 23, 24, 5, 1, 0, 0, 24, 29, 3, 2, 1, 4, 25, 26, 10, 2, 0, 0, 26, 27,
    5, 2, 0, 0, 27, 29, 3, 2, 1, 3, 28, 22, 1, 0, 0, 0, 28, 25, 1, 0, 0, 0, 29, 32, 1, 0, 0, 0, 30,
    28, 1, 0, 0, 0, 30, 31, 1, 0, 0, 0, 31, 3, 1, 0, 0, 0, 32, 30, 1, 0, 0, 0, 33, 39, 3, 6, 3, 0,
    34, 35, 5, 7, 0, 0, 35, 36, 3, 2, 1, 0, 36, 37, 5, 8, 0, 0, 37, 39, 1, 0, 0, 0, 38, 33, 1, 0, 0,
    0, 38, 34, 1, 0, 0, 0, 39, 5, 1, 0, 0, 0, 40, 41, 5, 9, 0, 0, 41, 42, 5, 5, 0, 0, 42, 60, 3, 10,
    5, 0, 43, 44, 5, 11, 0, 0, 44, 45, 5, 5, 0, 0, 45, 48, 3, 8, 4, 0, 46, 47, 5, 4, 0, 0, 47, 49,
    3, 8, 4, 0, 48, 46, 1, 0, 0, 0, 48, 49, 1, 0, 0, 0, 49, 60, 1, 0, 0, 0, 50, 51, 5, 13, 0, 0, 51,
    52, 5, 5, 0, 0, 52, 60, 3, 8, 4, 0, 53, 54, 5, 12, 0, 0, 54, 55, 5, 5, 0, 0, 55, 60, 3, 8, 4, 0,
    56, 57, 5, 10, 0, 0, 57, 58, 5, 5, 0, 0, 58, 60, 3, 8, 4, 0, 59, 40, 1, 0, 0, 0, 59, 43, 1, 0,
    0, 0, 59, 50, 1, 0, 0, 0, 59, 53, 1, 0, 0, 0, 59, 56, 1, 0, 0, 0, 60, 7, 1, 0, 0, 0, 61, 62, 7,
    0, 0, 0, 62, 9, 1, 0, 0, 0, 63, 64, 7, 1, 0, 0, 64, 11, 1, 0, 0, 0, 6, 20, 28, 30, 38, 48, 59,
  ];

  private static __ATN: antlr.ATN;
  public static get _ATN(): antlr.ATN {
    if (!AutomationSelectionParser.__ATN) {
      AutomationSelectionParser.__ATN = new antlr.ATNDeserializer().deserialize(
        AutomationSelectionParser._serializedATN,
      );
    }

    return AutomationSelectionParser.__ATN;
  }

  private static readonly vocabulary = new antlr.Vocabulary(
    AutomationSelectionParser.literalNames,
    AutomationSelectionParser.symbolicNames,
    [],
  );

  public override get vocabulary(): antlr.Vocabulary {
    return AutomationSelectionParser.vocabulary;
  }

  private static readonly decisionsToDFA = AutomationSelectionParser._ATN.decisionToState.map(
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
    return this.getToken(AutomationSelectionParser.EOF, 0)!;
  }
  public override get ruleIndex(): number {
    return AutomationSelectionParser.RULE_start;
  }
  public override enterRule(listener: AutomationSelectionListener): void {
    if (listener.enterStart) {
      listener.enterStart(this);
    }
  }
  public override exitRule(listener: AutomationSelectionListener): void {
    if (listener.exitStart) {
      listener.exitStart(this);
    }
  }
  public override accept<Result>(visitor: AutomationSelectionVisitor<Result>): Result | null {
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
    return AutomationSelectionParser.RULE_expr;
  }
  public override copyFrom(ctx: ExprContext): void {
    super.copyFrom(ctx);
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
    return this.getToken(AutomationSelectionParser.AND, 0)!;
  }
  public override enterRule(listener: AutomationSelectionListener): void {
    if (listener.enterAndExpression) {
      listener.enterAndExpression(this);
    }
  }
  public override exitRule(listener: AutomationSelectionListener): void {
    if (listener.exitAndExpression) {
      listener.exitAndExpression(this);
    }
  }
  public override accept<Result>(visitor: AutomationSelectionVisitor<Result>): Result | null {
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
    return this.getToken(AutomationSelectionParser.STAR, 0)!;
  }
  public override enterRule(listener: AutomationSelectionListener): void {
    if (listener.enterAllExpression) {
      listener.enterAllExpression(this);
    }
  }
  public override exitRule(listener: AutomationSelectionListener): void {
    if (listener.exitAllExpression) {
      listener.exitAllExpression(this);
    }
  }
  public override accept<Result>(visitor: AutomationSelectionVisitor<Result>): Result | null {
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
  public override enterRule(listener: AutomationSelectionListener): void {
    if (listener.enterTraversalAllowedExpression) {
      listener.enterTraversalAllowedExpression(this);
    }
  }
  public override exitRule(listener: AutomationSelectionListener): void {
    if (listener.exitTraversalAllowedExpression) {
      listener.exitTraversalAllowedExpression(this);
    }
  }
  public override accept<Result>(visitor: AutomationSelectionVisitor<Result>): Result | null {
    if (visitor.visitTraversalAllowedExpression) {
      return visitor.visitTraversalAllowedExpression(this);
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
    return this.getToken(AutomationSelectionParser.NOT, 0)!;
  }
  public expr(): ExprContext {
    return this.getRuleContext(0, ExprContext)!;
  }
  public override enterRule(listener: AutomationSelectionListener): void {
    if (listener.enterNotExpression) {
      listener.enterNotExpression(this);
    }
  }
  public override exitRule(listener: AutomationSelectionListener): void {
    if (listener.exitNotExpression) {
      listener.exitNotExpression(this);
    }
  }
  public override accept<Result>(visitor: AutomationSelectionVisitor<Result>): Result | null {
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
    return this.getToken(AutomationSelectionParser.OR, 0)!;
  }
  public override enterRule(listener: AutomationSelectionListener): void {
    if (listener.enterOrExpression) {
      listener.enterOrExpression(this);
    }
  }
  public override exitRule(listener: AutomationSelectionListener): void {
    if (listener.exitOrExpression) {
      listener.exitOrExpression(this);
    }
  }
  public override accept<Result>(visitor: AutomationSelectionVisitor<Result>): Result | null {
    if (visitor.visitOrExpression) {
      return visitor.visitOrExpression(this);
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
    return AutomationSelectionParser.RULE_traversalAllowedExpr;
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
    return this.getToken(AutomationSelectionParser.LPAREN, 0)!;
  }
  public expr(): ExprContext {
    return this.getRuleContext(0, ExprContext)!;
  }
  public RPAREN(): antlr.TerminalNode {
    return this.getToken(AutomationSelectionParser.RPAREN, 0)!;
  }
  public override enterRule(listener: AutomationSelectionListener): void {
    if (listener.enterParenthesizedExpression) {
      listener.enterParenthesizedExpression(this);
    }
  }
  public override exitRule(listener: AutomationSelectionListener): void {
    if (listener.exitParenthesizedExpression) {
      listener.exitParenthesizedExpression(this);
    }
  }
  public override accept<Result>(visitor: AutomationSelectionVisitor<Result>): Result | null {
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
  public override enterRule(listener: AutomationSelectionListener): void {
    if (listener.enterAttributeExpression) {
      listener.enterAttributeExpression(this);
    }
  }
  public override exitRule(listener: AutomationSelectionListener): void {
    if (listener.exitAttributeExpression) {
      listener.exitAttributeExpression(this);
    }
  }
  public override accept<Result>(visitor: AutomationSelectionVisitor<Result>): Result | null {
    if (visitor.visitAttributeExpression) {
      return visitor.visitAttributeExpression(this);
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
    return AutomationSelectionParser.RULE_attributeExpr;
  }
  public override copyFrom(ctx: AttributeExprContext): void {
    super.copyFrom(ctx);
  }
}
export class TagExprContext extends AttributeExprContext {
  public constructor(ctx: AttributeExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public TAG(): antlr.TerminalNode {
    return this.getToken(AutomationSelectionParser.TAG, 0)!;
  }
  public COLON(): antlr.TerminalNode {
    return this.getToken(AutomationSelectionParser.COLON, 0)!;
  }
  public value(): ValueContext[];
  public value(i: number): ValueContext | null;
  public value(i?: number): ValueContext[] | ValueContext | null {
    if (i === undefined) {
      return this.getRuleContexts(ValueContext);
    }

    return this.getRuleContext(i, ValueContext);
  }
  public EQUAL(): antlr.TerminalNode | null {
    return this.getToken(AutomationSelectionParser.EQUAL, 0);
  }
  public override enterRule(listener: AutomationSelectionListener): void {
    if (listener.enterTagExpr) {
      listener.enterTagExpr(this);
    }
  }
  public override exitRule(listener: AutomationSelectionListener): void {
    if (listener.exitTagExpr) {
      listener.exitTagExpr(this);
    }
  }
  public override accept<Result>(visitor: AutomationSelectionVisitor<Result>): Result | null {
    if (visitor.visitTagExpr) {
      return visitor.visitTagExpr(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class StatusExprContext extends AttributeExprContext {
  public constructor(ctx: AttributeExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public STATUS(): antlr.TerminalNode {
    return this.getToken(AutomationSelectionParser.STATUS, 0)!;
  }
  public COLON(): antlr.TerminalNode {
    return this.getToken(AutomationSelectionParser.COLON, 0)!;
  }
  public value(): ValueContext {
    return this.getRuleContext(0, ValueContext)!;
  }
  public override enterRule(listener: AutomationSelectionListener): void {
    if (listener.enterStatusExpr) {
      listener.enterStatusExpr(this);
    }
  }
  public override exitRule(listener: AutomationSelectionListener): void {
    if (listener.exitStatusExpr) {
      listener.exitStatusExpr(this);
    }
  }
  public override accept<Result>(visitor: AutomationSelectionVisitor<Result>): Result | null {
    if (visitor.visitStatusExpr) {
      return visitor.visitStatusExpr(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class NameExprContext extends AttributeExprContext {
  public constructor(ctx: AttributeExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public NAME(): antlr.TerminalNode {
    return this.getToken(AutomationSelectionParser.NAME, 0)!;
  }
  public COLON(): antlr.TerminalNode {
    return this.getToken(AutomationSelectionParser.COLON, 0)!;
  }
  public keyValue(): KeyValueContext {
    return this.getRuleContext(0, KeyValueContext)!;
  }
  public override enterRule(listener: AutomationSelectionListener): void {
    if (listener.enterNameExpr) {
      listener.enterNameExpr(this);
    }
  }
  public override exitRule(listener: AutomationSelectionListener): void {
    if (listener.exitNameExpr) {
      listener.exitNameExpr(this);
    }
  }
  public override accept<Result>(visitor: AutomationSelectionVisitor<Result>): Result | null {
    if (visitor.visitNameExpr) {
      return visitor.visitNameExpr(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class CodeLocationExprContext extends AttributeExprContext {
  public constructor(ctx: AttributeExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public CODE_LOCATION(): antlr.TerminalNode {
    return this.getToken(AutomationSelectionParser.CODE_LOCATION, 0)!;
  }
  public COLON(): antlr.TerminalNode {
    return this.getToken(AutomationSelectionParser.COLON, 0)!;
  }
  public value(): ValueContext {
    return this.getRuleContext(0, ValueContext)!;
  }
  public override enterRule(listener: AutomationSelectionListener): void {
    if (listener.enterCodeLocationExpr) {
      listener.enterCodeLocationExpr(this);
    }
  }
  public override exitRule(listener: AutomationSelectionListener): void {
    if (listener.exitCodeLocationExpr) {
      listener.exitCodeLocationExpr(this);
    }
  }
  public override accept<Result>(visitor: AutomationSelectionVisitor<Result>): Result | null {
    if (visitor.visitCodeLocationExpr) {
      return visitor.visitCodeLocationExpr(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class TypeExprContext extends AttributeExprContext {
  public constructor(ctx: AttributeExprContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public TYPE(): antlr.TerminalNode {
    return this.getToken(AutomationSelectionParser.TYPE, 0)!;
  }
  public COLON(): antlr.TerminalNode {
    return this.getToken(AutomationSelectionParser.COLON, 0)!;
  }
  public value(): ValueContext {
    return this.getRuleContext(0, ValueContext)!;
  }
  public override enterRule(listener: AutomationSelectionListener): void {
    if (listener.enterTypeExpr) {
      listener.enterTypeExpr(this);
    }
  }
  public override exitRule(listener: AutomationSelectionListener): void {
    if (listener.exitTypeExpr) {
      listener.exitTypeExpr(this);
    }
  }
  public override accept<Result>(visitor: AutomationSelectionVisitor<Result>): Result | null {
    if (visitor.visitTypeExpr) {
      return visitor.visitTypeExpr(this);
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
    return this.getToken(AutomationSelectionParser.QUOTED_STRING, 0);
  }
  public UNQUOTED_STRING(): antlr.TerminalNode | null {
    return this.getToken(AutomationSelectionParser.UNQUOTED_STRING, 0);
  }
  public NULL_STRING(): antlr.TerminalNode | null {
    return this.getToken(AutomationSelectionParser.NULL_STRING, 0);
  }
  public override get ruleIndex(): number {
    return AutomationSelectionParser.RULE_value;
  }
  public override enterRule(listener: AutomationSelectionListener): void {
    if (listener.enterValue) {
      listener.enterValue(this);
    }
  }
  public override exitRule(listener: AutomationSelectionListener): void {
    if (listener.exitValue) {
      listener.exitValue(this);
    }
  }
  public override accept<Result>(visitor: AutomationSelectionVisitor<Result>): Result | null {
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
    return this.getToken(AutomationSelectionParser.QUOTED_STRING, 0);
  }
  public UNQUOTED_STRING(): antlr.TerminalNode | null {
    return this.getToken(AutomationSelectionParser.UNQUOTED_STRING, 0);
  }
  public UNQUOTED_WILDCARD_STRING(): antlr.TerminalNode | null {
    return this.getToken(AutomationSelectionParser.UNQUOTED_WILDCARD_STRING, 0);
  }
  public override get ruleIndex(): number {
    return AutomationSelectionParser.RULE_keyValue;
  }
  public override enterRule(listener: AutomationSelectionListener): void {
    if (listener.enterKeyValue) {
      listener.enterKeyValue(this);
    }
  }
  public override exitRule(listener: AutomationSelectionListener): void {
    if (listener.exitKeyValue) {
      listener.exitKeyValue(this);
    }
  }
  public override accept<Result>(visitor: AutomationSelectionVisitor<Result>): Result | null {
    if (visitor.visitKeyValue) {
      return visitor.visitKeyValue(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
