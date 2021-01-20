import {Intent, Position, Toaster} from '@blueprintjs/core';

export const APP_PATH_PREFIX =
  document.querySelector('meta[name=dagit-path-prefix]')?.getAttribute('content') || '';

export const WEBSOCKET_URI =
  process.env.REACT_APP_GRAPHQL_URI ||
  `${document.location.protocol === 'https:' ? 'wss' : 'ws'}://${
    document.location.host
  }${APP_PATH_PREFIX}/graphql`;

// The address to the dagit server (eg: http://localhost:5000) based
// on our current "GRAPHQL_URI" env var. Note there is no trailing slash.
export const ROOT_SERVER_URI = WEBSOCKET_URI.replace('wss://', 'https://')
  .replace('ws://', 'http://')
  .replace('/graphql', '');

export const SharedToaster = Toaster.create({position: Position.TOP}, document.body);

export async function copyValue(event: React.MouseEvent<any>, value: string) {
  event.preventDefault();

  const el = document.createElement('textarea');
  document.body.appendChild(el);
  el.value = value;
  el.select();
  document.execCommand('copy');
  el.remove();

  SharedToaster.show({
    message: 'Copied to clipboard!',
    icon: 'clipboard',
    intent: Intent.NONE,
  });
}
