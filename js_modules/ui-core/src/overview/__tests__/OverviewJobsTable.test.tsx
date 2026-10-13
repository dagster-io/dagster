import {render, screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import {OverviewJobsTable} from '../OverviewJobsTable';

// The virtualizer measures a scroll container, which has no height in jsdom and would render no
// rows. Render every row instead so the flattening and expansion logic is what's under test.
jest.mock('@tanstack/react-virtual', () => ({
  useVirtualizer: ({count}: {count: number}) => ({
    getTotalSize: () => count * 64,
    getVirtualItems: () =>
      Array.from({length: count}, (_, index) => ({
        index,
        key: index,
        start: index * 64,
        size: 64,
      })),
    measureElement: () => {},
  }),
}));

// The real row fires a GraphQL query per job and pulls in the router; the table only needs to be
// verified on which rows it renders.
jest.mock('../../workspace/VirtualizedObserveJobRow', () => ({
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  VirtualizedObserveJobRow: require('react').forwardRef(
    ({name}: {name: string}, _ref: React.ForwardedRef<HTMLDivElement>) => (
      <div data-testid="job-row">{name}</div>
    ),
  ),
}));

const repoAddress = {name: 'my-repo', location: 'my-location'};

const jobNames = () => screen.queryAllByTestId('job-row').map((row) => row.textContent);

const REPO_HEADINGS = ['my-repo', 'other-repo'];

// Section headers render icons carrying their own aria-labels, so the accessible name of a
// header button is not just the group name. Match on text content instead.
const groupHeadings = () =>
  screen
    .queryAllByRole('button')
    .map((button) => button.textContent)
    .filter((text): text is string => !!text && !REPO_HEADINGS.includes(text));

const groupHeaderButton = (groupName: string, index = 0) =>
  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  screen.getAllByRole('button').filter((button) => button.textContent === groupName)[index]!;

describe('OverviewJobsTable', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('renders a section per group, sorted alphabetically with the default group last', () => {
    render(
      <OverviewJobsTable
        repos={[
          {
            repoAddress,
            jobs: [
              {name: 'ungrouped_job', isJob: true, groupName: 'default'},
              {name: 'vacuum_job', isJob: true, groupName: 'operational'},
              {name: 'customers_job', isJob: true, groupName: 'analytics'},
            ],
          },
        ]}
      />,
    );

    expect(groupHeadings()).toEqual(['analytics', 'operational', 'default']);
    expect(jobNames()).toEqual(['customers_job', 'vacuum_job', 'ungrouped_job']);
  });

  it('treats a missing group name as the default group', () => {
    render(
      <OverviewJobsTable
        repos={[
          {
            repoAddress,
            jobs: [
              {name: 'no_group_job', isJob: true},
              {name: 'vacuum_job', isJob: true, groupName: 'operational'},
            ],
          },
        ]}
      />,
    );

    expect(groupHeadings()).toEqual(['operational', 'default']);
    expect(jobNames()).toEqual(['vacuum_job', 'no_group_job']);
  });

  it('does not render group sections when every job is in the default group', () => {
    render(
      <OverviewJobsTable
        repos={[
          {
            repoAddress,
            jobs: [
              {name: 'job_one', isJob: true, groupName: 'default'},
              {name: 'job_two', isJob: true},
            ],
          },
        ]}
      />,
    );

    expect(groupHeadings()).toEqual([]);
    expect(jobNames()).toEqual(['job_one', 'job_two']);
  });

  it('collapses only the clicked group', async () => {
    const user = userEvent.setup();
    render(
      <OverviewJobsTable
        repos={[
          {
            repoAddress,
            jobs: [
              {name: 'customers_job', isJob: true, groupName: 'analytics'},
              {name: 'vacuum_job', isJob: true, groupName: 'operational'},
            ],
          },
        ]}
      />,
    );

    expect(jobNames()).toEqual(['customers_job', 'vacuum_job']);

    await user.click(groupHeaderButton('analytics'));

    // The analytics section is still listed, but its job is hidden.
    expect(groupHeadings()).toEqual(['analytics', 'operational']);
    expect(jobNames()).toEqual(['vacuum_job']);
  });

  it('renders nested groups as a tree, labeling each section with its own segment', () => {
    render(
      <OverviewJobsTable
        repos={[
          {
            repoAddress,
            jobs: [
              {name: 'digest_job', isJob: true, groupName: 'operational/notifications'},
              {name: 'vacuum_job', isJob: true, groupName: 'operational/maintenance'},
              {name: 'oncall_job', isJob: true, groupName: 'operational'},
            ],
          },
        ]}
      />,
    );

    // `operational` renders once as a parent; its children are labeled by their last segment.
    expect(groupHeadings()).toEqual(['operational', 'maintenance', 'notifications']);
    // Subgroups come before the parent's own jobs.
    expect(jobNames()).toEqual(['vacuum_job', 'digest_job', 'oncall_job']);
  });

  it('hides nested subgroups when their parent is collapsed', async () => {
    const user = userEvent.setup();
    render(
      <OverviewJobsTable
        repos={[
          {
            repoAddress,
            jobs: [
              {name: 'vacuum_job', isJob: true, groupName: 'operational/maintenance'},
              {name: 'customers_job', isJob: true, groupName: 'analytics'},
            ],
          },
        ]}
      />,
    );

    expect(groupHeadings()).toEqual(['analytics', 'operational', 'maintenance']);

    await user.click(groupHeaderButton('operational'));

    // The nested `maintenance` section disappears along with its jobs.
    expect(groupHeadings()).toEqual(['analytics', 'operational']);
    expect(jobNames()).toEqual(['customers_job']);
  });

  it('collapses a child group without collapsing its parent', async () => {
    const user = userEvent.setup();
    render(
      <OverviewJobsTable
        repos={[
          {
            repoAddress,
            jobs: [
              {name: 'vacuum_job', isJob: true, groupName: 'operational/maintenance'},
              {name: 'oncall_job', isJob: true, groupName: 'operational'},
            ],
          },
        ]}
      />,
    );

    await user.click(groupHeaderButton('maintenance'));

    expect(groupHeadings()).toEqual(['operational', 'maintenance']);
    expect(jobNames()).toEqual(['oncall_job']);
  });

  it('keeps group expansion state separate per code location', async () => {
    const user = userEvent.setup();
    const otherRepoAddress = {name: 'other-repo', location: 'my-location'};
    render(
      <OverviewJobsTable
        repos={[
          {
            repoAddress,
            jobs: [{name: 'first_vacuum_job', isJob: true, groupName: 'operational'}],
          },
          {
            repoAddress: otherRepoAddress,
            jobs: [{name: 'second_vacuum_job', isJob: true, groupName: 'operational'}],
          },
        ]}
      />,
    );

    expect(jobNames()).toEqual(['first_vacuum_job', 'second_vacuum_job']);

    // Both code locations have an `operational` group; collapsing one must not collapse the other.
    await user.click(groupHeaderButton('operational', 0));

    expect(jobNames()).toEqual(['second_vacuum_job']);
  });
});
