#!/usr/bin/env python3

#      #!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import re
import logging
import codecs


import component
import dandr  # disassemble and reassemble
import processenvironments
import makeoutput
import utilities

#logging.basicConfig(filename='logging.log', format='%(levelname)s:%(module)s:%(funcName)s:  %(message)s', level=logging.INFO)
logging.basicConfig(filename='logging.log', format='%(levelname)s:%(module)s:%(funcName)s:%(lineno)d:  %(message)s', level=logging.DEBUG)
# logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
# logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

#################################
# First use the command-line arguments to set up the
# input and output files.
#################################

if not len(sys.argv) >= 3:
    print('To convert a LaTeX file to XML or HTML:')
    print('./sl2x.py inputfile outputdirectory [-a known_paper_code] [-p publisher] [-w writer] [-t target] [-v] [-k] [-f]')
    sys.exit()

# set up input file, output directory, and command line arguments
makeoutput.process_argv(sys.argv)

makeoutput.setup_input_files()

component.find_known_people()

##############
#  Need to write a description of how the program works.
############

#################################
#
# Set up the counters and the global variables that
# will hold the components of the document, and
# read in the contents of the LaTeX file,
#
#################################

component.initialize_counters()
component.initialize_environments()

try:
    component.documentcontents = component.inputfile.read()
except UnicodeDecodeError:
    component.source_encoding = 'iso-8859-1'
    component.inputfile = codecs.open(component.inputfilename,'r', component.source_encoding)
    component.documentcontents = component.inputfile.read()
    try:
        component.documentcontents = component.documentcontents.encode('utf-8',errors='replace')
    except UnicodeEncodeError:
        logging.warning("FONT ERROR in main file %s", component.documentcontents[:40])

###############################
#
# Separate the document into components, putting all the pieces
# into component.environment
# 
################################

component.documentcontents = dandr.initial_preparations(component.documentcontents)

# put the whole document into component.documentcontents
dandr.expand_input_files()
# not sure if we can get away with dandr.initial_preparations just once.
# some things, like utilities.other_alphabets_to_latex, haveto be done after
# all files are read in
component.documentcontents = dandr.initial_preparations(component.documentcontents)

if r"\begin{document}" in component.documentcontents:
    makeoutput.setup_output_files()
else:
    logging.critical("Source does not appear to be LaTeX; unable to convert.")
    logging.critical("The file begins:")
    logging.critical("%s", component.documentcontents[:2000])
    sys.exit()

makeoutput.saveoutputfile("everything1.tex",component.documentcontents)

component.documentcontents = dandr.separate_into_latex_components(component.documentcontents)
    # fix: does not really handle appendices

# extract things like component.graphicspath
dandr.find_global_parameters(component.preamble)

# find things like \unitlength (for pictures)
dandr.find_local_parameters(component.preamble)
# if people wrote good latex then we could delete the next line
dandr.find_local_parameters(component.documentcontents)

###############
# component.documentcontents now consists of only the
# main body # of the document:  everything between \maketitle
# and the bibliography.
#
# Now separate into sections, subsections, and subsubsections

component.documentcontents = dandr.separate_into_chapters_sections_etc(component.documentcontents)

top_level_only = component.documentcontents
thetopsections = re.findall("(SEC([0-9a-f]{40})END)",
                             component.documentcontents)
logging.info("top level: %s",top_level_only)

if component.frontmatter:
    dandr.maketopmatter()

##############
# Go through every component and extract sub-components.
# Every part of the document is its own separate piece, including
# pieces that contain other pieces.
# Every piece is labeled with a 40 hex digit sha1 code.
#
# First do this for environments which could be labeled.
# After extracting labels and numbering everything,
# extract the remaining environments.

dandr.separate_latex_environments(exclude=['class','layout'], separatemath=False)
dandr.separate_latex_math_macros()
dandr.separate_math_rows()
dandr.separate_latex_environments(exclude="all", separatemath=True)
dandr.separate_latex_environments(exclude="all", include="footnotes", separatemath=False)
dandr.process_math_environments()

###############
# Since every environment is separated, each component should have
# at most one LaTeX \label, so we extract those.  But not quite,
# because environments like enumerate can have more than one label,
# because each "row" can have a label.  Here we separate the
# enumerate and itemize environments, but that should be revisited
# and done in a more careful way.  Multiline math displays have the
# same issue.

dandr.separate_latex_rows()
#dandr.separate_math_rows()
dandr.separate_labels()

# now don't exclude class=layout
dandr.separate_latex_environments(separatemath=False)

# Some environments, like those containing images,
# need further processing after they are separated.
dandr.process_separated_environments()

processenvironments.processbibliography(component.bibliography)

# Since there can be images outside a figure environment, those will
# now appear in a paragraph.  So we scan all the paragraphs to look
# for \includegraphics.

dandr.separate_isolated_figures()   
    # should be redone as separate_includegraphics

##################
# Reassemble the whole document to determine the counter numbers.
#############
processenvironments.numberenvironments()

##################
# Associate each label to its codenumber.  This only works if we
# successfully separated the document into sufficiently small pieces,
# so that at most one label occurs in each component.

processenvironments.makelabels()

# Paragraphs: tricky because the only clue is a blank line.
# Now that all the labeled environments are extracted, look for
# paragraphs in those environments which can contain paragraphs.

dandr.separate_paragraphs()

# At this point all the environments are separated.  We give
# an sl2xID to each component.environment.  This will become
# its id in the HTML version.

processenvironments.make_sl2xID()

# macros in math mode are handled by MathJax.
# author macros in text must be expanded.
# authors can have macros in terms of other macros

for _ in range(2):
    logging.info("finding unexpanded macros")
    processenvironments.findunexpandedmacros()
    processenvironments.expand_author_macros()

if component.guess_terminology:
    processenvironments.convert_author_terminology()
processenvironments.extract_index_and_terminology()

processenvironments.expand_smart_references()

######################################
# That completes the disassembly phase: the entire document is in
# separate pieces labeled by a sha1 code in component.environment
#
# component.documentcontents contains a SECsha1code for each top level
# component (chapter or section).  These form the basis for the TOC.

##################
# There are two table of contents (TOC) styles:  paper and book.
# Papers are divided into sections.
# Books are divided into chapters, which are then divided into sections.
#
# This should be determined differently.  A long survey article
# should have tocstyle = "book".  Also, currently tocstyle is not
# actually used.
if component.toplevel == 0:
    component.tocstyle = "book"
else:
    component.tocstyle = "paper"

# put the TOC into component.thetoc
makeoutput.tocinhtml(component.toplevel,thetopsections)


##################################
# To create the html version of everything, we do these steps:
#
# 1) Copy all the component_separated into component.target .
# 2) Do some initial LaTeX substitutions on those components which
#    need LaTeX to HTML conversion. Examples include:
#    a) \tag{} in mathdisplay
#    b) Convert \ref{}, \eqref{}, and \cite{}
#    c) Convert ~, \emph, \terminology, and more .
# 3) Recursively expand sha1 codes and wrap in appropriate tags.
# 4) Write to the appropriate html files.
# 5) Write to the appropriate knowl files.
#################################

# Step 1) Make component.target from component_separated.

# first just copy every component_separated into component.target
processenvironments.make_component_target()

# change things like $a<b$ to $a< b$ to un-confuse the browser.
# this has to be done before any html tags get added, but after
# things like tikz are processed
processenvironments.space_after_lessthan()

# Step 2) Do some initial LaTeX substitutions

processenvironments.expand_text_macros()
dandr.process_subfigures_to_html()
makeoutput.tables_to_html()

if component.target == "html" or True:
    makeoutput.cite_and_ref_to_html()

dandr.convert_non_mathjax_math()

#  this funciton separate html and ptx if component.target == "html":
dandr.convert_tex_markup_to_html()  # operates on component.target

if component.target == "html":
    processenvironments.preprocess_terminology()

# Step 3)  Recursively expand all the sha1 codes
# and wrap them in the appropriate tags

logging.info("expanding the nested %s environements", component.target)

# Next is the main loop when all the environments are expanded
# and converted into their HTML versions.  The actions are
# performed in several loops because it is better to expand
# certain environments first.

if component.stealth_knowls:
    makeoutput.make_terminology_links()

makeoutput.expand_to_html(excludedmarkers=["hint"])
makeoutput.expand_to_html()

makeoutput.chapterpages()
makeoutput.section_links_on_chapterpages()

# Step 4) Write to the appropriate html files.

makeoutput.chapter_section_files()
makeoutput.top_level_page()

if component.target == "html":
    makeoutput.make_knowls_from_labels()

if component.index:
    makeoutput.indexpage()

if component.target == "html":
    makeoutput.make_other_knowls()

logging.info("total number of sections: %s", component.totalnumberofsections)

makeoutput.bibliography()

try:
    if component.environment['abstract'][component.target].strip():
        makeoutput.saveoutputfile("abstract",
          makeoutput.mathjaxmacros() + component.environment['abstract'][component.target])
except AttributeError:    # no abstract
    pass

# omitting, temporarily, due to a font encoding problem
#if component.bibliography_in_html:
#    makeoutput.saveoutputfile("bibliography",makeoutput.mathjaxmacros() + component.bibliography_in_html)

makeoutput.printdiagnostics()

makeoutput.make_dependency_tree()

makeoutput.tidy_up()

#for ind in component.dependency_tree:
#    print ind

print("found",len(component.dependency_tree),"dependencies")

print("found",len(component.terminology),"terminologies")

for sec in component.html_sections:
    print(sec)

if component.image_errors:
    print(component.image_errors, " image files not found")

if component.debug_counter:
    print("special environments processed:", component.debug_counter)

print("done converting", component.inputfilename)
sys.exit()

