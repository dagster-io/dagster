import {ButtonLink, Colors} from '@dagster-io/ui-components';
import {useState} from 'react';

import {AssetKey} from '../types';
import {EvaluationDetailDialog, Tab} from './EvaluationDetailDialog';
import {EvaluationStatusTag} from './EvaluationStatusTag';
import {AssetConditionEvaluationRecordFragment} from './types/GetEvaluationsQuery.types';
import {DEFAULT_TIME_FORMAT} from '../../app/time/TimestampFormat';
import {TimestampDisplay} from '../../schedules/TimestampDisplay';

interface Props {
  assetKey: AssetKey;
  assetCheckName?: string;
  isPartitioned: boolean;
  evaluation: AssetConditionEvaluationRecordFragment;
}

export const EvaluationListRow = ({evaluation, assetKey, assetCheckName, isPartitioned}: Props) => {
  const [isOpen, setIsOpen] = useState(false);
  const [tab, setTab] = useState<Tab>('evaluation');

  return (
    <>
      <tr>
        <td style={{verticalAlign: 'middle'}}>
          <ButtonLink
            onClick={() => {
              setTab('evaluation');
              setIsOpen(true);
            }}
          >
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
          {evaluation.runIds.length > 0 ? (
            <ButtonLink
              onClick={() => {
                setTab('runs');
                setIsOpen(true);
              }}
            >
              {evaluation.runIds.length > 1 ? `${evaluation.runIds.length} runs` : '1 run'}
            </ButtonLink>
          ) : (
            <span style={{color: Colors.textDisabled()}}>None</span>
          )}
        </td>
      </tr>
      <EvaluationDetailDialog
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        evaluationID={evaluation.evaluationId}
        assetKeyPath={assetKey.path}
        assetCheckName={assetCheckName}
        initialTab={tab}
      />
    </>
  );
};
