import * as React from 'react';

import {RunFragment} from './types/RunFragment';

const initialContext = undefined;
export const RunContext = React.createContext<RunFragment | undefined>(initialContext);
