import {AbstractParseTreeVisitor} from 'antlr4ng';
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
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    return this.visit(ctx.expr()!) ?? this.defaultResult();
  }

  visitTraversalAllowedExpression(ctx: TraversalAllowedExpressionContext) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    return this.visit(ctx.traversalAllowedExpr()!) ?? this.defaultResult();
  }

  visitNotExpression(ctx: NotExpressionContext) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const selection = this.visit(ctx.expr()!) ?? this.defaultResult();
    return new Set([...this.all_automations].filter((i) => !selection.has(i)));
  }

  visitAndExpression(ctx: AndExpressionContext) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const left = this.visit(ctx.expr(0)!) ?? this.defaultResult();
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const right = this.visit(ctx.expr(1)!) ?? this.defaultResult();
    return new Set([...left].filter((i) => right.has(i)));
  }

  visitOrExpression(ctx: OrExpressionContext) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const left = this.visit(ctx.expr(0)!) ?? this.defaultResult();
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const right = this.visit(ctx.expr(1)!) ?? this.defaultResult();
    return new Set([...left, ...right]);
  }

  visitAllExpression(_ctx: AllExpressionContext) {
    return this.all_automations;
  }

  visitAttributeExpression(ctx: AttributeExpressionContext) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    return this.visit(ctx.attributeExpr()!) ?? this.defaultResult();
  }

  visitParenthesizedExpression(ctx: ParenthesizedExpressionContext) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    return this.visit(ctx.expr()!) ?? this.defaultResult();
  }

  visitNameExpr(ctx: NameExprContext) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const value: string = getValue(ctx.keyValue()!);
    const regex: RegExp = new RegExp(`^${escapeRegExp(value).replaceAll('\\*', '.*')}$`);
    const selection = [...this.all_automations].filter((i) => regex.test(i.name));
    return new Set(selection);
  }

  visitTypeExpr(ctx: TypeExprContext) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const value: string = getValue(ctx.value()!);
    const selection = [...this.all_automations].filter(
      (i) => i.type.toLowerCase() === value.toLowerCase(),
    );
    return new Set(selection);
  }

  visitTagExpr(ctx: TagExprContext) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const key: string = getValue(ctx.value(0)!);
    let value: string | undefined = undefined;
    if (ctx.EQUAL()) {
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      value = getValue(ctx.value(1)!);
    }
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const isNullKey = isNullValue(ctx.value(0)!);
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
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const value: string = getValue(ctx.value()!);
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
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const statusName: string = getValue(ctx.value()!);
    const selection = [...this.all_automations].filter((i) => i.status === statusName);
    return new Set(selection);
  }
}
