import {Box} from '@dagster-io/ui-components';
import faker from 'faker';
import {MemoryRouter} from 'react-router-dom';

import {AssetKeyTagCollection} from '../AssetTagCollections';
import styles from './css/AssetKeyTagCollection.module.css';

const makeKeys = (count: number) => {
  return Array(count)
    .fill(null)
    .map((_) => ({path: [faker.random.word()]}));
};

// eslint-disable-next-line import/no-default-export
export default {
  title: 'AssetKeyTagCollection',
  component: AssetKeyTagCollection,
};

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
      <Box className={styles.row}>
        <div>old style</div>
        <div>tag style</div>
        <div>tag + maxrows</div>
      </Box>
      <Box className={styles.row}>
        <div>
          <AssetKeyTagCollection assetKeys={single} />
        </div>
        <div>
          <AssetKeyTagCollection assetKeys={single} useTags />
        </div>
        <div style={{maxHeight: 60}}>
          <AssetKeyTagCollection assetKeys={single} useTags maxRows={2} />
        </div>
      </Box>
      <Box className={styles.row}>
        <div style={{overflow: 'hidden', maxWidth: 400}}>
          <AssetKeyTagCollection assetKeys={singleSuperLong} />
        </div>
        <div style={{minWidth: 0}}>
          <AssetKeyTagCollection assetKeys={singleSuperLong} useTags />
        </div>
        <div style={{minWidth: 0, maxHeight: 60}}>
          <AssetKeyTagCollection assetKeys={singleSuperLong} useTags maxRows={2} />
        </div>
      </Box>
      <Box className={styles.row}>
        <div>
          <AssetKeyTagCollection assetKeys={two} />
        </div>
        <div>
          <AssetKeyTagCollection assetKeys={two} useTags />
        </div>
        <div style={{maxHeight: 60}}>
          <AssetKeyTagCollection assetKeys={two} useTags maxRows={2} />
        </div>
      </Box>
      <Box className={styles.row}>
        <div>
          <AssetKeyTagCollection assetKeys={many} />
        </div>
        <div>
          <AssetKeyTagCollection assetKeys={many} useTags />
        </div>
        <div style={{maxHeight: 60}}>
          <AssetKeyTagCollection assetKeys={many} useTags maxRows={2} />
        </div>
      </Box>
      <Box className={styles.row}>
        <div>
          <AssetKeyTagCollection assetKeys={manySuperLong} />
        </div>
        <div>
          <AssetKeyTagCollection assetKeys={manySuperLong} useTags />
        </div>
        <div style={{maxHeight: 60}}>
          <AssetKeyTagCollection assetKeys={manySuperLong} useTags maxRows={2} />
        </div>
      </Box>
    </MemoryRouter>
  );
};
