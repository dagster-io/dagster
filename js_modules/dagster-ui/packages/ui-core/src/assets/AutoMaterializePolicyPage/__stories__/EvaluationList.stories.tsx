import {MockedProvider} from '@apollo/client/testing';

import {buildAssetNode} from '../../../graphql/types';
import {EvaluationList} from '../EvaluationList';
import {buildEvaluationRecordsForList} from '../__fixtures__/EvaluationList.fixtures';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Asset Details/Automaterialize/EvaluationList',
  component: EvaluationList,
};

export const Default = () => {
  const definition = buildAssetNode({
    id: '1',
    groupName: '1',
    isMaterializable: true,
    partitionDefinition: null,
    partitionKeysByDimension: [],
  });

  const evaluations = buildEvaluationRecordsForList(25);

  return (
    <MockedProvider>
      <EvaluationList
        assetKey={definition.assetKey}
        isPartitioned={false}
        evaluations={evaluations}
      />
    </MockedProvider>
  );
};
