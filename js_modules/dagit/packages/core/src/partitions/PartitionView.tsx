import * as React from 'react';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {DISABLED_MESSAGE, usePermissions} from '../app/Permissions';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {OptionsContainer} from '../gantt/VizComponents';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {useQueryPersistedRunFilters} from '../runs/RunsFilter';
import {Box} from '../ui/Box';
import {ButtonWIP} from '../ui/Button';
import {CursorHistoryControls} from '../ui/CursorControls';
import {DialogWIP} from '../ui/Dialog';
import {IconWIP} from '../ui/Icon';
import {Spinner} from '../ui/Spinner';
import {Tooltip} from '../ui/Tooltip';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext';
import {RepoAddress} from '../workspace/types';

import {PartitionGraphSet} from './PartitionGraphSet';
import {PartitionPageSizeSelector} from './PartitionPageSizeSelector';
import {PartitionRunMatrix} from './PartitionRunMatrix';
import {PartitionSetSelector} from './PartitionSetSelector';
import {PartitionsBackfillPartitionSelector} from './PartitionsBackfill';
import {RunTagsSupportedTokens} from './RunTagsTokenizingField';
import {PipelinePartitionsRootQuery_partitionSetsOrError_PartitionSets_results} from './types/PipelinePartitionsRootQuery';
import {useChunkedPartitionsQuery} from './useChunkedPartitionsQuery';

type PartitionSet = PipelinePartitionsRootQuery_partitionSetsOrError_PartitionSets_results;

interface PartitionViewProps {
  pipelineName: string;
  partitionSet: PartitionSet;
  partitionSets: PartitionSet[];
  onChangePartitionSet: (set: PartitionSet) => void;
  repoAddress: RepoAddress;
}

export const PartitionView: React.FC<PartitionViewProps> = ({
  pipelineName,
  partitionSet,
  partitionSets,
  onChangePartitionSet,
  repoAddress,
}) => {
  const [runTags, setRunTags] = useQueryPersistedRunFilters(RunTagsSupportedTokens);
  const [stepQuery = '', setStepQuery] = useQueryPersistedState<string>({queryKey: 'stepQuery'});
  const [showBackfillSetup, setShowBackfillSetup] = React.useState(false);
  const [blockDialog, setBlockDialog] = React.useState(false);
  const repo = useRepository(repoAddress);
  const isJob = isThisThingAJob(repo, pipelineName);
  const {
    loading,
    error,
    loadingPercent,
    partitions,
    paginationProps,
    pageSize,
    setPageSize,
  } = useChunkedPartitionsQuery(
    partitionSet.name,
    runTags,
    repoAddress,
    // only query by job name if there is only one partition set
    isJob && partitionSets.length === 1 ? pipelineName : undefined,
  );
  const {canLaunchPartitionBackfill} = usePermissions();
  const onSubmit = React.useCallback(() => setBlockDialog(true), []);
  React.useEffect(() => {
    if (error) {
      showCustomAlert({
        body: <PythonErrorInfo error={error} />,
      });
    }
  }, [error]);

  const allStepKeys = new Set<string>();
  partitions.forEach((partition) => {
    partition.runs.forEach((run) => {
      run.stepStats.forEach((stat) => {
        allStepKeys.add(stat.stepKey);
      });
    });
  });

  const launchButton = () => {
    if (!canLaunchPartitionBackfill) {
      return (
        <Tooltip content={DISABLED_MESSAGE}>
          <ButtonWIP icon={<IconWIP name="add_circle" />} disabled>
            Launch backfill
          </ButtonWIP>
        </Tooltip>
      );
    }

    return (
      <ButtonWIP
        onClick={() => setShowBackfillSetup(!showBackfillSetup)}
        icon={<IconWIP name="add_circle" />}
        active={showBackfillSetup}
      >
        Launch backfill
      </ButtonWIP>
    );
  };

  return (
    <div>
      <DialogWIP
        canEscapeKeyClose={!blockDialog}
        canOutsideClickClose={!blockDialog}
        onClose={() => setShowBackfillSetup(false)}
        style={{width: 800}}
        title={`Launch ${partitionSet.name} backfill`}
        isOpen={showBackfillSetup}
      >
        {showBackfillSetup && (
          <PartitionsBackfillPartitionSelector
            partitionSetName={partitionSet.name}
            pipelineName={pipelineName}
            onCancel={() => setShowBackfillSetup(false)}
            onLaunch={(backfillId, stepQuery) => {
              setStepQuery(stepQuery);
              setRunTags([{token: 'tag', value: `dagster/backfill=${backfillId}`}]);
              setShowBackfillSetup(false);
            }}
            onSubmit={onSubmit}
            repoAddress={repoAddress}
          />
        )}
      </DialogWIP>
      <OptionsContainer style={{gap: 12}}>
        {partitionSets.length <= 1 ? null : (
          <PartitionSetSelector
            selected={partitionSet}
            partitionSets={partitionSets}
            onSelect={onChangePartitionSet}
          />
        )}
        {launchButton()}
        {loading && (
          <Box flex={{alignItems: 'center'}} style={{overflow: 'hidden'}}>
            <Spinner purpose="body-text" value={loadingPercent} />
            <div style={{width: 5, flexShrink: 0}} />
            <div style={{overflow: 'hidden', textOverflow: 'ellipsis'}}>
              Loading&nbsp;partitions…
            </div>
          </Box>
        )}
        <div style={{flex: 1}} />
        <PartitionPageSizeSelector
          value={paginationProps.hasPrevCursor ? undefined : pageSize}
          onChange={(value) => {
            setPageSize(value);
            paginationProps.reset();
          }}
        />
        <CursorHistoryControls {...paginationProps} />
      </OptionsContainer>
      <div style={{position: 'relative'}}>
        <PartitionRunMatrix
          partitions={partitions}
          pipelineName={pipelineName}
          repoAddress={repoAddress}
          runTags={runTags}
          setRunTags={setRunTags}
          stepQuery={stepQuery}
          setStepQuery={setStepQuery}
        />
        <OptionsContainer>
          <strong>Run steps</strong>
        </OptionsContainer>
        <PartitionGraphSet
          isJob={isJob}
          partitions={partitions}
          allStepKeys={Array.from(allStepKeys).sort()}
        />
      </div>
    </div>
  );
};
