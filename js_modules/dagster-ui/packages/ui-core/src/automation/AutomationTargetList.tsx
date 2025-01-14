import {
  Box,
  Button,
  ButtonLink,
  Colors,
  Dialog,
  DialogFooter,
  Mono,
  Subtitle2,
  Tab,
  Tabs,
  Tag,
} from '@dagster-io/ui-components';
import {useEffect, useMemo, useState} from 'react';
import {Link} from 'react-router-dom';

import {
  labelForAssetCheck,
  renderItemAssetCheck,
  renderItemAssetKey,
  sortItemAssetCheck,
  sortItemAssetKey,
} from '../assets/AssetListUtils';
import {VirtualizedItemListForDialog} from '../ui/VirtualizedItemListForDialog';
import {AutomationAssetSelectionFragment} from './types/AutomationAssetSelectionFragment.types';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {displayNameForAssetKey, isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {
  assetDetailsPathForAssetCheck,
  assetDetailsPathForKey,
} from '../assets/assetDetailsPathForKey';
import {SensorType} from '../graphql/types';
import {PipelineReference} from '../pipelines/PipelineReference';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext/util';
import {RepoAddress} from '../workspace/types';

type AutomationType = 'schedule' | SensorType;

export const AutomationTargetList = ({
  assetSelection,
  automationType,
  targets,
  repoAddress,
}: {
  automationType: AutomationType;
  repoAddress: RepoAddress;
  targets: {pipelineName: string}[] | null;
  assetSelection: AutomationAssetSelectionFragment | null;
}) => {
  const repo = useRepository(repoAddress);
  if (!targets && !assetSelection) {
    return <span />;
  }

  const visibleTargets = targets?.filter((target) => !isHiddenAssetGroupJob(target.pipelineName));

  if (assetSelection) {
    return <AssetSelectionTag assetSelection={assetSelection} automationType={automationType} />;
  }

  if (visibleTargets?.length) {
    return (
      <Box flex={{direction: 'row', gap: 4}}>
        {visibleTargets.map((target) =>
          target.pipelineName ? (
            <Tag icon="job" tooltipText={target.pipelineName} key={target.pipelineName}>
              <PipelineReference
                key={target.pipelineName}
                pipelineName={target.pipelineName}
                pipelineHrefContext={repoAddress}
                isJob={!!(repo && isThisThingAJob(repo, target.pipelineName))}
              />
            </Tag>
          ) : null,
        )}
      </Box>
    );
  }

  return (
    <Tag>
      <div style={{color: Colors.textLight()}}>None</div>
    </Tag>
  );
};

const ALL_ASSETS_STRING = 'all materializable assets';

const AssetSelectionTag = ({
  assetSelection,
  automationType,
}: {
  assetSelection: AutomationAssetSelectionFragment;
  automationType: AutomationType;
}) => {
  const [showDialog, setShowDialog] = useState(false);

  const error =
    assetSelection.assetsOrError.__typename === 'PythonError' ? assetSelection.assetsOrError : null;

  const {checks, assets, assetsWithAMP, assetsWithoutAMP} = useMemo(() => {
    if (assetSelection.assetsOrError.__typename === 'PythonError') {
      return {checks: [], assets: [], assetsWithAMP: [], assetsWithoutAMP: []};
    }
    const assets = assetSelection.assetsOrError.nodes;

    return {
      checks: assetSelection.assetChecks.slice().sort(sortItemAssetCheck),
      assets: assets.map((a) => a.key).sort(sortItemAssetKey),
      assetsWithAMP: assets
        .filter((asset) => !!asset.definition?.automationCondition)
        .map((a) => a.key)
        .sort(sortItemAssetKey),
      assetsWithoutAMP: assets
        .filter((asset) => !asset.definition?.automationCondition)
        .map((a) => a.key)
        .sort(sortItemAssetKey),
    };
  }, [assetSelection]);

  const [selectedTab, setSelectedTab] = useState('none');
  const initialTab = checks.length && !assets.length ? 'checks' : 'assets';
  useEffect(() => setSelectedTab(initialTab), [initialTab]);

  const assetSelectionString = assetSelection.assetSelectionString || '';
  const isAllAssets = assetSelectionString === ALL_ASSETS_STRING;

  if (assets.length === 1 && assets[0]) {
    return (
      <Tag icon="asset">
        <Link to={assetDetailsPathForKey(assets[0])}>{displayNameForAssetKey(assets[0])}</Link>
      </Tag>
    );
  }

  if (checks.length === 1 && checks[0]) {
    return (
      <Tag icon="asset_check">
        <Link to={assetDetailsPathForAssetCheck(checks[0])}>{labelForAssetCheck(checks[0])}</Link>
      </Tag>
    );
  }

  const splitConditioned =
    automationType === SensorType.AUTO_MATERIALIZE || automationType === SensorType.AUTOMATION;

  return (
    <>
      <Dialog
        isOpen={showDialog}
        title="Targeted assets"
        onClose={() => setShowDialog(false)}
        style={{width: '750px', maxWidth: '80vw', minWidth: '500px'}}
        canOutsideClickClose
        canEscapeKeyClose
      >
        <Box
          flex={{direction: 'column', gap: 16}}
          padding={{horizontal: 20, vertical: 16}}
          border="bottom"
        >
          <Box flex={{direction: 'column', gap: 4}}>
            <Subtitle2>Asset selection</Subtitle2>
            <Mono>{assetSelectionString}</Mono>
          </Box>
        </Box>

        <Box padding={{horizontal: 20, top: 8}} border="bottom">
          <Tabs size="small" selectedTabId={selectedTab}>
            {splitConditioned ? (
              <Tab
                id="assets"
                title={`Assets with Automation Conditions (${assetsWithAMP.length})`}
                onClick={() => setSelectedTab('assets')}
              />
            ) : (
              <Tab
                id="assets"
                title={`Assets (${assets.length})`}
                onClick={() => setSelectedTab('assets')}
              />
            )}
            {splitConditioned && (
              <Tab
                id="assets-without-conditions"
                disabled={assetsWithoutAMP.length === 0}
                title={`Other Assets (${assetsWithoutAMP.length})`}
                onClick={() => setSelectedTab('assets-without-conditions')}
              />
            )}
            <Tab
              id="checks"
              disabled={checks.length === 0}
              title={`Checks ${checks.length}`}
              onClick={() => setSelectedTab('checks')}
            />
          </Tabs>
        </Box>
        <Box flex={{direction: 'column'}} style={{maxHeight: '60vh', minHeight: '300px'}}>
          {selectedTab === 'checks' ? (
            <VirtualizedItemListForDialog
              items={checks}
              renderItem={renderItemAssetCheck}
              itemBorders
            />
          ) : (
            <VirtualizedItemListForDialog
              items={
                selectedTab === 'assets-without-conditions'
                  ? assetsWithoutAMP
                  : splitConditioned
                    ? assetsWithAMP
                    : assets
              }
              renderItem={renderItemAssetKey}
              itemBorders
            />
          )}
        </Box>
        <DialogFooter topBorder>
          <Button
            intent="primary"
            onClick={() => {
              setShowDialog(false);
            }}
          >
            Close
          </Button>
        </DialogFooter>
      </Dialog>
      <Tag icon={assets.length === 1 ? 'asset' : 'asset_group'} intent={error ? 'danger' : 'none'}>
        <ButtonLink
          onClick={() => {
            if (error) {
              showCustomAlert({
                title: 'Python error',
                body: <PythonErrorInfo error={error} />,
              });
            } else {
              setShowDialog(true);
            }
          }}
          color={error ? Colors.textRed() : Colors.linkDefault()}
        >
          {error
            ? 'Error loading asset selection'
            : isAllAssets
              ? 'All materializable assets'
              : assetSelectionString}
        </ButtonLink>
      </Tag>
    </>
  );
};
