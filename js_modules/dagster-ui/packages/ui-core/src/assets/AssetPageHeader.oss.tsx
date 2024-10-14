// eslint-disable-next-line no-restricted-imports
import {BreadcrumbProps, Breadcrumbs2 as Breadcrumbs} from '@blueprintjs/popover2';
import {
  Box,
  Colors,
  Heading,
  Icon,
  IconWrapper,
  MiddleTruncate,
  PageHeader,
  Tooltip,
} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {showSharedToaster} from '../app/DomUtils';
import {useCopyToClipboard} from '../app/browser';
import {AnchorButton} from '../ui/AnchorButton';

type Props = Partial<React.ComponentProps<typeof PageHeader>> & {
  assetKey: {path: string[]};
  headerBreadcrumbs: BreadcrumbProps[];
  Title?: ({children}: {children: React.ReactNode}) => React.ReactNode;
  view: 'asset' | 'catalog';
};

const defaultTitleComponent = ({children}: {children: React.ReactNode}) => children;

export const AssetPageHeader = ({
  assetKey,
  headerBreadcrumbs,
  Title = defaultTitleComponent,
  view: _view,
  ...extra
}: Props) => {
  const copy = useCopyToClipboard();
  const copyableString = assetKey.path.join('/');
  const [didCopy, setDidCopy] = React.useState(false);
  const iconTimeout = React.useRef<ReturnType<typeof setTimeout>>();

  const performCopy = React.useCallback(async () => {
    if (iconTimeout.current) {
      clearTimeout(iconTimeout.current);
    }

    copy(copyableString);
    setDidCopy(true);
    await showSharedToaster({
      icon: 'done',
      intent: 'primary',
      message: 'Copied asset key!',
    });

    iconTimeout.current = setTimeout(() => {
      setDidCopy(false);
    }, 2000);
  }, [copy, copyableString]);

  const breadcrumbs = React.useMemo(() => {
    const list: BreadcrumbProps[] = [...headerBreadcrumbs];

    assetKey.path.reduce((accum: string, elem: string) => {
      const href = `${accum}/${encodeURIComponent(elem)}`;
      list.push({text: elem, href});
      return href;
    }, '/assets');

    return list;
  }, [assetKey.path, headerBreadcrumbs]);

  return (
    <PageHeader
      title={
        <Box flex={{alignItems: 'center', gap: 4}} style={{maxWidth: '600px'}}>
          <Title>
            <BreadcrumbsWithSlashes
              items={breadcrumbs}
              currentBreadcrumbRenderer={({text, href}) => (
                <span key={href}>
                  <TruncatedHeading>
                    {typeof text === 'string' ? <MiddleTruncate text={text} /> : text}
                  </TruncatedHeading>
                </span>
              )}
              breadcrumbRenderer={({text, href}) => (
                <span key={href}>
                  <TruncatedHeading>
                    <BreadcrumbLink to={href || '#'}>
                      {typeof text === 'string' ? <MiddleTruncate text={text} /> : text}
                    </BreadcrumbLink>
                  </TruncatedHeading>
                </span>
              )}
              $numHeaderBreadcrumbs={headerBreadcrumbs.length}
              popoverProps={{
                minimal: true,
                modifiers: {offset: {enabled: true, options: {offset: [0, 8]}}},
                popoverClassName: 'dagster-popover',
              }}
            />
            {copyableString ? (
              <Tooltip placement="bottom" content="Copy asset key">
                <CopyButton onClick={performCopy}>
                  <Icon
                    name={didCopy ? 'copy_to_clipboard_done' : 'copy_to_clipboard'}
                    color={Colors.accentGray()}
                  />
                </CopyButton>
              </Tooltip>
            ) : undefined}
          </Title>
        </Box>
      }
      {...extra}
    />
  );
};

const TruncatedHeading = styled(Heading)`
  max-width: 300px;
  overflow: hidden;
`;

const CopyButton = styled.button`
  border: none;
  background: transparent;
  cursor: pointer;
  padding: 3px;
  margin-top: 2px;

  :focus {
    outline: none;
  }

  ${IconWrapper} {
    transition: background-color 100ms linear;
  }

  :hover ${IconWrapper} {
    background-color: ${Colors.accentGrayHover()};
  }
`;

export const AssetGlobalLineageLink = () => (
  <Link to="/asset-groups">
    <Box flex={{gap: 4}}>
      <Icon color={Colors.linkDefault()} name="lineage" />
      View global asset lineage
    </Box>
  </Link>
);

export const AssetGlobalLineageButton = () => (
  <AnchorButton intent="primary" icon={<Icon name="lineage" />} to="/asset-groups">
    View asset lineage
  </AnchorButton>
);

// Only add slashes within the asset key path
const BreadcrumbsWithSlashes = styled(Breadcrumbs)<{$numHeaderBreadcrumbs: number}>`
  & li:nth-child(n + ${(p) => p.$numHeaderBreadcrumbs + 1})::after {
    background: none;
    font-size: 20px;
    font-weight: bold;
    color: ${Colors.textLighter()};
    content: '/';
    width: 8px;
    line-height: 16px;
  }
`;

const BreadcrumbLink = styled(Link)`
  color: ${Colors.textLight()};
  white-space: nowrap;

  :hover,
  :active {
    color: ${Colors.textLight()};
  }
`;
