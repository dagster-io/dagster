import {
  Body2,
  Box,
  Button,
  Caption,
  Dialog,
  DialogFooter,
  DialogHeader,
  Icon,
  TextInput,
  Tooltip,
  showToast,
} from '@dagster-io/ui-components';
import {useMemo, useState} from 'react';

import {gql, useMutation} from '../apollo-client';
import {AssetPartitionStatus} from './AssetPartitionStatus';
import {explodePartitionKeysInSelectionMatching} from './MultipartitioningSupport';
import {ReportEventsPartitionSection} from './ReportEventsPartitionSection';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {DEFAULT_DISABLED_REASON} from '../app/Permissions';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {AssetEventType, AssetKeyInput} from '../graphql/types';
import {RepoAddress} from '../workspace/types';
import {
  ReportEventMutation,
  ReportEventMutationVariables,
} from './types/useReportEventsDialog.types';
import {useReportEventsPartitioning} from './useReportEventsPartitioning';

type Asset = {
  isPartitioned: boolean;
  assetKey: AssetKeyInput;
  repoAddress: RepoAddress;
  hasReportRunlessAssetEventPermission: boolean;
};

export function useReportEventsDialog(asset: Asset | null, onEventReported?: () => void) {
  const [isOpen, setIsOpen] = useState(false);
  const hasReportRunlessAssetEventPermission = asset?.hasReportRunlessAssetEventPermission;

  const dropdownOptions = useMemo(
    () =>
      asset
        ? [
            {
              label: asset.isPartitioned
                ? 'Report materialization events'
                : 'Report materialization event',
              icon: <Icon name="asset_non_sda" />,
              disabled: !hasReportRunlessAssetEventPermission,
              onClick: () => setIsOpen(true),
            },
          ]
        : [],
    [asset, hasReportRunlessAssetEventPermission],
  );

  const element = asset ? (
    <ReportEventsDialog
      asset={asset}
      isOpen={isOpen}
      setIsOpen={setIsOpen}
      repoAddress={asset.repoAddress}
      onEventReported={onEventReported}
    />
  ) : undefined;

  return {
    dropdownOptions,
    element,
  };
}

const ReportEventsDialog = ({
  asset,
  repoAddress,
  isOpen,
  setIsOpen,
  onEventReported,
}: {
  asset: Asset;
  repoAddress: RepoAddress;
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
  onEventReported?: () => void;
}) => {
  return (
    <Dialog
      style={{width: 700}}
      isOpen={isOpen}
      canEscapeKeyClose
      canOutsideClickClose
      onClose={() => setIsOpen(false)}
    >
      <ReportEventDialogBody
        asset={asset}
        setIsOpen={setIsOpen}
        repoAddress={repoAddress}
        onEventReported={onEventReported}
      />
    </Dialog>
  );
};

const ReportEventDialogBody = ({
  asset,
  repoAddress,
  setIsOpen,
  onEventReported,
}: {
  asset: Asset;
  repoAddress: RepoAddress;
  setIsOpen: (open: boolean) => void;
  onEventReported?: () => void;
}) => {
  const [description, setDescription] = useState('');

  const [mutation] = useMutation<ReportEventMutation, ReportEventMutationVariables>(
    REPORT_EVENT_MUTATION,
  );

  const {assetPartitionDef, assetHealth, selections, setSelections, setLastRefresh} =
    useReportEventsPartitioning(asset.assetKey, asset.isPartitioned);

  const [filterFailed, setFilterFailed] = useState(true);
  const [filterMissing, setFilterMissing] = useState(true);
  const keysFiltered = useMemo(() => {
    return explodePartitionKeysInSelectionMatching(selections, (keyIdx) => {
      if (selections.length <= 1 || (!filterFailed && !filterMissing)) {
        return true;
      }

      const state = assetHealth.stateForKeyIdx(keyIdx);
      if (filterFailed && state.includes(AssetPartitionStatus.FAILED)) {
        return true;
      }
      if (filterMissing && state.includes(AssetPartitionStatus.MISSING)) {
        return true;
      }
      return false;
    });
  }, [selections, assetHealth, filterFailed, filterMissing]);

  const [isReporting, setIsReporting] = useState(false);

  const onReportEvent = async () => {
    setIsReporting(true);
    const result = await mutation({
      variables: {
        eventParams: {
          eventType: AssetEventType.ASSET_MATERIALIZATION,
          partitionKeys: asset.isPartitioned ? keysFiltered : undefined,
          assetKey: {path: asset.assetKey.path},
          description,
        },
      },
    });
    setIsReporting(false);
    const data = result.data?.reportRunlessAssetEvents;

    if (!data || data.__typename === 'PythonError') {
      showToast({
        message: <div>An unexpected error occurred. This event was not reported.</div>,
        icon: 'error',
        intent: 'danger',
        action: data
          ? {
              type: 'button',
              text: 'View error',
              onClick: () => showCustomAlert({body: <PythonErrorInfo error={data} />}),
            }
          : undefined,
      });
    } else if (data.__typename === 'UnauthorizedError') {
      showToast({
        message: <div>{data.message}</div>,
        icon: 'error',
        intent: 'danger',
      });
    } else {
      showToast({
        message:
          keysFiltered.length > 1 ? (
            <div>Your events have been reported.</div>
          ) : (
            <div>Your event has been reported.</div>
          ),
        icon: 'materialization',
        intent: 'success',
      });
      onEventReported?.();
      setIsOpen(false);
    }
  };

  const tooltipState = useMemo(() => {
    if (!asset.hasReportRunlessAssetEventPermission) {
      return {
        content: DEFAULT_DISABLED_REASON,
        canShow: true,
      };
    }
    if (asset.isPartitioned && keysFiltered.length === 0) {
      return {
        content: 'No partitions selected',
        canShow: true,
      };
    }
    return {content: '', canShow: false};
  }, [asset, keysFiltered.length]);

  return (
    <>
      <DialogHeader
        icon="info"
        label={
          asset.isPartitioned ? 'Report materialization events' : 'Report materialization event'
        }
      />
      <Box
        padding={{horizontal: 20, top: 16, bottom: 24}}
        border={asset.isPartitioned ? {side: 'bottom'} : undefined}
      >
        <Body2>
          Let Dagster know about a materialization that happened outside of Dagster. Typically used
          for testing or for manually fixing incorrect information in the asset catalog, not for
          normal operations.
        </Body2>
      </Box>

      {asset.isPartitioned ? (
        <ReportEventsPartitionSection
          selections={selections}
          setSelections={setSelections}
          assetHealth={assetHealth}
          assetPartitionDef={assetPartitionDef}
          repoAddress={repoAddress}
          setLastRefresh={setLastRefresh}
          healthFilters={{filterFailed, setFilterFailed, filterMissing, setFilterMissing}}
        />
      ) : undefined}

      <Box
        padding={{horizontal: 20, top: asset.isPartitioned ? 16 : 0, bottom: 16}}
        flex={{direction: 'column', gap: 12}}
      >
        <Box flex={{direction: 'column', gap: 4}}>
          <Caption>Description</Caption>
          <TextInput
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Add a description"
          />
        </Box>
      </Box>
      <DialogFooter topBorder>
        <Button onClick={() => setIsOpen(false)}>Cancel</Button>
        <Tooltip content={tooltipState.content} canShow={tooltipState.canShow}>
          <Button
            intent="primary"
            onClick={onReportEvent}
            disabled={
              !asset.hasReportRunlessAssetEventPermission ||
              isReporting ||
              (asset.isPartitioned && keysFiltered.length === 0)
            }
            loading={isReporting}
          >
            {keysFiltered.length > 1
              ? `Report ${keysFiltered.length.toLocaleString()} events`
              : 'Report event'}
          </Button>
        </Tooltip>
      </DialogFooter>
    </>
  );
};

const REPORT_EVENT_MUTATION = gql`
  mutation ReportEventMutation($eventParams: ReportRunlessAssetEventsParams!) {
    reportRunlessAssetEvents(eventParams: $eventParams) {
      ...PythonErrorFragment
      ... on UnauthorizedError {
        message
      }
      ... on ReportRunlessAssetEventsSuccess {
        assetKey {
          path
        }
      }
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
`;
