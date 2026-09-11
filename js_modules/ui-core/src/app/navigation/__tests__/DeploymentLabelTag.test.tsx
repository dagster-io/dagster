import {render, screen} from '@testing-library/react';

import {AppContext, AppContextValue} from '../../AppContext';
import {DeploymentLabelTag} from '../DeploymentLabelTag';

const renderTag = (context: Partial<AppContextValue>, collapsed = false) =>
  render(
    <AppContext.Provider
      value={{basePath: '', rootServerURI: '', telemetryEnabled: false, ...context}}
    >
      <DeploymentLabelTag collapsed={collapsed} />
    </AppContext.Provider>,
  );

describe('DeploymentLabelTag', () => {
  it('renders nothing without a label', () => {
    const {container} = renderTag({uiIntent: 'danger'});
    expect(container).toBeEmptyDOMElement();
  });

  it('renders the label', () => {
    renderTag({uiLabel: 'Production', uiIntent: 'danger'});
    expect(screen.getByText('Production')).toBeVisible();
  });

  it('falls back to the none intent for an unrecognized value', () => {
    const {container} = renderTag({uiLabel: 'Production', uiIntent: 'chartreuse'}, true);
    expect(container.querySelector('[data-intent]')).toHaveAttribute('data-intent', 'none');
  });

  it('keeps a recognized intent', () => {
    const {container} = renderTag({uiLabel: 'Production', uiIntent: 'warning'}, true);
    expect(container.querySelector('[data-intent]')).toHaveAttribute('data-intent', 'warning');
  });
});
