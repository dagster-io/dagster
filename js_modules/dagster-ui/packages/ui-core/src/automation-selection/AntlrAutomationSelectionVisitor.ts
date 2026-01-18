import {AbstractParseTreeVisitor, ParseTree} from 'antlr4ng';
import escapeRegExp from 'lodash/escapeRegExp';

import {Automation} from './input/useAutomationSelectionAutoCompleteProvider';
import {getValue, isNullValue} from '../asset-selection/util';
import {buildRepoPathForHuman} from '../workspace/buildRepoAddress';
import {
  AllExpressionContext,
  AndExpressionContext,
  AttributeExpressionContext,
  CodeLocationExprContext,
  NameExprContext,
  NotExpressionContext,
  OrExpressionContext,
  ParenthesizedExpressionContext,
  StartContext,
  StatusExprContext,
  TagExprContext,
  TraversalAllowedExpressionContext,
  TypeExprContext,
} from './generated/AutomationSelectionParser';
import {AutomationSelectionVisitor} from './generated/AutomationSelectionVisitor';

export class AntlrAutomationSelectionVisitor<T extends Automation>
  extends AbstractParseTreeVisitor<Set<T>>
  implements AutomationSelectionVisitor<Set<T>>
{
  protected all_automations: Set<T>;
  protected all_automations_by_key: Map<string, T>;

  protected defaultResult() {
    return new Set<T>();
  }

  /** Helper to visit a nullable context and return defaultResult() if null */
  private visitOrDefault(ctx: ParseTree | null): Set<T> {
    return ctx ? (this.visit(ctx) ?? this.defaultResult()) : this.defaultResult();
  }

  // Supplementary data is not used in oss
  constructor(all_automations: T[]) {
    super();
    this.all_automations = new Set(all_automations);
    this.all_automations_by_key = new Map(
      all_automations.map((automation) => [automation.name, automation]),
    );
  }

  visitStart(ctx: StartContext) {
    return this.visitOrDefault(ctx.expr());
  }

  visitTraversalAllowedExpression(ctx: TraversalAllowedExpressionContext) {
    return this.visitOrDefault(ctx.traversalAllowedExpr());
  }

  visitNotExpression(ctx: NotExpressionContext) {
    const selection = this.visitOrDefault(ctx.expr());
    return new Set([...this.all_automations].filter((i) => !selection.has(i)));
  }

  visitAndExpression(ctx: AndExpressionContext) {
    const left = this.visitOrDefault(ctx.expr(0));
    const right = this.visitOrDefault(ctx.expr(1));
    return new Set([...left].filter((i) => right.has(i)));
  }

  visitOrExpression(ctx: OrExpressionContext) {
    const left = this.visitOrDefault(ctx.expr(0));
    const right = this.visitOrDefault(ctx.expr(1));
    return new Set([...left, ...right]);
  }

  visitAllExpression(_ctx: AllExpressionContext) {
    return this.all_automations;
  }

  visitAttributeExpression(ctx: AttributeExpressionContext) {
    return this.visitOrDefault(ctx.attributeExpr());
  }

  visitParenthesizedExpression(ctx: ParenthesizedExpressionContext) {
    return this.visitOrDefault(ctx.expr());
  }

  visitNameExpr(ctx: NameExprContext) {
    const keyValue = ctx.keyValue();
    const value = keyValue ? getValue(keyValue) : '';
    const regex: RegExp = new RegExp(`^${escapeRegExp(value).replaceAll('\\*', '.*')}$`);
    const selection = [...this.all_automations].filter((i) => regex.test(i.name));
    return new Set(selection);
  }

  visitTypeExpr(ctx: TypeExprContext) {
    const valueCtx = ctx.value();
    const value = valueCtx ? getValue(valueCtx) : '';
    const selection = [...this.all_automations].filter(
      (i) => i.type.toLowerCase() === value.toLowerCase(),
    );
    return new Set(selection);
  }

  visitTagExpr(ctx: TagExprContext) {
    const keyCtx = ctx.value(0);
    const key = keyCtx ? getValue(keyCtx) : '';
    let value: string | undefined = undefined;
    if (ctx.EQUAL()) {
      const valueCtx = ctx.value(1);
      value = valueCtx ? getValue(valueCtx) : undefined;
    }
    const isNullKey = keyCtx ? isNullValue(keyCtx) : false;
    return new Set(
      [...this.all_automations].filter((i) => {
        if (i.tags.length > 0) {
          return i.tags.some(
            (t) => t.key === key && ((!value && t.value === '') || t.value === value),
          );
        }
        return isNullKey && !value;
      }),
    );
  }

  visitCodeLocationExpr(ctx: CodeLocationExprContext) {
    const valueCtx = ctx.value();
    const value = valueCtx ? getValue(valueCtx) : '';
    const regex: RegExp = new RegExp(`^${escapeRegExp(value).replaceAll('\\*', '.*')}$`);
    const selection = new Set<T>();
    for (const automation of this.all_automations) {
      const repository = automation.repo;
      const location = repository.name
        ? buildRepoPathForHuman(repository.name, repository.location)
        : '';
      if (regex.test(location)) {
        selection.add(automation);
      }
    }
    return selection;
  }

  visitStatusExpr(ctx: StatusExprContext) {
    const valueCtx = ctx.value();
    const statusName = valueCtx ? getValue(valueCtx) : '';
    const selection = [...this.all_automations].filter((i) => i.status === statusName);
    return new Set(selection);
  }
}
