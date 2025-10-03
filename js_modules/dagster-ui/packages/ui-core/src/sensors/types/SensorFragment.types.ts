// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type SensorFragment = {
  __typename: 'Sensor';
  id: string;
  name: string;
  description: string | null;
  minIntervalSeconds: number;
  sensorType: Types.SensorType;
  defaultStatus: Types.InstigationStatus;
  canReset: boolean;
  nextTick: {__typename: 'DryRunInstigationTick'; timestamp: number | null} | null;
  sensorState: {
    __typename: 'InstigationState';
    id: string;
    selectorId: string;
    name: string;
    instigationType: Types.InstigationType;
    status: Types.InstigationStatus;
    hasStartPermission: boolean;
    hasStopPermission: boolean;
    repositoryName: string;
    repositoryLocationName: string;
    runningCount: number;
    typeSpecificData:
      | {__typename: 'ScheduleData'; cronSchedule: string}
      | {__typename: 'SensorData'; lastRunKey: string | null; lastCursor: string | null}
      | null;
    runs: Array<{
      __typename: 'Run';
      id: string;
      status: Types.RunStatus;
      creationTime: number;
      startTime: number | null;
      endTime: number | null;
      updateTime: number | null;
    }>;
    ticks: Array<{
      __typename: 'InstigationTick';
      id: string;
      cursor: string | null;
      status: Types.InstigationTickStatus;
      timestamp: number;
      skipReason: string | null;
      runIds: Array<string>;
      runKeys: Array<string>;
      error: {
        __typename: 'PythonError';
        message: string;
        stack: Array<string>;
        errorChain: Array<{
          __typename: 'ErrorChainLink';
          isExplicitLink: boolean;
          error: {__typename: 'PythonError'; message: string; stack: Array<string>};
        }>;
      } | null;
    }>;
  };
  targets: Array<{
    __typename: 'Target';
    pipelineName: string;
    solidSelection: Array<string> | null;
    mode: string;
  }> | null;
  metadata: {
    __typename: 'SensorMetadata';
    assetKeys: Array<{__typename: 'AssetKey'; path: Array<string>}> | null;
  };
  owners: Array<
    | {__typename: 'TeamDefinitionOwner'; team: string}
    | {__typename: 'UserDefinitionOwner'; email: string}
  >;
};
