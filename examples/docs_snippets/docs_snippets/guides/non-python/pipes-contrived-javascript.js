import * as tf from '@tensorflow/tfjs';

const CONFIG = { /* ... */ };

async function train_model() {
  const { path_to_data, data_config, path_to_model } = CONFIG;
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
}
