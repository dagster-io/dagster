export interface AssetKey {
  path: string[];
}

export interface AssetNumericHistoricalData {
  [metadataEntryLabel: string]: {
    minY: number;
    maxY: number;
    minXNumeric: number;
    maxXNumeric: number;
    xAxis: 'time' | 'partition';
    values: {
      x: number | string; // time or partition
      xNumeric: number; // time or partition index
      y: number;
    }[];
  };
}
