import {Box, Colors} from '@dagster-io/ui-components';
import React, {useMemo} from 'react';

import {ActivityChart} from './AssetCatalogActivityChart';
import styles from './AssetCatalogInsights.module.css';
import {AssetCatalogInsightsLineChart} from './AssetCatalogInsightsLineChart';
import {AssetCatalogTopAssetsChart} from './AssetCatalogTopAssetsChart';
import {useRGBColorsForTheme} from '../../app/useRGBColorsForTheme';

export const AssetCatalogInsights = React.memo((_: {selection: string}) => {
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
          <AssetCatalogInsightsLineChart color={colors.NEUTRAL} />
          <AssetCatalogInsightsLineChart color={colors.FAILURE} />
        </div>
        <div className={styles.LineCharts}>
          <AssetCatalogInsightsLineChart color={colors.NEUTRAL} />
          <AssetCatalogInsightsLineChart color={colors.NEUTRAL} />
          <AssetCatalogInsightsLineChart color={colors.FAILURE} />
          <AssetCatalogInsightsLineChart color={colors.FAILURE} />
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
        <AssetCatalogTopAssetsChart header="Top assets by materialization count" />
        <AssetCatalogTopAssetsChart header="Top assets by failure count" />
        <AssetCatalogTopAssetsChart header="Top assets by avg. execution time" />
        <AssetCatalogTopAssetsChart header="Top assets by freshness failure count" />
        <AssetCatalogTopAssetsChart header="Top assets by check failure count" />
      </div>
    </Box>
  );
});
