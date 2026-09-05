import {Box, Intent} from '@dagster-io/ui-components';

import {AppContext, AppContextValue} from '../../AppContext';
import {DeploymentLabelTag} from '../DeploymentLabelTag';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'DeploymentLabelTag',
  component: DeploymentLabelTag,
};

const WithContext = ({
  uiLabel,
  uiIntent,
  collapsed = false,
}: {
  uiLabel?: string;
  uiIntent?: string;
  collapsed?: boolean;
}) => {
  const value: AppContextValue = {
    basePath: '',
    rootServerURI: '',
    telemetryEnabled: false,
    uiLabel,
    uiIntent,
  };
  return (
    <AppContext.Provider value={value}>
      <DeploymentLabelTag collapsed={collapsed} />
    </AppContext.Provider>
  );
};

const INTENTS: Intent[] = ['none', 'primary', 'success', 'warning', 'danger'];

export const AllIntents = () => (
  <Box flex={{direction: 'column', gap: 8}} style={{width: 240}}>
    {INTENTS.map((intent) => (
      <WithContext key={intent} uiLabel={`Deployment (${intent})`} uiIntent={intent} />
    ))}
  </Box>
);

export const DefaultIntent = () => <WithContext uiLabel="Production" />;

// An intent the server did not recognize is dropped before it reaches the client,
// so the tag falls back to the default color rather than rendering unstyled.
export const UnknownIntent = () => <WithContext uiLabel="Production" uiIntent="chartreuse" />;

export const NoLabel = () => <WithContext />;

export const Collapsed = () => (
  <Box flex={{direction: 'column', gap: 8}} style={{width: 68}}>
    {INTENTS.map((intent) => (
      <WithContext key={intent} uiLabel={`Deployment (${intent})`} uiIntent={intent} collapsed />
    ))}
  </Box>
);
