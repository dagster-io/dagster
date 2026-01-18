import {Colors, Table} from '@dagster-io/ui-components';

import {AssetKey} from '../types';
import {EvaluationListRow} from './EvaluationListRow';
import {AssetConditionEvaluationRecordFragment} from './types/GetEvaluationsQuery.types';

interface Props {
  assetKey: AssetKey;
  isPartitioned: boolean;
  assetCheckName?: string;
  evaluations: AssetConditionEvaluationRecordFragment[];
}

export const EvaluationList = ({assetKey, isPartitioned, assetCheckName, evaluations}: Props) => {
  return (
    <Table>
      <thead
        style={{
          position: 'sticky',
          top: 0,
          backgroundColor: Colors.backgroundDefault(),
          zIndex: 1,
          boxShadow: `inset 0 -1px 0 ${Colors.keylineDefault()}`,
        }}
      >
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
              assetCheckName={assetCheckName}
              isPartitioned={isPartitioned}
            />
          );
        })}
      </tbody>
    </Table>
  );
};
