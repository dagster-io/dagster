---
title: The Test Zone
description: Tests for all components and features of markdoc and our custom Markdoc build.
---

# Headers

## Complex Header That You Definitely Want to Use an Anchor Link For {% #complex-header %} 

**Bold**

_Italic_

[Links](/docs/nodes)

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

## Admonitions

{% warning %} This is a warning {% /warning %}

{% note %} This is a note {% /note %}

## Buttons

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


{% warning %}
### Don't format the buttons like this!
` {% button link="https://dog.ceo/" %}`

`Click Me!`

`{% /button %}`

It causes an odd formatting issue.

{% button link="https://dog.ceo/" %} 
Click Me!
{% /button %}
{% /warning %}

### Button Container
The main use case I've seen for buttons in the docs is basically setting up multiple styling links in a row. Doing this requires putting buttons into a `ButtonContainer`

{% buttonContainer %} {% button link="https://dog.ceo/" style="primary" %} Click Me! {% /button %} {% button link="https://dog.ceo/" style="secondary" %} Click Me! {% /button %} {% button link="https://dog.ceo/" style="blurple" %} Click Me! {% /button %} {% /buttonContainer %}

## Crosses and Checks 
A cross looks like this {% cross /%} and a check looks like this {% check /%}.

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

{% badge text="Badgey the Badger" /%}

## Code Reference Links

{% codeReferenceLink filePath="examples/deploy_ecs" %}{% /codeReferenceLink %}

## Reference Tables

{% referenceTable %}
{% referenceTableItem propertyName="isolated_agents.enabled" %}
When enabled, agents are isolated and will not be able to access each
others' resources. See the
<a href="/dagster-plus/deployment/agents/running-multiple-agents#running-multiple-agents-in-different-environments">
Running multiple agents guide
</a>
for more information.
{% /referenceTableItem %}

{% referenceTableItem propertyName="Item 2" %}
If the markdown works, we should be able to see it render here.

- Lists
- **Should**
- *Work*
- Now

Do They?

Maybe.
{% /referenceTableItem %}

{% /referenceTable %}
