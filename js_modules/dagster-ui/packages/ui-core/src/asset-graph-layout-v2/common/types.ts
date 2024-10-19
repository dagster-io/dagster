/** An incoming edge in the graph. */
export declare interface Edge {
  /** The id of the source node (where the edge comes from). */
  sourceNodeId: string;
  targetNodeId: string;
}

/** A point with x and y coordinate. */
export declare interface Point {
  x: number;
  y: number;
}

/** A rectangle. */
export declare interface Rect {
  x: number;
  y: number;
  width: number;
  height: number;
}
