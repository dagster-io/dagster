import * as React from 'react';

import {RunFragmentFragment} from '../graphql/graphql';

const initialContext = undefined;
export const RunContext = React.createContext<RunFragmentFragment | undefined>(initialContext);
