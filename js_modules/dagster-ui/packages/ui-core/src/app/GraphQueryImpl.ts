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

const QUOTED_TEXT_REGEX = /\".*\"/;

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
        input.dependsOn.forEach((d) => {
          const item = this.itemNamed(d.solid.name);
          item && callback(item);
        }),
      );

    return this.traverse(item, step, depth);
  }

  fetchDownstream(item: T, depth: number) {
    const step: TraverseStepFunction<T> = (item, callback) =>
      item.outputs.forEach((output) =>
        output.dependedBy.forEach((d) => {
          const item = this.itemNamed(d.solid.name);
          item && callback(item);
        }),
      );

    return this.traverse(item, step, depth);
  }

  findAllPathsBetweenMultiple(startNodes: T[], endNodes: T[], callback: (path: T[]) => void) {
    const endSet = new Set(endNodes);

    startNodes.forEach((nodeA) => {
      const start = this.itemNamed(nodeA.name);
      if (!start) {
        console.error(`Start node ${nodeA} does not exist.`);
        return;
      }

      const visited: Set<string> = new Set();
      const path: T[] = [];

      const dfs = (current: T): void => {
        path.push(current);
        visited.add(current.name);

        if (endSet.size === 0 || endSet.has(current)) {
          callback([...path]);
        }

        this.fetchDownstream(current, 1).forEach((next) => {
          if (!visited.has(next.name)) {
            dfs(next);
          }
        });

        path.pop();
        visited.delete(current.name);
      };

      dfs(start);
    });
  }
}

function expansionDepthForClause(clause: string) {
  return clause.includes('*') ? Number.MAX_SAFE_INTEGER : clause.length;
}

function selectionFilter({selection, itemName}: {selection: string; itemName: string}) {
  return QUOTED_TEXT_REGEX.test(selection)
    ? itemName === selection.replace(/\"/g, '')
    : itemName.includes(selection);
}

export function filterByQuery<T extends GraphQueryItem>(items: T[], query: string) {
  if (query === '*' || query === '' || query === '->') {
    return {all: items, focus: []};
  }

  const traverser = new GraphTraverser<T>(items);
  const results = new Set<T>();

  const clauses = removeSpacesAroundArrow(query).split(/(,| AND | and | )/g);
  const focus = new Set<T>();

  for (const clause of clauses) {
    // This regex focuses on matching exactly the quoted strings around "->" without any spaces
    const regex = /("([^"]+)"|(\w+))->("([^"]+)"|(\w+))?/g;
    const pathClauseParts = regex.exec(clause.trim());
    if (pathClauseParts) {
      const pathClauseStart = pathClauseParts[1] || pathClauseParts[2];
      const pathClauseEnd = pathClauseParts[4] || pathClauseParts[5];
      const pathClauseStartMatches = pathClauseStart
        ? items.filter((item) => selectionFilter({itemName: item.name, selection: pathClauseStart}))
        : [];
      const pathClauseEndMatches = pathClauseEnd
        ? items.filter((item) => selectionFilter({itemName: item.name, selection: pathClauseEnd}))
        : [];

      if (pathClauseStart) {
        if (pathClauseStartMatches.length) {
          traverser.findAllPathsBetweenMultiple(
            pathClauseStartMatches,
            pathClauseEndMatches,
            (path) => {
              path.forEach((node) => {
                results.add(node);
              });
            },
          );
        }
      }
      continue;
    }

    const parts = /(\*?\+*)([.\w\d>\[\?\]\"_\/-]+)(\+*\*?)/.exec(clause.trim());
    if (!parts) {
      continue;
    }
    const [, parentsClause = '', selectionName = '', descendentsClause = ''] = parts;

    const itemsMatching = items.filter((item) => {
      if (isPlannedDynamicStep(selectionName.replace(/\"/g, ''))) {
        // When unresolved dynamic step (i.e ends with `[?]`) is selected, match all dynamic steps
        return item.name.startsWith(dynamicKeyWithoutIndex(selectionName.replace(/\"/g, '')));
      } else {
        return selectionFilter({selection: selectionName, itemName: item.name});
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

function removeSpacesAroundArrow(inputString: string) {
  // This regex matches any characters (captured in group 1), followed by optional spaces,
  // the "->" symbol, more optional spaces, and any characters again (captured in group 2).
  const regex = /([^\s]+)\s*->\s*([^\s]+)/g;
  // Replace the matched strings with the first and second group concatenated with '->'
  return inputString.replace(regex, '$1->$2');
}
