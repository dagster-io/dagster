import {IPluginSidebarProps} from '../plugins';
import {NotebookButton} from '../ui/NotebookButton';

export const SidebarComponent = (props: IPluginSidebarProps) => {
  const metadata = props.definition.metadata;
  const notebookPath = metadata.find((m) => m.key === 'notebook_path');
  const repoLocName = props.repoAddress?.location;

  return (
    <NotebookButton
      path={notebookPath?.value}
      repoLocation={repoLocName || ''}
      label="View Source Notebook"
    />
  );
};
