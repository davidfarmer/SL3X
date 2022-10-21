# -*- coding: utf-8 -*-

import sys
import os.path
import re
import json
import logging
import codecs

import utilities
import component
import processenvironments
import preprocess
import dandr
import makeoutput
import mapping

####################################
#
# These functions separate the document into its components:
# preamble, header, sections, subsections, subsubsecitons,
# appendices, bibliography.
#
# These functions often occur in pairs:
#    the first uses a regular expression to locate a component of
#    the document and then pass it off to the second function, which
#    puts the component into the appropriate variable/list/dictionary.
#
####################################

def killunnessarytex(text):
    """Delete everything after the end of the document, and some other junk."""

    newtext = text
    logging.info("removing un-necessary tex")

    newtext = re.sub(r"\n\s*\\end{document}.*", r"", newtext,0,re.DOTALL)  # avoid  deleting after  %\end{document}
    newtext = re.sub(r"\n\s*\\endinput.*", r"", newtext,0,re.DOTALL)

    # we should hide instead of delete comments
    newtext = re.sub(r"([^%])\\begin{comment}.*?\\end{comment}", r"\1", newtext,0,re.DOTALL)

    # also should hide typepout
    newtext = utilities.replacemacro(newtext, "typeout", 1, "")

    # meaningless \\ at end of environment
    newtext = re.sub(r"\\\\(\s+\\end\{)",r"\1",newtext)

    return newtext

##########

def killcomments(text):
    """Delete TeX/LaTeX comments."""

    newtext = text
    logging.info("removing comments")

    # Think about hiding comments instead of deleting them.

    # A line starting with % should be removed completely, including
    # the line feed at the end.  Everything after a % in the middle
    # of a line should be removed, but not the line feed at the end.
    # (Except \% is a literal TeX percent sign.)
    newtext = re.sub(r"\\\\[%]", r"\\\\ %", newtext)   # because \\% in latex means \\ followed by a comment
                          # Use [%] because % is an operator.

    newtext = re.sub(r"[%]+", "%", newtext)   # collapse multiple percents
    newtext = re.sub(r"[%](\S+)[%]\n", r"%\1" + "\n", newtext)  # partial fix for the warning below
    newtext = re.sub(r"\n *[%].*", "", newtext)    # was \n\s, but \s could be \n
    newtext = re.sub(r"(\S)[%]+\n(\S)",r"\1\2",newtext)      # when the end-of-line % is meant to be eaten
    newtext = re.sub(r"([^\\])[%].*", r"\1", newtext)
    newtext = re.sub(r"^[%].*", "", newtext)   # kill a comment that starts at the top of the file

    # warning: the above fails in the following case:
    #A % B %
    #C
    # because first you get
    #A % B C
    # and then B and C are killed

    # These are already removed by killunnecessarytex, but shoudl also
    # be here for completeness
    newtext = re.sub(r"\\begin{comment}.*?\\end{comment}", r"", newtext,0,re.DOTALL)

    return newtext

##########

def input_and_preprocess_a_file(txt, preprocess=True):

    utilities.something_changed_file += 1

    filestub = txt.group(2).strip()
    if "." in filestub and filestub.endswith(('bib','bbl')):   # a hack because I am doing bibliographies stupidly
        filename = filestub
        filename2 = "iGNoRE"
    else:
        filename = filestub + ".tex"
        filename2 = filestub   # sometimes people leave off the extension
    
    oldinputfilename = component.inputfilename

    newinputfilename = component.inputdirectory + filename
    newinputfilename2 = component.inputdirectory + filename2
    newinputfilename3 = component.workingdirectory + filename
    newinputfilename4 = component.workingdirectory + filename2
    logging.info("looking for these files:\n%s\n%s\n", newinputfilename, newinputfilename2)
    print("looking for these files:", newinputfilename)

    if os.path.exists(newinputfilename):
   #     newinputfile = codecs.open(newinputfilename,'r', 'utf-8')
        component.inputfilename = newinputfilename
   #     logging.info("inputting the file: %s",newinputfilename)
    elif os.path.exists(newinputfilename2):
   #     newinputfile = codecs.open(newinputfilename2,'r', 'utf-8')
   #     logging.info("inputting the file: %s",newinputfilename2)
        component.inputfilename = newinputfilename2
    elif os.path.exists(newinputfilename3):
   #     newinputfile = codecs.open(newinputfilename3,'r', 'utf-8')
   #     logging.info("inputting the file: %s",newinputfilename3)
        component.inputfilename = newinputfilename3
    elif os.path.exists(newinputfilename4):
   #     newinputfile = codecs.open(newinputfilename4,'r', 'utf-8')
   #     logging.info("inputting the file: %s",newinputfilename4)
        component.inputfilename = newinputfilename4

    else:
        logging.critical("input file %s does not exist", newinputfilename)
        return "IIIII"

    try:
        logging.info("inputting the file: %s",component.inputfilename)
        newinputfile = codecs.open(component.inputfilename,'r', 'utf-8')
        newcontents = newinputfile.read()
    except UnicodeDecodeError:
        logging.info("inputting as latin-1")
        component.source_encoding = 'iso-8859-1'
        newinputfile = codecs.open(component.inputfilename,'r', component.source_encoding)
        newcontents = newinputfile.read()
#        print type(newcontents)
#        newcontents = newcontents.decode('iso-8859-1',errors='ignore')
#        newcontents = newcontents.encode('utf8',errors='ignore')

   # print "newcontents", component.inputfilename, newcontents

    newinputfile.close()

    if component.inputfilename in component.known_files:
        logging.critical("circular reference to file %s", component.inputfilename)
        return ""
    else:
        component.known_files.append(component.inputfilename)

    component.workingdirectory = re.sub(r"[^/]*$","",component.inputfilename)

    if preprocess:
        logging.debug("preprocess, initial_preparations")
        newcontents = dandr.initial_preparations(newcontents)

    try:
        newcontents = newcontents.encode('utf-8', errors="ignore")
    except UnicodeDecodeError:
        logging.critical("font encoding problem with %s", component.inputfilename)

    logging.debug("leaving input_and_preprocess_a_file")

    return newcontents

############

def input_and_preprocess_a_package(txt):

    utilities.something_changed_file += 1

    logging.debug("in input_and_preprocess_a_package")
    squaregroup = txt.group(2)
    filestubs = txt.group(4)
    filelist = filestubs.split(",")
    allnewcontents = ""

    extensions_to_try = [".sty",".cls"]

    for fs in filelist:
        filestub = fs.strip()

        # throw away some journal class/style files
        if filestub in mapping.style_files_to_omit:
            logging.info("skipping a .cls file we can't use: %s",filestub)
            continue
        for ext in extensions_to_try:
            filename = filestub + ext
            file_to_test = component.inputdirectory + filename
            if os.path.isfile(file_to_test):
                logging.info("found a style file to import: %s", file_to_test)
# should use "with" here
                newinputfile = codecs.open(file_to_test,'r','utf-8')
                newcontents = newinputfile.read()
                newinputfile.close()

                logging.debug("processing newcontents")
                newcontents = dandr.initial_preparations(newcontents)
                allnewcontents += newcontents

    return allnewcontents

############

def extract_newtheorems(text):
    """Find the definition of the theorem-like objects, and decide
    if they should be ignored (because we already know them),
    converted (because they are equivalent to something we already know),
    or expanded (because we can't think of what else to do with them).

    In the last case, we need to use a generic theorem-like envoronment
    with the type-name as a parameter.  [not implemented yet]

    """

    thetext = text

    logging.info("extract_newtheorems")

    find_thm = r"(\\newtheorem)\b\s*"
    find_thm += r"\*{0,1}"    # possibly followed by a *
    find_thm += r"\s*"    # possibly followed by white space
    find_thm += r"((\[|\{).*)"    # followed by anything that starts with [ or { 

    thetext = re.sub(find_thm,extract_newthm,thetext,1,re.DOTALL)
            # do them one at a time

    return(thetext)


def extract_newthm(txt):

    utilities.something_changed += 1
    utilities.what_changed = txt

    texcommand = txt.group(1)
    everythingelse = txt.group(2)

  # first extract the square group (currently unused)
    if everythingelse.startswith("["):
        thesqgrp, everythingelse = utilities.first_bracketed_string(everythingelse, 0, "[", "]")
        thesqgrp = utilities.strip_brackets(thesqgrp,"[","]")
        logging.debug("found a newtheorem with sqgrp %s", thesqgrp)

  # then extract the marker
    if everythingelse.startswith("{"):
        themarker, everythingelse = utilities.first_bracketed_string(everythingelse)
        themarker = utilities.strip_brackets(themarker)
        logging.info("found a newtheorem: %s", themarker)

    else:   # LaTeX source does not have the marker in curly brackets
            # nor does the marker start with \ , so something
            # is wrong
        return everythingelse

    everythingelse = everythingelse.lstrip()
  # now extract the counter

    if everythingelse.startswith("["):  # counter exists
        counter, everythingelse = utilities.first_bracketed_string(everythingelse,0,"[","]")
        counter = utilities.strip_brackets(counter,"[","]")
    else:
        counter = ""

    everythingelse = everythingelse.lstrip()

  # now extract the displayname
    if everythingelse.startswith("{"):
        thedisplayname, everythingelse = utilities.first_bracketed_string(everythingelse)
        thedisplayname = utilities.strip_brackets(thedisplayname)

    else:   # LaTeX source does not have the displayname in curly brackets
            # nor does displayname start with \ , so something is wrong
        logging.error("problem extracting a newtheorem: %s", everythingelse[:20])
        return everythingelse

    if everythingelse.startswith("["):  # orderby exists
        orderby, everythingelse = utilities.first_bracketed_string(everythingelse,0,"[","]")
        orderby = utilities.strip_brackets(orderby,"[","]")
    else:
        orderby = ""

    # we have the complete definition, so save it.
    if not themarker:
        logging.error("empty marker")

    if thedisplayname.lower() in list(mapping.environment_abbrev.keys()):    # an environment we know
        if (themarker in mapping.environment_abbrev[thedisplayname.lower()] or
               themarker == thedisplayname.lower()):   # an abbreviation we already know
            logging.info("no need to save this environment, because we already know it")
            return everythingelse
        else:
            logging.warning("an unknown abbreviation %s of a known environment %s",
                           themarker, thedisplayname)

    component.newtheorems_parsed.append({'texcommand':texcommand,
                                         'themarker':themarker,
                                         'counter':counter,
                                         'thedisplayname':thedisplayname,
                                         'orderby':orderby})

    #if the marker may be usable by mathjax, save it to component.definitions
    # this needs to be cleaned up
    logging.debug("newtheorem with texcommand %s and marker %s and displayname %s",
                   texcommand, themarker, thedisplayname)

    # not sure why we do this next step.  does it repeat a check from above?
    if ( (thedisplayname.lower() in list(component.environment_types.keys())) and
          (themarker not in list(component.environment_types.keys())) ):
        logging.warning("Seems to be a known environment %s, but an unknown abbreviation, %s",
                       thedisplayname, themarker)

    return everythingelse

############

def extract_newenvironments(text):
    """Currently we just delete newenvironment commands."""

    thetext = text
    logging.info("extract_newenvironments (actually, deleting them)")
    # first delete the indication that the newenvironment has parameters
    thetext = re.sub(r"\\newenvironment{([^}]+)}\[[^\]]*\]",r"\\newenvironment{\1}",thetext)
    # do it twice for \newenvironment{definition}[1][]{\begin{defn}[#1]\pushQED{\qed}}{\popQED \end{defn}}
    thetext = re.sub(r"\\newenvironment{([^}]+)}\[[^\]]*\]",r"\\newenvironment{\1}",thetext)
    thetext = utilities.replacemacro(thetext,"newenvironment",3,"")

    return thetext

############

def extract_definition(text):
    """Find one definition, try to parse it, and save in various places.

    """

    thetext = text

    logging.debug("starting extract_definition")


    # Set up a regular expression to find macros
    find_def = r"(\\let|\\def|\\newcommand|\\renewcommand|\\providecommand|\\DeclareMathOperator)\b\s*"
                              # some day add support for DeclareMathSymbol
    find_def += r"\*{0,1}"    # possibly followed by a *
    find_def += r"\s*"    # possibly followed by white space
    find_def += r"((\{|\\).*)"    # followed by anything that starts with { or \

    thetext = re.sub(find_def,extract_def,thetext,1,re.DOTALL)
                                                  # do them one at a time
    return(thetext)


def extract_def(txt):

    utilities.something_changed += 1
    utilities.what_changed = txt

    texcommand = txt.group(1)
    everythingelse = txt.group(2)

    logging.debug("found a def %s with %s tttttt",texcommand, everythingelse[:10])

  # first extract the macro
    if everythingelse.startswith("{"):
        themacro, everythingelse = utilities.first_bracketed_string(everythingelse)
        themacro = utilities.strip_brackets(themacro)
        themacro = themacro.strip()
        logging.debug("just produced the macro %s xxx", themacro)

    elif everythingelse[0] == "\\":   # maybe we should completely separate \def style from \newcmmand style?
        themacro = "\\"
        everythingelse = everythingelse[1:]

        # hack to handle examples like \def\proved\qedhere or \let \O=\Omega
        found_def = re.match(r"([a-zA-Z]+)\s*=*\s*(\\[a-zA-Z]+)\s*(.*)",everythingelse,re.DOTALL)
        if found_def:
            themacro = "\\"+found_def.group(1)
            everythingelse = found_def.group(2) + "\n" + found_def.group(3)
            logging.debug("now just produced the macro %s and everythign else starts %s", themacro, everythingelse[:50])
            
        # hack to handle things like \def\|{...}
        elif everythingelse[1] == "{":
            themacro = "\\" + everythingelse[0]
            everythingelse = everythingelse[1:]

        else:
            cc = 0
            logging.debug("setting cc=0, which counts characters in the macro")

            # we set this loop to me more agressive, which made partially obsolete AAAAAA below
            while len(everythingelse) > 0 and re.match(r"[a-zA-Z@#0-9]",everythingelse[0]) and cc < 99:
                           # could the macro have more than 100 characters?
                cc += 1
                themacro += everythingelse[0]
                everythingelse = everythingelse[1:]

    else:   # LaTeX source does not have the macro in curly brackets
            # nor does the macro start with \ , so something
            # is wrong
        logging.error("messed-up macro near %s", everythingelse[:50])
        return everythingelse

    everythingelse = everythingelse.lstrip()

    # now extract the numargs, which are in square brackets
    if (texcommand in [r"\newcommand",r"\renewcommand",r"\providecommand"] and
              everythingelse.startswith("[") ):  # numargs is 1 or more
        logging.debug("found a macro with multiple arguments %s", everythingelse[:10])
        numargs, everythingelse = utilities.first_bracketed_string(everythingelse,0,"[","]")
        try:
            numargs = int(utilities.strip_brackets(numargs,"[","]"))   # we use numargs to count
        except ValueError:
            logging.error("number of arguments shold have been an integer:")
            logging.error("first group %s", txt.group(1))
            logging.error("second group starts %s", txt.group(2)[:100])
            numargs = 0


        if everythingelse.startswith(r"["):  # I don't know why that would happen , but it does
            second_numargs, everythingelse = utilities.first_bracketed_string(everythingelse,0,"[","]")
            logging.warning("found a second_numargs %s",second_numargs)

        else:
            second_numargs = ""
    else:
        numargs = 0  # ""  (previously we used a string)
        second_numargs = ""  # (still use a string for this, because of \newcommand{\V}[3][r]{\| #2 \|_{V^{#1}_{#3}}}  from 1409.7120
        # AAAAAA this if is partially obsolote, as noted above.  See BBBBB below for a partial fix
    if everythingelse.startswith(r"#"):   # assume we have \def\mycmd#1{...}  (of course, it can be more complicated)
                                          # for example, \def\Times_#1{\mathop{\times}_{#1}}   (see * below)
        logging.info("parsing a definition like \def\mycmd#1{...} with macro %s", themacro)
        if texcommand == r"\def":
            texcommand = r"\newcommand"
            themacro = re.sub(r"[^a-zA-Z\\]","",themacro)         # (see * above )   # I don't understand
        numargs = 0
        while everythingelse.startswith(r"#"):
            everythingelse = everythingelse[2:]
            numargs += 1
            logging.info("numargs is at least %s",numargs)
    
    # Note: the above fails to correctly parse things like
    #   \def \foo [#1]#2{The first argument is ``#1'', the second one is ``#2''} 
    # We prefer LaTeX, not plain tex. 

    # this is just to handle \newcommand{\komment}[1]  *followed by blank lines* that someone used once
    if everythingelse.startswith("\n\n"):
        return everythingelse

    everythingelse = everythingelse.lstrip()

    # BBBBB  this is to handle macros like \def\xxxx#1#2{...}
    if texcommand == r"\def":
#### CHECK ON THIS!!!
        macrostripped = re.sub(r"^\\[@a-z]+","",themacro)
        if macrostripped == r"#1":
            texcommand = r"\newcommand"
            numargs = 1
            themacro = themacro[:-2]
            logging.warning("converted a one argument def to newcommand: %s", themacro)
        elif macrostripped == r"#1#2":
            texcommand = r"\newcommand"
            numargs = 2
            themacro = themacro[:-4]
            logging.warning("converted a two argument def to newcommand: %s", themacro)

    # now extract the definition
    if everythingelse.startswith("="):  # someone did \let\al=\alpha  (why?)
        logging.warning("found a silly equals sign %s", everythingelse[:30])
        everythingelse = everythingelse[1:].lstrip()    # get rid of the = and maybe a space after it
    if everythingelse.startswith("{"):
        thedefinition, everythingelse = utilities.first_bracketed_string(everythingelse)
        thedefinition = utilities.strip_brackets(thedefinition, depth=1)

    elif everythingelse.startswith("\\"):
             # the definition is not in curly brackets, so where does it end?
             # a reasonable guess is that it ends ad the end of the line?  or where the next definition starts?
        startofhtedefinition = everythingelse[0]
        everythingelse = everythingelse[1:]

        theendofthedefinition, everythingelse = utilities.text_before(everythingelse,["\\def","\\let","\n"])
        thedefinition = startofhtedefinition + theendofthedefinition

    else:   # LaTeX source does not have the definition in curly brackets
            # nor does the definition start with \ , so something
            # is wrong
        logging.error("something went wrong, with the definition of %s followed by %s", themacro, everythingelse[:50])
        logging.error("guessing that the definition is everything up to the end of the line")
        thedefinition, everythingelse = utilities.text_before(everythingelse,"\n")
        if not thedefinition:
            thedefinition = everythingelse
            everythingelse = ""

    thedefinition = utilities.modify_displaymath(thedefinition)
    # we have the complete definition, so save it.

    if not themacro:
        logging.error("empty macro")
    if component.target == 'ptx':
        thedefinition = re.sub("<", r"\\lt ",thedefinition)
        thedefinition = re.sub("&", r"\\amp ",thedefinition)

    if themacro not in mapping.known_macros and themacro[1:] not in mapping.macros_to_ignore and themacro != thedefinition:
        # need that last check to be more robust, to catch \def{\xx}{\xx 1}
        component.definitions_parsed_all[themacro] = ({'texcommand':texcommand,
                                                     'themacro':themacro,
                                                     'numargs':numargs,
                                                     'secondnumargs':second_numargs,
                                                     'thedefinition':thedefinition})

    if "textsc" in thedefinition:
        thedefinition = utilities.replacemacro(thedefinition,"textsc",1,"#1")

    if "&" in thedefinition:   # mathjax has trouble with \begin{array}{cc}#1&#2\\#3&#4\end{array}
        thedefinition = re.sub(r"(\S)&",r"\1 &",thedefinition)
        thedefinition = re.sub(r"&(\S)",r"& \1",thedefinition)
            # sort-of a hack to reassemble  &#9889;
        thedefinition = re.sub(r"& (#[0-9]{3}|nbsp)",r"&\1",thedefinition)

#   component.definitions_parsed are used to expand macros, and to put into LaTeX files

    if ("@" not in themacro and
         themacro and                   
        "ifthen" not in thedefinition and
        "ifx" not in thedefinition and
        "ifcase" not in thedefinition and
        "iftoggle" not in thedefinition and
        "##" not in themacro and
        "{" not in themacro and
        themacro != thedefinition and 
        themacro[1:] not in mapping.macros_to_ignore    # and
        #  "@" not in thedefinition
       ):
        component.definitions_parsed[themacro] = ({'texcommand':texcommand,
                                         'themacro':themacro,
                                         'numargs':numargs,
                                         'thedefinition':thedefinition})

    #if the macro may be usable by mathjax, save it to component.definitions
    # this needs to be cleaned up
    
    if "\\fam\\" in thedefinition:
        thedefinition = "#1"
    # to catch macros like \def\email#1{...}
    this_macro = themacro[1:]
    if not this_macro:
        logging.error("empty macro, with definition %s",thedefinition[:100])
        logging.error("amidst everythingelse %s",everythingelse[:100])
        return everythingelse
    elif this_macro[0].isalpha():
        this_macro = re.match(r"([a-zA-Z]+)",this_macro).group(1)
    logging.debug("this_macro is %s",this_macro)

#   component.definitions are put into the html files

    if (r"\(" not in themacro) and (r"\)" not in themacro and
        len(themacro) > 1 and
        themacro[1] not in ["\\", "[", "]", "(", ")"] and
        this_macro not in ["left","right"] and
        this_macro not in ["rm","bf"] and
        this_macro not in ["frak","cal"] and
        this_macro not in mapping.macros_to_ignore and
        "margin" not in thedefinition and
        "\\vrule" not in thedefinition and
        "\\height" not in thedefinition and
        "\\width" not in thedefinition and
 #       "\\setlength" not in thedefinition and  -- see \mat in 1306.0068
        "\\put" not in thedefinition and
        "\\ifx" not in thedefinition and
        "\\else" not in thedefinition and
        "\\ifcase" not in thedefinition and
        "\\setboolean" not in thedefinition and
        "\\foreach" not in thedefinition and
        "minipage" not in thedefinition and
        "joinrel" not in thedefinition and   # mathjax doesn't know that
        "newcommand" not in thedefinition and
        "\\def" not in thedefinition and
        "\\setbox" not in thedefinition and
        "fancy" not in thedefinition and
        "penalty" not in thedefinition and
        "##" not in themacro and
        "*" not in themacro and
        "@" not in themacro and
        "@" not in thedefinition and
        "baseline" not in themacro and
   #     "begin{" not in themacro and  -- see \mat in 1306.0068
        (r"\st" != themacro or r"#1" not in thedefinition) and
        "]}{" not in themacro        # a malformed macro \newcommand{\cccc[1]}{...} causes MathJax to choke
       ):

        thedefinition = utilities.fix_definition(thedefinition)

#  should also check that brackets are balanced in the definition

        if texcommand == r"\let":
            texcommand = r"\def"       # had trouble with \let in MathJax, probably because the source was wrong
        if texcommand == r"\providecommand":
            texcommand = r"\renewcommand"       # had trouble with \providecommand in MathJax, but don't know why

        if texcommand in [r"\def",r"\let"]:
            thefulldefinition = texcommand+themacro
        else:
            thefulldefinition = texcommand+"{"+themacro+"}"
        if numargs:
            thefulldefinition += "[" + str(numargs) + "]"
            if second_numargs:     # probably can do this in every case because False means ""
                thefulldefinition += second_numargs

     #   if thedefinition.endswith("{"):
        if not utilities.balanced_brackets(thedefinition):
            logging.error("problem with macro %s ::::::: %s", thefulldefinition, thedefinition)
        else:
            thedefinition = "{"+thedefinition+"}"
            thefulldefinition += thedefinition
            component.definitions.append(thefulldefinition)
            logging.debug("just saved the definition %s",thefulldefinition)
    else:
        logging.warning("rejected the macro %s with definition %s", themacro, thedefinition)

    return everythingelse

############

def separateextras(text):

    logging.info("separating the extras")
    thetext = text

    extras_types = {"primaryclass","keywords","thanks"}

    for extra in extras_types:
        thetext = re.sub(r"\\("+extra+")\s*\[[^\[\]]+\]\s*","\\\\"+extra,thetext,0,re.DOTALL)
        thetext = re.sub(r"\\("+extra+")\s*{(.*)",separateextr,thetext,0,re.DOTALL)
         # the 0 means that if an extra occurs more than once, we only save the last one

    # need to do something better  with footnotetext in title/author
    extra = "footnotetext"
    thetext = re.sub(r"\\("+extra+")\s*\[[^\[\]]+\]\s*","\\\\"+extra,thetext)
    thetext = utilities.replacemacro(thetext,extra,1,"")

    return thetext

def separateextr(txt):

    extra_type = txt.group(1)
    everythingelse = "{"+txt.group(2)

    the_extra, everythingelse = utilities.first_bracketed_string(everythingelse)
    the_extra = utilities.strip_brackets(the_extra)

    component.extras[extra_type] = the_extra   # why in extras instead of an environment?
                                               # could it be text that needs further processing?

    # see use of footnoretext in http://sl2x.aimath.org/development/collectedworks/htmlpaper/math__9807026/

    return everythingelse

############

def separatepreamble(text):
    """Remove everything up to and including \begin{document}
    and put it in component.preamble .
    """

    logging.info("separating the preabmble")
    thetext = text

    if "\\begin{document}" not in text:
        logging.critical("no \\begin{document}")
        logging.critical("document begins",text[:1000])
        logging.critical("exiting")
        sys.exit()

    # there may be more than one \begin{document}, possibly due to having one
    # in each included file.  Assume the first one is the "real" one and then
    # delete the others
    thetext = re.sub(r"(.*?)\\begin{document}",separatepreamb,thetext,1,re.DOTALL)
    thetext = re.sub(r"\\begin{document}","",thetext)

    logging.info("done separating the preamble")

    return(thetext)


def separatepreamb(txt):

    component.preamble = txt.group(1)

    return ""

############

def separateheader(text):
    r"""Remove everything up to and including \maketitle,
        and put in component.header .

    """

    logging.info("separateing the header")
    thetext = text

    # should we check there is at most one \maketitle?

    thetext = re.sub(r"^(.*)\\maketitle",separatehead,thetext,0,re.DOTALL)

    logging.debug("done separateing the header")
    return(thetext)

def separatehead(txt):

    component.header = txt.group(1)

    return ""

############

def authors_title_from_known_paper():

    logging.debug("in authors_title_from_known_paper")
    logging.info("authors were %s",component.authorlist)

# need to fix: use database
    known_papers_file = "../collectedworks/known_papers"
    with open(known_papers_file) as infile:
        known_works = json.load(infile)
    if component.known_paper_code in known_works:
        author_dict_list = known_works[component.known_paper_code]['authors']
        new_author_list = []
        for auth in author_dict_list:
            if auth:
                new_author_list.append(auth['firstname']+" "+auth['lastname'])
        component.authorlist = new_author_list
        if component.title == "Title Goes Here":
            logging.warning("    replacing the UNKNOWN title")
            component.title = known_works[component.known_paper_code]['title']
            logging.warning("title is now %s", component.title)
            component.environment['title'] = {'marker':"title",
                                              'component_separated': component.title}
        else:
            logging.warning("Keeping the title: %s", component.title)
        if 'title' not in component.environment:
            component.environment['title'] = {'marker':"title",
                                              'component_separated':"Title Goes Here"}
            logging.error("missing title")

        if component.environment['title']['component_separated'] == "Title Goes Here":
            logging.warning("replacing the UnKnOwn title")
            if 'title' in known_works[component.known_paper_code]:
                component.environment['title']['component_separated'] = known_works[component.known_paper_code]['title']
            else:
                component.environment['title']['component_separated'] = "Unknown Title"
                logging.error("unknown title of known work: %s", component.known_paper_code)

        logging.warning("authors are now %s", component.authorlist)
    else:
        logging.warning("not a known paper, %s, authors have not changed",component.known_paper_code)


############

def separateauthors():
    # need to rethink this function, particularly since the authors are in a database now

    logging.info("separateauthors")
    numberofauthors = len(component.authorlist)

    component.authorlist_html = []
    for author in component.authorlist:
        logging.debug("do we know %s",author)
        known_author = utilities.data_of_author(author, component.known_people)
        logging.debug("here is what we know: %s",known_author)
        if known_author:
            author_in_html = '<a href="http://sl2x.aimath.org/development/collectedworks/of/'
            link_name = utilities.author_name_for_link(known_author)
            author_in_html += link_name
            author_in_html += '/">'
            if 'preferredfullname' in known_author and known_author['preferredfullname']:
                full_name = known_author['preferredfullname']
            else:
                full_name = known_author['firstname']+" "+known_author['lastname']
            logging.debug("their full name is %s",full_name)
            author_in_html += utilities.tex_to_html_alphabets(full_name)
            author_in_html += '</a>'
            logging.debug("and in html they are %s",author_in_html)

        else:
            author_in_html = utilities.tex_to_html(author)
            author_in_html = utilities.remove_silly_brackets(author_in_html)
        component.authorlist_html.append(author_in_html)

    component.author_html = ", ".join(component.authorlist_html)
    logging.info("number of authors is %s",numberofauthors)

    # Make author_html with appropriate serial commas
    if numberofauthors > 2:
        component.author_html = re.sub(", *([^ a-z][^,]+)$",r", and \1",
                                       component.author_html)
    else:
        component.author_html = re.sub(", ([^,]+)$", r" and \1",component.author_html,1)


############

def separatebibliography(text):
    """Remove the bibliography and put it in component.bibliography .

       \\bibliography{filename}

       or

       \\begin{thebibliography}...\\end{thebibliography}

    """

    # this should be in the same location as the other code that reads in files.
    # (then remove import codecs from here)


    logging.info("separating the bibliography")
    thetext = text

    thetext = re.sub(r"\\bibliographystyle{[^{}]*}","",thetext)

    # \bibliography{...} can mean a bibtex file, or just a separate file
    # that is in \bibitem format
    if r"\bibliography{" in thetext:
        thetext = re.sub(r"\\bibliography{([^{}]+)}",inputbiblio,thetext)
    else:
        thebib = re.sub(r".*\\begin\s*{thebibliography}(.*?)(\\end{thebibliography}|$)", r"\1", thetext)
        component.bibliography += thebib
        thetext = re.sub(r"\\begin\s*{thebibliography}.*", "", thetext, 0, re.DOTALL)

#    thetext = re.sub(r"\\begin{thebibliography}(.*)\\end{thebibliography}",
#                     separatebiblio,thetext,0,re.DOTALL)
#    thetext = re.sub(r"\\begin{thebibliography}(.*)",         # in case \end{thebibliography} is missing
#                     separatebiblio,thetext,0,re.DOTALL)

    return(thetext)

def inputbiblio(txt):

    # may need to handle the case of mutliple files,
    # as in \bibliography{file1, file2, etc}

    bibfilestub = txt.group(1)
    if bibfilestub == "biblio":
       logging.debug("looking for a bibliography?")
    logging.debug("looking for a bibfile %s", bibfilestub)

    bibfileformats = ["bbl","bib"]

    inputfilestub = component.inputfilename
    inputfilestub = re.sub("^.*/","",inputfilestub)   # take away the directory part
    inputfilestub = re.sub("\.[^\.]*$","",inputfilestub)  # take away the extension
    logging.debug("inputfilestub: %s", inputfilestub)
    originalinputfilestub = component.originalinputfilename
    originalinputfilestub = re.sub("^.*/","",originalinputfilestub)
    originalinputfilestub = re.sub("\..*","",originalinputfilestub)
    logging.debug("originalinputfilestub: %s", originalinputfilestub)

# need to clean up this code

    bibfilename = ""
    for ext in bibfileformats:
       file_to_test = component.inputdirectory + bibfilestub + "." + ext
       logging.info("looking for the file %s", file_to_test)
       if os.path.isfile(file_to_test):
           logging.info("found it")
           bibfilename = file_to_test
           break
       file_to_test = component.inputdirectory + inputfilestub + "." + ext
       logging.info("looking for the file %s", file_to_test)
       if os.path.isfile(file_to_test):
           logging.info("found it")
           bibfilename = file_to_test
           break
       file_to_test = component.inputdirectory + originalinputfilestub + "." + ext
       logging.info("looking for the file %s", file_to_test)
       if os.path.isfile(file_to_test):
           logging.info( "found it")
           bibfilename = file_to_test
           break

    logging.info("looks like the bibfilename is %s", bibfilename)

    if not bibfilename:
        logging.error("the bibliography file %s does not exist", bibfilestub)
        return ""
    else:   # should use with
        logging.info("found the bibliography: %s", bibfilename)
        bibfile = codecs.open(bibfilename,'r', 'utf-8')
        try:
            thebibliography = bibfile.read()
        except UnicodeDecodeError:
            logging.critical("font error in bib file %s", bibfilename)
            thebibliography = "Error parsing bibliography: probably a font encoding problem in file " + bibfilename
        bibfile.close()

    thebibliography = killunnessarytex(thebibliography)  # delete comments

    thebibliography = dandr.initial_preparations(thebibliography)   # added rather late.  not sure why it wasn't there long ago

    thebibliography = re.sub(r".*\\begin{thebibliography}\s*","",thebibliography,1,re.DOTALL)
    thebibliography = re.sub(r"\s*\\end{thebibliography}.*","",thebibliography,1,re.DOTALL)

    component.bibliography += thebibliography
    logging.debug("the bibliography begins: %s", thebibliography[:100])

    return ""

#def separatebiblio(txt):
#
#    component.bibliography += txt.group(1)
#
#    logging.info("found the bibliography")
#
#    return ""

##########

def separatesections(sectionmarker,text):
    """Separate text into "sections", replacing each section by its sha1 code.

    The "sectionmarker" determines how to separate.  Each piece is saved in
    component.environment[sha1ofthetext] .  The original text ends up
    containing only sha1 codes and carriage returns.

    """

    thetext = text.strip()

    # it is legal to have "\subsection{}" in a LaTeX file, and that works in
    # the sense that you get a section marker with no title.  We don't want to
    # allow that, because sections need titles in the TOC.  So step 0 is to
    # delete those.
    thetext = re.sub(r"\\("+sectionmarker+")\s*\*?\s*\{\s*\}\s*","",thetext)

    numberofsections = len(re.findall(r"\\("+sectionmarker+")\s*\*?\s*\{",thetext))
    logging.debug("number of %s is %s", sectionmarker, numberofsections)

#    logging.debug("the whole document is %s", text)
    if numberofsections == 0:
        # hack for the case of subsubsection in a section, with no intervening subsection
        if sectionmarker == "subsection" and "subsubsection" in thetext:
            logging.warning("SUBSUB with no SUB")
            thetext = re.sub(r"\\subsubsection",r"\\subsection",thetext)
            numberofsections = len(re.findall(r"\\("+sectionmarker+")\s*\*?\s*\{",thetext))
        else:
            return thetext

    #  Since we allow text to occur before the first \section{},
    #  we treat that as a special case: "Section 0". 
    findsectionzero = "^\s*(.*?)(\\\\("+sectionmarker+")\*?\s*\{)"
    # That minimal match should be okay, but it could be replaced by
    # "does not contain sectionmarker."

    thetext = re.sub(findsectionzero,separatesec0,thetext,0,re.DOTALL)

    # now find the sections
    sectionstart = "\\\\("+sectionmarker+")"
                             # start with \section or \subseciton or ...
    sectionstart += "\s*(\*?)\s*"   # possibly folowed by a *

    for _ in range(1,numberofsections):
             # start at 1 because we find the last section after this loop
        logging.debug("in the section loop, text begins %s", thetext[:40])
        thetext = re.sub(sectionstart+"\s*({.*)", separatesect,thetext,1,re.DOTALL)  
             # only replace once, each time through the loop
    logging.debug("looking for the last section")

    thetext = re.sub(sectionstart+"\s*({.*)", lambda match: separatesect(match,finalsection=True) ,thetext,1,re.DOTALL)  
    
    return(thetext)
  
#-----------
def separatesec0(txt):

    if txt is None:
        return ""

    sec0 = txt.group(1)
    theother = txt.group(2)
    sectionmarker = txt.group(3)

    logging.debug("found a section zero with marker %s", sectionmarker)
    logging.debug("which has parent %s",component.parent)

    sec0 = sec0.strip()
    if not sec0:
        return theother

    sha1ofthetext = utilities.sha1hexdigest(sec0+"blob")

    # we use subsection0 for the  material before the first subsection
    # this is necessary to correctly increment the subsection counters
    component.environment[sha1ofthetext] = {'marker':'blob',
                                            'parent':component.parent,
                                            'sha1head':"SEC",
                                            'title':"",
                                            'sec0':sectionmarker,
                                            'component_raw':sec0,
                                            'component_separated':sec0}

    return "SEC"+sha1ofthetext+"END "+theother

def separatesect(txt,finalsection = False):

    sectionmarker = txt.group(1)
    star = txt.group(2)
    theremainder = txt.group(3)

    logging.debug("finalsection is %s", finalsection)

    component.totalnumberofsections[sectionmarker] += 1

    sectiontitle, theremainder = utilities.first_bracketed_string(theremainder)
    sectiontitle = utilities.strip_brackets(sectiontitle)

    if finalsection:
        sectiontext = theremainder
        theremainder = ""
    else:
        sectiontext, theremainder = utilities.text_before(theremainder,"\\"+sectionmarker)

    sectiontext = sectiontext.strip()

    logging.debug("sectiontext starts %s",sectiontext[:90])

    if not sectiontitle:
        logging.error("%s with no title, deleting section marker", sectionmarker)
        return theremainder

    if r"\label" in sectiontitle:  # move the label to the section text
        thelabel = re.sub(r".*\\label\s*{([^{}]*)}.*",r"\1",sectiontitle)
        sectiontitle = re.sub(r"\s*\\label\s*{([^{}]*)}\s*",r"",sectiontitle)
        sectiontext = r"\\label{"+thelabel+"}"+sectiontext

    sha1ofthetext = utilities.sha1hexdigest(sectiontext+sectionmarker)

    # is this robust enough?  why don't we treat this like math in the text?
    if component.target == 'html':
        sectiontitle = re.sub("\$([^$]+)\$",r"\\(\1\\)",sectiontitle)
    elif component.target == 'ptx':
        sectiontitle = re.sub("\$([^$]+)\$",r"<m>\1</m>",sectiontitle)

    component.environment[sha1ofthetext] = {
                                     'marker':sectionmarker,
                                     'parent':component.parent,
                                     'sha1head':'SEC',
                                     'star':star,
                                     'title':sectiontitle,
                                     'component_raw':sectiontext,
                                     'component_separated':sectiontext}

    return "SEC"+sha1ofthetext+"END "+theremainder

############

def separatemath(openingdelimiter,closingdelimiter,thetext):
    r"""Find display math with the given delimeters: $$/$$ or \[/\]."""

    findenvironment = "("+openingdelimiter+")"+"(.*?)"+closingdelimiter

    if openingdelimiter == r"\$" or openingdelimiter == r"\\\(":
        thenewtext = re.sub(findenvironment,separateim,thetext,0,re.DOTALL)
  #      thenewtext = re.sub(findenvironment,separateim,thetext)
          # could/should there be \n in inline math?
          # answer:  yes, people do that
    else:
        thenewtext = re.sub(findenvironment,separatedm,thetext,0,re.DOTALL)

    return thenewtext


def separatedm(txt):

    marker = "equation"
    markerwas = txt.group(1)
    therawtext = txt.group(0)
    sha1ofthetext = utilities.sha1hexdigest(therawtext+marker)

    thetext = txt.group(2)
    
    star = "*"        # don't number $$ or \[

    if "&" in thetext and "xymatrix" not in thetext:     # this is for the outrageous use of \[...\] in 1312.6378 and 0508388
        marker = "align"
        star = ""

    component.environment[sha1ofthetext] = {'marker':marker,
                                            'parent':component.parent,
                                            'sha1head': "mathdisplay",
                                            'star': star,  
                                            'component_raw':therawtext,
                                            'component_separated':thetext
                                            }
    return "mathdisplay"+sha1ofthetext+"END "


def separateim(txt):

    marker = r"$"
    markerwas = txt.group(1)
    therawtext = txt.group(0)
    thetext = txt.group(2)

    if "\n\n" in therawtext:
        return therawtext
    sha1ofthetext = utilities.sha1hexdigest(therawtext+marker)

    component.environment[sha1ofthetext] = {'marker':marker,
                                            'parent':component.parent,
                                            'sha1head': "mathinline",
                                   #         'star': "",
                                   #               # don't number $$ or \[
                                            'component_raw':therawtext,
                                            'component_separated':thetext
                                            }
    return "mathinline"+sha1ofthetext+"END"   # note: no extra space


############
def separateverb(thetext):
    r"""Find \verb+verbatim text goes here+ and extract it,
     where + can be anything.

    """

    findverb =  r"\\verb([^a-zA-Z])(.*?)\1"

    thenewtext = re.sub(findverb,separatevb,thetext,0,re.DOTALL)

    return thenewtext

def separatevb(txt):

    theverbatimtext = txt.group(2)
    # is it a problem that we throw away the specific character
    # marking the verb environment?

    sha1ofthetext = utilities.sha1hexdigest(theverbatimtext+"verb")

    component.environment[sha1ofthetext] = {'marker':'verb',
                                    'sha1head':'verb',
                                    'component_raw':theverbatimtext,
                                    'component_separated':theverbatimtext
                                    }

    return "verb"+sha1ofthetext+"END"  # note: no extra space
       # We use "verb" so that it doesn't induce a paragraph break
    
############

def separatemacro(themacroname,numargs,text):
    """Extract \themacroname{...} as a component."""

    if "\\"+themacroname not in text:
        return text
    logging.debug("found a macro: %s", themacroname)

    thetext = text

    findmacro = "\\\\"+themacroname+"({.*)"
    logging.debug("finding macro %s in the text", findmacro)

    utilities.somethingchanged = 1

    while utilities.somethingchanged:
        utilities.somethingchanged = 0
        thetext = re.sub(findmacro,lambda match: separatemac(match,themacroname,numargs),thetext,1,re.DOTALL)
        logging.debug("maccount = %s", utilities.somethingchanged)

    return thetext

def separatemac(txt,macro,numargs):

    utilities.somethingchanged += 1

    therawtext = txt.group(1)

    sha1ofthetext = utilities.sha1hexdigest(therawtext+macro+str(numargs))

    logging.debug("macroarg: %s",therawtext[:30])

    try:
        markerX = component.math_macro_types[macro]['display']

    except KeyError:
        logging.warning("found an unknown macro: %s", macro)
        markerX = "ENV"

    theargs=""
    everythingelse = therawtext
    for _ in range(numargs):
        thearg, everythingelse = utilities.first_bracketed_string(everythingelse)
        theargs += thearg

    logging.debug("theargs: %s", theargs)

    sha1ofthetext = utilities.sha1hexdigest(macro+theargs)

        # we seem to lose the fact that this is a macro, not an environment?
    component.environment[sha1ofthetext] = {'marker':"mathmacro",   
                                    'macro': macro,
                                    'parent':component.parent,
                                    'sha1head':markerX,
                                    'star':"",
                                    'sqgroup':"",
                                    'component_raw':therawtext,
                                    'component_separated':theargs
                                    }

    return markerX+sha1ofthetext+"END " + everythingelse


############
def separateenvironment(theenvironment,thetext):
    r"""Find the \begin{theenvironment}...\end{theenvironment},
    where we only want the *innermost* environment in those cases where
    the environment is allowed to appear inside that same type of environment
    (such as lists).

    """

    # Regular expression to find the environment.
    findenvironment = r"\\begin\s*{("+theenvironment+")(\*?)}"
                           # start with \begin{env} or \begin{env*}
    findenvironment += "\s*"                     # possibly some white space
    findenvironment += "(((\[[^\[\]]*\])?)"     
                                     # possibly something in square brackets
    findenvironment += "\s*"                     # possibly some white space
    findenvironment += "(((?!\\\\begin\s*{"+theenvironment+"\*?}).)*?))"  
                              # Don't allow that environment to start again,
                              # because we  want to find the innermost one.
                              # Also do a minimal match. Is that redundant?
    findenvironment += "\s*"                  # maybe some more white space
    findenvironment += r"\\end\s*{"+theenvironment+"\*?}"

    thenewtext = re.sub(findenvironment,separateenv,thetext,0,re.DOTALL)

    return thenewtext


def separateenv(txt):

    utilities.something_changed += 1
    utilities.what_changed = txt

    therawtext = txt.group(0)
    marker = txt.group(1)
    starflag = txt.group(2)
    sqgroup = txt.group(4)  # Either group(4) is nonempty and equals group(5),
                      # or group(4) is the empty string and group(5) is None.
    thetext = txt.group(6)
    sha1ofthetext = utilities.sha1hexdigest(therawtext+marker)

    # perhaps we should make a separate way to handle figure environments?
    thecaption = ""
    image_ratio = 99
    startingimagefile = "starting_image_file"

    thetext = thetext.strip()  # probably redundant
    if (not sqgroup) and thetext.startswith("["):
        sqgroup, thetext = utilities.first_bracketed_string(thetext,0,"[","]") 
        logging.debug("with marker %s sqgroup %s", marker, sqgroup)

    # A "[" starting an equation is a bracket, not an optional argument
    if sqgroup and marker == "equation":
        logging.debug("found marker %s found sqgroup %s", marker, sqgroup)
        thetext = sqgroup + thetext
        sqgroup = ""

    sqgroup = utilities.strip_brackets(sqgroup,"[","]")
    sqgroup = sqgroup.strip()
    if sqgroup.startswith("{"):
        sqgroup = utilities.strip_brackets(sqgroup)
        sqgroup = sqgroup.strip()
        # Check that {\bf ...} has already been converted to \textbf{...}

    try:
        markerX = component.environment_types[marker]['display']

    except KeyError:
        logging.error("found an unknown marker %s", marker)
        markerX = "ENV"

    if marker == "split":  # is this a special case of a un-numberable math environment?
        starflag = "*"

    component.environment[sha1ofthetext] = {'marker':marker,
                                    'parent':component.parent,
                                    'sha1head':markerX,
                                    'star':starflag,
                                    'sqgroup':sqgroup,
                                    'component_raw':therawtext,
                                    'component_separated':thetext,
                                    'caption':thecaption,
                                    'image_file_tex':startingimagefile,
                                    'image_ratio':image_ratio
                                    }

    if marker in component.list_environments:
        return markerX+sha1ofthetext+"END "+"anY"+component.end_of_list_code+"END "
    else:
        return markerX+sha1ofthetext+"END "

###########

def separatecaption(sha1):

    theoldtext = component.environment[sha1]['component_separated']

    thenewtext = re.sub(r"\\caption *(\{.*)",
                        lambda match: separatecap(match,sha1),theoldtext,1,re.DOTALL)

    component.environment[sha1]['component_separated'] = thenewtext


def separatecap(txt, sha1key):

    text_after = txt.group(1)

    thecaption, text_after = utilities.first_bracketed_string(text_after,0,"{","}")
    thecaption = utilities.strip_brackets(thecaption,"{","}")

    this_marker = component.environment[sha1key]['marker']
    if component.environment_types[this_marker]['class'] == 'layout':
        try:
            parent_key = component.environment[sha1key]['parent']
        except KeyError:
            logging.error("OOOOOOOO bad parent from sha1key: %s", sha1key)
            logging.error(component.environment[sha1key])
            parent_key = "OOOOOOOO"
        try:
            parent_marker = component.environment[parent_key]['marker']
        except KeyError:
            logging.error("bad parent_marker from parent_key: %s", parent_key)
            parent_marker = "blob"  # don't actually know how or why we could reach this point
        if component.environment_types[parent_marker]['class'] == 'figure':
            the_key_to_label = parent_key
        else:
            the_key_to_label = sha1key
    else:
        the_key_to_label = sha1key

    component.environment[the_key_to_label]['caption'] = thecaption

    marker = "caption"
    markerX = "ENV"
    sha1ofthetext = utilities.sha1hexdigest(thecaption+marker)
    therawtext = thecaption
    thetext = thecaption

    component.environment[the_key_to_label]['caption_sha1'] = sha1ofthetext

    component.environment[sha1ofthetext] = {'marker':marker,
                                    'parent':sha1key,
                                    'sha1head':markerX,  # not used?
                                    'star':"",
                                    'sqgroup':"",
                                    'component_raw':therawtext,
                                    'component_separated':thetext
                                    }

    return text_after

################

def separatefootnote(thetext):

    theoldtext = thetext

    thenewtext = re.sub(r"\\footnote *(\{.*)",
                        separatefoot,theoldtext,1,re.DOTALL)

    return thenewtext


def separatefoot(txt):

    utilities.something_changed += 1
    utilities.what_changed = txt

    text_after = txt.group(1)

    thefootnote, text_after = utilities.first_bracketed_string(text_after,0,"{","}")
    thefootnote = utilities.strip_brackets(thefootnote,"{","}")

    therawtext = thefootnote
    thetext = thefootnote
    marker = "footnote"

    sha1ofthetext = utilities.sha1hexdigest(thefootnote + marker)

    try:
        markerX = component.environment_types[marker]['display']

    except KeyError:
        logging.debug("found an unknown marker %s", marker)
        markerX = "ENV"

    logging.debug("saving the footnote %s", thefootnote)
    logging.debug("text_after starts %s yyyyyyyy", text_after[:50])

    component.environment[sha1ofthetext] = {'marker':marker,
                                    'parent':component.parent,
                                    'id':sha1ofthetext,
                                    'sha1head':markerX,
                                    'star':"",
                                    'component_raw':therawtext,
                                    'component_separated':thetext,
                                    component.target:thetext
                                    }

    if component.environment[component.parent]["marker"] in component.math_environments:
        return text_after     # footnote knowls don't (currently) work in math mode, but see Tom Leathrum's code
    else:
        return markerX+sha1ofthetext+"END" + text_after

##############

def extract_includegraphics(text):

    thetext = text

    # delay until the end, so nothing is processed in the image source
#    if component.target == 'ptx' and component.writer == 'apex':
#        thetext = preprocess.apexincludegraphics(thetext)
#        return thetext

    if "epsfbox" in text:
        logging.debug("found epsfbox in: %s", text[:50])

    while r"\scalebox" in thetext:
        thetext = re.sub(r"\\scalebox *(.*)",
                         lambda match: extract_includegr(match,"scalebox"),
                         thetext,1,re.DOTALL)

    while r"\includegraphicsinternal" in thetext:
        thetext = re.sub(r"\\includegraphicsinternal\*? *(.*)",
                         lambda match: extract_includegr(match,"includegraphicsinternal"),
                         thetext,1,re.DOTALL)

    while r"\includegraphics" in thetext and r"\includegraphicsinternal" not in thetext:
        thetext = re.sub(r"\\includegraphics\*? *(.*)",
                         lambda match: extract_includegr(match,"includegraphics"),
                         thetext,1,re.DOTALL)

   # go back and do this better

    for includecommand in ["psfig", "epsfbox", "epsfig"]:
      #  logging.debug("looking for %s", includecommand)
        while "\\" + includecommand in thetext:
            thematch = "\\\\" + includecommand + r"\*? *(.*)"
            logging.debug("substituting with %s in %s", thematch, thetext[:50])
            thetext = re.sub(thematch,
                         lambda match: extract_includegr(match,includecommand),
                         thetext,1,re.DOTALL)

    return thetext

def extract_includegr(txt,marker="includegraphics"):

    text_after = txt.group(1).strip()

    logging.debug("marker: %s", marker)

    if marker == "scalebox":
        scale_x, text_after = utilities.first_bracketed_string(text_after,0,"{","}")
        if scale_x:
            scale_x = utilities.strip_brackets(scale_x,"{","}")
        else:
            logging.warning("missing scale_x in scalebox, assuming 0")
            scale_x = 0
        scale_y, text_after = utilities.first_bracketed_string(text_after,0,"[","]")
        if scale_y:
            scale_y = utilities.strip_brackets(scale_y,"[","]")
        else:
            logging.warning("missing scale_y in scalebox, assuming 0")
            scale_y = 0

        text_after = text_after.strip()
        the_image, text_after = utilities.first_bracketed_string(text_after,0,"{","}")
        the_image = utilities.strip_brackets(the_image,"{","}")
        the_image = the_image.strip()

        if (not the_image.startswith(r"\includegraphics") and
            not the_image.startswith(r"\epsfig")
           ):
            logging.error("Error: no \\includegraphics")
            logging.error("text starts with %s CCCCCC", the_image[:130])
            imagemarker = "MISSINGincludegraphics"
        else:
            the_image = re.sub(r"^\\(includegraphics|epsfile)\*? *","",the_image,1)
            text_after = the_image + text_after
            imagemarker = "includegraphics"

    else:
        imagemarker = marker
        scale_x = 0
        scale_y = 0

    #  We just extracted and saved the scalebox data, if it exists.
    #  Now in all cases text_after starts immediately after the
    #  (now missing) \includegraphcs.

    if text_after.startswith("["):
        size_directive, text_after = utilities.first_bracketed_string(text_after,0,"[","]")
        size_directive = utilities.strip_brackets(size_directive,"[","]")
    else:
        size_directive = ""

    try:
        src_file, text_after = utilities.first_bracketed_string(text_after,0,"{","}")
    except ValueError:
        logging.error("error locating src_file in %s", text_after[:100])
        src_file = ""
    src_file = utilities.strip_brackets(src_file,"{","}")
    if "=" in src_file:
        # typical use:  \epsfig{figure=filename, [other directives]}  file is a synonym for figure
        src_file_name = re.sub(r".*(figure|file)\s*=\s*([0-9a-zA-Za._-]+).*",r"\2",src_file)
        
        if src_file_name == src_file:   # i.e., the above re.sub failed to match
            src_file_name = re.sub(".*=","",src_file)
            src_file_name = src_file_name.strip()

    else:
        src_file_name = src_file

    if not src_file_name:
        logging.error("missing image file in %s", component.inputfilename)

    logging.debug("found an image: %s a %s b %s c %s d",
                   scale_x, scale_y, size_directive, src_file_name)

    sha1ofthetext = utilities.sha1hexdigest(src_file_name+"image")

    component.environment[sha1ofthetext] = {'marker':'image',
                                            'imagemarker':imagemarker,
                                            'component_separated':"",
                                            'sha1head':"image",
                                            'image_type':"file",
                                            'src_file':src_file_name,
                                            'scale_x':scale_x,
                                            'scale_y':scale_y,
                                            'size_directive':size_directive}

    return "image"+sha1ofthetext+"END "+text_after

##############

def extract_captionof(txt,sha1key):

    textafter = txt.group(1)
    countertype,textafter = utilities.first_bracketed_string(textafter)
    countertype = utilities.strip_brackets(countertype)
    captionof,textafter = utilities.first_bracketed_string(textafter)
    captionof = utilities.strip_brackets(captionof)

    if countertype == "table":
        countertype = "figure"

    component.environment[sha1key]['captionof'] = captionof
    component.environment[sha1key]['countertype'] = countertype

    return textafter

##############

def extract_isolated_images(text):
    """Find the images that ate not in a figure environment.

    This function needs a lot of work in order to handle multiple images
    in a figure, different aspect ratios, etc.

    """

    thetext = text

    findimage1a = r"(\\scalebox *{([0-9\.]*)} *\[([0-9\.]*)\])"
    findimage1b = r"{ *\\includegraphics\*?\s*{([^{}]+)}}"
    findimage1 = findimage1a + findimage1b

    findimage2 = r" *\\includegraphics\*? *\[(.*?)\]\s*{([^{}]+)}"

    if "scalebox" in thetext:
        findimage = findimage1
    else:
        findimage = findimage2

    logging.debug("using the pattern: %s", findimage)
    imagedata = re.search(findimage,thetext)
    logging.debug("imagedata: %s",imagedata)
    thetext = re.sub(findimage,"",thetext)

          # need to clean up this code.  What if there were a 3rd possibility?
    try:
        image_x = imagedata.group(1)
        image_y = imagedata.group(2)
        image_file_tex = imagedata.group(4)
        inputfile = component.inputfilename
        if "/" in inputfile:
            component.inputdirectory = re.sub(r"[^/]+$","",inputfile)
        else:
            component.inputdirectory = "./"

  # maybe call it imageinputdirectory?

        startingimagefile = component.inputdirectory + image_file_tex

        image_ratio = 1.0  # y/x as numbers

    except:   # IndexError:   #  (IndexError, AttributeError):
        try:
            image_ratio = imagedata.group(1)
            image_file_tex = imagedata.group(2)
            inputfile = component.inputfilename
            if "/" in inputfile:
                component.inputdirectory = re.sub(r"[^/]+$","",inputfile)
            else:
                component.inputdirectory = "./"

            startingimagefile = component.inputdirectory + image_file_tex

        except  AttributeError as IndexError:

            logging.warning("failed to find an image")
            startingimagefile = ""
            image_file_html = ""
            image_ratio = 1

    return (image_ratio, startingimagefile, thetext)

############

def extractlatexlabel(sha1key,text):
    """ Find the \label's in an environment and save in component.label
    and in component.environment[sha1key]['latex_label'].

    Note that some environments, like align, can have multiple labels.
    These must be separated before extracting labels.

    """

    thetext = text

    if "GS12" in thetext:
        logging.info(sha1key + " found GS12 " + thetext)
        component.environment[sha1key]

### Find and save the labels, and then delete the labels.
### why don't we do in in one big step instead of two smaller steps?

    findlabel = "\s*" + r"\\label\s*{([^{}]*)}" + "\s*"
    # the label can be empty, as in \label{}

    thelabels = re.findall(findlabel,thetext,re.DOTALL)
                # Use re.DOTALL because some people put \n in a label,
                # which seems crazy to me.
    if len(thelabels) > 1:
        logging.error("environment %s has %s labels, keeping the first one:",
                       sha1key, len(thelabels))
        logging.error(thetext)

    try:
        label = thelabels[0]   # just keep the first label
                           # (but there should only be one)
    except IndexError:
        logging.error("missing label")
        logging.debug(thetext[:100])
        label = "abcdefg"
    label = re.sub(r"\s*\n\s*"," ",label)   # remove \n from label

    this_marker = component.environment[sha1key]['marker']
        # If an image is in a "center" environment inside a "figure"
        # environment, then the label goes with "figure", not "center".
        # We handle that case below, but should re-write more generally.
    if component.environment_types[this_marker]['class'] == 'layout':
        logging.info("extracting the label %s", label)
        try:
            parent_key = component.environment[sha1key]['parent']
        except KeyError:
            logging.error("no parent of %s in %s", sha1key, thetext[:100])
            parent_key = ""
        if not parent_key:
            logging.error("missing parent key of %s", sha1key)
            the_key_to_label = sha1key
            logging.debug("%s", component.environment[sha1key]['component_separated'][:100])
        else:
            parent_marker = component.environment[parent_key]['marker']
            if (this_marker in {'blob', 'enumerate'} or   # can label an item, but not the whole list
                component.environment_types[parent_marker]['class'] in ['figure']):
                the_key_to_label = parent_key
            else:
                the_key_to_label = sha1key
    else:
        the_key_to_label = sha1key

    if label == "GS12":
        logging.info("found GS12 in"+ the_key_to_label+ "which is"+ str(component.environment[the_key_to_label]))

    label = utilities.safe_name(label, idname=True)

    if label:   # edge case of \label{}
        component.environment[the_key_to_label]['latex_label'] = label
        component.label[label] = {'sha1':the_key_to_label}
        
        logging.debug("found a label: %s", label)

    thetext = re.sub(findlabel," ",thetext,0,re.DOTALL)

    return(thetext)

############

def separateparagraphs0(parent_sha1,thetext):
    """Break thetext into implicit paragraphs.

    There are 4 cases, depending on whether a block of text has an equation
    or other component immediately before or after it.

    """

    text_remaining = thetext  # we will repeatedly pull words from the
                              # beginning of text_remaining, until it is empty

    parsed_text = ""          # the answer we will return
    current_paragraph = ""    # the current paragraph we are building
    current_word = ""         # the word we just removed from text_remaining

    parstart = ""             # is there an environemnt immediately before
    parend = ""               # or after the text?

    par_ending_strings = "(("+component.sha1heads_para+")"+"[0-9a-f]{40}END)"

    text_remaining = text_remaining.strip()

    text_remaining = re.sub(" *(\n|\r\n?) *",r"\1",text_remaining)
              # remove extraneous spaces that confuse \n\n at paragraph end

    while text_remaining:
        try:
            current_word, text_remaining = text_remaining.split(" ",1)
        except ValueError:    # presumably no spaces, so on the last word
            current_word = text_remaining
            text_remaining = ""

        current_word = current_word.lstrip(" ")

        if "\\" in current_word and len(current_word.strip()) == 1:
            current_word = " "      # saveparagraph will strip() what it is sent,
                                    # so there is no danger of " " being a paragraph

        if not current_word:  # presumably because the text_remaining
                              # started with a space
            continue

        try:
            current_word.startswith('\n')
        except TypeError:
            logging.error("Error 2: %s", current_word)

        if re.match(par_ending_strings, current_word):
                        # word starts with a paragraph ending string,
                        # so finish this paragraph
            first_part, second_part = current_word.split("END",1)
            first_part += "END" 

            if current_paragraph:
                current_paragraph = saveparagraph(parent_sha1, current_paragraph, parstart, parend="Y")
                            # current_paragraph is now a sha1hash
                parsed_text += current_paragraph + " "
                current_paragraph = ""

            parsed_text += first_part + " "
            parstart = "X"
            if second_part:
                text_remaining = second_part + " " + text_remaining

            continue    # because we just ended a paragraph, so now start a new one
            
        # Check if the current "word" contains the end of the paragraph
        # The end is either "\n\n" or a par_ending_string.
        parend_ret = False
        parend_env = False
        if re.search("(\n\n|\r\n?\r\n?)",current_word):
            first_part_ret = re.sub("^(.*?)(\n\n|\r\n?\r\n?).*",
                                    r"\1",current_word,1,re.DOTALL)
            parend_ret = True
        if re.search(par_ending_strings, current_word):
            first_part_env = re.sub("^(.*?)"+par_ending_strings+".*",
                                    r"\1",current_word,1,re.DOTALL)
            parend_env = True

        if parend_ret and parend_env:   # both endings are in current_word,
                                        # so which comes first?
            if len(first_part_ret) < len(first_part_env):   # \n\n comes first
                parend_env = False
            else:
                parend_ret = False

        if parend_env:    # word contains, but does not start with,
                          # a paragraph ending string

            current_paragraph += " " + first_part_env
            parend = "Y"
            current_paragraph = saveparagraph(parent_sha1, current_paragraph, parstart, parend)
                            # current_paragraph is now a sha1hash
            parsed_text += current_paragraph + " "   # why add a space?
            current_paragraph = ""
            parstart = "X"

            text_remaining = current_word[len(first_part_env):].lstrip() + " " + text_remaining

            continue   # paragraph ended, so start again

        if parend_ret:    # word contains, but does not start with,
                          # paragraph \n\n ending

            current_paragraph += " " + first_part_ret
            parend = ""
            current_paragraph = saveparagraph(parent_sha1, current_paragraph, parstart, parend)
                            # current_paragraph is now a sha1hash
            parsed_text += current_paragraph + " "   # why add a space?
            current_paragraph = ""
            parstart = ""

            text_remaining = current_word[len(first_part_ret):].lstrip() + " " + text_remaining

            continue   # paragraph ended, so start again

        else:
            current_word = current_word.strip()
            if current_paragraph:
                current_paragraph += " "+current_word
            elif current_word:
                current_paragraph = current_word

    if current_paragraph:    # we fell off the end of the text,
                             # so save the final paragraph
        current_paragraph = saveparagraph(parent_sha1, current_paragraph, parstart, parend)
        parsed_text += current_paragraph

    return parsed_text

#-------
def saveparagraph(parent_sha1, thetext, parstart="", parend=""):

    # we should be saving parstart and parend so that we can
    #     later have <p class="XparY">

    thenewtext = thetext.strip()

#    if not thenewtext or thenewtext == "\\":
    if not thenewtext or thenewtext in ["\\", "{", "}"]:
        return ""

    sha1ofthetext = utilities.sha1hexdigest(thenewtext+"text")

    component.environment[sha1ofthetext] = {'marker':'text',
                                    'sha1head':'text',
                                    'parent':parent_sha1,
                                    'component_raw':thenewtext,
                                    'component_separated':thenewtext
                                    }

    return "text"+sha1ofthetext+"END "

###########

def separatetikzpictures(themarker,thetext):
    r"""Find the \begin{tikzpicture}...\end{tikzpicture} and convert to PDF.
    Here "tikzpicture" is one of several possibilities for themarker.

    """

# Switched to just hiding tikz and then putting it back later.
# This avoids accidentally processing the tikz as text.

    findtikzpicture = r"\\begin{(" + themarker + ")(\*?)}"
    findtikzpicture += "\s*"                     # possibly some white space

    findtikzpicture += "(((?!\\\\begin{(" + themarker + ")\*?}).)*?)"
                              # Don't allow that environment to start again,
                              # because we  want to find the innermost one.
                              # Also do a minimal match. Is that redundant?
    findtikzpicture += "\s*"                  # maybe some more white space
    findtikzpicture += r"\\end{" + themarker + "\*?}"

    thenewtext = re.sub(findtikzpicture,separatetikz,thetext,0,re.DOTALL)

    return thenewtext

####

def separatetikz(txt):

    themarker = txt.group(1)
    thetikz = txt.group(3)

    thetikz = re.sub("("+component.sha1heads_all+")([0-9a-f]{40})END",
                                      makeoutput.expandseparated,thetikz)

    sha1ofthetikz = utilities.sha1hexdigest(thetikz)

    if component.target == 'ptx':
        component.environment[sha1ofthetikz] = {'marker':'tikz',
                                    'parent':component.parent,
                                    'id':sha1ofthetikz,
                                    'sha1head':'anY',
                                    'star':"",
                                    'component_raw':thetikz,
                                    'component_separated':thetikz
                                    }
        return "\n" + "anY"+sha1ofthetikz+"END" + "\n"

    tikzfilename_stub = component.imagesdirectory + "/" + sha1ofthetikz
    tikzfilename_tex = tikzfilename_stub + ".tex"
    tikzfile_tex = open(tikzfilename_tex,'w')

#    texheader = r"\documentclass{article}" + "\n"
#    texheader += r"\usepackage{amsopn}" + "\n"
#    texheader += r"\usepackage{pstricks,pst-text,pst-node}" + "\n"
#    texheader += r"\usepackage{tikz}" + "\n"
#    texheader += r"\usepackage{tkz-graph}" + "\n"
#    texheader += r"\usepackage{color}" + "\n"
#    texheader += r"\usepackage{pgfplots}" + "\n"
#    texheader += r"\usepackage{pinlabel}" + "\n"
#    texheader += r"\usetikzlibrary{patterns}" + "\n"
#    texheader += r"\usetikzlibrary{positioning}" + "\n"
#    texheader += r"\usetikzlibrary{matrix,arrows}" + "\n"
    texheader = ""
    for line in mapping.latexheader_top:
        texheader += line + "\n"
    for param in mapping.latexheader_param:
        texheader += mapping.latexheader_param[param] + "\n"
    for line in mapping.latexheader_other:
        texheader += line + "\n"
    for line in mapping.latexheader_tikz:
        texheader += line + "\n"


    texheader += makeoutput.mathjaxmacros(htmlwrap=False)

    texheader += "\n\n" + r"\begin{document}" + "\n\n"
    texheader += "\n" + r"\pagestyle{empty}" + "\n"

    texheader += r"\begin{" + themarker + "}" + "\n"

    texfooter =  "\n" + r"\end{" + themarker + "}" + "\n"
    texfooter += "\n" + r"\end{document}" + "\n"

    thecontents = makeoutput.expand_sha1_codes(thetikz)

    tikzfile_tex.write(texheader)
    tikzfile_tex.write(thecontents)
    tikzfile_tex.write(texfooter)
    tikzfile_tex.close()

    pdffilename = utilities.latex_to_pdf(tikzfilename_tex)
    new_imgfilename, imagefactor = utilities.imageconvert(pdffilename)

    return r"\includegraphicsinternal{" + new_imgfilename + "}\n"

#---------------

