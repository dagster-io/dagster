import {AssetCatalogMetricNames} from './AssetCatalogMetricUtils';
import {AssetTableFragment} from '../types/AssetTableFragment.types';

export type ActivityChartDialogData = {
  after: number;
  before: number;
  metric: AssetCatalogMetricNames;
  assets: AssetTableFragment[];
  selection: string;
  unit: string;
};

export const AssetCatalogActivityChartDialog = ({
  _dialogConfig,
  _isOpen,
  _onClose,
}: {
  _dialogConfig: ActivityChartDialogData;
  _isOpen: boolean;
  _onClose: () => void;
}) => {
  return null;
};
