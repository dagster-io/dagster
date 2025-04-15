import {useEffect, useState} from 'react';
import {AssetNodeFacet, AssetNodeFacetDefaults} from './AssetNodeFacets';
import {Box, Button, Colors, Dialog, DialogFooter, Icon} from '@dagster-io/ui-components';
import {AssetNodeFacetsPicker} from './AssetNodeFacetsPicker';
import {AssetNode2025} from './AssetNode2025';
import {
  AssetNodeFragmentBasic,
  LiveDataForNodeMaterializedAndStaleAndOverdue,
  LiveDataForNodeMaterializedWithChecks,
} from './__fixtures__/AssetNode.fixtures';
import {LiveDataForNodeWithStaleData, tokenForAssetKey} from './Utils';
import {
  AssetCheckExecutionResolvedStatus,
  AssetCheckSeverity,
  buildAssetCheck,
  buildAssetCheckEvaluation,
  buildAssetCheckExecution,
  buildAssetKey,
  buildAssetNode,
  buildMaterializationEvent,
  buildStaleCause,
  StaleCauseCategory,
  StaleStatus,
} from 'shared/graphql/types';
import {AssetBaseData} from 'shared/asset-data/AssetBaseDataProvider';
import {AssetStaleStatusData} from 'shared/asset-data/AssetStaleStatusDataProvider';
import {ASSET_NODE_WIDTH} from './layout';

const ExampleAssetChecks = [
  buildAssetCheck({
    name: 'check_1',
    executionForLatestMaterialization: buildAssetCheckExecution({
      runId: '1234',
      status: AssetCheckExecutionResolvedStatus.SUCCEEDED,
      evaluation: buildAssetCheckEvaluation({
        severity: AssetCheckSeverity.WARN,
      }),
    }),
  }),
  buildAssetCheck({
    name: 'check_2',
    executionForLatestMaterialization: buildAssetCheckExecution({
      runId: '1234',
      status: AssetCheckExecutionResolvedStatus.SUCCEEDED,
      evaluation: buildAssetCheckEvaluation({
        severity: AssetCheckSeverity.WARN,
      }),
    }),
  }),
];

const ExampleAssetNode = {
  ...AssetNodeFragmentBasic,
  assetKey: buildAssetKey({path: ['example_asset']}),
  kinds: ['sql'],
  assetChecks: ExampleAssetChecks,
};

const ExampleLiveData: LiveDataForNodeWithStaleData = {
  stepKey: 'asset9',
  unstartedRunIds: [],
  inProgressRunIds: [],
  lastMaterialization: buildMaterializationEvent({
    runId: 'ABCDEF',
    timestamp: `${Math.floor(Date.now() / 1000 - 5 * 60)}`,
  }),
  lastMaterializationRunStatus: null,
  lastObservation: null,
  runWhichFailedToMaterialize: null,
  staleStatus: StaleStatus.STALE,
  staleCauses: [
    buildStaleCause({
      key: buildAssetKey({path: ['asset1']}),
      reason: 'has a new code version',
      category: StaleCauseCategory.CODE,
      dependency: buildAssetKey({path: ['asset1']}),
    }),
  ],
  freshnessInfo: {
    __typename: 'AssetFreshnessInfo',
    currentMinutesLate: 12,
  },
  partitionStats: null,
  opNames: [],
  assetChecks: ExampleAssetChecks,
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

  useEffect(() => {
    const entry = {[tokenForAssetKey(ExampleAssetNode.assetKey)]: ExampleLiveData};
    const {staleStatus, staleCauses} = ExampleLiveData;
    const staleEntry = {
      [tokenForAssetKey(ExampleAssetNode.assetKey)]: buildAssetNode({
        assetKey: ExampleAssetNode.assetKey,
        staleCauses: staleCauses.map((cause) => buildStaleCause(cause)),
        staleStatus,
      }),
    };
    AssetStaleStatusData.manager._updateCache(staleEntry);
    AssetBaseData.manager._updateCache(entry);
  }, []);

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
              <AssetNode2025 selected={false} facets={edited} definition={ExampleAssetNode} />
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
            intent={'primary'}
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
