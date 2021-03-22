import { App, AppMentionEvent, LogLevel } from "@slack/bolt";

import { WebClient } from "@slack/web-api";
import { createGithubIssue } from "./github/github";
import { promises as fs } from "fs";
import path from "path";

const DOCS_TRIGGER = "docs";
const ISSUE_TRIGGER = "issue";

const issueTemplates = {
  [DOCS_TRIGGER]: "docs-issue-template.md",
  [ISSUE_TRIGGER]: "issue-template.md",
};

const repliesAsString = async (
  client: WebClient,
  channel: string,
  thread_ts: string
) => {
  const replies = await client.conversations.replies({
    channel,
    ts: thread_ts,
  });
  const { messages } = replies;

  // @ts-ignore
  const messageText = messages.map(
    (message) => `${message.user}: ${message.text}`
  );
  return messageText.join("\n");
};

const threadTimeStampFromEvent = (event: AppMentionEvent) => {
  return event.thread_ts ? event.thread_ts : event.ts;
};

const getContextFromEvent = async (event: AppMentionEvent) => {
  const thread_ts = threadTimeStampFromEvent(event);
  const channel = event.channel;

  return { thread_ts, channel };
};

export default function (receiver) {
  const app = new App({
    receiver,
    token: process.env.SLACK_BOT_TOKEN,
    logLevel: LogLevel.DEBUG,
  });

  app.event("app_mention", async ({ event, say, client }) => {
    if (
      event.text.includes(DOCS_TRIGGER) ||
      event.text.includes(ISSUE_TRIGGER)
    ) {
      const trigger = event.text.includes(DOCS_TRIGGER)
        ? DOCS_TRIGGER
        : ISSUE_TRIGGER;
      const { channel, thread_ts } = await getContextFromEvent(event);
      const message = event.text.substring(
        event.text.indexOf(trigger) + trigger.length + 1
      );
      const repliesString = await repliesAsString(client, channel, thread_ts);
      const { permalink } = await client.chat.getPermalink({
        channel,
        message_ts: thread_ts,
      });

      const template = (
        await fs.readFile(
          path.resolve("util", "github", issueTemplates[trigger])
        )
      ).toString();

      const values = {
        message,
        permalink,
        replies: repliesString,
      };

      let githubIssueBody = template;
      for (const [key, value] of Object.entries(values)) {
        githubIssueBody = githubIssueBody.replace("{{ " + key + " }}", value);
      }

      const issue = await createGithubIssue({
        body: githubIssueBody,
        title: `${trigger === DOCS_TRIGGER ? "[Content Gap] " : ""}${message}`,
        labels: trigger === DOCS_TRIGGER ? ["documentation"] : [],
        dryRun: event.text.includes("--skip-issue"),
      });

      await say({ text: `Created issue at: ${issue}`, thread_ts });
    }
  });
}
