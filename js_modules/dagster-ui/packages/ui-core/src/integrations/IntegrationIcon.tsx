import {Box, Icon} from '@dagster-io/ui-components';

import styles from './IntegrationIcon.module.css';
import {INTEGRATIONS_HOSTNAME} from './constants';

interface Props {
  name: string;
  content: string | null; // URL or image filename or an emoji
}

export const IntegrationIcon = ({name, content}: Props) => {
  const icon = () => {
    if (!content) {
      return <Icon name="workspace" size={24} />;
    }

    if (content.length <= 2) {
      return <div className={styles.integrationIconEmoji}>{content}</div>;
    }

    const url = content.startsWith('http') ? content : `${INTEGRATIONS_HOSTNAME}/logos/${content}`;

    return (
      <div
        role="img"
        aria-label={name}
        className={styles.integrationIconWrapper}
        style={{backgroundImage: `url(${url})`}}
      />
    );
  };

  return (
    <Box
      flex={{alignItems: 'center', justifyContent: 'center'}}
      border="all"
      style={{borderRadius: 8, height: 48, width: 48}}
      padding={8}
    >
      {icon()}
    </Box>
  );
};
