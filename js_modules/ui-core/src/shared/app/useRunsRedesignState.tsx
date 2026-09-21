export type RunsRedesignState = 'loading' | 'enabled' | 'disabled';

// Keep OSS on the legacy runs feed until the redesign is ready for open source.
export const useRunsRedesignState = (): RunsRedesignState => 'disabled';
