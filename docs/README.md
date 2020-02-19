To develop the Sphinx docs:

    make livehtml

To build for Gatsby:

    make gatsby

To check for broken links, run the local server (`make livehtml`), then run:

    wget --spider -r -nd -nv -nc http://127.0.0.1:8000

You can also use [linkchecker](https://github.com/linkchecker/linkchecker/tree/htmlparser-beautifulsoup),
which is much slower but friendlier.
    
    linkchecker http://127.0.0.1:8000
