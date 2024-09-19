import {Alert} from '@dagster-io/ui-components';

export const DeclarativeAutomationBanner = () => {
  return (
    <Alert
      intent="info"
      title="[Experimental] Dagster can automatically materialize assets when criteria are met."
      description={
        <>
          Automation conditions enable a declarative approach to asset automation. Instead of
          defining imperative workflows to execute your assets, you just describe the conditions
          under which they should be executed.{' '}
          <a
            href="https://docs.dagster.io/concepts/automation/declarative-automation"
            target="_blank"
            rel="noreferrer"
          >
            Learn more about declarative automation here
          </a>
          .
        </>
      }
    />
  );
};
