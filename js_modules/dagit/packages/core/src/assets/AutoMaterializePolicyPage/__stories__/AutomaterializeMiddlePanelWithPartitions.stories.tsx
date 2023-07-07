import {MockedProvider} from '@apollo/client/testing';
import * as React from 'react';

import {RunStatus} from '../../../graphql/types';
import {AutomaterializeMiddlePanelWithPartitions} from '../AutomaterializeMiddlePanelWithPartitions';
import {
  Evaluations,
  SINGLE_MATERIALIZE_RECORD_WITH_PARTITIONS,
} from '../__fixtures__/AutoMaterializePolicyPage.fixtures';
import {buildRunStatusOnlyQuery} from '../__fixtures__/RunStatusOnlyQuery.fixtures';

// eslint-disable-next-line import/no-default-export
export default {component: AutomaterializeMiddlePanelWithPartitions};

const path = ['test'];

export const WithPartitions = () => {
  return (
    <MockedProvider
      mocks={[Evaluations.Single(path), buildRunStatusOnlyQuery('abcdef12', RunStatus.STARTED)]}
    >
      <div style={{width: '800px'}}>
        <AutomaterializeMiddlePanelWithPartitions
          maxMaterializationsPerMinute={1}
          selectedEvaluation={SINGLE_MATERIALIZE_RECORD_WITH_PARTITIONS}
        />
      </div>
    </MockedProvider>
  );
};
