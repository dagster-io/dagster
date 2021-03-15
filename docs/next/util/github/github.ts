import { Octokit } from "@octokit/rest";
import { createAppAuth } from "@octokit/auth-app";
import crypto from "crypto";
import { encrypted } from "./private-key.enc";

const algorithm = "aes-128-cbc";
const decipher = crypto.createDecipheriv(
  algorithm,
  process.env.GITHUB_ENCRYPTION_KEY,
  process.env.GITHUB_ENCRYPTION_IV
);

export const getDecryptedPrivateKey = () => {
  let decrypted = decipher.update(encrypted, "base64", "utf8");

  decrypted += decipher.final("utf8");
  return decrypted;
};

const octokit = new Octokit({
  authStrategy: createAppAuth,
  auth: {
    appId: process.env.GITHUB_APP_ID,
    privateKey: getDecryptedPrivateKey(),
    clientId: process.env.GITHUB_CLIENT_ID,
    installationId: process.env.GITHUB_INSTALLATION_ID,
    clientSecret: process.env.GITHUB_CLIENT_SECRET,
  },
});

export const createGithubIssue = async ({
  title,
  body,
  labels = [],
  dryRun = false,
}: {
  title: string;
  body: string;
  labels: string[];
  dryRun: boolean;
}) => {
  if (dryRun) {
    return "https://github.com";
  }

  const issue = await octokit.issues.create({
    owner: process.env.GITHUB_OWNER,
    repo: process.env.GITHUB_REPO,
    title,
    body,
    labels: labels,
  });

  return issue.data.html_url;
};
