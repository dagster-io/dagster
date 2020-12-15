import {Icon, Breadcrumbs, Colors, IBreadcrumbProps, Tabs, Tab} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {Group} from 'src/ui/Group';

export interface TopNavProps {
  activeTab?: string;
  breadcrumbs: IBreadcrumbProps[];
  tabs?: {text: string; href: string}[];
}

export const TopNav = (props: TopNavProps) => {
  const {activeTab, breadcrumbs, tabs} = props;
  const lastBreadcrumb = breadcrumbs.length - 1;
  const items = breadcrumbs.map((breadcrumb, ii) => {
    const {text, href, icon} = breadcrumb;
    const isLast = lastBreadcrumb === ii;
    const content = (
      <Group direction="row" spacing={2} alignItems="center">
        {icon ? (
          <BreadcrumbIcon
            icon={icon}
            iconSize={14}
            color={isLast ? Colors.DARK_GRAY3 : Colors.GRAY1}
          />
        ) : null}
        <BreadcrumbText isLink={!!href} isLast={isLast}>
          {text}
        </BreadcrumbText>
      </Group>
    );
    return {text: href ? <BreadcrumbLink to={href}>{content}</BreadcrumbLink> : content};
  });

  return (
    <Container>
      <BreadcrumbContainer>
        <Breadcrumbs items={items} />
      </BreadcrumbContainer>
      {tabs ? (
        <Tabs large={false} selectedTabId={activeTab}>
          {tabs.map((tab) => {
            const {href, text} = tab;
            return <Tab key={text} id={text} title={<Link to={href}>{text}</Link>} />;
          })}
        </Tabs>
      ) : null}
    </Container>
  );
};

const BreadcrumbLink = styled(Link)`
  color: ${Colors.GRAY1};
  text-decoration: none;

  &&:hover {
    color: ${Colors.DARK_GRAY1};
    text-decoration: none;
  }
`;

interface BreadcrumbTextProps {
  isLast: boolean;
  isLink: boolean;
}

const BreadcrumbIcon = styled(Icon)`
  display: block;
  margin: 0;
  padding: 0;
`;

const BreadcrumbText = styled.div<BreadcrumbTextProps>`
  ${({isLast, isLink}) => {
    if (isLink) {
      return null;
    }
    return `color: ${isLast ? Colors.DARK_GRAY3 : Colors.GRAY1};`;
  }}
  font-size: 14px;
  ${({isLast}) => (isLast ? 'font-weight: 600;' : null)}
`;

const BreadcrumbContainer = styled.div`
  margin-right: 40px;
`;

const Container = styled.div`
  background: ${Colors.LIGHT_GRAY4};
  border-bottom: 1px solid ${Colors.GRAY5};
  display: flex;
  flex: 0 0 auto;
  flex-wrap: wrap;
  padding: 2px 16px 0;
`;
