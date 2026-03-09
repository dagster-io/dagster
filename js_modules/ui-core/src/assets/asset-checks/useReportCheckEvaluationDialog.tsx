import {
  Body2,
  Box,
  Button,
  Caption,
  Colors,
  Dialog,
  DialogFooter,
  DialogHeader,
  Icon,
  Radio,
  RadioContainer,
  TextInput,
  Tooltip,
} from '@dagster-io/ui-components';
import {useMemo, useState} from 'react';

import {useMutation} from '../../apollo-client';
import {showCustomAlert} from '../../app/CustomAlertProvider';
import {showSharedToaster} from '../../app/DomUtils';
import {DEFAULT_DISABLED_REASON} from '../../app/Permissions';
import {PythonErrorInfo} from '../../app/PythonErrorInfo';
import {AssetCheckSeverity, AssetKeyInput} from '../../graphql/types';
import {RepoAddress} from '../../workspace/types';
import {explodePartitionKeysInSelectionMatching} from '../MultipartitioningSupport';
import {ReportEventsPartitionSection} from '../ReportEventsPartitionSection';
import {REPORT_CHECK_EVALUATION_MUTATION} from '../ReportEventsQueries';
import {
  ReportCheckEvaluationMutation,
  ReportCheckEvaluationMutationVariables,
} from '../types/ReportEventsQueries.types';
import {useReportEventsPartitioning} from '../useReportEventsPartitioning';

type CheckForDialog = {
  name: string;
  assetKey: AssetKeyInput;
  isPartitioned: boolean;
  repoAddress: RepoAddress;
  hasReportRunlessAssetEventPermission: boolean;
};

type EvaluationResult = 'passed' | 'failed_warn' | 'failed_error';

const EVALUATION_RESULT_OPTIONS: {
  value: EvaluationResult;
  label: string;
  icon: React.ReactNode;
}[] = [
  {
    value: 'passed',
    label: 'Passed',
    icon: <Icon name="check_circle" color={Colors.accentGreen()} />,
  },
  {
    value: 'failed_warn',
    label: 'Failed (Warning)',
    icon: <Icon name="error_outline" color={Colors.accentYellow()} />,
  },
  {
    value: 'failed_error',
    label: 'Failed (Error)',
    icon: <Icon name="cancel" color={Colors.accentRed()} />,
  },
];

export function useReportCheckEvaluationDialog(
  check: CheckForDialog | null,
  onEventReported?: () => void,
) {
  const [isOpen, setIsOpen] = useState(false);

  const element = check ? (
    <ReportCheckEvaluationDialog
      check={check}
      isOpen={isOpen}
      setIsOpen={setIsOpen}
      onEventReported={onEventReported}
    />
  ) : undefined;

  return {
    isOpen,
    setIsOpen,
    element,
    hasPermission: check?.hasReportRunlessAssetEventPermission ?? false,
  };
}

const ReportCheckEvaluationDialog = ({
  check,
  isOpen,
  setIsOpen,
  onEventReported,
}: {
  check: CheckForDialog;
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
      <ReportCheckEvaluationDialogBody
        check={check}
        setIsOpen={setIsOpen}
        onEventReported={onEventReported}
      />
    </Dialog>
  );
};

const ReportCheckEvaluationDialogBody = ({
  check,
  setIsOpen,
  onEventReported,
}: {
  check: CheckForDialog;
  setIsOpen: (open: boolean) => void;
  onEventReported?: () => void;
}) => {
  const [evaluationResult, setEvaluationResult] = useState<EvaluationResult>('passed');
  const [description, setDescription] = useState('');
  const [isReporting, setIsReporting] = useState(false);

  const [performReportCheckEvaluation] = useMutation<
    ReportCheckEvaluationMutation,
    ReportCheckEvaluationMutationVariables
  >(REPORT_CHECK_EVALUATION_MUTATION);

  const {assetPartitionDef, assetHealth, selections, setSelections, setLastRefresh} =
    useReportEventsPartitioning(check.assetKey, check.isPartitioned);

  const keysFiltered = useMemo(() => {
    // Include all selected partitions regardless of health status
    return explodePartitionKeysInSelectionMatching(selections, () => true);
  }, [selections]);

  const onReportEvent = async () => {
    setIsReporting(true);

    const passed = evaluationResult === 'passed';
    const severity =
      evaluationResult === 'failed_warn' ? AssetCheckSeverity.WARN : AssetCheckSeverity.ERROR;

    const result = await performReportCheckEvaluation({
      variables: {
        eventParams: {
          assetKey: {path: check.assetKey.path},
          checkName: check.name,
          passed,
          severity: !passed ? severity : undefined,
          partitionKeys: check.isPartitioned ? keysFiltered : undefined,
          description: description || undefined,
        },
      },
    });

    setIsReporting(false);

    const data = result.data?.reportAssetCheckEvaluations;
    if (!data) {
      await showSharedToaster({
        message: <div>An unexpected error occurred. This evaluation was not reported.</div>,
        icon: 'error',
        intent: 'danger',
      });
    } else if (data.__typename === 'PythonError') {
      showCustomAlert({body: <PythonErrorInfo error={data} />});
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
            <div>Your evaluations have been reported.</div>
          ) : (
            <div>Your evaluation has been reported.</div>
          ),
        icon: 'asset_check',
        intent: 'success',
      });
      onEventReported?.();
      setIsOpen(false);
    }
  };

  const tooltipContent = useMemo(() => {
    if (!check.hasReportRunlessAssetEventPermission) {
      return DEFAULT_DISABLED_REASON;
    }
    if (check.isPartitioned && keysFiltered.length === 0) {
      return 'No partitions selected';
    }
    return '';
  }, [check, keysFiltered.length]);

  const submitDisabled =
    !check.hasReportRunlessAssetEventPermission ||
    isReporting ||
    (check.isPartitioned && keysFiltered.length === 0);

  return (
    <>
      <DialogHeader
        icon="info"
        label={check.isPartitioned ? 'Report check evaluations' : 'Report check evaluation'}
      />
      <Box
        padding={{horizontal: 20, top: 16, bottom: 24}}
        border={check.isPartitioned ? {side: 'bottom'} : undefined}
      >
        <Body2>
          Record check evaluations to correct information or test alerts. Manually recorded check
          evaluations are not typically used for normal operations.
        </Body2>
      </Box>

      {check.isPartitioned ? (
        <ReportEventsPartitionSection
          selections={selections}
          setSelections={setSelections}
          assetHealth={assetHealth}
          assetPartitionDef={assetPartitionDef}
          repoAddress={check.repoAddress}
          setLastRefresh={setLastRefresh}
        />
      ) : undefined}

      <Box
        padding={{horizontal: 20, top: check.isPartitioned ? 16 : 0, bottom: 16}}
        flex={{direction: 'column', gap: 12}}
      >
        <Box flex={{direction: 'column', gap: 4}}>
          <Caption>Evaluation result</Caption>
          <RadioContainer>
            {EVALUATION_RESULT_OPTIONS.map((option) => (
              <Radio
                key={option.value}
                checked={evaluationResult === option.value}
                onChange={() => setEvaluationResult(option.value)}
              >
                <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
                  {option.icon}
                  <span>{option.label}</span>
                </Box>
              </Radio>
            ))}
          </RadioContainer>
        </Box>
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
        <Tooltip content={tooltipContent} canShow={submitDisabled && !!tooltipContent}>
          <Button
            intent="primary"
            onClick={onReportEvent}
            disabled={submitDisabled}
            loading={isReporting}
          >
            {keysFiltered.length > 1
              ? `Report ${keysFiltered.length.toLocaleString()} evaluations`
              : 'Report evaluation'}
          </Button>
        </Tooltip>
      </DialogFooter>
    </>
  );
};
