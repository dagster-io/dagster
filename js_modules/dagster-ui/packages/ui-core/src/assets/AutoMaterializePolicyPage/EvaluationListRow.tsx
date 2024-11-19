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

import {EvaluationStatusTag} from './EvaluationStatusTag';
import {PolicyEvaluationTable} from './PolicyEvaluationTable';
import {AssetConditionEvaluationRecordFragment} from './types/GetEvaluationsQuery.types';
import {DEFAULT_TIME_FORMAT} from '../../app/time/TimestampFormat';
import {RunsFeedTableWithFilters} from '../../runs/RunsFeedTable';
import {TimestampDisplay} from '../../schedules/TimestampDisplay';
import {AssetViewDefinitionNodeFragment} from '../types/AssetView.types';

interface Props {
  definition: AssetViewDefinitionNodeFragment;
  evaluation: AssetConditionEvaluationRecordFragment;
}

export const EvaluationListRow = ({evaluation, definition}: Props) => {
  const [isOpen, setIsOpen] = useState(false);
  // const [selectedPartition, setSelectedPartition] = useState<string | null>(null);

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
            definition={definition}
            selectedEvaluation={evaluation}
            selectPartition={() => {}}
          />
        </td>
        <td style={{verticalAlign: 'middle'}}>
          <EvaluationRunInfo evaluation={evaluation} />
        </td>
      </tr>
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
            icon="automation"
            label={
              <div>
                Evaluation details:{' '}
                <TimestampDisplay
                  timestamp={evaluation.timestamp}
                  timeFormat={{...DEFAULT_TIME_FORMAT, showSeconds: true}}
                />
              </div>
            }
          />
          <div style={{flex: 1, overflowY: 'auto'}}>
            <PolicyEvaluationTable
              assetKeyPath={definition?.assetKey.path ?? null}
              evaluationId={evaluation.evaluationId}
              evaluationNodes={
                !evaluation.isLegacy
                  ? evaluation.evaluationNodes
                  : // : selectedPartition && specificPartitionData?.assetConditionEvaluationForPartition
                    //   ? specificPartitionData.assetConditionEvaluationForPartition.evaluationNodes
                    evaluation.evaluation.evaluationNodes
              }
              isLegacyEvaluation={evaluation.isLegacy}
              rootUniqueId={evaluation.evaluation.rootUniqueId}
              // todo dish
              selectPartition={() => {}}
            />
          </div>
          <div style={{flexGrow: 0}}>
            <DialogFooter topBorder>
              <Button onClick={() => setIsOpen(false)}>Done</Button>
            </DialogFooter>
          </div>
        </Box>
      </Dialog>
    </>
  );
};

const EvaluationRunInfo = ({evaluation}: {evaluation: AssetConditionEvaluationRecordFragment}) => {
  const {runIds} = evaluation;
  const [isOpen, setIsOpen] = useState(false);

  if (runIds.length === 0) {
    return <span style={{color: Colors.textDisabled()}}>None</span>;
  }

  if (runIds.length === 1) {
    return (
      <Box flex={{direction: 'row', gap: 4}}>
        <Mono>{runIds[0]}</Mono>
      </Box>
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
                  timestamp={evaluation.timestamp}
                  timeFormat={{...DEFAULT_TIME_FORMAT, showSeconds: true}}
                />
              </>
            }
          />
          <div style={{flex: 1, overflowY: 'auto'}}>
            <RunsFeedTableWithFilters filter={{runIds}} />
          </div>
          <DialogFooter topBorder>
            <Button onClick={() => setIsOpen(false)}>Done</Button>
          </DialogFooter>
        </Box>
      </Dialog>
    </>
  );
};
