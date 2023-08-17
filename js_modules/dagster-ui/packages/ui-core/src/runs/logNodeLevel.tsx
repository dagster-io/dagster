import {LogLevel} from './LogLevel';
import {LogNode} from './types';

export const logNodeLevel = (node: LogNode): LogLevel =>
  node.__typename === 'LogMessageEvent' ? node.level : LogLevel.EVENT;
