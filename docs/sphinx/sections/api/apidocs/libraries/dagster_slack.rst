.. role:: raw-html-m2r(raw)
   :format: html

Slack (dagster_slack)
---------------------

:raw-html-m2r:`<img src="https://user-images.githubusercontent.com/609349/57994610-c581f680-7a72-11e9-85cd-41fd649cc26d.png" />`

|

This library provides an integration with Slack, to support posting messages in your company's Slack workspace.

|

Presently, it provides a thin wrapper on the Slack client API `chat.postMessage <https://api.slack.com/methods/chat.postMessage>`_.

|

To use this integration, you'll first need to create a Slack App for it.


#.
   **Create App**\ : Go to `https://api.slack.com/apps <https://api.slack.com/apps>`_ and click "Create New App":

   :raw-html-m2r:`<img width=200px src="https://user-images.githubusercontent.com/609349/57993925-d3824800-7a6f-11e9-8618-bdd1611f15a4.png" />`

#.
   **Install App**\ : After creating an app, on the left-hand side of the app configuration, click "Bot Users", and then create a bot user. Then, click "Install App" on the left hand side, and finally "Install App to Workspace".

#.
   **Bot Token**\ : Once finished, this will create a new bot token for your bot/workspace:

   :raw-html-m2r:`<img width=600px src="https://user-images.githubusercontent.com/609349/57994422-ed248f00-7a71-11e9-9cbc-f6869ed33315.png" />`

Copy this bot token and put it somewhere safe; see `Safely Storing Credentials
<https://api.slack.com/docs/oauth-safety>`_ for more on this topic.


.. currentmodule:: dagster_slack

.. autodata:: slack_resource
  :annotation: ResourceDefinition
