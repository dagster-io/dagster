import {IconName} from '@dagster-io/ui-components';

export interface FileNode {
  type: 'file';
  name: string;
  path: string;
  icon?: IconName;
}

export interface FolderNode {
  type: 'folder';
  name: string;
  path: string;
  children: (FileNode | FolderNode)[];
  icon?: IconName;
}

export type HierarchyNode = FileNode | FolderNode;

export interface TreeNode {
  [key: string]: TreeNode;
}

export interface RenderedNode {
  name: string;
  path: string;
  level: number;
  type: 'file' | 'folder';
  icon: IconName;
  hasChildren?: boolean;
}
