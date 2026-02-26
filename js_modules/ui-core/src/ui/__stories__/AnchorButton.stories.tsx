import {Box, ExternalAnchorButton, Icon} from '@dagster-io/ui-components';

import {AnchorButton} from '../AnchorButton';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'AnchorButton',
  component: AnchorButton,
};

export const Default = () => {
  return (
    <Box flex={{direction: 'column', gap: 8, alignItems: 'flex-start'}}>
      <AnchorButton to="/">Button</AnchorButton>
      <AnchorButton to="/" icon={<Icon name="star" />}>
        Button
      </AnchorButton>
      <AnchorButton to="/" rightIcon={<Icon name="close" />}>
        Button
      </AnchorButton>
      <AnchorButton to="/" icon={<Icon name="source" />} rightIcon={<Icon name="expand_more" />}>
        Button
      </AnchorButton>
      <AnchorButton to="/" icon={<Icon name="cached" />} />
    </Box>
  );
};

export const Intent = () => {
  return (
    <Box flex={{direction: 'column', gap: 8, alignItems: 'flex-start'}}>
      <AnchorButton to="/" icon={<Icon name="star" />}>
        No intent set
      </AnchorButton>
      <AnchorButton to="/" icon={<Icon name="star" />} intent="primary">
        Primary
      </AnchorButton>
      <AnchorButton to="/" icon={<Icon name="done" />} intent="success">
        Success
      </AnchorButton>
      <AnchorButton to="/" icon={<Icon name="error" />} intent="danger">
        Danger
      </AnchorButton>
      <AnchorButton to="/" icon={<Icon name="warning" />} intent="warning">
        Warning
      </AnchorButton>
      <AnchorButton to="/" icon={<Icon name="star" />} intent="none">
        None
      </AnchorButton>
    </Box>
  );
};

export const Outlined = () => {
  return (
    <Box flex={{direction: 'column', gap: 8, alignItems: 'flex-start'}}>
      <AnchorButton to="/" outlined icon={<Icon name="star" />}>
        No intent set
      </AnchorButton>
      <AnchorButton to="/" outlined icon={<Icon name="star" />} intent="primary">
        Primary
      </AnchorButton>
      <AnchorButton to="/" outlined icon={<Icon name="done" />} intent="success">
        Success
      </AnchorButton>
      <AnchorButton to="/" outlined icon={<Icon name="error" />} intent="danger">
        Danger
      </AnchorButton>
      <AnchorButton to="/" outlined icon={<Icon name="warning" />} intent="warning">
        Warning
      </AnchorButton>
      <AnchorButton to="/" outlined icon={<Icon name="star" />} intent="none">
        None
      </AnchorButton>
    </Box>
  );
};

export const ExternalButton = () => {
  return (
    <Box flex={{direction: 'column', gap: 8, alignItems: 'flex-start'}}>
      <ExternalAnchorButton href="https://html5zombo.com/">Button</ExternalAnchorButton>
      <ExternalAnchorButton href="https://html5zombo.com/" icon={<Icon name="star" />}>
        Button
      </ExternalAnchorButton>
      <ExternalAnchorButton href="https://html5zombo.com/" rightIcon={<Icon name="close" />}>
        Button
      </ExternalAnchorButton>
      <ExternalAnchorButton
        href="https://html5zombo.com/"
        icon={<Icon name="source" />}
        rightIcon={<Icon name="expand_more" />}
      >
        Button
      </ExternalAnchorButton>
      <ExternalAnchorButton href="https://html5zombo.com/" icon={<Icon name="cached" />} />
    </Box>
  );
};
