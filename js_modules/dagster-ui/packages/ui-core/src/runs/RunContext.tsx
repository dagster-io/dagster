import * as React from 'react';

import {RunFragment} from './types/RunFragments.types';

const initialContext = undefined;
export const RunContext = React.createContext<RunFragment | undefined>(initialContext);
