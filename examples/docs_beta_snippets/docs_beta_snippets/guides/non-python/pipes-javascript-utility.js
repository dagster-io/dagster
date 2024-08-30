import * as util from 'util';
import { promises as fs } from "fs";
import { inflate } from 'zlib';

const inflateAsync = util.promisify(inflate);

async function _decodeParam(value) {
  if (!value) {
    return null;
  }
  // Decode from base64 and unzip
  const decoded = Buffer.from(value, "base64");
  const decompressed = await inflateAsync(decoded);
  // Deserialize to JSON
  return JSON.parse(decompressed.toString("utf-8"));
}

async function getPipesContext() {
  // get the env var value for where the pipes context is stored
  const encodedPipesContextParam = process.env.DAGSTER_PIPES_CONTEXT;
  // decove the value to get the input file path
  const decodedPipesContextParam = await _decodeParam(encodedPipesContextParam);
  if (!decodedPipesContextParam) {
    return null;
  }
  return await fs.readFile(decodedPipesContextParam.path, "utf-8")
    .then((data) => JSON.parse(data));
}

async function setPipesMessages(message) {
  // get the env var value for where the pipes message is stored
  const encodedPipesMessagesParam = process.env.DAGSTER_PIPES_MESSAGES;
  // decode the value to get the output file path
  const decodedPipesMessagesParam = await _decodeParam(encodedPipesMessagesParam);
  if (!decodedPipesMessagesParam) {
    return null;
  }
  const path = decodedPipesMessagesParam.path;
  await fs.appendFile(path, JSON.stringify(message) + "\n");
}