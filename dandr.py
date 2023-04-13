# -*- coding: utf-8 -*-
                                             #    dandr.py
import sys
import logging

import re
import time
#import json

import preprocess
import component
import separatecomponents
import processenvironments
import makeoutput
import utilities
#import oldtex
import mapping

############################

def initial_preparations(text):
    """Extract verbatim enviroments, remove comments, and do some
    conversions specific to particular authors.

    """

    thetext = text;

    thetext = re.sub("\x0d+\n","\n",thetext)   # ^M
    thetext = re.sub("\x0d","\n",thetext)   # ^M

    thetext = re.sub("\t","  ",thetext)   # make tab into 2 spaces (why 2?)

    thetext = utilities.other_alphabets_to_latex(thetext)

   # remove comments, material after \end{document}, etc
    thetext = separatecomponents.killunnessarytex(thetext)

   # \ifthenelse determines which sources to use, and so has higher
   # priority than verbatim or other environments
   # BUT, we have to do some conversion for particular authors
   # in order to have the right conditionals in the ifthenelse
    thetext = preprocess.conversion_for_particular_authors(thetext)
    print("foncerted particular for", component.writer.lower(), component.writer.lower() in ["austin"]);
    thetext = ifthenelse(thetext)

   # Since a verbatim environment could contain comments which
   # are intended to be shown, we extract verbatim comments first.
   # Note that one can construct scenarios where this approach fails.
    thetext = separatecomponents.separateenvironment("verbatim",thetext)
    thetext = separatecomponents.separateenvironment("lstlisting",thetext)
    thetext = separatecomponents.separateenvironment("sageexample",thetext)
   # Also extract \verb+verbatim textgoes here+
    thetext = separatecomponents.separateverb(thetext)   

    thetext = separatecomponents.killcomments(thetext)

   # Transform LaTeX constructions to a standard form.
   # (The main program only handles "good" LaTeX.  This is
   # necessary in order to keep the main program managable.)
    thetext = preprocess.latexconvert(thetext)

    thetext = preprocess.throw_away_environments(thetext)

    thetext = utilities.fix_bad_font_directives(thetext)

    preprocess.find_particular_packages(thetext)

    thetext = preprocess.hide_figure_inputs(thetext)
    thetext = preprocess.hide_diagram_in_math(thetext)

    logging.debug("done with initial_preparations")

    return thetext

###############

def ifthenelse(text):
    r"""Return the appropriate \ifthenelse selections, assuming the
    arguments of \ifthenelse have been replaced by true or false.
    Treat unknown arguments as true.
    Probably this isn't working too well and should be re-thought

    """

    if r"\ifthenelse" not in text:
        return text

    thetext = text

    utilities.something_changed = 1
    
    while utilities.something_changed:
        utilities.something_changed = 0
        thetext = re.sub(r"\\ifthenelse *(.*)",
                                ifthenel,thetext,1,re.DOTALL)

    return thetext

######################

def ifthenel(txt):

   text_after = txt.group(1)

   utilities.something_changed += 1

   booleanflag, text_after = utilities.first_bracketed_string(text_after)
   booleanflag = utilities.strip_brackets(booleanflag)

   truepart, text_after = utilities.first_bracketed_string(text_after)
   falsepart, text_after = utilities.first_bracketed_string(text_after)

   if booleanflag == "true":    # LaTeX uses "true" for True
        return utilities.strip_brackets(truepart) + " " + text_after
   else:
        return utilities.strip_brackets(falsepart) + " " + text_after

######################

def expand_input_files():

    logging.info( "reading all the input files")

    file_count = 0
    utilities.something_changed_file = 1
    while utilities.something_changed_file:
        logging.info("looking for an input file", separatecomponents.input_and_preprocess_a_file)
        utilities.something_changed_file = 0
        logging.info("nnnothing");
        component.documentcontents = re.sub(
           #   r"\s\\(include|input|import)\*?\s*{([^}]+)}",
              r"\\(include|input|import)\*?\s*{([^{}]+)}",
              separatecomponents.input_and_preprocess_a_file,
              component.documentcontents,1)
        logging.debug("trid looking for input{...} %s")
        # should we do this with just one regular expression?
        # probably that would be asking for trouble
        component.documentcontents = re.sub(
              r"\\(include|input|import)\s+(\S+)(\s+|$)",
              separatecomponents.input_and_preprocess_a_file,
              component.documentcontents,1)
        logging.debug("tried looking for input, %s", utilities.something_changed_file)

        if not utilities.something_changed_file:
            logging.info("done reading %s input files", file_count)
            logging.info("the file ends:\n%s",component.documentcontents[-50:])
            break
        else:
            file_count += 1

        if file_count > 1000:
            logging.error("Error: more than 1000 files: %s", file_count)
            break

    file_count = 0
    utilities.something_changed_file = 1
    while utilities.something_changed_file:
        logging.info("looking for a package")
        utilities.something_changed_file = 0
        component.documentcontents = re.sub(
            r"\\(usepackage|documentclass|documentstyle)((\[[^\[\]]+\])?){([^}]+)}",
            separatecomponents.input_and_preprocess_a_package,
            component.documentcontents,1)
        if not utilities.something_changed_file:
            logging.info("done reading %s packages",file_count)
            break
        else:
            file_count += 1

        if file_count > 100:
            logging.error("Error: more than 100 packages: %s", file_count)
            break


##################

def separate_into_latex_components(text):
    """To process the contents of the document, we first separate
    it into preamble, header, sections, appendices, and bibliography.
    Then we can process each of those components separately.
    
    """

    logging.info(time.strftime("%H:%M:%S"))

    thetext = text

    # Because people don't follow the rules (such as putting the
    # abstract in the preamble), we extract some material before
    # separating the header, etc.

    # remove the preamble from thetext, saving the preamble material
    # in the appropriate places.
    # Note: preamble = everything before \begin{document}

    thetext = separatecomponents.separatepreamble(thetext)

    # Remove the definitions from the body of the document and
    # put them in the list  component.definition, and some of
    # them in component.definition_parsed .

    for depth in range(5):  # should we have more than 5-times nested macros?
        logging.info("about to extract environments/definitions/macros")
        logging.info("macro depth: %s", depth)

        for dd in range(0,999):  # could we ever have 1000 macros?

            utilities.something_changed=0
            component.preamble = separatecomponents.extract_newenvironments(component.preamble)
            component.preamble = separatecomponents.extract_definition(component.preamble)
            if not component.definitions_only_in_preamble:
                thetext = separatecomponents.extract_newenvironments(thetext)
                thetext = separatecomponents.extract_definition(thetext)

            if not utilities.something_changed:
                logging.info("found %s definitions",dd)
                break

      # If someone uses \be for \begin{equation} , then we need to
      # substitute for that before we parse the document.
      # And if they define \nc to be \newcommand and then use it,
      # we need to substitute before extracting another round of macros

        component.preamble = processenvironments.replace_bad_macros(component.preamble)
        thetext = processenvironments.replace_bad_macros(thetext)
        makeoutput.saveoutputfile("everything"+str(depth + 2)+".tex",thetext)

    # expanding the authors macros may have revealed some environment shortcuts,
    # so we repeat a command which was done previously in preprocess.latexconvert
    thetext = utilities.environment_shortcuts(thetext)
    
    for dd in range(999):  # could we ever have 1000 theorem-like environments?

        utilities.something_changed = 0
        component.preamble = separatecomponents.extract_newtheorems(component.preamble)
        thetext = separatecomponents.extract_newtheorems(thetext)

        if not utilities.something_changed:
           logging.info("found %s newtheorems",dd)
           break

    thetext = processenvironments.replace_bad_theorems(thetext)

    thetext = processenvironments.processthanks(thetext)
    thetext = processenvironments.processabstract(thetext)

    # title should be in the preamble, but often isn't
    thetext = processenvironments.processtitle(thetext)
    component.preamble = processenvironments.processtitle(component.preamble)

    # should be in the preamble, but often isn't
    thetext = processenvironments.processauthor(thetext)
    component.preamble = processenvironments.processauthor(component.preamble)
    logging.info("found %s authors", len(component.authorlist))
    logging.info("and they are %s", component.authorlist)

    if component.known_paper_code:
        logging.info("will extract title and authors from: %s",component.known_paper_code)
        separatecomponents.authors_title_from_known_paper()
        logging.info("now the author list is %s", component.authorlist)

    separatecomponents.separateauthors()

    # where should email addresses be?
    thetext = processenvironments.processemail(thetext)     
    component.preamble = processenvironments.processemail(component.preamble)
    
    thetext = separatecomponents.separateextras(thetext)
    component.preamble = separatecomponents.separateextras(component.preamble)

    # remove the header from thetext, saving the header material
    # in the appropriate places.
    # (header =  everything between \begin{document} and \maketitle
    # (Is \maketitle required?)
    thetext = separatecomponents.separateheader(thetext)
    
    # same for the bibliography
    thetext = separatecomponents.separatebibliography(thetext)
    component.bibliography = preprocess.adjust_bibliography(component.bibliography)
    
    # same for the appendices
    # need to rethink this
    # ??? maybe appendices should be treated more like sections?
    thetext = processenvironments.processappendices(thetext)

    thetext = preprocess.throw_away_environments_later(thetext)

    logging.info("done separating into components")
    logging.info("the top level text is %s", thetext[:1000]+ "\n...\n")

    return thetext

#################

def separate_into_chapters_sections_etc(text):

    logging.info("separating into chapters, sections, etc")
    thetext = text

    component.theparent = ""

    # separate the top level (maybe chapter, maybe section)
    if "\\chapter{" in thetext or "\\chapter[" in thetext:
        component.toplevel = 0
        logging.info("processing a book")
    else:
        component.toplevel = 1
        logging.info("processing a paper")
        if "\\section" not in thetext:
            logging.error('no sections in text: treating document as one "section*"')
            thetext = "\\section*{XXXX}\n\n" + thetext
     # fix: some papers have long sections and should be treated like books.
    logging.info("separating the top level: %s", component.toplevel)

    topsectiontype = component.sectioncounters[component.toplevel]
    thetext = separatecomponents.separatesections(topsectiontype,thetext)

    logging.info("done separating the %s", topsectiontype)

    # successively extract each type of subsection, subsubsection, etc
    for depth in range(component.toplevel,len(component.sectioncounters)-1):

        subsectiontype = component.sectioncounters[depth]
        subsubsectiontype = component.sectioncounters[depth + 1]
        logging.debug("separating level %s : %s", depth, subsubsectiontype)

        for sha1key in list(component.environment.keys()):
                 # need keys() because the dictionary changes during the loop
            component.parent = sha1key
            if component.environment[sha1key]['marker'] == subsectiontype:
                theoldtext = component.environment[sha1key]['component_separated']
                thenewtext = separatecomponents.separatesections(subsubsectiontype,theoldtext)
                component.environment[sha1key]['component_separated'] = thenewtext

    return thetext

#####################

def process_math_environments():
    """ These substitution are only for math mode.
    """

    logging.info("processing math environments")
    for sha1key in list(component.environment.keys()):
        parentmarker = component.environment[sha1key]['marker']

        if (parentmarker not in component.math_environments):
            continue

        thetext = component.environment[sha1key]['component_separated']

        thetext = re.sub(r"\\qed\b\s*","",thetext)   # 0806.0867/section2.html

        thetext = re.sub(r"\\<",r"\\langle ",thetext)   # 0806.0867/section2.html
        thetext = re.sub(r"\\>",r"\\rangle ",thetext)   # 0806.0867/section2.html

        if component.target == 'ptx':
            thetext = preprocess.math_special(thetext)

        if "\\eqalign" in thetext:
            logging.debug("replacing eqalign in %s",thetext[:50])
            thetext = utilities.replacemacro(thetext,"eqalign",1,"#1")
            component.environment[sha1key]['marker'] = "align"
            component.environment[sha1key]['star'] = ""     # there may be cases where too many things are numbered?
            parentmarker = "align"

        if "intertext" in thetext:
            if parentmarker == "alignat":   # then we need to know the argument indicating how many alignments
   # agtually, this is not working properly.
                numalign, _ = utilities.first_bracketed_string(thetext)
            else:
                numalign = ""
            
            if component.target == 'ptx':
                pass  # because this has to be done at the end, because the <tag>
                      # is corrupted by later conversions
            #    thetext = utilities.replacemacro(thetext,"intertext",1,
            #              "</mrow>" + "\n" + r"<intertext>#1</intertext>" + r"\n" + "<mrow>")
            else:
                thetext = utilities.replacemacro(thetext,"intertext",1,
                          "\\end{"+parentmarker+"}\n#1\n\\begin{"+parentmarker+"}"+numalign)

        if "eqno" in thetext:
            thetext = re.sub(r"\\leqno\b\s*(\S+)(\s|$)",r"\\tag*{\1}\2",thetext)
            thetext = re.sub(r"\\reqno\b\s*(\S+)(\s|$)",r"\\tag*{\1}\2",thetext)
            thetext = re.sub(r"\\eqno\b\s*(\S+)(\s|$)",r"\\tag*{\1}\2",thetext)
            # If the above were done in a way that strips brackets from \1, then we wouldn't need the next line.
            thetext = re.sub(r"\\tag\*{{([^{}]+)}}",r"\\tag*{\1}",thetext)

        component.environment[sha1key]['component_separated'] = thetext

############

def find_global_parameters(text):

    logging.info("finding global parameters: %s", mapping.global_parameters)
    thetext = text

    # currently code only works when there is one \graphicspath which contains only one directory
    for parameter in mapping.global_parameters:
        findparameter = r"\\"+parameter
        if parameter in thetext:
            thetext = re.sub(r".*findparameter",findparameter,thetext,1,re.DOTALL)
            theparameter = re.sub(findparameter + "(.*)",r"\1",thetext)
            theparameter, _ = utilities.first_bracketed_string(theparameter)
            theparameter = utilities.strip_brackets(theparameter)
            logging.debug("the parameter is %s", theparameter)
            component.extras[parameter] = [theparameter] + component.extras[parameter]

############

def find_local_parameters(thetext):

    # currently we only find \unitlength.
    # rewrite once we have somethign else

    logging.info("finding local parameters")
    if r"\unitlength" not in thetext:
        return ""

    if "unitlength" not in component.extras:
        # Currently this shouldn't happen because we seed it with "6mm" just to have something to use.
        # And when we use it, we start counting at 1 if we can.
        component.extras["unitlength"] = ["6mm"]

    the_unitlengths = re.findall(r"\\unitlength\s*\S+\s", thetext)
    # might be "\setlength 0.1in" or might be "\setlength{\unitlength}{0.4mm}".  We handle both.

    for sl in the_unitlengths:
        this_sl = re.sub("[{}]"," ",sl)
        this_sl = this_sl[11:]
        this_sl = this_sl.strip()
        component.extras["unitlength"].append(this_sl)

    logging.debug("now have these unitlengths: %s", component.extras["unitlength"])

#####################

def separate_latex_math_macros():

    logging.info("separate_latex_math_macros")
    for sha1key in list(component.environment.keys()):
        parentmarker = component.environment[sha1key]['marker']

        component.parent = sha1key     # is that still needed?
        thetext = component.environment[sha1key]['component_separated']

        for themacroname in component.math_macro_types:
            numargs = component.math_macro_types[themacroname]['numargs']
            thetext = separatecomponents.separatemacro(themacroname,numargs,thetext)

        component.environment[sha1key]['component_separated'] = thetext

#####################

def separate_latex_environments(exclude="",include="",separatemath=True):

    # exclude could be something like ['class':'layout'], to not separate
    # those environments whose 'class' is 'layout'

    # we extract LaTeX-style display math last because some
    # people redefine \[ and \(, so we need to substitute something
    # harmless for these inside the actual math delimiters.

    # Now we need to repeatedly extract all the environments.  Highly nested
    # environments have one level extracted each time.

    logging.info("in separate_latex_environments %s,%s,%s", exclude, include, separatemath)

    for depth in range(0,11):   # Could we have 11 nested levels?

        logging.info("separating at depth %s", depth)
        logging.info("scanning %s environments", len(list(component.environment.keys())))
 #       logging.info("what_changed last", utilities.what_changed.group(0))
 #       print utilities.what_changed.group(0)

        utilities.something_changed = 0

        skipped = 0

        for sha1key in list(component.environment.keys()):
            component.parent = sha1key
            comp = component.environment[sha1key]
            if comp['marker'] in [r'$', r'$$', r'\(', r'\[', 'equation', 'align', 'reaction', 'reactions']:
                skipped += 1
                continue  # because math mode can't contain a theorem, remark, etc
            
            thetext = comp['component_separated']

            for env in component.environment_types:
                if not (exclude and 
                         (exclude == "all"  or
                          component.environment_types[env][exclude[0]] == exclude[1])):
                    thetext = separatecomponents.separateenvironment(env,thetext)
            component.environment[sha1key]['component_separated'] = thetext

            # separate footnotes if no environment was excluded
            if (not exclude) or include == "footnotes":  
                thetext = separatecomponents.separatefootnote(thetext)
                component.environment[sha1key]['component_separated'] = thetext

        logging.info("number of math environments skipped: %s", skipped)

        logging.info("number of environments extracted: %s", utilities.something_changed)

        if not utilities.something_changed:
            logging.info("extracted all environments at depth %s",depth)
            break

    if separatemath:
        logging.info("now separating inline math")
        for sha1key in list(component.environment.keys()):
                  # need keys() because the dictionary changes during the loop
            this_component_type = component.environment[sha1key]['marker']
            if (this_component_type in component.environment_types and
                component.environment_types[this_component_type]['class']) not in ["math","mathrow"]:
                component.parent = sha1key
                thetext = component.environment[sha1key]['component_separated']

# Beause there are many possibilities of people using/abusing \( and \[
# to mean something other than math mode delimiters, it is impossible
# for this approach to work in all cases.  But this order seems to be
# reaspnable.  Possibly \( should come before \[   (if, for example,
# \[...\] inside inline math was deemed more likely than \(...\)
# inside display math).

                thetext = separatecomponents.separatemath(r"\$\$",r"\$\$",
                                                                 thetext)
                thetext = separatecomponents.separatemath(r"\$",r"\$",
                                                                 thetext)
                thetext = separatecomponents.separatemath(r"\\\[",r"\\\]",
                                                                 thetext)
                thetext = separatecomponents.separatemath(r"\\\(",r"\\\)",
                                                                 thetext)
                component.environment[sha1key]['component_separated'] = thetext

        logging.info("finished separating inline math")

    # There is another round separating the items in list environments
    # and in multiline display math.  See separate_latex_rows()

####################

def process_separated_environments():
    '''Further processing of figures, minipages, etc.

    '''

    logging.info("initial processing of minipage, tikz, images, etc")

    for sha1key in list(component.environment.keys()):
        if component.environment[sha1key]['marker'] == "minipage":
            theoldtext = component.environment[sha1key]['component_separated']
            thenewtext = theoldtext.strip()
        #    print "thenewtext", thenewtext
            try:
                thedimensions, thenewtext = utilities.first_bracketed_string(thenewtext)
                thedimensions = utilities.strip_brackets(thedimensions)
                component.environment[sha1key]['dimensions'] = thedimensions
                component.environment[sha1key]['component_separated'] = thenewtext
            except ValueError:  # usually means thenewtext is empty
                component.environment[sha1key]['dimensions'] = "0"
                component.environment[sha1key]['component_separated'] += thenewtext

# captions 
        if r"\caption" in component.environment[sha1key]['component_separated']:
            separatecomponents.separatecaption(sha1key)

# tikzpictures and pspicture
        theoldtext = component.environment[sha1key]['component_separated']
        thenewtext = separatecomponents.separatetikzpictures("tikzpicture",theoldtext)
        thenewtext = separatecomponents.separatetikzpictures("circuitikz",theoldtext)
        thenewtext = separatecomponents.separatetikzpictures("pspicture",thenewtext)
        thenewtext = separatecomponents.separatetikzpictures("pgfpicture",thenewtext)
        component.environment[sha1key]['component_separated'] = thenewtext

# includegraphics
        theoldtext = component.environment[sha1key]['component_separated']
             # labellist can include pinlabel

        # fix common figure anomalies
        # maybe this should be its own separate function?
        if component.environment[sha1key]['marker'] == "figure":
            theoldtext = re.sub(r"\\begin{center}\s*", "", theoldtext)
            theoldtext = re.sub(r"\\end{center}\s*", "", theoldtext)
            theoldtext = re.sub(r"\\leavevmode", "", theoldtext)

            theoldtext = re.sub(r"^\s*\\vskip.*", "", theoldtext)

        # maybe these could be "elif"s, but no harm to try them all
            if r"\figureinput" in theoldtext:
                theoldtext = utilities.re_convert_image(theoldtext)
            if r"\includegraphics" in theoldtext and r"\labellist" in theoldtext:
                theoldtext = utilities.re_convert_image(theoldtext)
            if r"\includegraphics" in theoldtext and r"\put(" in theoldtext:
                theoldtext = utilities.re_convert_image(theoldtext)
            if r"\includegraphics" in theoldtext and r"\psfrag" in theoldtext:
                theoldtext = utilities.re_convert_image(theoldtext)
            if r"\begin{overpic}" in theoldtext:
                theoldtext = utilities.re_convert_image(theoldtext)

# temporary, gatehr some information
        if component.environment[sha1key]['marker'] == "figure":
            tmp = re.sub(r"\\includegraphics.*", "", theoldtext)
            tmp = tmp.strip()
            if tmp:
                logging.warning("extra material (unprocessed?) in image: %s", tmp)

   #     the_parent = component.environment[sha1key]['parent']
   #     if component.environment[sha1key]['marker'] == "picture" and component.environment[the_parent] != 'figure':
        if component.environment[sha1key]['marker'] == "picture":
            the_parent = component.environment[sha1key]['parent']
            if component.environment[the_parent]['marker'] != 'figure':
                logging.info("re-converting image %s", theoldtext[:50])
                theoldtext = utilities.re_convert_image("\\begin{picture}\n" + theoldtext + "\n\\end{picture}\n")
            else:
                logging.info("skipping picture %s because it is in figure %s", theoldtext[:50], the_parent)
                component.environment[sha1key]['component_separated'] = theoldtext
                continue

        thenewtext = separatecomponents.extract_includegraphics(theoldtext)
        component.environment[sha1key]['component_separated'] = thenewtext

####################

def process_subfigures_to_html():

    logging.info("processing subfigures")
    for sha1key in list(component.environment.keys()):

        theoldtext = component.environment[sha1key][component.target]

        if r"\subfigure" not in theoldtext:
            continue
        
        try:
            thenewtext = utilities.processsubfigures_to_html(theoldtext)
        except:
            thenewtext = theoldtext

        component.environment[sha1key][component.target] = thenewtext

####################

def separate_math_rows():
    '''Environments like 'enumerate' can contain multiple labels,
    so we separate those rows into their own environments.

    '''

#    This function is similar to separatecomponents.separatesections,
#    because in both cases there is a begin tag (\section or \item)
#    but no end tag.  Either build a unified function, or at least
#    move this one to the correct file.

    logging.info("separating math rows")
    itemmarker = "mathrow"
    
    for sha1key in list(component.environment.keys()):
        component.parent = sha1key
        parentmarker = component.environment[sha1key]['marker']

        if (parentmarker not in component.display_math_environments):
            continue

        try:
            thetext = component.environment[sha1key]['component_separated']
        except KeyError:
            logging.error("environment %s has no component_separated", sha1key)

        if parentmarker not in component.multiline_math_environments:
            continue

        elif ("xymatrix" in thetext or
           r"\xygraph" in thetext or
           r"\bordermatrix" in thetext or
           r"\diagram" in thetext or
           r"\begin{mathdiagram}" in thetext or
           r"\begin{CD}" in thetext or
           r"\begin{xy}" in thetext   #or
     #      parentmarker == "diagram"
           ):
            continue  # because these are handled later by dandr.convert_non_mathjax_math()

        else:
            parentstar = component.environment[sha1key]['star']
            logging.debug("parent marker %s and parentstar %s", parentmarker, parentstar)
            logging.debug("looking for backslashes in %s", thetext)
            therows = re.split(r"(\\\\|\\cr\b)",thetext)
            numrows = 1+int(len(therows)/2)
            logging.debug("the number of rows is %s", numrows)
            logging.debug("the first row is %s", therows[0])

            equation_as_sha1 = ""

            for rownum in range(numrows - 1):
                star = parentstar
                this_row = therows[2*rownum].strip()
                this_row_end = therows[2*rownum + 1]
                sha1ofthetext = utilities.sha1hexdigest(this_row + this_row_end + str(rownum) + component.parent)
                        # the problem is that you can have the same row multiple times, succh as  "& \vdots \\"
                if this_row_end == "\\cr" or "\\nonumber" in this_row:
                    star = "*"

                equation_as_sha1 += itemmarker+sha1ofthetext+"END "
                component.environment[sha1ofthetext] = {'marker':itemmarker,
                                            'sha1head':itemmarker,
                                            'parent':component.parent,
                                            'star':star,
                                            'sqgroup':"",
                                            'component_raw':this_row,
                                            'component_separated':this_row}
            this_row = therows[2*numrows - 2].strip()
            sha1ofthetext = utilities.sha1hexdigest(this_row)
            star = parentstar
            if "\\nonumber" in this_row:
                star = "*"

            equation_as_sha1 += itemmarker+sha1ofthetext+"END "
            component.environment[sha1ofthetext] = {'marker':itemmarker,
                                        'sha1head':itemmarker,
                                        'star':star,
                                        'parent':component.parent,
                                        'sqgroup':"end",     
                       #is it a bad idea to overload the sqgroup like that?
                                        'component_raw':this_row,
                                        'component_separated':this_row}

        component.environment[sha1key]['component_separated'] = equation_as_sha1

###########

def separate_latex_rows():
    '''Environments like 'enumerate' can contain multiple labels,
    so we separate those rows into their own environments.

    '''

#    This function is similar to separatecomponents.separatesections,
#    because in both cases there is a begin tag (\section or \item)
#    but no end tag.  Either build a unified function, or at least
#    move this one to the correct file.

    logging.info("separate_latex_rows")

    itemmarker = "item"
    
    finditem = "\s*" + "\\\\(" + itemmarker + ")\\b" + "\s*"  
                           # start with \item or \whatever or ...
    finditem += "(\*?)"    # possibly folowed by a *
    # the square group could be empty
    finditem += "((\[[^\[\]]*\])?)" + "\s*"  
                    # possibly followed by something in square brackets
    finditem += "(.*?)(\\\\" + itemmarker + r"\b)"

    findlastitem = "\s*" + "\\\\(" + itemmarker + ")\\b" + "\s*"
                               # start with \item or \whatever or ...
    findlastitem += "(\*?)"    # possibly folowed by a *
    findlastitem += "((\[[^\[\]]*\])?)" + "\s*"
                    # possibly followed by something in square brackets
    findlastitem += "(.*)"

    for sha1key in list(component.environment.keys()):
        if (component.environment[sha1key]['marker'] 
                              not in component.list_environments):
            continue

        try:
            thetext = component.environment[sha1key]['component_separated']
        except KeyError:
            logging.error("environment %s has no component_separated", sha1key)

        numberofitems = len(re.findall(r"\\item\b",thetext))

        if numberofitems == 0:
            continue

        if numberofitems > 50:
            logging.warning("more than 50 items in text starting %s", thetext[:50])
        for _ in range(1,numberofitems):
            thetext = re.sub(finditem, 
                             lambda match: separate_l_r(match,sha1key),
                             thetext,1,re.DOTALL)
        thetext = re.sub(findlastitem, 
                         lambda match: separate_l_r(match,sha1key),
                         thetext,1,re.DOTALL)
        component.environment[sha1key]['component_separated'] = thetext

###########

def separate_l_r(txt, parent_sha1):

    if txt is None:
        return ""

    itemmarker = txt.group(1)
    star = txt.group(2)
    squaregroup = txt.group(3)

    try:
        itemtext = txt.group(5)
    except IndexError:
        itemtext = ""
        logging.warning("empty itemtext in: %s", txt)

    try:
        remainingitems = txt.group(6)
    except IndexError:
        remainingitems = ""

    logging.debug("separating listitems: %s %s %s %s %s",
                   itemmarker,star,squaregroup,itemtext,remainingitems)

    # normally we strip the square brackets from the squaregroup,
    # but \item[] means no bullet/label, so we need to detect that,
    # so we don't strip [] from squaregroup
    # squaregroup = utilities.strip_brackets(squaregroup,"[","]")

    itemtext = itemtext.strip()
    itemtext = utilities.strip_brackets(itemtext)
    itemtext = itemtext.strip()
    sha1ofthetext = utilities.sha1hexdigest(itemtext+itemmarker)

    component.environment[sha1ofthetext] = {'marker':itemmarker,
                                            'sha1head':itemmarker,
                                            'parent':parent_sha1,
                                            'star':star,
                                            'sqgroup':squaregroup,
                                            'component_raw':itemtext,
                                            'component_separated':itemtext}

    return itemmarker+sha1ofthetext+"END "+remainingitems

###########

def separate_labels(excluded=[]):
    """Check if each component has a label.  If it does, remove it and
    save it.

    """

    logging.info("now extracting labels")
    for sha1key in list(component.environment.keys()):
        thetext = component.environment[sha1key]['component_separated']
        if r"\label{" in thetext:
            if component.environment[sha1key]['marker'] not in excluded:
                thetext = separatecomponents.extractlatexlabel(sha1key,thetext)
                component.environment[sha1key]['component_separated'] = thetext

####################

def separate_paragraphs():

    logging.info("separating the paragraphs")
    logging.info("blocks_that_can_contain_paragraphs: %s", component.blocks_that_can_contain_paragraphs)

    for sha1key in list(component.environment.keys()):
        if (component.environment[sha1key]['marker'] 
                      in component.blocks_that_can_contain_paragraphs):
            thetext = component.environment[sha1key]['component_separated']

            if component.target == "ptx":   # PTX does not allow <br />, so as a possibly long-term
                                            # hack, turn \\ into a paragraph break
                thetext = re.sub(r"\\linebreak\s+","\n\n",thetext)
                thetext = re.sub(r"\\\\\s+","\n\n",thetext)
                thetext = re.sub(r"\\\\(\[[^\[\]]*\])?\s+","\n\n",thetext)

            # If the LaTeX was good, then we just have blocks of text
            # separated by blank lines.  But unfortunately...
            thetext = re.sub(r"\\(hskip|hfuzz|vskip)\s*-?([0-9]|\.|,)+\s*(in|pt|cm|mm|px|em|en)","",thetext)
            thetext = re.sub(r"\\vskip\s*-?([0-9]|\.|,)*[a-z]+(\baselineskip)*","\n\n",thetext)
    # included above        thetext = re.sub(r"\\hskip\s*-?([0-9]|\.)+\s*(in|pt|cm|mm|px|em|en)","",thetext)
            thetext = re.sub(r"\\vglue\s*-?([0-9]|\.|,)+\s*(in|pt|cm|mm|px|em|en)","",thetext)
            thetext = re.sub(r"\\vskip\s*\\\S*","\n\n",thetext)
            thetext = re.sub(r"\\quad\s*","",thetext)

            thetext = separatecomponents.separateparagraphs0(sha1key, thetext)
            component.environment[sha1key]['component_separated'] = thetext

    # After breaking into paragraphs, the components in a paragraph need to have
    # their 'parent' updated, to indicate that the nearest enclosing object is
    # now that paragraph.
    # Do the same for items.  Maybe those should be separated.

# why was this inside the previous loop?
    logging.info("updating the parents of components in paragraphs")
    for sha1key in list(component.environment.keys()):
        if component.environment[sha1key]['marker'] in ['text', 'item']:
            thetext = component.environment[sha1key]['component_separated']
            re.sub("("+component.sha1heads_all+")([0-9a-f]{40})END",
                    lambda match: change_parent(match,sha1key),thetext)

#------------#

def change_parent(txt, theparent):
    this_child = txt.group(2)
    component.environment[this_child]['parent'] = theparent  

######################

def separate_isolated_figures():
    """Process \includegraphics in paragraphs, outside figure.

    """

    logging.info("separating isolated figures")
    for sha1key in list(component.environment.keys()):

        comp = component.environment[sha1key]
        if comp['marker'] in ['text','center','minipage']:
            thetext = comp['component_separated']
            (image_ratio, startingimagefile, thetext) = (
                                 separatecomponents.extract_isolated_images(thetext) )
            component.environment[sha1key]['component_separated'] = thetext
            component.environment[sha1key]['image_ratio'] = image_ratio
            component.environment[sha1key]['image_file_tex'] = startingimagefile

            thetext = re.sub(r"\\captionof *(\{.*)",
                        lambda match: separatecomponents.extract_captionof(match,sha1key),thetext,1,re.DOTALL)
            component.environment[sha1key]['component_separated'] = thetext

###################

def convert_tex_markup_to_html():
    """Convert the LaTeX markup in each component to HTML, where the
    conversion depends on environment of each component.

    """

    logging.info("converting LaTeX markup to HTML in various environments")

    for sha1key in list(component.environment.keys()):
        comp = component.environment[sha1key]
        marker = comp['marker']

        if marker in component.verbatim_environments:
            continue

        thetext = comp[component.target]
        if not thetext:
            continue

        if marker in component.math_environments or marker == "$":
            thetext = utilities.modify_displaymath(thetext)
        else:

#            thetext = utilities.fix_bad_font_directives(thetext)
#                       # that should be elsewhere, as a latex conversion
#
            if component.target == 'html':
                thetext = utilities.tex_to_html_fonts(thetext)
                thetext = utilities.tex_to_html_alphabets(thetext)
                thetext = utilities.remove_silly_brackets(thetext)
                thetext = utilities.tex_to_html_text_only(thetext)
            elif component.target == 'ptx':
                thetext = utilities.tex_to_ptx(thetext)
         #       thetext = utilities.tex_to_ptx_fonts(thetext)
         #       thetext = utilities.tex_to_ptx_alphabets(thetext)
         #  # need to put this back once we decide how to not apply it to tikz
         #  #     thetext = utilities.remove_silly_brackets(thetext)
 

# note when refactoring:
# make a clear divide between replacing latexx by HTML,
# and then expanding all the sha1 codes.

            if marker not in component.environments_with_linebreaks:
                thetext = utilities.tex_to_html_spacing(thetext)

        thetext = utilities.tex_to_html_other(thetext)

        component.environment[sha1key][component.target] = thetext

###################

def convert_text_in_math():
    """ \text{...} in math should use $..$ not \(..\)
        (But I don't know why.  Mathjax bug?)

    """

    # this didn't work because things have not been expanded yet

    return ""

    for sha1key in list(component.environment.keys()):
        comp = component.environment[sha1key]
        if comp['marker'] == "text":
            thetext = comp[component.target]
            logging.debug("found this text %s", thetext)
            thetext = re.sub(r"\\\(","$",thetext)
            thetext = re.sub(r"\\\)","$",thetext)
            component.environment[sha1key][component.target] = thetext

###################

def convert_non_mathjax_math():
    """For the math that MathJax can't handle, we convert to an image.

    """

    logging.info("converting non-MathJax math to images")
    for sha1key in list(component.environment.keys()):
        comp = component.environment[sha1key]
        marker = comp['marker']
        if marker == "picture":
            logging.debug("found a picture %s", comp['component_separated'][:80])

        if marker not in component.math_environments and marker not in ["tabu","tabular","tabularx","minipage","picture"]:
            continue

        thetext = comp['component_separated']

        numberedeqn = False

        if ("xymatrix" in thetext or 
           r"\xygraph" in thetext or 
           r"\diagram" in thetext or 
           r"\begin{mathdiagram}" in thetext or  # diagram is its own stand-alone nvironment, called mathdiagram when inside math
           r"\begin{CD}" in thetext or
           r"\begin{xy}" in thetext or
           r"\young{" in thetext or
           r"\tableau" in thetext or
           r"\vsquare{" in thetext or   # 1301_3569
           r"\bordermatrix" in thetext):
            try:
                thecodenumber = comp['codenumber']
            except KeyError:
                thecodenumber = ""

            thetext = makeoutput.expand_sha1_codes(thetext, markup="latex")
            thetext = re.sub(r"{mathdiagram}", r"{diagram}", thetext)
            logging.debug("converting a non-MathJax item")
            logging.debug("the marker: %s",marker)
            logging.debug("after expanding: %s",thetext[:80])

            try:
                this_star = comp['star']
            except KeyError:
                this_star = ""

            if (thecodenumber and marker in component.math_environments and not comp['star']
                   and marker not in ['diagram']):  # no tag for tabular
                numberedeqn = True
                thetext = "{" + thetext + "}"
                thetext = thetext + '\\quad\\quad\\quad\\quad\\quad' + r'('+thecodenumber+')'
                if marker not in ['array']:     # because align starts with something like {cr|ccc}
                    thetext = '\\quad\\quad\\quad\\quad\\quad' + thetext 
            logging.debug("Separating xymatrix from %s",thetext[:100])
   # maybe next line should be the original marker, which could be something like "align"
            if marker == r"$":
                thetext = r'$' + thetext + r'$'
            elif marker == "diagram":
                thetext = r'\begin{'+marker+'}' + thetext + r'\end{'+marker+'}'
            elif marker in component.math_environments:
                thetext = r'\begin{'+marker+'*}' + thetext + r'\end{'+marker+'*}'
            else:
                if marker == "picture":   # not sure this can ever happen
                    logging.debug("convertingpicture")
                thetext = r'\begin{'+marker+'}' + thetext + r'\end{'+marker+'}'
            thenewtext = utilities.convert_some_math_to_html_img(thetext, hasequationnumber=numberedeqn)
            component.environment[sha1key][component.target] = thenewtext

            component.environment[sha1key]['marker'] = 'image'

        elif marker == "picture":
            logging.debug("before expanding: %s",thetext[:180])
            thetext = makeoutput.expand_sha1_codes(thetext, markup="latex")
            logging.debug("after expanding: %s",thetext[:180])

            checknonempty = re.sub(r"^\s*\([0-9]+\s*,\s*[0-9]+\)\s*","",thetext,1)  
                                                 # if the picture is only (6,4)
            if not checknonempty:
                component.environment[sha1key][component.target] = ""
                component.environment[sha1key]['marker'] = "none"
                continue

            thetext = r'\begin{'+marker+'}' + thetext + r'\end{'+marker+'}'
            thenewtext = utilities.convert_some_math_to_html_img(thetext, hasequationnumber=numberedeqn)
            component.environment[sha1key][component.target] = thenewtext

            component.environment[sha1key]['marker'] = 'image'

###############

def maketopmatter():

    # currently Cremona's lecture notes is the only document with frontmatter.
    # when that changes, do this better.
    # Note: the existence of topmatter is currently indicated on the command line.
    component.environment['frontmatter'] = {'marker':'frontmatter'}

    thetopmatter = "These lecture notes provide supplementary material for the course\n"
    thetopmatter += "\\emph{MA257: Introduction to Number Theory},\n"
    thetopmatter += "taught by Professor John E. Cremona at Warwick University,\n"
    thetopmatter += "Winter term, 2016."

    component.environment['frontmatter']['component_separated'] = thetopmatter

