import {RunTargets} from '../RunTargets';
import {
  checksOnlyRun,
  completeSelectionRun,
  incompleteSelectionRun,
} from '../__fixtures__/RunsFeedEntries.fixtures';
import {MappedRunsFeedEntry} from '../mapRunsFeedData';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Runs Redesign/RunTargets',
  component: RunTargets,
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
    <RunTargets entry={entry} />
  </div>
);

export const CompleteSelection = () => <CellTemplate entry={completeSelectionRun} />;
export const IncompleteSelection = () => <CellTemplate entry={incompleteSelectionRun} />;
export const ChecksOnly = () => <CellTemplate entry={checksOnlyRun} />;
