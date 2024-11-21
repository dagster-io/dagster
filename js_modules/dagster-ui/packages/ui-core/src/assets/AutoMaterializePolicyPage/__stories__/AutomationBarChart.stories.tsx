import {useRef} from 'react';

import {AutomationBarChart} from '../AutomationBarChart';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Asset Details/Automaterialize/AutomationBarChart',
};

const ONE_MINUTE_MS = 60 * 1000;
const PER_PAGE = 25;
const EMPTY_PER_PAGE = 25;

export const Default = () => {
  const now = useRef(Date.now());
  const timestamps = new Array(PER_PAGE).fill(null).map((_, ii) => {
    return new Date(now.current + ONE_MINUTE_MS * ii).getTime();
  });

  const values = new Array(PER_PAGE).fill(null).map((_, ii) => {
    return {
      value: Math.floor(Math.random() * 5),
      evaluationID: `evaluation-${ii}`,
    };
  });

  return (
    <div style={{height: '240px'}}>
      <AutomationBarChart
        timestamps={timestamps}
        values={values}
        loading={false}
        onClickEvaluation={(evaluationID) => {
          console.log('evaluationID', evaluationID);
        }}
      />
    </div>
  );
};

export const NoData = () => {
  const now = useRef(Date.now());
  const timestamps: number[] = new Array(EMPTY_PER_PAGE).fill(null).map((_, ii) => {
    return new Date(now.current + ONE_MINUTE_MS * ii).getTime();
  });
  const values: {value: number | null; evaluationID: string}[] = [];

  return (
    <div style={{height: '240px'}}>
      <AutomationBarChart
        timestamps={timestamps}
        values={values}
        loading={false}
        onClickEvaluation={() => {}}
      />
    </div>
  );
};

export const Loading = () => {
  const now = useRef(Date.now());
  const timestamps: number[] = new Array(EMPTY_PER_PAGE).fill(null).map((_, ii) => {
    return new Date(now.current + ONE_MINUTE_MS * ii).getTime();
  });
  const values: {value: number | null; evaluationID: string}[] = [];

  return (
    <div style={{height: '240px'}}>
      <AutomationBarChart
        timestamps={timestamps}
        values={values}
        loading={true}
        onClickEvaluation={() => {}}
      />
    </div>
  );
};
