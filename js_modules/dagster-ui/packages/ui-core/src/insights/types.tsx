export enum ReportingMetricsGranularity {
  DAILY = 'DAILY',
  MONTHLY = 'MONTHLY',
  WEEKLY = 'WEEKLY',
}

export enum ReportingUnitType {
  FLOAT = 'FLOAT',
  INTEGER = 'INTEGER',
  TIME_MS = 'TIME_MS',
}

export type DatapointType = 'deployment' | 'asset-group' | 'asset' | 'job';
export type Datapoint = {
  lineColor: string;
  type: DatapointType;
  label: string;
  values: (number | null)[];
};

export type BarValue = {
  value: number;
  key: string;
  label: string;
  href: string;
};

export type BarDatapoint = {
  barColor: string;
  type: DatapointType;
  label: string;
  values: (BarValue | null)[];
};
