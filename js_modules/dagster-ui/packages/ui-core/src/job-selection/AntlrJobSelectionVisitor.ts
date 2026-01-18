import {AbstractParseTreeVisitor, ParseTree} from 'antlr4ng';
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

  /** Helper to visit a nullable context and return defaultResult() if null */
  private visitOrDefault(ctx: ParseTree | null): Set<T> {
    return ctx ? (this.visit(ctx) ?? this.defaultResult()) : this.defaultResult();
  }

  constructor(all_jobs: T[]) {
    super();
    this.all_jobs = new Set(all_jobs);
  }

  visitStart(ctx: StartContext) {
    return this.visitOrDefault(ctx.expr());
  }

  visitTraversalAllowedExpression(ctx: TraversalAllowedExpressionContext) {
    return this.visitOrDefault(ctx.traversalAllowedExpr());
  }

  visitNotExpression(ctx: NotExpressionContext) {
    const selection = this.visitOrDefault(ctx.expr());
    return new Set([...this.all_jobs].filter((i) => !selection.has(i)));
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
    return this.all_jobs;
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
