---
title: The Test Zone
description: Tests for all components and features of markdoc and our custom Markdoc build.
---

# Headers

## Complex Header That You Definitely Want to Use an Anchor Link For {% #complex-header %} 

**Bold**

_Italic_

[Links](/docs/nodes)

![Images](/logo.svg)

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



### Don't format the buttons like this!
` {% button link="https://dog.ceo/" %}`

`Click Me!`

`{% /button %}`

Or else they look like this.

{% button link="https://dog.ceo/" %} 
Click Me! 
{% /button %}