import subtree from './sub-tree.json';
import { TreeElement } from './Nav';

export default (apiDocs: TreeElement[]): Record<string, TreeElement[]> => ({
  ...subtree,
  'API Docs': apiDocs,
});
