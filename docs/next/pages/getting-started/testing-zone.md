---
title: The Test Zone
description: Tests for all components and features of markdoc and our custom Markdoc build.
---

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

# Custom Markdoc Tags
We've extended markdown with custom tags that let us make the docs richer and more interactive.

## Admonitions

Two types of admonitions are available. Warnings and notes.

`{% warning %} This is a warning {% /warning %}`

{% warning %} This is a warning {% /warning %}

`{% note %} This is a note {% /note %}`

{% note %} This is a note {% /note %}

## Buttons
Buttons are basically just links that are styled to look neat to the user and work for making links stand out.

We have a few different styles of buttons that all do the same thing.

### Default

`{% button link="https://dog.ceo/" %} Click Me! {% /button %}`

{% button link="https://dog.ceo/" %} Click Me! {% /button %}

### Primary

`{% button link="https://dog.ceo/" style="primary" %} Click Me! {% /button %}`

{% button link="https://dog.ceo/" style="primary" %} Click Me! {% /button %}

### Secondary

`{% button link="https://dog.ceo/" style="secondary" %} Click Me! {% /button %}`

{% button link="https://dog.ceo/" style="secondary" %} Click Me! {% /button %}

### Blurple

` {% button link="https://dog.ceo/" style="blurple" %} Click Me! {% /button %} `

{% button link="https://dog.ceo/" style="blurple" %} Click Me! {% /button %}

### Button Container
The main use case I've seen for buttons in the docs is basically setting up multiple styling links in a row. Doing this requires putting buttons into a `ButtonContainer`

{% buttonContainer %} {% button link="https://dog.ceo/" style="primary" %} Click Me! {% /button %} {% button link="https://dog.ceo/" style="secondary" %} Click Me! {% /button %} {% button link="https://dog.ceo/" style="blurple" %} Click Me! {% /button %} {% /buttonContainer %}

## Crosses and Checks 
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
We've got a tag that handles making sure images are pretty, optimized, and accessible.

`{% image src="/images/some-image.png" width=300 height=200 alt="Text for screenreaders. Usually you want to describe things here." /%}`

<!-- {% image src="/images/concepts/assets/asset-activity-observation.png" width=300 height=200 alt="Text for screenreaders. Usually you want to describe things here." /%} -->

{% image src="/images/concepts/assets/asset-activity-observation.png" width=1758 height=1146 alt="Text go here" /%}


## Badges

`{% badge text="Badgey the Badger" /%}` lets you put a custom badge onto the page like this. {% badge text="Badgey the Badger" /%}

### API Status Badges
We've also got a bunch of badges that you can use to indicate the level of support an API or feature has.

There are three types of badges:

- `{% experimental /%}` {% experimental /%}
- `{% deprecated /%}` {% deprecated /%}
- `{% legacy /%}` {% legacy /%}

## Code Reference Links

Code reference links let you point to a specific file in the codebase. They're useful for linking to examples or reference implementations.

`{% codeReferenceLink filePath="examples/deploy_ecs" /%}`

{% codeReferenceLink filePath="examples/deploy_ecs" /%}


You can also add text to the link like this:

`{% codeReferenceLink filePath="examples/deploy_ecs" %}Check out our code on Github.{% /codeReferenceLink %}`

{% codeReferenceLink filePath="examples/deploy_ecs" %}Check out our code on Github.{% /codeReferenceLink %}

## Reference Tables

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
{% /referenceTableItem %}

{% /referenceTable %}

## Article Lists

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
