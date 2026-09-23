import {RunTargetsCell} from '../RunTargetsCell';
import {
  assetsKnownChecksUnknownRun,
  checksOnlyRun,
  completeSelectionRun,
  emptyWholeJobRun,
  incompleteSelectionRun,
  partitionRangeRun,
  partitionSetBackfill,
  singlePartitionRun,
  unknownSelectionsRun,
} from '../__fixtures__/RunsFeedEntries.fixtures';
import {MappedRunsFeedEntry} from '../mapRunsFeedData';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Runs Redesign/RunTargetsCell',
  component: RunTargetsCell,
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
    <RunTargetsCell entry={entry} />
  </div>
);

export const CompleteSelection = () => <CellTemplate entry={completeSelectionRun} />;
export const IncompleteSelection = () => <CellTemplate entry={incompleteSelectionRun} />;
export const UnknownSelections = () => <CellTemplate entry={unknownSelectionsRun} />;
export const AssetsKnownChecksUnknown = () => <CellTemplate entry={assetsKnownChecksUnknownRun} />;
export const ChecksOnly = () => <CellTemplate entry={checksOnlyRun} />;
export const WholeJob = () => <CellTemplate entry={emptyWholeJobRun} />;
export const SinglePartition = () => <CellTemplate entry={singlePartitionRun} />;
export const PartitionRange = () => <CellTemplate entry={partitionRangeRun} />;
export const PartitionSetBackfill = () => <CellTemplate entry={partitionSetBackfill} />;
