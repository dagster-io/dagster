import {
  ExternalAnchorButton,
  Icon,
  Menu,
  MenuDivider,
  MenuExternalLink,
  MenuItem,
  Popover,
  ProductTour,
  ProductTourPosition,
  Tooltip,
} from '@dagster-io/ui-components';
import {useCallback, useState} from 'react';

import {ShortcutHandler} from './ShortcutHandler';
import {TooltipShortcutInfo, TopNavButton} from './TopNavButton';
import DagsterUniversityImage from './dagster_university.svg';
import {useStateWithStorage} from '../hooks/useStateWithStorage';

interface Props {
  showContactSales?: boolean;
  onShareFeedback?: () => void;
}

export const HelpMenu = ({showContactSales = true, onShareFeedback}: Props) => {
  const [isOpen, setIsOpen] = useState(false);

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
        canShow={!isOpen && !didDismissDaggyU}
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
              <MenuExternalLink
                href="https://dagster.io/slack"
                icon="slack"
                text="Join our Slack"
              />
              <MenuExternalLink
                href="https://github.com/dagster-io/dagster/discussions"
                icon="github"
                text="Discuss on GitHub"
              />
              <MenuExternalLink
                href="https://docs.dagster.io"
                icon="concept_book"
                text="Read the docs"
              />
              <div
                onClick={() => {
                  setDidDismissDaggyU(true);
                }}
              >
                <MenuExternalLink
                  href="https://courses.dagster.io/"
                  icon="graduation_cap"
                  text="Dagster University"
                />
              </div>
              {showContactSales ? (
                <MenuExternalLink
                  href="https://dagster.io/contact"
                  icon="open_in_new"
                  text="Contact sales"
                />
              ) : null}
            </Menu>
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
