import {MemoryRouter} from 'react-router-dom';

import {DagsterTag} from '../../RunTag';
import {RunTagsDialog} from '../RunTagsDialog';
import {runEntry, tag} from '../__fixtures__/RunsFeedEntries.fixtures';
import {RunSummaryFragment} from '../types/RunsFeedFragments.types';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Runs Redesign/RunTagsDialog',
  component: RunTagsDialog,
};

type DialogTemplateProps = {
  tags: RunSummaryFragment['tags'];
};

const DialogTemplate = ({tags}: DialogTemplateProps) => {
  const run = runEntry({id: 'a1b2c3d4-1111-2222-3333-444455556666', tags});
  return (
    <MemoryRouter>
      <RunTagsDialog run={run} onClose={() => {}} />
    </MemoryRouter>
  );
};

export const Default = () => (
  <DialogTemplate
    tags={[
      tag('team', 'data'),
      tag(DagsterTag.Partition, '2026-09-08'),
      tag(DagsterTag.ScheduleName, 'daily_etl_schedule'),
      tag('env', 'prod'),
    ]}
  />
);

export const ManyTagsWithLongValues = () => (
  <DialogTemplate
    tags={[
      tag(DagsterTag.Partition, '2026-09-08'),
      tag(DagsterTag.SensorName, 'inventory_automation'),
      tag(
        'description',
        'Nightly refresh of the sales and inventory marts, rebuilt after the upstream warehouse export completes and the freshness checks pass',
      ),
      tag('commit_sha', '9fceb02d0ae598e95dc970b74767f19372d61af8a1b2c3d4e5f60718293a4b5c6d7e8f90'),
      tag('owner', 'data-platform'),
      tag('team', 'data'),
      tag('env', 'prod'),
      tag('region', 'us-east-1'),
      tag('cost_center', '4410'),
      tag('priority', 'high'),
      tag('notify', 'data-oncall@example.com'),
      tag('source', 'warehouse_export'),
    ]}
  />
);
