import {
  Box,
  Button,
  Dialog,
  DialogFooter,
  NonIdealState,
  TextInput,
} from '@dagster-io/ui-components';
import * as React from 'react';

interface Props {
  isOpen: boolean;
  setIsOpen: (value: boolean) => void;
  header: React.ReactNode;
  content: React.ReactNode;
  height?: number;
}

export const AssetKeysDialog = (props: Props) => {
  const {isOpen, setIsOpen, header, content, height = 272} = props;
  return (
    <Dialog
      isOpen={isOpen}
      onClose={() => setIsOpen(false)}
      style={{width: '750px', maxWidth: '80vw', minWidth: '500px', transform: 'scale(1)'}}
      canOutsideClickClose
      canEscapeKeyClose
    >
      {header}
      <div style={{height: `${height}px`, overflow: 'hidden'}}>{content}</div>
      <DialogFooter topBorder>
        <Button onClick={() => setIsOpen(false)}>Close</Button>
      </DialogFooter>
    </Dialog>
  );
};

interface HeaderProps {
  title: React.ReactNode;
  showSearch: boolean;
  placeholder: string;
  queryString: string;
  setQueryString: (value: string) => void;
}

export const AssetKeysDialogHeader = (props: HeaderProps) => {
  const {title, showSearch, placeholder, queryString, setQueryString} = props;
  return (
    <Box
      padding={{horizontal: 24, vertical: 16}}
      flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}
      border="bottom"
    >
      <div style={{fontSize: '16px'}}>{title}</div>
      {showSearch ? (
        <TextInput
          icon="search"
          value={queryString}
          onChange={(e) => setQueryString(e.target.value)}
          placeholder={placeholder}
          style={{width: '252px'}}
        />
      ) : null}
    </Box>
  );
};

interface EmptyStateProps {
  title: string;
  description: React.ReactNode;
}

export const AssetKeysDialogEmptyState = ({title, description}: EmptyStateProps) => {
  return (
    <Box padding={32}>
      <NonIdealState icon="search" title={title} description={description} />
    </Box>
  );
};
