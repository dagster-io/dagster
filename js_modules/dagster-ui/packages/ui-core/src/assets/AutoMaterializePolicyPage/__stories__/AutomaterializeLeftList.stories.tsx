import * as React from 'react';

import {AutomaterializeLeftList} from '../AutomaterializeLeftPanel';
import {
  buildEvaluationRecordsWithPartitions,
  buildEvaluationRecordsWithoutPartitions,
} from '../__fixtures__/AutoMaterializePolicyPage.fixtures';
import {AssetConditionEvaluationRecordFragment} from '../types/GetEvaluationsQuery.types';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Asset Details/Automaterialize/AutomaterializeLeftList',
  component: AutomaterializeLeftList,
};

export const WithPartitions = () => {
  const [selectedEvaluation, setSelectedEvaluation] = React.useState<
    AssetConditionEvaluationRecordFragment | undefined
  >();

  const evaluations = buildEvaluationRecordsWithPartitions();

  return (
    <div style={{width: '320px'}}>
      <AutomaterializeLeftList
        evaluations={evaluations as any}
        onSelectEvaluation={(evaluation: AssetConditionEvaluationRecordFragment) =>
          setSelectedEvaluation(evaluation)
        }
        selectedEvaluation={selectedEvaluation}
      />
    </div>
  );
};

export const NoPartitions = () => {
  const [selectedEvaluation, setSelectedEvaluation] = React.useState<
    AssetConditionEvaluationRecordFragment | undefined
  >();

  const evaluations = buildEvaluationRecordsWithoutPartitions();

  return (
    <div style={{width: '320px'}}>
      <AutomaterializeLeftList
        evaluations={evaluations as any}
        onSelectEvaluation={(evaluation: AssetConditionEvaluationRecordFragment) =>
          setSelectedEvaluation(evaluation)
        }
        selectedEvaluation={selectedEvaluation}
      />
    </div>
  );
};
