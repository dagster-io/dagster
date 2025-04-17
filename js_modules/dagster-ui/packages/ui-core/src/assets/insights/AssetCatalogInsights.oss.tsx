import {Box, Colors} from '@dagster-io/ui-components';
import React, {useMemo} from 'react';

import {ActivityChart} from './AssetCatalogActivityChart';
import styles from './AssetCatalogInsights.module.css';
import {AssetCatalogInsightsLineChart} from './AssetCatalogInsightsLineChart';
import {AssetCatalogTopAssetsChart} from './AssetCatalogTopAssetsChart';
import {useRGBColorsForTheme} from '../../app/useRGBColorsForTheme';
import { useQuery } from '@apollo/client';

export const AssetCatalogInsights = React.memo((_: {selection: string}) => {
  return <div>not supported in oss</div>
});
