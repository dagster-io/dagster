import {
  DEFAULT_JOB_GROUP_NAME,
  JobGroupNode,
  allJobGroupPaths,
  buildJobGroupTree,
} from '../jobGroups';

type TestJob = {name: string; groupName?: string | null};

// Reduce a tree to `path(jobs)[children]` strings so assertions stay readable.
const summarize = (nodes: JobGroupNode<TestJob>[]): string[] =>
  nodes.map((node) => {
    const jobs = node.jobs.map((job) => job.name).join(',');
    const children = summarize(node.children);
    return `${node.path}(${jobs})${children.length ? `[${children.join(' ')}]` : ''}`;
  });

describe('buildJobGroupTree', () => {
  it('buckets jobs by group name, sorted alphabetically with the default group last', () => {
    const groups = buildJobGroupTree([
      {name: 'a', groupName: 'operational'},
      {name: 'b', groupName: null},
      {name: 'c', groupName: 'analytics'},
      {name: 'd', groupName: 'operational'},
      {name: 'e', groupName: DEFAULT_JOB_GROUP_NAME},
    ]);

    expect(summarize(groups)).toEqual(['analytics(c)', 'operational(a,d)', 'default(b,e)']);
  });

  it('nests groups on the `/` separator', () => {
    const groups = buildJobGroupTree([
      {name: 'a', groupName: 'operational/maintenance'},
      {name: 'b', groupName: 'operational/notifications'},
      {name: 'c', groupName: 'analytics'},
    ]);

    expect(summarize(groups)).toEqual([
      'analytics(c)',
      'operational()[operational/maintenance(a) operational/notifications(b)]',
    ]);
  });

  it('lets a group hold both its own jobs and nested subgroups', () => {
    const groups = buildJobGroupTree([
      {name: 'a', groupName: 'operational'},
      {name: 'b', groupName: 'operational/maintenance'},
    ]);

    expect(summarize(groups)).toEqual(['operational(a)[operational/maintenance(b)]']);
  });

  it('reports depth for each level of nesting', () => {
    const [root] = buildJobGroupTree([{name: 'a', groupName: 'one/two/three'}]);

    expect(root?.depth).toBe(0);
    expect(root?.name).toBe('one');
    expect(root?.children[0]?.depth).toBe(1);
    expect(root?.children[0]?.children[0]?.depth).toBe(2);
    expect(root?.children[0]?.children[0]?.name).toBe('three');
    expect(root?.children[0]?.children[0]?.path).toBe('one/two/three');
  });

  it('treats jobs with no group name as members of the default group', () => {
    expect(summarize(buildJobGroupTree([{name: 'a'}, {name: 'b', groupName: ''}]))).toEqual([
      'default(a,b)',
    ]);
  });

  it('returns an empty list when there are no jobs', () => {
    expect(buildJobGroupTree([])).toEqual([]);
  });
});

describe('allJobGroupPaths', () => {
  it('lists every path in depth-first display order', () => {
    const groups = buildJobGroupTree([
      {name: 'a', groupName: 'operational/maintenance'},
      {name: 'b', groupName: 'operational'},
      {name: 'c', groupName: 'analytics'},
      {name: 'd'},
    ]);

    expect(allJobGroupPaths(groups)).toEqual([
      'analytics',
      'operational',
      'operational/maintenance',
      'default',
    ]);
  });
});
