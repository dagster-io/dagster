import {AbstractParseTreeVisitor} from 'antlr4ts/tree/AbstractParseTreeVisitor';
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

  // Supplementary data is not used in oss
  constructor(all_automations: T[]) {
    super();
    this.all_automations = new Set(all_automations);
    this.all_automations_by_key = new Map(
      all_automations.map((automation) => [automation.name, automation]),
    );
  }

  visitStart(ctx: StartContext) {
    return this.visit(ctx.expr());
  }

  visitTraversalAllowedExpression(ctx: TraversalAllowedExpressionContext) {
    return this.visit(ctx.traversalAllowedExpr());
  }

  visitNotExpression(ctx: NotExpressionContext) {
    const selection = this.visit(ctx.expr());
    return new Set([...this.all_automations].filter((i) => !selection.has(i)));
  }

  visitAndExpression(ctx: AndExpressionContext) {
    const left = this.visit(ctx.expr(0));
    const right = this.visit(ctx.expr(1));
    return new Set([...left].filter((i) => right.has(i)));
  }

  visitOrExpression(ctx: OrExpressionContext) {
    const left = this.visit(ctx.expr(0));
    const right = this.visit(ctx.expr(1));
    return new Set([...left, ...right]);
  }

  visitAllExpression(_ctx: AllExpressionContext) {
    return this.all_automations;
  }

  visitAttributeExpression(ctx: AttributeExpressionContext) {
    return this.visit(ctx.attributeExpr());
  }

  visitParenthesizedExpression(ctx: ParenthesizedExpressionContext) {
    return this.visit(ctx.expr());
  }

  visitNameExpr(ctx: NameExprContext) {
    const value: string = getValue(ctx.keyValue());
    const regex: RegExp = new RegExp(`^${escapeRegExp(value).replaceAll('\\*', '.*')}$`);
    const selection = [...this.all_automations].filter((i) => regex.test(i.name));
    return new Set(selection);
  }

  visitTypeExpr(ctx: TypeExprContext) {
    const value: string = getValue(ctx.value());
    const selection = [...this.all_automations].filter(
      (i) => i.type.toLowerCase() === value.toLowerCase(),
    );
    return new Set(selection);
  }

  visitTagExpr(ctx: TagExprContext) {
    const key: string = getValue(ctx.value(0));
    let value: string | undefined = undefined;
    if (ctx.EQUAL()) {
      value = getValue(ctx.value(1));
    }
    const isNullKey = isNullValue(ctx.value(0));
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
    const value: string = getValue(ctx.value());
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
    const statusName: string = getValue(ctx.value());
    const selection = [...this.all_automations].filter((i) => i.status === statusName);
    return new Set(selection);
  }
}
