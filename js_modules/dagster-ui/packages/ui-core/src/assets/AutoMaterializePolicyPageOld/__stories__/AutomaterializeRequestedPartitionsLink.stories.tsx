import {MockedProvider} from '@apollo/client/testing';
import faker from 'faker';
import * as React from 'react';

import {AutomaterializeRequestedPartitionsLink} from '../AutomaterializeRequestedPartitionsLink';
import {buildRunStatusAndPartitionKeyQuery} from '../__fixtures__/AutomaterializeRequestedPartitionsLink.fixtures';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Asset Details/Automaterialize/AutomaterializeRequestedPartitionsLink',
  component: AutomaterializeRequestedPartitionsLink,
};

export const ManyPartitionsAndRuns = () => {
  const partitionKeys = new Array(40).fill(null).map((_) => faker.lorem.words(3));
  const runIds = new Array(40).fill(null).map((_) => faker.datatype.uuid());
  return (
    <MockedProvider mocks={[buildRunStatusAndPartitionKeyQuery(partitionKeys, runIds)]}>
      <AutomaterializeRequestedPartitionsLink partitionKeys={partitionKeys} runIds={runIds} />
    </MockedProvider>
  );
};

export const OnlyPartitions = () => {
  const partitionKeys = new Array(40).fill(null).map((_) => faker.lorem.words(3));
  return <AutomaterializeRequestedPartitionsLink partitionKeys={partitionKeys} />;
};
