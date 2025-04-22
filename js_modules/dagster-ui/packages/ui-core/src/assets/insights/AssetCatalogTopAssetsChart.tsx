import {BodyLarge, BodySmall, Box, Colors, MiddleTruncate} from '@dagster-io/ui-components';
import {BarElement, CategoryScale, Chart as ChartJS, Legend, LinearScale, Tooltip} from 'chart.js';
import React from 'react';
import {Bar} from 'react-chartjs-2';

import styles from './AssetCatalogTopAssetsChart.module.css';

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

const assets = [
  'stitch/salesforce/account',
  'fivetran/linear/team_project',
  'purina/staging/product__asset_observations',
  'purina/staging/cloud_product__teams_users',
  'fivetran/linear/attachment_metadata',
  'stitch/elementl_cloud_prod/customer_info',
  'stitch/elementl_cloud_prod/deployment_settings',
  'stitch/elementl_cloud_prod/users',
  'stitch/stripe_prod_v3/plans',
  'stitch/salesforce/account',
];

const options = {
  scales: {
    y: {
      beginAtZero: true,
      grid: {color: '#333', borderDash: [4, 4]},
    },
    x: {grid: {display: false}, ticks: {display: false}},
  },
  plugins: {
    legend: {display: false},
  },
};

export const AssetCatalogTopAssetsChart = React.memo(
  ({
    header,
    datasets,
    unitType,
  }: {
    header: string;
    datasets: {labels: string[]; data: number[]};
    unitType: string;
  }) => {
    const chartConfig = {
      labels: datasets.labels,
      datasets: [
        {
          label: unitType,
          data: datasets.data,
          backgroundColor: '#b095f9',
          borderRadius: 0,
        },
      ],
    };

    return (
      <div className={styles.container}>
        <BodyLarge>{header}</BodyLarge>
        <Box border="bottom">
          <Bar data={chartConfig} options={options} />
        </Box>
        <div>
          <Box
            flex={{direction: 'row', justifyContent: 'space-between', gap: 12}}
            style={{color: Colors.textLighter()}}
            border="bottom"
            padding={{vertical: 8}}
          >
            <BodySmall>Asset</BodySmall>
            <BodySmall>Count</BodySmall>
          </Box>
          <div className={styles.table}>
            {assets.map((asset, i) => (
              <React.Fragment key={i}>
                <BodySmall as="div">
                  <MiddleTruncate text={asset} />
                </BodySmall>
                <BodySmall>190</BodySmall>
              </React.Fragment>
            ))}
          </div>
        </div>
      </div>
    );
  },
);
