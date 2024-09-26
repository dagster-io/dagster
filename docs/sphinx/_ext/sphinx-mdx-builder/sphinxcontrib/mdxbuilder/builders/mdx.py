from os import path
from typing import Iterator

from docutils import nodes
from docutils.io import StringOutput

from sphinx.builders import Builder
from sphinx.util import logging
from sphinx.util.osutil import ensuredir

from ..writers.mdx import MdxWriter

logger = logging.getLogger(__name__)


class MdxBuilder(Builder):
    name = "mdx"
    format = "mdx"
    epilog: str = "______ [Finished writing mdx files for %(project)s to %(outdir)s] ______"
    allow_parallel = True
    file_suffix: str = ".mdx"
    link_suffix: str | None = None  # defaults to file_suffix

    def init(self):
        if self.config.mdx_file_suffix is not None:
            self.file_suffix = self.config.mdx_file_suffix
        if self.config.mdx_link_suffix is not None:
            self.link_suffix = self.config.mdx_link_suffix
        elif self.link_suffix is None:
            self.link_suffix = self.file_suffix

        def file_transform(docname: str) -> str:
            return docname + self.file_suffix

        def link_transform(docname: str) -> str:
            return docname + (self.link_suffix or self.file_suffix)

        self.file_transform = self.config.mdx_file_transform or file_transform
        self.link_transform = self.config.mdx_link_transform or link_transform

    def get_outdated_docs(self) -> Iterator[str]:
        for docname in self.env.found_docs:
            if docname not in self.env.all_docs:
                yield docname
                continue
            targetname = path.join(self.outdir, self.file_transform(docname))
            try:
                targetmtime = path.getmtime(targetname)
            except Exception:
                targetmtime = 0
            try:
                srcmtime = path.getmtime(path.join(self.env.srcdir, docname + self.file_suffix))
                if srcmtime > targetmtime:
                    yield docname
            except OSError:
                pass

    def get_target_uri(self, docname: str, typ: str | None = None) -> str:
        return self.link_transform(docname)

    def prepare_writing(self, docnames: set[str]) -> None:
        self.writer = MdxWriter(self)

    def write_doc(self, docname: str, doctree: nodes.document) -> None:
        destination = StringOutput(encoding="utf-8")
        self.writer.write(doctree, destination)
        outfilename = path.join(self.outdir, self.file_transform(docname))
        ensuredir(path.dirname(outfilename))
        try:
            with open(outfilename, "w", encoding="utf-8") as f:
                f.write(self.writer.output)
        except (IOError, OSError) as err:
            logger.warning(f"error writing file {outfilename}: {err}")
            raise err

    def finish(self):
        pass
