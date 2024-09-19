import {
  Box,
  Button,
  ButtonLink,
  Caption,
  Colors,
  Dialog,
  DialogFooter,
  DisclosureTriangleButton,
  MiddleTruncate,
  Subtitle2,
  Tag,
} from '@dagster-io/ui-components';
import {useMemo, useState} from 'react';
import {Link} from 'react-router-dom';

import {
  AssetSelectionNodeFragment,
  AutomationAssetSelectionFragment,
} from './types/AutomationAssetSelectionFragment.types';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {COMMON_COLLATOR} from '../app/Util';
import {displayNameForAssetKey, isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';
import {SensorType} from '../graphql/types';
import {PipelineReference} from '../pipelines/PipelineReference';
import {VirtualizedItemListForDialog} from '../ui/VirtualizedItemListForDialog';
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
  const [showAssetSelection, setShowAssetSelection] = useState(false);

  const error =
    assetSelection.assetsOrError.__typename === 'PythonError' ? assetSelection.assetsOrError : null;

  const sortedAssets = useMemo(() => {
    if (assetSelection.assetsOrError.__typename === 'PythonError') {
      return [];
    }
    return assetSelection.assetsOrError.nodes
      .slice()
      .sort((a, b) =>
        COMMON_COLLATOR.compare(displayNameForAssetKey(a.key), displayNameForAssetKey(b.key)),
      );
  }, [assetSelection.assetsOrError]);

  const assetsWithAMP = useMemo(
    () => sortedAssets.filter((asset) => !!asset.definition?.autoMaterializePolicy),
    [sortedAssets],
  );
  const assetsWithoutAMP = useMemo(
    () => sortedAssets.filter((asset) => !asset.definition?.autoMaterializePolicy),
    [sortedAssets],
  );

  const assetSelectionString = assetSelection.assetSelectionString || '';
  const isAllAssets = assetSelectionString === ALL_ASSETS_STRING;
  const firstAsset = sortedAssets[0];

  if (firstAsset && sortedAssets.length === 1) {
    return (
      <Tag icon="asset">
        <Link to={assetDetailsPathForKey(firstAsset.key)}>{assetSelectionString}</Link>
      </Tag>
    );
  }

  return (
    <>
      <Dialog
        isOpen={showAssetSelection}
        title="Targeted assets"
        onClose={() => setShowAssetSelection(false)}
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
                assets={assetsWithAMP}
              />
              <Section
                title="Assets without a materialization policy"
                titleBorder="top-and-bottom"
                assets={assetsWithoutAMP}
              />
            </>
          ) : (
            <Section assets={sortedAssets} />
          )}
        </Box>
        <DialogFooter topBorder>
          <Button
            intent="primary"
            onClick={() => {
              setShowAssetSelection(false);
            }}
          >
            Close
          </Button>
        </DialogFooter>
      </Dialog>
      <Tag
        icon={sortedAssets.length === 1 ? 'asset' : 'asset_group'}
        intent={error ? 'danger' : 'none'}
      >
        <ButtonLink
          onClick={() => {
            if (error) {
              showCustomAlert({
                title: 'Python error',
                body: <PythonErrorInfo error={error} />,
              });
            } else {
              setShowAssetSelection(true);
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
  assets,
  title,
  titleBorder = 'top-and-bottom',
}: {
  assets: AssetSelectionNodeFragment[];
  title?: string;
  titleBorder?: React.ComponentProps<typeof Box>['border'];
}) => {
  const [isOpen, setIsOpen] = useState(true);
  return (
    <>
      {title ? (
        <Box border={titleBorder} padding={{right: 24, vertical: 12}}>
          <Box
            flex={{direction: 'row', gap: 4}}
            style={{cursor: 'pointer'}}
            onClick={() => {
              setIsOpen(!isOpen);
            }}
          >
            <DisclosureTriangleButton onToggle={() => {}} isOpen={isOpen} />
            <Subtitle2>
              {title} ({numberFormatter.format(assets.length)})
            </Subtitle2>
          </Box>
        </Box>
      ) : null}
      {isOpen ? (
        assets.length ? (
          <div style={{height: '100%', overflowY: 'hidden'}}>
            <VirtualizedItemListForDialog
              padding={0}
              items={assets}
              renderItem={(asset) => <VirtualizedSelectedAssetRow asset={asset} key={asset.id} />}
              itemBorders
            />
          </div>
        ) : (
          <Box padding={{horizontal: 24, vertical: 12}}>
            <Caption color={Colors.textLight()}>0 assets</Caption>
          </Box>
        )
      ) : null}
    </>
  );
};

const VirtualizedSelectedAssetRow = ({asset}: {asset: AssetSelectionNodeFragment}) => {
  return (
    <Box
      flex={{alignItems: 'center', gap: 4}}
      style={{cursor: 'pointer'}}
      padding={{horizontal: 24}}
    >
      <Link to={assetDetailsPathForKey(asset.key)} target="_blank">
        <Box style={{overflow: 'hidden'}}>
          <MiddleTruncate text={displayNameForAssetKey(asset.key)} />
        </Box>
      </Link>
    </Box>
  );
};
