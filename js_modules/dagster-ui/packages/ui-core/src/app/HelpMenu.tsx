import {
  Box,
  Colors,
  ExternalAnchorButton,
  FontFamily,
  Icon,
  Menu,
  MenuDivider,
  MenuExternalLink,
  MenuItem,
  Popover,
  ProductTour,
  ProductTourPosition,
  Spinner,
  Tooltip,
} from '@dagster-io/ui-components';
import {useCallback, useContext, useState} from 'react';
import {useLocation} from 'react-router-dom';

import {AppContext} from './AppContext';
import {ShortcutHandler} from './ShortcutHandler';
import {TooltipShortcutInfo, TopNavButton} from './TopNavButton';
import DagsterUniversityImage from './dagster_university.svg';
import {useStateWithStorage} from '../hooks/useStateWithStorage';
import {useLatestVersionNumber} from '../nav/LatestVersionNumber';
import {useVersionNumber} from '../nav/VersionNumber';
import {CopyIconButton} from '../ui/CopyButton';

interface Props {
  showContactSales?: boolean;
  onShareFeedback?: () => void;
}

const TOUR_BLOCKED_ROUTES = ['/getting-started'];

export const HelpMenu = ({showContactSales = true, onShareFeedback}: Props) => {
  const [isOpen, setIsOpen] = useState(false);

  const location = useLocation();
  const isTourBlocked = TOUR_BLOCKED_ROUTES.some(
    (route) => location.pathname === route || location.pathname.startsWith(route),
  );

  const onInteraction = useCallback((open: boolean) => setIsOpen(open), []);

  const [didDismissDaggyU, setDidDismissDaggyU] = useStateWithStorage<boolean>(
    'daggy_u_pt',
    (json) => !!json,
  );

  return (
    <ShortcutHandler
      onShortcut={() => setIsOpen(!isOpen)}
      shortcutLabel="?"
      shortcutFilter={(e) => e.key === '?'}
    >
      <ProductTour
        title="Master the Dagster basics"
        description="Learn the basics of Dagster with the free Dagster Essentials course from Dagster University"
        position={ProductTourPosition.BOTTOM_LEFT}
        canShow={!isOpen && !didDismissDaggyU && !isTourBlocked}
        img={DagsterUniversityImage.src}
        actions={{
          custom: (
            <ExternalAnchorButton href="https://courses.dagster.io/courses/dagster-essentials">
              Learn more
            </ExternalAnchorButton>
          ),
          dismiss: () => {
            setDidDismissDaggyU(true);
          },
        }}
      >
        <Popover
          isOpen={isOpen}
          placement="bottom-end"
          canEscapeKeyClose
          onInteraction={onInteraction}
          modifiers={{offset: {enabled: true, options: {offset: [0, 16]}}}}
          content={
            <HelpMenuContents
              onShareFeedback={onShareFeedback}
              dismissDaggyU={() => setDidDismissDaggyU(true)}
              showContactSales={showContactSales}
            />
          }
        >
          <Tooltip
            content={<TooltipShortcutInfo label="Help" shortcutKey="?" />}
            placement="bottom"
            canShow={!isOpen}
          >
            <TopNavButton>
              <Icon name="help_circle" size={20} />
            </TopNavButton>
          </Tooltip>
        </Popover>
      </ProductTour>
    </ShortcutHandler>
  );
};

interface HelpMenuContentsProps {
  onShareFeedback?: () => void;
  dismissDaggyU: () => void;
  showContactSales?: boolean;
}

export const HelpMenuContents = ({
  onShareFeedback,
  dismissDaggyU,
  showContactSales,
}: HelpMenuContentsProps) => {
  const {version, loading} = useVersionNumber();
  const {version: latestVersion, loading: latestLoading} = useLatestVersionNumber();
  const {telemetryEnabled} = useContext(AppContext);

  // const isNewVersionAvailable = latestVersion && latestVersion !== version;

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
        onClick={dismissDaggyU}
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
      {telemetryEnabled ? (
        <div>
          <MenuDivider title="New version available" />
          <Box
            flex={{direction: 'row', gap: 8, alignItems: 'center', justifyContent: 'space-between'}}
            padding={{vertical: 4, horizontal: 8}}
          >
            <div style={{fontSize: '12px', color: Colors.textLight()}}>
              {latestVersion ? (
                <span style={{fontFamily: FontFamily.monospace}}>{latestVersion}</span>
              ) : (
                <Spinner purpose="caption-text" />
              )}
            </div>
            <Tooltip content="Copy version number" canShow={!latestLoading} placement="top">
              <CopyIconButton
                value={latestVersion ?? ''}
                iconSize={12}
                iconColor={Colors.textLight()}
              />
            </Tooltip>
          </Box>
        </div>
      ) : null}
    </Menu>
  );
};
