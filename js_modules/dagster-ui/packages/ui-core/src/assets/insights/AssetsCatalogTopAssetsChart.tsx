import {BodyLarge, BodySmall, Box, Colors, MiddleTruncate} from '@dagster-io/ui-components';
import {BarElement, CategoryScale, Chart as ChartJS, Legend, LinearScale, Tooltip} from 'chart.js';
import React from 'react';
import {Bar} from 'react-chartjs-2';

import styles from './AssetsCatalogTopAssetsChart.module.css';

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

const data = {
  labels: Array.from({length: 20}, (_, i) => `Asset ${i + 1}`),
  datasets: [
    {
      label: 'Materialization Count',
      data: [
        5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 10, 10, 20, 40, 40, 40, 40, 40, 40, 40, 45, 50, 100,
        110, 110, 120, 120, 130, 140, 190,
      ],
      backgroundColor: '#b095f9',
      borderRadius: 0,
    },
  ],
};

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

export const AssetsCatalogTopAssetsChart = React.memo(({header}: {header: string}) => {
  return (
    <div className={styles.container}>
      <BodyLarge>{header}</BodyLarge>
      <Box border="bottom">
        <Bar data={data} options={options} />
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
});
