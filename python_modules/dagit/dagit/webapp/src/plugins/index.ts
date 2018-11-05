import {
  SolidFragment,
  SolidFragment_definition_metadata
} from "../types/SolidFragment";

const context = require.context(".", true);
const plugins: { [kind: string]: IPluginInterface } = {};
context.keys().forEach((filename: string) => {
  const ext = filename
    .replace("./", "")
    .split(".")
    .shift();
  if (ext) {
    plugins[ext] = context(filename);
  }
});

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
