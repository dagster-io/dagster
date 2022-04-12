import * as generic from '../plugins/generic';
import * as ipynb from '../plugins/ipynb';
import * as sql from '../plugins/sql';
import {RepoAddress} from '../workspace/types';

const plugins = {
  sql,
  ipynb,
  snowflake: sql,
};

export interface IPluginSidebarProps {
  definition: {
    name: string;
    metadata: {
      key: string;
      value: string;
    }[];
  };
  repoAddress?: RepoAddress;
}

interface IPluginInterface {
  SidebarComponent: React.ComponentClass<IPluginSidebarProps> | React.SFC<IPluginSidebarProps>;
}

export function pluginForMetadata(
  metadata: {key: string; value: string}[],
): IPluginInterface | null {
  const kindMetadata = metadata.find((m) => m.key === 'kind');
  if (!kindMetadata) {
    return null;
  }
  return plugins[kindMetadata.value] || generic;
}
