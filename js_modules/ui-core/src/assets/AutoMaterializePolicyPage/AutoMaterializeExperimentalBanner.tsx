import {Alert, Box, Colors, Icon} from '@dagster-io/ui-components';

import {useStateWithStorage} from '../../hooks/useStateWithStorage';

const LEARN_MORE_LINK =
  'https://docs.dagster.io/concepts/assets/asset-auto-execution#auto-materializing-assets-';

export const AutoMaterializeExperimentalBanner = () => {
  const [closed, setClosed] = useStateWithStorage('automation-experimental', (value) => !!value);
  if (closed) {
    return null;
  }
  return (
    <Box padding={{horizontal: 24, vertical: 12}} border="bottom">
      <Alert
        intent="info"
        title="Automation conditions are experimental"
        icon={<Icon name="info" color={Colors.accentBlue()} />}
        onClose={() => {
          setClosed(true);
        }}
        description={
          <span>
            You can learn more about this new feature and provide feedback{' '}
            <a target="_blank" href={LEARN_MORE_LINK} rel="noreferrer">
              here
            </a>
            .
          </span>
        }
      />
    </Box>
  );
};
