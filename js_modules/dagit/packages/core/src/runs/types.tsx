import {RunDagsterRunEventFragmentFragment} from '../graphql/graphql';

export type LogNode = RunDagsterRunEventFragmentFragment & {clientsideKey: string};
