Digital Mohalla (F26-188) - FYP-1 Mid-Evaluation Report, LaTeX source
======================================================================

Built on the distributed FYP-1 mid report template (F26_FYP1_Mid_Report_LaTeX_Complete).
fast-nuces-bs.cls and tikz-uml.sty are the distributed files, unmodified.

Structure:
main.tex                       preamble, title page, chapter order
chapters/                      one file per front-matter part, chapter and appendix
references/references.bib      bibliography (IEEEtran, numbered)
figures/diagrams/              design diagrams exported from the draw.io sources (vector PDF)
figures/drawio_links/          one link per diagram that opens it full size in draw.io
figures/wireframes/            wireframes W1-W7 (PNG)
figures/use_case_diagram.tex   core use case diagram (Figure 4.1), drawn in TikZ
ThesisFigs/FASTLogo.jpg        logo for the title page

Submitted PDF: F26_188_i230746_i230570_i230554.pdf (group 188; roll numbers in team order).

Compile (pdfLaTeX):
1. pdflatex main.tex
2. bibtex main
3. pdflatex main.tex
4. pdflatex main.tex

Works with MiKTeX, TeX Live and Overleaf (upload the folder or the zip, main document main.tex).

Diagrams:
Every diagram is shown whole on one page, upright, in a single figure. Diagrams that are too
large to read comfortably on an A4 page also carry a link, "Open the full-size diagram in draw.io",
under the figure. The link contains the complete .drawio file (draw.io "Export as URL" encoding),
so it opens exactly the diagram printed in the report in the diagrams.net viewer, where it can be
zoomed and inspected; nothing has to be hosted. The source path of each diagram is printed under
the link. To update a diagram: edit the .drawio file in docs/design/, export it again as PDF
(File > Export as > PDF, "Crop" ticked) into figures/diagrams/ under the same name, and
regenerate its link (File > Export as > URL, then paste it into the \href in figures/drawio_links/).
