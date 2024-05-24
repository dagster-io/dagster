import {faker} from '@faker-js/faker';
import {Meta} from '@storybook/react';
import {useEffect, useMemo, useState} from 'react';

import {orderedColors} from '../InsightsColors';
import {InsightsLineChart} from '../InsightsLineChart';
import {ReportingMetricsGranularity, ReportingUnitType} from '../types';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Insights/InsightsLineChart',
  component: InsightsLineChart,
} as Meta;

const ONE_DAY = 24 * 60 * 60 * 1000;
const JUNE_1_2023_EDT = 1685592000000;
const MIN = 100;
const MAX = 20000;

const randomDataPoint = (min: number, max: number) => {
  const rand = Math.random();
  return min + Math.floor((max - min) * rand);
};

export const Default = () => {
  const numDates = 10;
  const numLines = 4;

  const datapoints = useMemo(() => {
    const listOfDatapointLists = new Array(numLines).fill(null).map((_) => {
      return new Array(numDates).fill(null).map(() => randomDataPoint(MIN, MAX));
    });
    return Object.fromEntries(
      listOfDatapointLists.map((datapointsForKey, ii) => {
        const key = faker.random.words(3).replaceAll(' ', '-').toLowerCase();
        return [
          key,
          {
            lineColor: orderedColors[ii % numLines]!,
            type: 'asset-group' as const,
            label: key,
            values: datapointsForKey,
          },
        ];
      }),
    );
  }, []);

  const timestamps = useMemo(() => {
    return new Array(numDates).fill(null).map((_, ii) => JUNE_1_2023_EDT + ONE_DAY * ii);
  }, [numDates]);

  return (
    <div style={{height: '600px'}}>
      <InsightsLineChart
        datapointType="asset-group"
        datapoints={datapoints}
        loading={false}
        metricLabel="Materializations"
        metricName="__dagster_materializations"
        costMultiplier={0.001}
        unitType={ReportingUnitType.INTEGER}
        granularity={ReportingMetricsGranularity.DAILY}
        timestamps={timestamps}
        highlightKey={null}
      />
    </div>
  );
};

export const Empty = () => {
  const numDates = 10;

  const timestamps = useMemo(() => {
    return new Array(numDates).fill(null).map((_, ii) => JUNE_1_2023_EDT + ONE_DAY * ii);
  }, [numDates]);

  return (
    <div style={{height: '600px'}}>
      <InsightsLineChart
        datapointType="asset-group"
        datapoints={{}}
        loading={false}
        metricLabel="Materializations"
        metricName="__dagster_materializations"
        costMultiplier={0.001}
        unitType={ReportingUnitType.INTEGER}
        granularity={ReportingMetricsGranularity.DAILY}
        timestamps={timestamps}
        highlightKey={null}
      />
    </div>
  );
};

const LOADING_DELAY_SEC = 5000;

export const InitiallyLoading = () => {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setTimeout(() => {
      setLoading(false);
    }, LOADING_DELAY_SEC);
  }, []);

  const numDates = 10;

  const timestamps = useMemo(() => {
    return new Array(numDates).fill(null).map((_, ii) => JUNE_1_2023_EDT + ONE_DAY * ii);
  }, [numDates]);

  return (
    <div style={{height: '600px'}}>
      <InsightsLineChart
        datapointType="asset-group"
        datapoints={{}}
        loading={loading}
        metricLabel="Materializations"
        metricName="__dagster_materializations"
        costMultiplier={0.001}
        unitType={ReportingUnitType.INTEGER}
        granularity={ReportingMetricsGranularity.DAILY}
        timestamps={timestamps}
        highlightKey={null}
      />
    </div>
  );
};
