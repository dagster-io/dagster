import {render, screen} from '@testing-library/react';
import {useContext} from 'react';

import {CloudOSSContext} from '../../app/CloudOSSContext';
import {buildRunQueueConfig} from '../../graphql/builders';
import {RunConcurrencyContent} from '../InstanceConcurrency';
import {useRunQueueConfig} from '../useRunQueueConfig';

jest.mock('../useRunQueueConfig', () => ({
  useRunQueueConfig: jest.fn(),
}));

jest.mock('@dagster-io/ui-components/editor', () => ({
  StyledRawCodeMirror: () => <div />,
}));

const mockUseRunQueueConfig = useRunQueueConfig as jest.MockedFunction<typeof useRunQueueConfig>;

// Spread the context default rather than enumerating feature flags, so new
// required flags don't break this fixture.
const BranchDeploymentContext = ({children}: {children: React.ReactNode}) => {
  const value = useContext(CloudOSSContext);
  return (
    <CloudOSSContext.Provider value={{...value, isBranchDeployment: true}}>
      {children}
    </CloudOSSContext.Provider>
  );
};

describe('RunConcurrencyContent', () => {
  it('renders the max concurrent runs value on non-branch deployments', async () => {
    const runQueueConfig = buildRunQueueConfig({
      maxConcurrentRuns: 12,
      tagConcurrencyLimitsYaml: null,
    });
    mockUseRunQueueConfig.mockReturnValue(runQueueConfig);

    render(<RunConcurrencyContent hasRunQueue runQueueConfig={runQueueConfig} />);

    expect(await screen.findByText('Max concurrent runs:')).toBeVisible();
    expect(await screen.findByText('12')).toBeVisible();
    expect(screen.queryByText(/all branch deployments/)).toBeNull();
  });

  it('hides the -1 sentinel on branch deployments and shows the all-branch limit', async () => {
    const runQueueConfig = buildRunQueueConfig({
      maxConcurrentRuns: -1,
      maxConcurrentRunsAllBranchDeployments: 50,
      tagConcurrencyLimitsYaml: null,
    });
    mockUseRunQueueConfig.mockReturnValue(runQueueConfig);

    render(
      <BranchDeploymentContext>
        <RunConcurrencyContent hasRunQueue runQueueConfig={runQueueConfig} />
      </BranchDeploymentContext>,
    );

    expect(await screen.findByText('Max concurrent runs (all branch deployments):')).toBeVisible();
    expect(await screen.findByText('50')).toBeVisible();
    expect(screen.queryByText('Max concurrent runs (this branch deployment):')).toBeNull();
    expect(screen.queryByText('-1')).toBeNull();
  });

  it('shows the per-branch limit on branch deployments when one is set', async () => {
    const runQueueConfig = buildRunQueueConfig({
      maxConcurrentRuns: 10,
      maxConcurrentRunsAllBranchDeployments: 50,
      tagConcurrencyLimitsYaml: null,
    });
    mockUseRunQueueConfig.mockReturnValue(runQueueConfig);

    render(
      <BranchDeploymentContext>
        <RunConcurrencyContent hasRunQueue runQueueConfig={runQueueConfig} />
      </BranchDeploymentContext>,
    );

    expect(await screen.findByText('Max concurrent runs (all branch deployments):')).toBeVisible();
    expect(await screen.findByText('50')).toBeVisible();
    expect(await screen.findByText('Max concurrent runs (this branch deployment):')).toBeVisible();
    expect(await screen.findByText('10')).toBeVisible();
  });
});
