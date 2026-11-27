import {dynamicKeyWithoutIndex, isPlannedDynamicStep} from '../gantt/DynamicStepSupport';

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

export class GraphTraverser<T extends GraphQueryItem> {
  itemNameMap = new Map<string, T>();

  constructor(items: T[]) {
    items.forEach((item) => this.itemNameMap.set(item.name, item));
  }

  itemNamed(name: string): T | undefined {
    return this.itemNameMap.get(name);
  }

  traverse(roots: T | T[], nextItemsForItem: TraverseStepFunction<T>, maxDepth: number) {
    /** Breadth-first from all roots at once, so each item is reached at its shortest distance
     * from any root and is queued only once. Depth limits depend on this, since graphs can
     * look like this:
     *
     *  /---------\
     * A --> B --> C
     */
    const visited = new Set<string>();
    const queue: [T, number][] = [];
    for (const root of Array.isArray(roots) ? roots : [roots]) {
      if (!visited.has(root.name)) {
        visited.add(root.name);
        queue.push([root, 0]);
      }
    }

    // The array iterator also visits entries appended during the loop, so this walks the BFS
    // without the O(n) `shift()`.
    for (const [item, depth] of queue) {
      if (depth < maxDepth) {
        nextItemsForItem(item, (next) => {
          if (!visited.has(next.name)) {
            visited.add(next.name);
            queue.push([next, depth + 1]);
          }
        });
      }
    }

    return queue.map(([item]) => item);
  }

  private upstreamStep: TraverseStepFunction<T> = (item, callback) =>
    item.inputs.forEach((input) =>
      input.dependsOn.forEach((d) => {
        const next = this.itemNamed(d.solid.name);
        if (next) {
          callback(next);
        }
      }),
    );

  private downstreamStep: TraverseStepFunction<T> = (item, callback) =>
    item.outputs.forEach((output) =>
      output.dependedBy.forEach((d) => {
        const next = this.itemNamed(d.solid.name);
        if (next) {
          callback(next);
        }
      }),
    );

  fetchUpstream(items: T | T[], depth: number) {
    return this.traverse(items, this.upstreamStep, depth);
  }

  fetchDownstream(items: T | T[], depth: number) {
    return this.traverse(items, this.downstreamStep, depth);
  }

  /** Items in `selection` with no other selected item downstream. Assumes the graph is acyclic. */
  sinks(selection: Set<T>) {
    return this.withoutSelectedNeighbors(selection, this.upstreamStep);
  }

  /** Items in `selection` with no other selected item upstream. Assumes the graph is acyclic. */
  roots(selection: Set<T>) {
    return this.withoutSelectedNeighbors(selection, this.downstreamStep);
  }

  // Everything reachable (via `step`) from a neighbor of a selected item has a selected item on
  // the other side, so one traversal replaces a traversal per item. Self-edges (assets that
  // depend on their own earlier partitions) don't count.
  private withoutSelectedNeighbors(selection: Set<T>, step: TraverseStepFunction<T>) {
    const neighbors: T[] = [];
    for (const item of selection) {
      step(item, (next) => {
        if (next.name !== item.name) {
          neighbors.push(next);
        }
      });
    }
    const excluded = new Set(this.traverse(neighbors, step, Number.MAX_SAFE_INTEGER));
    return new Set([...selection].filter((item) => !excluded.has(item)));
  }
}

function expansionDepthForClause(clause: string) {
  return clause.includes('*') ? Number.MAX_SAFE_INTEGER : clause.length;
}

export function filterByQuery<T extends GraphQueryItem>(items: T[], query: string) {
  if (query === '*' || query === '') {
    return {all: items, focus: []};
  }

  const traverser = new GraphTraverser<T>(items);
  const results = new Set<T>();
  const clauses = query.toLowerCase().split(/(,| AND | and | )/g);
  const focus = new Set<T>();

  for (const clause of clauses) {
    const parts = /(\*?\+*)([.\w\d>\[\?\]\"_\/-]+)(\+*\*?)/.exec(clause.trim());
    if (!parts) {
      continue;
    }
    const [, parentsClause = '', itemName = '', descendentsClause = ''] = parts;

    const itemsMatching = items.filter((s) => {
      const name = s.name.toLowerCase();
      if (isPlannedDynamicStep(itemName.replace(/\"/g, ''))) {
        // When unresolved dynamic step (i.e ends with `[?]`) is selected, match all dynamic steps
        return name.startsWith(dynamicKeyWithoutIndex(itemName.replace(/\"/g, '')));
      } else {
        return /\".*\"/.test(itemName)
          ? name === itemName.replace(/\"/g, '')
          : name.includes(itemName);
      }
    });

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
