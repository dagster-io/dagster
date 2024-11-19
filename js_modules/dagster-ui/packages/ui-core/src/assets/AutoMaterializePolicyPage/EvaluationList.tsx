import {Table} from '@dagster-io/ui-components';

import {EvaluationListRow} from './EvaluationListRow';
import {AssetViewDefinitionNodeFragment} from '../types/AssetView.types';
import {AssetConditionEvaluationRecordFragment} from './types/GetEvaluationsQuery.types';

interface Props {
  definition: AssetViewDefinitionNodeFragment;
  evaluations: AssetConditionEvaluationRecordFragment[];
}

export const EvaluationList = ({definition, evaluations}: Props) => {
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
              definition={definition}
            />
          );
        })}
      </tbody>
    </Table>
  );
};
