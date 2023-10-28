# -*- coding: utf-8 -*-

import os
import re
import sys
import logging
import getopt
import random
import time
import codecs

import preprocess
import component
import processenvironments
import headerandcss
import dandr
import utilities
import mapping
import postprocess

##########################

def vvideotolink(text):
    # temporary, for openintro stats

    thetext = text

    thetext = re.sub(r"\\vvideohref\s*{(.*)",vvideotoli,thetext,0,re.DOTALL)

    return thetext

def vvideotoli(txt):

    thetext = txt.group(1)

    thefootnote,therest = utilities.first_bracketed_string(thetext,depth=1)
    thefootnote = utilities.strip_brackets("{"+thefootnote)
    theyoutubeid = re.sub(r"&.*$","",thefootnote)
    theyoutubeid = re.sub(r"^.*-","",theyoutubeid)

    videolink = '&nbsp;&nbsp;<span class="videolink"><a href="https://www.youtube.com/watch?v='+theyoutubeid+'">'+"&#127909;"+'</a></span>'

    return videolink+therest

############

def ref_to_knowl(text, link=True):
    """Convert LaTeX \ref and \eqref to a knowl of the referenced text.

    """

    thetext = text
    global makereflink
    makereflink = link

    # when we have "Figure~\ref{fig:xyz}" we want that whole string as the knowl
    # we need to detect "Section \ref{sec:xyz}" and make it a link, not a knowl

    thetext = re.sub(r"\\eqref{(.*?)}",eqref_to_kn,thetext,0,re.DOTALL)
    thetext = re.sub(r"(\\S)\s*?(\s|~|&nbsp;){0,1}\\ref\*{0,1}\s*{(.*?)}",
                       ref_to_kn,thetext,0,re.DOTALL)
    thetext = re.sub(r"([A-Za-z]+\.?)\s*?(\s|~|&nbsp;){0,1}\\ref\*{0,1}\s*{(.*?)}",
                       ref_to_kn,thetext,0,re.DOTALL)
    thetext = re.sub(r"(\w+)( *)\\ref\*{0,1}\s*{([^{}]+)}",ref_to_kn,thetext,0,re.DOTALL)
      # do it again, with a throw-away first character
      # (why do we do that?)
    thetext = re.sub(r"(.{1})( *)\\ref\*{0,1}\s*{([^{}]+)}",ref_to_kn,thetext,0,re.DOTALL)

      #what if a \ref{...} has no previous character?
    thetext = re.sub(r"(\S*)( *)\\ref\*{0,1}\s*{([^{}]+)}",ref_to_kn,thetext,0,re.DOTALL)

    return(thetext)

def ref_to_kn(txt):

    ctype = txt.group(1)
    ctypestrip = ctype.strip()
    thespace = txt.group(2)
    thelabel = txt.group(3)
    thelabel = re.sub(r" *\n *"," ",thelabel)  # labels can have extraneous \n's
    thelabel = utilities.safe_name(thelabel, idname=True)

    if ctype.endswith("\\"):
        ctype = ctype[:-1]

    if component.target == 'html':
         thespace = "&nbsp;"
    elif component.target == 'ptx':
         thespace = "<nbsp />"
    elif component.target == 'latex':
         thespace = "~"

 # if we have "Lemmas 2.7 and 3.2", then "Lemmas" should be part of the
 # link, but "and" should not   
    if ((not ctypestrip) or 
        (ctypestrip in  ["and","from","of","to","through","in","by","that"]) or 
         ctypestrip.endswith("END")  or    #  ctype was a sha1END
     # next one misses  Prop. \ref{prop:xxxx}
         ctypestrip.endswith(tuple([".",",",":",";"]))  or   # ctype was punctuation 
        (not ctypestrip.startswith(r"\S") and  not ctypestrip[0].isalpha())
       ):
        clickon = ""
        thespace = ""
        previous_word = ctype.strip() + " "
    else:
        clickon = ctype
        previous_word = ""

    if ctypestrip.startswith("END"):
        previous_word += "END"
        ctype = ctype[3:]
        clickon = clickon[3:]

    if component.target == 'html':
        try:
            codenumber = component.label[thelabel]["codenumber"]
            if codenumber:   # things like footnotes have codenumber = ""
                clickon += thespace + component.label[thelabel]["codenumber"]
        except KeyError:
            logging.error("label %s not known", thelabel)
            clickon += thespace + "ERR"+thelabel+"ThereWasAnERRor"

        try:
            filestub = component.label[thelabel]["sha1"].strip()
            filename = utilities.safe_name(filestub, idname=True) + '.knowl'
        except KeyError:
            logging.error("Missing Label: %s", thelabel)
            clickon = thelabel
            # see 1304.0738, which is probably not worth fixing
            previous_word = re.sub("END END","END",previous_word)
            return previous_word + '\\missingreflink{'+clickon+'}'

    # investigate how the extra END can be avoided.  Seems to involve $\S$
    # See end of 3rd paragraph of intro to 0809.2034
    previous_word = re.sub("END END","END",previous_word)

    # to do: make a non-plural version of ctype

    # The above code is okay if we are making a knowl, but if the \ref{...}
    # is to a chapter or section, then we need to make a link.  

    linkflag = False
    if component.target == 'html':
        try:
            sha1 = component.label[thelabel]["sha1"]
        except KeyError:
            logging.error("missing label %s", thelabel)
            return "XX"+ctype+thespace+thelabel+"XX"

        try:
            codenumber = component.environment[sha1]['codenumber']
            section_type = component.environment[sha1]['marker']
            if section_type == 'blob' and 'sec0' in component.environment[sha1]:
                is_sec0 = True
            else:
                is_sec0 = False

            if section_type in component.math_environments:
                # they should have used \eqref{...}
                clickon = "(" + codenumber + ")"
                if ctype:
                    previous_word = ctype + " "
                else:
                    previous_word = ""
        except KeyError:
            logging.error("missing codenumber")
            codenumber = "000000.1111111"
            section_type = ctype.lower()
            is_sec0 = False
        codenumber_dash = re.sub(r"\.","-",codenumber)
        if section_type in ['chapter','section']:
            filename = section_type + codenumber_dash + ".html"
            linkflag = True
                   # still need to interpret section 4.0.1 as section 4

        if (component.tocstyle == "book" and section_type == "section"):
            logging.debug("Linking to a SECtion %s from codenumber %s", thelabel, codenumber)
            logging.debug("from section_type %s", section_type)
            parentsection = re.match("^(.*?)(\.[0-9])*$",codenumber).group(1)
            filename = 'section' + codenumber_dash + '.html'
            if is_sec0:
                filename = 'section'+parentsection+'.html'
                clickon = re.sub("\.[^\.]+$","",clickon)  # a hack: should handle sec0 earlier
            linkflag = True
            logging.debug("made link %s", filename)

        elif section_type in ['subsection','subsubsection']:

#  go back and make parentsection a property instead of re-deriving it each time

            logging.debug("Linking to a SECTION %s from section_type %s",
                           thelabel, section_type)
            parentsection = re.match("^(.*?)(\.[0-9])*$",codenumber).group(1)
            logging.debug("parent section: %s from codenumber %s",
                           parentsection, codenumber)
            filename = 'section'+parentsection+'.html#subsection'+codenumber_dash
            if not component.toplevel:  # i.e., "chapter is the top, so sections use 2-level numbering
                parentsection = re.match("^((.*?)\.([0-9]+)).*$",codenumber).group(1)
                logging.debug("revised parent section: %s from codenumber %s",
                               parentsection, codenumber)
                parentsection_dash = re.sub("\.","-",parentsection)
                filename = 'section'+parentsection_dash+'.html#subsection'+codenumber_dash
            linkflag = True
            logging.debug("made link %s", filename)

        elif is_sec0:
            logging.debug("Linking to a sec0 %s from codenumber %s",
                           thelabel, codenumber)
            logging.debug("from section_type %s", section_type)
            logging.debug("sec0: %s", component.environment[sha1]["sec0"])
            this_type = "section"  # is that a reasonable default?
            parentsection = re.match("^(.*?)(\.[0-9])*$",codenumber).group(1)
            parentsection_dash = parentsection
            if component.tocstyle == "book":
                if component.environment[sha1]["sec0"] == "section":
                    this_type = "chapter"
                    clickon = re.sub("\.[^\.]+$","",clickon)  # a hack: should handle sec0 earlier
                else:
                 #   this_type = section_type
                    this_type = "section"
                    parentsection = re.match("^((.*?)\.([0-9]+)).*$",codenumber).group(1)
                    parentsection_dash = re.sub("\.","-",parentsection)
                    # if we get this far, then the codenumber is actually too large by one,
                    # because of a bug in numbering section 0s.
                    newcodenumber_start = codenumber[:-1]
                    newcodenumber_end = int(codenumber[-1]) - 1
                    if newcodenumber_end == -1:  newcodenumber_end = 9
                    if newcodenumber_end or not newcodenumber_start.endswith("."):   
                            # i.e., not 0, or previous ending was like ".11"
                        newcodenumber = newcodenumber_start + str(newcodenumber_end)
                    else:  # take away the "." at the end
                        newcodenumber = newcodenumber_start[:-1]
                        
                    clickon = re.sub("[0-9].*$",newcodenumber,clickon)
                    codenumber_dash = re.sub("\.","-",newcodenumber)
                    logging.debug("revised parent section: %s from codenumber %s",
                                   parentsection, codenumber)
                    logging.debug("new codenumber_dash %s", codenumber_dash)

            filename = this_type + parentsection_dash + '.html'
            if parentsection_dash != codenumber_dash:
                filename += '#subsection'+codenumber_dash
            linkflag = True
            logging.debug("made link %s", filename)

        logging.debug("after switches: %s", filename)

    if component.target == 'html':
        if linkflag:
            thelink = '<a class="internal" href="'+filename+'">'
            thelink += clickon
            thelink += '</a>'

        else:
            thelink = '<a knowl="'+filename+'">'
            thelink += clickon
            thelink += '</a>'
    elif component.target == 'ptx':
        thelink = '<xref ref="' + thelabel + '">'
        thelink += clickon
        thelink += '</xref>'
        return previous_word+thelink


    if makereflink:
        return previous_word+thelink
    else:
        return previous_word+clickon

def eqref_to_kn(txt):

    thelabel = txt.group(1)

    thelabel = re.sub(r" *\n *"," ",thelabel)  # labels can have extraneous \n's
    thelabel = utilities.safe_name(thelabel, idname=True)

    try:
        clickon = component.label[thelabel]["codenumber"]
    except KeyError:
        logging.error("missing label: %s", thelabel)
        clickon = thelabel
        return '('+clickon+')'

    clickon = '('+clickon+')'

    try:
        filestub = component.label[thelabel]["sha1"]   # eventually we will use a different filename?
        filename = utilities.safe_name(filestub, idname=True) + '.knowl'
    except KeyError:
        logging.error("something went wrong %s", thelabel)
        filename = "XXXX.knowl"
        clickon += "TherewasanERROR"

    if component.target == 'html':
        thelink = '<a knowl="'+filename+'">'
        thelink += clickon
        thelink += '</a>'
    elif component.target == 'ptx':
        thelink = '<xref ref="' + thelabel + '" />'

    if makereflink:
        return thelink
    else:
        return clickon

##################

def cite_to_knowl(text, link=True):
    """Convert LaTeX \cite to a knowl of the referenced bibliographic entry.

    """

    # this is abad hack, because I could not find where this was beign called incorrectly
    if component.target == 'ptx':
        return text
 ###  need to make this like ref_to_knowl.  Why do we use something_else_changed here,
 ###  but not in ref_to_knowl?
    logging.debug("process cite to knowl: %s", text[:20])
    thetext = text
    global makecitelink
    makecitelink = link

    utilities.something_else_changed = 1
    while utilities.something_else_changed:

        utilities.something_else_changed = 0
        thetext = re.sub(r"(\S*)\s*(\s|~|&nbsp;)\\(cite|citeib)\b(.*)",cite_to_kn,thetext,0,re.DOTALL)

    return(thetext)

def cite_to_kn(txt):

    theword = txt.group(1)
    thespace = txt.group(2)
    thecite = txt.group(3)
    thetext = txt.group(4)
    thetext = thetext.lstrip()

    if theword.endswith("\\"):
        theword = theword[:-1]

    utilities.something_else_changed += 1

    if component.target == 'html':
         thespace = "&nbsp;"
    elif component.target == 'ptx':
         thespace = "<nbsp />"
    elif component.target == 'latex':
         thespace = "~"

    if theword.endswith(tuple([".",",",":",";"])):   # ctype was punctuation
        thespace = " "
    elif not theword:
        thespace = ""  # no point in putting a space after nothing

    if thecite == "citeib": 
        if not thetext.startswith("["):
            logging.error("citeib with no first argument")
            return thetext
        else:
            ibid_arg, thetext = utilities.first_bracketed_string(thetext,0,"[","]")
            ibid_arg = utilities.strip_brackets(ibid_arg,"[","]")
            thetext = thetext.lstrip()
    else:
        ibid_arg = ""

    if thetext.startswith("["):
        sq_arg, thetext = utilities.first_bracketed_string(thetext,0,"[","]")
        sq_arg = utilities.strip_brackets(sq_arg,"[","]")
        thetext = thetext.lstrip()
    else:
        sq_arg = ""

    if not thetext.startswith("{"):
        logging.error("cite with no argument")
        return thetext
    else:
        theref, everythingelse = utilities.first_bracketed_string(thetext)
        theref = theref.strip()
        theref = utilities.strip_brackets(theref)
        theref = theref.strip()
    
    # Some people use multiple, comma-separated citations.
    separated_refs = theref.split(",")

    if len(separated_refs) == 1:
        theref = utilities.safe_name(theref, idname=True)
        thefile = theref + '.knowl'  # later we will make a better naming scheme
        if sq_arg:
            sq_arg = ", "+sq_arg
        try:
            thelabel = component.environment['bibitem' + theref]['thelabel']
        except KeyError:
            thelabel = theref
            logging.error("Missing bibitem: %s",'bibitem' + theref)
        if ibid_arg:
            clickon = '['+ibid_arg+sq_arg+']'
        else:
            clickon = '['+thelabel+sq_arg+']'

        if component.target == 'html':
            thelink = '<a knowl="'+thefile+'">'
            thelink += clickon
            thelink += '</a>'
        elif component.target == 'ptx':
            thelink = '<xref ref="' + theref + '" />'

    else:
        clickon = ""
        thelink = ""
        for oneref in separated_refs:
            this_ref = oneref.strip()
            this_ref = utilities.strip_brackets(this_ref)
            this_ref = utilities.safe_name(this_ref.strip(), idname=True)
            thefile = this_ref + '.knowl'
            try:
                thelabel = component.environment['bibitem' + this_ref]['thelabel']
            except KeyError:
                thelabel = this_ref
                logging.error("Missing bibitem: %s",'bibitem' + this_ref)
            clickon += thelabel
            clickon += ', '
            thelink += '<a knowl="'+thefile+'">'
            thelink += thelabel
            thelink += '</a>'
            thelink += ', '
        thelink = re.sub(", $","",thelink)
        thelink = '['+thelink+']'
        clickon = '['+clickon+']'

    clickon = utilities.remove_silly_brackets(clickon)  # need to make one catch-all conversion
    thelink = utilities.remove_silly_brackets(thelink)  # need to make one catch-all conversion

    if makecitelink:
        return theword + thespace + thelink + everythingelse
    else:
        return theword + thespace + clickon + everythingelse

##################

def expandhtml(txt, sec0only=False):

    try:
        sha1head = txt.group(1)
        sha1key = txt.group(2)
    except AttributeError:
        if len(txt) != 40:  # okay if we passes a sha1key for a top level page
            logging.error("missing sha1head or sha1key in %s", txt)
        sha1head = "nnoonnee"   # not used anyway
        sha1key = txt

    comp = component.environment[sha1key]

    rawmode = False

    if sec0only:
        if "sec0" not in comp:
            return sha1head + sha1key + "END"

    marker = comp['marker']
    filestub = utilities.safe_name(sha1key, idname=True)

    utilities.something_changed += 1

    if marker in ["proof", "solution"]  and component.target == 'html' and component.knowlify_proofs:
        logging.debug("making a %s be a knowl", marker)
        link_start = "\n<article class='hiddenproof'><a knowl='" + filestub + ".knowl'><h5 class='heading'><span class='type'>"
        link_end = "</span></h5></a></article>\n"
        if marker == "proof":   # should we use marker.title() ?
            squaregroup = comp['sqgroup']
            title = squaregroup
            if title.startswith("of "):
                title = "Proof " + title
            if not title:
                title = "Proof"
            return link_start + title + link_end
         #   return "\n<article class='hiddenproof'><a knowl='" + filestub + ".knowl'><h5 class='heading'><span class='type'>" + title + "</h5></a></article>\n"
        else:
            return link_start + "Solution" + link_end
         #   return "\n<article class='hiddenproof'><a knowl='" + filestub + ".knowl'><h5 class='heading'>Solution</h5></a></article>\n"

    if marker == 'image':
        if comp[component.target]:
            return comp[component.target]
        else:
            img_html = expandimage_html(comp)
            component.environment[sha1key][component.target] = img_html
        return img_html

    if marker in ['verb','verbatim', 'program']:    # would be better to have type == 'verbatim' ?
        thehtmltext = comp['component_separated']
        thehtmltext = re.sub("<", "&lt;", thehtmltext)

    elif marker in ['sageexample']:
        thehtmltext = utilities.makesagecell(comp['component_separated'], component.target)

    else:
        try:
            thehtmltext = comp[component.target]
        except KeyError:
            if marker not in component.math_environments:
                logging.error("no component.target %s with marker %s", comp, marker)
                thehtmltext = ""
            else:  # need to rethink this
                thehtmltext = comp["component_separated"]
#                if comp['marker'] == 'mathmacro'
#                    thehtmltext = "\\" + comp['macro'] + comp["component_separated"]
#                elif comp['marker'] == '$':
#                    thehtmltext = "$" + comp['macro'] + "$"
#                else:
#                    thehtmltext = comp["component_separated"]
#                rawmode = True

    if not thehtmltext.strip():
     #   if marker not in component.math_environments and marker != "endlist":
     # why had we allowed empty thehtmltext for math environments?
        if marker != "endlist":
            logging.error("empty x %s y %s z %s w", marker, sha1key, comp["component_raw"])
        return ""     # endlist is not really an environment

    if component.environment_types[marker]['class'] == 'hint':
        if component.target == 'html':
            if component.hide_hints:
                thehtmltext = re.sub(r'"',r"'",thehtmltext)  # because knowl class="internal"
                                                             # value = "<the_hint>" is confused by "
            else:
                return "\n<a knowl='" + filestub + ".knowl'>Hint</a>\n"

    if marker in component.verbatim_environments:
        thehtmltext = re.sub("~","&#126;",thehtmltext)

    tagsandhead = tagsandheading(sha1key, target=component.target)
    if rawmode:
        tagsandhead = ('', '', '')

    #  hack: determine the right way to do this.  see example:
    #  http://sl2x.aimath.org/development/collectedworks/htmlpaper/dg-ga__9511018/section4x.html

    if "\\tag " in thehtmltext:
        thehtmltext = re.sub(r"\\tag\s+(\S+)",r"\\tag{\1}",thehtmltext)

    if component.target == 'html':
        return tagsandhead[0] + utilities.tex_to_html(tagsandhead[1]) + thehtmltext + tagsandhead[2]
    elif component.target == 'ptx':
        return tagsandhead[0] + utilities.tex_to_ptx(tagsandhead[1]) + thehtmltext + tagsandhead[2]

##################

def expandlatex(txt):

    # copied from expandhtml.  need to rethink and unify

    try:
        sha1head = txt.group(1)
        sha1key = txt.group(2)
    except AttributeError:
        logging.error("missing sha1head or sha1key in %s", txt)
        sha1head = "nnoonnee"
        sha1key = txt

    utilities.something_changed += 1

    comp = component.environment[sha1key]
    marker = comp['marker']
    thelatex = comp['component_separated']

    logging.info("in expandlatex: %s", thelatex[-50:])

    if marker in ['verb','verbatim','center','equation', 'sageexample', 'program']:   
        return "\\begin{" + marker + "}" + thelatex + "\\end{" + marker + "}"

    try:
        if component.environment_types[marker]['class'] in ["table", "figure"]:
            return "\\begin{" + marker + "}" + thelatex + "\\end{" + marker + "}"
    except KeyError:
        logging.error("unknown marker %s", marker)

#    if marker == "endlist":
#        return ""     # endlist is not really an environment

    tagsandhead = tagsandheading(sha1key, target=component.target)

    return tagsandhead[0] + tagsandhead[1] + thelatex + tagsandhead[2]

####################

def expandseparated(txt):

    # there are other functions which do similar things.
    # need to decide how to handle each case (LaTeX, HTML, PTX)
    # and then write appropriately named functions.
    try:
        sha1head = txt.group(1)
        sha1key = txt.group(2)
    except AttributeError:
        sha1head = "nnoonnee"
        sha1key = txt

    utilities.something_changed += 1

    comp = component.environment[sha1key]
    marker = comp['marker']

    theseparatedtext = comp['component_separated']

    if not theseparatedtext:
        return ""     # is there any case we want tags around nothing?

    tagsandhead = tagsandheading(sha1key, target=component.target)

    return tagsandhead[0] + tagsandhead[1] + theseparatedtext + tagsandhead[2]

###############

def img_scale_percent(comp):
    """ Convert size_directive to an integer width percent.
        Return 73 as the default.
    """

    try:
        this_size_directive = comp['size_directive']
    except KeyError:
        this_size_directive = ""

    if not this_size_directive:
        logging.warning("image with unknown size: %s", comp['src_file'])
        return 73

    this_size_match = re.match(r".*(scale|width)\s*=\s*([0-9.]+)((in)?).*", this_size_directive)
    if not this_size_match:
        logging.warning("failed to determine image size: %s", comp['src_file'])
        return 73

    if this_size_match.group(1) == "scale":
        this_size = utilities.to_integer_percent(this_size_match.group(2))
    elif this_size_match.group(1) == "width":
        if this_size_match.group(3) == "in":
            this_size = utilities.to_integer_percent(this_size_match.group(2),5.33)
        else:
            this_size = utilities.to_integer_percent(this_size_match.group(2))

    return this_size

def expandimage_html(comp):

    if comp['image_type'] == 'file':
        if not comp['src_file']:
            logging.error("no source file: %s", comp)
            return '<img src="MISSINGFILE"  width="400" />'

        if comp['imagemarker'] == "includegraphicsinternal":
            # no need to reconvert
            out_filename = comp['src_file']
        else:
            out_filename, imagefactor = utilities.imageconvert(component.inputdirectory+comp['src_file'])

    else:
        logging.error("unknown image source")
        out_filename = "UNKNOWN_IMAGE_SOURCE"

    if component.target == 'html':
        tmp = '<img src="'
        tmp += out_filename
        tmp += '" />'
    # need to do this differently, because need different files for LaTeX and HTML
    elif component.target == 'ptx':
        image_width_percent = img_scale_percent(comp)
 #       print "    image comp"
 #       print comp
 #       print "    out_filename"
 #       print out_filename
        tmp = '<image '
        if image_width_percent:
            tmp += 'width="' + str(image_width_percent) + '%"' + ' '
        tmp += 'source="'
   #     tmp += "images" + "/" + comp['src_file']
        if out_filename:
            tmp += 'images' + '/' + re.sub(r".*/([^/]+)$",r"\1",out_filename)
        else:
            tmp += comp['src_file']
        tmp += '" />'

    return tmp
    
###############

def tagsandheading(sha1key, target="html"):
    """Returns the html opening tag, header, and closing tag for a component.

    This function is a big mess of if-then's.  It needs to be rethought.

    Also need to make a LaTeX and a PTX version.
    """

    comp = component.environment[sha1key]
    marker = comp['marker']

    try:
        thisenvironment = component.environment_types[marker]
    except KeyError:
        logging.warning("unknown environment %s in  %s", marker, comp)
        return ['<div class="unprocessed">','','</div>']

    if marker in ["verbatim","lstlisting"]:
        return ['<pre>','','</pre>']

    if marker in ["program"]:
        return ['<program><input>','','</input></program>']

    if marker in ["sageexample"]:
        return ['','','']

    if marker in ["picture"]:
        return ['','','']

    if marker == "verb":
        if component.target == 'ptx':
            return ['<c>','','</c>']
        else:
            return ['<code class="inline">','','</code>']
      # "code" is not best, because it may not be code, but it seems to look okay

    try:
        thecodenumber = comp['codenumber'] 
    except KeyError:
        thecodenumber = ""
    
    theclass = thisenvironment['class']

    try:
        parent_sha1 = comp['parent']
        parentcomp = component.environment[parent_sha1]
    except KeyError:
        parentcomp = ""

    try:
        thisID = comp['sl2xID']
    except KeyError:
     #   logging.debug("no sl2xID for %s", comp)
        thisID = "MISSING"

    if 'latex_label' in comp:
        latex_label = comp['latex_label']
    else:
        latex_label = ""

    if marker in ['footnote']:
      if component.target == 'html':
        try:
            id = comp['id']
            opening_tag = '<sup><a knowl="" class="id-ref" refid="'+id+'">note</a></sup>'
            opening_tag += '<span id="'+id+'" style="display: none" class="tex2jax_ignore" >'
            closing_tag = '</span>'
            return [opening_tag,"",closing_tag]
        except KeyError:
            logging.error("footnote id error: %s", comp)
            return ["AA","","BB"]
      elif component.target == 'ptx':
          opening_tag = '<fn'
          if latex_label:
              opening_tag += ' xml:id="' + latex_label + '"'
          opening_tag += '>'
          closing_tag = '</fn>'
          return [opening_tag,"",closing_tag]

    if marker in ['tikz', 'tikzpicture']:
        opening_tag = "\\begin{tikzpicture}"
        closing_tag = "\\end{tikzpicture}"
        return [opening_tag,"",closing_tag]

    if marker in ['circuitikz']:
        opening_tag = "\\begin{circuitikz}"
        closing_tag = "\\end{circuitikz}"
        return [opening_tag,"",closing_tag]

    if marker in ['generictheorem']:   # typically a user-defined theorem
        logging.debug("found a generic theorem")
        typename = thisenvironment['typename']
        squaregroup = comp['sqgroup']
        title = squaregroup
        if component.target == 'html':
            title = ref_to_knowl(title,link=False)
            title = cite_to_knowl(title,link=False)
            opening_tag = '\n<article class="'+theclass+'-like" id="' + thisID + '">'
            closing_tag = '\n</article>\n'
            heading = '<h5 class="heading">'
            if title:
                heading += '<span class="title">' + title + '</span>'
            else:
                heading += '<span class="title">' + 'GTheorem' + '</span>'
            heading += '</h5>' 
        elif component.target == 'ptx':
            opening_tag = '<paragraphs' # + ' whyamihere '
            if latex_label:
                opening_tag += ' xml:id="' + latex_label + '"'
            opening_tag += '>'
            closing_tag = '</paragraphs>'
            if title:
                heading = '<title>' + title + '</title>'
            else:
                heading = ''
                logging.error('%s %s with no title', marker, typename)
        return [opening_tag,heading,closing_tag]

    
    if theclass in ['definition','theorem','exercise','example','remark']:
        typename = thisenvironment['typename']
        squaregroup = comp['sqgroup']
        this_star = comp['star']
        title = squaregroup
        if target == "html":
            title = ref_to_knowl(title,link=False)
            title = cite_to_knowl(title,link=False)
        logging.debug("here, and target is %s", target)
        if target == "html":
            opening_tag = '\n<article class="'+theclass+'-like" id="' + thisID + '">'
            closing_tag = '\n</article>\n'
            heading = '<h5 class="heading">'
            heading += '<span class="type">'+typename+'</span>'
            if not this_star:
                heading += '<span class="codenumber">'+thecodenumber+'</span>'
            if title:
                heading += '(<span class="parentitle">'+title+'</span>)'
            heading += '</h5>'
        elif target == "ptx":
            tagname = typename.lower()
            if tagname == "task":
                tagname = marker
            opening_tag = '\n<' + tagname
            if latex_label:
                opening_tag += ' xml:id="' + latex_label + '"'
            opening_tag += '>'
            closing_tag = '\n</' + tagname + '>\n'
            if title:
                heading = '<title>' + title + '</title>' + "\n" 
            else:
                heading= ''
        #    closing_tag = '</statement>' + '\n</' + typename.lower() + '>\n'
        #    if title:
        #        heading = '<title>' + title + '</title>' + "\n" + '<statement>'
        #    else:
        #        heading= '<statement>'
    #        heading = '<h5 class="heading">'
    #        heading += '<span class="type">'+typename+'</span>'
    #        heading += '<span class="codenumber">'+thecodenumber+'</span>'
        return [opening_tag,heading,closing_tag]

    if theclass in ['aside']:      # these are un-numbered environments
        typename = thisenvironment['typename']
        squaregroup = comp['sqgroup']
        title = squaregroup
        if target == "html":
            title = ref_to_knowl(title,link=False)
            title = cite_to_knowl(title,link=False)
            opening_tag = '\n<article class="'+theclass+'-like" id="' + thisID + '">'
            closing_tag = '\n</article>\n'
            heading = '<h5 class="heading">'
            heading += '<span class="type">'+typename+'</span>'
            heading += '<span class="codenumber">'+thecodenumber+'</span>'
            if title:
                heading += ' (<span class="title">'+title+'</span>)'
            heading += '</h5>'
        if target == "ptx":
            opening_tag = '\n' + '<aside>' + '\n'
            closing_tag = '\n</aside>\n'
            heading = ''
            if title:
                heading = '<title>'+title+'</title>'
        return [opening_tag,heading,closing_tag]

    elif theclass in ['text']:
        if target == "html":
            return ['\n<p id="' + thisID + '">','','</p>\n']
        elif target == "ptx":
            return ['\n<p>\n','','\n</p>\n']

   # each row in multi-line math can have its own tag
    elif theclass == 'mathrow':  # also insert the \tag{}
        if target == 'html':
            opening_tag =  ''
            if (thecodenumber and "x" not in thecodenumber and
               r"\tag{" not in comp[component.target] and comp['star'] != "*"):
                closing_tag =  '\\quad \\quad \\tag{'+thecodenumber+'}'
                closing_tag = '\\quad\\quad\\quad\\quad\\quad' + closing_tag
            else:
                closing_tag =  ''
            if comp['sqgroup'] == "end":
                if ("\\tag" not in closing_tag and not comp['star'] and
                                 r"\tag{" not in comp[component.target]):
                    closing_tag += '\\quad \\quad \\tag{'+thecodenumber+'}' + '\n'
            else:
                closing_tag += "\\\\" + "\n"
        elif target == 'ptx':
            opening_tag = '<mrow'
            if latex_label:
                opening_tag += ' xml:id="' + latex_label + '" '
                opening_tag += 'number="yes"'
            opening_tag += '>'
            closing_tag = '</mrow>\n'
        return [opening_tag,'',closing_tag]

    #mathwrapper: eqnarray, align, gather, alignat
    #mathcomponent: diagram, aligned, cases, (p|b|)matrix,  array
    elif theclass in ['mathwrapper','mathcomponent']:  # no \tag{}, because the tags go in the rows
        if target == "html":
            opening_tag =  '\\begin{'+marker+'}'     # + '\n'
            closing_tag =  '\n' + '\\end{'+marker+'}'
        elif target == "ptx":
            if theclass == 'mathcomponent':
                opening_tag =  '\\begin{'+marker+'}'     # + '\n'
                closing_tag =  '\n' + '\\end{'+marker+'}'
            else:
    # may be missing the case where we need md because of contained mrows
                opening_tag = '\n<md'
                if latex_label:
                    opening_tag += 'n xml:id="' + latex_label + '" '
                    opening_tag += '>'
                    closing_tag = '\n</mdn>\n'
                else:
                    opening_tag += '>'
                    closing_tag = '\n</md>\n'
        return [opening_tag,'',closing_tag]

    elif theclass in ['mathmacro']:  # no \tag{}, because the tags go in the rows
        opening_tag =  '\\'+ comp['macro']    # the argument should retain its {enclosing brackets} so don't add any (check on that)
        closing_tag =  ''
        return [opening_tag,'',closing_tag]

    #math: equation, multiline, split
    elif theclass == 'math':  # also insert the \tag{}
        if target == 'html':
            opening_tag =  '\\begin{'+marker+'}'

            if (thecodenumber and "x" not in thecodenumber and
                   r"\tag{" not in comp[component.target] and not comp['star']):
                closing_tag =  '\\quad\\quad\\tag{'+thecodenumber+'}\n\\end{'+marker+'}'
                if marker in ["multline", "split"]:   # split probably can't happen because (according to mathjax) split can't have a \tag{...}
                     closing_tag = '\\quad\\quad\\quad\\quad\\quad' + closing_tag
            else:
                closing_tag =  '\n\\end{'+marker+'}'
        elif target == "ptx":
            if marker in {'equation', 'reaction'}:
                if comp['star']:  
                    opening_tag = '\n<me'
                    closing_tag = '\n</me>\n'
                else:
                    opening_tag = '\n<men'
                    closing_tag = '\n</men>\n'
                if latex_label:
                    opening_tag += ' xml:id="' + latex_label + '" '
                opening_tag += '>\n'

            else:
                opening_tag = '\n<md'
                if latex_label:
                    opening_tag += ' xml:id="' + latex_label + '" '
                opening_tag += '>'
                closing_tag = '\n</md>\n'

        return [opening_tag,'',closing_tag]

    elif theclass == 'mathinline':  
        if target == 'html':
            opening_tag =  '\\('
            closing_tag =  '\\)'
        elif target == "ptx":
            opening_tag = '<m>'
            closing_tag = '</m>'
        return [opening_tag,'',closing_tag]

    elif theclass == 'hint':  
        if component.target == 'html':
            if component.hide_hints:
                opening_tag =  '<span class="hint"><a knowl="" class="internal" value="'
                closing_tag =  '">'+marker.title()+'</a></span>'
            else:
                opening_tag =  '<span class="hint"><a knowl="xxxx">'
                closing_tag =  marker.title() + '</a></span>'
        elif component.target == 'ptx':
            opening_tag = '<' + marker
            if latex_label:
                opening_tag += ' xml:id="' + latex_label + '" '
            opening_tag += '>'
            closing_tag = '</' + marker + '>'
        return [opening_tag,"",closing_tag]

    elif theclass == 'section':
        # section titles and chapter titles

        section_marker = comp['marker']
        try:
            title = comp['title']
        except KeyError:
            try:
                title = comp['sqgroup']
            except:
                title = "Missing Title"
        if target == 'html':
            thecodenumber_dash = re.sub("\.","-",thecodenumber)
            secindex = component.sectioncounters.index(section_marker)
            title = utilities.tex_to_html(title)
            title = ref_to_knowl(title,link=False)
            title = cite_to_knowl(title,link=False)
            title = vvideotolink(title)
            opening_tag = '\n<section '
            opening_tag += 'class="' + section_marker + '" '
       #     opening_tag += 'class="'+comp['marker']+'" '
            opening_tag += 'id="' + thisID + '"'
            opening_tag += '>'
            closing_tag = '\n</section>\n'
            htag = 'h'+str(secindex+1)  # we want chapter to be h1, section h2, etc
            heading = '<' + htag + ' class="heading hide-type">'
            if "*" not in thecodenumber:
                heading += '<span class="type">'+section_marker.title()+'</span> '
                if thecodenumber and not thecodenumber.endswith("x"):
                    heading += '<span class="codenumber">'+thecodenumber+'</span>'
            if title == "XXXX":
                thetitle = ""
            else:
                thetitle = title
            heading += '<span class="title">'+thetitle+'</span>'
            heading += '</' + htag + '>' 
            if section_marker == "subsection":
                 opening_tag = '<a name="subsection'+thecodenumber_dash+'"></a>' + opening_tag
        elif target == 'ptx':
            title = ref_to_knowl(title,link=False)
            title = cite_to_knowl(title,link=False)
            opening_tag = "\n" + '<' + section_marker
            if section_marker == 'chapter':
                opening_tag += ' xmlns:xi="http://www.w3.org/2001/XInclude" '
            if latex_label:
                opening_tag += ' xml:id="' + latex_label + '"'
            opening_tag += '>\n'
            closing_tag = '</' + section_marker + '>'
            heading = '<title>' + title + '</title>'
            


        return [opening_tag,heading,closing_tag]

    elif theclass in ['proof','proofsketch']:
        squaregroup = comp['sqgroup']
        title = squaregroup
        if title.startswith("of "):
            title = "Proof " + title
        if target == "html":
            title = ref_to_knowl(title,link=False)
            title = cite_to_knowl(title,link=False)
        if component.target == 'html':
            opening_tag = '\n<article class="'+'proof'+'" id="' + thisID + '">'
            closing_tag = '\n</article>\n'
            heading = '<h5 class="heading">'
        elif component.target == 'ptx':
            opening_tag = "\n" + '<proof>' + "\n"
            closing_tag = '\n</proof>\n'
            heading = ""
        headingtitle = ""
        if component.target == 'html':
            if title:
                heading += '<span class="title">'+title+'</span>'
                headingtitle += '<span class="title">'+title+'</span>'
            elif marker == 'proofsketch':
                heading += 'Sketch of Proof'
            else:
                heading += 'Proof'
            heading += '</h5>' 
            if component.knowlify_proofs:
                return ["",headingtitle,""]
        return [opening_tag,heading,closing_tag]

    elif theclass == 'list':
        list_marker = comp['marker']
        squaregroup = comp['sqgroup']
        if list_marker == 'enumerate':
            if squaregroup:
                list_type = re.sub(r"[^a-zA-Z0-9]","",squaregroup)
                if target == "ptx":
                    return ['<ol label="' + list_type + '">','','</ol>']
                else:
                    return ['<ol type="' + list_type + '">','','</ol>']
            else:
                return ['<ol>','','</ol>']
        elif list_marker == 'descriptionlist':
            return ['<dl>','','</dl>']
        elif list_marker in ['parts','subparts']:
            return ['','','']
        else:
            return ['<ul>','','</ul>']

    elif theclass == 'item':
        #    print "          item"
        #    print comp
        #    print component.environment[comp['parent']]['marker']
            squaregroup = comp['sqgroup']
            logging.debug("theclass == 'item':", comp)
            if component.target == 'html':
                if squaregroup:
                    this_label = utilities.strip_brackets(comp['sqgroup'],"[","]")
                    return ['<li class="custom-list-style-type" label="' + this_label + '" id="' + thisID + '">',"","</li>\n"]
                else:
                    this_label = '(' + thecodenumber + ')'
                    return ['<li label="' + this_label + '" id="' + thisID + '">',"","</li>\n"]
            elif component.target == 'ptx':
                if component.environment[comp['parent']]['marker'] in ['parts']:
                    return ["\n<task>\n","","\n</task>\n"]
                if component.environment[comp['parent']]['marker'] in ['subparts']:
                    return ["\n<subtask>\n","","\n</subtask>\n"]
                if squaregroup:
                    this_label = utilities.strip_brackets(comp['sqgroup'],"[","]")
                    opening_tag = '<li class="custom-list-style-type" label="' + this_label + '"' 
                    if latex_label:
                        opening_tag += ' xml:id="' + latex_label + '" '
                    opening_tag += ' >'
                    closing_tag = "</li>\n"
                    return [opening_tag,"",closing_tag]
                else:
                    opening_tag = '<li'
                    if latex_label:
                        opening_tag += ' xml:id="' + latex_label + '" '
                    opening_tag += '>'
                    return [opening_tag,"","</li>\n"]

    elif marker == "quote":
        if component.target == 'html':
            return ['<div class="quote">','','</div>']
        elif component.target == 'ptx':
            return ['<blockquote>','','</blockquote>']

    elif marker == 'minipage':  # temporary for testing
        try:
            thecaption = comp['captionof'].strip()
            figtype = comp['countertype']

            thecaption_html = ref_to_knowl(thecaption)
            thecaption_html = cite_to_knowl(thecaption_html)
            thecaption_html = utilities.tex_to_html(thecaption_html)
            fullcaption = '<div class="caption">'
            fullcaption += '<span class="heading">'+figtype.title()+'</span>'
            fullcaption += '<span class="codenumber">'+thecodenumber+'</span>'
            fullcaption += thecaption_html
            fullcaption += '</div>'
        except KeyError:
            thecaption = ""
            fullcaption = ""

        placeholder = comp['marker']
        if component.target == 'html':
            return ['<div class="'+placeholder+'">','',fullcaption+'</div>']
        elif component.target == 'ptx' and thecaption:
         #   return ['<sidebyside>','<!-- <caption>' + thecaption + '</caption> -->','</sidebyside>']
            return ['\n<!-- <caption>' + utilities.tex_to_ptx_alphabets(thecaption) + '</caption> -->\n<sidebyside>','','</sidebyside>']
        else:
            return ['<sidebyside>','','</sidebyside>']


    elif theclass == 'layout':  # sections (sec0 in particular) end up here.

        if target == "html":
            try:    # why are we looking for a caption here?
                thecaption = comp['captionof']
                figtype = comp['countertype']
    
                thecaption_html = ref_to_knowl(thecaption)
                thecaption_html = cite_to_knowl(thecaption_html)
                thecaption_html = utilities.tex_to_html(thecaption_html)
                fullcaption = '<div class="caption">'
                fullcaption += '<span class="heading">'+figtype.title()+'</span>'
                fullcaption += '<span class="codenumber">'+thecodenumber+'</span>'
                fullcaption += thecaption_html
                fullcaption += '</div>'
            except KeyError:
                fullcaption = "" 

            placeholder = comp['marker']
            return ['<div class="'+placeholder+'">','',fullcaption+'</div>']
        elif target == "ptx":
            try:
                title = squaregroup
            except UnboundLocalError:
                title = ""
#            placeholder = comp['marker']
#   # what is "placeholder" for?
            if marker == "blob":   # probably means sec0
                return ['<introduction>','','</introduction>']
            elif marker in ["objectives", "sidebyside"]:  # what can that mean?
                this_title = ""
                if title:
                    this_title = '<title>'+title+'</title>'
                return['<' + marker + '>',this_title,'</' + marker + '>']
            elif marker in ['lateximage']:
                return['<image>\n<latex-image>','','</latex-image>\n</image>']
            else:  # what can that mean?
                return ['','','']

    elif theclass == 'table':
        if component.target == 'html':
            return ['<table id="' + thisID + '" >','','</table>']
        elif component.target == 'ptx':
            opening_tag = '<tabular'
            if latex_label:
                opening_tag += ' xml:id="' + latex_label + '" '
            opening_tag += '>'
            closing_tag = '</tabular>'
            return [opening_tag,'',closing_tag]



    elif marker in component.environments_with_captions:
        thecaption = comp['caption'].strip()
        try:
            thecaption_sha1 = comp['caption_sha1']
            thecaption_component = component.environment[thecaption_sha1][component.target]
        except KeyError:
            logging.warning("missing caption")
            thecaption_component = ""
        thecaption_target = thecaption_component
        try:
            thecodenumber = comp['codenumber']
        except KeyError:
            logging.error("found a %s with no codenumber", marker)
            return ['\n<figure>\n','','\n</figure>\n']
        if thecaption:
          if component.target == 'html':
            if marker == "wrapfigure":
                fullcaption = '<figcaption>'
                fullcaption += '<span class="heading">Figure</span>'
            else:
                fullcaption = '<figcaption>'
                fullcaption += '<span class="heading">'+marker.title()+'</span>'
            fullcaption += '<span class="codenumber">'+thecodenumber+'</span>'
            fullcaption += thecaption_target
            fullcaption += '</figcaption>'
          elif component.target == 'ptx':
              titleorcaption = "caption"
              if marker == "table":  # tables have titles, not captions
                  titleorcaption = "title"
              opening_tag = '<figure'
              if latex_label:
                  opening_tag += ' xml:id="' + latex_label + '" '
              if marker == "wrapfigure":     # need to rethink this for ptx
                  opening_tag += ' class = "wrap" '
              opening_tag += '>'
              closing_tag = '</figure>'
              fullcaption = '<' + titleorcaption + '>'
              fullcaption += thecaption_target
              fullcaption += '</' + titleorcaption + '>'
        else:
            logging.info("%s with no caption", marker)
            opening_tag = '<figure>' + "\n"
            closing_tag = "\n" + '</figure>' + "\n"
            fullcaption = ""

        
        if component.target == 'html':
            if marker == "wrapfigure":
                return ['<figure class="wrap">','','\n'+fullcaption+'\n</figure>\n']
            else:
                return ['\n<figure>\n','',fullcaption+'\n</figure>\n']
        elif component.target == 'ptx':
            return [opening_tag, '\n'+fullcaption+'\n', closing_tag + '\n']

    elif marker == "picture":  # can't be reached because of a previous if marker == "picture" ?
        return ['<div>','','</div><div><b>GNUplot/picture not implemented yet</b></div>']

    elif theclass == "none":
        return ['','','']
    elif theclass == "macro":
        themacro = '\\' + comp['macro']
        return [themacro,'','']
    else:
        logging.error("unknown class %s", theclass)
        return ['<div class="unprocessed">','<b>something else: '+theclass+'</b>','<b>end of something else</b></div>']

###############

def sectionlink(txt):
    '''
    Take a sha1code for a chapter and return an <h2> link to the section file
    FIX: it is only on a chapter page link
    '''

    sha1key=txt.group(2)

    comp = component.environment[sha1key]

    try:
        sectionfilename = comp['filename']
    except KeyError:
        logging.info("section with no filename %s", sha1key)
        sectionfilename = component.sectioncounters[component.toplevel + 1]  # ??? how to do it right?

        try:
            thecodenumber = comp['codenumber']
        except KeyError:
            thecodenumber = "000000000.111111111"
        thecodenumber_dash = re.sub("\.","-",thecodenumber)
        sectionfilename += thecodenumber_dash
        sectionfilename += "." + component.target

    if component.target == 'html':
        thelink = '<h2 class="link"><a href="'+sectionfilename+'">'
        thelink += utilities.tex_to_html(comp['title'])
        thelink += '</a></h2>\n'
    elif component.target == 'ptx':
        thelink = '<xi:include  href="'+sectionfilename+'" />'
        thelink += '\n'

    return thelink

###############

def arxivabstract(bibref,bibentry):

    hasarxiv = re.search(r"arXiv[ ~:]*([0-9]{4}\.[0-9]{4})(\b|v[0-9]+)",bibentry,re.I) # re.I :case insensitive
    try:
        arxiv_code = hasarxiv.group(1)
        thelink = '<div>'
  # uncomment these after implementing the code to fetch the abstract
  #      thelink += '<a knowl="'+bibref+'.abs.knowl">Abstract</a>'
  #      thelink += '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
        thelink += '<a href="http://arxiv.org/abs/'+arxiv_code+'">paper</a>'
        thelink += '</div>'
        return thelink

   # redo the following so that MR is actually scanned, and MR and ArXiv
   # work properly in all combinations
    except:  # no ArXiv code, so do nothing
        pass

#   need to make it work if there is both an ArXiv and MR code

    hasMR = re.search("MR:* *([0-9]{7})\\b",bibentry,re.I) # re.I :case insensitive
    try:
        MR_code = hasMR.group(1)
        thelink = '<div>'
        thelink += '<a href="http://ams.org/mathscinet/'+MR_code+'">AMS Math Review</a>'
        thelink += '</div>'
        return thelink
    except:
        return ""

##################

def pageheader(filename):

    try:
        fileindex = component.html_sections.index(filename)
        if fileindex < len(component.html_sections)-1:
            nextfilename = component.html_sections[fileindex+1]
        else:
           nextfilename = ""
        if fileindex > 0:
            prevfilename = component.html_sections[fileindex-1]
        else:
            prevfilename = ""
    except ValueError:
       nextfilename = ""
       prevfilename = ""

    theheader = headerandcss.header()

    try:
        theheader += mathjaxmacros(processby=component.target)
    except UnicodeDecodeError:
        logging.error("mathjaxmacros problem: %s", mathjaxmacros())
        macros_in_ascii = str(mathjaxmacros(), errors="ignore")
        theheader += macros_in_ascii

    if component.target == 'ptx':
        # not sure if this function is called when making PTX output
        theheader += "\n" + "</docinfo>" + "\n\n"

    if component.target == 'html':
        thetitle = '<h1 class="heading">'
        thetitle += '<span class="title">'
        thetitle += utilities.remove_silly_brackets(utilities.tex_to_html(component.title)) 
        thetitle += '</span></h1>'
    elif component.target == 'ptx':
        thetitle = '<title>'
        thetitle += utilities.remove_silly_brackets(utilities.tex_to_ptx(component.title))
        thetitle += '</title>'

    if component.target == 'html':
        theauthors = '<p class="byline">'
        if component.author_html:
            theauthors += component.author_html
        else:
            logging.error("No author name")
            theauthors += "Author Name"
        theauthors += '</p>'
    elif component.target == 'ptx':
        theauthors = ""
        for author in component.authorlist:
            theauthors += "<author>" + "\n"
            theauthors += "<personname>"
            theauthors += author
            theauthors += "</personname>" + "\n"
            theauthors += "</author>" + "\n"

    if component.target == 'html':
        theheader += '<header id="masthead">\n<div class="banner">\n<div class="container">'
        theheader += '\n<a id="logo-link" href="."></a>'
        theheader += '\n<div class="title-container">\n'
        theheader += thetitle

        try:
            theheader += "\n"+theauthors
        except UnicodeDecodeError:
            logging.error("theauthors problem: %s", theauthors)
            theauthors_in_ascii = theauthors.encode("utf-8") #, errors="ignore")
            theheader += theauthors_in_ascii

        theheader += '\n</div>\n'    # <div class="title-container">'
        theheader += '</div>\n'
        theheader += '</div>\n'


        theheader += '''<nav id="primary-navbar" class="navbar" style="">
            <div class="container">
'''
        theheader += '<div class="navbar-bottom-buttons toolbar toolbar-divisor-3">'
        theheader += '<button class="sidebar-left-toggle-button toolbar-item button" style="">Table of Contents</button>'
        theheader += pageprevnext(filename, "mobile")
        theheader += '</div>\n'  #  <!-- navbar-bottom-buttons toolbar toolbar-divisor-3 -->

        theheader += '''
           <div class="navbar-top-buttons">
                <button class="sidebar-left-toggle-button button active" style="">Table of Contents</button>
                <div class="toolbar toolbar-align-right">
'''

        # the index is in the navbar across the top, but only for the widest screen
        if component.index:
            if filename == "theindex.html":
                theheader += '<div class="toolbar-item-left">jump to:</div>'
            else:
                theheader += '<div class="toolbar-item-left"><a href="theindex.html">index</a></div>'

        theheader += pageprevnext(filename)
    elif component.target == 'ptx':
        theheader += "\n" + '<article>' + "\n"
        theheader += thetitle
        theheader += "\n" + '<frontmatter>' + "\n"
        theheader += '<titlepage>' + "\n"
        theheader += theauthors
        theheader += '</titlepage>' + "\n"
          # abstract should go here
        theheader += '</frontmatter>' + "\n" + "\n"

    if filename == "theindex.html":
        theheader += '''
<span class="indexnav">
<a href="#indexletter-a">A </a><a href="#indexletter-b">B </a><a href="#indexletter-c">C </a><a href="#indexletter-d">D </a><a href="#indexletter-e">E </a><a href="#indexletter-f">F </a><a href="#indexletter-g">G </a><a href="#indexletter-h">H </a><a href="#indexletter-i">I </a><a href="#indexletter-j">J </a><a href="#indexletter-k">K </a><a href="#indexletter-l">L </a><a href="#indexletter-m">M </a><br /><a href="#indexletter-n">N </a><a href="#indexletter-o">O </a><a href="#indexletter-p">P </a><a href="#indexletter-q">Q </a><a href="#indexletter-r">R </a><a href="#indexletter-s">S </a><a href="#indexletter-t">T </a><a href="#indexletter-u">U </a><a href="#indexletter-v">V </a><a href="#indexletter-w">W </a><a href="#indexletter-x">X </a><a href="#indexletter-y">Y </a><a href="#indexletter-z">Z </a>
</span>
'''
    if component.target == 'html':
        theheader += '</div>  <!-- toolbar toolbar-align-right  -->\n'
        theheader += '</div>  <!-- navbar-top-buttons -->\n'
        theheader += '''
        </div>  <!-- container -->
    </nav>
'''

        theheader += '</header>'

    return theheader

#############

def pagetoc(filename):

    try:
        fileindex = component.html_sections.index(filename)
        if fileindex < len(component.html_sections)-1:
            nextfilename = component.html_sections[fileindex+1]
        else:
           nextfilename = ""
        if fileindex > 0:
            prevfilename = component.html_sections[fileindex-1]
        else:
            prevfilename = ""
    except ValueError:
       nextfilename = ""
       prevfilename = ""

    thetoc = '<aside id="sidebar-left" class="sidebar">\n'
    thetoc += '<div class="sidebar-content">\n'
    thetoc += '\n<nav id="toc">'
    thetoc += component.thetoc
    thetoc += '</nav>\n'

    thetoc += '<div class="extras">\n'
    thetoc += '<a class="logo" href="https://www.mathjax.org"> <img title="Powered by MathJax" src="https://cdn.mathjax.org/mathjax/badge/badge.gif" border="0" alt="Powered by MathJax" /> </a>\n'
    thetoc += '<nav>\n'
    thetoc += '<a href="https://docs.google.com/forms/d/1vnyQAWbXD-Ae1j9pw_7GT_AFOgG8C_xRX0FSQQByiWs/viewform?usp=send_form">Feedback on the LaTeX to HTML conversion.</a>'
    thetoc += '</nav>\n'
    thetoc += '</div>\n'
    thetoc += '</div>\n'
    thetoc += '</aside>\n'

    thetoc = re.sub("vvi","ccc",thetoc)

    return thetoc

#############

def pageprevnext(filename, type=""):

    try:
        fileindex = component.html_sections.index(filename)
        if fileindex < len(component.html_sections)-1:
            nextfilename = component.html_sections[fileindex+1]
        else:
           nextfilename = ""
        if fileindex > 0:
            prevfilename = component.html_sections[fileindex-1]
        else:
            prevfilename = ""
    except ValueError:
       nextfilename = ""
       prevfilename = ""

    if type == "mobile":
        theprevnext = '<a class="previous-button toolbar-item button'
        if not prevfilename:
            theprevnext += " disabled"
        theprevnext += '" href="' + prevfilename + '">Previous</a>'
        theprevnext += '<a class="next-button toolbar-item button'
        if not nextfilename:
            theprevnext += " disabled"
        theprevnext += '" href="' + nextfilename + '">Next</a>'

        return theprevnext

    theprevnext = '<div class="toolbar-item">'
    if prevfilename:
        theprevnext += '<a href="'+prevfilename+'">'
        theprevnext += headerandcss.arrowleft()
        theprevnext += '</a>&nbsp;'     # should use  CSS way to make space
    if nextfilename:
        theprevnext += '<a href="'+nextfilename+'">'
        theprevnext += headerandcss.arrowright()
        theprevnext += '</a>'
    theprevnext += '</div>\n'   # .toolbar-item

    return theprevnext

#############

def mathjaxmacros(processby="html",htmlwrap=True):

    themacros = ""

    standardmacros = [
        r"\def\C{\mathbb C}",
        r"\def\R{\mathbb R}",
        r"\def\Z{\mathbb Z}",
        r"\def\Q{\mathbb Q}",
        r"\def\F{\mathbb F}",
        r"\def\smash{}",
        r"\def\phantomplus{}",
        r"\def\nobreak{}",
        r"\def\omit{}",
        r"\def\hidewidth{}"
    ]


    for macro in standardmacros:
            themacros += macro + "\n"

    if processby == 'html' and htmlwrap:      # make this into iterating over a list
        themacros = "\(\n" + themacros
        themacros = '<span style="display: none">' + themacros

                   # mathjax doesn't seem to know "ensuremath" and some other things
        themacros += "\\renewcommand{\mathnormal}{}\n"
        themacros += "\\renewcommand{\qedhere}{}\n"
        themacros += "\\renewcommand{\o}{\phi}\n"
        themacros += "\def\sp{^}\n"
        themacros += "\def\sb{_}\n"
        themacros += "\def\\vrule{|}\n"
        themacros += "\def\\hrule{}\n"
        themacros += "\def\dag{\dagger}\n"
        themacros += "\def\llbracket{[\![}\n"
        themacros += "\def\\rrbracket{]\!]}\n"
        themacros += "\def\llangle{\langle\!\langle}\n"  # from MnSymbols
        themacros += "\def\\rrangle{\\rangle\!\\rangle}\n"
        themacros += "\def\sssize{\scriptsize}\n"
        themacros += "\def\mathpalette{}\n"
        themacros += "\def\superimpose{}\n"   # from 1609:03838
                                              # \newcommand{\ttimes}{\hspace{0.4mm}{\mathpalette\superimpose{{\circ}
                                              # {\cdot}}}\hspace{0.4mm}}
        themacros += "\def\mathclap{}\n"
        themacros += "\def\coloneqq{\,:=\,}\n"   # from mathtools
        themacros += "\def\eqqcolon{\,=:\,}\n"
        themacros += "\def\colonequals{\,:=\,}\n"
        themacros += "\def\equalscolon{\,=:\,}\n"
        themacros += "\def\\textup{\mbox}\n"
        themacros += "\def\makebox{\mbox}\n"
        themacros += "\def\\vbox{\mbox}\n"
        themacros += "\def\\hbox{\mbox}\n"
        themacros += "\def\mathbbm{\mathbb}\n"
        themacros += "\def\\bm{\\boldsymbol}\n"
 #       themacros += "\def\quad{\\ }\n"
 #       themacros += "\def\qquad{\\ \\ }\n"
        themacros += "\def\/{}\n"
        themacros += "\def\\rq{'}\n"
        themacros += "\def\lq{`}\n"
 #       themacros += "\\def\\<{\\left\\langle}\n"
 #       themacros += "\\def\\>{\\right\\rangle}\n"
        themacros += "\def\\noalign{}\n"
        themacros += "\def\iddots{\\vdots}\n"
        themacros += "\def\\varint{\int}\n"
        themacros += "\def\\l{l}\n"

        themacros += "\def\\lefteqn{}\n"
        themacros += "\def\\adjustlimits{}\n"
        themacros += "\def\slash{/}\n"
 #       themacros += "\def\\boxslash{\\boxed{/}}\n"
        themacros += "\def\\boxslash{\\boxminus}\n"
        themacros += "\\def\\ensuremath{}\n"  # what could I have meant by that?
        themacros += "\def\hfil{}\n"
        themacros += "\def\hfill{}\n"
        themacros += "\def\pmod#1{~(\mathrm{mod}~#1)}\n"
        themacros += "\def\dasharrow{\dashrightarrow}\n"
        themacros += "\def\eqno{\hskip 50pt}\n"
        themacros += "\def\curly{\mathcal}\n"  # a few people used a complicated font directive to make \curly
        themacros += "\def\EuScript{\mathcal}\n"  
        themacros += "\def\widebar{\overline}\n"  # mathjax can't handle the usual construction
        themacros += "\\newcommand{\Eins}{\mathbb{1}}\n"  # from the mathbbol package
        themacros += "\\newcommand{\\textcolor}[2]{#2}\n"
        themacros += "\\newcommand{\\textsc}[1]{#1}\n"
        themacros += "\\newcommand{\\textmd}[1]{#1}\n"
        themacros += "\\newcommand{\\emph}{\\text}\n"
        themacros += "\\newcommand{\\uppercase}[1]{#1}\n"
   #     themacros += "\\newcommand{\Sha}{\mathbf{Sha}}\n"
        themacros += "\\newcommand{\Sha}{{III}}\n"
        themacros += "\\renewcommand{\setlength}[2]{}\n"
#        themacros += "\\newcommand{\\raisebox}[2]{#2}\n"
        themacros += "\\newcommand{\\scalebox}[2]{\\text{#2}}\n"
        themacros += "\\newcommand{\stepcounter}[1]{}\n"
        themacros += "\\newcommand{\\vspace}[1]{}\n"
        themacros += "\\newcommand{\displaybreak}[1]{}\n"
        themacros += "\\newcommand{\\textsl}[1]{#1}\n"
        themacros += "\\newcommand{\\cline}[1]{}\n"
        themacros += "\\newcommand{\\prescript}[3]{{}^{#1}_{#2}#3}\n"

        themacros += "\def\\llparenthesis{(\!\!|}\n"
        themacros += "\def\\rrparenthesis{|\!\!)}\n"
        themacros += "\def\\ae{a\!e}\n"
        themacros += "\def\\nolinebreak{}\n"
        themacros += "\\def\\allowbreak{}\n"
        themacros += "\def\\relax{}\n"
        themacros += "\def\\newline{}\n"
        themacros += "\def\\iffalse{}\n"
        themacros += "\def\\fi{}\n"
        themacros += "\def\\func{}\n"        # from tcilatex
        themacros += "\def\\limfunc{}\n"     # from tcilatex
        themacros += "\def\\roman{\mathrm}\n"
        themacros += "\def\mathbold{\mathbf}\n"
        themacros += "\def\mathscr{\mathit}\n"
        themacros += "\def\\bold{\mathbf}\n"
        themacros += "\def\dvtx{\,:\,}\n"
        themacros += "\def\widecheck{\check}\n"
        themacros += "\def\spcheck{^\\vee}\n"
        themacros += "\def\sphat{^{{}^\wedge}}\n"
        themacros += "\def\degree{{}^{\circ}}\n"
        themacros += "\def\\tr{tr}\n"
        themacros += "\def\defeq{\ :=\ }\n"

        themacros += "\\newcommand\\rule[3][]{}\n"   # ignore \rule[-2mm]{0mm}{6mm} , see 1112.5029

        themacros += "\\newcommand{\\up}[1]{\\textsuperscript{#1}}\n"
        themacros += "\\newcommand{\\textsuperscript}[1]{^{#1}}\n"
        themacros += "\\newcommand{\\fracwithdelims}[4]{\left#1\\frac{#3}{#4}\\right#2}\n"
        themacros += "\\newcommand{\\nicefrac}[2]{\left. #1\\right/#2}\n"
        themacros += "\\newcommand{\\sfrac}[2]{\left. #1\\right/#2}\n"
        themacros += "\\newcommand{\discretionary}[3]{#3}\n"
        themacros += "\\newcommand{\\xlongrightarrow}[1]{\\xrightarrow{\quad #1\quad}}\n"
        themacros += "\\def\\twoheadlongrightarrow{ \\quad \\longrightarrow \\!\\!\\!\\!\\to \\quad }\n"
        themacros += "\def\\xmapsto{\\xrightarrow}\n"

        themacros += "\def\hooklongrightarrow{\ \quad \hookrightarrow \quad \ }\n"
        themacros += "\def\longlonglongrightarrow{\ \quad \quad \quad \longrightarrow \quad \quad \quad \ }\n"
        themacros += "\def\\Longmapsto{ \\longmapsto }\n"
        themacros += "\def\\rto{ \longrightarrow }\n"
        themacros += "\def\\tto{ \longleftarrow }\n"
        themacros += "\def\\rcofib{ \hookrightarrow }\n"
        themacros += "\def\\L{\\unicode{x141}}\n"
        themacros += "\def\\niplus{\\ \\unicode{x2A2E}\\ }\n"
        themacros += "\def\\shuffle{\\ \\unicode{x29E2}\\ }\n"
        themacros += "\\def\\fint{{\\LARGE \\unicode{x2A0F}}}\n"
        themacros += "\\def\\XXint#1#2#3{\\vcenter{\\hbox{$#2#3$}}\\kern-0.4cm}\n"     # 1401.2061
        themacros += "\\newcommand{\\gls}[1]{#1}\n"
        themacros += "\\newcommand{\IEEEeqnarraymulticol}[3]{#3}\n"
        themacros += "\\require{cancel}\n"


    elif processby == 'ptx':
        themacros = '<macros>\n'




    if processby in ['html', 'ptx']:
        for defn in component.definitions:
            # should first check if the macro is actually useful to MathJax
            themacros += defn+"\n"

    elif processby == "latex":
        for defn in component.definitions_parsed:
            this_definition = component.definitions_parsed[defn]
      # make a funciotn that does the following, and incorporate it into extract_def
            texcommand = this_definition['texcommand']
            themacro = this_definition['themacro']
            numargs = this_definition['numargs']
            thedefinition = this_definition['thedefinition']
 ##           if texcommand == r"\let":
 ##               texcommand = r"\def"       # had trouble with \let in MathJax, probably because the source was wrong
            if texcommand == r"\providecommand":
                texcommand = r"\renewcommand"       # had trouble with \providecommand in MathJax, but don't know why

            if texcommand in [r"\def",r"\let"]:
                thefulldefinition = texcommand+themacro
            else:
                thefulldefinition = texcommand+"{"+themacro+"}"
            if numargs:
                thefulldefinition += "[" + str(numargs) + "]"
            thefulldefinition += "{"+thedefinition+"}"

            themacros += thefulldefinition+"\n"

    if processby == 'html' and htmlwrap:
        themacros += "\)\n"
        themacros += '</span>\n'
    elif processby == 'ptx':
        themacros += '</macros>\n'

    if processby == 'ptx' and component.writer == 'apex':
        return '\n<!-- <xi:include href="../macros.ptx" /> -->\n'

    return themacros

#############

def tocinhtml(toplevel,topsections):
    """Make the Table of Contents and put it in component.thetoc.

    Also assemble component.html_sections, which is used for ptx (maybe)

    There are two styles of TOC, depending on whether the 2nd level
    (section or subsection) is its own file or a part of a 1sr level
    page.  Currently this is determined by component.toplevel, but
    instead it should be be determined by component.tocstyle.  That
    way a long survey article could have a book-style TOC.

    """

    logging.info("making the TOC")

    if component.toplevel and ('abstract' in component.environment):
        component.thetoc += '<h2 class="link"><a href="index.html">Abstract</a></h2>\n'
        component.html_sections.append("index." + component.target)

    elif component.frontmatter:
        component.thetoc += '<h2 class="link"><a href="index.html">Front Matter</a></h2>\n'
        component.html_sections.append("index." + component.target)

    component.html_sections_type["index." + component.target] = "main"

    for thissection in topsections:
        thissectionsha1 = thissection[1]

        topsectionfilename = component.sectioncounters[toplevel]
        try:
            thecodenumber = component.environment[thissectionsha1]['codenumber']
        except KeyError:
            thecodenumber = "UNKNOWN"
        topsectionfilename += thecodenumber
        scrolllink = topsectionfilename
        topsectionfilename += '.' + component.target # ".html"

        comp = component.environment[thissectionsha1]

        # make this general once the prev/next filenames are fixed
        if component.target == 'ptx':
            try:
                topsectionfilename = comp['latex_label'] + '.' + component.target
            except KeyError:
                  # keep the number-based file name
                logging.info("%s with no latex_label", comp['marker'])

        component.environment[thissectionsha1]['filename'] = topsectionfilename

        if comp['title']:  # how could a section not have a title??
   # to do: answer the above question and then get rid of the if
            component.thetoc += '<h2 class="link"><a href="'+topsectionfilename+'" data-scroll="' + scrolllink +'">'
            component.html_sections.append(topsectionfilename)
            component.html_sections_type[topsectionfilename] = "top"

            if thecodenumber and "*" not in thecodenumber and not thecodenumber.endswith("x"):
                component.thetoc += '<span class="codenumber">' + thecodenumber + "." + '</span>'
            if comp['title'] == "XXXX":
                component.thetoc += '<span class="title">' + 'The paper' + '</span>'
            else:
                thistitle = ref_to_knowl(comp['title'],link=False)
                thistitle = cite_to_knowl(thistitle,link=False)
                thistitle = utilities.tex_to_html(thistitle)
                component.thetoc += '<span class="title">' + thistitle + '</span>'
            component.thetoc += '</a></h2>\n'
            thesectiontext = comp['component_separated']

            thesubsections = re.findall("SEC([0-9a-f]{40})END",thesectiontext) # the, not this
            if len(thesubsections) > 0:
                component.thetoc += '<ul>\n'
            for section_sha1 in thesubsections:
                comp = component.environment[section_sha1]
                try:
                    thecodenumber = comp['codenumber']
                except KeyError:
                    thecodenumber = "00000.111111"
                    logging.warning("no code number for %s", section_sha1)

                marker = comp['marker']
                thisenvironmenttype = component.environment_types[marker]
                if (marker == component.sectioncounters[toplevel+1] and
                    comp['title'] != ""):  

                   # slightly confusing that sections of books get their own file,
                   # but subsections of papers don't
                    thecodenumber_dash = re.sub("\.","-",thecodenumber)
                    if toplevel == 0:   # should use tocstyle
                        thefilestub = marker+thecodenumber_dash
                        thefilename = thefilestub + '.' + component.target #'.html'

                        # remove this if once prev/next is fixed
                        if component.target == 'ptx':
                            try:
                                thefilename = comp['latex_label'] + '.' + component.target
                            except KeyError:
                                  # keep the number-based file name
                                logging.info("%s with no latex_label", comp['marker'])

                        component.thetoc += '<li><a href="'+thefilename+'" '
                        component.thetoc += 'data-scroll="'+thefilestub+'" '
                        component.thetoc += '>'
                        thistitle = ref_to_knowl(comp['title'],link=False)
                        thistitle = cite_to_knowl(thistitle,link=False)
                        thistitle = utilities.tex_to_html(thistitle)
                        component.thetoc += thistitle + '</a></li>\n'
                        component.html_sections.append(thefilename)
                        component.html_sections_type[thefilename] = 'section'
                        component.environment[section_sha1]['filename'] = thefilename

                    else:
                        try:
                            parentsection = re.match("(.*)(\.[0-9]+)",thecodenumber).group(1)
                        except AttributeError:
                            logging.error("failed to find parent of %s",thecodenumber)
                            parentsection = "XXXX"
                        component.thetoc += '<li><a href="section'+parentsection+'.html'
                        component.thetoc += '#'+marker+thecodenumber_dash+'" '
                        component.thetoc += 'data-scroll="'+marker+thecodenumber_dash+'" '
                        component.thetoc += '>'
                        thistitle = ref_to_knowl(comp['title'],link=False)
                        thistitle = cite_to_knowl(thistitle,link=False)
                        thistitle = utilities.tex_to_html(thistitle)
                        thistitle = re.sub(r"vvi","ddd",thistitle)
                        component.thetoc += thistitle + '</a></li>\n'
           #   may need to rejuvenate the following code for a deeper TOC
           #     else:  # it is a deep enough to not be its own file
           #         parentsection = re.match("(.*)(\.[0-9]+)",thecodenumber).group(1)
           #         component.thetoc += '<li><a href="section'+parentsection+'.html#subsection'+thecodenumber+'">'
           #         component.thetoc += utilities.tex_to_html(ref_to_knowl(comp['title'],link=False))+'</a></li>\n'
            if len(thesubsections) > 0:
                component.thetoc += '</ul>\n'

        elif comp['marker'] == 'blob' and 'sec0' in comp:
            logging.debug("found a sec0, which should not have a title")

        else:
            logging.error("section %s has no title", comp)

    if component.bibliography:
        component.thetoc += '<h2 class="link"><a href="bibliography.html">Bibliography</a></h2>\n'
        component.html_sections.append("bibliography." + component.target)
        component.html_sections_type["bibliography." + component.target] = 'biblio'

    if component.index and component.target == 'html':
        component.thetoc += '<h2 class="link"><a href="theindex.html">Index</a></h2>\n'
        component.html_sections.append("theindex.html")

    component.thetoc = re.sub(r"\\vvideohref\{[^{}]*\}","",component.thetoc)

############

def makeknowl(id,content):

   if not content:
       logging.warning("knowl with no content: %s", id)
   else:  # rewrite using "with"
       the_content = content
       logging.debug("making knowl %s which starts %s", id, content[:30])
       knowlfilename=utilities.safe_name(id, idname=True)+".knowl"
       thefile = codecs.open(component.outputdirectory+"/"+knowlfilename,"w", "utf-8")
#       try:
#           the_content = the_content.decode('utf-8', errors='replace')
#       except UnicodeEncodeError:
#           logging.warning("FONT ERROR in knowl %s : %s", knowlfilename, the_content[:30])
#       except AttributeError:
#           print("Error with utf-8 decode")

       thefile.write(the_content)
       thefile.close()

####################

def process_argv(sys_argv):

    component.inputfilename = sys_argv[1]
    component.outputdirectory = sys_argv[2]

    logging.info("\n\n\n\n\n\n")
    logging.info("converting the FILE %s to something in the directory %s",
                  component.inputfilename, component.outputdirectory)
    logging.info("\n\n\n\n\n\n")

    # options are in sys.argv[3:] because prog inputfile outputdirectory are in [:3]
    opts, args = getopt.getopt(sys_argv[3:],"vkfa:p:w:o:t:",
                                ["verbose","knowlifyproofs",
                                 "frontmatter","arx=","publisher=","writer=","output=","target="])

    logging.debug("opts: %s", opts)
    logging.debug("args: %s", args)

    component.known_paper_code = ""
    component.publisher = "AIM"
    component.writer = ""
    component.verbose = False

    component.frontmatter = False

    for opt, arg in opts:
        logging.debug("opt: %s, arg: %s", opt, arg)
        if opt in ('-a', '--arx'):
            component.known_paper_code = arg
        elif opt in ('-p', '--publisher'):
            component.publisher = arg
        elif opt in ('-w', '--writer'):
            component.writer = arg
        elif opt in ('-t', '--target'):
            component.target = arg
        elif opt in ('-v', '--verbose'):
            component.verbose = True
        elif opt in ('-k', '--knowlifyproofs'):
            component.knowlify_proofs = True
        elif opt in ('-f', '--frontmatter'):
            component.frontmatter = True

    if component.target == "unknown":
        component.target = "html"

    component.originalinputfilename = component.inputfilename

####################

def setup_input_files():

    component.inputdirectory = re.sub("[^/]*$","",component.inputfilename)

    if os.path.exists(component.inputfilename):
     #   component.inputfile = open(component.inputfilename,'r')
        component.inputfile = codecs.open(component.inputfilename,'r', 'utf-8')
        component.known_files.append(component.inputfilename)
    else:
        logging.critical("input file %s does not exist",
                       component.inputfilename)
        sys.exit()

####################

def setup_output_files():

    component.imagesdirectory = component.outputdirectory + "/../assets"

    if os.path.exists(component.outputdirectory):
        logging.info("re-using the existing directory, %s, files in it will be over-written",
                      component.outputdirectory)
    else:
        os.mkdir(component.outputdirectory)

    if os.path.exists(component.imagesdirectory):
        logging.info("re-using the existing directory, %s, files in it will be over-written",
                      component.imagesdirectory)
    else:
        os.mkdir(component.imagesdirectory)

    thestyle = random.randint(0,6)  # 7 possible styles, chosen randomly
    component.style_number = str(thestyle)   # randomly generate a style

    if "html" in component.target:
        if headerandcss.add_on_css():
            cssfilename = component.outputdirectory + "/add-on.css"
            cssfile = open(cssfilename,'w')
            cssfile.write(headerandcss.add_on_css())
            cssfile.write(" ")
            cssfile.close()

        if headerandcss.add_on_js():
            jsfilename = component.outputdirectory + "/add-on.js"
            jsfile = open(jsfilename,'w')
            jsfile.write(headerandcss.add_on_js())
            jsfile.close()

##################

def tables_to_html():

    logging.info("initial substitutions of LaTeX tables")
    for sha1key in list(component.environment.keys()):
        # array is handled in math mode?
        if component.environment[sha1key]['marker'] in ['tabu','tabular','tabularx']:
            thetext = component.environment[sha1key][component.target]
            thetext = utilities.latex_array_to_html(thetext)
            component.environment[sha1key][component.target] = thetext

#####################

def cite_and_ref_to_html():

    logging.info("initial substitutions of LaTeX ref and cite")
    for sha1key in list(component.environment.keys()):
        thetext = component.environment[sha1key][component.target]
        if ((component.environment[sha1key]['marker'] in component.environments_with_linebreaks) or
            (component.environment[sha1key]['marker'] in component.math_environments) or
            (component.environment[sha1key]['marker'] in ['macro'])):
            thetext = ref_to_knowl(thetext, link=False)
            thetext = cite_to_knowl(thetext, link=False)
        else:
            thetext = ref_to_knowl(thetext)
            thetext = cite_to_knowl(thetext)

        component.environment[sha1key][component.target] = thetext

#  The following is a bad hack because it changes sqgroup in place.
#  Need a better way to handle cites and refs in the [sqgroup]
        if 'sqgroup' not in component.environment[sha1key]:
            continue

        thetext = component.environment[sha1key]['sqgroup']
        thetext = ref_to_knowl(thetext)
        thetext = cite_to_knowl(thetext)

        component.environment[sha1key]['sqgroup'] = thetext

     # fix: may still need to convert ref and cite in captions

####################

def make_knowls_from_labels():
    """For everything with a label, make a knowl file.

    """

    if component.target == 'ptx':
        logging.info("no reason to make knowls for ptx output")
        return ""

    logging.info("make a knowl for each label")
    for label in component.label:

        # at some point we should switch to saving referenced objects,
        # not all objects with a label

        logging.debug("label is %s", label)
        sha1key = component.label[label]['sha1']
        comp = component.environment[sha1key]
        if comp['marker'] in ['chapter','section','subsection']:
            continue
            # chapters and sections are referenced by links, not knowls
        try:
            thetext = comp[component.target]
        except KeyError:
            logging.error("component with no html version %s", sha1key)
            thetext = comp['component_separated']
        tagsandhead = tagsandheading(sha1key)
        thetext = tagsandhead[0] + utilities.tex_to_html(tagsandhead[1]) + thetext + tagsandhead[2]
        if comp['marker'] in component.sub_environments:
            try:
                this_parent = comp['parent']
                this_parent_comp = component.environment[this_parent]
                this_parent_tagsandhead = tagsandheading(this_parent)
                logging.debug("successfully wrapped parent of %s", thetext)
                thetext = this_parent_tagsandhead[0] + utilities.tex_to_html(this_parent_tagsandhead[1]) + this_parent_comp[component.target] + this_parent_tagsandhead[2]
            except KeyError:
                logging.warning("no parent for %s", comp)
        makeknowl(sha1key,thetext)

###################
# knowlify proof, if we want proofs to be knowlified by default.
# this function repeats a much of make_knowls_from_labels

def make_other_knowls():

    if component.target != 'html':
        logging.info('not making other knowls')
        return ""

    if component.knowlify_proofs or not component.hide_hints:
      logging.info("knowlifying some proofs (and maybe other things, too).")
      for sha1key in list(component.environment.keys()):
        if component.environment[sha1key]['marker'] in ['proof', 'solution', 'hint']:
            # need to make the start of this loop less stupid
            if component.environment[sha1key]['marker'] == 'hint' and component.hide_hints:
                continue
            if component.environment[sha1key]['marker'] != 'hint' and not component.knowlify_proofs:
                continue
            comp = component.environment[sha1key]
            try:
                thetext = comp[component.target]
            except KeyError:
                logging.error("component with no html version %s",sha1key)
                thetext = comp['component_separated']
            tagsandhead = tagsandheading(sha1key)
            thetext = tagsandhead[0] + utilities.tex_to_html(tagsandhead[1]) + thetext + tagsandhead[2]
            makeknowl(sha1key,thetext)
            logging.debug("knowlified the %s %s", component.environment[sha1key]['marker'], sha1key)

    index_and_terminology = component.index + component.terminology
    for entry in index_and_terminology:

        this_item = entry['entry']
        logging.debug('making an index/terminology knowl for %s', entry)

        if 'context_parent' in entry:
            this_parent = entry['context_parent']
        else:
            this_parent = entry['parent']
        parent_ID = component.environment[this_parent]['sl2xID']

        section_type = "section"
        containing_section_sha1 = processenvironments.section_containing(this_parent,section_type=section_type)
        containing_section = component.environment[containing_section_sha1]
        containing_section_number = containing_section['codenumber']
        containing_section_number_dash = re.sub("\.","-",containing_section_number)
        in_context_link = '<span class="incontext">'
        in_context_link += '<a href="'
        in_context_link += section_type + containing_section_number_dash + '.html'
        in_context_link += '#' + parent_ID
        in_context_link += '">'
        in_context_link += "in context"
        in_context_link += '</a>'
        in_context_link += '</span>'
         
# partially copied from make_knowls_from_labels
        comp = component.environment[this_parent]
        tagsandhead = tagsandheading(this_parent)
        thetext = comp[component.target]

        the_knowl_text = tagsandhead[0] + utilities.tex_to_html(tagsandhead[1]) 
        the_knowl_text += thetext 
        the_knowl_text += tagsandhead[2] + in_context_link
        makeknowl(this_parent,the_knowl_text)

###################

def expand_sha1_codes(text, markup="html"):
    """Experimental new approach to expanding sha1 codes.

    """

    logging.debug("expand_sha1_codes")
    expansionfunction = expandhtml
    if markup == "latex":
        expansionfunction = expandlatex
        logging.debug("expanding to latex")

    thetext = text

    utilities.something_changed = 1

    while utilities.something_changed:
        utilities.something_changed = 0
        thetext = re.sub("("+component.sha1heads_all+")([0-9a-f]{40})END",
                                      expansionfunction,thetext,1)

    logging.debug("in expand_sha1_codes, end: %s",thetext[:100])

    return thetext

###################

# The main loop when all the environments are expanded into their
# HTML versions.  This loop should be replaced by several loops because it
# is better to expand certain environments first.  Examples are the content
# of an internal knowl, or the images in a figure (images should know their
# "parent" figure environment, and need to be told what size to be.)

def expand_to_html(excludedmarkers=[]):

    logging.info("expanding to html, excludedmarkers: %s", excludedmarkers)

    for depth in range(1,1999):  # could we have more that 2000 levels of nested environments?
                                 # note: not really levels, because sometimes we only expand one sha1 code per iteration
        utilities.something_changed = 0
        for sha1key in list(component.environment.keys()):
            if ((component.environment[sha1key]['marker'] != 'chapter' or
                   (component.environment[sha1key]['marker'] == 'chapter' and
                   'SEC' not in component.environment[sha1key][component.target]))
               and component.environment[sha1key]['marker'] not in excludedmarkers):
              # in other words: don't expand sections on the opening page of
              # a chapter, and don't expand excluded environments

                thetext_html = component.environment[sha1key][component.target]
                thetext_html = re.sub("("+component.sha1heads_all+")([0-9a-f]{40})END",
                                      expandhtml,thetext_html,1)
                component.environment[sha1key][component.target] = thetext_html

            try:
                if component.environment[sha1key]['sec0'] == 'section':
#   twice?                 component.preface_sec0 = thetext_html
                    component.preface_sec0 = thetext_html
            except KeyError:
                pass
        if not utilities.something_changed:
            break
        else:
            logging.info("%s environments expanded", utilities.something_changed)

    logging.info("expanded to a depth of %s", depth)

##################

def chapterpages():

    # The chapter pages have section 0 at the top, and links to the sections
    # Here we put in the section 0, if there is one
    logging.info("make the chapter pages, if there are chapters")
    for sha1key in list(component.environment.keys()):
        if component.environment[sha1key]['marker'] == 'chapter':
            thetext_html = component.environment[sha1key][component.target]
            thetext_html = re.sub("(SEC)([0-9a-f]{40})END",
                                   lambda match: expandhtml(match, sec0only=True),
                                   thetext_html,1)
            component.environment[sha1key][component.target] = thetext_html

#################

def section_links_on_chapterpages():

    logging.info("chapter pages, part 2: section links")
    for sha1key in list(component.environment.keys()):
        if component.environment[sha1key]['marker'] == 'chapter':
            thetext_html = component.environment[sha1key][component.target]
            thetext_html = re.sub("(SEC)([0-9a-f]{40})END",
                                   sectionlink,thetext_html)
      #  a hack: need a general way to handle \vvideohref
            for _ in range(10):
                thetext_html = vvideotolink(thetext_html)
            component.environment[sha1key][component.target] = thetext_html

#################

def chapter_section_files():
    """Make separate files for each chapter and section."""

    logging.info("write the chapter and section files")
    for sha1key in list(component.environment.keys()):
        if component.environment[sha1key]['marker'] in ['chapter','section']:
            thiscomponent = component.environment[sha1key]
            try:
                thecodenumber = thiscomponent['codenumber']
            except KeyError:
                logging.error("component with no codenumber: %s", thiscomponent)
                thecodenumber = "UNKNOWN"
            thecodenumber_dash = re.sub("\.","-",thecodenumber)
            filename = thiscomponent['marker']
            filename += thecodenumber_dash
            filename += '.' + component.target # ".html"

            if component.target == 'ptx':
                try:
                    filename = component.environment[sha1key]['filename']
                    logging.info("switched to the filename %s", filename)
                except KeyError:
                    # no latex_label based fiel name, so use the codenumber version
                    pass

            logging.info("writing the file %s", filename)
         # move this to a function
            try:
                fileindex = component.html_sections.index(filename)
                if fileindex < len(component.html_sections)-1:
                    nextfilename = component.html_sections[fileindex+1]
                else:
                   nextfilename = ""
            except ValueError:
                nextfilename = ""


            filestub = filename
            filename = component.outputdirectory+"/"+filename

            # should use 'with'
            thefile = codecs.open(filename,'w', 'utf-8')

            if component.target == 'html':
                thefile.write(pageheader(filestub))

            if component.target == 'html':
                thefile.write('<div class="page">\n')
                thefile.write(pagetoc(filestub))
                thefile.write('<main class="main">\n')
                thefile.write('<div id="content" class="pretext-content">\n')

            this_page = expandhtml(sha1key)  # needed for page title

            this_page = postprocess.fix_various_tags(this_page)

            if component.target == 'ptx':
                this_page = postprocess.ptx_change_figure_wrapping(this_page)
                this_page = postprocess.ptx_fix_various_tags(this_page)
                this_page = postprocess.ptx_fix_answer(this_page)
                this_page = postprocess.ptx_fix_hint(this_page)
                this_page = postprocess.ptx_put_hints_in_activities(this_page)
                this_page = postprocess.ptx_minipage_sidebyside(this_page)
                this_page = postprocess.ptx_paired_lists(this_page)
                this_page = postprocess.ptx_wrap_statements(this_page)
                this_page = postprocess.ptx_wrap_CDATA(this_page)
                this_page = postprocess.ptx_change_math_markup(this_page)
                this_page = postprocess.ptx_fix_p_and_br_in_li(this_page)
                this_page = postprocess.titles_outside_paragraphs(this_page)
                this_page = postprocess.put_math_in_paragraphs(this_page)
                this_page = postprocess.put_lists_in_paragraphs(this_page)
                this_page = postprocess.ptx_revert_tikzpicture(this_page)
                this_page = postprocess.ptx_final_hacks(this_page)
                this_page = postprocess.ptx_normalize_whitespace(this_page)
     #           this_page = preprocess.apexincludegraphics(this_page)
                this_page = postprocess.ptx_unwrap_p_images(this_page)
                this_page = postprocess.ptx_unwrap_sidebyside(this_page)
                this_page = postprocess.ptx_remove_empty_tags(this_page)
                this_page = postprocess.ptx_fix_particular_author(this_page)
       # need a flag for when to do this
     #           this_page = postprocess.apex_exercise_group(this_page)

# no longer needed for python3?
#            try:
#                this_page = this_page.decode('utf-8', errors='replace')
#            except UnicodeEncodeError:
#                logging.warning("FONT ERROR in this_page %s : %s", filename, this_page[:40])
#            except AttributeError:
#                print("Error with utf-8 decode")

            thefile.write(this_page)

            if component.target == 'html':
                thefile.write('</div>')  # id=content
                thefile.write('</main>')
                thefile.write('</div>')
                thefile.write('</body>')
                thefile.write('</html>')
            elif component.target == 'ptx':
                pass  # because these are only in the main file
                # thefile.write("\n" + '</article>' + "\n")
                # thefile.write("\n" + '</pretext>' + "\n")

            thefile.close()

#################

def bibliography():

    logging.info("making the bibliography")
    bibliofilename = component.outputdirectory+"/"+"bibliography." + component.target # html"

    bibliofile = codecs.open(bibliofilename,'w', 'utf-8')

    if component.target == 'html':
        bibliofile.write(pageheader("bibliography.html"))

    if component.target == 'html':
        bibliofile.write('<div class="page">')
        bibliofile.write(pagetoc("bibliography.html"))
        bibliofile.write('<main class="main">\n')
        bibliofile.write('<div id="content" class="pretext-content">')
        bibliofile.write('<section class="section" id="section1*"><h2 class="heading hide-type"><span class="type">Section</span>')
        bibliofile.write('<span class="title">Bibliography</span></h2>')
    elif component.target == 'ptx':
        bibliofile.write('\n<references>\n')
        bibliofile.write('\n<title>Bibliography</title>\n')

    if component.target == 'html':
        component.bibliography_in_html = re.sub("("+"verb"+")([0-9a-f]{40})END",
                                      expandhtml,component.bibliography_in_html)
        bibliofile.write(component.bibliography_in_html)
    elif component.target == 'ptx':
        for bibitem in component.bibliography_entries:
            key = bibitem['thelabel']
            the_entry = bibitem['component_raw']
            bibliofile.write('\n<biblio type="raw" xml:id="' + key + '">')
            the_entry = re.sub(r"(\\)*&\s*", "&amp; ",the_entry)
            bibliofile.write(the_entry)
            bibliofile.write('</biblio>')

    if component.target == 'html':
        bibliofile.write('</section>' + "\n")
        bibliofile.write('</div></main></div>' + "\n")
        bibliofile.write('</html>' + "\n")
    elif component.target == 'ptx':
        bibliofile.write("\n" + '</references>' + "\n")

    bibliofile.close()

    logging.info("done making the bibliography")

#################

def top_level_page():

    logging.info("making the top level page")
    if component.target == 'html':
        mainoutputfilename = component.outputdirectory + "/index.html"
    elif component.target == 'ptx':
        mainoutputfilename = component.outputdirectory + "/main.ptx"
    mainoutputfile = codecs.open(mainoutputfilename,'w', 'utf-8')

    if component.target == 'html':
        mainoutputfile.write(pageheader("index.html"))

        mainoutputfile.write('<div class="page">')
        mainoutputfile.write(pagetoc("index.html"))
        mainoutputfile.write('<main class="main">\n')

        mainoutputfile.write('<div id="content" class="pretext-content">')

    # need to clean this up
    elif component.target == 'ptx':

        theheader = headerandcss.header()

        try:
            theheader += mathjaxmacros(processby=component.target)
        except UnicodeDecodeError:
            logging.error("mathjaxmacros problem: %s", mathjaxmacros())
            macros_in_ascii = str(mathjaxmacros(), errors="ignore")
            theheader += macros_in_ascii

        if component.writer == 'apex':
            theheader += '\n<!-- \n'
            theheader += '\n<xi:include href="../latex-image-preamble.ptx" />\n'
            theheader += '\n--> \n'
        else:
            theheader += "\n" + "<latex-image-preamble>" + "\n"
            for line in mapping.latexheader_tikz:
                theheader += line + "\n"
            theheader += "\n"
            theheader += r'\usepackage{pgfplots}' + "\n"
            theheader += "\n" + "</latex-image-preamble>" + "\n"

        if component.publisher == "aimpl":
            theheader += '<rename element="openproblem">Problem</rename>' + '\n'
            theheader += '<rename element="openquestion">Question</rename>' + '\n'
            theheader += '<rename element="openconjecture">Conjecture</rename>' + '\n'

        if component.writer == 'apex':
            theheader += '\n<rename element="insight" lang="en-US">Key Idea</rename>\n'
        elif component.writer == 'active':
            theheader += '\n<rename element="exploration" lang="en-US">Preview Activity</rename>\n'
        elif component.writer == 'schmitt':
            theheader += '\n<rename element="exploration" lang="en-US">Challenge</rename>\n'
        elif component.writer == 'rosulek':
            theheader += '\n<rename element="exploration" lang="en-US">Construction</rename>\n'
        theheader += "\n" + "</docinfo>" + "\n\n"

        thetitle = "    " + '<title>'
        thetitle += utilities.remove_silly_brackets(component.title)
        thetitle += "    " + '</title>'

        theauthors = ""
        for author in component.authorlist:
            theauthors += "<author>" + "\n"
            theauthors += "<personname>"
            theauthors += author
            theauthors += "</personname>" + "\n"
            theauthors += "</author>" + "\n"

        if component.toplevel == 0:
            theheader += "\n" + '<book>' + "\n"
        else:
            theheader += "\n" + '<article>' + "\n"
        theheader += thetitle
        theheader += "\n" + '<frontmatter>' + "\n"
        theheader += '<titlepage>' + "\n"
        theheader += theauthors
        theheader += '</titlepage>' + "\n"
          # abstract should go here

    try:
        component.environment['abstract'][component.target] = component.environment['abstract'][component.target].strip()
    except KeyError:
        component.environment['abstract'] = {'marker':"abstract",   # every environment needs a marker
                                             component.target:""}

    if component.environment['abstract'][component.target]:
        if component.target == 'html':
            mainoutputfile.write('\n<article class="abstract"><h5 class="heading">Abstract</h5>'+
                              component.environment['abstract'][component.target] + '</article>\n')
        elif component.target == 'ptx':
            theheader += "\n" + '<abstract>' + "\n"
            theheader += component.environment['abstract'][component.target]
            theheader += "\n" + '</abstract>' + "\n"

    component.preface_sec0 = component.preface_sec0.strip()

    if component.target == 'html':
        if 'frontmatter' in component.environment:
            mainoutputfile.write('\n<article class="preface"><h5 class="heading">Preface</h5>')
            mainoutputfile.write(component.environment['frontmatter'][component.target])
            mainoutputfile.write('</article>\n')

        elif component.preface_sec0:
            mainoutputfile.write('\n<article class="preface"><h5 class="heading">Preface</h5>'+component.preface_sec0+'</article>\n')

    # disabled because the preface was coming before the usual header in main.ptx
    elif component.target == 'ptx':
        if 'frontmatter' in component.environment:
            logging.error("need to implement frontmatter/preface in PTX")
    
        elif component.preface_sec0:
            logging.error("need to implement preface in PTX")

    if component.target == 'html':
        mainoutputfile.write('</div>\n')  # id=content

        mainoutputfile.write('</main>\n')
        mainoutputfile.write('</div>\n')
        mainoutputfile.write('</body>\n')
        mainoutputfile.write('</html>\n')

    if component.target == 'ptx':
        theheader += '</frontmatter>' + "\n" + "\n"
        # the main PTX file is not finished: we need to include all the section files

    if component.target == 'ptx':
        mainoutputfile.write(theheader)

    mainoutputfile.close()

    # Make the titleauthor.txt page, which provides a link to the document.

    compilationfilename = component.outputdirectory + "/titleauthor.txt"
    compilationfile = codecs.open(compilationfilename,'w', 'utf-8')
    compilationfile.write('\n\n<div class="title"><a href="'+component.outputdirectory+'">')
    compilationfile.write(component.title)
    compilationfile.write('</a></div>\n')
    compilationfile.write('\n\n<div class="author">by '+component.author_html+'</div>\n\n')
    compilationfile.close()

    # hack for top level file when there is no abstract
    if component.target == 'html':
        if not (component.environment['abstract'][component.target]
                or ('frontmatter' in component.environment and
                     component.environment['frontmatter'][component.target])):
            logging.warning("moving preliminary section to index.html")
            toptype = component.sectioncounters[component.toplevel]
            indexfilename = component.outputdirectory+"/"+"index.html"

            sec0filename = component.outputdirectory+"/"+toptype+"x1.html"
            if not os.path.exists(sec0filename):
                sec0filename = component.outputdirectory+"/"+toptype+"1x.html"
            if not os.path.exists(sec0filename):
                sec0filename = component.outputdirectory+"/"+toptype+"1.html"
            cpcommand = "cp "+sec0filename + " " + indexfilename
            logging.debug("trying to copy file: %s", cpcommand)
            os.system(cpcommand)
            logging.debug("sec0filename: %s", sec0filename)

#################

def make_terminology_links():

    if component.target != 'html':
        logging.info('skipping terminology links')
        return ""

    logging.info("making terminology links")
    reserved_words = ['lemma','proposition','theorem']
    # we once had span, div, and article reserved,
    # but the "space before" match seems to take care of that

    math_terminology = False
    for entry_number, entry in enumerate(component.terminology):
        this_item = entry['entry']
        this_parent = entry['parent']
        if len(this_item) < 4:
            continue    # skip very short words
           # it might be better to solve the underlying problem.  From 1208.1077 :
           # \begin{defn} ... $$(u,\phi_0\circ st): (F,j,{\bf x}) ...
           # the \bf x is interpreted as bold x, which in a definition means x is being defined
        try:
            knowl_parent = entry['context_parent']
        except KeyError:
            knowl_parent = entry['parent']
        knowl_parent_stub = utilities.safe_name(knowl_parent, idname=True)

        parent_environment = component.environment[this_parent]
        parent_marker = parent_environment['marker']
        if parent_marker not in component.environment_types:
            logging.critical("unknown parent_marker %s in %s", parent_marker, knowl_parent_stub)
                # this happened once, with terminology in a caption
            continue
        if component.environment_types[parent_marker]['class'].startswith('math'):
            logging.debug("found math terminology: %s", parent_environment)
            math_terminology = True
            # the terminology could be \Z^+
            search_string_start = re.sub(r"\\",r"\\\\",this_item)
            search_string_start = re.sub(r"([+^()])",r"\\\1",search_string_start)
            search_string_start = r"(^|[^{])" + search_string_start
            search_string_plural = r"(())"
            search_string_punctuation = r"(\b|$)"
            replace_string = r"\1\\stealthknowl{" + knowl_parent_stub + ".knowl" + "}"
            # \varphi
            this_item_modified = re.sub(r"(\\s|\\t|\\v|\\n)",r"\\\1",this_item)
            replace_string += "{" + this_item_modified + "}"

        else:
            logging.debug("non-math terminology: %s", parent_environment)


            if "$" in this_item[2:-2] or r"\(" in this_item[2:-2]:
                logging.debug("skipping this_item %s", this_item)
                continue  # later we think about embedded math formulas

            if (len(this_item) < 3 or this_item in reserved_words or
                not this_item.replace(" ","").replace("-","").isalpha()):
                logging.debug("skipping terminology: %s", this_item)
                continue

        # Since nested a tags are not allowed in html, we need to prevent
        # "normal subgroup" to later have "subgroup" replaced.
        # A space is needed before a substituted term, so we fill in the space.
            this_item_nospace = this_item.replace(" ","&nbsp;")

            search_string_start = re.sub(r"\\",r"\\\\",this_item)
            search_string_start = re.sub(r"\(",r"\\(",search_string_start)
            search_string_start = re.sub(r"\)",r"\\)",search_string_start)
# had to change the next line for p3
            search_string_start = r"\s" + re.sub(r"\s+",r"\\s+",search_string_start)
            search_string_plural = r"((s?))"
            search_string_punctuation = r"(\s|[,:;.?!]|$)"

            # class/classes
            if this_item.endswith("ss"):
                search_string_plural = r"((es)?)"
            # symmetry/symmetries
            elif  this_item.endswith("y") and this_item[-2] not in "aeiou":
                this_item_nospace = this_item_nospace[:-1]
                search_string_start = r"\s" + re.sub(r"\s+",r"\\s+",this_item[:-1])
                search_string_plural = r"((y|ies))"

            replace_string = " " + '<span class="autoterm">'
            replace_string += '<a knowl="' + knowl_parent_stub + '.knowl">'
            replace_string += this_item_nospace + r"\1" 
            replace_string += '</a>' + r"\3"
            replace_string += '</span>' + " "

        search_string = search_string_start + search_string_plural + search_string_punctuation

        logging.debug("terminology search_string %s", search_string)
        logging.debug("terminology replace_string %s", replace_string)
# still need to determine how to have "group" match "Groups"
# (easier to handle that for one-word terms.

        for sha1key in list(component.environment.keys()):
            if not math_terminology and component.environment[sha1key]['marker'] not in ['text', 'item']:
                continue

            # need to rethink the cases when terminology only appears once.
            # do we want backward links in that case?
            # Yes, so we are temporarily making links in all cases
            if False and closest_codenumber_ordinal(this_parent) > closest_codenumber_ordinal(sha1key): 
                continue     # only make terminology links after the terminology was introduced

# need an 'else' here

            thetext = component.environment[sha1key][component.target]
            thetext = re.sub(search_string, replace_string, thetext,)
            component.environment[sha1key][component.target] = thetext
            
#################

def indexpage():
    """ Make the index: theindex.html """
    
    if component.target != "html":
        logging.info("skipping the index")
        return ""

    if not component.index:
        logging.info("no index")
        return ""

    logging.info("making the index: theindex.html")
    # entries involving math have to be expanded so that alphabetizing
    # puts them in the correct order
    for entry_number, entry in enumerate(component.index):
        this_item = entry['entry']
        for _ in range(5):  # instead shoudl be until things stop changing
            this_item = re.sub("("+component.sha1heads_all+")([0-9a-f]{40})END",
                                      expandhtml,this_item,1)
        component.index[entry_number]['entry'] = this_item

    component.index = sorted(component.index, key=lambda k: k['entry'].upper()) 

    indexfilename = component.outputdirectory+"/"+"theindex.html"
    indexfile = codecs.open(indexfilename,'w', 'utf-8')
    indexfile.write(pageheader("theindex.html"))




    indexfile.write('<div class="page">')
    indexfile.write(pagetoc("theindex.html"))
    indexfile.write('<main class="main">\n')
    indexfile.write('<div id="content" class="pretext-content">')
    indexfile.write('<section class="section" id="section1*"><h2 class="heading hide-type"><span class="type">Section</span>')
    indexfile.write('<span class="title">Index</span></h2>')

    first_entry = component.index[0]
    this_item = first_entry['entry']
    try:
        current_letter = this_item[0].lower()
    except IndexError:
        logging.critical("empty first entry in component.index")
        current_letter = "*"

    current_heading = ""
    current_item = ""
    current_entry = ""
    new_letter = False

    indexfile.write('<div class="indexletter">')

    depth = 0

    for entry_number, entry in enumerate(component.index):
        if entry == current_entry:
            continue
        else:
            current_entry = entry

        this_item = entry['entry']
        if not this_item:
            logging.critical("empty entry %s in component.index", entry_number)
            continue
        this_parent = entry['parent']
        this_knowl_target = this_parent
        this_knowl_target_stub = utilities.safe_name(this_knowl_target, idname=True)
        this_environment = component.environment[this_parent]

 #       if this_item[0].upper() != current_letter:
        if this_item[0].lower() != current_letter:
   #         current_letter = this_item[0].upper()
            current_letter = this_item[0].lower()
            indexfile.write('\n</div>')  # close the entry at the bottom of the last letter
            indexfile.write('\n</div>\n')  # close off the last letter
#            indexfile.write('\n<div id="index' + current_letter+ '" class="indexletter">' + current_letter + "</div>\n")
            indexfile.write('\n<div id="indexletter-' + current_letter.lower() + '" class="indexletter">\n')
            new_letter = True
            depth = 0
        else:
            new_letter = False

        try:
            this_marker = this_environment['marker']
        except KeyError:
            this_marker = "Unknown Marker"
        if this_marker in ["text", "center", "table"]:  # think: equation > center > table
             try:
                 this_parents_parent = this_environment['parent']
                 parents_parent_marker = component.environment[this_parents_parent]['marker']
                 if parents_parent_marker not in ['blob','section','subsection','subsubsection']:
                     this_marker = parents_parent_marker
                     this_knowl_target = this_parents_parent
                     this_knowl_target_stub = utilities.safe_name(this_knowl_target, idname=True)
                     component.index[entry_number]['context_parent'] = this_parents_parent
             except KeyError:
                 logging.error('no parent of %s', this_environment)
                 logging.error('or maybe I mean %s', component.environment[this_parents_parent])
                 this_marker += "NP"
        if this_marker in mapping.name_of_index_item:
            this_link_name = mapping.name_of_index_item[this_marker]
        else:
            this_link_name = this_marker

        if this_link_name == "par":
            this_link_name = "&sect;" + closest_codenumber(this_parent) + "-p"
        else:
            this_link_name += "-" + closest_codenumber(this_parent)

        # need to remove the part before the @ after the list is sorted:
        # used for things like \index{Dn@$D_n$} or \index{group!Dn@$D_n$}
        if "@" in this_item:
            this_item = re.sub("[^!]*@","",this_item)
        this_item = utilities.tex_to_html(this_item)

        this_knowl = '<a knowl="' + this_knowl_target_stub + '.knowl">'
        this_knowl += this_link_name
        this_knowl += '</a>'

        if this_item == current_item:
            indexfile.write('<span class="indexknowl">' + this_knowl + '</span>')
        elif "!" in this_item:
            this_heading, this_sub_item = this_item.split("!",1)
            if current_heading and this_heading == current_heading:
                # necessarily this_item is different than the previous item
                indexfile.write('</div>\n')  # close off the current item
                depth -= 1

                indexfile.write('\n<div class="subindexitem">'+this_sub_item)
                indexfile.write('<span class="indexknowl">' + this_knowl +'</span>')
                depth += 1
            elif this_heading == current_item:
                indexfile.write('</div>\n')  # close off the previous item, which is now a heading
                depth -= 1

                current_heading = this_heading
                indexfile.write('\n<div class="subindexitem">'+this_sub_item)
                indexfile.write('<span class="indexknowl">' + this_knowl +'</span>')
                depth += 1
            else:   # new heading
                if depth:  # or True:
                    indexfile.write('</div>\n')  # close off the previous item
                    depth -= 1

                indexfile.write('\n<div class="indexitem">'+this_heading+'</div>\n')
                current_heading = this_heading
                indexfile.write('\n<div class="subindexitem">'+this_sub_item)
                indexfile.write('<span class="indexknowl">' + this_knowl +'</span>') 
                depth += 1

        else:
            if depth:
                indexfile.write('</div>\n')  # close off the previous item
                depth -= 1
            else:
                pass

            indexfile.write('\n<div class="indexitem">'+this_item)
            depth += 1
            indexfile.write('<span class="indexknowl">' + this_knowl +'</span>')
            current_heading = ""

        current_item = this_item


    indexfile.write('\n</div>\n')   # close off item
    indexfile.write('\n</div>\n')   # close off the final letter

    indexfile.write('</section>')
    indexfile.write('</div></main></div>')
    indexfile.write('</html>')
    indexfile.close()

    logging.info("wrote the index")


#################

def saveoutputfile(filename,filecontents):

    fullfilename = component.outputdirectory + "/" + filename
#    print filename
#    if filename.startswith("biblio"):
#        print filecontents[:175]
#        print filecontents[6000:6075]

# no longer needed for python3?
#    try:
#        filecontents = filecontents.decode('utf-8',errors='replace')
#    except UnicodeEncodeError:
#        logging.warning("FONT ERROR in %s", filename)
#        filecontents = utilities.other_alphabets_to_latex(filecontents)
#        #filecontents = filecontents.encode('utf-8',errors='ignore')
#    except AttributeError:
#        print("Error with utf-8 decode")
    filecontents = utilities.other_alphabets_to_latex(filecontents)
    thefile = codecs.open(fullfilename,"w", "utf-8")
    thefile.write(filecontents)
    thefile.close()

##################

def printdiagnostics():

    print("author macros, parsed:")
    for j in component.definitions_parsed:
        print(component.definitions_parsed[j])

    print("author macros, all(?):")
    for j in component.definitions:
        print(j)

    print("missing macros")
    print(component.missing_macros)

    print(component.html_sections)

    if component.verbose:
        for pers in component.known_people:
            pers_data = '"'+str(pers['mr_id'])+'"'+":"
            link_name = utilities.author_name_for_link(pers)
            pers_data += '"'+link_name+'"'
            print(pers_data + ",")

    print("writer",component.writer)

    print("component.index has", len(component.index), "entries")
    print("component.terminology has", len(component.terminology), "entries")
    for entry in component.terminology:
        print(entry)

###############

def closest_codenumber(sha1key):

    this_sha1 = sha1key

    while this_sha1:
        try:
            this_codeumber = component.environment[this_sha1]['codenumber']
            return this_codeumber
        except KeyError:
            try:
                this_sha1 = component.environment[this_sha1]['parent']    
            except KeyError:
                this_sha1 = ""

    return ""

def closest_codenumber_ordinal(sha1key, scale=100, depth=4):

    # the defaults are adequate if no section has more than 99 subsections,
    # and there are fewer than 4 levels of numbering

    closest_number = closest_codenumber(sha1key)

    if not closest_number:
        return 0

    digits = closest_number.split(".")

    scale_at_this_level = scale**depth

    answer = 0
    for dig in digits: 
        dig = re.sub(r"[^0-9]","",dig)  # can have codenumbers like 3.1.4x
        if dig:
            answer += int(dig)*scale_at_this_level
        scale_at_this_level /= scale

    return answer

###############

def make_dependency_tree():

    if 'html' not in component.target:
        return ""

    for sha1key in component.environment:
        try:
            this_marker = component.environment[sha1key]['marker']
        except KeyError:
            logging.error("environment %s has no marker: %s", sha1key, component.environment[sha1key])
            this_marker = ""
            continue
        if this_marker != "definition" and this_marker not in component.theoremlikeenvironments:
            continue
        this_text = component.environment[sha1key][component.target]
        
        this_text = re.sub('a\s+knowl="([0-9a-f]{40}).knowl">([^<]+)<',
                            lambda match: make_dependency_tr(match, sha1key),
                            this_text)

#################

def make_dependency_tr(txt, target):

    source = txt.group(1)
    theword = txt.group(2)

    source_dict = component.environment[source]
    try:
        source_location = source_dict['codenumber']
    except KeyError:
        source_location = ""
    try:
        source_title = source_dict['sqgroup']
    except KeyError:
        source_title = ""
    try:
        source_marker = source_dict['marker']
    except KeyError:
        source_marker = ""

    target_dict = component.environment[target]
    try: 
        target_location = target_dict['codenumber']
    except KeyError:
        target_location = ""
    try:
        target_title = target_dict['sqgroup']
    except KeyError:
        target_title = "" 
    try:
        target_marker = target_dict['marker']
    except KeyError:
        target_marker = ""

    component.dependency_tree.append([[source, source_marker, source_location, source_title],theword,[target,target_marker,target_location,target_title]])

#############

def tidy_up():

    logging.info("final tidy_up")

    hasbackmatter = False

    if component.target == 'ptx':
        with open(component.outputdirectory + "/" + "main.ptx", "a") as mainfile:
            for j, secfile in enumerate(component.html_sections):
               # skip the first one becuse it is main.ptx
                if not component.html_sections_type[secfile].startswith("main"):
                    if secfile.startswith("bib"):
                        mainfile.write("\n")
                        mainfile.write('<backmatter>')
                        mainfile.write("\n")
                        hasbackmatter = True
                        logging.info("started backmatter")
                    # if there are chapters, then the seciton files are included in the
                    # chapter files, not in the main file

       # This is broken because we use the latex_label for section names,
       # and those do not typically start with "section".
       # maybe need to look if the item has a parent?  No, not good enough if all
       # we have is the component.html_sections list
                #    if not (secfile.startswith('sec') or secfile.startswith('s_')) or component.toplevel > 0:
                    if not component.html_sections_type[secfile] == 'section'  or component.toplevel > 0:
                        mainfile.write("\n")
                        mainfile.write('<xi:include href="./' + secfile + '" />')
                        mainfile.write("\n")
                else:
                    logging.warn("skipping index file: %s", secfile)
            logging.info("closing the top level tags in the main file")
            if not hasbackmatter:
                mainfile.write('<backmatter>' + "\n")
                # the backmatter section may be empty

            if component.index:
                mainfile.write("<index>" + "\n")
                mainfile.write("<title>Index</title>" + "\n")
                mainfile.write("<index-list />" + "\n")
                mainfile.write("</index>" + "\n")

            mainfile.write("\n")
            mainfile.write('</backmatter>')
            mainfile.write("\n")
            if component.toplevel == 0:
                mainfile.write('</book>')
            else:
                mainfile.write('</article>')
            mainfile.write("\n")
            mainfile.write('</pretext>')
            mainfile.write("\n")

    logging.info("files which were input: %s", component.known_files)


