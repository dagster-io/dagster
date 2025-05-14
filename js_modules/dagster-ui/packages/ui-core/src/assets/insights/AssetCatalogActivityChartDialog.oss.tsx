import { Button, Dialog, DialogFooter } from '@dagster-io/ui-components';
import { AssetTableFragment } from '../types/AssetTableFragment.types';

// interface Props {
//   after: number; 
//   before: number;
//   metricName: string;
//   isOpen: boolean;
// }

// export type ActivityChartDialogData = {
//   after: number; 
//   before: number;
//   metric: string;
//   assets: AssetTableFragment[];
//   selection: string;
//   // isOpen: boolean;
//   // onClose: () => void;
// }


export type ActivityChartDialogData = {
  after: number; 
  before: number;
  metric: string;
  assets: AssetTableFragment[];
  selection: string;
  // isOpen: boolean;
  // onClose: () => void;
}


export const AssetCatalogActivityChartDialog = ({dialogConfig, isOpen, onClose}: {dialogConfig: ActivityChartDialogData; isOpen: boolean; onClose: () => void}) => {
  return null;
};