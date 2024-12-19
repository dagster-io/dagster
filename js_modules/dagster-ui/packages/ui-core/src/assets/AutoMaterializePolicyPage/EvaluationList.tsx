import {Table} from '@dagster-io/ui-components';

import {AssetKey} from '../types';
import {EvaluationListRow} from './EvaluationListRow';
import {AssetConditionEvaluationRecordFragment} from './types/GetEvaluationsQuery.types';

interface Props {
  assetKey: AssetKey;
  isPartitioned: boolean;
  evaluations: AssetConditionEvaluationRecordFragment[];
}

export const EvaluationList = ({assetKey, isPartitioned, evaluations}: Props) => {
  return (
    <Table>
      <thead>
        <tr>
          <th>Timestamp</th>
          <th style={{width: '240px'}}>Evaluation result</th>
          <th style={{width: '240px'}}>Run(s)</th>
        </tr>
      </thead>
      <tbody>
        {evaluations.map((evaluation) => {
          return (
            <EvaluationListRow
              key={evaluation.id}
              evaluation={evaluation}
              assetKey={assetKey}
              isPartitioned={isPartitioned}
            />
          );
        })}
      </tbody>
    </Table>
  );
};
