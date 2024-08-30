const ALL_OPERATIONS = {
  train_model
}

async function run_operation() {
  const { asset_keys, extras: { operation_name, config } } = await getPipesContext()
  if (!(operation_name in ALL_OPERATIONS)) {
    setPipesMessages({ error: `Operation ${operation_name} not found` });
    return;
  }
  const operation = ALL_OPERATIONS[operation_name];
  const model = await operation(config);
  await setPipesMessages({
    method: "report_asset_materialization",
    params: {
      asset_key: asset_keys[0],
      data_version: null,
      metadata: {
        metrics: model.metrics ? { raw_value: model.metrics, type: "text" } : undefined,
        loss: { raw_value: model.loss, type: "text" },
      },
    },
  });
  return 0;
}

run_operation().then((result) => {
  process.exit(result);
});