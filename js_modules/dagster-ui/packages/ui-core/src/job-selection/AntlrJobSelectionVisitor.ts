import {AbstractParseTreeVisitor} from 'antlr4ts/tree/AbstractParseTreeVisitor';
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
    return this.visit(ctx.expr());
  }

  visitTraversalAllowedExpression(ctx: TraversalAllowedExpressionContext) {
    return this.visit(ctx.traversalAllowedExpr());
  }

  visitNotExpression(ctx: NotExpressionContext) {
    const selection = this.visit(ctx.expr());
    return new Set([...this.all_jobs].filter((i) => !selection.has(i)));
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
    return this.all_jobs;
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
    const selection = [...this.all_jobs].filter((i) => regex.test(i.name));
    return new Set(selection);
  }

  visitCodeLocationExpr(ctx: CodeLocationExprContext) {
    const value: string = getValue(ctx.value());
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
