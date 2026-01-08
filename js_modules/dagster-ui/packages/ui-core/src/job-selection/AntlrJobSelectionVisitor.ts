import {AbstractParseTreeVisitor} from 'antlr4ng';
import escapeRegExp from 'lodash/escapeRegExp';

import {buildRepoPathForHuman} from '../workspace/buildRepoAddress';
import {RepoAddress} from '../workspace/types';
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
  TraversalAllowedExpressionContext,
} from './generated/JobSelectionParser';
import {JobSelectionVisitor} from './generated/JobSelectionVisitor';
import {getValue} from '../asset-selection/util';

type Job = {
  name: string;
  repo: RepoAddress;
};

export class AntlrJobSelectionVisitor<T extends Job>
  extends AbstractParseTreeVisitor<Set<T>>
  implements JobSelectionVisitor<Set<T>>
{
  all_jobs: Set<T>;

  protected defaultResult() {
    return new Set<T>();
  }

  constructor(all_jobs: T[]) {
    super();
    this.all_jobs = new Set(all_jobs);
  }

  visitStart(ctx: StartContext) {
    const expr = ctx.expr();
    return expr ? (this.visit(expr) ?? this.defaultResult()) : this.defaultResult();
  }

  visitTraversalAllowedExpression(ctx: TraversalAllowedExpressionContext) {
    const expr = ctx.traversalAllowedExpr();
    return expr ? (this.visit(expr) ?? this.defaultResult()) : this.defaultResult();
  }

  visitNotExpression(ctx: NotExpressionContext) {
    const expr = ctx.expr();
    const selection = expr ? (this.visit(expr) ?? this.defaultResult()) : this.defaultResult();
    return new Set([...this.all_jobs].filter((i) => !selection.has(i)));
  }

  visitAndExpression(ctx: AndExpressionContext) {
    const leftExpr = ctx.expr(0);
    const rightExpr = ctx.expr(1);
    const left = leftExpr ? (this.visit(leftExpr) ?? this.defaultResult()) : this.defaultResult();
    const right = rightExpr
      ? (this.visit(rightExpr) ?? this.defaultResult())
      : this.defaultResult();
    return new Set([...left].filter((i) => right.has(i)));
  }

  visitOrExpression(ctx: OrExpressionContext) {
    const leftExpr = ctx.expr(0);
    const rightExpr = ctx.expr(1);
    const left = leftExpr ? (this.visit(leftExpr) ?? this.defaultResult()) : this.defaultResult();
    const right = rightExpr
      ? (this.visit(rightExpr) ?? this.defaultResult())
      : this.defaultResult();
    return new Set([...left, ...right]);
  }

  visitAllExpression(_ctx: AllExpressionContext) {
    return this.all_jobs;
  }

  visitAttributeExpression(ctx: AttributeExpressionContext) {
    const attrExpr = ctx.attributeExpr();
    return attrExpr ? (this.visit(attrExpr) ?? this.defaultResult()) : this.defaultResult();
  }

  visitParenthesizedExpression(ctx: ParenthesizedExpressionContext) {
    const expr = ctx.expr();
    return expr ? (this.visit(expr) ?? this.defaultResult()) : this.defaultResult();
  }

  visitNameExpr(ctx: NameExprContext) {
    const keyValue = ctx.keyValue();
    const value = keyValue ? getValue(keyValue) : '';
    const regex: RegExp = new RegExp(`^${escapeRegExp(value).replaceAll('\\*', '.*')}$`);
    const selection = [...this.all_jobs].filter((i) => regex.test(i.name));
    return new Set(selection);
  }

  visitCodeLocationExpr(ctx: CodeLocationExprContext) {
    const valueCtx = ctx.value();
    const value = valueCtx ? getValue(valueCtx) : '';
    const regex: RegExp = new RegExp(`^${escapeRegExp(value).replaceAll('\\*', '.*')}$`);
    const selection = new Set<T>();
    for (const job of this.all_jobs) {
      const repository = job.repo;
      const location = repository.name
        ? buildRepoPathForHuman(repository.name, repository.location)
        : '';
      if (regex.test(location)) {
        selection.add(job);
      }
    }
    return selection;
  }
}
