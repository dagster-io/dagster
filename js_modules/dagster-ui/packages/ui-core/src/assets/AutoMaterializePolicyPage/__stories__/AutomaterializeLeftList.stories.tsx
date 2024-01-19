import {useState} from 'react';

import {AutomaterializeLeftList} from '../AutomaterializeLeftPanel';
import {
  buildEvaluationRecordsWithPartitions,
  buildEvaluationRecordsWithoutPartitions,
} from '../__fixtures__/AutoMaterializePolicyPage.fixtures';
import {AutoMaterializeEvaluationRecordItemFragment} from '../types/GetEvaluationsQuery.types';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Asset Details/Automaterialize/AutomaterializeLeftList',
  component: AutomaterializeLeftList,
};

export const WithPartitions = () => {
  const [selectedEvaluation, setSelectedEvaluation] = useState<
    AutoMaterializeEvaluationRecordItemFragment | undefined
  >();

  const evaluations = buildEvaluationRecordsWithPartitions();

  return (
    <div style={{width: '320px'}}>
      <AutomaterializeLeftList
        assetHasDefinedPartitions
        evaluations={evaluations}
        onSelectEvaluation={(evaluation: AutoMaterializeEvaluationRecordItemFragment) =>
          setSelectedEvaluation(evaluation)
        }
        selectedEvaluation={selectedEvaluation}
      />
    </div>
  );
};

export const NoPartitions = () => {
  const [selectedEvaluation, setSelectedEvaluation] = useState<
    AutoMaterializeEvaluationRecordItemFragment | undefined
  >();

  const evaluations = buildEvaluationRecordsWithoutPartitions();

  return (
    <div style={{width: '320px'}}>
      <AutomaterializeLeftList
        assetHasDefinedPartitions={false}
        evaluations={evaluations}
        onSelectEvaluation={(evaluation: AutoMaterializeEvaluationRecordItemFragment) =>
          setSelectedEvaluation(evaluation)
        }
        selectedEvaluation={selectedEvaluation}
      />
    </div>
  );
};
