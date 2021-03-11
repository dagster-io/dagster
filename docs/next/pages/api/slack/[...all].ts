import { HTTPReceiver, LogLevel } from "@slack/bolt";

import bolt from "../../../util/bolt";

const receiver = new HTTPReceiver({
  signingSecret: process.env.SLACK_SIGNING_SECRET,
  processBeforeResponse: true,
  endpoints: "/api/slack/events",
  logLevel: LogLevel.ERROR,
});

bolt(receiver);

export default receiver.requestListener;

export const config = {
  api: {
    bodyParser: false,
    externalResolver: true,
  },
};
