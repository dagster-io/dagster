import {LogNode} from './types';

// https://jsbench.me/o8kqzo8olz/1
export function flattenNodeChunks(nodeChunks: LogNode[][]) {
  return ([] as LogNode[]).concat(...nodeChunks);
}
