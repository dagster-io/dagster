import {
  Box,
  Colors,
  FontFamily,
  Menu,
  MenuDivider,
  MenuExternalLink,
  MenuItem,
  Spinner,
  Tooltip,
} from '@dagster-io/ui-components';

import {useVersionNumber} from '../nav/VersionNumber';
import {CopyIconButton} from '../ui/CopyButton';

interface HelpMenuContentsProps {
  onShareFeedback?: () => void;
  showContactSales?: boolean;
}

export const HelpMenuContents = ({onShareFeedback, showContactSales}: HelpMenuContentsProps) => {
  const {version, loading} = useVersionNumber();
  return (
    <Menu>
      <MenuDivider title="What's new" />
      <MenuExternalLink
        href="https://docs.dagster.io/changelog"
        icon="concept_book"
        text="View changelog"
      />
      <MenuDivider title="Help" />
      {onShareFeedback ? (
        <MenuItem icon="send" text="Create a support ticket" onClick={onShareFeedback} />
      ) : null}
      <MenuExternalLink href="https://dagster.io/slack" icon="slack" text="Join our Slack" />
      <MenuExternalLink
        href="https://github.com/dagster-io/dagster/discussions"
        icon="github"
        text="Discuss on GitHub"
      />
      <MenuExternalLink href="https://docs.dagster.io" icon="concept_book" text="Read the docs" />
      <MenuExternalLink
        href="https://courses.dagster.io/"
        icon="graduation_cap"
        text="Dagster University"
      />
      {showContactSales ? (
        <MenuExternalLink
          href="https://dagster.io/contact"
          icon="open_in_new"
          text="Contact sales"
        />
      ) : null}
      <MenuDivider title="Version" />
      <Box
        flex={{direction: 'row', gap: 8, alignItems: 'center', justifyContent: 'space-between'}}
        padding={{vertical: 4, horizontal: 8}}
      >
        <div style={{fontSize: '12px', color: Colors.textLight()}}>
          {version ? (
            <span style={{fontFamily: FontFamily.monospace}}>{version}</span>
          ) : (
            <Spinner purpose="caption-text" />
          )}
        </div>
        <Tooltip content="Copy version number" canShow={!loading} placement="top">
          <CopyIconButton value={version ?? ''} iconSize={12} iconColor={Colors.textLight()} />
        </Tooltip>
      </Box>
    </Menu>
  );
};
