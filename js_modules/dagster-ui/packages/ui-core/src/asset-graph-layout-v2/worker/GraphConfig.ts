const MARGIN = 100;

export type AssetLayoutDirection = 'vertical' | 'horizontal';

export type LayoutAssetGraphConfig = dagre.GraphLabel & {
  direction: AssetLayoutDirection;
  /** Pass `auto` to use getAssetNodeDimensions, or a value to give nodes a fixed height */
  nodeHeight: number | 'auto';
  /** Our asset groups have "title bars" - use these numbers to adjust the bounding boxes.
   * Note that these adjustments are applied post-dagre layout. For padding > nodesep, you
   * may need to set "clusterpaddingtop", "clusterpaddingbottom" so Dagre lays out the boxes
   * with more spacing.
   */
  groupPaddingTop: number;
  groupPaddingBottom: number;
  groupRendering: 'if-varied' | 'always';

  /** Supported in Dagre, just not documented. Additional spacing between group nodes */
  clusterpaddingtop?: number;
  clusterpaddingbottom?: number;
  ranker?: 'tight-tree' | 'longest-path' | 'network-simplex';
};

export type LayoutAssetGraphOptions = {
  direction: AssetLayoutDirection;
  overrides?: Partial<LayoutAssetGraphConfig>;
};

export const Config: Record<AssetLayoutDirection, LayoutAssetGraphConfig> = {
  horizontal: {
    ranker: 'tight-tree',
    direction: 'horizontal',
    marginx: MARGIN,
    marginy: MARGIN,
    ranksep: 60,
    rankdir: 'LR',
    edgesep: 90,
    nodesep: -10,
    nodeHeight: 'auto',
    groupPaddingTop: 65,
    groupPaddingBottom: -15,
    groupRendering: 'if-varied',
    clusterpaddingtop: 100,
  },
  vertical: {
    ranker: 'tight-tree',
    direction: 'horizontal',
    marginx: MARGIN,
    marginy: MARGIN,
    ranksep: 20,
    rankdir: 'TB',
    nodesep: 40,
    edgesep: 10,
    nodeHeight: 'auto',
    groupPaddingTop: 55,
    groupPaddingBottom: -5,
    groupRendering: 'if-varied',
  },
};
