import {Redirect, Switch, useParams} from 'react-router-dom';

import {CodeLocationComponentsRoot} from './CodeLocationComponentsRoot';
import {Route} from '../app/Route';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

interface Props {
  repoAddress: RepoAddress;
}

// All `/locations/:repoPath/components/*` routes live here so `WorkspaceRoot`
// only needs to forward to this component. `library/...` and `instances` both
// resolve to `CodeLocationComponentsRoot`, which picks the right subtab from
// the URL.
export const CodeLocationComponentsRoutes = ({repoAddress}: Props) => (
  <Switch>
    <Route path="/locations/:repoPath/components" exact>
      <CodeLocationComponentsRoot repoAddress={repoAddress} />
    </Route>
    <Route path="/locations/:repoPath/components/instances" exact>
      <Redirect to={workspacePathFromAddress(repoAddress, '/components')} />
    </Route>
    <Route path="/locations/:repoPath/components/catalog" exact>
      <Redirect to={workspacePathFromAddress(repoAddress, '/components/library')} />
    </Route>
    <Route path="/locations/:repoPath/components/catalog/packages/:packageName?/:componentName?">
      <RedirectCatalogToLibrary repoAddress={repoAddress} />
    </Route>
    <Route path="/locations/:repoPath/components/library" exact>
      <CodeLocationComponentsRoot repoAddress={repoAddress} />
    </Route>
    <Route path="/locations/:repoPath/components/library/packages/:packageName?/:componentName?">
      <CodeLocationComponentsRoot repoAddress={repoAddress} />
    </Route>
  </Switch>
);

// `/components/catalog/...` was the original home of the type registry; it
// moved to `/components/library/...`. Forward deep links here too.
const RedirectCatalogToLibrary = ({repoAddress}: {repoAddress: RepoAddress}) => {
  const {packageName, componentName} = useParams<{packageName?: string; componentName?: string}>();
  let suffix = '';
  if (packageName) {
    suffix = componentName
      ? `/packages/${packageName}/${componentName}`
      : `/packages/${packageName}`;
  }
  return <Redirect to={workspacePathFromAddress(repoAddress, `/components/library${suffix}`)} />;
};
