import {Box, Button, Colors, Dialog, DialogFooter, Icon} from '@dagster-io/ui-components';
import {useState} from 'react';
import {assetHealthEnabled} from 'shared/app/assetHealthEnabled.oss';

import {AssetNodeWithLiveData} from './AssetNode';
import {AssetNodeFacetDefaults} from './AssetNodeFacets';
import {AssetNodeFacetsPicker} from './AssetNodeFacetsPicker';
import {AssetNodeFacet} from './AssetNodeFacetsUtil';
import {LiveDataForNodeWithStaleData} from './Utils';
import {ASSET_NODE_WIDTH} from './layout';
import {AssetAutomationFragment} from '../asset-data/types/AssetAutomationDataProvider.types';
import {
  AssetCheckCanExecuteIndividually,
  AssetCheckExecutionResolvedStatus,
  AssetCheckSeverity,
  InstigationStatus,
  SensorType,
  StaleCauseCategory,
  StaleStatus,
} from '../graphql/types';
import {AssetNodeFragment} from './types/AssetNode.types';

const ExampleAssetChecks: LiveDataForNodeWithStaleData['assetChecks'] = [
  {
    __typename: 'AssetCheck',
    name: 'check_1',
    canExecuteIndividually: AssetCheckCanExecuteIndividually.CAN_EXECUTE,
    executionForLatestMaterialization: {
      __typename: 'AssetCheckExecution',
      id: '1',
      timestamp: Date.now(),
      stepKey: '',
      runId: '1234',
      status: AssetCheckExecutionResolvedStatus.SUCCEEDED,
      evaluation: {
        __typename: 'AssetCheckEvaluation',
        severity: AssetCheckSeverity.WARN,
      },
    },
    partitionDefinition: null,
    partitionStatuses: null,
  },
  {
    __typename: 'AssetCheck',
    name: 'check_2',
    canExecuteIndividually: AssetCheckCanExecuteIndividually.CAN_EXECUTE,
    executionForLatestMaterialization: {
      __typename: 'AssetCheckExecution',
      id: '1',
      timestamp: Date.now(),
      stepKey: '',
      runId: '1234',
      status: AssetCheckExecutionResolvedStatus.SUCCEEDED,
      evaluation: {
        __typename: 'AssetCheckEvaluation',
        severity: AssetCheckSeverity.WARN,
      },
    },
    partitionDefinition: null,
    partitionStatuses: null,
  },
];

const ExampleAssetNode: AssetNodeFragment = {
  __typename: 'AssetNode',
  assetKey: {__typename: 'AssetKey', path: ['example_asset']},
  computeKind: null,
  description: 'This is a test asset description',
  graphName: null,
  hasMaterializePermission: true,
  isAutoCreatedStub: false,
  id: '["asset1"]',
  isObservable: false,
  isPartitioned: true,
  isMaterializable: true,
  jobNames: ['job1'],
  opNames: ['asset1'],
  opVersion: '1',
  changedReasons: [],
  owners: [
    {
      __typename: 'UserAssetOwner',
      email: 'test@company.com',
    },
  ],

  kinds: ['sql'],
  tags: [],
};

const ExampleLiveData: LiveDataForNodeWithStaleData = {
  stepKey: 'asset9',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterialization: {
    __typename: 'MaterializationEvent',
    runId: 'ABCDEF',
    stepKey: '',
    timestamp: `${Math.floor(Date.now() / 1000 - 5 * 60)}`,
  },
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: null,
  staleStatus: StaleStatus.STALE,
  staleCauses: [
    {
      __typename: 'StaleCause',
      key: {__typename: 'AssetKey', path: ['asset1']},
      reason: 'has a new code version',
      category: StaleCauseCategory.CODE,
      dependency: {__typename: 'AssetKey', path: ['asset1']},
    },
  ],
  freshnessInfo: {
    __typename: 'AssetFreshnessInfo',
    currentMinutesLate: 12,
  },
  partitionStats: {
    numMaterialized: 90,
    numMaterializing: 0,
    numPartitions: 100,
    numFailed: 2,
  },
  opNames: [],
  assetChecks: ExampleAssetChecks,
};

const ExampleAutomationData: AssetAutomationFragment = {
  __typename: 'AssetNode',
  id: '["example_asset"]',
  assetKey: {__typename: 'AssetKey', path: ['example_asset']},
  automationCondition: {
    __typename: 'AutomationCondition',
    label: 'eager',
    expandedLabel: ['eager expanded'],
  },
  lastAutoMaterializationEvaluationRecord: null,
  targetingInstigators: [
    {
      __typename: 'Sensor',
      id: 'sensor1',
      name: 'sensor1',
      sensorType: SensorType.AUTOMATION,
      sensorState: {
        __typename: 'InstigationState',
        id: 'sensorstate',
        selectorId: 'sensor_selector_id',
        status: InstigationStatus.STOPPED,
        typeSpecificData: {__typename: 'SensorData', lastCursor: null},
        hasStartPermission: true,
        hasStopPermission: true,
      },
    },
  ],
};

export const AssetNodeFacetSettingsButton = ({
  value,
  onChange,
}: {
  value: Set<AssetNodeFacet>;
  onChange: (v: Set<AssetNodeFacet>) => void;
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [edited, setEdited] = useState<Set<AssetNodeFacet>>(new Set());

  return (
    <>
      <Dialog
        isOpen={isOpen}
        title="Choose Asset Facets"
        onClose={() => setIsOpen(false)}
        style={{width: '700px'}}
      >
        <Box flex={{gap: 16}}>
          <Box style={{flex: 1}} padding={{horizontal: 24, vertical: 12}}>
            <AssetNodeFacetsPicker value={edited} onChange={setEdited} />
          </Box>
          <Box
            padding={{vertical: 8}}
            flex={{alignItems: 'center', justifyContent: 'center'}}
            style={{width: 380, height: 280, background: Colors.backgroundLight()}}
          >
            <div style={{width: ASSET_NODE_WIDTH}}>
              <AssetNodeWithLiveData
                selected={false}
                facets={edited}
                definition={ExampleAssetNode}
                liveData={ExampleLiveData}
                automationData={ExampleAutomationData}
                assetHealthEnabled={assetHealthEnabled()}
              />
            </div>
          </Box>
        </Box>
        <DialogFooter
          topBorder
          left={
            <Button onClick={() => setEdited(new Set(AssetNodeFacetDefaults))}>
              Reset to default
            </Button>
          }
        >
          <div style={{flex: 1}} />
          <Button onClick={() => setIsOpen(false)}>Cancel</Button>
          <Button
            intent="primary"
            onClick={() => {
              onChange(edited);
              setIsOpen(false);
            }}
          >
            Save
          </Button>
        </DialogFooter>
      </Dialog>
      <Button
        icon={<Icon name="config" />}
        onClick={() => {
          setEdited(value);
          setIsOpen(true);
        }}
      />
    </>
  );
};
