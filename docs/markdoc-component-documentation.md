---
title: Authoring Component Examples
description: This page shows off what each of the components we're using in our docs looks like.
---



This page contains examples of all of the native Markdoc node and the custom markdoc tags that we are using in our docs.

To see the rendered version of these tags, move this file into the `next/pages/getting-started` directory, run the local server for the site, and navigate to the `getting-started/markdoc-component-documentation` page in your browser.

# Header 1

## Header 2

### Header 3

#### Header 4

##### Header 5

## Regular text

When the wire was despatched he had a cup of tea; over it he told me of a diary kept by Jonathan Harker when abroad, and gave me a typewritten copy of it, as also of Mrs. Harker's diary at Whitby. "Take these," he said, "and study them well. When I have returned you will be master of all the facts, and we can then better enter on our inquisition. Keep them safe, for there is in them much of treasure. You will need all your faith, even you who have had such an experience as that of to-day. What is here told," he laid his hand heavily and gravely on the packet of papers as he spoke, "may be the beginning of the end to you and me and many another; or it may sound the knell of the Un-Dead who walk the earth. Read all, I pray you, with the open mind; and if you can add in any way to the story here told do so, for it is all-important. You have kept diary of all these so strange things; is it not so? Yes! Then we shall go through all these together when we meet." He then made ready for his departure, and shortly after drove off to Liverpool Street. I took my way to Paddington, where I arrived about fifteen minutes before the train came in.

## Complex Header Where You Definitely Want to Use an Anchor Link {% #complex-header %}

```
## Complex Header Where You Definitely Want to Use an
Anchor Link {\% #complex-header %}
```

# Vanilla Markdown Nodes

**Bold**

_Italic_

[Links](/docs/nodes)

Vanilla markdown images work, but we should really be using the image tag because it optimizes the images, makes them more accessible, and handles resizing them for us.
![Images](/images/concepts/assets/asset-activity-observation.png)

Lists
- Item 1
- Item 1
- Item 1

> Quotes

`Inline code`

```
Code fences
```

Markdoc doesn't have syntax highlighting out of the box. We're going to need to add that in. When it get's added in, this python code should be beautifully highlighted.

### BASH
```bash
python --version
pip --version
pip install dagster dagster-webserver
```

### Python
```python
import random

def magic_8_ball():
    responses = [
        "As I see it, yes.",
        "Ask again later.",
        "Better not tell you now.",
        "Cannot predict now.",
        "Don’t count on it.",
        "My reply is no.",
        "My sources say no.",
        "Outlook not so good.",
        "Outlook good.",
        "Reply hazy, try again.",
        "Yes – definitely.",
        "You may rely on it.",
        "Absolutely not!",
        "Go for it!",
        "No way, José!",
        "Oh, hell no!",
        "Hell yes!",
        "Yes, if you believe hard enough.",
        "No, but that shouldn't stop you.",
        "Why would you even ask that?"
    ]

    while True:
        question = input("Ask the Magic 8 Ball a question (type 'exit' to quit): ")
        if question.lower() == 'exit':
            print("Magic 8 Ball has left the chat.")
            break
        else:
            print(random.choice(responses))

if __name__ == "__main__":
    magic_8_ball()
```

### JSON
```json
{
  "name": "Dagster",
  "description": "A data orchestrator for machine learning, analytics, and ETL",
  "version": "0.13.0",
  "license": "Apache-2.0",
  "repository": {
    "type": "git",
  }
}
```

### YAML
```yaml
name: Dagster
description: A data orchestrator for machine learning, analytics, and ETL
version: 0.13.0
license: Apache-2.0
repository:
  type: git
```

### TOML
```toml
[package]
name = "dagster"
version = "0.13.0"
description = "A data orchestrator for machine learning, analytics, and ETL"
license = "Apache-2.0"
repository = { type = "git" }
```


# Custom Markdoc Tags
We've extended markdown with custom tags that let us make the docs richer and more interactive.

{% warning %}
There are two types of tags.
- Inline tags can be used in the middle of a line of and look like this `{% inlineTag %} Inline tag contents {% /inline tags %}`
- Block tags can be used to wrap around a block of content and look like this:

`{% blockTag %}`

`Block tag contents`

`{% /blockTag %}`

The docs for each tag calls out whether it can be used inline, as a block, or both.

{% /warning %}

## Admonitions : Block

Two types of admonitions are available. Warnings and notes.

`{% warning %} This is a warning {% /warning %}`

{% warning %}
This is a warning
{% /warning %}

`{% note %} This is a note {% /note %}`

{% note %}
This is a note
{% /note %}

## Button : Block
Buttons are basically just links that are styled to look neat to the user and work for making links stand out.

We have a few different styles of buttons that all do the same thing.

### Default

`{% button link="https://dog.ceo/" %} Click Me! {% /button %}`

{% button link="https://dog.ceo/" %}
Click Me!
{% /button %}

### Primary

`{% button link="https://dog.ceo/" style="primary" %} Click Me! {% /button %}`

{% button link="https://dog.ceo/" style="primary" %}
Click Me!
{% /button %}

### Secondary

`{% button link="https://dog.ceo/" style="secondary" %} Click Me! {% /button %}`

{% button link="https://dog.ceo/" style="secondary" %}
Click Me!
{% /button %}

### Blurple

` {% button link="https://dog.ceo/" style="blurple" %} Click Me! {% /button %} `

{% button link="https://dog.ceo/" style="blurple" %}
Click Me!
{% /button %}

### Button Container : Block
The main use case I've seen for buttons in the docs is basically setting up multiple styling links in a row. Doing this requires putting buttons into a `ButtonContainer`

{% buttonContainer %}
{% button link="https://dog.ceo/" style="primary" %}
Click Me!
{% /button %}
{% button link="https://dog.ceo/" style="secondary" %}
Click Me!
{% /button %}
{% button link="https://dog.ceo/" style="blurple" %}
Click Me!
{% /button %}
{% /buttonContainer %}

## Crosses and Checks : Inline
You can invoke a cross with this tag `{% cross /}%` and it looks like this {% cross /%}. You can invoke checks with this tag `{% check /}%` and it looks like this {% check /%}.

Crosses and checks can also be used in lists:
- {% check /%} Completed task
- {% cross /%} Incomplete task
- {% cross /%} Super Incomplete task

You can also put crosses and checks into headers

### This is a header with a check {% check /%}
Which is pretty neat.

### This is a header with a cross {% cross /%}
Which is also pretty neat.

## Images
In the old MDX way of doing things, images were a bit of a pain. You had to either manually specify the height and width of the image or run a script (`make MDX-format`) to do it for you.

Document preprocessors like this have a number of issues such as being slow, error-prone, and making edits to the docs more difficult.

To that end, I've opted to extended the default markdoc image node to automatically determine the height and width of the image during the transform step and use that to instantiate the image using the `Next/Image` component. Doing this allows us to retain the benefits of our current make script approach while also preserving the easy authoring experience of vanilla markdown.

So, the default way to use images is like this:

`![Alt Text Goes Here](/images/concepts/assets/asset-activity-observation.png)`

and outputs like this:

![Alt Text Goes Here](/images/concepts/assets/asset-activity-observation.png)

The default markdown syntax is effectively the same as using this tag manually: `{% image src="/images/concepts/assets/asset-activity-observation.png" alt="Text go here" /%}`

Which yields this:

{% image src="/images/concepts/assets/asset-activity-observation.png" alt="Text go here" /%}

You can also specify the width and height of the image like this:

`{% image src="/images/concepts/assets/asset-activity-observation.png" width=1758 height=1146 alt="Text go here" /%}`

Which yields this:

{% image src="/images/concepts/assets/asset-activity-observation.png" width=1758 height=1146 alt="Text go here" /%}

The cool part about all of this is that it removes the need to run `make MDX-format` for images as it handles assigning a size to the image as part of page rendering rather than as a batch text-preprocess that gets performed on the docs.

## Badges : Inline

`{% badge text="Badgey the Badger" /%}` lets you put a custom badge onto the page like this. {% badge text="Badgey the Badger" /%}

### API Status Badges
We've also got a bunch of badges that you can use to indicate the level of support an API or feature has.

There are the available badges:

- `{% experimental /%}` {% experimental /%}
- `{% preview /%}` {% preview /%}
- `{% beta /%}` {% beta /%}
- `{% deprecated /%}` {% deprecated /%}
- `{% superseded /%}` {% superseded /%}
- `{% legacy /%}` {% legacy /%}

## Code Reference Links : Block

Code reference links let you point to a specific file in the codebase. They're useful for linking to examples or reference implementations.

`{% codeReferenceLink filePath="examples/deploy_ecs" /%}`

{% codeReferenceLink filePath="examples/deploy_ecs" /%}

## Reference Tables : Block

{% referenceTable %}
{% referenceTableItem propertyName="isolated_agents.enabled" %}
The cool thing about these tables that will spare people working with them a lot of grief is that they support vanilla markdown and custom tags while the MDX implementation only supported HTML.

They still aren't the best thing to work with, but this is a night and day different from having to keep track of raw HTML while authoring.
{% /referenceTableItem %}

{% referenceTableItem propertyName="Item 2" %}

**Bold**

_Italic_

[Links](/docs/nodes)

Vanilla markdown images work, but we should really be using the image tag because it optimizes the images, makes them more accessible, and handles resizing them for us.
<!-- ![Images](/images/concepts/assets/asset-activity-observation.png) -->

Lists
- Item 1
- Item 1
- Item 1

> Quotes

`Inline code`

```
Code fences
```
{% /referenceTableItem %}

{% /referenceTable %}

## Article Lists : Block

Authors can use article lists.

They work like this:
`{% articleList %}`

  `{% articleListItem title="Software-defined Assets" href="/concepts/assets/software-defined-assets" /%}`

  `{% articleListItem title="Graph-backed Assets" href="/concepts/assets/graph-backed-assets" /%}`

  `{% articleListItem title="Multi-assets" href="/concepts/assets/multi-assets" /%}`

  `{% articleListItem title="Asset jobs" href="/concepts/assets/asset-jobs" /%}`

  `{% articleListItem title="Asset observations" href="/concepts/assets/asset-observations" /%}`

  `{% articleListItem title="Asset selection syntax" href="/concepts/assets/asset-selection-syntax" /%}`

  `{% articleListItem title="Asset checks" href="/concepts/assets/asset-checks" /%}`

  `{% articleListItem title="External assets (Experimental)" href="/concepts/assets/external-assets" /%}`

`{% /articleList %}`

{% articleList %}
  {% articleListItem title="Software-defined Assets" href="/concepts/assets/software-defined-assets" /%}
  {% articleListItem title="Graph-backed Assets" href="/concepts/assets/graph-backed-assets" /%}
  {% articleListItem title="Multi-assets" href="/concepts/assets/multi-assets" /%}
  {% articleListItem title="Asset jobs" href="/concepts/assets/asset-jobs" /%}
  {% articleListItem title="Asset observations" href="/concepts/assets/asset-observations" /%}
  {% articleListItem title="Asset selection syntax" href="/concepts/assets/asset-selection-syntax" /%}
  {% articleListItem title="Asset checks" href="/concepts/assets/asset-checks" /%}
  {% articleListItem title="External assets (Experimental)" href="/concepts/assets/external-assets" /%}
{% /articleList %}

## CodeSnippets : Block

The `CodeSnippet` component allows you to easily include code snippets from your project files into your documentation. Here are various ways to use it, along with examples:

### Basic File Retrieval
This example shows how to include an entire file as a code snippet. It's useful when you want to showcase a complete file without any modifications.

`{% codeSnippet file="concepts/assets/asset_group_argument.py" lang="python" /%}`

{% codeSnippet file="concepts/assets/asset_group_argument.py" lang="python" /%}

### Specific Line Range
You can specify exact lines to include from a file. This is helpful when you want to focus on a particular section of code without showing the entire file.

`{% codeSnippet file="concepts/assets/asset_group_argument.py" lang="python" lines="5-15" /%}`

{% codeSnippet file="concepts/assets/asset_group_argument.py" lang="python" lines="5-15" /%}

### Multiple Line Ranges
For more complex scenarios, you can include multiple, non-contiguous line ranges. This allows you to showcase different parts of a file while skipping irrelevant sections.

`{% codeSnippet file="concepts/assets/asset_group_argument.py" lang="python" lines="1-5,10-15" /%}`

{% codeSnippet file="concepts/assets/asset_group_argument.py" lang="python" lines="1-5,10-15" /%}

### Start After a Specific String
This option lets you start the snippet after a specific string in the file. It's useful for beginning your snippet at a particular point, like after a comment or function definition.

`{% codeSnippet file="concepts/assets/asset_group_argument.py" lang="python" startafter="# start_example" /%}`

{% codeSnippet file="concepts/assets/asset_group_argument.py" lang="python" startafter="# start_example" /%}

### End Before a Specific String
Similar to `startafter`, this option lets you end the snippet before a specific string. It's helpful for showing code up to a certain point.

`{% codeSnippet file="concepts/assets/asset_group_argument.py" lang="python" endbefore="# end_example" /%}`

{% codeSnippet file="concepts/assets/asset_group_argument.py" lang="python" endbefore="# end_example" /%}

### Combine Start and End
You can use both `startafter` and `endbefore` to extract a specific section of code between two markers. This is great for showcasing a particular function or code block.

`{% codeSnippet file="concepts/assets/asset_group_argument.py" lang="python" startafter="# start_example" endbefore="# end_example" /%}`

{% codeSnippet file="concepts/assets/asset_group_argument.py" lang="python" startafter="# start_example" endbefore="# end_example" /%}

### Dedenting
The `dedent` option allows you to remove a specified number of leading spaces from each line. This is useful for adjusting the indentation of your snippet to match your documentation's formatting.

`{% codeSnippet file="concepts/assets/asset_group_argument.py" lang="python" dedent=4 /%}`

{% codeSnippet file="concepts/assets/asset_group_argument.py" lang="python" dedent=4 /%}

### Disable Trimming
By default, the component trims whitespace from the beginning and end of the snippet. You can disable this behavior if you need to preserve exact whitespace.

`{% codeSnippet file="concepts/assets/asset_group_argument.py" lang="python" trim=false /%}`

{% codeSnippet file="concepts/assets/asset_group_argument.py" lang="python" trim=false /%}

### Combining Multiple Parameters
You can combine multiple parameters for fine-grained control over your snippets. This example shows how to select specific lines, start after a marker, dedent, and trim the result.

`{% codeSnippet file="concepts/assets/asset_group_argument.py" lang="python" lines="5-15" startafter="# start_example" dedent=4 trim=true /%}`

{% codeSnippet file="concepts/assets/asset_group_argument.py" lang="python" lines="5-15" startafter="# start_example" dedent=4 trim=true /%}

By using these options, you can flexibly include and format code snippets to best suit your needs.
