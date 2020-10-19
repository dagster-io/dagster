import {NonIdealState} from '@blueprintjs/core';
import React from 'react';
import {Redirect, Route, RouteComponentProps, Switch} from 'react-router-dom';

import {DagsterRepositoryContext} from 'src/DagsterRepositoryContext';

const InstanceRedirect = (props: RouteComponentProps<any>) => {
  const {location} = props;
  const path = `${location.pathname}${location.search}`;
  return <Redirect to={`/instance${path}`} />;
};

export const FallthroughRoot = () => {
  return (
    <Switch>
      <Route path={['/runs/(.*)?', '/assets/(.*)?', '/scheduler']} component={InstanceRedirect} />
      <DagsterRepositoryContext.Consumer>
        {(context) =>
          context?.repository?.pipelines.length ? (
            <Redirect to={`/pipeline/${context?.repository.pipelines[0].name}/`} />
          ) : (
            <Route render={() => <NonIdealState title="No pipelines" />} />
          )
        }
      </DagsterRepositoryContext.Consumer>
    </Switch>
  );
};
