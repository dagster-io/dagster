import {CaptionMono, Mono} from '@dagster-io/ui-components';
import {useEffect} from 'react';
import {Link, useHistory} from 'react-router-dom';

export interface ExplorerPath {
  pipelineName: string;
  snapshotId?: string;
  opsQuery: string;
  explodeComposites?: boolean;
  opNames: string[];
}

export const explorerPathSeparator = '~';

export function explorerPathToString(path: ExplorerPath) {
  const root = [
    path.pipelineName,
    path.snapshotId ? `@${path.snapshotId}` : ``,
    path.opsQuery
      ? `${explorerPathSeparator}${path.explodeComposites ? '!' : ''}${encodeURIComponent(
          path.opsQuery,
        )}`
      : ``,
  ].join('');

  return `${root}/${path.opNames.map(encodeURIComponent).join('/')}`;
}

/** react-router-dom helpfully auto-decodes the location.path, but does not auto-encode it.
 * We still need explorerPathToString to encode the path, since the value could be passed
 * to window.open, etc., and we need explorerPathFromString to reverse explorerPathToString.
 *
 * Our best option is to try decoding the path, and if it fails, assume that react-router-dom
 * has already done it for us.
 */
function tryDecodeURIComponent(str: string) {
  try {
    return decodeURIComponent(str);
  } catch {
    return str;
  }
}

export function explorerPathFromString(path: string): ExplorerPath {
  const rootAndOps = path.split('/');
  const root = rootAndOps[0]!;
  const opNames = rootAndOps.length === 1 ? [''] : rootAndOps.slice(1);

  const match = /^([^@~]+)@?([^~]+)?~?(!)?(.*)$/.exec(root);
  const [, pipelineName, snapshotId, explodeComposites, opsQuery] = [
    ...(match || []),
    '',
    '',
    '',
    '',
  ];

  return {
    pipelineName,
    snapshotId,
    opsQuery: tryDecodeURIComponent(opsQuery || ''),
    explodeComposites: explodeComposites === '!',
    opNames: opNames.map(tryDecodeURIComponent),
  };
}

export function useStripSnapshotFromPath(params: {pipelinePath: string}) {
  const history = useHistory();
  const {pipelinePath} = params;

  useEffect(() => {
    const {snapshotId, ...rest} = explorerPathFromString(pipelinePath);
    if (!snapshotId) {
      return;
    }
    history.replace({
      pathname: history.location.pathname.replace(
        new RegExp(`/${pipelinePath}/?`),
        `/${explorerPathToString(rest)}`,
      ),
    });
  }, [history, pipelinePath]);
}

export function getPipelineSnapshotLink(pipelineName: string, snapshotId: string) {
  return `/snapshots/${explorerPathToString({
    pipelineName,
    snapshotId,
    opsQuery: '',
    opNames: [],
  })}`;
}

export const PipelineSnapshotLink = (props: {
  pipelineName: string;
  snapshotId: string;
  size: 'small' | 'normal';
}) => {
  const snapshotLink = getPipelineSnapshotLink(props.pipelineName, props.snapshotId);
  const linkElem = <Link to={snapshotLink}>{props.snapshotId.slice(0, 8)}</Link>;
  return props.size === 'small' ? <CaptionMono>{linkElem}</CaptionMono> : <Mono>{linkElem}</Mono>;
};
