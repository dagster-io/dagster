import {ExecutionParams, ExecutionTag} from '../graphql/types';
import {DagsterTag} from '../runs/RunTag';

export const UI_EXECUTION_TAGS: ExecutionTag[] = [{key: DagsterTag.FromUI, value: 'true'}];

export function tagsWithUIExecutionTags(tags: ExecutionTag[] | null | undefined) {
  return [
    ...(tags || []).filter((t) => !UI_EXECUTION_TAGS.some((a) => a.key === t.key)),
    ...UI_EXECUTION_TAGS,
  ];
}

export function paramsWithUIExecutionTags(params: ExecutionParams) {
  return {
    ...params,
    executionMetadata: {
      ...params.executionMetadata,
      tags: tagsWithUIExecutionTags(params.executionMetadata?.tags),
    },
  };
}
