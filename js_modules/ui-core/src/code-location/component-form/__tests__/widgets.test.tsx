import {widgets} from '../widgets';

describe('widget registry', () => {
  it('registers the custom widgets keyed to the ui:widget values the form schema emits', () => {
    expect(widgets.cron).toBeDefined();
    expect(widgets.date).toBeDefined();
    expect(widgets.secret).toBeDefined();
  });
});
