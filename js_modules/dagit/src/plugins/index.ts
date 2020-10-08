import * as generic from 'src/plugins/generic';
import * as ipynb from 'src/plugins/ipynb';
import * as sql from 'src/plugins/sql';
import {SidebarSolidDefinitionFragment} from 'src/types/SidebarSolidDefinitionFragment';

const plugins = {
  sql: sql,
  ipynb: ipynb,
  snowflake: sql,
};

export interface IPluginSidebarProps {
  definition: SidebarSolidDefinitionFragment;
}

export interface IPluginInterface {
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
