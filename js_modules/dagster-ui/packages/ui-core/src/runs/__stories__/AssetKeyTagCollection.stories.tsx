import {Box} from '@dagster-io/ui-components';
import {Meta} from '@storybook/react';
import faker from 'faker';
import {MemoryRouter} from 'react-router-dom';
import styled from 'styled-components';

import {AssetKeyTagCollection} from '../AssetTagCollections';

const makeKeys = (count: number) => {
  return Array(count)
    .fill(null)
    .map((_) => ({path: [faker.random.word()]}));
};

// eslint-disable-next-line import/no-default-export
export default {
  title: 'AssetKeyTagCollection',
  component: AssetKeyTagCollection,
} as Meta;

export const Scenarios = () => {
  const single = makeKeys(1);
  const two = makeKeys(2);
  const many = makeKeys(20);

  const singleSuperLong = [{path: [faker.lorem.word(10).repeat(10)]}];
  const manySuperLong = Array(20)
    .fill(null)
    .map((_) => ({path: [faker.lorem.word(10).repeat(10)]}));

  return (
    <MemoryRouter>
      <Row>
        <div>old style</div>
        <div>tag style</div>
        <div>tag + maxrows</div>
      </Row>
      <Row>
        <div>
          <AssetKeyTagCollection assetKeys={single} />
        </div>
        <div>
          <AssetKeyTagCollection assetKeys={single} useTags />
        </div>
        <div style={{maxHeight: 60}}>
          <AssetKeyTagCollection assetKeys={single} useTags maxRows={2} />
        </div>
      </Row>
      <Row>
        <div style={{overflow: 'hidden', maxWidth: 400}}>
          <AssetKeyTagCollection assetKeys={singleSuperLong} />
        </div>
        <div style={{minWidth: 0}}>
          <AssetKeyTagCollection assetKeys={singleSuperLong} useTags />
        </div>
        <div style={{minWidth: 0, maxHeight: 60}}>
          <AssetKeyTagCollection assetKeys={singleSuperLong} useTags maxRows={2} />
        </div>
      </Row>
      <Row>
        <div>
          <AssetKeyTagCollection assetKeys={two} />
        </div>
        <div>
          <AssetKeyTagCollection assetKeys={two} useTags />
        </div>
        <div style={{maxHeight: 60}}>
          <AssetKeyTagCollection assetKeys={two} useTags maxRows={2} />
        </div>
      </Row>
      <Row>
        <div>
          <AssetKeyTagCollection assetKeys={many} />
        </div>
        <div>
          <AssetKeyTagCollection assetKeys={many} useTags />
        </div>
        <div style={{maxHeight: 60}}>
          <AssetKeyTagCollection assetKeys={many} useTags maxRows={2} />
        </div>
      </Row>
      <Row>
        <div>
          <AssetKeyTagCollection assetKeys={manySuperLong} />
        </div>
        <div>
          <AssetKeyTagCollection assetKeys={manySuperLong} useTags />
        </div>
        <div style={{maxHeight: 60}}>
          <AssetKeyTagCollection assetKeys={manySuperLong} useTags maxRows={2} />
        </div>
      </Row>
    </MemoryRouter>
  );
};

const Row = styled(Box)`
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  min-height: 30px;
  margin-bottom: 24px;
  height: 100%;

  & > div {
    min-width: 0;
  }
`;
