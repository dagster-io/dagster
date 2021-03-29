const MAX_RENDERED_FOR_EMPTY_QUERY = 100;

export interface GraphQueryItem {
  name: string;
  inputs: {
    dependsOn: {
      solid: {
        name: string;
      };
    }[];
  }[];
  outputs: {
    dependedBy: {
      solid: {
        name: string;
      };
    }[];
  }[];
}

type TraverseStepFunction<T> = (item: T, callback: (nextItem: T) => void) => void;

class GraphTraverser<T extends GraphQueryItem> {
  itemNameMap: {[name: string]: T} = {};

  // TODO: One reason doing DFS on the client side is sub optimal.
  // javascript is tail end recursive tho so we could go for ever without worrying about
  // stack overflow problems?

  constructor(items: T[]) {
    items.forEach((item) => (this.itemNameMap[item.name] = item));
  }

  itemNamed(name: string): T | undefined {
    return this.itemNameMap[name];
  }

  traverse(
    item: T,
    step: TraverseStepFunction<T>,
    depth: number,
    results: {[key: string]: T} = {},
  ) {
    results[item.name] = item;

    if (depth > 0) {
      step(item, (next) => {
        if (!(next.name in results)) {
          this.traverse(next, step, depth - 1, results);
        }
      });
    }
    return Object.values(results);
  }

  fetchUpstream(item: T, depth: number) {
    const step: TraverseStepFunction<T> = (item, callback) =>
      item.inputs.forEach((input) =>
        input.dependsOn.forEach((d) => callback(this.itemNamed(d.solid.name)!)),
      );

    return this.traverse(item, step, depth);
  }

  fetchDownstream(item: T, depth: number) {
    const step: TraverseStepFunction<T> = (item, callback) =>
      item.outputs.forEach((output) =>
        output.dependedBy.forEach((d) => callback(this.itemNamed(d.solid.name)!)),
      );

    return this.traverse(item, step, depth);
  }
}

function expansionDepthForClause(clause: string) {
  return clause.includes('*') ? Number.MAX_SAFE_INTEGER : clause.length;
}

export function filterByQuery<T extends GraphQueryItem>(items: T[], query: string) {
  if (query === '*') {
    return {all: items, focus: []};
  }
  if (query === '') {
    return {
      all: items.length < MAX_RENDERED_FOR_EMPTY_QUERY ? items : [],
      focus: [],
    };
  }

  const traverser = new GraphTraverser<T>(items);
  const results = new Set<T>();
  const clauses = query.split(/(,| AND | and | )/g);
  const focus = new Set<T>();

  for (const clause of clauses) {
    const parts = /(\*?\+*)([.\w\d\[\]_-]+)(\+*\*?)/.exec(clause.trim());
    if (!parts) {
      continue;
    }
    const [, parentsClause, itemName, descendentsClause] = parts;
    const itemsMatching = items.filter((s) => itemName.length > 3 && s.name.includes(itemName));

    for (const item of itemsMatching) {
      const upDepth = expansionDepthForClause(parentsClause);
      const downDepth = expansionDepthForClause(descendentsClause);

      focus.add(item);
      results.add(item);
      traverser.fetchUpstream(item, upDepth).forEach((other) => results.add(other));
      traverser.fetchDownstream(item, downDepth).forEach((other) => results.add(other));
    }
  }

  return {
    all: Array.from(results),
    focus: Array.from(focus),
  };
}
