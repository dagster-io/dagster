// Generated from /home/user/dagster/js_modules/dagster-ui/packages/ui-core/src/partitions/PartitionSelection.g4 by ANTLR 4.9.0-SNAPSHOT

import {FailedPredicateException} from 'antlr4ts/FailedPredicateException';
import {NoViableAltException} from 'antlr4ts/NoViableAltException';
import {Parser} from 'antlr4ts/Parser';
import {ParserRuleContext} from 'antlr4ts/ParserRuleContext';
import {RecognitionException} from 'antlr4ts/RecognitionException';
//import { RuleVersion } from "antlr4ts/RuleVersion";
import {TokenStream} from 'antlr4ts/TokenStream';
import {Vocabulary} from 'antlr4ts/Vocabulary';
import {VocabularyImpl} from 'antlr4ts/VocabularyImpl';
import {ATN} from 'antlr4ts/atn/ATN';
import {ATNDeserializer} from 'antlr4ts/atn/ATNDeserializer';
import {ParserATNSimulator} from 'antlr4ts/atn/ParserATNSimulator';
import * as Utils from 'antlr4ts/misc/Utils';
import {TerminalNode} from 'antlr4ts/tree/TerminalNode';

import {PartitionSelectionListener} from './PartitionSelectionListener';
import {PartitionSelectionVisitor} from './PartitionSelectionVisitor';

export class PartitionSelectionParser extends Parser {
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
  // tslint:disable:no-trailing-whitespace
  public static readonly ruleNames: string[] = [
    'start',
    'partitionList',
    'partitionItem',
    'range',
    'wildcard',
    'partitionKey',
  ];

  private static readonly _LITERAL_NAMES: Array<string | undefined> = [
    undefined,
    "'['",
    "']'",
    "'...'",
    "','",
  ];
  private static readonly _SYMBOLIC_NAMES: Array<string | undefined> = [
    undefined,
    'LBRACKET',
    'RBRACKET',
    'RANGE_DELIM',
    'COMMA',
    'QUOTED_STRING',
    'WILDCARD_PATTERN',
    'UNQUOTED_STRING',
    'WS',
  ];
  public static readonly VOCABULARY: Vocabulary = new VocabularyImpl(
    PartitionSelectionParser._LITERAL_NAMES,
    PartitionSelectionParser._SYMBOLIC_NAMES,
    [],
  );

  // @Override
  // @NotNull
  public get vocabulary(): Vocabulary {
    return PartitionSelectionParser.VOCABULARY;
  }
  // tslint:enable:no-trailing-whitespace

  // @Override
  public get grammarFileName(): string {
    return 'PartitionSelection.g4';
  }

  // @Override
  public get ruleNames(): string[] {
    return PartitionSelectionParser.ruleNames;
  }

  // @Override
  public get serializedATN(): string {
    return PartitionSelectionParser._serializedATN;
  }

  protected createFailedPredicateException(
    predicate?: string,
    message?: string,
  ): FailedPredicateException {
    return new FailedPredicateException(this, predicate, message);
  }

  constructor(input: TokenStream) {
    super(input);
    this._interp = new ParserATNSimulator(PartitionSelectionParser._ATN, this);
  }
  // @RuleVersion(0)
  public start(): StartContext {
    const _localctx: StartContext = new StartContext(this._ctx, this.state);
    this.enterRule(_localctx, 0, PartitionSelectionParser.RULE_start);
    let _la: number;
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 13;
        this._errHandler.sync(this);
        _la = this._input.LA(1);
        if (
          (_la & ~0x1f) === 0 &&
          ((1 << _la) &
            ((1 << PartitionSelectionParser.LBRACKET) |
              (1 << PartitionSelectionParser.QUOTED_STRING) |
              (1 << PartitionSelectionParser.WILDCARD_PATTERN) |
              (1 << PartitionSelectionParser.UNQUOTED_STRING))) !==
            0
        ) {
          {
            this.state = 12;
            this.partitionList();
          }
        }

        this.state = 15;
        this.match(PartitionSelectionParser.EOF);
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
  public partitionList(): PartitionListContext {
    const _localctx: PartitionListContext = new PartitionListContext(this._ctx, this.state);
    this.enterRule(_localctx, 2, PartitionSelectionParser.RULE_partitionList);
    let _la: number;
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 17;
        this.partitionItem();
        this.state = 22;
        this._errHandler.sync(this);
        _la = this._input.LA(1);
        while (_la === PartitionSelectionParser.COMMA) {
          {
            {
              this.state = 18;
              this.match(PartitionSelectionParser.COMMA);
              this.state = 19;
              this.partitionItem();
            }
          }
          this.state = 24;
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
  public partitionItem(): PartitionItemContext {
    let _localctx: PartitionItemContext = new PartitionItemContext(this._ctx, this.state);
    this.enterRule(_localctx, 4, PartitionSelectionParser.RULE_partitionItem);
    try {
      this.state = 28;
      this._errHandler.sync(this);
      switch (this._input.LA(1)) {
        case PartitionSelectionParser.LBRACKET:
          _localctx = new RangePartitionItemContext(_localctx);
          this.enterOuterAlt(_localctx, 1);
          {
            this.state = 25;
            this.range();
          }
          break;
        case PartitionSelectionParser.WILDCARD_PATTERN:
          _localctx = new WildcardPartitionItemContext(_localctx);
          this.enterOuterAlt(_localctx, 2);
          {
            this.state = 26;
            this.wildcard();
          }
          break;
        case PartitionSelectionParser.QUOTED_STRING:
        case PartitionSelectionParser.UNQUOTED_STRING:
          _localctx = new SinglePartitionItemContext(_localctx);
          this.enterOuterAlt(_localctx, 3);
          {
            this.state = 27;
            this.partitionKey();
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
  public range(): RangeContext {
    const _localctx: RangeContext = new RangeContext(this._ctx, this.state);
    this.enterRule(_localctx, 6, PartitionSelectionParser.RULE_range);
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 30;
        this.match(PartitionSelectionParser.LBRACKET);
        this.state = 31;
        this.partitionKey();
        this.state = 32;
        this.match(PartitionSelectionParser.RANGE_DELIM);
        this.state = 33;
        this.partitionKey();
        this.state = 34;
        this.match(PartitionSelectionParser.RBRACKET);
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
  public wildcard(): WildcardContext {
    const _localctx: WildcardContext = new WildcardContext(this._ctx, this.state);
    this.enterRule(_localctx, 8, PartitionSelectionParser.RULE_wildcard);
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 36;
        this.match(PartitionSelectionParser.WILDCARD_PATTERN);
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
  public partitionKey(): PartitionKeyContext {
    let _localctx: PartitionKeyContext = new PartitionKeyContext(this._ctx, this.state);
    this.enterRule(_localctx, 10, PartitionSelectionParser.RULE_partitionKey);
    try {
      this.state = 40;
      this._errHandler.sync(this);
      switch (this._input.LA(1)) {
        case PartitionSelectionParser.QUOTED_STRING:
          _localctx = new QuotedPartitionKeyContext(_localctx);
          this.enterOuterAlt(_localctx, 1);
          {
            this.state = 38;
            this.match(PartitionSelectionParser.QUOTED_STRING);
          }
          break;
        case PartitionSelectionParser.UNQUOTED_STRING:
          _localctx = new UnquotedPartitionKeyContext(_localctx);
          this.enterOuterAlt(_localctx, 2);
          {
            this.state = 39;
            this.match(PartitionSelectionParser.UNQUOTED_STRING);
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

  public static readonly _serializedATN: string =
    '\x03\uC91D\uCABA\u058D\uAFBA\u4F53\u0607\uEA8B\uC241\x03\n-\x04\x02\t' +
    '\x02\x04\x03\t\x03\x04\x04\t\x04\x04\x05\t\x05\x04\x06\t\x06\x04\x07\t' +
    '\x07\x03\x02\x05\x02\x10\n\x02\x03\x02\x03\x02\x03\x03\x03\x03\x03\x03' +
    '\x07\x03\x17\n\x03\f\x03\x0E\x03\x1A\v\x03\x03\x04\x03\x04\x03\x04\x05' +
    '\x04\x1F\n\x04\x03\x05\x03\x05\x03\x05\x03\x05\x03\x05\x03\x05\x03\x06' +
    '\x03\x06\x03\x07\x03\x07\x05\x07+\n\x07\x03\x07\x02\x02\x02\b\x02\x02' +
    '\x04\x02\x06\x02\b\x02\n\x02\f\x02\x02\x02\x02+\x02\x0F\x03\x02\x02\x02' +
    '\x04\x13\x03\x02\x02\x02\x06\x1E\x03\x02\x02\x02\b \x03\x02\x02\x02\n' +
    '&\x03\x02\x02\x02\f*\x03\x02\x02\x02\x0E\x10\x05\x04\x03\x02\x0F\x0E\x03' +
    '\x02\x02\x02\x0F\x10\x03\x02\x02\x02\x10\x11\x03\x02\x02\x02\x11\x12\x07' +
    '\x02\x02\x03\x12\x03\x03\x02\x02\x02\x13\x18\x05\x06\x04\x02\x14\x15\x07' +
    '\x06\x02\x02\x15\x17\x05\x06\x04\x02\x16\x14\x03\x02\x02\x02\x17\x1A\x03' +
    '\x02\x02\x02\x18\x16\x03\x02\x02\x02\x18\x19\x03\x02\x02\x02\x19\x05\x03' +
    '\x02\x02\x02\x1A\x18\x03\x02\x02\x02\x1B\x1F\x05\b\x05\x02\x1C\x1F\x05' +
    '\n\x06\x02\x1D\x1F\x05\f\x07\x02\x1E\x1B\x03\x02\x02\x02\x1E\x1C\x03\x02' +
    '\x02\x02\x1E\x1D\x03\x02\x02\x02\x1F\x07\x03\x02\x02\x02 !\x07\x03\x02' +
    '\x02!"\x05\f\x07\x02"#\x07\x05\x02\x02#$\x05\f\x07\x02$%\x07\x04\x02' +
    "\x02%\t\x03\x02\x02\x02&\'\x07\b\x02\x02\'\v\x03\x02\x02\x02(+\x07\x07" +
    '\x02\x02)+\x07\t\x02\x02*(\x03\x02\x02\x02*)\x03\x02\x02\x02+\r\x03\x02' +
    '\x02\x02\x06\x0F\x18\x1E*';
  public static __ATN: ATN;
  public static get _ATN(): ATN {
    if (!PartitionSelectionParser.__ATN) {
      PartitionSelectionParser.__ATN = new ATNDeserializer().deserialize(
        Utils.toCharArray(PartitionSelectionParser._serializedATN),
      );
    }

    return PartitionSelectionParser.__ATN;
  }
}

export class StartContext extends ParserRuleContext {
  public EOF(): TerminalNode {
    return this.getToken(PartitionSelectionParser.EOF, 0);
  }
  public partitionList(): PartitionListContext | undefined {
    return this.tryGetRuleContext(0, PartitionListContext);
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return PartitionSelectionParser.RULE_start;
  }
  // @Override
  public enterRule(listener: PartitionSelectionListener): void {
    if (listener.enterStart) {
      listener.enterStart(this);
    }
  }
  // @Override
  public exitRule(listener: PartitionSelectionListener): void {
    if (listener.exitStart) {
      listener.exitStart(this);
    }
  }
  // @Override
  public accept<Result>(visitor: PartitionSelectionVisitor<Result>): Result {
    if (visitor.visitStart) {
      return visitor.visitStart(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class PartitionListContext extends ParserRuleContext {
  public partitionItem(): PartitionItemContext[];
  public partitionItem(i: number): PartitionItemContext;
  public partitionItem(i?: number): PartitionItemContext | PartitionItemContext[] {
    if (i === undefined) {
      return this.getRuleContexts(PartitionItemContext);
    } else {
      return this.getRuleContext(i, PartitionItemContext);
    }
  }
  public COMMA(): TerminalNode[];
  public COMMA(i: number): TerminalNode;
  public COMMA(i?: number): TerminalNode | TerminalNode[] {
    if (i === undefined) {
      return this.getTokens(PartitionSelectionParser.COMMA);
    } else {
      return this.getToken(PartitionSelectionParser.COMMA, i);
    }
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return PartitionSelectionParser.RULE_partitionList;
  }
  // @Override
  public enterRule(listener: PartitionSelectionListener): void {
    if (listener.enterPartitionList) {
      listener.enterPartitionList(this);
    }
  }
  // @Override
  public exitRule(listener: PartitionSelectionListener): void {
    if (listener.exitPartitionList) {
      listener.exitPartitionList(this);
    }
  }
  // @Override
  public accept<Result>(visitor: PartitionSelectionVisitor<Result>): Result {
    if (visitor.visitPartitionList) {
      return visitor.visitPartitionList(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class PartitionItemContext extends ParserRuleContext {
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return PartitionSelectionParser.RULE_partitionItem;
  }
  public copyFrom(ctx: PartitionItemContext): void {
    super.copyFrom(ctx);
  }
}
export class RangePartitionItemContext extends PartitionItemContext {
  public range(): RangeContext {
    return this.getRuleContext(0, RangeContext);
  }
  constructor(ctx: PartitionItemContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: PartitionSelectionListener): void {
    if (listener.enterRangePartitionItem) {
      listener.enterRangePartitionItem(this);
    }
  }
  // @Override
  public exitRule(listener: PartitionSelectionListener): void {
    if (listener.exitRangePartitionItem) {
      listener.exitRangePartitionItem(this);
    }
  }
  // @Override
  public accept<Result>(visitor: PartitionSelectionVisitor<Result>): Result {
    if (visitor.visitRangePartitionItem) {
      return visitor.visitRangePartitionItem(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class WildcardPartitionItemContext extends PartitionItemContext {
  public wildcard(): WildcardContext {
    return this.getRuleContext(0, WildcardContext);
  }
  constructor(ctx: PartitionItemContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: PartitionSelectionListener): void {
    if (listener.enterWildcardPartitionItem) {
      listener.enterWildcardPartitionItem(this);
    }
  }
  // @Override
  public exitRule(listener: PartitionSelectionListener): void {
    if (listener.exitWildcardPartitionItem) {
      listener.exitWildcardPartitionItem(this);
    }
  }
  // @Override
  public accept<Result>(visitor: PartitionSelectionVisitor<Result>): Result {
    if (visitor.visitWildcardPartitionItem) {
      return visitor.visitWildcardPartitionItem(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class SinglePartitionItemContext extends PartitionItemContext {
  public partitionKey(): PartitionKeyContext {
    return this.getRuleContext(0, PartitionKeyContext);
  }
  constructor(ctx: PartitionItemContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: PartitionSelectionListener): void {
    if (listener.enterSinglePartitionItem) {
      listener.enterSinglePartitionItem(this);
    }
  }
  // @Override
  public exitRule(listener: PartitionSelectionListener): void {
    if (listener.exitSinglePartitionItem) {
      listener.exitSinglePartitionItem(this);
    }
  }
  // @Override
  public accept<Result>(visitor: PartitionSelectionVisitor<Result>): Result {
    if (visitor.visitSinglePartitionItem) {
      return visitor.visitSinglePartitionItem(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class RangeContext extends ParserRuleContext {
  public LBRACKET(): TerminalNode {
    return this.getToken(PartitionSelectionParser.LBRACKET, 0);
  }
  public partitionKey(): PartitionKeyContext[];
  public partitionKey(i: number): PartitionKeyContext;
  public partitionKey(i?: number): PartitionKeyContext | PartitionKeyContext[] {
    if (i === undefined) {
      return this.getRuleContexts(PartitionKeyContext);
    } else {
      return this.getRuleContext(i, PartitionKeyContext);
    }
  }
  public RANGE_DELIM(): TerminalNode {
    return this.getToken(PartitionSelectionParser.RANGE_DELIM, 0);
  }
  public RBRACKET(): TerminalNode {
    return this.getToken(PartitionSelectionParser.RBRACKET, 0);
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return PartitionSelectionParser.RULE_range;
  }
  // @Override
  public enterRule(listener: PartitionSelectionListener): void {
    if (listener.enterRange) {
      listener.enterRange(this);
    }
  }
  // @Override
  public exitRule(listener: PartitionSelectionListener): void {
    if (listener.exitRange) {
      listener.exitRange(this);
    }
  }
  // @Override
  public accept<Result>(visitor: PartitionSelectionVisitor<Result>): Result {
    if (visitor.visitRange) {
      return visitor.visitRange(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class WildcardContext extends ParserRuleContext {
  public WILDCARD_PATTERN(): TerminalNode {
    return this.getToken(PartitionSelectionParser.WILDCARD_PATTERN, 0);
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return PartitionSelectionParser.RULE_wildcard;
  }
  // @Override
  public enterRule(listener: PartitionSelectionListener): void {
    if (listener.enterWildcard) {
      listener.enterWildcard(this);
    }
  }
  // @Override
  public exitRule(listener: PartitionSelectionListener): void {
    if (listener.exitWildcard) {
      listener.exitWildcard(this);
    }
  }
  // @Override
  public accept<Result>(visitor: PartitionSelectionVisitor<Result>): Result {
    if (visitor.visitWildcard) {
      return visitor.visitWildcard(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class PartitionKeyContext extends ParserRuleContext {
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return PartitionSelectionParser.RULE_partitionKey;
  }
  public copyFrom(ctx: PartitionKeyContext): void {
    super.copyFrom(ctx);
  }
}
export class QuotedPartitionKeyContext extends PartitionKeyContext {
  public QUOTED_STRING(): TerminalNode {
    return this.getToken(PartitionSelectionParser.QUOTED_STRING, 0);
  }
  constructor(ctx: PartitionKeyContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: PartitionSelectionListener): void {
    if (listener.enterQuotedPartitionKey) {
      listener.enterQuotedPartitionKey(this);
    }
  }
  // @Override
  public exitRule(listener: PartitionSelectionListener): void {
    if (listener.exitQuotedPartitionKey) {
      listener.exitQuotedPartitionKey(this);
    }
  }
  // @Override
  public accept<Result>(visitor: PartitionSelectionVisitor<Result>): Result {
    if (visitor.visitQuotedPartitionKey) {
      return visitor.visitQuotedPartitionKey(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class UnquotedPartitionKeyContext extends PartitionKeyContext {
  public UNQUOTED_STRING(): TerminalNode {
    return this.getToken(PartitionSelectionParser.UNQUOTED_STRING, 0);
  }
  constructor(ctx: PartitionKeyContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: PartitionSelectionListener): void {
    if (listener.enterUnquotedPartitionKey) {
      listener.enterUnquotedPartitionKey(this);
    }
  }
  // @Override
  public exitRule(listener: PartitionSelectionListener): void {
    if (listener.exitUnquotedPartitionKey) {
      listener.exitUnquotedPartitionKey(this);
    }
  }
  // @Override
  public accept<Result>(visitor: PartitionSelectionVisitor<Result>): Result {
    if (visitor.visitUnquotedPartitionKey) {
      return visitor.visitUnquotedPartitionKey(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
