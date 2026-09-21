import * as tf from '@tensorflow/tfjs';

async function train_model() {
  // highlight-start
  // Get configuration from Dagster instead of `CONFIG` object
  const { asset_keys, extras: { path_to_data, data_config, path_to_model } } = await getPipesContext()

  setPipesMessages({ info: `Materializing ${asset_keys}` });
  // highlight-end

  const dataset = await tf.data.csv(path_to_data, data_config).map(({ xs, ys }) => {
    return {
      xs: tf.tensor2d(Object.values(xs), [Object.values(xs).length, 1]),
      ys: tf.tensor2d(Object.values(ys), [Object.values(ys).length, 1])
    };
  })
  .batch(100);

  const model = tf.sequential()
  model.add(tf.layers.dense({units: 1, inputShape: [1]}));
  model.compile({loss: 'meanSquaredError', optimizer: 'sgd'});

  await model.fitDataset(dataset, {epochs: 250})
  await model.save(path_to_model);
  model.summary();

  // highlight-start
  // Report materialization to Dagster
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
  // highlight-end
}
