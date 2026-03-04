import {render, screen} from '@testing-library/react';

import {
  RunStatus,
  buildAssetLatestInfo,
  buildFailedToMaterializeEvent,
  buildMaterializationEvent,
  buildObservationEvent,
  buildRun,
} from '../../graphql/types';
import {AssetRecentUpdatesTrend} from '../AssetRecentUpdatesTrend';

jest.mock('../../ui/PezItem', () => ({
  ...jest.requireActual('../../ui/PezItem'),
  PezItem: ({color}: {color: string}) => <div style={{backgroundColor: color}}>pez {color}</div>,
}));

describe('AssetRecentUpdatesTrend', () => {
  it('should render for empty events list', async () => {
    render(<AssetRecentUpdatesTrend events={[]} />);
    const allPez = await screen.findAllByText(/pez/i);
    expect(allPez).toHaveLength(5);
    const allGray = await screen.findAllByText(/var\(--color-background-disabled\)/i);
    expect(allGray).toHaveLength(5);
  });

  it('should render for events list', async () => {
    const events = Array.from({length: 5}, (_, i) => {
      return buildMaterializationEvent({
        runId: `1-${i}`,
        timestamp: `${1000000 + i}`,
      });
    });
    render(<AssetRecentUpdatesTrend events={events} />);
    const allPez = await screen.findAllByText(/pez/i);
    expect(allPez).toHaveLength(5);
    const allGreen = await screen.findAllByText(/var\(--color-accent-green\)/i);
    expect(allGreen).toHaveLength(5);
  });

  it('should render for short events list', async () => {
    const events = Array.from({length: 2}, (_, i) => {
      return buildMaterializationEvent({
        runId: `1-${i}`,
        timestamp: `${1000000 + i}`,
      });
    });
    render(<AssetRecentUpdatesTrend events={events} />);
    const allPez = await screen.findAllByText(/pez/i);
    expect(allPez).toHaveLength(5);
    expect(allPez[0]).toHaveTextContent('pez var(--color-background-disabled)');
    expect(allPez[1]).toHaveTextContent('pez var(--color-background-disabled)');
    expect(allPez[2]).toHaveTextContent('pez var(--color-background-disabled)');
    expect(allPez[3]).toHaveTextContent('pez var(--color-accent-green)');
    expect(allPez[4]).toHaveTextContent('pez var(--color-accent-green)');
  });

  it('should handle cases where more than 5 events are provided', async () => {
    const events = Array.from({length: 10}, (_, i) => {
      return buildMaterializationEvent({
        runId: `1-${i}`,
        timestamp: `${1000000 + i}`,
      });
    });
    render(<AssetRecentUpdatesTrend events={events} />);
    const allPez = await screen.findAllByText(/pez/i);
    expect(allPez).toHaveLength(5);
    const allGreen = await screen.findAllByText(/var\(--color-accent-green\)/i);
    expect(allGreen).toHaveLength(5);
  });

  it('should handle latest info', async () => {
    const events = Array.from({length: 5}, (_, i) => {
      return buildMaterializationEvent({
        runId: `1-${i}`,
        timestamp: `${1000000 + i}`,
      });
    });
    const latestInfo = buildAssetLatestInfo({
      latestRun: buildRun({
        id: '1',
        status: RunStatus.SUCCESS,
        startTime: 1000000,
      }),
    });
    render(<AssetRecentUpdatesTrend latestInfo={latestInfo} events={events} />);
    const allPez = await screen.findAllByText(/pez/i);
    expect(allPez).toHaveLength(5);
    expect(allPez[0]).toHaveTextContent('pez var(--color-accent-green)');
    expect(allPez[1]).toHaveTextContent('pez var(--color-accent-green)');
    expect(allPez[2]).toHaveTextContent('pez var(--color-accent-green)');
    expect(allPez[3]).toHaveTextContent('pez var(--color-accent-green)');
    expect(allPez[4]).toHaveTextContent('pez var(--color-accent-blue)');
  });

  it('should handle failed to materialize event', async () => {
    const events = Array.from({length: 5}, (_, i) => {
      return buildFailedToMaterializeEvent({
        runId: `1-${i}`,
        timestamp: `${1000000 + i}`,
      });
    });
    render(<AssetRecentUpdatesTrend events={events} />);
    const allPez = await screen.findAllByText(/pez/i);
    expect(allPez).toHaveLength(5);
    const allRed = await screen.findAllByText(/var\(--color-accent-red\)/i);
    expect(allRed).toHaveLength(5);
  });

  it('should handle observation event', async () => {
    const events = Array.from({length: 5}, (_, i) => {
      return buildObservationEvent({
        runId: `1-${i}`,
        timestamp: `${1000000 + i}`,
      });
    });
    render(<AssetRecentUpdatesTrend events={events} />);
    const allPez = await screen.findAllByText(/pez/i);
    expect(allPez).toHaveLength(5);
    const allGreen = await screen.findAllByText(/var\(--color-accent-green\)/i);
    expect(allGreen).toHaveLength(5);
  });
});
