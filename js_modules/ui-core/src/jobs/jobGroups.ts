/**
 * Group name used for jobs that were defined without an explicit `group_name`. Matches
 * `dagster._core.definitions.utils.DEFAULT_GROUP_NAME`.
 */
export const DEFAULT_JOB_GROUP_NAME = 'default';

/**
 * Separator used to express hierarchy within a group name, e.g. `operational/maintenance`.
 * Matches `dagster._core.definitions.utils.VALID_GROUP_NAME_REGEX`.
 */
export const JOB_GROUP_SEPARATOR = '/';

type WithGroupName = {groupName?: string | null};

export type JobGroupNode<T> = {
  /** The last segment of the group name, used as the display label. */
  name: string;
  /** The full group name, e.g. `operational/maintenance`. Unique within a code location. */
  path: string;
  /** Nesting level, where top-level groups are 0. */
  depth: number;
  /** Jobs whose group name is exactly `path`. */
  jobs: T[];
  children: JobGroupNode<T>[];
};

type MutableNode<T> = Omit<JobGroupNode<T>, 'children'> & {
  childrenByName: Map<string, MutableNode<T>>;
};

const createNode = <T>(name: string, path: string, depth: number): MutableNode<T> => ({
  name,
  path,
  depth,
  jobs: [],
  childrenByName: new Map(),
});

/**
 * Sorts sibling groups alphabetically, with the default group always last so that explicitly
 * organized jobs appear first. Only a top-level group can be named `default`.
 */
const compareSiblings = <T>(a: MutableNode<T>, b: MutableNode<T>) => {
  if (a.path === DEFAULT_JOB_GROUP_NAME) {
    return b.path === DEFAULT_JOB_GROUP_NAME ? 0 : 1;
  }
  if (b.path === DEFAULT_JOB_GROUP_NAME) {
    return -1;
  }
  return a.name.localeCompare(b.name);
};

const finalize = <T>(node: MutableNode<T>): JobGroupNode<T> => {
  const {childrenByName, ...rest} = node;
  return {
    ...rest,
    children: Array.from(childrenByName.values()).sort(compareSiblings).map(finalize),
  };
};

/**
 * Builds a tree of job groups from the `/`-separated segments of each job's group name. A group
 * may hold both jobs of its own and nested subgroups, e.g. a job in `operational` alongside jobs
 * in `operational/maintenance`.
 */
export const buildJobGroupTree = <T extends WithGroupName>(jobs: T[]): JobGroupNode<T>[] => {
  const rootsByName = new Map<string, MutableNode<T>>();

  for (const job of jobs) {
    const segments = (job.groupName || DEFAULT_JOB_GROUP_NAME)
      .split(JOB_GROUP_SEPARATOR)
      .filter((segment) => segment.length > 0);

    // Defensive: the backend rejects group names that normalize to nothing, but never drop a job
    // on the floor if one slips through.
    const path = segments.length ? segments : [DEFAULT_JOB_GROUP_NAME];

    let siblings = rootsByName;
    let node: MutableNode<T> | undefined;

    path.forEach((segment, index) => {
      const fullPath = path.slice(0, index + 1).join(JOB_GROUP_SEPARATOR);
      let next = siblings.get(segment);
      if (!next) {
        next = createNode<T>(segment, fullPath, index);
        siblings.set(segment, next);
      }
      node = next;
      siblings = next.childrenByName;
    });

    node?.jobs.push(job);
  }

  return Array.from(rootsByName.values()).sort(compareSiblings).map(finalize);
};

/** Every group path in the tree, including nested ones, in depth-first display order. */
export const allJobGroupPaths = <T>(nodes: JobGroupNode<T>[]): string[] =>
  nodes.flatMap((node) => [node.path, ...allJobGroupPaths(node.children)]);
