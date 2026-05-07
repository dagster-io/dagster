import {AssetNodeRepositoryFragment} from './types/AssetTableFragment.types';
import {AssetNodeKeyFragment} from '../asset-graph/types/AssetNode.types';
import {RepositoryAssetFragment} from '../workspace/WorkspaceContext/types/WorkspaceQueries.types';

// Workspace-merged asset node — analogous to the server's
// `RemoteWorkspaceAssetNode`. Produced by `getAssets` (in `useAllAssets.tsx`)
// from one or more `RepositoryAssetFragment` definitions of the same asset
// key:
//
// - Array fields (`jobNames`, `kinds`, `tags`, `owners`, `pools`, `dependencyKeys`)
//   are unioned across all per-repo definitions.
// - Boolean fields (`isMaterializable`, `isObservable`, `isExecutable`,
//   `isPartitioned`, `hasAssetChecks`) are OR'd across all per-repo definitions.
// - `repository` is the chosen representative repo when the asset is defined
//   in multiple repos (typically the materializable / non-stub one). The
//   server's `AssetNode.repository` field has the same semantics — it's
//   always already chosen-from-many on the merged remote workspace asset
//   node. `AssetDefinedInMultipleReposNotice` is the surface that
//   disambiguates for the user.
// - `dependedByKeys` is workspace-wide: every loaded asset whose
//   `dependencyKeys` includes this asset's key. Cross-repo edges are included.
//
// Most UI consumers (graph builder, asset table, search, sidebar, asset
// selection, repo address routing) operate on this shape, not on
// `RepositoryAssetFragment`. This file is intentionally pure-types so it can
// be imported from `asset-graph/Utils.tsx` and similar modules that are
// loaded by Web Workers (which can't pull in React or Apollo).
export type WorkspaceAssetNode = RepositoryAssetFragment & {
  repository: AssetNodeRepositoryFragment['repository'];
  dependedByKeys: AssetNodeKeyFragment[];
};
