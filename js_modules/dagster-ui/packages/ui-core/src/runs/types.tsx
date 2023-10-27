import {RunDagsterRunEventFragment} from './types/RunFragments.types';

export type LogNode = RunDagsterRunEventFragment & {clientsideKey: string};
