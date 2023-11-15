import * as React from 'react';

import {AutomaterializeLeftList} from '../AutomaterializeLeftPanel';
import {
  buildEvaluationRecordsWithPartitions,
  buildEvaluationRecordsWithoutPartitions,
} from '../__fixtures__/AutoMaterializePolicyPage.fixtures';
import {getEvaluationsWithEmptyAdded} from '../getEvaluationsWithEmptyAdded';
import {EvaluationOrEmpty} from '../types';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Asset Details/Automaterialize/AutomaterializeLeftList',
  component: AutomaterializeLeftList,
};

export const WithPartitions = () => {
  const [selectedEvaluation, setSelectedEvaluation] = React.useState<
    EvaluationOrEmpty | undefined
  >();

  const evaluations = buildEvaluationRecordsWithPartitions();
  const evaluationsWithEmpty = getEvaluationsWithEmptyAdded({
    evaluations,
    currentAutoMaterializeEvaluationId: evaluations[0]!.evaluationId,
    isLastPage: true,
    isFirstPage: true,
    isLoading: false,
  });

  return (
    <div style={{width: '320px'}}>
      <AutomaterializeLeftList
        assetHasDefinedPartitions
        evaluationsIncludingEmpty={evaluationsWithEmpty}
        onSelectEvaluation={(evaluation: EvaluationOrEmpty) => setSelectedEvaluation(evaluation)}
        selectedEvaluation={selectedEvaluation}
      />
    </div>
  );
};

export const NoPartitions = () => {
  const [selectedEvaluation, setSelectedEvaluation] = React.useState<
    EvaluationOrEmpty | undefined
  >();

  const evaluations = buildEvaluationRecordsWithoutPartitions();
  const evaluationsWithEmpty = getEvaluationsWithEmptyAdded({
    evaluations,
    currentAutoMaterializeEvaluationId: evaluations[0]!.evaluationId,
    isLastPage: true,
    isFirstPage: true,
    isLoading: false,
  });

  return (
    <div style={{width: '320px'}}>
      <AutomaterializeLeftList
        assetHasDefinedPartitions={false}
        evaluationsIncludingEmpty={evaluationsWithEmpty}
        onSelectEvaluation={(evaluation: EvaluationOrEmpty) => setSelectedEvaluation(evaluation)}
        selectedEvaluation={selectedEvaluation}
      />
    </div>
  );
};
