import {
  Body2,
  Box,
  Button,
  Caption,
  Dialog,
  DialogFooter,
  DialogHeader,
  Icon,
  Subheading,
  TextInput,
  Tooltip,
} from '@dagster-io/ui-components';
import {useMemo, useState} from 'react';

import {partitionCountString} from './AssetNodePartitionCounts';
import {
  explodePartitionKeysInSelectionMatching,
  mergedAssetHealth,
} from './MultipartitioningSupport';
import {asAssetKeyInput} from './asInput';
import {
  ReportEventMutation,
  ReportEventMutationVariables,
  ReportEventPartitionDefinitionQuery,
  ReportEventPartitionDefinitionQueryVariables,
} from './types/useReportEventsModal.types';
import {usePartitionDimensionSelections} from './usePartitionDimensionSelections';
import {keyCountInSelections, usePartitionHealthData} from './usePartitionHealthData';
import {gql, useMutation, useQuery} from '../apollo-client';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {showSharedToaster} from '../app/DomUtils';
import {DEFAULT_DISABLED_REASON} from '../app/Permissions';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {AssetEventType, AssetKeyInput, PartitionDefinitionType} from '../graphql/types';
import {DimensionRangeWizards} from '../partitions/DimensionRangeWizards';
import {ToggleableSection} from '../ui/ToggleableSection';
import {RepoAddress} from '../workspace/types';

type Asset = {
  isPartitioned: boolean;
  assetKey: AssetKeyInput;
  repoAddress: RepoAddress;
  hasReportRunlessAssetEventPermission: boolean;
};

export function useReportEventsModal(asset: Asset | null, onEventReported?: () => void) {
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

  const assetPartitionDefResult = useQuery<
    ReportEventPartitionDefinitionQuery,
    ReportEventPartitionDefinitionQueryVariables
  >(REPORT_EVENT_PARTITION_DEFINITION_QUERY, {
    variables: {
      assetKey: asAssetKeyInput(asset.assetKey),
    },
  });

  const assetPartitionDef =
    assetPartitionDefResult.data?.assetNodeOrError.__typename === 'AssetNode'
      ? assetPartitionDefResult.data?.assetNodeOrError.partitionDefinition
      : null;

  const [mutation] = useMutation<ReportEventMutation, ReportEventMutationVariables>(
    REPORT_EVENT_MUTATION,
  );

  const [lastRefresh, setLastRefresh] = useState(Date.now());
  const assetHealth = mergedAssetHealth(
    usePartitionHealthData(
      asset.isPartitioned ? [asset.assetKey] : [],
      lastRefresh.toString(),
      'background',
    ),
  );
  const isDynamic = assetHealth.dimensions.some((d) => d.type === PartitionDefinitionType.DYNAMIC);
  const [selections, setSelections] = usePartitionDimensionSelections({
    assetHealth,
    modifyQueryString: false,
    skipPartitionKeyValidation: isDynamic,
    shouldReadPartitionQueryStringParam: true,
  });

  const keysFiltered = useMemo(() => {
    return explodePartitionKeysInSelectionMatching(selections, () => true);
  }, [selections]);

  const onReportEvent = async () => {
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
    const data = result.data?.reportRunlessAssetEvents;

    if (!data || data.__typename === 'PythonError') {
      await showSharedToaster({
        message: <div>An unexpected error occurred. This event was not reported.</div>,
        icon: 'error',
        intent: 'danger',
        action: data
          ? {
              text: 'View error',
              onClick: () => showCustomAlert({body: <PythonErrorInfo error={data} />}),
            }
          : undefined,
      });
    } else if (data.__typename === 'UnauthorizedError') {
      await showSharedToaster({
        message: <div>{data.message}</div>,
        icon: 'error',
        intent: 'danger',
      });
    } else {
      await showSharedToaster({
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
        <ToggleableSection
          isInitiallyOpen={true}
          title={
            <Box flex={{direction: 'row', justifyContent: 'space-between'}}>
              <Subheading>Partition selection</Subheading>
              <span>{partitionCountString(keyCountInSelections(selections))}</span>
            </Box>
          }
        >
          <DimensionRangeWizards
            repoAddress={repoAddress}
            refetch={async () => setLastRefresh(Date.now())}
            selections={selections}
            setSelections={setSelections}
            displayedHealth={assetHealth}
            displayedPartitionDefinition={assetPartitionDef}
          />
        </ToggleableSection>
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
        <Tooltip
          content={DEFAULT_DISABLED_REASON}
          canShow={!asset.hasReportRunlessAssetEventPermission}
        >
          <Button
            intent="primary"
            onClick={onReportEvent}
            disabled={!asset.hasReportRunlessAssetEventPermission}
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

const REPORT_EVENT_PARTITION_DEFINITION_QUERY = gql`
  query ReportEventPartitionDefinitionQuery($assetKey: AssetKeyInput!) {
    assetNodeOrError(assetKey: $assetKey) {
      __typename
      ... on AssetNode {
        id
        partitionDefinition {
          type
          name
          dimensionTypes {
            type
            name
            dynamicPartitionsDefinitionName
          }
        }
      }
    }
  }
`;

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
