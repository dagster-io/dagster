import {RunStatus} from '../graphql/types';

interface Props {
  run: {id: string; status: RunStatus};
}

// eslint-disable-next-line unused-imports/no-unused-vars
export const AISummaryForRunMenuItem = ({run}: Props) => null;
