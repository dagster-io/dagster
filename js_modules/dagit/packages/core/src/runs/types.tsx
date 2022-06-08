import {RunDagsterRunEventFragment} from './types/RunDagsterRunEventFragment';

export type LogNode = RunDagsterRunEventFragment & {clientsideKey: string};
