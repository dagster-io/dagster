import {QueryResult} from '@apollo/client';
import {
  Box,
  Button,
  ButtonLink,
  Colors,
  Dialog,
  DialogFooter,
  Icon,
  MiddleTruncate,
  Subtitle2,
  ToggleButton,
} from '@dagster-io/ui-components';
import React from 'react';
import {Link} from 'react-router-dom';

import {
  SensorAssetSelectionFragment,
  SensorAssetSelectionQuery,
  SensorAssetSelectionQueryVariables,
} from './types/SensorRoot.types';
import {COMMON_COLLATOR} from '../app/Util';
import {displayNameForAssetKey, isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';
import {PipelineReference} from '../pipelines/PipelineReference';
import {VirtualizedItemListForDialog} from '../ui/VirtualizedItemListForDialog';
import {numberFormatter} from '../ui/formatters';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext';
import {RepoAddress} from '../workspace/types';

export const SensorTargetList = ({
  targets,
  selectionQueryResult,
  repoAddress,
}: {
  targets: {pipelineName: string}[] | null | undefined;
  repoAddress: RepoAddress;
  selectionQueryResult: QueryResult<SensorAssetSelectionQuery, SensorAssetSelectionQueryVariables>;
}) => {
  const repo = useRepository(repoAddress);
  const assetSelectionResult = selectionQueryResult.data?.sensorOrError;
  const assetSelectionData =
    assetSelectionResult?.__typename === 'Sensor' ? assetSelectionResult : null;

  if (!targets && !assetSelectionData) {
    return <span />;
  }

  const selectedAssets = assetSelectionData?.assetSelection;

  const visibleTargets = targets?.filter((target) => !isHiddenAssetGroupJob(target.pipelineName));

  return (
    <Box flex={{direction: 'column', gap: 2}}>
      {selectedAssets && <AssetSelectionLink assetSelection={selectedAssets} />}
      {visibleTargets?.map((target) =>
        target.pipelineName ? (
          <PipelineReference
            key={target.pipelineName}
            pipelineName={target.pipelineName}
            pipelineHrefContext={repoAddress}
            isJob={!!(repo && isThisThingAJob(repo, target.pipelineName))}
          />
        ) : null,
      )}
    </Box>
  );
};

const AssetSelectionLink = ({assetSelection}: {assetSelection: SensorAssetSelectionFragment}) => {
  const [showAssetSelection, setShowAssetSelection] = React.useState(false);

  const sortedAssets = React.useMemo(() => {
    return assetSelection.assets
      .slice()
      .sort((a, b) =>
        COMMON_COLLATOR.compare(displayNameForAssetKey(a.key), displayNameForAssetKey(b.key)),
      );
  }, [assetSelection.assets]);

  const assetsWithAMP = React.useMemo(
    () => sortedAssets.filter((asset) => !!asset.definition?.autoMaterializePolicy),
    [sortedAssets],
  );
  const assetsWithoutAMP = React.useMemo(
    () => sortedAssets.filter((asset) => !asset.definition?.autoMaterializePolicy),
    [sortedAssets],
  );

  return (
    <>
      <Dialog
        isOpen={showAssetSelection}
        title="Targeted assets"
        onClose={() => setShowAssetSelection(false)}
        style={{width: '750px', maxWidth: '80vw', minWidth: '500px', transform: 'scale(1)'}}
        canOutsideClickClose
        canEscapeKeyClose
      >
        <Box flex={{direction: 'column'}}>
          {assetsWithAMP.length ? (
            <Section
              title="Assets with a materialization policy"
              titleBorder="bottom"
              assets={assetsWithAMP}
            />
          ) : null}
          {assetsWithoutAMP.length ? (
            <Section
              title="Assets without a materialization policy"
              titleBorder="top-and-bottom"
              assets={assetsWithoutAMP}
            />
          ) : null}
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
      <ButtonLink
        onClick={() => {
          setShowAssetSelection(true);
        }}
      >
        {assetSelection.assetSelectionString}
      </ButtonLink>
    </>
  );
};

const Section = ({
  assets,
  title,
  titleBorder = 'top-and-bottom',
}: {
  assets: SensorAssetSelectionFragment['assets'];
  title: string;
  titleBorder: React.ComponentProps<typeof Box>['border'];
}) => {
  const [isOpen, setIsOpen] = React.useState(true);
  return (
    <>
      <Box border={titleBorder} padding={{right: 24, vertical: 12}}>
        <Box
          flex={{direction: 'row', gap: 4}}
          style={{cursor: 'pointer'}}
          onClick={() => {
            setIsOpen(!isOpen);
          }}
        >
          <ToggleButton onToggle={() => {}} isOpen={isOpen} />
          <Subtitle2>
            {title} ({numberFormatter.format(assets.length)})
          </Subtitle2>
        </Box>
      </Box>
      {isOpen ? (
        <div style={{maxHeight: '300px', overflowY: 'scroll'}}>
          <VirtualizedItemListForDialog
            padding={0}
            items={assets}
            renderItem={(asset) => <VirtualizedSelectedAssetRow asset={asset} key={asset.id} />}
            itemBorders
          />
        </div>
      ) : null}
    </>
  );
};

const VirtualizedSelectedAssetRow = ({
  asset,
}: {
  asset: SensorAssetSelectionFragment['assets'][0];
}) => {
  return (
    <Box
      flex={{alignItems: 'center', gap: 4}}
      style={{cursor: 'pointer'}}
      padding={{horizontal: 24}}
    >
      <Box style={{overflow: 'hidden'}}>
        <MiddleTruncate text={displayNameForAssetKey(asset.key)} />
      </Box>
      <Link to={assetDetailsPathForKey(asset.key)} target="_blank">
        <Icon name="open_in_new" color={Colors.linkDefault()} />
      </Link>
    </Box>
  );
};
