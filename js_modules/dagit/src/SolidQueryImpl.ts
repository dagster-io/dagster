import { PipelineExplorerSolidHandleFragment_solid as Solid } from "./types/PipelineExplorerSolidHandleFragment";

const MAX_RENDERED_FOR_EMPTY_QUERY = 100;

type TraverseStepFunction = (
  solid: Solid,
  callback: (nextSolid: Solid) => void
) => void;

class SolidGraphTraverser {
  solidNameMap: { [name: string]: Solid } = {};

  // TODO: One reason doing DFS on the client side is sub optimal.
  // javascript is tail end recursive tho so we could go for ever without worrying about
  // stack overflow problems?

  constructor(solids: Solid[]) {
    solids.forEach(solid => (this.solidNameMap[solid.name] = solid));
  }

  solidNamed(name: string): Solid | undefined {
    return this.solidNameMap[name];
  }

  traverse(solid: Solid, step: TraverseStepFunction, depth: number) {
    const results: Solid[] = [solid];
    if (depth > 0) {
      step(solid, next => {
        results.push(...this.traverse(next, step, depth - 1));
      });
    }
    return results;
  }

  fetchUpstream(solid: Solid, depth: number) {
    const step: TraverseStepFunction = (solid, callback) =>
      solid.inputs.forEach(input =>
        input.dependsOn.forEach(d => callback(this.solidNamed(d.solid.name)!))
      );

    return this.traverse(solid, step, depth);
  }

  fetchDownstream(solid: Solid, depth: number) {
    const step: TraverseStepFunction = (solid, callback) =>
      solid.outputs.forEach(output =>
        output.dependedBy.forEach(d => callback(this.solidNamed(d.solid.name)!))
      );

    return this.traverse(solid, step, depth);
  }
}

function expansionDepthForClause(clause: string) {
  return clause.includes("*") ? Number.MAX_SAFE_INTEGER : clause.length;
}

export function filterSolidsByQuery(solids: Solid[], query: string) {
  if (query === "*") {
    return { all: solids, focus: [] };
  }
  if (query === "") {
    return {
      all: solids.length < MAX_RENDERED_FOR_EMPTY_QUERY ? solids : [],
      focus: []
    };
  }

  const traverser = new SolidGraphTraverser(solids);
  const results = new Set<Solid>();
  const clauses = query.split(/(,| AND | and )/g);
  const focus = new Set<Solid>();

  for (const clause of clauses) {
    const parts = /(\*?\+*)([\w\d_-]+)(\+*\*?)/.exec(clause.trim());
    if (!parts) continue;
    const [, parentsClause, solidName, descendentsClause] = parts;
    const solidsMatching = solids.filter(
      s =>
        solidName === s.name ||
        (solidName.length > 3 && s.name.includes(solidName))
    );

    for (const solid of solidsMatching) {
      const upDepth = expansionDepthForClause(parentsClause);
      const downDepth = expansionDepthForClause(descendentsClause);

      focus.add(solid);
      results.add(solid);
      traverser
        .fetchUpstream(solid, upDepth)
        .forEach(other => results.add(other));
      traverser
        .fetchDownstream(solid, downDepth)
        .forEach(other => results.add(other));
    }
  }

  return {
    all: Array.from(results),
    focus: Array.from(focus)
  };
}
