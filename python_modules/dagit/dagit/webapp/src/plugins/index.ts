import {
  SolidFragment,
  SolidFragment_definition_metadata
} from "../types/SolidFragment";

import * as ipynb from "./ipynb";
import * as sql from "./sql";

const plugins = {
  sql: sql,
  ipynb: ipynb
};

export interface IPluginSidebarProps {
  solid: SolidFragment;
}

export interface IPluginInterface {
  SidebarComponent:
    | React.ComponentClass<IPluginSidebarProps>
    | React.SFC<IPluginSidebarProps>;
}

export function pluginForMetadata(
  metadata: SolidFragment_definition_metadata[] | null
): IPluginInterface | null {
  if (metadata === null) return null;

  const kindMetadata = metadata.find(m => m.key === "kind");
  if (!kindMetadata || !kindMetadata.value) return null;
  return plugins[kindMetadata.value];
}
