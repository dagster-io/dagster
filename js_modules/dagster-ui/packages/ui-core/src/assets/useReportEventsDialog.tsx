import {
  Body2,
  Box,
  Button,
  Caption,
  Checkbox,
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
import {AssetPartitionStatus} from './AssetPartitionStatus';
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
} from './types/useReportEventsDialog.types';
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
import {testId} from '../testing/testId';
import {ToggleableSection} from '../ui/ToggleableSection';
import {RepoAddress} from '../workspace/types';

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
                ? '报告物化事件'
                : '报告物化事件',
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
    defaultSelection: 'empty',
  });

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
      await showSharedToaster({
        message: <div>发生意外错误。此事件未被报告。</div>,
        icon: 'error',
        intent: 'danger',
        action: data
          ? {
              type: 'button',
              text: '查看错误',
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
            <div>事件已报告。</div>
          ) : (
            <div>事件已报告。</div>
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
        content: '未选择分区',
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
          asset.isPartitioned ? '报告物化事件' : '报告物化事件'
        }
      />
      <Box
        padding={{horizontal: 20, top: 16, bottom: 24}}
        border={asset.isPartitioned ? {side: 'bottom'} : undefined}
      >
        <Body2>
          让 Dagster 知道在 Dagster 外部发生的物化。通常用于测试或手动修复资产目录中的错误信息，
          而非正常操作。
        </Body2>
      </Box>

      {asset.isPartitioned ? (
        <ToggleableSection
          isInitiallyOpen={true}
          title={
            <Box flex={{direction: 'row', justifyContent: 'space-between'}}>
              <Subheading>分区选择</Subheading>
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
          {/* Only show the failed and missing filters for multi-dimensional partitions */}
          {/* because DimensionRangeWizards will set quickSelectButtons to false for multi-dimensional partitions */}
          {/* so this is the only way for the user to filter to failed and missing partitions */}
          {selections.length > 1 && (
            <Box padding={{vertical: 8, horizontal: 20}} flex={{direction: 'column', gap: 8}}>
              <Checkbox
                data-testid={testId('failed-only-checkbox')}
                label="仅报告选择范围内的失败分区"
                checked={filterFailed}
                onChange={() => setFilterFailed(!filterFailed)}
              />
              <Checkbox
                data-testid={testId('missing-only-checkbox')}
                label="仅报告选择范围内的缺失分区"
                checked={filterMissing}
                onChange={() => setFilterMissing(!filterMissing)}
              />
            </Box>
          )}
        </ToggleableSection>
      ) : undefined}

      <Box
        padding={{horizontal: 20, top: asset.isPartitioned ? 16 : 0, bottom: 16}}
        flex={{direction: 'column', gap: 12}}
      >
        <Box flex={{direction: 'column', gap: 4}}>
          <Caption>描述</Caption>
          <TextInput
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="添加描述"
          />
        </Box>
      </Box>
      <DialogFooter topBorder>
        <Button onClick={() => setIsOpen(false)}>取消</Button>
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
              ? `报告 ${keysFiltered.length.toLocaleString()} 个事件`
              : '报告事件'}
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
