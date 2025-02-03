import {Box, Button, Dialog, DialogFooter} from '@dagster-io/ui-components';

import {PoolTag} from '../instance/PoolTag';

export const RunPoolsDialog = ({
  isOpen,
  onClose,
  pools,
}: {
  isOpen: boolean;
  onClose: () => void;
  pools: string[];
}) => {
  return (
    <Dialog isOpen={isOpen} onClose={onClose} canOutsideClickClose canEscapeKeyClose title="Pools">
      <Box margin={{horizontal: 24, vertical: 12}} flex={{gap: 12}}>
        {pools.map((pool) => (
          <PoolTag key={pool} pool={pool} />
        ))}
      </Box>
      <DialogFooter topBorder>
        <Button onClick={onClose} intent="primary">
          Close
        </Button>
      </DialogFooter>
    </Dialog>
  );
};
