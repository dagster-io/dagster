export type Edge = {a: string; b: string};

export const isHighlighted = (edges: Edge[], {a, b}: Edge) =>
  edges.some((h) => (h.a === a && h.b === b) || (h.b === a && h.a === b));

export const isSolidHighlighted = (edges: Edge[], name: string) =>
  edges.some((h) => h.a.split(':')[0] === name || h.b.split(':')[0] === name);
