import {Box, Colors} from '@dagster-io/ui-components';
import React, {useMemo} from 'react';

import {ActivityChart} from './AssestCatalogActiveChart';
import styles from './AssetsCatalogInsights.module.css';
import {AssetsCatalogInsightsLineChart} from './AssetsCatalogInsightsLineChart';
import {AssetsCatalogTopAssetsChart} from './AssetsCatalogTopAssetsChart';
import {useRGBColorsForTheme} from '../../app/useRGBColorsForTheme';

export const AssetsCatalogInsights = React.memo(() => {
  const rgbColors = useRGBColorsForTheme();
  const colors = useMemo(() => {
    return {
      FAILURE: rgbColors[Colors.accentRed()]!,
      SUCCESS: rgbColors[Colors.accentGreen()]!,
      NEUTRAL: rgbColors[Colors.accentBlue()]!,
      WARNING: rgbColors[Colors.accentYellow()]!,
    };
  }, [rgbColors]);

  return (
    <Box padding={24}>
      <Box flex={{direction: 'column', gap: 12}}>
        <div className={styles.MainLineCharts}>
          <AssetsCatalogInsightsLineChart color={colors.NEUTRAL} />
          <AssetsCatalogInsightsLineChart color={colors.FAILURE} />
        </div>
        <div className={styles.LineCharts}>
          <AssetsCatalogInsightsLineChart color={colors.NEUTRAL} />
          <AssetsCatalogInsightsLineChart color={colors.NEUTRAL} />
          <AssetsCatalogInsightsLineChart color={colors.FAILURE} />
          <AssetsCatalogInsightsLineChart color={colors.FAILURE} />
        </div>
      </Box>
      <div className={styles.ActivityCharts}>
        <ActivityChart header="Materializations by hour" color={colors.SUCCESS} />
        <ActivityChart header="Avg execution time by hour" color={colors.NEUTRAL} />
        <ActivityChart header="Retries by hour" color={colors.NEUTRAL} />
        <ActivityChart header="Materialization failures by hour" color={colors.FAILURE} />
        <ActivityChart header="Freshness policy violations by hour" color={colors.FAILURE} />
        <ActivityChart header="Check failures by hour" color={colors.FAILURE} />
      </div>
      <div className={styles.TopAssetsChartsSection}>
        <AssetsCatalogTopAssetsChart header="Top assets by materialization count" />
        <AssetsCatalogTopAssetsChart header="Top assets by failure count" />
        <AssetsCatalogTopAssetsChart header="Top assets by avg. execution time" />
        <AssetsCatalogTopAssetsChart header="Top assets by freshness failure count" />
        <AssetsCatalogTopAssetsChart header="Top assets by check failure count" />
      </div>
    </Box>
  );
});
