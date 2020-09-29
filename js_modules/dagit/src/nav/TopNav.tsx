import {Breadcrumbs, Colors, IBreadcrumbProps, Tabs, Tab} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

interface TopNavProps {
  activeTab?: string;
  breadcrumbs: IBreadcrumbProps[];
  tabs?: {text: string; href: string}[];
}

export const TopNav = (props: TopNavProps) => {
  const {activeTab, breadcrumbs, tabs} = props;
  return (
    <PipelineTabBarContainer>
      <BreadcrumbContainer>
        <Breadcrumbs items={breadcrumbs} />
      </BreadcrumbContainer>
      {tabs ? (
        <Tabs large selectedTabId={activeTab}>
          {tabs.map((tab) => {
            const {href, text} = tab;
            return <Tab key={text} id={text} title={<Link to={href}>{text}</Link>} />;
          })}
        </Tabs>
      ) : null}
    </PipelineTabBarContainer>
  );
};

const BreadcrumbContainer = styled.div`
  margin-right: 40px;
  padding: 4px 0;
`;

const PipelineTabBarContainer = styled.div`
  align-items: center;
  background: ${Colors.LIGHT_GRAY4};
  border-bottom: 1px solid ${Colors.GRAY5};
  display: flex;
  min-height: 46px;
  padding: 4px 16px 0;
`;
