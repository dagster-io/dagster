import {createContext} from 'react';

import {RunFragment} from './types/RunFragments.types';

const initialContext = undefined;
export const RunContext = createContext<RunFragment | undefined>(initialContext);
