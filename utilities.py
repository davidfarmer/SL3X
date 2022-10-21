# -*- coding: utf-8 -*-
import sys
import os
import re
import logging
import hashlib

import component
import processenvironments
import separatecomponents
import mapping
import makeoutput

one_level_of_brackets = r"[^{}]*({[^{}]*})*[^{}]*"

greek_letters = ["alpha","beta","gamma","delta","epsilon"
"zeta","eta","theta","mu","nu","tau","rho","sigma","xi","kappa",
"iota","lambda","upsilon","omicron","phi","chi","omega","psi","pi"]

something_changed = 0
what_changed = "nothing"
something_else_changed = 0
something_changed_file = 0

verbose = False

list_depth = 0

################

def sha1hexdigest(text):
    """Return the sha1 hash of text, in hexadecimal."""

    the_text = text
    sha1 = hashlib.sha1()
#    the_text = the_text.decode('utf-8',errors='replace')
#    sha1.update(the_text.encode('utf-8'))
    try:
        sha1.update(the_text.encode('utf-8', errors="ignore"))
    except UnicodeDecodeError:
        sha1.update(the_text)

    return(sha1.hexdigest())

###############

def text_up_to(text,target):
    """Find the initial segment of text that ends with target.

    """

    thetext = text
    if not thetext:
        return ""

    first_part = ""
    remaining_text = thetext
    while remaining_text and not first_part.endswith(target):
        currentchar = remaining_text[0]
        first_part += currentchar
        remaining_text = remaining_text[1:]

    return first_part, remaining_text

###############

def strip_brackets(text,lbrack="{",rbrack="}",depth=0):
    """Convert {{text}}} to text}.

    """

    thetext = text
    current_depth = 0

    if not thetext:
        return ""

    while thetext and thetext[0] == lbrack and thetext[-1] == rbrack:
        current_depth += 1
        firstpart,secondpart = first_bracketed_string(thetext,0,lbrack,rbrack)
        firstpart = firstpart[1:-1]
        if not firstpart:
            return secondpart
        elif depth and current_depth >= depth:
            return firstpart
        thetext = firstpart + secondpart

    return thetext

###############

def filestub(text):
    """Given a/b.c/d/e.f.g return e.f

    """

    thetext = text

    base_filename = re.sub(r"\.[^./]*$", "", thetext)   # delete the .pdf or .whatever
    the_stub = re.sub(r".*/", "", base_filename)   # greedily delete up to and including the first slash
    
    return the_stub

###############

def putback(txt):
    """ Expand the given sha1key into its components, incrementing
        appropriate counters and wrapping in a div.

        Only used to determine the numbering.
    """

    sha1key=txt.group(2)

    global something_changed
    something_changed += 1

    toplevel = component.toplevel

    comp = component.environment[sha1key]
    marker = comp['marker']

    try:
        this_star = comp['star']
    except KeyError:
        this_star = ""

    try:
        thiscounter = comp['countertype']
        # this happens when, for example, a captioned image appears in
        # a center environment.
    except KeyError:
        thiscounter = component.environment_types[marker]['counter']

    processenvironments.incrementcounter(thiscounter, this_star)
    thecodenumber = processenvironments.currentcounterastext(toplevel,thiscounter,this_star)
    component.environment[sha1key]['codenumber'] = thecodenumber
    if comp['marker'].endswith("section"):
        logging.debug("TTTTTT %s %s %s", comp['marker'], thecodenumber, this_star)

    return "<div><b>"+marker+thecodenumber+"</b>"+comp['component_separated']+"</div>"


###############

def extractcline(textrow):
    """extract cline information from a row in a LaTeX table.

    """

    thetext = textrow

    clist = ["" for _ in range(100)]

    if "cline" not in thetext:
        return clist, thetext

    clinematch = r"\s*\\cline\{\s*[^{}]*\s*\}\s*"

    cmatches = re.findall(clinematch,thetext)
    logging.debug("found cline: %s",cmatches)
    logging.debug("thetext was %s", thetext)
    thetext = re.sub(clinematch,"",thetext)
    logging.debug("thetext is now %s", thetext)

    for cl in cmatches:
        logging.debug("looking for the start in %s", cl)
        sys.stdout.flush()
        this_start = re.search(r"\\cline\{\s*([0-9]+)-",cl).group(1)
        this_end = re.search(r"-([0-9]+)\s*\}",cl).group(1)
        this_start = int(this_start)
        this_end = int(this_end)

        for j in range(this_start-1,this_end):
            clist[j] += " t2"

    return clist, thetext

###############

def imageconvert(sourcefile):
    """Convert an image to a 400dpi PNG, or SVG as appropriate."""

    imagefactor = 0   # not currently used

    startingimagefile = sourcefile
    logging.debug("imageconvert, startingimagefile: %s", startingimagefile)
    logging.debug("subdirectories to search are: %s",
                   component.extras["graphicspath"])
    if "\\" in startingimagefile:
        logging.warning("must expand a macro: %s", startingimagefile)
        startingimagefile = processenvironments.expand_author_macros(startingimagefile)
        logging.warning("and now it is: %s", startingimagefile)

    # \includegraphics doesn't have the file extension, so we look to see
    # which image file is actually available.

    # sourcefile might look like inputfiles/1308.0068/LoomisWhitney.jpg, so
    # directiries in the graphicspath must be inserted after the last / 

    imagefile = ""
    for dir in component.extras["graphicspath"]:
        file_to_test = re.sub(r"/([^/]+)$",r"/" + dir + "/" + r"\1", startingimagefile)
        logging.debug("looking for the file %s", file_to_test)
        if os.path.isfile(file_to_test):
            imagefile = file_to_test
            logging.debug("found the image file %s", imagefile)
        else: 
            for ext in component.imageformats:
               file_to_test = re.sub(r"/([^/]+)$",r"/" + dir + "/" + r"\1", startingimagefile)
               file_to_test = file_to_test + "." + ext
               logging.debug("looking for the file %s", file_to_test)
               if os.path.isfile(file_to_test):
                   imagefile = file_to_test
                   logging.debug("found the image file %s", imagefile)
                   break

    if not imagefile:
        logging.error("the image file %s does not exist, from file: %s",
                       startingimagefile, component.inputfilename)
        return "",imagefactor

    logging.debug("image file: %s", imagefile)

    base_filename = filestub(imagefile)
    logging.debug("base_filename %s", base_filename)

#    output_filename = base_filename + ".png"
    output_filename = base_filename + "." + component.imgtarget
    full_output_filename = component.imagesdirectory + "/" + output_filename

    if imagefile.lower().endswith("eps"):  # may need to crop white space
                                           # epscrop not available, so convert to pdf
        logging.debug("converting the eps file %s", imagefile)
        new_imagefile = component.imagesdirectory + "/" + base_filename + ".pdf"
        os.system("convert " + imagefile + " " + new_imagefile)
        logging.debug("converted the eps %s new imagefile is %s",
                       imagefile, new_imagefile)
        # also copy the original image file to the output directory (for use with ptx)
        os.system("cp " + imagefile + " " + component.imagesdirectory)
            # check if the converted file was created?
        if os.path.isfile(new_imagefile):
            logging.debug("using the new, converted to pdf file %s",new_imagefile)
            imagefile = new_imagefile
        else:
            logging.debug("failed to convert the eps file, so using the original version")


    if imagefile.lower().endswith("pdf"):   # may need to crop white space
        if component.imgtarget != 'svg':
            new_imagefile = component.imagesdirectory + "/" + base_filename + ".pdf"
            os.system("pdfcrop " + imagefile + " " + new_imagefile + " > /dev/null")
            logging.debug("cropped the pdf %s new imagefile is %s",
                           imagefile, new_imagefile)
                # for some reason, for example 1308.3926/NewD1.pdf, pdfcrop can fail.
                # So check if the cropped file was created
            if os.path.isfile(new_imagefile):
                logging.debug("using the new, cropped, pdf file")
                imagefile = new_imagefile
            else:
                logging.error("failed to crop the file, so using the original version")
        else:
            pass  # for now we just use the original image pdf when converting to svg

    if component.target == 'html':
        specialextensions = ["png","jpg","svg"]
    elif component.target == 'ptx':
        specialextensions = [component.imgtarget]

    if not imagefile.lower().endswith(tuple(specialextensions)):
        if component.target == 'html':    # not sure the parameters are correct or even meaningful
            if imagefile.lower().endswith('pdf'):
                output_filename = base_filename + "." + "svg"  #component.imgtarget
                full_output_filename = component.imagesdirectory + "/" + output_filename
                os.system("pdf2svg " + imagefile + " " + full_output_filename + " >/dev/null")
                rescalesvg(full_output_filename)
            else:
                os.system("convert -quiet -resize 35% -density 400 " + imagefile + " " + full_output_filename + " >/dev/null")
        elif component.target == 'ptx':
            pass
        #    if imagefile.lower().endswith('pdf'):
        #        os.system("pdf2svg " + imagefile + " " + full_output_filename + " >/dev/null")
        #    else:
        #        os.system("convert " + imagefile + " " + full_output_filename + " >/dev/null")
    else: # imagefile.lower().endswith(tuple(specialextensions)):
        os.system("cp " + imagefile + " " + full_output_filename)

    #hack to fix the multiple image problem in APEX calculus
    # need to determine the right way to do this
    # maybe it has to do with multi-page images?
    multiplefile = re.sub("\.png","-0.png",full_output_filename)
    if os.path.isfile(multiplefile):
        newtarget = "images/" + re.sub("\.png","-0.png",output_filename)
        logging.warning("changing image target to %s", newtarget)
        return newtarget,imagefactor

##### revisit the above, and determine why sometimes we need to use the -1 instead of the -0
##### and exactly why do the -0 and -1 files appear?

      # FIX: should use a previously set variable, not "images/" in the return.
    return "images/" + output_filename, imagefactor

##############

def rescalesvg(file, scale=1.4):

  try:
    with open(file) as f:
        this_svg = f.read()
        this_svg_height = re.search('height="(.*?)pt',this_svg).group(1)
        this_svg_width = re.search('width="(.*?)pt',this_svg).group(1)
        new_svg_height = str(scale*float(this_svg_height))
        new_svg_width = str(scale*float(this_svg_width))
        this_svg = re.sub('height="(.*?)pt','height="' + new_svg_height + 'pt',this_svg,1)
        this_svg = re.sub('width="(.*?)pt','width="' + new_svg_width + 'pt',this_svg,1)

    with open(file, "w") as f:
        f.write(this_svg)
  except:
    pass

##############

def latex_to_pdf(sourcefile, mode="latex"):
    """Convert latex file to pdf."""

    logging.debug("latex_to_pdf of %s", sourcefile)
    base_filename = sourcefile

    # is it always true that no extension means tex?

    base_filename = re.sub("\.tex\s*$","",base_filename)
    startingfile_stub = re.sub(".*/([^/]+)$", r"\1", base_filename)
    startingfile_tex = base_filename + ".tex"
    outputfile_dvi = base_filename + ".dvi"
    outputfile_ps = base_filename + ".ps"
    outputfile_pdf = base_filename + ".pdf"

    logging.debug("starting latex file: %s", startingfile_tex)

    logging.debug("file stub: %s", base_filename)
    if "/" in base_filename:
        base_directory = re.search(r"^(.*)/[^/]*$",base_filename).group(1)
    else:
        logging.error("no base_directory for %s", base_filename)
        base_directory = ""

    target_directory = base_directory

    logging.debug("output file %s", outputfile_pdf)

#    os.system("latex -interaction batchmode -output-directory="+base_directory+" "+ startingfile_tex + " > /dev/null; "
#              "dvips -q -Ppdf " + outputfile_dvi + " -o " + outputfile_ps + " > /dev/null" + "; "
#              "ps2pdf " + outputfile_ps + " " + outputfile_pdf + "; "
#              "pdfcrop " + outputfile_pdf + " " + outputfile_pdf + " > /dev/null")

    if mode == "latex":
        os.system("latex -interaction batchmode -output-directory="+base_directory+" "+ startingfile_tex + " > /dev/null; "
              "cd " + base_directory + "; " + "dvips -q -Ppdf " + startingfile_stub+".dvi" + " -o " + startingfile_stub+".ps" + " > /dev/null" + "; "
              "ps2pdf " + startingfile_stub+".ps" + " " + startingfile_stub+".pdf" + "; "
              "pdfcrop " + startingfile_stub+".pdf" + " " + startingfile_stub+".pdf" + " > /dev/null")
    else:
        os.system("cd " + base_directory + "; "
              "pdflatex -interaction batchmode " + startingfile_stub + ".tex > /dev/null;  "
              "pdfcrop " + startingfile_stub+".pdf" + " " + startingfile_stub+".pdf" + " > /dev/null")


    return outputfile_pdf


##############

def safe_name(text, idname=False, cwname=False):
    """Replace unsafe characters in a file name."""

    logging.debug("making a safe_name for %s", text)

    safe_text = text.strip()
    safe_text = re.sub("\s+"," ",safe_text)  # consecutive white space should be just one space

    if cwname:
        safe_text = to_ascii(safe_text)
        safe_text = re.sub(r"[^a-zA-Z ]","",safe_text)
        safe_text = re.sub(r" ","_",safe_text)
    else:
        safe_text = to_ascii(safe_text)
        # should this just use [^a-zA-Z0-9] ?
        safe_text = re.sub(r"[: ~!@#$%^&*|(){}<>,+=;/\\\`\'\".]","_",safe_text)

    if idname:
        # the CSS messes up the main theorem if it is given the label "main"
        safe_text = re.sub(r"\b(main)\b","mainmain",safe_text)
        # xml ids have to start with a letter
        safe_text = re.sub(r"^([^a-zA-Z])",r"x\1",safe_text)

    logging.debug("made the safe_name:%s", safe_text)

    return(safe_text)

##############

def first_bracketed_string(text, depth=0, lbrack="{", rbrack="}"):
    """If text is of the form {A}B, return {A},B.
    Initial white space is stripped.

    Otherwise, return "",text.

    """

    thetext = text.lstrip()

    if not thetext:
        logging.warning("empty string sent to first_bracketed_string()")
        return ""

    previouschar = ""
       # we need to keep track of the previous character becaause \{ does not
       # count as a bracket

    if depth == 0 and thetext[0] != lbrack:
        return "",thetext

    elif depth == 0:
        firstpart = lbrack
        depth = 1
        thetext = thetext[1:]
    else:
        firstpart = ""   # should be some number of brackets?

    while depth > 0 and thetext:
        currentchar = thetext[0]
        if currentchar == lbrack and previouschar != "\\":
            depth += 1
        elif currentchar == rbrack and previouschar != "\\":
            depth -= 1
        firstpart += currentchar
        if previouschar == "\\" and currentchar == "\\":
            previouschar = "\n"
        else:
            previouschar = currentchar
        
        thetext = thetext[1:]

    if depth == 0:
        return firstpart, thetext
    else:
        logging.error("no matching bracket %s in %s XX", lbrack, thetext)
        return "",firstpart[1:]   # firstpart should be everything
                                  # but take away the bracket that doesn't match

##############

def text_before(text, target):
    """If text is of the form *target*, return (*,target*).
    Otherwise, return ("",text)
    Note that target can be a tuple.
    """

    thetext = text
    thetarget = target

    if isinstance(thetarget, str):  # basestring uncludes str and unicode
        thetarget = [thetarget]
    thetarget = tuple(thetarget)

    firstpart = ""

    while thetext and not thetext.startswith(thetarget):
        firstpart += thetext[0]
        thetext = thetext[1:]

    if thetext:
        return (firstpart,thetext)
    else:
        return("",text)

##############

def text_exactly_contains(text, word):
    """ A silly function """

    the_word = re.sub(r"\\", r"\\\\", word)
    if re.search(the_word + r"\b", text):
        return True
    else:
        return False

##############

def replacemacro(text,macroname,numargs,replacementtext):
    """Expand a LaTeX macro in text.

    """

    if text == "":
        logging.debug("replacing macro %s in an empty string", macroname)
        return ""

    if "\\"+macroname not in text:
        return text

    # there is a tricky situation when a macro is being replaced by nothing.  if it is
    # alone on a line, then you just introduced a paragraph break.  it seems we must
    # treat that as a special case

    
    thetext = text
    global a_macro_changed
    
    a_macro_changed = 1

    while a_macro_changed:   # maybe change to:  while "\\"+macroname in text:

        # first, the special case described above, which we are not really handling right
        if not replacementtext:
            while a_macro_changed:
                logging.debug("replacing macro %s by nothing in: %s", macroname, re.sub("\s{2,}","\n",thetext.strip())[:30])
                a_macro_changed = 0
                thetext = re.sub(r"\n\\("+macroname+r")\s*({[^{}]*})\s",
                                 lambda match: replacemac(match,numargs,"\n"),thetext,1,re.DOTALL)
        a_macro_changed = 0

        thetext = re.sub(r"\\("+macroname+r")\**(([0-9]|\b)+.*)",lambda match: replacemac(match,numargs,replacementtext),thetext,1,re.DOTALL)

    return thetext

##############

def replacemac(txt,numargs,replacementtext):

    this_macro = txt.group(1)
    text_after = txt.group(2)

    if numargs:
        text_after = text_after.lstrip()

    if text_after.startswith("["):
        logging.debug("found square group")
        squaregroup, text_after = first_bracketed_string(text_after,0,"[","]")
        text_after = text_after.lstrip()
        # Currently we ignore the squaregroup.  What should we do with it?

     # first a hack to handle some oddly formed macro calls
    try:
        first_character = text_after[0]
    except IndexError:
        first_character = ""

    if numargs and first_character  not in ["{","\\"] and first_character not in r"0123456789":
        logging.debug("found %s but it has no argument %s", this_macro, text_after[:50])
        return text_after

    if first_character in "0123456789":   # wrap it in {} and proceed normally
        logging.debug("found that the argument is a number")
        text_after = re.sub("^([0-9])",r"{\1}",text_after,1)
        logging.debug("now the text after starts: %s", text_after[:20])
        
    if first_character == r"\\":   # wrap the argument in {} and proceed normally
        logging.debug("found that the argument is another macro")
        text_after = re.sub(r"^\\([a-zA-Z]+)",r"{\\\1}",text_after,1)

    global a_macro_changed
    a_macro_changed += 1

    arglis=[""]      # put a throw-away element 0 so that it is less confusing
                     # when we assign to the LaTeX "#N" argmuments

    for ar in range(numargs):
            try:
                theitem, text_after = first_bracketed_string(text_after)
            except ValueError:
                logging.error("no text_after in replacemac for argument %s of %s", ar, this_macro)
                logging.error("text_after begins %s", text_after[:40])
                if ar:
                    logging.error("arglis so far is %s", arglis)
                theitem = ""
                # below is to fail gracefully when there is an error.
                # need to come up with a better way
            if not theitem:  # probably missing close bracket
                logging.error("was scanning argument %s of %s before text_after %s", ar, this_macro, text_after[:20])
                logging.error("missing brace?  guess to stop at end of line")
                if "\n" in text_after:
                    theitem, text_after = text_after.split("\n",1)
                else:
                    theitem = ""
            theitem = strip_brackets(theitem)
            theitem = re.sub(r"\\",r"\\\\",theitem)  # This is tricky.  We are using the extracted LaTeX
                                                   # in a substitution, so we should think of it as code.
                                                   # Therefore we need to excape the backslashes.
            arglis.append(theitem)

# confused about which of the next two lines is correct
    macroexpanded = replacementtext
#    macroexpanded = re.sub(r"\\",r"\\\\",replacementtext)

    for arg in range(1,numargs+1):
        mysubstitution = "#"+str(arg)
        macroexpanded = re.sub(mysubstitution,arglis[arg],macroexpanded)
        
    return macroexpanded + text_after

#################

def author_name_for_link(author_dict):
# why don't we use safe_name here?

    try:
        thelink = author_dict['preferredfullname']
    except KeyError:
        thelink = ""

    if not thelink:
        firstname = author_dict['firstname']
        lastname = author_dict['lastname']
        thelink = firstname+" "+lastname

    thelink = to_ascii(thelink)
    thelink = re.sub(r" ","_",thelink)
    thelink = re.sub("\.","",thelink)
    thelink = re.sub("\,","",thelink)
    thelink = re.sub("'","_",thelink)

    return thelink

#################

def data_of_author(author_string, known_people):

    theauthor = to_ascii(author_string)
    print("theauthor", author_string, theauthor)
    if theauthor != author_string:
        logging.info("author name converted from %s to %s", author_string, theauthor)

    # J. Brian Conrey  vs  Gerard Ben Arous 
    start_of_name = theauthor[:3]
    logging.debug("start_of_name %s",start_of_name)
    if " " in start_of_name:
        logging.debug("looks like they have a first initial")
        auth_lastname = re.sub(".*\s+(\S+)\s*$",r"\1",theauthor)
    else:
        auth_lastname = re.sub("\S+\s+","",theauthor,1)

    # now handle David W. Farmer or Harry S Truman
    start_of_last_name = auth_lastname[:2]
    if "." in start_of_last_name or " " in start_of_last_name:
        auth_lastname = re.sub(r".\.\s*","",auth_lastname)
    # now handle Vaughan F. R. Jones
    start_of_last_name = auth_lastname[:2]
    if "." in start_of_last_name or " " in start_of_last_name:
        auth_lastname = re.sub(r".\.\s*","",auth_lastname)

    try:
        firstinitial = theauthor[0]
        auth_firstname = re.sub(r"^([^ .]+)(\.| ).*",r"\1",theauthor)
    except IndexError:
        logging.warning("missing first initial of %s", theauthor)
        firstinitial = ""

    possible_authors = []

    logging.debug("their last name is %s", auth_lastname)
    for person in known_people:
          # some times the middle name becomes part of the last name
        this_lastname = other_alphabets_to_latex(person['lastname'])
        this_firstname = other_alphabets_to_latex(person['firstname'])

        try:
            if ( (this_lastname.endswith(auth_lastname) or auth_lastname.endswith(this_lastname))
               and this_firstname.startswith(firstinitial)):
                  possible_authors.append(person)
        except UnicodeDecodeError:
            logging.critical("problem name %s", theauthor)


    if theauthor:
        logging.info("there are %s possible matches for this author: %s", len(possible_authors), theauthor)
        logging.info("who has firstname %s and lastname %s", auth_firstname, auth_lastname)

    revised_possible_authors = []
    if theauthor:
      for person in possible_authors:
        this_lastname = other_alphabets_to_latex(person['lastname'])
        this_firstname = other_alphabets_to_latex(person['firstname'])
        # if we have a first name and last name apparent match, then good.  otherwise, delete)
        if ( (this_firstname.startswith(auth_firstname) or auth_firstname.startswith(this_firstname))
         and
          (this_lastname.endswith(auth_lastname) or auth_lastname.endswith(this_lastname))):
            revised_possible_authors.append(person)
            

    if len(revised_possible_authors) == 1:
        logging.info("found one matching first name %s",revised_possible_authors[0])
        return revised_possible_authors[0]
    else:
        logging.info("name does not match")
        return ""

#################

def remove_silly_brackets(text):

    thetext = text

    thetext = re.sub(r"(^|\W){([A-Z])}",r'\1\2',thetext)   # {R}iemann --> Riemann
    thetext = re.sub(r'{\s+}',r"",thetext)  # in TikZ {} may have meaning
    thetext = re.sub(r'([^a-zA-Z]){([A-Za-z0-9])}',r"\1\2",thetext)  
            # is {.} around a single character after a space always silly?
    thetext = re.sub(r' {([A-Z]+)}',r" \1",thetext)
    thetext = re.sub(r'{([A-Z]+)} ',r"\1 ",thetext)
    thetext = re.sub(r'{(&[a-zA-Z]+;\s*)}',r"\1",thetext)
    thetext = re.sub(r'{(&#[0-9a-zA-Z]+;\s*)}',r"\1",thetext)
    thetext = re.sub(r"{'\s*}",r"'",thetext)
    thetext = re.sub("{(\$[^\$]+\$)}",r'\1',thetext)
    thetext = re.sub(r"{(\\['`\"^][a-zA-Z])}",r"\1",thetext)  
                    # as in Petter Br{\"a}nd{\'e}n
    return thetext

#################

def delete_one_environment(env, text):

    thetext = text

    logging.debug("deleting this env: %s", env)

    searchstring = r"\\begin{" + env + r"}(.*)"

    thetext = re.sub(searchstring,
                     lambda match: delete_one_env(env,match),
                     thetext,0,re.DOTALL)
    return thetext

############

def delete_one_env(theenv,txt):

    thetext = txt.group(1)


    endingstring = r"\end{" + theenv + r"}"
    logging.debug("endstring is %s", endingstring)
    if endingstring not in thetext:
        logging.error("failed to find endingstring %s", endingstring)
        return thetext

    starttext = ""
    remainingtext = thetext

    while not starttext.endswith(endingstring):
        starttext += remainingtext[0]
        remainingtext = remainingtext[1:]

    return remainingtext

##########

def delete_one_macro(mac, text):

    thetext = text

    searchstring = r"\\" + mac + r"\b"
    logging.debug("in delete_one_macro %s", searchstring)
    thetext = re.sub(searchstring,"",thetext)

    return thetext

#################

def delete_one_macro_arguments(mac, text, keeparg=False,numargs=1):

    thetext = text
    searchstring = r"\\" + mac + r"{(.*)"

    logging.debug("in delete_one_macro_arguments %s", searchstring)
    thetext = re.sub(searchstring,
                     lambda match: delete_one_macro_args(mac,match,keeparg,numargs),
                     thetext,0,re.DOTALL)
    return thetext

############

def delete_one_macro_args(mac, txt, keeparg, numargs):

    # this version only works if keeparg=1  (? when was that written?)

    thetext = txt.group(1)

    logging.debug("throwing away part of %s", thetext[:50])

    firstpart,secondpart = first_bracketed_string(thetext,1)
    firstpart = firstpart[:-1]   # delete the bracket at the end

    logging.debug("firstpart %s", firstpart)
    # throw away firstpart, which is the argument to the macro

    if keeparg:
        return firstpart + secondpart
    else:
        return secondpart

#################

def delete_formatting(text):
# remove LeTeX formatting commands

    newtext = text

    # some of these should be hidden in the html at the end,
    # not deleted at the beginnig.

    logging.debug("deleting some formatting")
    for cmd in mapping.throw_away_formatting0:
        thesub = r"\\" + cmd + r"\b"
        newtext = re.sub(thesub,r"",newtext)

    newtext = re.sub(r"\\setcounter{[^{}]*}{[^{}]*}",r"",newtext)
         # this is just a hack to fix a problem with extracting macros
         # probably delete_formatting() should come later in the process

#   omitting, because this can mess up macro definitions
#    newtext = re.sub(r"\\hbox\b",r"\\mbox",newtext)   # MathJax wants mbox, not hbox
        # later we will remove all the \mbox es in text

    newtext = re.sub(r"\\par\b\s*",r"\n\n",newtext)
    newtext = re.sub(r"\\parskip[^\n]*\n",r"",newtext)
    newtext = re.sub(r"\\baselineskip[^\n]*\n",r"",newtext)

    for env in mapping.throw_away_formatting_environments:
        thesub = r"\\(begin|end){" + env + r"}\s*"
        newtext = re.sub(thesub,r"",newtext)

#    protect_def = "#1"
#    newtext = replacemacro(newtext,"protect",1,protect_def)
        # \protect{...} is not actually formatting...

#  Check that these come after extracting author macros
    for macro in mapping.throw_away_macros:
        newtext = replacemacro(newtext,macro,1,"")
    for macro in mapping.throw_away_macros_and_argument:
        newtext = replacemacro(newtext,macro,1,"")
    for macro in mapping.throw_away_macros_keep_argument:
        newtext = replacemacro(newtext,macro,1,"#1")

    return(newtext)

#################

def latex_to_ascii(text):

    thetext = text

    # these convert like \alpha -> alpha
#    latex_to_ascii_greek = ["alpha","beta","gamma","delta","epsilon"
#"zeta","eta","theta","mu","nu","tau","rho","sigma","xi","kappa",
#"iota","lambda","upsilon","omicron","phi","chi","omega","psi","pi"]

#    for letter in latex_to_ascii_greek:
    for letter in greek_letters:
        the_sub =  "\\\\" + "(" + letter + ")" + r"\b"
        thetext = re.sub(the_sub,r"\1",thetext,re.I)  # case insensitive

    latex_to_ascii_symbol = [["ge",">="],["geq",">="],["le","<="],["leq","<="]]
    for pair in latex_to_ascii_symbol:
        the_sub =  "\\\\" + "(" + pair[0] + ")" + r"(\b|[0-9])"
        the_target = " " + pair[1] + " "
        thetext = re.sub(the_sub,the_target+r"\2",thetext,re.I)  # case insensitive

    thetext = re.sub(r"\s*\\times\s*"," x ",thetext)

    thetext = re.sub(r"\\tfrac",r"\\frac",thetext)
    thetext = re.sub(r"\\widehat",r"\\hat",thetext)
    thetext = re.sub(r"\\widetilde",r"\\tilde",thetext)
    thetext = re.sub(r"\\widecheck",r"\\check",thetext)
    thetext = re.sub(r"\\bar\b",r"\\overline",thetext)

    thetext = re.sub(r"\\[\^\'\`\"\~\-\=]\s*","",thetext)  # remove latex accents

    # in TeX, \\i is an i (without a dot), but usually \\. is a diacritical mark

    # shuld put these into a list in mapping.py
    thetext = re.sub(r"\\varphi","phi",thetext)
    thetext = re.sub(r"\\varrho","rho",thetext)
    thetext = re.sub(r"\\varnu","nu",thetext)
    thetext = re.sub(r"\\varepsilon","epsilon",thetext)
    thetext = re.sub(r"\\pm\b","+-",thetext)
    thetext = re.sub(r"\\ell(\b|\s+)","l",thetext)
    thetext = re.sub(r"{\\i}","i",thetext)
    thetext = re.sub(r"\\i ([A-Z])",r"i \1",thetext)
    thetext = re.sub(r"\\i\b","i",thetext)
    thetext = re.sub(r"{\\l}","l",thetext)
    thetext = re.sub(r"\\l ([A-Z])",r"l \1",thetext)
    thetext = re.sub(r"\\l ","l",thetext)
    thetext = re.sub(r"\\l\b","l",thetext)
    thetext = re.sub(r"\\L ","L",thetext)
    thetext = re.sub(r"{\\L}","L",thetext)
    thetext = re.sub(r"{\\o}","o",thetext)
    thetext = re.sub(r"\\o\b","o",thetext)
    thetext = re.sub(r"{\\oe}","oe",thetext)
    thetext = re.sub(r"{\\ss}","ss",thetext)
    thetext = re.sub(r"\\ss\b","ss",thetext)
    thetext = re.sub(r"\\H o","o",thetext)
    thetext = re.sub(r"\\H{o}","o",thetext)
    thetext = re.sub(r"\\\.([a-zA-Z])",r"\1",thetext)

    thetext = re.sub(r"\s*\\cprime\s*","'",thetext)
    thetext = re.sub(r"\s*\\vert\b\s*","|",thetext)

    thetext = re.sub(r"\s*\\left\b\s*","",thetext)
    thetext = re.sub(r"\s*\\right\b\s*","",thetext)

    latex_to_delete_from_ascii = ["rm","it","sl","bf","tt","em","emph",
                       "Bbb","mathbb","bold",
                       "scr",
                       "roman",
                       "Cal","cal","mathcal",
                       "mathrm","mathit","mathsl","mathbf","mathsf","mathtt",
                       "germ","frak", "mathfrak"]

    for macro in latex_to_delete_from_ascii:
        the_sub =  "\\\\" + macro + r"\b"
        thetext = re.sub(the_sub,"",thetext)  

    other_latex_markup = ["v","u","c"]     # as in Nata\v sa or Altu\u{g} or Ho{\c{s}}ten/

    for macro in other_latex_markup:
        the_sub =  "\\\\" + "(" + macro + ")" + r"\s*{([a-zA-Z])}"
        thetext = re.sub(the_sub,r"\2",thetext)  
        the_sub =  "\\\\" + "(" + macro + ")" + r"\b\s*"
        thetext = re.sub(the_sub,"",thetext)  

    thetext = re.sub(r"{([^}])}",r"\1",thetext)  #  {.} --> .
    thetext = re.sub(r"{([^}])}",r"\1",thetext)  #  {.} --> .  # Twice, because of {\v{S}}emrl

    thetext = re.sub(r"\s+"," ",thetext)

    return thetext

################

def other_alphabets_to_latex(text):  # including Word characters

    thetext = text

    # turn these into a list (in mapping.py) and loop through them
    # maybe use str.replace instead of a regular expression

    thetext = re.sub('−',r"-",thetext)
    thetext = re.sub('’',r"'",thetext)
    thetext = re.sub('“',r"``",thetext)
    thetext = re.sub('”',r"''",thetext)

    thetext = re.sub('\xc3\xb3',r"\\'o",thetext)
    thetext = re.sub('\xc3\xa1',r"\\'a",thetext)
    thetext = re.sub('\xc5\x9f',r"\\c{a}",thetext)
    thetext = re.sub('\xc3\xb1',r"\\~n",thetext)
    thetext = re.sub('\xc5\xa0',r"\\v{S}",thetext)

    thetext = re.sub('\xe2\x80\x22',r'-',thetext)   # not sure why that worked, but the clue was
                                                    # looking at the html file.  That character is
                                                    # the windows 0x2013 en dash
    
    thetext = re.sub('\x91',r"'",thetext)
    thetext = re.sub('\x92',r"'",thetext)
    thetext = re.sub('\x93',r'"',thetext)
    thetext = re.sub('\x94',r'"',thetext)
    thetext = re.sub('\x96',r'-',thetext)
    thetext = re.sub('\x97',r' - ',thetext)

    thetext = re.sub('\x85',r' - ',thetext)
    thetext = re.sub('\x8a',r'\\"a',thetext)
    thetext = re.sub('\x9a',r'\\"o',thetext)
    thetext = re.sub('\x96',r"-",thetext)
    thetext = re.sub('\x9f',r'\\"u',thetext)
    thetext = re.sub('\xa0'," ",thetext)
    thetext = re.sub('\xb1',r"\\pm",thetext)
    thetext = re.sub('\xb4',r"'",thetext)
    thetext = re.sub('\xc2'," ",thetext)
    thetext = re.sub('\xd5',r"'",thetext)
    thetext = re.sub('\xdf',r"{\\ss}",thetext)
    thetext = re.sub('ß',r"{\\ss}",thetext)
    thetext = re.sub('ł',r"{\\l}",thetext)
    thetext = re.sub('ồ',r"\\^o",thetext)   # note: not the correct translation
    thetext = re.sub('á',r"\\'a",thetext)
    thetext = re.sub('à',r"\\`a",thetext)
    thetext = re.sub('ä',r'\\"a',thetext)
    thetext = re.sub('ã',r'\\~a',thetext)
    thetext = re.sub('é',r"\\'e",thetext)
    thetext = re.sub('è',r"\\`e",thetext)
    thetext = re.sub('ë',r'\\"e',thetext)
    thetext = re.sub('É',r"\\'E",thetext)
    thetext = re.sub('a̧',r"\\c{a}",thetext)
    thetext = re.sub('ż',r"\\\.z",thetext)
    thetext = re.sub('\xe0',r"\\`a",thetext)
    thetext = re.sub('\xe1',r"\\'a",thetext)
    thetext = re.sub('\xe9',r"\\'e",thetext)
    thetext = re.sub('í',r"\\'{\\i}",thetext)
    thetext = re.sub('\xed',r"\\'{\\i}",thetext)
    thetext = re.sub('\xee',r"\\^{\\i}",thetext)
    thetext = re.sub('Á',r"\\'{A}",thetext)
    thetext = re.sub('Å',r"\\c{A}",thetext)
    thetext = re.sub('ń',r"\\'n",thetext)
    thetext = re.sub('ñ',r"\\~n",thetext)
    thetext = re.sub('ó',r"\\'o",thetext)
    thetext = re.sub('ø',r"{\\o}",thetext)
    thetext = re.sub('ú',r"\\'u",thetext)
    thetext = re.sub('ü',r'\\"u',thetext)
    thetext = re.sub('\xf1',r"\\~n",thetext)
    thetext = re.sub('\xf3',r"\\'o",thetext)
    thetext = re.sub('\xf6',r'\\"o',thetext)
    thetext = re.sub('ö',r'\\"o',thetext)
    thetext = re.sub('š',r'\\v{s}',thetext)
    thetext = re.sub('Š',r'\\v{S}',thetext)
    thetext = re.sub('ş',r'\\c{s}',thetext)
    thetext = re.sub('ç',r'\\c{c}',thetext)
    thetext = re.sub('č',r'\\v{c}',thetext)
    thetext = re.sub("ć",r"\\'c",thetext)
    thetext = re.sub('ř',r'\\v{r}',thetext)
    thetext = re.sub('\xfc',r'\\"u',thetext)
    thetext = re.sub('\xe8',r'\\`e',thetext)
    thetext = re.sub('Ã ',r'\\`a',thetext)
    thetext = re.sub('—',r'--',thetext)

    return thetext

################

def html_to_latex_alphabet(text):

    thetext = text

    for ht,la in mapping.html_to_latex_pairs:
        thetext = re.sub(ht,la,thetext)

    thetext = re.sub(r"&#34;",r'"',thetext)
    thetext = re.sub(r"&#39;",r"'",thetext)

    thetext = re.sub(r"&(.)uml;",r'\\"\1',thetext)
    thetext = re.sub(r"&iacute;",r"\\'{\\i}",thetext)
    thetext = re.sub(r"&(.)acute;",r"\\'\1",thetext)
    thetext = re.sub(r"&(.)grave;",r"\\`\1",thetext)
    thetext = re.sub(r"&(.)tilde;",r"\\~\1",thetext)
    thetext = re.sub(r"&(.)caron;",r"\\v{\1}",thetext)
    thetext = re.sub(r"&(.)cedil;",r"\\c{\1}",thetext)
    thetext = re.sub(r"&(o|O)slash;",r"{\\\1}",thetext)


    return thetext

#################

def tex_to_html_alphabets(text):

    # we need to develop these as a list of pairs, which then generate
    # substitutions that go either way.

    thetext = text

    # for people who write \'{e} instead of \'e
    thetext = re.sub(r"\\('|`|\^|~)\{([a-zA-Z])\}",r"\\\1\2",thetext)
    thetext = re.sub(r'\\"\{([a-zA-Z])\}',r'\\"\1',thetext)

    for tex, html in mapping.tex_to_html_characters:
#        print("mapping.tex_to_html_characters", tex, html)
        thetext = re.sub(tex, html, thetext)

    thetext = re.sub(r"\\S ",'&#xa7;',thetext)
    thetext = re.sub(r"\\S\b",'&#xa7;',thetext)
    thetext = re.sub(r"\\S([0-9])",r'&#xa7;\1',thetext)

    thetext = re.sub(r"([^-])---([^-])",r"\1&#8202;&#x2014;&#8202;\2",thetext)  #emdash
    thetext = re.sub(r"--",'&#x2013;',thetext)  #endash

    thetext = re.sub(r"(\W){([A-Z])}",r'\1\2',thetext)   # {R}iemann --> Riemann
    thetext = re.sub(r"(Mc|Mac){([A-Z])}",r'\1\2',thetext)   # Mc{K}ay --> McKay
    thetext = re.sub(r"{(&[a-z]+;)}",r'\1',thetext)   # fr{&eacute;}re --> fr&eacute;re
    thetext = re.sub(r"{(&#[0-9a-z]+;)}",r'\1',thetext)   # Ho{&#351;}ten --< Ho&#351;ten

    thetext = re.sub(r"\\LaTeX\b",'<span class="latex">L<sup>A</sup>T<sub>E</sub>X</span>',thetext)
    thetext = re.sub(r"\\MathML\b",'<span class="latex">MathML</span>',thetext)
    thetext = re.sub(r"\\,",' ',thetext)   # check that this is only applied in the correct places

    return thetext

def tex_to_ptx_alphabets(text):

    # we need to develop these as a list of pairs, which then generate
    # substitutions that go either way.

    thetext = text

    # for people who write \'{e} instead of \'e
    thetext = re.sub(r"\\('|`|\^|~)\{([a-zA-Z])\}",r"\\\1\2",thetext)
    thetext = re.sub(r'\\"\{([a-zA-Z])\}',r'\\"\1',thetext)

    for tex, html in mapping.tex_to_html_characters:
        thetext = re.sub(tex, html, thetext)

    thetext = re.sub(r"\\S ",'&#xa7;',thetext)
    thetext = re.sub(r"\\S\b",'&#xa7;',thetext)
    thetext = re.sub(r"\\S([0-9])",r'&#xa7;\1',thetext)

    thetext = re.sub(r"([^-])---([^-])",r"\1<mdash/>\2",thetext)  #emdash
    thetext = re.sub(r"--",'<ndash/>',thetext)  #endash

    thetext = re.sub(r"(\W){([A-Z])}",r'\1\2',thetext)   # {R}iemann --> Riemann
    thetext = re.sub(r"(Mc|Mac){([A-Z])}",r'\1\2',thetext)   # Mc{K}ay --> McKay
    thetext = re.sub(r"{(&[a-z]+;)}",r'\1',thetext)   # fr{&eacute;}re --> fr&eacute;re
    thetext = re.sub(r"{(&#[0-9a-z]+;)}",r'\1',thetext)   # Ho{&#351;}ten --< Ho&#351;ten

    thetext = re.sub(r"\\LaTeX\b",'<latex/>',thetext)
    thetext = re.sub(r"\\,",'<nbsp/>',thetext)   # wrong, because we should use a thin space

    return thetext

#################

def tex_to_html_fonts(text):

    thetext = text

    # First convert archaic TeX constructions
    # should this be somewhere else?  fixing the non-math-mode markup?

    # We call it font_styles, but it includes anythign where
    # \macro{...} in LaTeX corresponds to <tag>...</tag> in HTML

    for (macro, tag) in mapping.font_styles_html:
        thetext = replacemacro(thetext,macro,1,
                                         "<" + tag  + ">#1</" + tag + ">")
    thetext = re.sub("``",'"',thetext)
    thetext = re.sub("''",'"',thetext)

    thetext = re.sub(r"\\\%",r"%",thetext)
    thetext = re.sub(r"\\&",r"&amp;",thetext)
    thetext = re.sub(r"\\dots",r"&hellip;",thetext)
    thetext = re.sub(r"\\copyright",r"&copy;",thetext)
 #   thetext = re.sub(r"\\dollar",r"&#36;",thetext)   # fails, because mathjax interprets as $ (!)
    thetext = re.sub(r"\\dollar",r"\\$",thetext)
    thetext = re.sub(r"\\,",r" ",thetext)
    thetext = re.sub(r"\\;",r" ",thetext)
    thetext = re.sub(r"\\@",r" ",thetext)
    thetext = re.sub(r"\\!",r"",thetext)  # small negative space, but how in html?
    thetext = re.sub(r"(\s)\\(\s)",r"\1\2",thetext)  # a \ by itself
    thetext = re.sub(r"^\\(\s)",r"\1",thetext)  # a \ by itself
    thetext = re.sub(r"(\s)\\$",r"\1",thetext)  # a \ by itself
    thetext = re.sub(r"([^\\])\\$",r"\1",thetext)  # a \ by itself
    thetext = re.sub(r"\{\}",r"",thetext)

    # discretionary hyphen
    thetext = re.sub(r"([a-zA-Z0-9])\\-([a-zA-Z0-9])",r"\1\2",thetext)

    return thetext

#################

def tex_to_ptx_fonts(text):

    thetext = text

    # First convert archaic TeX constructions
    # should this be somewhere else?  fixing the non-math-mode markup?

    # We call it font_styles, but it includes anythign where
    # \macro{...} in LaTeX corresponds to <tag>...</tag> in HTML

    for (macro, tag) in mapping.font_styles_ptx:
        thetext = replacemacro(thetext,macro,1,
                                         "<" + tag  + ">#1</" + tag + ">")

    thetext = re.sub(r"\\dollar",r"<dollar/>",thetext)
    thetext = re.sub(r"\\&",r"<ampersand/>",thetext)
    thetext = re.sub(r"\\dots",r"<ellipsis/>",thetext)
    thetext = re.sub(r"\\copyright",r"&copy;",thetext)
    thetext = re.sub(r"\\\%",r"<percent/>",thetext)
    thetext = re.sub(r"\\#",r"<hash/>",thetext)

    thetext = re.sub(r"(\s)\\(\s)",r"\1\2",thetext)  # a \ by itself
    thetext = re.sub(r"^\\(\s)",r"\1",thetext)  # a \ by itself
    thetext = re.sub(r"(\s)\\$",r"\1",thetext)  # a \ by itself
    thetext = re.sub(r"([^\\])\\$",r"\1",thetext)  # a \ by itself

    if component.writer.lower() != "doob":
        thetext = re.sub("``([^\"]+?)''",r"<q>\1</q>",thetext)  # note: not re.DOTALL
        thetext = re.sub("(^|[^\\`])`([^\\'`]+?)'",r"\1<sq>\2</sq>",thetext)  # note: not re.DOTALL
    # thetext = re.sub("``",'"',thetext)
    # thetext = re.sub("''",'"',thetext)

 #   thetext = re.sub(r"\\dollar",r"&#36;",thetext)   # fails, because mathjax interprets as $ (!)
    thetext = re.sub(r"\\,",r" ",thetext)
    thetext = re.sub(r"\\;",r" ",thetext)
    thetext = re.sub(r"\\@",r" ",thetext)
    thetext = re.sub(r"\\!",r"",thetext)  # small negative space, but how in html?
    thetext = re.sub(r"\{\}",r"",thetext)

    # discretionary hyphen
    thetext = re.sub(r"([a-zA-Z0-9])\\-([a-zA-Z0-9])",r"\1\2",thetext)
    thetext = re.sub(r"([a-zA-Z0-9])\\-([a-zA-Z0-9])",r"\1\2",thetext)

    return thetext

#################

def tex_to_html_spacing(text):

    thetext = text

    
    if component.target == 'html':
        thetext = re.sub(r"(^|[^\\])~~",r"\1&nbsp;&nbsp;&nbsp;&nbsp;",thetext)  
        # because ~~ probably means someone wants to make a wide space
        thetext = re.sub(r"(^|[^\\])~",r"\1&nbsp;",thetext)  # because a~b is a tie, and \~b is a b-tilde
        thetext = re.sub(r"(^|[^\\])~",r"\1&nbsp;",thetext)  # twice because of tag abuse like ~~~~~~~

        thetext = re.sub(r"([^\\])\\ ",r"\1&nbsp;",thetext)   # forced\ space
        thetext = re.sub(r"([^\\])\\ ",r"\1&nbsp;",thetext)   # do it twice to handle \ \ \ \ \ 

        thetext = re.sub(r"\\quad\b","&nbsp;&nbsp;",thetext)
    elif component.target == 'ptx':
        thetext = re.sub(r"(^|[^\\])~~",r"\1<nbsp/><nbsp/><nbsp/><nbsp/>",thetext)
        # because ~~ probably means someone wants to make a wide space
        thetext = re.sub(r"(^|[^\\])~",r"\1<nbsp/>",thetext)  # because a~b is a tie, and \~b is a b-tilde
        thetext = re.sub(r"(^|[^\\])~",r"\1<nbsp/>",thetext)  # twice because of tag abuse like ~~~~~~~

        thetext = re.sub(r"([^\\])\\ ",r"\1<nbsp/>",thetext)   # forced\ space
        thetext = re.sub(r"([^\\])\\ ",r"\1<nbsp/>",thetext)   # do it twice to handle \ \ \ \ \ 

        thetext = re.sub(r"\\quad\b","<nbsp/><nbsp/>",thetext)


    thetext = re.sub(r"^\s*(\\\\)+","",thetext)   # Starting with a line break makes no sense
    thetext = re.sub(r"\\linebreak\b","<br/>",thetext)   # don't do that in a table or math mode
    thetext = re.sub(r"\\\\(\[[^\[\]]*\])?","<br/>",thetext)   # don't do that in a table or math mode

    return thetext

#################

def tex_to_html_other(text):

    # These should be "safe" to convert, because they can't appear in math mode.
    # Need to check that more carefully, and maybe only apply these to components
    # that are only text

    thetext = text

    if not thetext:
        logging.warning("converting tex_to_html_other on an empty string")
        return ""

    # hack for math mode.  rethink
    thetext = replacemacro(thetext,"knownterminology",1,r'#1')

    if component.target == 'html':
        thetext = re.sub(r"\\url\{([^{}]+)\}",r'<a href="\1">\1</a>',thetext)
        thetext = replacemacro(thetext,"href",2,'<a href="#1">#2</a>')

    elif component.target == 'ptx':
        pass   # see issue #43


#    thetext = re.sub(r"\\parbox *(\[[.]*\])?{([^{}]*)}{([^{}]*)}",r"\\text{\3}",thetext)
    thetext = re.sub(r"\\parbox *(\[[.]*\])?{([^{}]*)}{([^{}]*)}",r"\3",thetext)
    thetext = replacemacro(thetext,"parbox\\\\[t\\\\]",2,'#2')
    thetext = replacemacro(thetext,"parbox",2,'#2')
       # redo without a regular expression, and check if \text is good in all case
       # example where \text{} was used:  http://sl2x.aimath.org/development/collectedworks/htmlpaper/1407.7186/section1.html
       # update: no it is not.  this is minipage-like, and so cannot be handled properly in all cases.

    # thetext = re.sub(r"\\qed\b",'<div align="right">&nbsp;&#9646;&nbsp;</div>',thetext)
                        # The end-of-proof sign is automatic at the end of a proof.
                        # So maybe we should just delete \qed?
                        # Yes: we now do that
    thetext = re.sub(r"\\qed\b",'',thetext)

    # delete things like \Large
    for cmd in mapping.throw_away_formatting1:
        thesub = r"\\" + cmd + r"\b"
        thetext = re.sub(thesub,r"",thetext)

    thetext = replacemacro(thetext,"setlength",2,'')

   # should put the following in a list
    thetext = re.sub(r"\\addcontentsline\b.*",'',thetext)   # put in arguments instead of .*
    thetext = re.sub(r"\\markboth\b.*",'',thetext)   # put in arguments instead of .*
    thetext = re.sub(r"\\pagestyle\b.*",'',thetext)   # put in arguments instead of .*
    thetext = re.sub(r"\\thispagestyle\b.*",'',thetext)   # put in arguments instead of .*

    return thetext

#################

def tex_to_html_text_only(text):

    thetext = text

    if component.target == 'html':
        thetext = replacemacro(thetext,"knownterminology",1,r'<em class="terminology">#1</em>')
        thetext = replacemacro(thetext,"knownindex",1,"")
    elif component.target == 'ptx':
        thetext = replacemacro(thetext,"knownterminology",1,r'<term>#1</term>')
        thetext = replacemacro(thetext,"knownindex",1,"<idx>#1</idx>")

    for macro in mapping.throw_away_macros_keep_argument_in_text_only:
        thetext = replacemacro(thetext,macro,1," #1 ")

    for (macro, replacement) in mapping.replace_macros_in_text_only:
        thetext = replacemacro(thetext,macro,0,replacement)

    for macro in mapping.throw_away_commands_in_text_only:
        thetext = replacemacro(thetext,macro,0,"")

    thetext = re.sub(r"\\_","_",thetext)

    return thetext

#################

def fix_bad_font_directives(text):

    newtext = text

    logging.debug("in fix_bad_font_directives")

    # We handle the plain-TeX directives \bf, \tt, etc, in two ways.
    # in places like \title{\bf ...} or \begin{proof}[\sc ...]  we throw it away.

    for font in mapping.tex_latex_font_switch + ["em"]:
        this_font_as_re = r"\\" + font + r"\s"
        newtext = re.sub(r"([a-z]{3}\*?){\s*" + this_font_as_re,r"\1{",newtext)
        newtext = re.sub(r"\[\s*" + this_font_as_re,r"[",newtext)
   
    newtext = re.sub(r"\{\s*\\em\b\s*",r"\\emph{",newtext)

    # and things like {\bf ...  get converted to \textbf{...
    for font in mapping.tex_latex_font_switch:
        thesub = r"\{\s*\\" + font + r"\s"
        theans = r"\\text" + font + r"{"
        newtext = re.sub(thesub, theans, newtext)

        # and then delete every other instance of \rm, \it, \bf
        newtext = re.sub(r"\\" + font + r"\b","",newtext)

    # rm is not in mapping.tex_latex_font_switch
    newtext = re.sub(r"\\rm\b","",newtext)

    return newtext

#################

def tex_to_html(text):
    """Convert various LaTeX markup to HTML."""

    thetext = text

    if not thetext:
        return ""

    thetext = tex_to_html_alphabets(thetext)
    thetext = tex_to_html_fonts(thetext)
    thetext = tex_to_html_spacing(thetext)

    thetext = tex_to_html_other(thetext)

    thetext = tex_to_html_text_only(thetext)   # need to reorganize where we put such things

    # The following maybe should be in a separate function.
    # The point is that this function transforms simple markup,
    # so anything environment-like should already be gone, and if
    # it isn't, remove it now.

    thetext = replacemacro(thetext,"footnote",1,"")

    # should expand_text_macros_core be here?

    return(thetext)

#################

def tex_to_ptx(text):
    """Convert various LaTeX markup to PTX."""

    thetext = text

    if not thetext:
        return ""

    thetext = tex_to_ptx_alphabets(thetext)
    thetext = tex_to_ptx_fonts(thetext)
    thetext = tex_to_html_spacing(thetext)

    thetext = tex_to_html_other(thetext)

    thetext = tex_to_html_text_only(thetext)   # need to reorganize where we put such things

    # The following maybe should be in a separate function.
    # The point is that this function transforms simple markup,
    # so anything environment-like should already be gone, and if
    # it isn't, remove it now.

    # probably irrelevant because footnote is an environemnt
    thetext = replacemacro(thetext,"footnote",1,"<footnote>#1</footnote>")

    # should expand_text_macros_core be here?

    return(thetext)

#################

def latex_array_to_html(text):
    "rename, because it does both html and ptx"

    thetext = text

    logging.debug("processing the table: %s", thetext[:50])

    if component.target == 'html':
        rowmarker = "tr"
        cellmarker = "td"
    elif component.target == "ptx":
        rowmarker = "row"
        cellmarker = "cell"

    thetext = re.sub(r"^\s*\{\s*\\[^{}]*\}\s*","",thetext)

    thetext = re.sub(r"\s*\{\s*\\extracolsep{[^{}]*\}\s*}\s*","",thetext)

    logging.debug("now the table is: %s", thetext[:50])

    # the simplest layouts look like  {lrcc|c|rr|c}
    findlayout = r"^ *{("+one_level_of_brackets+r")}"
    # but they can also include entries like p{1.5in},
    # so for now we hide those

    thetext = re.sub(r"p{[0-9.]+(cm|in)}","l",thetext)
    thetext = re.sub(r"\\tabularnewline",r"\\\\",thetext)

    try:
        thelayout = re.match(findlayout,thetext).group(1)
    except AttributeError:
        thelayout =""
        logging.error("no layout in: %s from %s", thetext[:50], component.inputfilename)
        return thetext

    thetext = re.sub(findlayout,"",thetext)
    if "extwidth" in thelayout:
        try:
            thelayout = re.match(r"^ *{([^{}]*)}",thetext).group(1)
        except AttributeError:
            thelayout =""
            logging.error("no layout in: %s from %s", thetext[:50], component.inputfilename)
            return thetext
        thetext = re.sub(r"^ *{([^{}]*)}","",thetext)

    thelayout = re.sub(" ","",thelayout)   # do spaces in the layout mean anything?

    if thelayout[0] == "*":
        try:
            logging.debug("thelayout: %s", thelayout)
            thelay = re.match(r"\*\{([0-9]+)\}\{([a-z])\}",thelayout)
            thenumber = int(thelay.group(1))
            theclr = thelay.group(2)
            thelayout = theclr * thenumber   # string with a repeating character
            logging.debug("thelayout: %s", thelayout)

        except IndexError:
            logging.error("IndexError: thelayout: %s", thelayout)
            logging.error("thetext: %s", thetext)
            return thetext

        except AttributeError:
            logging.error("AttributeError: thelayout: %s", thelayout)
            logging.error("thetext: %s", thetext)
            return thetext

    layout_list_raw = list(thelayout)
    layout_list=[]
    logging.debug("at first, layout_list_raw is %s", layout_list_raw)
    if layout_list_raw[0] not in mapping.table_layout_options:
        left_marker = "v"
        layout_list = ["v"]   # had a problem http://sl2x.aimath.org/development/collectedworks/htmlpaper/1202.6657/section5.html table 5.1.1
        layout_list_raw.pop(0)
    else:
        left_marker = ""
        layout_list = [""]
    logging.debug("now layout_list_raw is %s", layout_list_raw)
    for j in range(len(layout_list_raw)):   # do this more elegantly
        curr_elem = layout_list_raw[j]
        if j == 0:
            layout_list[0] += curr_elem
        elif curr_elem not in mapping.table_layout_options:
            layout_list[-1] = layout_list[-1] + "v"     #   v means |
        else:
            layout_list.append(curr_elem)

    logging.debug("the layout_list %s", layout_list)

    therows = re.split("\\\\\\\\|\\\\cr\b",thetext)
    thelastrow = therows[-1].split("&")

    thehtmltable = ""

    for row in therows:
        logging.debug("row was: %s", row)
        cline_layout, thisrow = extractcline(row)
        logging.debug("thisrow is now: %s", thisrow)
        logging.debug("cline_layout starts: %s", cline_layout[0:10])
        thisrow = thisrow.split("&")
        logging.debug("after splitting: %s",thisrow)
     #   thehtmltable += "<tr>"
        thehtmltable += "<" + rowmarker + ">"
        rowcounter = 0
        for entry in thisrow:
            this_entry = entry
        # this program design may end up causing problems.  At this point the
        # rows of the table should be plain text and sha1 environments.  So we
        # now do some conversions.  But we should seriously consider a more
        # sophisticated approach.
            this_entry = tex_to_html_spacing(this_entry)
            try:
            #    thehtmltable += "<td class='" + layout_list[rowcounter] + cline_layout[rowcounter] + "'>" + this_entry + "</td>"
                thehtmltable += '<' + cellmarker
                if component.target == 'html':
                    thehtmltable += ' class="' + layout_list[rowcounter] + cline_layout[rowcounter] + '"'
                thehtmltable += '>' + this_entry + '</' + cellmarker + '>'
            except IndexError:
             #   thehtmltable += "<td class='" + "unknown" + "'>" + this_entry + "</td>"
                thehtmltable += '<' + cellmarker + ' class="' + 'unknown' + '">' + this_entry + '</' + cellmarker + '>'
                logging.error("error: table width")
            rowcounter += 1
        thehtmltable += "</" + rowmarker + ">" + "\n"

    # convert more transparently to html
    htmlhline = "<tr><td class='hline' colspan='" + str(len(layout_list)) + "'><hr/></td></tr>\n"
    htmlhlinethick = "<tr><td class='hlinethick' colspan='" + str(len(layout_list)) + "'><hr/></td></tr>\n"
    if component.target == "ptx":
        htmlhline = '<' + rowmarker + ' bottom="minor">'
        htmlhlinethick = '<' + rowmarker + ' bottom="medium">'
        empty_row_list = ('<' + cellmarker + '></' + cellmarker + '>' for _ in layout_list)
        empty_row = "".join(empty_row_list)
        htmlhline += empty_row +  '</' + rowmarker + '>' + "\n"
        htmlhlinethick += empty_row +  '</' + rowmarker + '>' + "\n"

    # special case for \hline at the bottom of a table
    thehtmltable = re.sub('(<' + rowmarker + '><' + cellmarker + r'[^>]*>)\s*\\hline\s*</' + cellmarker + '></' + rowmarker + '>',htmlhline,thehtmltable)

    # the other \hlines
    thehtmltable = re.sub('(<' + rowmarker + '><' + cellmarker + r'([^>]*)>)\s*\\hline\s*\\hline',htmlhlinethick + '\n<' + rowmarker + '><' + cellmarker + r' \2 >',thehtmltable)
    thehtmltable = re.sub('(<' + rowmarker + '><' + cellmarker + r'[^>]*>)\s*\\hline',htmlhline + r'\1',thehtmltable)
    return thehtmltable

#################

def to_ascii(text):

    thetext = text

    thetext = html_to_latex_alphabet(thetext)
    thetext = other_alphabets_to_latex(thetext)
    thetext = latex_to_ascii(thetext)

    return thetext

##############

def rearrange_subscripts(text):
    """ change x^2_1 into x_1^2.

    """

    thetext = text

    a_subscript = r"_(\{[^{}]+\}|[a-zA-Z0-9]|\\[a-zA-Z]+)"
    a_superscript = r"\^(\{[^{}]+\}|[a-zA-Z0-9]|\\[a-zA-Z]+)"

    thetext = re.sub(a_superscript+a_subscript,r"_\2^\1",thetext)

    return thetext
    
##############

def text_ascii_reduce(text):
    """ Make a "reduced" form of the text.
        Used to check if titles are equal.
    """

    thetext = text

    thetext = html_to_latex_alphabet(thetext)
    thetext = re.sub(r"\\sb\b","_",thetext)   # recheck.  See The+distribution+of+values+of+$L(1,\chi\sb+d)
    thetext = rearrange_subscripts(thetext)
    thetext = latex_to_ascii(thetext)
    thetext = thetext.lower()

    thetext = re.sub(r"--","-",thetext)
    thetext = re.sub(r"on-","on",thetext)   # as in (N|n)on-
    thetext = re.sub(r"-"," ",thetext)

    # remove plural 's' from long words
    # but first remove possesives
    thetext = re.sub(r"'s\b","",thetext)
    # first: classes -> class, foxes -> fox
    thetext = re.sub(r"([a-z]{3}(x|ch|sh|ss))es\b",r"\1",thetext)
    # properties -> property
    thetext = re.sub(r"([a-z]{4})ies\b",r"\1y",thetext)
    # actually, the 's' from the end of any long word, but not if it ends in 'ss'
    thetext = re.sub(r"([a-z]{3}[a-rt-z])s\b",r"\1",thetext)

    # let's try to be less agressive
    # thetext = re.sub(r"[^a-zA-Z0-9 ]","",thetext)

    thetext = re.sub(r"\\frac","",thetext)
    thetext = re.sub(r"\\backslash","",thetext)
    thetext = re.sub(r"\\\S\s","",thetext)    # such as?
    thetext = re.sub(r"[\^\'\`\"\~\-\_]","",thetext)
    thetext = re.sub(r"[\{\}]","",thetext)
    thetext = re.sub(r"\\","",thetext)
    thetext = re.sub(r"\$","",thetext)
    thetext = re.sub(r"[;:,.]","",thetext)

    letter_word_to_symbol = [
        ["one","1"],
        ["two","2"],
        ["three","3"],
        ["four","4"],
        ["five","5"],
        ["six","6"],
        ["seven","7"],
        ["eight","8"],
        ["nine","9"],
        ["ten","10"]
        ]

    for words, number in letter_word_to_symbol:
        thesub = r"\b" + words + r"\b"
        thetext = re.sub(thesub,number,thetext)

    roman_to_number = [
        ["I","1"],
        ["II","2"],
        ["III","3"],
        ["IV","4"],
        ["IIII","4"],
        ["V","5"],
        ["VI","6"],
        ["VII","7"],
        ["VIII","8"],
        ["IX","9"],
        ["X","10"],
        ["XI","11"],
        ["XII","12"]
        ]

    for numeral, number in roman_to_number:
        thesub = r"part\s" + r"\b" + numeral + r"\b"
        thetext = re.sub(thesub,"part " + number,thetext)

    thetext = re.sub(r"^a note on","",thetext)
    thetext = re.sub(r"^notes on","",thetext)
    thetext = re.sub(r"^remark on","",thetext)
    thetext = re.sub(r"^on the","",thetext)
    thetext = re.sub(r"^on ","",thetext)
    thetext = re.sub(r"^(the|an|a) +","",thetext)

    # above we delete some simple words at the beginning of the title.
    # now we delete some of those everywhere.

    # we delete the words "a", "an", and "the".  is that reasonable?
    thetext = re.sub(r"\b(a|an|the)\b","",thetext)

    # delete some 2-letter prepositions.  is that reasonable?
    thetext = re.sub(r"\b(on|in|of|at|for)\b","",thetext)

    # need \"* and *e to be recognized as the same
    thetext = re.sub(r"mueller","muller",thetext)
    thetext = re.sub(r"goedel","godel",thetext)
    thetext = re.sub(r"moebius","mobius",thetext)
    thetext = re.sub(r"schroed","schrod",thetext)
    thetext = re.sub(r"hoelder","holder",thetext)
    thetext = re.sub(r"kaehler","kahler",thetext)

    # british -> american
    thetext = re.sub(r"alogue","alog",thetext)  # analog, catalog
    thetext = re.sub(r"colour","color",thetext)
    thetext = re.sub(r"flavour","flavor",thetext)
    thetext = re.sub(r"tumour","tumor",thetext)
    thetext = re.sub(r"rigour","rigor",thetext)
    thetext = re.sub(r"mould","mold",thetext)

    thetext = re.sub(r"modell","model",thetext)
    thetext = re.sub(r"travell","travel",thetext)
    thetext = re.sub(r"cancell","cancel",thetext)
    thetext = re.sub(r"annell","annel",thetext)
    thetext = re.sub(r"avell","avel",thetext)
    thetext = re.sub(r"biass","bias",thetext)
    thetext = re.sub(r"disc","disk",thetext)
    thetext = re.sub(r"cheque","check",thetext)
    thetext = re.sub(r"centre","center",thetext)
    thetext = re.sub(r"fibre","fiber",thetext)

    thetext = re.sub(r"alis(e|i)",r"aliz\1",thetext)  # generaliz(es|ed|ing)
    thetext = re.sub(r"oris(a|e|i)",r"oriz\1",thetext)  # factorization
    thetext = re.sub(r"eris(a|e|i)",r"eriz\1",thetext)  # factorization
    thetext = re.sub(r"randomis","randomiz",thetext)
    thetext = re.sub(r"itemis","itemiz",thetext)

    thetext = re.sub(r"cypher","cipher",thetext)
    thetext = re.sub(r"grey","gray",thetext)
    thetext = re.sub(r"gramme","gram",thetext)
    thetext = re.sub(r"neurone","neuron",thetext)
    thetext = re.sub(r"sceptic","skeptic",thetext)

    # remove parentheses
    thetext = re.sub(r"[()]","",thetext)

    # finally, remove spaces.  This is key to handling dashes and hyphenation
    thetext = re.sub(r"\s","",thetext)

    #finally finally, remove everything that is not a letter or a number
    thetext = re.sub(r"[^a-zA-Z0-9]","",thetext)

    return thetext

#################
def arxiv_author_match(firstname, lastname, paper,strict=False):
    """Did firstname lastname write a particular paper in the arxiv?
       "strict=True" means that we don't match the name if there are
       4 or more authors and the arXiv author only uses first initial.

    """

    logging.debug("Did %s %s write %s", firstname, lastname, paper)

    the_metadata = re.findall("(<meta\s+name.*)",paper)

    all_lastnames = ""

    for meta in the_metadata:
        if "citation_author" not in meta:
            continue
        that_author = re.sub(r'.*content="(.*)" />',r"\1",meta)
        that_author = html_to_latex_alphabet(that_author)
        that_author = other_alphabets_to_latex(that_author)
        that_author = latex_to_ascii(that_author)
        that_author = re.sub("'","",that_author)   # Gel'fand --> Gelfand
        logging.debug("that_author is: %s", that_author)
        try:
            that_author_ln, that_author_fn  = that_author.split(',')
        except ValueError:                        # i.e., no comma in that_author
            that_author_ln = that_author.strip()
            that_author_fn = ""
        that_author_ln = re.sub(r"(Jr|Sr|III|IV)","",that_author_ln)
        that_author_ln = that_author_ln.strip()
        that_author_ln = re.sub("\.","",that_author_ln)  # remove periods.  can that happen?
        that_author_fn = that_author_fn.strip()
        that_author_fn = re.sub("\..*","",that_author_fn)   # for example, Farmer, D.  --> first name is "D" 

        all_lastnames += "XX" + that_author_ln + "YY"

        if (that_author_ln.endswith(lastname) or lastname.endswith(that_author_ln)) and  (
               that_author_fn.startswith(firstname) or firstname.startswith(that_author_fn)):

               # the above "either starts with the other" construction is meant to catch first initials
               # and multi-word last names

            if not strict and paper.count("citation_author") > 12 and len(that_author_fn) == 1:
                logging.debug("not matching because of very many authors and only first initial")
                return False
            elif strict and paper.count("citation_author") > 5 and len(that_author_fn) == 1:
                logging.debug("not matching because of many authors and only first initial")
                return False
            else:
                logging.debug("True %s %s", paper.count("citation_author"), len(that_author_fn))
                return True

    print("lastname:", lastname, "all_lastnames:", all_lastnames)

    return False

#################

def fix_definition(the_def):
    """Rewrite some definitions so that they work with MathJax.  Mostly
       these are hacks for particular authors.

    """

    thedefinition = the_def

    if "ensuremath" in thedefinition:
        thedefinition = delete_one_macro_arguments("ensuremath",thedefinition,keeparg=True)
        thedefinition = delete_one_macro("ensuremath",thedefinition)

    if "ifmmode" in thedefinition:   # just keep the math mode part
        logging.debug("has ifmmode, was %s", thedefinition)
        thedefinition = replacemacro(thedefinition,"ifmmode",1,"#1")
        thedefinition = replacemacro(thedefinition,"else",1,"")
        thedefinition = replacemacro(thedefinition,"fi",0,"")
        logging.debug("now is %s", thedefinition)

    if "setbox0" in thedefinition and "overline" in thedefinition:
        thedefinition = r"\overline{#1}"

    return thedefinition

##################

def environment_shortcuts(text):

    newtext = text

    for env in mapping.environment_abbrev:

       # first convert to lower case
   #    thesub1 = r"(?i)\\" + "(begin|end)\s*{" + env + r"s?" + r"}"  # s? to un-pluralize
       thesub1 = r"(?i)\\" + "(begin|end)\s*{" + env + r"}"  # un-pluralizing broke some sources
       theans = r"\\\1{" + env + r"}"
       newtext = re.sub(thesub1, theans,newtext)

       # then convert the abbreviations
       for abbrev in mapping.environment_abbrev[env]:
           thesub2 = r"(?i)\\" + "(begin|end)\s*{" + abbrev + r"}"
           newtext = re.sub(thesub2, theans,newtext)

    newtext = re.sub(r"\\begin{enumerate[^{}]+}",r"\\begin{enumerate}",newtext)
    newtext = re.sub(r"\\end{enumerate[^{}]+}",r"\\end{enumerate}",newtext)

    newtext = re.sub(r"\\term\b",r"\\terminology",newtext)

    return newtext

##################

def modify_displaymath(text):
    """Replace \( and \) by \left( and \right) .

    Some people use \( for \left( and \) for \right).  It is legal in
    LaTeX to make those macros, but it seems to be quite tricky to have
    MathJax understand them.  We can't globally replace \( by \left(,
    because in some cases \( is the inline math delimiter.  But in
    display math we should be safe to assume \( means \left.

    Also see ??? where we delete the \( macro.

    """

    thetext = text

    for _ in range(2):
        # hack to handle \)\)  
        thetext = re.sub(r"(^|[^\\])"+r"\\"+"\(",r"\1\\left(",thetext)
        thetext = re.sub(r"(^|[^\\])"+r"\\"+"\)",r"\1\\right)",thetext)

    # why is this here?  it is not specific to displaymath
    thetext = re.sub(r"\\(hskip|hfuzz|vskip)\s*-?([0-9]|\.|,)+\s*(in|pt|cm|mm|px|em|en)","",thetext)

# consider putting this back after we properly separate the math-mode-only substitutions.
#    thetext = re.sub(r"\\emph",r"\\mathrm",thetext)
        # emph in math is a poor way to make non-italics in an equation

    return thetext

#####################

def convert_some_math_to_html_img(text,hasequationnumber=False):

    thetext = text

    # the next group will be obsolete after we extract xy as a basic environment
    thetext = re.sub(r"\\begin{minipage}","",thetext)
    thetext = re.sub(r"\\end{minipage}","",thetext)
    if r"\begin{xy}" in thetext:
        logging.debug("xyprocessing of %s", thetext[:30])
        thetext = re.sub(r".*\\begin{xy}",r"\\begin{xy}",thetext,0,re.DOTALL)

    sha1ofthetext = sha1hexdigest(thetext)
    if "picture" in thetext:
        logging.debug("converting picture %s", sha1ofthetext)

    if r"\includegraphics" in thetext:
        try:
            included_image_base = re.search(r"\\includegraphics\s*{\s*([^}]+)}", thetext).group(1)
        except AttributeError:
            included_image_base = re.search(r"\\includegraphics\[[^\[\]]*\]\s*{\s*([^}]+)}", thetext).group(1)
        included_old_imagefile = component.inputdirectory + "/" + included_image_base
        included_new_imagefile = component.imagesdirectory + "/" + included_image_base
        srcs=["", ".eps", ".pdf", ".svg"]
        for ext in srcs:
            os.system("cp " + included_old_imagefile + ext + " " + included_new_imagefile + ext)

    textfilename_stub = component.imagesdirectory + "/" + sha1ofthetext

    textfilename_tex = textfilename_stub + ".tex"
    textfile_tex = open(textfilename_tex,'w')

    texheader = ""
#    for line in mapping.latexheader:
#        texheader += line + "\n"
    for line in mapping.latexheader_top:
        texheader += line + "\n"
    for param in mapping.latexheader_param:
        texheader += mapping.latexheader_param[param] + "\n"
    for line in mapping.latexheader_other:
        texheader += line + "\n"
    for line in mapping.latexheader_tikz:
        texheader += line + "\n"

    the_author_macros = makeoutput.mathjaxmacros(processby="latex",htmlwrap=False)

# temporary hack for young diagrams in Anne Schilling's book
    if "\\young{" in text or "\\tableau" in text:
        texheader += "\\newdimen\\squaresize \\squaresize=9pt" + "\n"
        texheader += "\\newdimen\\thickness \\thickness=0.4pt" + "\n"

# note that these both define \tableau, but they are not compatible
##        os.system("cp " + "/home/sl2x/www/sl2x.aimath.org/htdocs/development/latexpackages/tableau.sty" + " " + component.imagesdirectory)
        os.system("cp " + "/home/sl2x/www/sl2x.aimath.org/htdocs/development/latexpackages/tabmac.sty" + " " + component.imagesdirectory)

        the_author_macros = re.sub(r"\\newcommand", r"\\declarecommand", the_author_macros)
##        the_author_macros = r"\usepackage{tableau}" + "\n\n" + the_author_macros
        the_author_macros = r"\usepackage{tabmac}" + "\n\n" + the_author_macros
        the_author_macros = r"\definecolor{Gray}{rgb}{0.9,0.9,0.9}" + "\n" + the_author_macros
        the_author_macros = r"\newcommand{\declarecommand}[1]{\providecommand{#1}{}\renewcommand{#1}}" + "\n" + the_author_macros

    texheader += the_author_macros

    texheader += "\n\n" + r"\begin{document}" + "\n\n"
    texheader += "\n" + r"\pagestyle{empty}" + "\n"

#    texheader = r"\documentclass{article}" + "\n"
#    texheader += r"\usepackage{amsmath}" + "\n"
#    texheader += r"\usepackage{amssymb}" + "\n"
#    texheader += r"\usepackage{amscd}" + "\n"
#    texheader += r"\usepackage{xypic}" + "\n"
#    texheader += r"\usepackage{epic}" + "\n"
#    texheader += r"\usepackage{eepic}" + "\n"
#    texheader += r"\usepackage{color}" + "\n"
#    texheader += r"\usepackage{multirow, booktabs, makecell}" + "\n"
#    texheader += r"\usepackage[all]{xy}" + "\n"
#    texheader += makeoutput.mathjaxmacros(processby="latex",htmlwrap=False)
#    texheader += "\n\n" + r"\begin{document}" + "\n\n"
#    texheader += "\n" + r"\pagestyle{empty}" + "\n"

    if "unitlength" not in thetext:
        if len(component.extras["unitlength"])>1:
            this_length = component.extras["unitlength"][1]     # need to change this to a counter
        else:
            this_length = "6mm"

        if not this_length:
            this_length = "6mm"

        texheader += "\n" + r"\setlength{\unitlength}{" + this_length + "}" + "\n"

    texfooter = "\n\n" + r"\end{document}" + "\n\n"

    textfile_tex.write(texheader)
    textfile_tex.write(thetext)
    textfile_tex.write(texfooter)
    textfile_tex.close()

    pdffilename = latex_to_pdf(textfilename_tex)
    new_imgfilename, imagefactor = imageconvert(pdffilename)
    # imagefactor not used, but in future may use it to determine size

    if component.target == 'html':
        if new_imgfilename.endswith("svg"):
            return r'<img class="cs svg" src="' + new_imgfilename + '"/>\n'
        else:
            return r'<img class="cs" src="' + new_imgfilename + '"/>\n'
    elif component.target == 'ptx':
        return r'<image source="' + new_imgfilename + '"/>\n'

###############
def re_convert_image(text, srcs=["", ".eps", ".pdf", ".svg"]):

    thetext = text

    thetext = makeoutput.expand_sha1_codes(thetext)

    thetext_expanded = thetext

    mode = ""
    input_base = ""

    if r"\figureinput" in thetext:
        logging.warning("Found a figureinput")
        input_base = re.search(r"\\figureinput\s*{\s*([^}]+)}", thetext).group(1)

        # We need to leave the \input in the file because it may contain \makeatletter .
        # (which can appear in an input file but not in the body of a LaTeX file)
        # But that file may contain \includegraphics, so we need to know what files to copy.
        thetext_expanded = re.sub(r"\\(figureinput)\*?\s*{([^}]+)}",
              lambda match: separatecomponents.input_and_preprocess_a_file(match, preprocess=False),
              thetext)
        # the input file could have lines like
        # %% To include the image in your LaTeX document, write
        # %%   \input{<filename>.pdf_tex}
        # %%  instead of
        # %%   \includegraphics{<filename>.pdf}
        thetext_expanded = re.sub(r"[%].+", "", thetext_expanded)
        thetext_expanded = re.sub("\n+", "\n", thetext_expanded)

    thetext = re.sub(r"\\figureinput", r"\\input", thetext)
    thetext = re.sub(r"\\figuredef", r"\\def", thetext)
    thetext = re.sub(r"\\figurenewcommand", r"\\newcommand", thetext)
    thetext = re.sub(r"\\figurerenewcommand", r"\\renewcommand", thetext)

    image_base_list = []
    if r"\includegraphics" in thetext_expanded:
            image_base_list = re.findall(r"\\includegraphics\s*{\s*([^}]+)}", thetext_expanded)
            if not image_base_list:
                image_base_list = re.findall(r"\\includegraphics\[[^\[\]]*\]\s*{\s*([^}]+)}", thetext_expanded)
            logging.info("starting image_base_list %s", image_base_list)
    elif "overpic" in thetext_expanded:
            image_base_list = re.findall(r"\\begin{overpic}[^{}]{,50}\s*\{([^{}]+)\}", thetext_expanded)
            if not image_base_list:
                logging.error("cannot find filename in %s", thetext_expanded)
                return thetext
    elif "begin{picture}" in thetext_expanded:  # need a more robust way to generate a name
        name_tmp = sha1hexdigest(thetext_expanded + "picture")[:10]
        image_base_list = ["picture" + name_tmp]
        logging.info("made-up image_base: %s", image_base_list[0])
    else:   # need to raise an error
        logging.error("image type not recognized %s wwwwwwwwww", thetext)
        return "image type not recognized"

    if not image_base_list:
        logging.warning("no image_base_list in %s", thetext_expanded)

    for image_base in image_base_list:
        image_base_stub = re.sub(r"\.[^\.]*$", "", image_base)

        old_imagefile = component.inputdirectory + "/" + image_base
        old_imagefile_stub = component.inputdirectory + "/" + image_base_stub
        new_imagefile = component.imagesdirectory + "/" + image_base
        new_imagefile_stub = component.imagesdirectory + "/" + image_base_stub

        for ext in srcs:   # The source may or may not include the extension,
                       # and the extension may or may not be one of the usual suspects.
  # Change this so that it checks for the existence of the file before trying to copy
            if os.path.isfile(old_imagefile + ext):
                os.system("cp " + old_imagefile + ext + " " + new_imagefile + ext)
            if os.path.isfile(old_imagefile_stub + ext):
                os.system("cp " + old_imagefile_stub + ext + " " + new_imagefile_stub + ext)

    if input_base:
        mode = "pdflatex"
        old_input = component.inputdirectory + "/" + input_base
        new_input = component.imagesdirectory + "/" + input_base
        for ext in ["", ".tex"]:
            if os.path.isfile(old_input + ext):
                os.system("cp " + old_input + ext + " " + new_input + ext)

    texheader = ""
    for line in mapping.latexheader_top:
        texheader += line + "\n"
    for param in mapping.latexheader_param:
        texheader += mapping.latexheader_param[param] + "\n"
    for line in mapping.latexheader_other:
        texheader += line + "\n"
    for line in mapping.latexheader_tikz:
        texheader += line + "\n"

    texheader += makeoutput.mathjaxmacros(processby="latex",htmlwrap=False)
    texheader += "\n\n" + r"\begin{document}" + "\n\n"
    texheader += "\n" + r"\pagestyle{empty}" + "\n"

    thetext = makeoutput.expand_sha1_codes(thetext)

    texfooter = "\n\n" + r"\end{document}" + "\n\n"

    new_image_filename_stub = image_base_stub + "_rev"
    textfilename_stub = component.imagesdirectory + "/" + new_image_filename_stub
    textfilename_tex = textfilename_stub + ".tex"
     # change to "with"
    textfile_tex = open(textfilename_tex,'w')

    textfile_tex.write(texheader)
    textfile_tex.write(thetext)
    textfile_tex.write(texfooter)
    textfile_tex.close()

    if mode:
        pdffilename = latex_to_pdf(textfilename_tex, mode)
    else:
        pdffilename = latex_to_pdf(textfilename_tex)
    new_imgfilename, imagefactor = imageconvert(pdffilename)
    # imagefactor not used, but in future may use it to determine size

    if component.target == 'html':
        return r"\includegraphicsinternal{" + new_imgfilename + "}" + "\n"
    elif component.target == 'ptx':
        return r'<image source="' + new_imgfilename + '"/>\n'

###############

def processsubfigures_to_html(text):

    newtext = text

    newtext = re.sub(r"\\hspace\s*\{[^{}]*}\s*","",newtext)
    newtext = re.sub(r"\\vspace\s*\{[^{}]*}\s*","",newtext)

    find_subfigure = r"\\subfigure\b(.*)"

    while r"\subfigure" in newtext:
        logging.debug('processing subfigure in %s', text[:30])
        newtext = re.sub(find_subfigure,processsubfigs_to_html,newtext)

    return newtext

def processsubfigs_to_html(txt):

    text_after = txt.group(1).strip()

    if text_after.startswith("["):

        squaregroup, text_after = first_bracketed_string(text_after,0,"[","]")
        squaregroup = strip_brackets(squaregroup,"[","]")
        squaregroup = squaregroup.strip()
        text_after = text_after.strip()

    else:
        squaregroup = ""

    thefigure, text_after = first_bracketed_string(text_after,0,"{","}")
    thefigure = strip_brackets(thefigure,"{","}")
    thefigure = thefigure.strip()

    if squaregroup:
        return thefigure + '<div class="subcaption">' + squaregroup + '</div>' + text_after
    else:
        return thefigure +  text_after


#############

def to_integer_percent(val, scal=1.0):
    """ convert val/scal to an integer percent
    """

    this_value = float(val)
    this_scale = float(scal)
    this_percent = 100.0 * this_value/this_scale

    return int(this_percent)

#############

def replacein(txt, word_was, word_is, the_first="", the_last="", at_start="", at_end=""):
    """ Replace word_was by word_is in txt.group(0),
        except possibly the fist and last instances.

        User must supply correct number of backslashes.
    """

    text = txt.group(1)
    try:
        start_tag = txt.group(2)
        end_tag = txt.group(3)
    except IndexError:
        start_tag = ""
        end_tag = ""

    # need this so the usual use case is idempotent.
    # but what if we want to only use the at_start and at_end?
    if re.sub(r"\\\\",r"\\",word_was) not in text:
        return text

#    oldword = re.sub(r"\\",r"\\\\",word_was) 
#    newword = re.sub(r"\\",r"\\\\",word_is) 
#    new_first_word = re.sub(r"\\",r"\\\\",the_first) 
#    new_last_word = re.sub(r"\\",r"\\\\",the_last) 
    the_start_tag = re.sub(r"\\",r"\\\\",start_tag) 
    the_end_tag = re.sub(r"\\",r"\\\\",end_tag) 
    oldword = word_was
    newword = word_is
    new_first_word = the_first
    new_last_word = the_last

    if at_start and start_tag:
        text = re.sub(the_start_tag, the_start_tag + at_start, text, 1)
    if at_end and end_tag:
        text = re.sub(the_end_tag, at_end + the_end_tag, text, 1)
    if new_first_word:
        text = re.sub(r"^(.*?)" + oldword, r"\1" + new_first_word, text, 1, re.DOTALL)
    if new_last_word:
        text = re.sub(oldword + r"(.*?)$", new_last_word + r"\1", text, 1, re.DOTALL)
    text = re.sub(oldword, newword, text)

    return text

#############

def balanced_brackets(text, lbrack="{", rbrack="}"):
    """ Check if text contains equal numbers of lbrack and rbrack.
        Later make this function actually check if they are balanced.

    """

    return text.count(lbrack) == text.count(rbrack)

#################

def argument_of_macro(text,mac,argnum=1):
    """Return the argument (without brackets) of the argnum
       argument of the first appearance of the macro \mac
       in text.

    """

    searchstring = r".*?" + r"\\" + mac + r"\b" + r"(.*)"
    # the ? means non-greedy, so it matches the first appearance of \\mac\b

    try:
        text_after = re.match(searchstring,text,re.DOTALL).group(1)
    except AttributeError:
        logging.warning("macro %s not in text", mac)
        return ""

    for _ in range(argnum):
        the_argument, text_after = first_bracketed_string(text_after)

    the_argument = strip_brackets(the_argument)

    return the_argument

#################

def makesagecell(text, mode):
    """Interpret text as a sage cell input and output, and then convert it
       to the correct markup for the given mode in ['html', 'ptx']

    """
    
    original_source = text
    # the following is needed because we change lstlisting to sageexample
    if not "sage:" in original_source:
        if mode.lower() in ['ptx', 'mbx']:
            original_source = re.sub("<", "<lt/>", original_source)
        return "<pre>" + original_source + "</pre>"

    if mode.lower() == 'html':
        original_source_lines = original_source.split("\n")
   #     print "sageexample component_separated", original_source
        processed_source = ""
        this_portion = ""
        sageinputmode = True
        for line in original_source_lines:
            #stripped_line = line.strip()
            line = re.sub("\s*(sage|\.\.\.\.)", r"\1", line)  # some people indent every sage: line
            if line.startswith("sage:") or line.startswith("....:") or (sageinputmode and this_portion.endswith("\\\n")):  # get rid of the 'sage: '
                if line.startswith("sage:") or line.startswith("....:"):
                    line = line[6:]
                if not sageinputmode:
                    this_portion = re.sub("<", "&lt;", this_portion)
                    processed_source += "\n" + '<div class="sageanswer">' + '<span class="key">Output:</span>'
                    processed_source += '<span class="output">' + this_portion + '</span>' + '</div>' + "\n"
                    sageinputmode = True
                    this_portion = line + "\n"
                else:
                    this_portion += line + "\n"
            else:
                if sageinputmode:
                    processed_source += "\n" + component.sagecellstart + this_portion + component.sagecellend + "\n"
                    sageinputmode = False
                    this_portion = line + "\n"
                else:
                    this_portion += line + "\n"
        if sageinputmode:
            processed_source += "\n" + component.sagecellstart + this_portion + component.sagecellend + "\n"
        else:
            this_portion = re.sub("<", "&lt;", this_portion)
            processed_source += "\n" + '<div class="sageanswer">' + '<span class="key">Output:</span>'
            processed_source += '<span class="output">' + this_portion + '</span>' + '</div>' + "\n"

        thehtmltext = processed_source

    elif mode.lower() in ['ptx', 'mbx']:
        original_source_lines = original_source.split("\n")
   #     print "sageexample component_separated", original_source
        processed_source = ""
        this_portion = ""
        sageinputmode = True
        for line in original_source_lines:
            #stripped_line = line.strip()
            line = re.sub("\s*(sage|\.\.\.\.)", r"\1", line)  # some people indent every sage: line
            if line.startswith("sage:") or line.startswith("....:") or (sageinputmode and this_portion.endswith("\\\n")):  # get rid of the 'sage: '
                line = re.sub("sage:\s?", "", line)
                line = re.sub("\.\.\.\.:\s?", "    ", line)
         #       if line.startswith("sage:") or line.startswith("....:"):
         #           line = line[5:]
         #           line = line.lstrip()
                if not sageinputmode:
                  #  this_portion = re.sub("<", "<lt/>", this_portion)
                    this_portion = re.sub("<", "&lt;", this_portion)
                    processed_source += "\n" + '<output>' + this_portion + '</output>' + '</sage>' + "\n"
                    sageinputmode = True
                    this_portion = line + "\n"
                else:
                    this_portion += line + "\n"
            else:
                if sageinputmode:
                 #   this_portion = re.sub("<", "<lt/>", this_portion)
                    this_portion = re.sub("<", "&lt;", this_portion)
                    processed_source += "\n" + "<sage><input>" + this_portion + "</input>" + "\n"
                    sageinputmode = False
                    this_portion = line + "\n"
                else:
                    this_portion += line + "\n"
  ###  <lt/>###  <lt/>###  <lt/> , "&lt;", this_portion)
        this_portion = re.sub("<", "&lt;", this_portion)
        if sageinputmode:
            processed_source += "\n" + "<sage><input>" + this_portion + "</input></sage>" + "\n"
        else:
            processed_source += "\n" + '<output>' + this_portion + '</output>' + '</sage>' + "\n"

        thehtmltext = processed_source


    return thehtmltext

#############

def SItoPTX(txt):

    mag = txt.group(1)
    units = txt.group(2)

    print("SI",mag,units,"IS")

    the_units_full = sitoPTX(units)

    the_units = re.sub(r"\s*<quantity>\s*", "", the_units_full)
    the_units = re.sub(r"\s*</quantity>\s*", "", the_units)

    the_answer = "<quantity>"
#    the_answer += "\n"
    the_answer += "<mag>" + mag + "</mag>"
#    the_answer += "\n"
    the_answer += the_units
#    the_answer += "\n"
    the_answer += "</quantity>"

    return the_answer

#-------------#

def sitoPTX(txt_or_units):

    try:
        the_units = txt_or_units.group(1)
    except:
        the_units = txt_or_units

    if "/" in the_units:
        the_top, the_bot = the_units.split("/", 1)
        print("found the_top, the_bot",the_top, the_bot,"xxx")

    else:
        the_top = the_units
        the_bot = ""

    the_top_ans = sitoP(the_top)
    the_bot_ans = sitoP(the_bot, "bot")

    the_ans = "<quantity>" + the_top_ans + the_bot_ans + "</quantity>"

    return the_ans

#-------------#

def sitoP(unit, loc="top"):

    if not unit:
        return ""

    if "." in unit:
        unitL, unitR = unit.split(".", 1)
        return sitoP(unitR, loc) + sitoP(unitR, loc)
    if "/" in unit:
        unitL, unitR = unit.split("/", 1)
        return sitoP(unitR, "bot") + sitoP(unitR, "bot")

    if r"^" in unit:
        the_unit, the_exp = unit.split(r"^")
        print("split to get",the_unit,"^",the_exp)
    else:
        the_unit = unit
        the_exp = ""

    if the_unit == 'g':
        the_inside = 'base="gram"'
    elif the_unit == 'm':
        the_inside = 'base="meter"'
    elif the_unit == 'dm':
        the_inside = 'prefix= "deci" base="meter"'
    elif the_unit == 'cm':
        the_inside = 'prefix= "centi" base="meter"'
    elif the_unit == 'mm':
        the_inside = 'prefix= "milli" base="meter"'
    elif the_unit == '\\celsius':
        the_inside = 'base="celsius"'
    elif the_unit in ['s', '\\second']:
        the_inside = 'base="second"'
    elif the_unit == 'min':
        the_inside = 'base="minute"'
    elif the_unit == 'atm':
        the_inside = 'base="atmosphere"'
    elif the_unit == 'W':
        the_inside = 'base="watt"'
    elif the_unit == 'MW':
        the_inside = 'prefix="mega" base="watt"'
    elif the_unit == 'J':
        the_inside = 'base="joule"'
    elif the_unit == 'K':
        the_inside = 'base="kelvin"'
    elif the_unit == 'yr':
        the_inside = 'base="year"'
    elif the_unit == '\\%':
        the_inside = 'base="percent"'
    elif the_unit == 'ha':
        the_inside = 'base="hectare"'
    elif the_unit == 'MJ':
        the_inside = 'prefix="mega" base="joule"'
    elif the_unit == 'kg':
        the_inside = 'prefix="kilo" base="gram"'
    elif the_unit == 'Mg':
        the_inside = 'prefix="mega" base="gram"'
    elif the_unit in ['l', 'L']:
        the_inside = 'base="liter"'
    elif the_unit in ['ml', 'mL']:
        the_inside = 'prefix="mili" base="liter"'
    elif the_unit in ['mg']:
        the_inside = 'prefix="mili" base="gram"'
    elif the_unit in ['ng']:
        the_inside = 'prefix="nano" base="gram"'
    elif the_unit in ['\\micro\\gram']:
        the_inside = 'prefix="micro" base="gram"'
    else:
        print("ERROR, unknown unit", unit, "xx",the_unit, "??")
        the_inside = 'ERROR'

    if the_exp:
        the_inside += ' exp="' + the_exp + '"'

    if loc == "bot":
        the_ans = '<per ' + the_inside + '/>'
    else:
        the_ans = '<unit ' + the_inside + '/>'

    return the_ans

