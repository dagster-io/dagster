import {
  Box,
  Button,
  ButtonLink,
  Caption,
  Colors,
  Dialog,
  DialogFooter,
  DisclosureTriangleButton,
  Subtitle2,
  Tag,
} from '@dagster-io/ui-components';
import {useMemo, useState} from 'react';
import {Link} from 'react-router-dom';

import {
  renderItemAssetCheck,
  renderItemAssetKey,
  sortItemAssetCheck,
  sortItemAssetKey,
} from '../assets/AssetListUtils';
import {VirtualizedItemListForDialog} from '../ui/VirtualizedItemListForDialog';
import {AutomationAssetSelectionFragment} from './types/AutomationAssetSelectionFragment.types';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {
  assetDetailsPathForAssetCheck,
  assetDetailsPathForKey,
} from '../assets/assetDetailsPathForKey';
import {SensorType} from '../graphql/types';
import {PipelineReference} from '../pipelines/PipelineReference';
import {numberFormatter} from '../ui/formatters';
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

  const assetSelectionString = assetSelection.assetSelectionString || '';
  const isAllAssets = assetSelectionString === ALL_ASSETS_STRING;

  if (assets.length === 1) {
    return (
      <Tag icon="asset">
        <Link to={assetDetailsPathForKey(assets[0]!)}>{assetSelectionString}</Link>
      </Tag>
    );
  }

  if (checks.length === 1) {
    return (
      <Tag icon="asset_check">
        <Link to={assetDetailsPathForAssetCheck(checks[0]!)}>{assetSelectionString}</Link>
      </Tag>
    );
  }

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
          flex={{direction: 'column'}}
          style={{height: '50vh', maxHeight: '1000px', minHeight: '400px'}}
        >
          {automationType === SensorType.AUTO_MATERIALIZE ||
          automationType === SensorType.AUTOMATION ? (
            <>
              <Section
                title="Assets with a materialization policy"
                titleBorder="bottom"
                count={assetsWithAMP.length}
                list={
                  <VirtualizedItemListForDialog
                    items={assetsWithAMP}
                    renderItem={renderItemAssetKey}
                    itemBorders
                  />
                }
              />
              <Section
                title="Assets without a materialization policy"
                titleBorder="bottom"
                count={assetsWithoutAMP.length}
                list={
                  <VirtualizedItemListForDialog
                    items={assetsWithoutAMP}
                    renderItem={renderItemAssetKey}
                    itemBorders
                  />
                }
              />
            </>
          ) : (
            <Section
              title={checks.length ? 'Assets' : undefined}
              titleBorder="bottom"
              count={assets.length}
              list={
                <VirtualizedItemListForDialog
                  items={assets}
                  renderItem={renderItemAssetKey}
                  itemBorders
                />
              }
            />
          )}
          {checks.length > 0 && (
            <Section
              title="Asset checks"
              titleBorder="bottom"
              count={checks.length}
              list={
                <VirtualizedItemListForDialog
                  items={checks}
                  renderItem={renderItemAssetCheck}
                  itemBorders
                />
              }
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

const Section = ({
  count,
  list,
  title,
  titleBorder = 'top-and-bottom',
}: {
  count: number;
  list: React.ReactNode;
  title?: string;
  titleBorder?: React.ComponentProps<typeof Box>['border'];
}) => {
  const [isOpen, setIsOpen] = useState(true);

  // BG Note: This doesn't use CollapsibleSection because we want to put
  // the sections and their content in the same top-level flexbox to render
  // two sections with two virtualized lists that each scroll.
  return (
    <>
      {title ? (
        <Box
          border={titleBorder}
          padding={{horizontal: 24, vertical: 12}}
          onClick={() => setIsOpen(!isOpen)}
        >
          <Box flex={{direction: 'row', gap: 4}} style={{cursor: 'pointer', userSelect: 'none'}}>
            <Subtitle2>
              {title} ({numberFormatter.format(count)})
            </Subtitle2>
            <DisclosureTriangleButton onToggle={() => {}} isOpen={isOpen} />
          </Box>
        </Box>
      ) : null}
      {isOpen ? (
        count ? (
          <div style={{height: '100%', overflowY: 'hidden'}}>{list}</div>
        ) : (
          <Box padding={{horizontal: 24, vertical: 12}}>
            <Caption color={Colors.textLight()}>0 assets</Caption>
          </Box>
        )
      ) : null}
    </>
  );
};
