import {
  Box,
  Button,
  ButtonLink,
  Colors,
  Dialog,
  DialogFooter,
  DialogHeader,
  Mono,
} from '@dagster-io/ui-components';
import {useState} from 'react';
import {Link} from 'react-router-dom';

import {AssetKey} from '../types';
import {EvaluationDetailDialog} from './EvaluationDetailDialog';
import {EvaluationStatusTag} from './EvaluationStatusTag';
import {AssetConditionEvaluationRecordFragment} from './types/GetEvaluationsQuery.types';
import {DEFAULT_TIME_FORMAT} from '../../app/time/TimestampFormat';
import {RunsFeedTableWithFilters} from '../../runs/RunsFeedTable';
import {TimestampDisplay} from '../../schedules/TimestampDisplay';

interface Props {
  assetKey: AssetKey;
  assetCheckName?: string;
  isPartitioned: boolean;
  evaluation: AssetConditionEvaluationRecordFragment;
}

export const EvaluationListRow = ({evaluation, assetKey, assetCheckName, isPartitioned}: Props) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <tr>
        <td style={{verticalAlign: 'middle'}}>
          <ButtonLink onClick={() => setIsOpen(true)}>
            <TimestampDisplay
              timestamp={evaluation.timestamp}
              timeFormat={{...DEFAULT_TIME_FORMAT, showSeconds: true}}
            />
          </ButtonLink>
        </td>
        <td style={{verticalAlign: 'middle'}}>
          <EvaluationStatusTag
            assetKey={assetKey}
            isPartitioned={isPartitioned}
            selectedEvaluation={evaluation}
            selectPartition={() => {}}
          />
        </td>
        <td style={{verticalAlign: 'middle'}}>
          <EvaluationRunInfo runIds={evaluation.runIds} timestamp={evaluation.timestamp} />
        </td>
      </tr>
      <EvaluationDetailDialog
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        evaluationID={evaluation.evaluationId}
        assetKeyPath={assetKey.path}
        assetCheckName={assetCheckName}
      />
    </>
  );
};

interface EvaluationRunInfoProps {
  runIds: string[];
  timestamp: number;
}

const EvaluationRunInfo = ({runIds, timestamp}: EvaluationRunInfoProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const firstRun = runIds[0];

  if (!firstRun) {
    return <span style={{color: Colors.textDisabled()}}>None</span>;
  }

  if (runIds.length === 1) {
    const truncated = firstRun.slice(0, 8);

    // This looks like a backfill ID. Link there.
    if (truncated === firstRun) {
      return (
        <Link to={`/runs/b/${firstRun}`}>
          <Mono>{firstRun}</Mono>
        </Link>
      );
    }

    return (
      <Link to={`/runs/${firstRun}`}>
        <Mono>{truncated}</Mono>
      </Link>
    );
  }

  return (
    <>
      <ButtonLink onClick={() => setIsOpen(true)}>{runIds.length} runs</ButtonLink>
      <Dialog
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        style={{
          width: '80vw',
          maxWidth: '1400px',
          minWidth: '800px',
          height: '80vh',
          minHeight: '400px',
          maxHeight: '1400px',
        }}
      >
        <Box flex={{direction: 'column'}} style={{height: '100%'}}>
          <DialogHeader
            label={
              <>
                Runs at{' '}
                <TimestampDisplay
                  timestamp={timestamp}
                  timeFormat={{...DEFAULT_TIME_FORMAT, showSeconds: true}}
                />
              </>
            }
          />
          <div style={{flex: 1, overflowY: 'auto'}}>
            <RunsFeedTableWithFilters filter={{runIds}} includeRunsFromBackfills={true} />
          </div>
          <DialogFooter topBorder>
            <Button onClick={() => setIsOpen(false)}>Done</Button>
          </DialogFooter>
        </Box>
      </Dialog>
    </>
  );
};
