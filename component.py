# -*- coding: utf-8 -*-

import json

verbose = False
pureasciimode = False  # not currently used

inputfilename=""
originalinputfilename = ""
inputdirectory=""
outputdirectory=""
imagesdirectory=""
workingdirectory=""  # when files in a dubdirectory import other files

inputfile=""
known_files=[]

documentcontents=""
preface_sec0=""

abstract=""
title="Title Goes Here"
title_short=""
author=""
authorlist=[]
author_html=""
email=""
thanks=""

preamble=""
header=""
bibliography=""
bibliography_in_html=""
bibliography_entries = []
appendix=""
extras={}
extras["graphicspath"] = ["."]     # subdirectories to look for images
extras["unitlength"] = ["6mm"]      # scale of picture

tocstyle = ""

sagecellstart = '<div class="sagecell-sage"><script type="text/x-sage">'
sagecellend = '</script></div>'


style_number = "0"

footnote = 0

parent = ""

known_paper_code = ""
publisher = "AIM"

writer = ""
frontmatter = False
knowlify_proofs = True
hide_hints = False
guess_terminology = True
stealth_knowls = True

environment={}  # Each entry corresponds to a LaTeX environment 
                # (theorem, definition, equation, etc). 
                # The key is the sha1 of the text+environment

environment_types={}
math_macro_types={}

single_use_dictionary={}

environments_with_captions = []
environments_with_images = []
environments_with_linebreaks = []
list_environments = []
math_environments = []
sub_environments = []
display_math_environments = []
multiline_math_environments = []
verbatim_environments = []
theoremlikeenvironments = []
definitionlikeenvironments = []

html_sections=[]   #  list of sections that become html files
html_sections_type={}   #  list of sections that become html files

index=[]    # list of dictionaries describing the index entries
terminology=[]    # list of dictionaries describing defined terms

dependency_tree=[] # which definitions and theorems are mentioned in other definitions and theorems

label={}

bibliography_entry={}

definitions=[]
definitions_parsed={}
definitions_parsed_all={}
newtheorems_parsed=[]

toplevel = 0      # 0 for chapter, 1 for section (will be determined from document contents).

thetoc=""

end_of_list_code = "1234512345123451234512345123451234512345"

definitions_only_in_preamble = False  

missing_macros = {}

known_people = []  # will become a list of dictionaries
linktocw = True

source_encoding = 'utf-8'

target = "html"  # options: html, ptx, ptxstrict?
imgtarget = "png"  # png, svg

image_errors = 0
debug_counter = 0
preprocess_counter = 0
debug = False

####################
# counters

def initialize_counters():

#
# The following setup for counters should be better.
#
# For a long book, add 'part' at the beginning of the sectioncounters,
# if appropriate.
# (what we should to is make part, chapter, section,... all available,
# scan the document to see the highest one used, then go down from there.)
#
# The environmentcounters are also used in environment_types,
# so the current setup makes it easy to have an inconsistency.

    global sectioncounters
    sectioncounters = ['chapter','section','subsection','subsubsection','exercises','worksheet','paragraphs']
    global totalnumberofsections
    totalnumberofsections = {x:0 for x in sectioncounters}

    global environmentcounters
    environmentcounters = ['equation','theorem','figure','misc','exercise',
                           'list','endlist','bibitem','none']  # text?
                                                 # why none?

    global counter, counterstar
    counter={}
    counterstar={}  # for counting the un-numbered items

    for cc in sectioncounters:
        counter[cc] = 0
        counterstar[cc] = 0

    for cc in environmentcounters:
        counter[cc] = 0
        counterstar[cc] = 0

    counter['item'] = [0,0,0,0,0,0,99990]
    counter['item'] = [0,0,0,0,0,0,0,0,99990]
               # since lists can be nested, we need a counter for each level
    counterstar['item'] = counter['item']

    global imageformats
    imageformats = ["svg", "eps", "pdf", "png", "jpg", "jpeg", "gif"]

#####################

# Some environments cannot occur inside a paragraph: they are their own block-level
# component of the document, comparable to a paragraph.
# Note:  some of these are "float"s in LaTeX.  Not sure if we want to handle those differently.

# Some environments should only occur inside a paragraph, or inside some other block-level
# environment, others are always their own block, and some can be either.

# This distinction is important for determining the paragraph breaks.

def initialize_environments():

    global math_macro_types
    global environment_types
    global environments_with_captions
    global environments_with_images
    global list_environments
    global environments_with_linebreaks
    global math_environments
    global sub_environments
    global display_math_environments
    global multiline_math_environments
    global verbatim_environments
    global theoremlikeenvironments
    global definitionlikeenvironments
    global blocks_that_can_contain_paragraphs
    global sha1heads_para, sha1heads_numberable, sha1heads_all

    sha1heads_para = "SEC|mathdisplay|block|text|anY|item"
    sha1heads_numberable = "SEC|mathdisplay|mathrow|block|text|anY|item"
    sha1heads_all = "SEC|mathdisplay|block|text|anY|item|verb|image|mathrow|mathinline|FOOT|mathtxt|section"
        #and those are the heads which need to be expanded when reassembling
#  why are we using "anY" for itemize and enumerate?

    math_macro_types = {
                "text":{'display':'mathtxt','class':'mathtxt','counter':'','numargs':1},
                "textrm":{'display':'mathtxt','class':'mathtxt','counter':'','numargs':1},   
                "mbox":{'display':'mathtxt','class':'mathtxt','counter':'','numargs':1},
                "substack":{'display':'anY','class':'mathcomponentmacro','counter':'misc','numargs':1}
         # need to treat mbox and textup the same way as text ?
                  }

    environment_types={
                "macro":{'display':'anY','class':'macro','counter':'none'},    
                       # possibly not used, replaced by mathmacro?
                "mathmacro":{'display':'anY','class':'mathmacro','counter':'none'},
                "chapter":{'display':'section','class':'section','counter':'chapter'},
                "section":{'display':'section','class':'section','counter':'section'},
                "subsection":{'display':'section','class':'section','counter':'subsection'},
                "subsubsection":{'display':'section','class':'section','counter':'subsubsection'},
                "worksheet":{'display':'section','class':'section','counter':'worksheet'},
                "exercises":{'display':'section','class':'section','counter':'exercises'},
                "abstract":{'display':'section','class':'section','counter':'none'},
                "paragraphs":{'display':'section','class':'section','counter':'none'},
                "$":{'display':'mathinline','class':'mathinline','counter':'none'},
                "equation":{'display':'mathdisplay','class':'math','counter':'equation'},
                "reaction":{'display':'mathdisplay','class':'math','counter':'equation'},
                "diagram":{'display':'mathdisplay','class':'mathcomponent','counter':'misc'},        
                       # apparently diagram can be a stand-alone environment,
                       # even though it usually occurs in math mode.
                       # maybe it is better to just wrap diagram in equation (if it isn't already)
                "eqnarray":{'display':'mathdisplay','class':'mathwrapper','counter':'misc'},   
                       # because each mathrow is numbered
                "multline":{'display':'mathdisplay','class':'math','counter':'equation'},     
                       # multline is for *one* equation taking multiple lines
                "aligned":{'display':'mathdisplay','class':'mathcomponent','counter':'misc'},     
                       # aligned does not allow a tag
                "split":{'display':'mathdisplay','class':'math','counter':'equation'},     
                       # split is like multline?
                "align":{'display':'mathdisplay','class':'mathwrapper','counter':'misc'},
                "reactions":{'display':'mathdisplay','class':'mathwrapper','counter':'misc'},
                "gather":{'display':'mathdisplay','class':'mathwrapper','counter':'misc'},
                "alignat":{'display':'mathdisplay','class':'mathwrapper','counter':'misc'},
                "mathrow":{'display':'anY','class':'mathrow','counter':'equation'},         
                       # not sure 'display':'anY' is wise. rethink See convert_tex_markup_to_html
                "cases":{'display':'block','class':'mathcomponent','counter':'misc'},       
                       # not sure 'display':'block' is wise. rethink.  Seeconvert_tex_markup_to_html
                "matrix":{'display':'block','class':'mathcomponent','counter':'misc'},       
                "pmatrix":{'display':'block','class':'mathcomponent','counter':'misc'},       
                "bmatrix":{'display':'block','class':'mathcomponent','counter':'misc'},       
                       # not sure 'display':'block' is wise. rethink.  Seeconvert_tex_markup_to_html
                "array":{'display':'block','class':'mathcomponent','counter':'misc'},
                "picture":{'display':'block','class':'image','counter':'misc'},
                "mathpicture":{'display':'block','class':'image','counter':'misc'},
                "acknowledgement":{'display':'block','class':'remark','typename':'Acknowledgement','counter':'subsection'},
                "hint":{'display':'block','class':'hint','typename':'Hint','counter':'misc'},
                "answer":{'display':'block','class':'hint','typename':'Answer','counter':'misc'},
                "aside":{'display':'block','class':'aside','typename':'Aside','counter':'misc'},
                "scrapwork":{'display':'block','class':'aside','typename':'Scrapwork','counter':'misc'},
                "marginalnote":{'display':'block','class':'aside','typename':'','counter':'misc'},
                "para":{'display':'block','class':'layout','typename':'','counter':'subsection'},
                "task":{'display':'block','class':'exercise','typename':'Task','counter':'theorem'},
                "subtask":{'display':'block','class':'exercise','typename':'Task','counter':'theorem'},
                "exercise":{'display':'block','class':'exercise','typename':'Exercise','counter':'theorem'},
     #           "exercises":{'display':'block','class':'exercise','typename':'Exercises','counter':'theorem'},
                "table":{'display':'block','class':'figure','counter':'figure'},
                "tabu":{'display':'block','class':'table','counter':'misc'},
                "tabular":{'display':'block','class':'table','counter':'misc'},
                "tabularx":{'display':'block','class':'table','counter':'misc'},
                "tabbing":{'display':'block','class':'table','counter':'misc'},
                "enumerate":{'display':'anY','class':'list','counter':'list'},
                "itemize":{'display':'anY','class':'list','counter':'list'},
                "parts":{'display':'anY','class':'list','counter':'list'},  # probably obsolete, see questions_to_exercises
                "subparts":{'display':'anY','class':'list','counter':'list'},  # probably obsolete, see questions_to_exercises
                "description":{'display':'anY','class':'list','counter':'list'},
                "descriptionlist":{'display':'anY','class':'list','counter':'list'},
                "list":{'display':'anY','class':'list','counter':'list'},
                "endlist":{'display':'anY','class':'none','counter':'endlist'},
                "item":{'display':'anY','class':'item','counter':'item'},  
                       # how to label items?
                "proof":{'display':'block','class':'proof','counter':'misc'},  
                       # is there a general category?
                "proofsketch":{'display':'block','class':'proof','counter':'misc'},  
                       # is there a general category?
                "minipage":{'display':'block','class':'layout','counter':'misc'}, 
                       # ???  minipage is evil
                "historicalnote":{'display':'block','class':'aside','typename':'Historical Note','counter':'misc'}, 
                "commentary":{'display':'block','class':'aside','typename':'Commentary','counter':'misc'}, 
                "program":{'display':'block','class':'remark','typename':'Program','counter':'misc'},
                       # modify after looking at more examples
                "quote":{'display':'anY','class':'layout','counter':'misc'},
                "quotation":{'display':'anY','class':'layout','counter':'misc'},
                "assemblage":{'display':'anY','class':'layout','counter':'misc'},
                "flushleft":{'display':'anY','class':'layout','counter':'misc'},
                "flushright":{'display':'anY','class':'layout','counter':'misc'},
                "verbatim":{'display':'anY','class':'layout','counter':'misc'},
                "sageexample":{'display':'anY','class':'layout','counter':'misc'},
                "lstlisting":{'display':'anY','class':'layout','counter':'misc'},
                "trinket":{'display':'anY','class':'layout','counter':'misc'},
                "stdout":{'display':'anY','class':'layout','counter':'misc'},
                "code":{'display':'anY','class':'layout','counter':'misc'},
                "verb":{'display':'anY','class':'layout','counter':'misc'},
                "verse":{'display':'anY','class':'layout','counter':'misc'},
                "figure":{'display':'block','class':'figure','counter':'figure'},
                "wrapfigure":{'display':'block','class':'figure','counter':'figure'},
        #        "center":{'display':'anY','class':'layout','counter':'misc'},
                "tikz":{'display':'anY','class':'layout','counter':'misc'},
                "tikzpicture":{'display':'anY','class':'layout','counter':'misc'},
                "circuitikz":{'display':'anY','class':'layout','counter':'misc'},
                "lateximage":{'display':'anY','class':'layout','counter':'misc'},
                "objectives":{'display':'anY','class':'layout','counter':'misc'},
                "sidebyside":{'display':'anY','class':'layout','counter':'misc'},
                "footnote":{'display':'FOOT','class':'layout','counter':'misc'},
                "text":{'display':'anY','class':'text','counter':'misc'},
                "blob":{'display':'anY','class':'layout','counter':'misc'}
                }

    verbatim_environments = ['verb','verbatim','lstlisting', 'trinket', 'stdout', 'code', 'sageexample', 'genericpreformat', 'tikz', 'tikzpicture', 'circuitikz']

    blocks_that_can_contain_paragraphs=[
                   'blob','abstract','paragraphs',
                   'chapter','section','subsection','subsubsection','worksheet','exercises','sidebyside','objectives']

    blocks_that_can_contain_paragraphs.extend(['proof','proofsketch',
                   'exercise','marginalnote','historicalnote','scrapwork',
                   'commentary',
                   'aside','answer','hint', 'task', 'subtask'])

    theoremlikeenvironments = {"theorem":"Theorem",
                           "computationaltheorem":"Computational Theorem",
                           "proposition":"Proposition",
                           "lemma":"Lemma",
                           "corollary":"Corollary",
                           "heuristic":"Heuristic",
                           "algorithm":"Algorithm",
                           "subalgorithm":"Subalgorithm",
                           "slogan":"Slogan",
                           "generictheorem":"THeorem"}

    for type in theoremlikeenvironments:
        environment_types[type] = {'display':'block',
                                   'class':'theorem',
                                   'typename':theoremlikeenvironments[type],
                                   'counter':'theorem'}
        blocks_that_can_contain_paragraphs.append(type)


    examplelikeenvironments = {"example":"Example",
                               "counterexample":"Counterexample",
                               "problem":"Problem",
                               "project":"Project",
                               "homework":"Homework",
                               "challenge":"Challenge",
                               "exploration":"Exploration",
                               "investigation":"Investigation",
                               "activity":"Activity",
                               "scratchwork":"Scratchwork",
                               "application":"Application"}

    for type in examplelikeenvironments:
        environment_types[type] = {'display':'block',
                                   'class':'example',
                                   'typename':examplelikeenvironments[type],
                                   'counter':'theorem'}
        blocks_that_can_contain_paragraphs.append(type)

     # need to add property
    definitionlikeenvironments = {"definition":"Definition",
                               "conjecture":"Conjecture",
                               "question":"Question",
                               "note":"Note",
                               "claim":"Claim",
                               "subclaim":"Subclaim",
                               "fact":"Fact",
                               "identity":"Identity",
                               "assumption":"Assumption",
                               "situation":"Situation",
                               "hypothesis":"Hypothesis",
                               "setup":"Setup",
                               "axiom":"Axiom",
                               "principle":"Principle",
                               "convention":"Convention",
                               "observation":"Observation",
                               "notation":"Notation",
                               "construction":"Construction",
                               "keyidea":"Key Idea",
                               "previewactivity":"Preview Activity",
                               "conundrum":"Conundrum"}

    for type in definitionlikeenvironments:
        environment_types[type] = {'display':'block',
                                   'class':'definition',
                                   'typename':definitionlikeenvironments[type],
                                   'counter':'theorem'}
        blocks_that_can_contain_paragraphs.append(type)

    remarklikeenvironments = {"remark":"Remark",
                              "remarks":"Remarks",
                              "scholium":"Scholium",
                              "warning":"Warning",
                              "caution":"Caution",
                              "case":"Case",
                              "assemblage":"Assemblage",
                              "summary":"Summary",
                              "review":"Review",
                              "solution":"Solution"}

    for type in remarklikeenvironments:
        environment_types[type] = {'display':'block',
                                   'class':'remark',
                                   'typename':remarklikeenvironments[type],
                                   'counter':'theorem'}
        blocks_that_can_contain_paragraphs.append(type)

    environments_with_captions = ['table','figure','wrapfigure']
    environments_with_images = ['figure','wrapfigure']
    list_environments = ['enumerate','itemize','description','descriptionlist','parts','subparts']
    environments_with_linebreaks = ['$', r'\(', r'\[', 'tabu','tabular', 'tabularx']
    math_environments = ['$', r'\(', r'\[']
    sub_environments = []
    display_math_environments = []
    multiline_math_environments = []

    environments_with_linebreaks.append("mathmacro")   
             # the macro "substack" can contain \\, but I don't actually know of any other cases

    for env in environment_types:
        if environment_types[env]['display'] == "mathdisplay":
            math_environments.append(env)
            display_math_environments.append(env)
            environments_with_linebreaks.append(env)    
             # true for multline, but false for equation.  Is that okay?
        if environment_types[env]['class'] == 'mathwrapper':
            math_environments.append(env)
            environments_with_linebreaks.append(env)
            multiline_math_environments.append(env)
        if environment_types[env]['class'] == 'mathcomponent':
            math_environments.append(env)
            environments_with_linebreaks.append(env)
        if environment_types[env]['class'] in ['mathrow','mathcomponent','mathmacro']:
            math_environments.append(env)
            sub_environments.append(env)

    environment[end_of_list_code] = {'marker':'endlist',
                                    'sha1head':'anY',
                                    'star':'',
                                    'sqgroup':'',
                                    'component_raw':'',
                                    'component_separated':'',
                                    'caption':'',
                                    'image_file_tex':'',
                                    'image_ratio':''
                                    }

###################

def find_known_people():

    global known_people

    try:
        known_people_file = "../collectedworks_backup/known_people"
        with open(known_people_file) as infile:
            known_people = json.load(infile)
    except IOError:
        pass  # most users will not have that file

