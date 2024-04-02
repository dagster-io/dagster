import {faker} from '@faker-js/faker';
import {Meta} from '@storybook/react';
import {useEffect, useMemo, useState} from 'react';

import {InsightsBarChart} from '../InsightsBarChart';
import {orderedColors} from '../InsightsColors';
import {ReportingUnitType} from '../types';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Insights/InsightsBarChart',
  component: InsightsBarChart,
} as Meta;

const TWO_HOURS = 2 * 60 * 60 * 1000;
const JUNE_1_2023_EDT = 1685592000000;
const MIN = 100;
const MAX = 1000;

const randomDataPoint = (min: number, max: number) => {
  const rand = Math.random();
  return min + Math.floor((max - min) * rand);
};

export const Default = () => {
  const numDates = 50;
  const numLines = 1;

  const datapoints = useMemo(() => {
    const listOfDatapointLists = new Array(numLines).fill(null).map((_) => {
      return new Array(numDates).fill(null).map(() => {
        const key = faker.random.alphaNumeric(8);
        return {
          value: randomDataPoint(MIN, MAX),
          key,
          href: `/runs/${key}`,
          label: `Run ${key}`,
        };
      });
    });
    return Object.fromEntries(
      listOfDatapointLists.map((datapointsForKey, ii) => {
        const key = faker.random.words(3).replaceAll(' ', '-').toLowerCase();
        return [
          key,
          {
            barColor: orderedColors[ii % numLines]!,
            type: 'asset-group' as const,
            label: key,
            values: datapointsForKey,
          },
        ];
      }),
    );
  }, []);

  const timestamps = useMemo(() => {
    return new Array(numDates).fill(null).map((_, ii) => JUNE_1_2023_EDT + TWO_HOURS * ii);
  }, [numDates]);

  return (
    <div style={{height: '600px'}}>
      <InsightsBarChart
        datapointType="asset-group"
        datapoints={datapoints}
        loading={false}
        metricLabel="Dagster credits"
        metricName="__dagster_dagster_credits"
        unitType={ReportingUnitType.INTEGER}
        timestamps={timestamps}
        costMultiplier={null}
      />
    </div>
  );
};

export const Empty = () => {
  const numDates = 10;

  const timestamps = useMemo(() => {
    return new Array(numDates).fill(null).map((_, ii) => JUNE_1_2023_EDT + TWO_HOURS * ii);
  }, [numDates]);

  return (
    <div style={{height: '600px'}}>
      <InsightsBarChart
        datapointType="asset-group"
        datapoints={{}}
        loading={false}
        metricLabel="Dagster credits"
        metricName="__dagster_dagster_credits"
        unitType={ReportingUnitType.INTEGER}
        timestamps={timestamps}
        costMultiplier={null}
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
    return new Array(numDates).fill(null).map((_, ii) => JUNE_1_2023_EDT + TWO_HOURS * ii);
  }, [numDates]);

  return (
    <div style={{height: '600px'}}>
      <InsightsBarChart
        datapointType="asset-group"
        datapoints={{}}
        loading={loading}
        metricLabel="Dagster credits"
        metricName="__dagster_dagster_credits"
        unitType={ReportingUnitType.INTEGER}
        timestamps={timestamps}
        costMultiplier={null}
      />
    </div>
  );
};
