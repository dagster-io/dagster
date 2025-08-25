// Generated from /Users/salazarm/code/dagster/js_modules/dagster-ui/packages/ui-core/src/automation-selection/AutomationSelection.g4 by ANTLR 4.9.0-SNAPSHOT

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

import {AutomationSelectionListener} from './AutomationSelectionListener';
import {AutomationSelectionVisitor} from './AutomationSelectionVisitor';

export class AutomationSelectionParser extends Parser {
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
  // tslint:disable:no-trailing-whitespace
  public static readonly ruleNames: string[] = [
    'start',
    'expr',
    'traversalAllowedExpr',
    'attributeExpr',
    'value',
    'keyValue',
  ];

  private static readonly _LITERAL_NAMES: Array<string | undefined> = [
    undefined,
    undefined,
    undefined,
    undefined,
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
    undefined,
    undefined,
    undefined,
    "'<null>'",
  ];
  private static readonly _SYMBOLIC_NAMES: Array<string | undefined> = [
    undefined,
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
  public static readonly VOCABULARY: Vocabulary = new VocabularyImpl(
    AutomationSelectionParser._LITERAL_NAMES,
    AutomationSelectionParser._SYMBOLIC_NAMES,
    [],
  );

  // @Override
  // @NotNull
  public get vocabulary(): Vocabulary {
    return AutomationSelectionParser.VOCABULARY;
  }
  // tslint:enable:no-trailing-whitespace

  // @Override
  public get grammarFileName(): string {
    return 'AutomationSelection.g4';
  }

  // @Override
  public get ruleNames(): string[] {
    return AutomationSelectionParser.ruleNames;
  }

  // @Override
  public get serializedATN(): string {
    return AutomationSelectionParser._serializedATN;
  }

  protected createFailedPredicateException(
    predicate?: string,
    message?: string,
  ): FailedPredicateException {
    return new FailedPredicateException(this, predicate, message);
  }

  constructor(input: TokenStream) {
    super(input);
    this._interp = new ParserATNSimulator(AutomationSelectionParser._ATN, this);
  }
  // @RuleVersion(0)
  public start(): StartContext {
    const _localctx: StartContext = new StartContext(this._ctx, this.state);
    this.enterRule(_localctx, 0, AutomationSelectionParser.RULE_start);
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 12;
        this.expr(0);
        this.state = 13;
        this.match(AutomationSelectionParser.EOF);
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
    this.enterRecursionRule(_localctx, 2, AutomationSelectionParser.RULE_expr, _p);
    try {
      let _alt: number;
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 20;
        this._errHandler.sync(this);
        switch (this._input.LA(1)) {
          case AutomationSelectionParser.LPAREN:
          case AutomationSelectionParser.NAME:
          case AutomationSelectionParser.CODE_LOCATION:
          case AutomationSelectionParser.TAG:
          case AutomationSelectionParser.STATUS:
          case AutomationSelectionParser.TYPE:
            {
              _localctx = new TraversalAllowedExpressionContext(_localctx);
              this._ctx = _localctx;
              _prevctx = _localctx;

              this.state = 16;
              this.traversalAllowedExpr();
            }
            break;
          case AutomationSelectionParser.NOT:
            {
              _localctx = new NotExpressionContext(_localctx);
              this._ctx = _localctx;
              _prevctx = _localctx;
              this.state = 17;
              this.match(AutomationSelectionParser.NOT);
              this.state = 18;
              this.expr(4);
            }
            break;
          case AutomationSelectionParser.STAR:
            {
              _localctx = new AllExpressionContext(_localctx);
              this._ctx = _localctx;
              _prevctx = _localctx;
              this.state = 19;
              this.match(AutomationSelectionParser.STAR);
            }
            break;
          default:
            throw new NoViableAltException(this);
        }
        this._ctx._stop = this._input.tryLT(-1);
        this.state = 30;
        this._errHandler.sync(this);
        _alt = this.interpreter.adaptivePredict(this._input, 2, this._ctx);
        while (_alt !== 2 && _alt !== ATN.INVALID_ALT_NUMBER) {
          if (_alt === 1) {
            if (this._parseListeners != null) {
              this.triggerExitRuleEvent();
            }
            _prevctx = _localctx;
            {
              this.state = 28;
              this._errHandler.sync(this);
              switch (this.interpreter.adaptivePredict(this._input, 1, this._ctx)) {
                case 1:
                  {
                    _localctx = new AndExpressionContext(new ExprContext(_parentctx, _parentState));
                    this.pushNewRecursionContext(
                      _localctx,
                      _startState,
                      AutomationSelectionParser.RULE_expr,
                    );
                    this.state = 22;
                    if (!this.precpred(this._ctx, 3)) {
                      throw this.createFailedPredicateException('this.precpred(this._ctx, 3)');
                    }
                    this.state = 23;
                    this.match(AutomationSelectionParser.AND);
                    this.state = 24;
                    this.expr(4);
                  }
                  break;

                case 2:
                  {
                    _localctx = new OrExpressionContext(new ExprContext(_parentctx, _parentState));
                    this.pushNewRecursionContext(
                      _localctx,
                      _startState,
                      AutomationSelectionParser.RULE_expr,
                    );
                    this.state = 25;
                    if (!this.precpred(this._ctx, 2)) {
                      throw this.createFailedPredicateException('this.precpred(this._ctx, 2)');
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
    this.enterRule(_localctx, 4, AutomationSelectionParser.RULE_traversalAllowedExpr);
    try {
      this.state = 38;
      this._errHandler.sync(this);
      switch (this._input.LA(1)) {
        case AutomationSelectionParser.NAME:
        case AutomationSelectionParser.CODE_LOCATION:
        case AutomationSelectionParser.TAG:
        case AutomationSelectionParser.STATUS:
        case AutomationSelectionParser.TYPE:
          _localctx = new AttributeExpressionContext(_localctx);
          this.enterOuterAlt(_localctx, 1);
          {
            this.state = 33;
            this.attributeExpr();
          }
          break;
        case AutomationSelectionParser.LPAREN:
          _localctx = new ParenthesizedExpressionContext(_localctx);
          this.enterOuterAlt(_localctx, 2);
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
  public attributeExpr(): AttributeExprContext {
    let _localctx: AttributeExprContext = new AttributeExprContext(this._ctx, this.state);
    this.enterRule(_localctx, 6, AutomationSelectionParser.RULE_attributeExpr);
    try {
      this.state = 59;
      this._errHandler.sync(this);
      switch (this._input.LA(1)) {
        case AutomationSelectionParser.NAME:
          _localctx = new NameExprContext(_localctx);
          this.enterOuterAlt(_localctx, 1);
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
          _localctx = new TagExprContext(_localctx);
          this.enterOuterAlt(_localctx, 2);
          {
            this.state = 43;
            this.match(AutomationSelectionParser.TAG);
            this.state = 44;
            this.match(AutomationSelectionParser.COLON);
            this.state = 45;
            this.value();
            this.state = 48;
            this._errHandler.sync(this);
            switch (this.interpreter.adaptivePredict(this._input, 4, this._ctx)) {
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
          _localctx = new TypeExprContext(_localctx);
          this.enterOuterAlt(_localctx, 3);
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
          _localctx = new StatusExprContext(_localctx);
          this.enterOuterAlt(_localctx, 4);
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
          _localctx = new CodeLocationExprContext(_localctx);
          this.enterOuterAlt(_localctx, 5);
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
    this.enterRule(_localctx, 8, AutomationSelectionParser.RULE_value);
    let _la: number;
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 61;
        _la = this._input.LA(1);
        if (
          !(
            (_la & ~0x1f) === 0 &&
            ((1 << _la) &
              ((1 << AutomationSelectionParser.QUOTED_STRING) |
                (1 << AutomationSelectionParser.UNQUOTED_STRING) |
                (1 << AutomationSelectionParser.NULL_STRING))) !==
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
    this.enterRule(_localctx, 10, AutomationSelectionParser.RULE_keyValue);
    let _la: number;
    try {
      this.enterOuterAlt(_localctx, 1);
      {
        this.state = 63;
        _la = this._input.LA(1);
        if (
          !(
            (_la & ~0x1f) === 0 &&
            ((1 << _la) &
              ((1 << AutomationSelectionParser.QUOTED_STRING) |
                (1 << AutomationSelectionParser.UNQUOTED_STRING) |
                (1 << AutomationSelectionParser.UNQUOTED_WILDCARD_STRING))) !==
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
    '\x03\uC91D\uCABA\u058D\uAFBA\u4F53\u0607\uEA8B\uC241\x03\x14D\x04\x02' +
    '\t\x02\x04\x03\t\x03\x04\x04\t\x04\x04\x05\t\x05\x04\x06\t\x06\x04\x07' +
    '\t\x07\x03\x02\x03\x02\x03\x02\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03' +
    '\x05\x03\x17\n\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x07' +
    '\x03\x1F\n\x03\f\x03\x0E\x03"\v\x03\x03\x04\x03\x04\x03\x04\x03\x04\x03' +
    '\x04\x05\x04)\n\x04\x03\x05\x03\x05\x03\x05\x03\x05\x03\x05\x03\x05\x03' +
    '\x05\x03\x05\x05\x053\n\x05\x03\x05\x03\x05\x03\x05\x03\x05\x03\x05\x03' +
    '\x05\x03\x05\x03\x05\x03\x05\x05\x05>\n\x05\x03\x06\x03\x06\x03\x07\x03' +
    '\x07\x03\x07\x02\x02\x03\x04\b\x02\x02\x04\x02\x06\x02\b\x02\n\x02\f\x02' +
    '\x02\x04\x04\x02\x10\x11\x13\x13\x03\x02\x10\x12\x02G\x02\x0E\x03\x02' +
    '\x02\x02\x04\x16\x03\x02\x02\x02\x06(\x03\x02\x02\x02\b=\x03\x02\x02\x02' +
    '\n?\x03\x02\x02\x02\fA\x03\x02\x02\x02\x0E\x0F\x05\x04\x03\x02\x0F\x10' +
    '\x07\x02\x02\x03\x10\x03\x03\x02\x02\x02\x11\x12\b\x03\x01\x02\x12\x17' +
    '\x05\x06\x04\x02\x13\x14\x07\x05\x02\x02\x14\x17\x05\x04\x03\x06\x15\x17' +
    '\x07\b\x02\x02\x16\x11\x03\x02\x02\x02\x16\x13\x03\x02\x02\x02\x16\x15' +
    '\x03\x02\x02\x02\x17 \x03\x02\x02\x02\x18\x19\f\x05\x02\x02\x19\x1A\x07' +
    '\x03\x02\x02\x1A\x1F\x05\x04\x03\x06\x1B\x1C\f\x04\x02\x02\x1C\x1D\x07' +
    '\x04\x02\x02\x1D\x1F\x05\x04\x03\x05\x1E\x18\x03\x02\x02\x02\x1E\x1B\x03' +
    '\x02\x02\x02\x1F"\x03\x02\x02\x02 \x1E\x03\x02\x02\x02 !\x03\x02\x02' +
    '\x02!\x05\x03\x02\x02\x02" \x03\x02\x02\x02#)\x05\b\x05\x02$%\x07\t\x02' +
    "\x02%&\x05\x04\x03\x02&'\x07\n\x02\x02')\x03\x02\x02\x02(#\x03\x02\x02" +
    '\x02($\x03\x02\x02\x02)\x07\x03\x02\x02\x02*+\x07\v\x02\x02+,\x07\x07' +
    '\x02\x02,>\x05\f\x07\x02-.\x07\r\x02\x02./\x07\x07\x02\x02/2\x05\n\x06' +
    '\x0201\x07\x06\x02\x0213\x05\n\x06\x0220\x03\x02\x02\x0223\x03\x02\x02' +
    '\x023>\x03\x02\x02\x0245\x07\x0F\x02\x0256\x07\x07\x02\x026>\x05\n\x06' +
    '\x0278\x07\x0E\x02\x0289\x07\x07\x02\x029>\x05\n\x06\x02:;\x07\f\x02\x02' +
    ';<\x07\x07\x02\x02<>\x05\n\x06\x02=*\x03\x02\x02\x02=-\x03\x02\x02\x02' +
    '=4\x03\x02\x02\x02=7\x03\x02\x02\x02=:\x03\x02\x02\x02>\t\x03\x02\x02' +
    '\x02?@\t\x02\x02\x02@\v\x03\x02\x02\x02AB\t\x03\x02\x02B\r\x03\x02\x02' +
    '\x02\b\x16\x1E (2=';
  public static __ATN: ATN;
  public static get _ATN(): ATN {
    if (!AutomationSelectionParser.__ATN) {
      AutomationSelectionParser.__ATN = new ATNDeserializer().deserialize(
        Utils.toCharArray(AutomationSelectionParser._serializedATN),
      );
    }

    return AutomationSelectionParser.__ATN;
  }
}

export class StartContext extends ParserRuleContext {
  public expr(): ExprContext {
    return this.getRuleContext(0, ExprContext);
  }
  public EOF(): TerminalNode {
    return this.getToken(AutomationSelectionParser.EOF, 0);
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return AutomationSelectionParser.RULE_start;
  }
  // @Override
  public enterRule(listener: AutomationSelectionListener): void {
    if (listener.enterStart) {
      listener.enterStart(this);
    }
  }
  // @Override
  public exitRule(listener: AutomationSelectionListener): void {
    if (listener.exitStart) {
      listener.exitStart(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AutomationSelectionVisitor<Result>): Result {
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
    return AutomationSelectionParser.RULE_expr;
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
  public enterRule(listener: AutomationSelectionListener): void {
    if (listener.enterTraversalAllowedExpression) {
      listener.enterTraversalAllowedExpression(this);
    }
  }
  // @Override
  public exitRule(listener: AutomationSelectionListener): void {
    if (listener.exitTraversalAllowedExpression) {
      listener.exitTraversalAllowedExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AutomationSelectionVisitor<Result>): Result {
    if (visitor.visitTraversalAllowedExpression) {
      return visitor.visitTraversalAllowedExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class NotExpressionContext extends ExprContext {
  public NOT(): TerminalNode {
    return this.getToken(AutomationSelectionParser.NOT, 0);
  }
  public expr(): ExprContext {
    return this.getRuleContext(0, ExprContext);
  }
  constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: AutomationSelectionListener): void {
    if (listener.enterNotExpression) {
      listener.enterNotExpression(this);
    }
  }
  // @Override
  public exitRule(listener: AutomationSelectionListener): void {
    if (listener.exitNotExpression) {
      listener.exitNotExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AutomationSelectionVisitor<Result>): Result {
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
    return this.getToken(AutomationSelectionParser.AND, 0);
  }
  constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: AutomationSelectionListener): void {
    if (listener.enterAndExpression) {
      listener.enterAndExpression(this);
    }
  }
  // @Override
  public exitRule(listener: AutomationSelectionListener): void {
    if (listener.exitAndExpression) {
      listener.exitAndExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AutomationSelectionVisitor<Result>): Result {
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
    return this.getToken(AutomationSelectionParser.OR, 0);
  }
  constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: AutomationSelectionListener): void {
    if (listener.enterOrExpression) {
      listener.enterOrExpression(this);
    }
  }
  // @Override
  public exitRule(listener: AutomationSelectionListener): void {
    if (listener.exitOrExpression) {
      listener.exitOrExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AutomationSelectionVisitor<Result>): Result {
    if (visitor.visitOrExpression) {
      return visitor.visitOrExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class AllExpressionContext extends ExprContext {
  public STAR(): TerminalNode {
    return this.getToken(AutomationSelectionParser.STAR, 0);
  }
  constructor(ctx: ExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: AutomationSelectionListener): void {
    if (listener.enterAllExpression) {
      listener.enterAllExpression(this);
    }
  }
  // @Override
  public exitRule(listener: AutomationSelectionListener): void {
    if (listener.exitAllExpression) {
      listener.exitAllExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AutomationSelectionVisitor<Result>): Result {
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
    return AutomationSelectionParser.RULE_traversalAllowedExpr;
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
  public enterRule(listener: AutomationSelectionListener): void {
    if (listener.enterAttributeExpression) {
      listener.enterAttributeExpression(this);
    }
  }
  // @Override
  public exitRule(listener: AutomationSelectionListener): void {
    if (listener.exitAttributeExpression) {
      listener.exitAttributeExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AutomationSelectionVisitor<Result>): Result {
    if (visitor.visitAttributeExpression) {
      return visitor.visitAttributeExpression(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class ParenthesizedExpressionContext extends TraversalAllowedExprContext {
  public LPAREN(): TerminalNode {
    return this.getToken(AutomationSelectionParser.LPAREN, 0);
  }
  public expr(): ExprContext {
    return this.getRuleContext(0, ExprContext);
  }
  public RPAREN(): TerminalNode {
    return this.getToken(AutomationSelectionParser.RPAREN, 0);
  }
  constructor(ctx: TraversalAllowedExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: AutomationSelectionListener): void {
    if (listener.enterParenthesizedExpression) {
      listener.enterParenthesizedExpression(this);
    }
  }
  // @Override
  public exitRule(listener: AutomationSelectionListener): void {
    if (listener.exitParenthesizedExpression) {
      listener.exitParenthesizedExpression(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AutomationSelectionVisitor<Result>): Result {
    if (visitor.visitParenthesizedExpression) {
      return visitor.visitParenthesizedExpression(this);
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
    return AutomationSelectionParser.RULE_attributeExpr;
  }
  public copyFrom(ctx: AttributeExprContext): void {
    super.copyFrom(ctx);
  }
}
export class NameExprContext extends AttributeExprContext {
  public NAME(): TerminalNode {
    return this.getToken(AutomationSelectionParser.NAME, 0);
  }
  public COLON(): TerminalNode {
    return this.getToken(AutomationSelectionParser.COLON, 0);
  }
  public keyValue(): KeyValueContext {
    return this.getRuleContext(0, KeyValueContext);
  }
  constructor(ctx: AttributeExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: AutomationSelectionListener): void {
    if (listener.enterNameExpr) {
      listener.enterNameExpr(this);
    }
  }
  // @Override
  public exitRule(listener: AutomationSelectionListener): void {
    if (listener.exitNameExpr) {
      listener.exitNameExpr(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AutomationSelectionVisitor<Result>): Result {
    if (visitor.visitNameExpr) {
      return visitor.visitNameExpr(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class TagExprContext extends AttributeExprContext {
  public TAG(): TerminalNode {
    return this.getToken(AutomationSelectionParser.TAG, 0);
  }
  public COLON(): TerminalNode {
    return this.getToken(AutomationSelectionParser.COLON, 0);
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
    return this.tryGetToken(AutomationSelectionParser.EQUAL, 0);
  }
  constructor(ctx: AttributeExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: AutomationSelectionListener): void {
    if (listener.enterTagExpr) {
      listener.enterTagExpr(this);
    }
  }
  // @Override
  public exitRule(listener: AutomationSelectionListener): void {
    if (listener.exitTagExpr) {
      listener.exitTagExpr(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AutomationSelectionVisitor<Result>): Result {
    if (visitor.visitTagExpr) {
      return visitor.visitTagExpr(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class TypeExprContext extends AttributeExprContext {
  public TYPE(): TerminalNode {
    return this.getToken(AutomationSelectionParser.TYPE, 0);
  }
  public COLON(): TerminalNode {
    return this.getToken(AutomationSelectionParser.COLON, 0);
  }
  public value(): ValueContext {
    return this.getRuleContext(0, ValueContext);
  }
  constructor(ctx: AttributeExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: AutomationSelectionListener): void {
    if (listener.enterTypeExpr) {
      listener.enterTypeExpr(this);
    }
  }
  // @Override
  public exitRule(listener: AutomationSelectionListener): void {
    if (listener.exitTypeExpr) {
      listener.exitTypeExpr(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AutomationSelectionVisitor<Result>): Result {
    if (visitor.visitTypeExpr) {
      return visitor.visitTypeExpr(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class StatusExprContext extends AttributeExprContext {
  public STATUS(): TerminalNode {
    return this.getToken(AutomationSelectionParser.STATUS, 0);
  }
  public COLON(): TerminalNode {
    return this.getToken(AutomationSelectionParser.COLON, 0);
  }
  public value(): ValueContext {
    return this.getRuleContext(0, ValueContext);
  }
  constructor(ctx: AttributeExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: AutomationSelectionListener): void {
    if (listener.enterStatusExpr) {
      listener.enterStatusExpr(this);
    }
  }
  // @Override
  public exitRule(listener: AutomationSelectionListener): void {
    if (listener.exitStatusExpr) {
      listener.exitStatusExpr(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AutomationSelectionVisitor<Result>): Result {
    if (visitor.visitStatusExpr) {
      return visitor.visitStatusExpr(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
export class CodeLocationExprContext extends AttributeExprContext {
  public CODE_LOCATION(): TerminalNode {
    return this.getToken(AutomationSelectionParser.CODE_LOCATION, 0);
  }
  public COLON(): TerminalNode {
    return this.getToken(AutomationSelectionParser.COLON, 0);
  }
  public value(): ValueContext {
    return this.getRuleContext(0, ValueContext);
  }
  constructor(ctx: AttributeExprContext) {
    super(ctx.parent, ctx.invokingState);
    this.copyFrom(ctx);
  }
  // @Override
  public enterRule(listener: AutomationSelectionListener): void {
    if (listener.enterCodeLocationExpr) {
      listener.enterCodeLocationExpr(this);
    }
  }
  // @Override
  public exitRule(listener: AutomationSelectionListener): void {
    if (listener.exitCodeLocationExpr) {
      listener.exitCodeLocationExpr(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AutomationSelectionVisitor<Result>): Result {
    if (visitor.visitCodeLocationExpr) {
      return visitor.visitCodeLocationExpr(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class ValueContext extends ParserRuleContext {
  public QUOTED_STRING(): TerminalNode | undefined {
    return this.tryGetToken(AutomationSelectionParser.QUOTED_STRING, 0);
  }
  public UNQUOTED_STRING(): TerminalNode | undefined {
    return this.tryGetToken(AutomationSelectionParser.UNQUOTED_STRING, 0);
  }
  public NULL_STRING(): TerminalNode | undefined {
    return this.tryGetToken(AutomationSelectionParser.NULL_STRING, 0);
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return AutomationSelectionParser.RULE_value;
  }
  // @Override
  public enterRule(listener: AutomationSelectionListener): void {
    if (listener.enterValue) {
      listener.enterValue(this);
    }
  }
  // @Override
  public exitRule(listener: AutomationSelectionListener): void {
    if (listener.exitValue) {
      listener.exitValue(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AutomationSelectionVisitor<Result>): Result {
    if (visitor.visitValue) {
      return visitor.visitValue(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}

export class KeyValueContext extends ParserRuleContext {
  public QUOTED_STRING(): TerminalNode | undefined {
    return this.tryGetToken(AutomationSelectionParser.QUOTED_STRING, 0);
  }
  public UNQUOTED_STRING(): TerminalNode | undefined {
    return this.tryGetToken(AutomationSelectionParser.UNQUOTED_STRING, 0);
  }
  public UNQUOTED_WILDCARD_STRING(): TerminalNode | undefined {
    return this.tryGetToken(AutomationSelectionParser.UNQUOTED_WILDCARD_STRING, 0);
  }
  constructor(parent: ParserRuleContext | undefined, invokingState: number) {
    super(parent, invokingState);
  }
  // @Override
  public get ruleIndex(): number {
    return AutomationSelectionParser.RULE_keyValue;
  }
  // @Override
  public enterRule(listener: AutomationSelectionListener): void {
    if (listener.enterKeyValue) {
      listener.enterKeyValue(this);
    }
  }
  // @Override
  public exitRule(listener: AutomationSelectionListener): void {
    if (listener.exitKeyValue) {
      listener.exitKeyValue(this);
    }
  }
  // @Override
  public accept<Result>(visitor: AutomationSelectionVisitor<Result>): Result {
    if (visitor.visitKeyValue) {
      return visitor.visitKeyValue(this);
    } else {
      return visitor.visitChildren(this);
    }
  }
}
