import * as util from 'util';
import { promises as fs } from "fs";
import { inflate } from 'zlib';

const inflateAsync = util.promisify(inflate);


/**
 * Decodes, decompresses, and parses the data sent by Dagster
 */
async function _decodeParam(value) {
  if (!value) {
    return null;
  }
  const decoded = Buffer.from(value, "base64");
  const decompressed = await inflateAsync(decoded);
  return JSON.parse(decompressed.toString("utf-8"));
}

/**
 * Extracts the context from the file defined by `DAGSTER_PIPES_CONTEXT`
 */
async function getPipesContext() {
  const encodedPipesContextParam = process.env.DAGSTER_PIPES_CONTEXT;
  const decodedPipesContextParam = await _decodeParam(encodedPipesContextParam);
  if (!decodedPipesContextParam) {
    return null;
  }
  return await fs.readFile(decodedPipesContextParam.path, "utf-8")
    .then((data) => JSON.parse(data));
}

/**
 * Writes JSON messages to the file defined by `DAGSTER_PIPES_MESSAGES`
 */
async function setPipesMessages(message) {
  const encodedPipesMessagesParam = process.env.DAGSTER_PIPES_MESSAGES;
  const decodedPipesMessagesParam = await _decodeParam(encodedPipesMessagesParam);
  if (!decodedPipesMessagesParam) {
    return null;
  }
  const path = decodedPipesMessagesParam.path;
  await fs.appendFile(path, JSON.stringify(message) + "\n");
}
