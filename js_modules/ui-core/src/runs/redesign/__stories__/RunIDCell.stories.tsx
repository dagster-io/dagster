import {RunIDCell} from '../RunIDCell';
import {runEntry} from '../__fixtures__/RunsFeedEntries.fixtures';
import {MappedRunsFeedEntry} from '../mapRunsFeedData';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Runs Redesign/RunIDCell',
  component: RunIDCell,
};

const CellTemplate = ({entry}: {entry: MappedRunsFeedEntry}) => (
  <div
    style={{
      display: 'flex',
      alignItems: 'center',
      width: 420,
      height: 48,
      padding: '0 16px',
      border: '1px solid var(--color-keyline-default)',
    }}
  >
    <RunIDCell entry={entry} />
  </div>
);

export const Run = () => (
  <CellTemplate entry={runEntry({id: 'a1b2c3d4-1111-2222-3333-444455556666'})} />
);
