// Generated from /home/user/dagster/js_modules/dagster-ui/packages/ui-core/src/partitions/PartitionSelection.g4 by ANTLR 4.13.1

import * as antlr from 'antlr4ng';
import {Token} from 'antlr4ng';

import {PartitionSelectionListener} from './PartitionSelectionListener.js';
import {PartitionSelectionVisitor} from './PartitionSelectionVisitor.js';

// for running tests with parameters, TODO: discuss strategy for typed parameters in CI
// eslint-disable-next-line no-unused-vars
type int = number;

export class PartitionSelectionParser extends antlr.Parser {
  public static readonly LBRACKET = 1;
  public static readonly RBRACKET = 2;
  public static readonly RANGE_DELIM = 3;
  public static readonly COMMA = 4;
  public static readonly QUOTED_STRING = 5;
  public static readonly WILDCARD_PATTERN = 6;
  public static readonly UNQUOTED_STRING = 7;
  public static readonly WS = 8;
  public static readonly RULE_start = 0;
  public static readonly RULE_partitionList = 1;
  public static readonly RULE_partitionItem = 2;
  public static readonly RULE_range = 3;
  public static readonly RULE_wildcard = 4;
  public static readonly RULE_partitionKey = 5;

  public static readonly literalNames = [null, "'['", "']'", "'...'", "','"];

  public static readonly symbolicNames = [
    null,
    'LBRACKET',
    'RBRACKET',
    'RANGE_DELIM',
    'COMMA',
    'QUOTED_STRING',
    'WILDCARD_PATTERN',
    'UNQUOTED_STRING',
    'WS',
  ];
  public static readonly ruleNames = [
    'start',
    'partitionList',
    'partitionItem',
    'range',
    'wildcard',
    'partitionKey',
  ];

  public get grammarFileName(): string {
    return 'PartitionSelection.g4';
  }
  public get literalNames(): (string | null)[] {
    return PartitionSelectionParser.literalNames;
  }
  public get symbolicNames(): (string | null)[] {
    return PartitionSelectionParser.symbolicNames;
  }
  public get ruleNames(): string[] {
    return PartitionSelectionParser.ruleNames;
  }
  public get serializedATN(): number[] {
    return PartitionSelectionParser._serializedATN;
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
      PartitionSelectionParser._ATN,
      PartitionSelectionParser.decisionsToDFA,
      new antlr.PredictionContextCache(),
    );
  }
  public start(): StartContext {
    let localContext = new StartContext(this.context, this.state);
    this.enterRule(localContext, 0, PartitionSelectionParser.RULE_start);
    try {
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 13;
        this.errorHandler.sync(this);
        switch (this.interpreter.adaptivePredict(this.tokenStream, 0, this.context)) {
          case 1:
            {
              this.state = 12;
              this.partitionList();
            }
            break;
        }
        this.state = 15;
        this.match(PartitionSelectionParser.EOF);
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
  public partitionList(): PartitionListContext {
    let localContext = new PartitionListContext(this.context, this.state);
    this.enterRule(localContext, 2, PartitionSelectionParser.RULE_partitionList);
    let _la: number;
    try {
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 18;
        this.errorHandler.sync(this);
        _la = this.tokenStream.LA(1);
        if ((_la & ~0x1f) === 0 && ((1 << _la) & 226) !== 0) {
          {
            this.state = 17;
            this.partitionItem();
          }
        }

        this.state = 26;
        this.errorHandler.sync(this);
        _la = this.tokenStream.LA(1);
        while (_la === 4) {
          {
            {
              this.state = 20;
              this.match(PartitionSelectionParser.COMMA);
              this.state = 22;
              this.errorHandler.sync(this);
              _la = this.tokenStream.LA(1);
              if ((_la & ~0x1f) === 0 && ((1 << _la) & 226) !== 0) {
                {
                  this.state = 21;
                  this.partitionItem();
                }
              }
            }
          }
          this.state = 28;
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
  public partitionItem(): PartitionItemContext {
    let localContext = new PartitionItemContext(this.context, this.state);
    this.enterRule(localContext, 4, PartitionSelectionParser.RULE_partitionItem);
    try {
      this.state = 32;
      this.errorHandler.sync(this);
      switch (this.tokenStream.LA(1)) {
        case PartitionSelectionParser.LBRACKET:
          localContext = new RangePartitionItemContext(localContext);
          this.enterOuterAlt(localContext, 1);
          {
            this.state = 29;
            this.range();
          }
          break;
        case PartitionSelectionParser.WILDCARD_PATTERN:
          localContext = new WildcardPartitionItemContext(localContext);
          this.enterOuterAlt(localContext, 2);
          {
            this.state = 30;
            this.wildcard();
          }
          break;
        case PartitionSelectionParser.QUOTED_STRING:
        case PartitionSelectionParser.UNQUOTED_STRING:
          localContext = new SinglePartitionItemContext(localContext);
          this.enterOuterAlt(localContext, 3);
          {
            this.state = 31;
            this.partitionKey();
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
  public range(): RangeContext {
    let localContext = new RangeContext(this.context, this.state);
    this.enterRule(localContext, 6, PartitionSelectionParser.RULE_range);
    try {
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 34;
        this.match(PartitionSelectionParser.LBRACKET);
        this.state = 35;
        this.partitionKey();
        this.state = 36;
        this.match(PartitionSelectionParser.RANGE_DELIM);
        this.state = 37;
        this.partitionKey();
        this.state = 38;
        this.match(PartitionSelectionParser.RBRACKET);
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
  public wildcard(): WildcardContext {
    let localContext = new WildcardContext(this.context, this.state);
    this.enterRule(localContext, 8, PartitionSelectionParser.RULE_wildcard);
    try {
      this.enterOuterAlt(localContext, 1);
      {
        this.state = 40;
        this.match(PartitionSelectionParser.WILDCARD_PATTERN);
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
  public partitionKey(): PartitionKeyContext {
    let localContext = new PartitionKeyContext(this.context, this.state);
    this.enterRule(localContext, 10, PartitionSelectionParser.RULE_partitionKey);
    try {
      this.state = 44;
      this.errorHandler.sync(this);
      switch (this.tokenStream.LA(1)) {
        case PartitionSelectionParser.QUOTED_STRING:
          localContext = new QuotedPartitionKeyContext(localContext);
          this.enterOuterAlt(localContext, 1);
          {
            this.state = 42;
            this.match(PartitionSelectionParser.QUOTED_STRING);
          }
          break;
        case PartitionSelectionParser.UNQUOTED_STRING:
          localContext = new UnquotedPartitionKeyContext(localContext);
          this.enterOuterAlt(localContext, 2);
          {
            this.state = 43;
            this.match(PartitionSelectionParser.UNQUOTED_STRING);
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

  public static readonly _serializedATN: number[] = [
    4, 1, 8, 47, 2, 0, 7, 0, 2, 1, 7, 1, 2, 2, 7, 2, 2, 3, 7, 3, 2, 4, 7, 4, 2, 5, 7, 5, 1, 0, 3, 0,
    14, 8, 0, 1, 0, 1, 0, 1, 1, 3, 1, 19, 8, 1, 1, 1, 1, 1, 3, 1, 23, 8, 1, 5, 1, 25, 8, 1, 10, 1,
    12, 1, 28, 9, 1, 1, 2, 1, 2, 1, 2, 3, 2, 33, 8, 2, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 4, 1,
    4, 1, 5, 1, 5, 3, 5, 45, 8, 5, 1, 5, 0, 0, 6, 0, 2, 4, 6, 8, 10, 0, 0, 47, 0, 13, 1, 0, 0, 0, 2,
    18, 1, 0, 0, 0, 4, 32, 1, 0, 0, 0, 6, 34, 1, 0, 0, 0, 8, 40, 1, 0, 0, 0, 10, 44, 1, 0, 0, 0, 12,
    14, 3, 2, 1, 0, 13, 12, 1, 0, 0, 0, 13, 14, 1, 0, 0, 0, 14, 15, 1, 0, 0, 0, 15, 16, 5, 0, 0, 1,
    16, 1, 1, 0, 0, 0, 17, 19, 3, 4, 2, 0, 18, 17, 1, 0, 0, 0, 18, 19, 1, 0, 0, 0, 19, 26, 1, 0, 0,
    0, 20, 22, 5, 4, 0, 0, 21, 23, 3, 4, 2, 0, 22, 21, 1, 0, 0, 0, 22, 23, 1, 0, 0, 0, 23, 25, 1, 0,
    0, 0, 24, 20, 1, 0, 0, 0, 25, 28, 1, 0, 0, 0, 26, 24, 1, 0, 0, 0, 26, 27, 1, 0, 0, 0, 27, 3, 1,
    0, 0, 0, 28, 26, 1, 0, 0, 0, 29, 33, 3, 6, 3, 0, 30, 33, 3, 8, 4, 0, 31, 33, 3, 10, 5, 0, 32,
    29, 1, 0, 0, 0, 32, 30, 1, 0, 0, 0, 32, 31, 1, 0, 0, 0, 33, 5, 1, 0, 0, 0, 34, 35, 5, 1, 0, 0,
    35, 36, 3, 10, 5, 0, 36, 37, 5, 3, 0, 0, 37, 38, 3, 10, 5, 0, 38, 39, 5, 2, 0, 0, 39, 7, 1, 0,
    0, 0, 40, 41, 5, 6, 0, 0, 41, 9, 1, 0, 0, 0, 42, 45, 5, 5, 0, 0, 43, 45, 5, 7, 0, 0, 44, 42, 1,
    0, 0, 0, 44, 43, 1, 0, 0, 0, 45, 11, 1, 0, 0, 0, 6, 13, 18, 22, 26, 32, 44,
  ];

  private static __ATN: antlr.ATN;
  public static get _ATN(): antlr.ATN {
    if (!PartitionSelectionParser.__ATN) {
      PartitionSelectionParser.__ATN = new antlr.ATNDeserializer().deserialize(
        PartitionSelectionParser._serializedATN,
      );
    }

    return PartitionSelectionParser.__ATN;
  }

  private static readonly vocabulary = new antlr.Vocabulary(
    PartitionSelectionParser.literalNames,
    PartitionSelectionParser.symbolicNames,
    [],
  );

  public override get vocabulary(): antlr.Vocabulary {
    return PartitionSelectionParser.vocabulary;
  }

  private static readonly decisionsToDFA = PartitionSelectionParser._ATN.decisionToState.map(
    (ds: antlr.DecisionState, index: number) => new antlr.DFA(ds, index),
  );
}

export class StartContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public EOF(): antlr.TerminalNode {
    return this.getToken(PartitionSelectionParser.EOF, 0)!;
  }
  public partitionList(): PartitionListContext | null {
    return this.getRuleContext(0, PartitionListContext);
  }
  public override get ruleIndex(): number {
    return PartitionSelectionParser.RULE_start;
  }
  public override enterRule(listener: PartitionSelectionListener): void {
    if (listener.enterStart) {
      listener.enterStart(this);
    }
  }
  public override exitRule(listener: PartitionSelectionListener): void {
    if (listener.exitStart) {
      listener.exitStart(this);
    }
  }
  public override accept<Result>(visitor: PartitionSelectionVisitor<Result>): Result | null {
    if (visitor.visitStart) {
      return visitor.visitStart(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class PartitionListContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public partitionItem(): PartitionItemContext[];
  public partitionItem(i: number): PartitionItemContext | null;
  public partitionItem(i?: number): PartitionItemContext[] | PartitionItemContext | null {
    if (i === undefined) {
      return this.getRuleContexts(PartitionItemContext);
    }

    return this.getRuleContext(i, PartitionItemContext);
  }
  public COMMA(): antlr.TerminalNode[];
  public COMMA(i: number): antlr.TerminalNode | null;
  public COMMA(i?: number): antlr.TerminalNode | null | antlr.TerminalNode[] {
    if (i === undefined) {
      return this.getTokens(PartitionSelectionParser.COMMA);
    } else {
      return this.getToken(PartitionSelectionParser.COMMA, i);
    }
  }
  public override get ruleIndex(): number {
    return PartitionSelectionParser.RULE_partitionList;
  }
  public override enterRule(listener: PartitionSelectionListener): void {
    if (listener.enterPartitionList) {
      listener.enterPartitionList(this);
    }
  }
  public override exitRule(listener: PartitionSelectionListener): void {
    if (listener.exitPartitionList) {
      listener.exitPartitionList(this);
    }
  }
  public override accept<Result>(visitor: PartitionSelectionVisitor<Result>): Result | null {
    if (visitor.visitPartitionList) {
      return visitor.visitPartitionList(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class PartitionItemContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public override get ruleIndex(): number {
    return PartitionSelectionParser.RULE_partitionItem;
  }
  public override copyFrom(ctx: PartitionItemContext): void {
    super.copyFrom(ctx);
  }
}
export class RangePartitionItemContext extends PartitionItemContext {
  public constructor(ctx: PartitionItemContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public range(): RangeContext {
    return this.getRuleContext(0, RangeContext)!;
  }
  public override enterRule(listener: PartitionSelectionListener): void {
    if (listener.enterRangePartitionItem) {
      listener.enterRangePartitionItem(this);
    }
  }
  public override exitRule(listener: PartitionSelectionListener): void {
    if (listener.exitRangePartitionItem) {
      listener.exitRangePartitionItem(this);
    }
  }
  public override accept<Result>(visitor: PartitionSelectionVisitor<Result>): Result | null {
    if (visitor.visitRangePartitionItem) {
      return visitor.visitRangePartitionItem(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class SinglePartitionItemContext extends PartitionItemContext {
  public constructor(ctx: PartitionItemContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public partitionKey(): PartitionKeyContext {
    return this.getRuleContext(0, PartitionKeyContext)!;
  }
  public override enterRule(listener: PartitionSelectionListener): void {
    if (listener.enterSinglePartitionItem) {
      listener.enterSinglePartitionItem(this);
    }
  }
  public override exitRule(listener: PartitionSelectionListener): void {
    if (listener.exitSinglePartitionItem) {
      listener.exitSinglePartitionItem(this);
    }
  }
  public override accept<Result>(visitor: PartitionSelectionVisitor<Result>): Result | null {
    if (visitor.visitSinglePartitionItem) {
      return visitor.visitSinglePartitionItem(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class WildcardPartitionItemContext extends PartitionItemContext {
  public constructor(ctx: PartitionItemContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public wildcard(): WildcardContext {
    return this.getRuleContext(0, WildcardContext)!;
  }
  public override enterRule(listener: PartitionSelectionListener): void {
    if (listener.enterWildcardPartitionItem) {
      listener.enterWildcardPartitionItem(this);
    }
  }
  public override exitRule(listener: PartitionSelectionListener): void {
    if (listener.exitWildcardPartitionItem) {
      listener.exitWildcardPartitionItem(this);
    }
  }
  public override accept<Result>(visitor: PartitionSelectionVisitor<Result>): Result | null {
    if (visitor.visitWildcardPartitionItem) {
      return visitor.visitWildcardPartitionItem(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class RangeContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public LBRACKET(): antlr.TerminalNode {
    return this.getToken(PartitionSelectionParser.LBRACKET, 0)!;
  }
  public partitionKey(): PartitionKeyContext[];
  public partitionKey(i: number): PartitionKeyContext | null;
  public partitionKey(i?: number): PartitionKeyContext[] | PartitionKeyContext | null {
    if (i === undefined) {
      return this.getRuleContexts(PartitionKeyContext);
    }

    return this.getRuleContext(i, PartitionKeyContext);
  }
  public RANGE_DELIM(): antlr.TerminalNode {
    return this.getToken(PartitionSelectionParser.RANGE_DELIM, 0)!;
  }
  public RBRACKET(): antlr.TerminalNode {
    return this.getToken(PartitionSelectionParser.RBRACKET, 0)!;
  }
  public override get ruleIndex(): number {
    return PartitionSelectionParser.RULE_range;
  }
  public override enterRule(listener: PartitionSelectionListener): void {
    if (listener.enterRange) {
      listener.enterRange(this);
    }
  }
  public override exitRule(listener: PartitionSelectionListener): void {
    if (listener.exitRange) {
      listener.exitRange(this);
    }
  }
  public override accept<Result>(visitor: PartitionSelectionVisitor<Result>): Result | null {
    if (visitor.visitRange) {
      return visitor.visitRange(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class WildcardContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public WILDCARD_PATTERN(): antlr.TerminalNode {
    return this.getToken(PartitionSelectionParser.WILDCARD_PATTERN, 0)!;
  }
  public override get ruleIndex(): number {
    return PartitionSelectionParser.RULE_wildcard;
  }
  public override enterRule(listener: PartitionSelectionListener): void {
    if (listener.enterWildcard) {
      listener.enterWildcard(this);
    }
  }
  public override exitRule(listener: PartitionSelectionListener): void {
    if (listener.exitWildcard) {
      listener.exitWildcard(this);
    }
  }
  public override accept<Result>(visitor: PartitionSelectionVisitor<Result>): Result | null {
    if (visitor.visitWildcard) {
      return visitor.visitWildcard(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class PartitionKeyContext extends antlr.ParserRuleContext {
  public constructor(parent: antlr.ParserRuleContext | null, invokingState: number) {
    super(parent, invokingState);
  }
  public override get ruleIndex(): number {
    return PartitionSelectionParser.RULE_partitionKey;
  }
  public override copyFrom(ctx: PartitionKeyContext): void {
    super.copyFrom(ctx);
  }
}
export class UnquotedPartitionKeyContext extends PartitionKeyContext {
  public constructor(ctx: PartitionKeyContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public UNQUOTED_STRING(): antlr.TerminalNode {
    return this.getToken(PartitionSelectionParser.UNQUOTED_STRING, 0)!;
  }
  public override enterRule(listener: PartitionSelectionListener): void {
    if (listener.enterUnquotedPartitionKey) {
      listener.enterUnquotedPartitionKey(this);
    }
  }
  public override exitRule(listener: PartitionSelectionListener): void {
    if (listener.exitUnquotedPartitionKey) {
      listener.exitUnquotedPartitionKey(this);
    }
  }
  public override accept<Result>(visitor: PartitionSelectionVisitor<Result>): Result | null {
    if (visitor.visitUnquotedPartitionKey) {
      return visitor.visitUnquotedPartitionKey(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class QuotedPartitionKeyContext extends PartitionKeyContext {
  public constructor(ctx: PartitionKeyContext) {
    super(ctx.parent, ctx.invokingState);
    super.copyFrom(ctx);
  }
  public QUOTED_STRING(): antlr.TerminalNode {
    return this.getToken(PartitionSelectionParser.QUOTED_STRING, 0)!;
  }
  public override enterRule(listener: PartitionSelectionListener): void {
    if (listener.enterQuotedPartitionKey) {
      listener.enterQuotedPartitionKey(this);
    }
  }
  public override exitRule(listener: PartitionSelectionListener): void {
    if (listener.exitQuotedPartitionKey) {
      listener.exitQuotedPartitionKey(this);
    }
  }
  public override accept<Result>(visitor: PartitionSelectionVisitor<Result>): Result | null {
    if (visitor.visitQuotedPartitionKey) {
      return visitor.visitQuotedPartitionKey(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
