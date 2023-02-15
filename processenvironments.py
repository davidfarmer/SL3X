# -*- coding: utf-8 -*-

import sys
import re
import logging
import codecs

import component
import makeoutput
import utilities
import mapping

####################################
#
# These functions occur in pairs:
#    the first uses a regular expression to locate a component of
#    the document and then pass it off to the second function, which
#    puts the component into the appropriate variable/list/dictionary.
#
####################################

def processabstract(text):

    logging.info("looking for the abstract")
    thetext = text

    thetext = re.sub(r"\\begin{abstract}(.*?)\\end{abstract}",
                     processabs,thetext,0,re.DOTALL)

    return(thetext)

def processabs(txt):

    theabstract = txt.group(1).strip()

    component.environment['abstract'] = {'marker':"abstract",
                                            'parent':"",
                                            'sha1head': "abstract",
                                            'star': "",
                                            'component_raw':theabstract,
                                            'component_separated':theabstract,
                                            component.target:theabstract
                                            }
     #  Warning:  the last entry is a hack, because we build the TOC
     #            before we process the abstract

    return ""

############ title

def processtitle(text):

    logging.info("looking for the title")
    thetext = text

    thetext = re.sub(r"\\title\*?((\{|\[).*)", processtitl,thetext,0,re.DOTALL)
    logging.debug("the title is: %s", component.title)

    # later go back and do something useful with the footnote and thanks
    component.title =  utilities.replacemacro(component.title,"footnote",1,"")
    component.title =  utilities.replacemacro(component.title,"thanks",1,"")
    component.title =  utilities.replacemacro(component.title,"vspace",1,"")

    component.title =  utilities.html_to_latex_alphabet(component.title)
    component.title = re.sub("\$([^$]+)\$", r"\\(\1\\)", component.title)

    logging.info("the title is: %s", component.title)

    return(thetext)

def processtitl(txt):

    textafter = txt.group(1).lstrip()
    logging.debug("the title should start with %s",textafter[:30])
    if textafter.startswith("["):
        title_short, textafter = utilities.first_bracketed_string(textafter,0,"[","]")
        title_short = utilities.strip_brackets(title_short,"[","]")
        title_short = title_short.strip()
        component.title_short = title_short
        component.environment['title_short'] = {'marker':"title_short",
                                                'component_raw':title_short,
                                                'component_separated':title_short,
                                                component.target:title_short
                                               }

    textafter = textafter.lstrip()

    if textafter.startswith("{"):
        title, textafter = utilities.first_bracketed_string(textafter,0,"{","}")
        title = utilities.strip_brackets(title,"{","}") 
        title = title.strip()
        component.title = title
        component.environment['title'] = {'marker':"title",
                                          'component_raw':title,
                                          'component_separated':title,
                                          component.target:title
                                         }
    else:
        component.environment['title'] = {'marker':"title",
                                          'component_raw':"Title Goes Here",
                                          'component_separated':"Title Goes Here",
                                          component.target:"Title Goes Here"
                                         }
        logging.error("title not in curly brackets")

    return textafter

############ thanks

def processthanks(text):

    logging.info("looking for the thanks")
    thetext = text

    thetext = re.sub(r"\\thanks *({.*)",
                     processthk,thetext,0,re.DOTALL)

    return(thetext)

def processthk(txt):

    thanks_and_more = txt.group(1)
    thanks, the_rest = utilities.first_bracketed_string(thanks_and_more)
    thanks = utilities.strip_brackets(thanks)

    component.thanks = thanks

    logging.debug("the thanks is: %s", component.thanks)

    return the_rest

########### author

def processauthor(text):

    logging.info("looking for authors")
    thetext = text

## need to handle \author[farmer]{David W. Farmer}
# Can have multiple \author{...} entries:  1502.00938

    utilities.something_changed = 1
    while utilities.something_changed:
        utilities.something_changed = 0
        thetext = re.sub(r"\\author\b(.*)",
                        processauth,thetext,1,re.DOTALL)

    return(thetext)


def processauth(txt):

    utilities.something_changed += 1

    author_and_more = txt.group(1).lstrip()
    if author_and_more.startswith("["):
        throw_away, author_and_more = utilities.first_bracketed_string(author_and_more,lbrack="[",rbrack="]")
    author_and_more = author_and_more.lstrip()
    author_raw, therest = utilities.first_bracketed_string(author_and_more)
    author_raw = utilities.strip_brackets(author_raw)

    # later go back and do something with the footnote and thanks
    author_raw = utilities.replacemacro(author_raw,"footnote",1,"")
    author_raw = utilities.replacemacro(author_raw,"thanks",1,"")

    # \author{Jeffrey Giansiracusa$^1$}
    author_raw = re.sub(r"\$[^\$]+\$", "", author_raw)

    logging.debug("author_raw, %s", author_raw[0:150])
    if r"\and" in author_raw:
        author_raw_list = author_raw.split(r"\and")
    else:
        author_raw_list = author_raw.split(r" and ")
    logging.debug("author_raw_list %s", author_raw_list)
    for auth in author_raw_list:
        auth_only = re.sub(r"\\\\.*","",auth,0,re.DOTALL)
        auth_only = auth_only.strip()
        component.authorlist.append(auth_only)

    sys.stdout.flush()

    return therest

########## email

def processemail(text):

    thetext = text

    thetext = re.sub(r"\\email{([^{}]*)}",processeml,thetext,0,re.DOTALL)

    return(thetext)

def processeml(txt):
# need to fix: associate email to author

    component.email = txt.group(1)

    return ""

############

def processappendices(text):

    # need to do a better job at handling appendices
    logging.info("looking for appendices, and ignoring them")
    thetext = text

# there are other cases where the appendices are marked differently
    thetext = re.sub(r"(\\begin{appendix}.*\\end{appendix})",
                     processappendix,thetext,0,re.DOTALL)

    return(thetext)


def processappendix(txt):

# there could be more than one appendix, so we should make a list of them
    component.appendix = txt.group(1)

    return component.appendix  

##########

def processbibliography(text):

    logging.info("processing the bibliography")
    thetext = text

    thetext = utilities.replacemacro(thetext,"bib",1,"\\bibitem{#1}")   # see 1308.5417
 ###   need a place where the following is used, so we can reconcile it with the above
 ###   thetext = utilities.replacemacro(thetext,"bib",3,"\\bibitem{#1} #3")

# temporary hack for biblatex.  example: 1410.0806
    thetext = utilities.replacemacro(thetext,"entry",3,"\\bibitem{#1} ")
    thetext = re.sub(r"\\endentry","",thetext)

    logging.debug("still processing the bibliography: %s", thetext[:150])

      # stick in \endbibitem in the right places, so then we can minimal search on 
      # \begin ... \end pairs.
    thetext += "\endbibitem"
    thetext = re.sub("\\\\bibitem","\\\\endbibitem\n\\\\bibitem",thetext)

    thetext = re.sub("\\\\bibitem(.*?)\\\\endbibitem",
                     processbibitem,thetext,0,re.DOTALL)

    logging.debug("done processing bibliography")

def processbibitem(txt):

    thebibentry = txt.group(1).strip()
    component.counter['bibitem'] +=1

    if thebibentry.startswith("["):  # author named the bibitem
        squaregroup, everythingelse = utilities.first_bracketed_string(thebibentry,0,"[","]")
        squaregroup = utilities.strip_brackets(squaregroup,"[","]")
        squaregroup = utilities.strip_brackets(squaregroup)
    else:
        squaregroup = ""
        everythingelse = thebibentry

    everythingelse = everythingelse.strip()

    if everythingelse.startswith("{"):  # the key should come next
        thekey, everythingelse = utilities.first_bracketed_string(everythingelse,0,"{","}")
        thekey = utilities.strip_brackets(thekey,"{","}")
        thekey = utilities.safe_name(thekey, idname=True)
        everythingelse = everythingelse.strip()
        everythingelse = utilities.strip_brackets(everythingelse,"{","}")
    else:
        logging.error("Error, missing bib key: %s", thebibentry)
        thekey = squaregroup

    theentry = everythingelse
    theentry = re.sub(r"\\newblock","",theentry)
    theentry = re.sub(r"\\thinspace"," ",theentry)

    if squaregroup:
        thelabel = squaregroup
    else:
        thelabel = str(component.counter['bibitem'])

    logging.debug("Saving bibitem: %s", 'bibitem' + thekey)

    thekey = thekey.strip()
    thelabel = thelabel.strip()

    component.environment['bibitem' + thekey] = {'marker':'bibitem',
                                    'thelabel':thelabel,
                                    'sha1head':"",   # is that entry optional?
                                    'star':"",
                                    'component_raw':theentry,
                                    'component_separated':theentry
                                    }

    component.bibliography_entries.append({'thelabel':thekey,'component_raw':theentry})

    bibfilename = component.outputdirectory + "/" + utilities.safe_name(thekey, idname=True) + ".knowl"

    try:

# no longer needed for python3?
#        try:
#            theentry = theentry.decode('utf-8',errors='replace')
#        except UnicodeEncodeError:
#            logging.warning("font encoding issue in theentry: %s", theentry)

        theentry = re.sub("("+component.sha1heads_all+")([0-9a-f]{40})END",
                                      makeoutput.expandhtml,theentry)

        theentry_html = utilities.tex_to_html(theentry)
        theentry_html = expand_text_macros_core(theentry_html)
        theentry_html = utilities.remove_silly_brackets(theentry_html)

    #    bibfile.write(theentry_html + makeoutput.arxivabstract(thekey,theentry))
        if component.target == "html":

    # rewrite this using 'with'
          bibfile = codecs.open(bibfilename,'w', 'utf-8')
          bibfile.write(theentry_html)
          bibfile.write(makeoutput.arxivabstract(thekey,theentry))
          bibfile.close()

    except IOError:
        logging.error("problem opening bibfile: %s", bibfilename)
        theentry_html = ""

    thelabel_html = utilities.tex_to_html(thelabel)

    component.bibliography_in_html += '\n\n<div class="bib">\n<div class="bibitem">['+thelabel_html+']</div>\n'
    component.bibliography_in_html += '\n\n<div class="bibentry">'
    component.bibliography_in_html += theentry_html + makeoutput.arxivabstract(thekey,theentry)
    component.bibliography_in_html += '</div>\n</div>\n'

    return ""

############

def replace_bad_macros(text):
    """Expand macros that hide the structure.

    For example:  \be --> \begin{equation}
    """

    thetext = text

    for macro in component.definitions_parsed:
        macroname = macro[1:]  # take away the \.  Probably should treat that uniformly.
        defn = component.definitions_parsed[macro]
        replace_it_by = defn['thedefinition']
        logging.debug("possibly replacing %s by %s, more completely %s", macro, replace_it_by, defn)

     #   print "macroname", macroname, "gg"
        if not macroname:
            logging.warning("skipping empty macro %s with definition %s", macro, replace_it_by)
            continue

        if not macroname[0].isalpha():
            logging.warning("skipping weird macro %s with definition %s", macro, replace_it_by)
            continue

        if re.search(r"\\" + macroname + r"\b", replace_it_by):  # as in \def{\ax}{\ax 0}, which keps expanding forever
            logging.warning("skipping recursive macro %s with definition %s", macro, replace_it_by)
            continue
        
        if defn['numargs'] > 1:
             # only expand bad macros with 0 or 1 arguments (why?)
             logging.info("skipping macro %s because it has >1 argument",macroname)

        elif (("\\begin" in replace_it_by  or  "\\end" in replace_it_by or
               "\\section" in replace_it_by  or "\\subsection" in replace_it_by or
               "\\item" in replace_it_by  or "\\bibitem" in replace_it_by or
               "\\ref{" in replace_it_by  or "\\cite{" in replace_it_by or "\\label{" in replace_it_by or
               replace_it_by == "" or   # if the macro expands to nothing, might as well replace it
               "\\newcommand" in replace_it_by or "\\DeclareMathOperator" in replace_it_by) and
               "#" not in macroname and   # probably we missed a plain-style macro with an argument 
               "newif" not in replace_it_by and
               len(macroname.strip()) > 1 and
               "@" not in replace_it_by and
               # the next one was supposed to avoid an infinite loop,
               # but is also blocked \be --> \begin{equation}
         #      macro not in replace_it_by and
               len(replace_it_by) < 100): 
            logging.info("replacing a bad macro %s with numargs %s and definition %s",
                          macroname, defn['numargs'], replace_it_by)
            thetext = utilities.replacemacro(thetext,macroname,defn['numargs'],replace_it_by)

    return thetext

##############

def replace_macro_in_text(macro, text):

    defn = macro
    thetext = text

    themacro = defn['themacro']
    themacro = re.sub(r"\\",r"\\\\",themacro)
    the_reg_expr = themacro
    the_reg_expr += r"\b"
    replace_it_by = defn['thedefinition']
    replace_it_by = re.sub(r"\\",r"\\\\",replace_it_by)
    thetext = re.sub(the_reg_expr,replace_it_by,thetext)

    return thetext

##############

def replace_bad_theorems(text):

    thetext = text

    for thm in component.newtheorems_parsed:
        logging.debug("have we seen this: %s ", thm)

        themarker = thm['themarker']
        thedisplaynamelower = thm['thedisplayname'].lower()

        themarkerstem = re.sub(r"\*","",themarker)
        themarkerescaped = re.sub(r"\*",r"\\*",themarker)

        if themarker in list(component.environment_types.keys()):
            logging.debug("already know about this environment: %s which is a %s",
                           themarker, thedisplaynamelower)
        
        elif thedisplaynamelower in list(component.environment_types.keys()):
            logging.debug("yes, found something to replace: %s", thedisplaynamelower)
            the_re = r'(begin|end){' + themarkerescaped + r'(\**)' + r'}'
            the_new_text = r'\1{' + thedisplaynamelower + r'\2' +  r'}'

            thetext = re.sub(the_re,the_new_text,thetext)
            sys.stdout.flush()

        else:
            logging.debug("that one is new to me")

            escaped_displayname = re.sub(r"\\",r"\\\\",thm['thedisplayname'])
                       # because thedisplayname may contain backslashes

            the_re_begin = r'(begin){' + themarkerescaped + r'(\**)' + r'}'
            the_new_text_begin = r'\1{' + 'generictheorem' + r'\2' +  r'}'
            the_new_text_begin += r'[' + escaped_displayname + r']'

            thetext = re.sub(the_re_begin,the_new_text_begin,thetext)

            the_re_end = r'(end){' + themarkerescaped + r'(\**)' + r'}'
            the_new_text_end = r'\1{' + 'generictheorem' + r'\2' +  r'}'

            thetext = re.sub(the_re_end,the_new_text_end,thetext)

    return thetext

##############

def incrementcounter(cc,star=""):
    """ Increment/reset the appropriate counters when entering a new environment.
    """

    if cc == 'list':
        utilities.list_depth += 1
        component.counter['list'] += 1
        logging.debug("list_depth: %s", utilities.list_depth)

    elif cc == 'endlist':
        component.counter['list'] = 0
        try:
            component.counter['item'][utilities.list_depth] = 0
        except IndexError:
            utilities.list_depth -= 1
     #       component.counter['item'][utilities.list_depth] = 0
        utilities.list_depth -= 1
        logging.debug("list_depth: %s", utilities.list_depth)

    elif cc == 'item':
        try:
            component.counter['item'][utilities.list_depth] += 1
        except IndexError:
            logging.error("utilities.list_depth " + str(utilities.list_depth) + " too large") 

    else:
        if star:
            component.counterstar[cc] += 1
            logging.debug("incrementing counterstar of %s, its value now is %s",
                          cc, component.counterstar[cc])
        else:
            component.counter[cc] += 1

    # if the counter is a (sub)section then that means we just entered a (sub)section.
    # so we need to reset all lower (subsub)sections and all environment counters.
    try:
        secindex = component.sectioncounters.index(cc)
        if not star:
            for j in range(secindex+1, len(component.sectioncounters)):
                subcc = component.sectioncounters[j]
                component.counter[subcc] = 0
            if secindex <= component.toplevel + 1:
                # in a paper, we number within subsections but not subsubsections
                for env in component.environmentcounters:
                    component.counter[env] = 0
                utilities.list_depth = 0

    except ValueError:  # the cc was not a section counter, so nothing to do
        pass

def currentcounterastext(toplevel, cc, star=""):
    """ Return the codenumber of the environment, as in "Theorem 3.1.1"
        or "Subsection 3.1".

    """

    # There is a weird case where a top level section is starred.
    # Our fix may not handle the case where such a section has subsections.

    if star and cc == component.sectioncounters[toplevel]:
        thecodenumber = str(component.counterstar[component.sectioncounters[toplevel]])
    else:
        thecodenumber = str(component.counter[component.sectioncounters[toplevel]])

    # not sure the above makes sense:  can we "star" the top level?
 #   thecodenumber = str(component.counter[component.sectioncounters[toplevel]])

    try:
        secindex = component.sectioncounters.index(cc)
        if star and secindex == toplevel:   # this didn't work.  See 
            thecodenumber += "x"
        for j in range(toplevel+1,secindex+1):
            if star and j == secindex:   # the parents are numbered as usual, just not the last number
                thecodenumber += "." + str(component.counterstar[component.sectioncounters[j]]) + "x"
                logging.debug("counterstar so far: %s", thecodenumber)
            else:
                thecodenumber += "." + str(component.counter[component.sectioncounters[j]])

    except ValueError:  # the cc was not a section counter
        for j in range(toplevel+1,toplevel+2):  
            this_subsec_counter = component.counter[component.sectioncounters[j]]
            if this_subsec_counter:   # omit the 0 for ssec0
                thecodenumber += "." + str(component.counter[component.sectioncounters[j]])
        thecodenumber += "." + str(component.counter[cc])

    if cc == "item":
        thecode = ""
        for j in range(1,6):   #utilities.list_depth):
            thevalue = component.counter['item'][j]
            if thevalue:
                thecode += str(thevalue)
                thecode += "."
            else:
                thecode = re.sub("\.$","",thecode)
                break
        return thecode

    else:
        if star:
            return thecodenumber     # ""    # "tttt"+thecodenumber
        else:
            return thecodenumber

###############

def numberenvironments():

    logging.info("determining environment numbering")

    for env in range(1,29999):  # could we ever have more than 30k environments?
                             # Probably yes, because APEX Calulus has >20000
        utilities.something_changed=0
        component.documentcontents = re.sub("(" + component.sha1heads_numberable + ")([0-9a-f]{40})END",
                                  utilities.putback,component.documentcontents,1)

        if not utilities.something_changed:
            logging.info("finished numbering after %s environments", env)
            break

###############

def makelabels():

    logging.info("associating labels to the environment numbering")
    for label in component.label:
        sha1key = component.label[label]['sha1']
        try:
            codenumber = component.environment[sha1key]['codenumber']
        except KeyError:
         # TO DO:  don't flag cases like footnotes, which are not supposed to be numbered.
            logging.error("environment %s with label %s has no codenumber, from file %s",
                           sha1key, label, component.inputfilename)
            codenumber = "x"
        component.label[label]['codenumber'] = codenumber

##############

def make_sl2xID():

    logging.info("making the IDs for everything")
    for sha1key in component.environment:
        this_sl2xID = ""
        comp = component.environment[sha1key]
        this_marker = comp['marker']
        try:
            this_environment = component.environment_types[this_marker]
            this_class = this_environment['class']
        except KeyError:
            this_class = ""

        if 'latex_label' in comp:
            this_sl2xID = comp['latex_label']
        elif ((this_marker == 'generictheorem') or
              (this_class in ['definition','theorem','exercise','example','remark',
                              'aside', 'section'])):
            try:
                the_codenumber = comp['codenumber']
            except KeyError:
                if this_marker != "abstract":
                    logging.error("error, comp with no codenumber %s", comp)
                the_codenumber = "no.code.number"
            the_codenumber_dash = the_codenumber.replace(".", "-")
            this_sl2xID =  this_marker + the_codenumber_dash
        elif this_class in ['proof','proofsketch']:
            try:
                the_codenumber = comp['codenumber']
            except:
                the_codenumber = "xyz"
            the_codenumber_dash = the_codenumber.replace(".", "-")
            this_sl2xID =  "proof" + the_codenumber_dash
        else:
            this_sl2xID = sha1key

        component.environment[sha1key]['sl2xID'] = this_sl2xID

##############

def make_component_target():

    logging.info("making %s version of all the separated components", component.target)
    for sha1key in list(component.environment.keys()):
        component.environment[sha1key][component.target] = component.environment[sha1key]['component_separated']

################

def space_after_lessthan():
    """ change things like $a<b$ to $a< b$ to un-confuse the browser.
        this has to be done before any html tags get added, but after
        things like tikz are processed

        may need an XML version that converts to &lt;

    """

    if component.target == 'ptx':
        logging.info("not converting < for ptx output")

    logging.info("making math < not look like an html tag")

    for sha1key in list(component.environment.keys()):
        thetext = component.environment[sha1key][component.target]
        # should we skip non-math environments?  verbatim environments?

        if component.target == 'html':
            thetext = re.sub("<<", r"< < ", thetext)  # probably should have been \ll
            thetext = re.sub("<(\S)", r"< \1", thetext)  # to un-confuse HTML
        if component.target == 'ptx':
            this_marker = component.environment[sha1key]['marker']
            if this_marker in component.math_environments or this_marker == "$":
                thetext = re.sub("<", r"\\lt ", thetext)
                thetext = re.sub("&", r"\\amp ", thetext)

        component.environment[sha1key][component.target] = thetext

################

def findunexpandedmacros():

    logging.info("looking for unexpanded macros")
    component.missing_macros = {}

    for sha1key in component.environment:
        try:
            thetext = component.environment[sha1key]['caption']
            if thetext: logging.debug("captiontext %s", thetext)
            if "\\" in thetext:
                foundmacro = re.sub(r"(\\[a-zA-Z0-9]+)(.*)",
                                      findunexpandedmac,thetext,0,re.DOTALL)
        except KeyError:
            pass

      #the above is a hack.  We need to be more organized about where we keep captions, titles,
      # and other words that are not "text"

        if component.environment[sha1key]['marker'] != 'text':
            continue
        thetext = component.environment[sha1key]['component_separated']
        utilities.something_changed = 1
        while utilities.something_changed:
            utilities.something_changed = 0
            thetext = re.sub(r"(\\[a-zA-Z]+)(.*)",findunexpandedmac,thetext,1,re.DOTALL)

    logging.debug("component.missing_macros: %s", component.missing_macros)
    
def findunexpandedmac(txt):
    themacro = txt.group(1)
    everythingelse = txt.group(2)

    utilities.something_changed +=1

    if everythingelse.startswith("{"):
        the_extra, everythingelse = utilities.first_bracketed_string(everythingelse)
        if themacro not in mapping.known_macros and themacro not in component.missing_macros:
            logging.warning("unknown macro: %s with the_extra %s", themacro, the_extra)

    if themacro in mapping.known_macros:
        pass    
    elif themacro in component.missing_macros:
        component.missing_macros[themacro] += 1
    else:
        component.missing_macros[themacro] = 1

    return everythingelse

###############

def expand_author_macros(text=""):
    """Replace (some) author macros in text by their expansion."""

    thetext = text

#      if thetext:
#          for macro in component.definitions_parsed:
#              thedefn = component.definitions_parsed[macro]
#              macro_name = thedefn['themacro'][1:]
#              numargs = thedefn['numargs']
#              if numargs > 2:
#                  continue   # for now, just replace 0 or 1 argument macros
#              thedef = thedefn['thedefinition']
#              thetext = expand_author_mac(macro_name,numargs,thedef,thetext)
#          return thetext
#  
#  ######
#  ######   Somethign is wrong here: you can't reach the second part of this
#  ######   function unless text is empty, in which case it doesn't do anything.
#  ######   So I am adding the 'return ""' directly below, and will come back
#  ######   and try to fix this later.   DF  2/22/16
#  ######
#  
#      return ""

    logging.info("expanding author macros everywhere")
    for macro in component.missing_macros:
        if (macro in component.definitions_parsed
                    and macro not in mapping.known_macros):
            macro_name = macro[1:]
            logging.debug("expanding the author macro: %s", macro_name)
            thedefn = component.definitions_parsed[macro]
            numargs = thedefn['numargs']
            if numargs > 2:
                continue   # for now, just replace 0 or 1 argument macros
            thedef = thedefn['thedefinition']
            # a hack to avoid certain bad macros
            thedef = re.sub(r"\\@", " " ,thedef)  #  \newcommand{\tdlc}{t.d.l.c.\@\xspace}
            if "@" not in thedef and not utilities.text_exactly_contains(thedef,macro):
                thetext = expand_author_mac(macro_name,numargs,thedef,thetext)
            else:
                logging.error("avoided expanding the macro %s with definition %s", macro_name, thedef)
    return thetext

def expand_author_mac(macro,numargs,thedef,text=""):

    logging.debug("replacing author macro %s with numargs %s and thedef %s",
                   macro, numargs, thedef)

    if text:
        thetext = text
        thetext = utilities.replacemacro(thetext,macro,numargs,thedef)
        return thetext

    for _ in range(99):  # could we have 100 macros to expand in 1 paragraph?
        utilities.something_changed = 0
        for sha1key in component.environment:
          # elements of a list are text but have marker 'item', not 'text'
            if component.environment[sha1key]['marker'] not in ['text', 'item']:
                continue
            thetext = component.environment[sha1key]['component_separated']
            thetext = utilities.replacemacro(thetext,macro,numargs,thedef)
            component.environment[sha1key]['component_separated'] = thetext
        if not utilities.something_changed:
            logging.debug("finished expanding author macros at depth %s", _)
            break

    for sha1key in component.environment:
        try:
            thetitle = component.environment[sha1key]['title']
            thetitle = utilities.replacemacro(thetitle,macro,numargs,thedef)
            component.environment[sha1key]['title'] = thetitle

        except KeyError:   # component does not have a title
            pass

    # The next one failed because apparently caption is not what we call the caption
    for sha1key in component.environment:
        try:
            thecaption = component.environment[sha1key]['captiontext']
            thecaption = utilities.replacemacro(thecaption,macro,numargs,thedef)
            component.environment[sha1key]['captiontext'] = thecaption
            logging.debug("replacedauthormacro %s in captiontext %s %s", macro, sha1key, thecaption)
        except KeyError:   # component does not have a caption
            pass

    return ""
##############

def expand_text_macros():

    logging.info("replacing text macros")

    for sha1key in component.environment:
        if component.environment[sha1key]['marker'] not in ['text', 'footnote', 
                                  'bibitem','item','itemize','enumerate','descriptionlist','abstract']:
                  # there should be a list component.textenvironmentmarkers
            continue
        thetext = component.environment[sha1key][component.target]
        if "\\" in thetext:
            thetext = expand_text_macros_core(thetext)
             #  need to rethink how these functions will be used

        component.environment[sha1key][component.target] = thetext

def expand_text_macros_core(text):

    thetext = text
    if not thetext:
        logging.warning("empty string passed to expand_text_macros_core")
    else:  # need to do this cleaner
        if component.target == 'html':
            for macro in mapping.text_macros_html:
                numargs = mapping.text_macros_html[macro][0]
                thedef = mapping.text_macros_html[macro][1]
                thetext = utilities.replacemacro(thetext,macro,numargs,thedef)
        elif component.target == 'ptx':
            for macro in mapping.text_macros_ptx:
                numargs = mapping.text_macros_ptx[macro][0]
                thedef = mapping.text_macros_ptx[macro][1]
                thetext = utilities.replacemacro(thetext,macro,numargs,thedef)

    return thetext

##############

def expand_smart_references():

    logging.info("replacing smart references")

    for sha1key in component.environment:
        thetext = component.environment[sha1key]['component_separated']
        if "\\fullref" in thetext or "\\autoref" in thetext:
            thetext = re.sub(r"\\(full|auto)ref\s*\{([^{}]+)\}",expand_smart_refs,thetext)
            component.environment[sha1key]['component_separated'] = thetext

        try:
            thetitle = component.environment[sha1key]['title']
            if "\\fullref" in thetitle:
                thetitle = re.sub(r"\\(full|auto)ref\s*\{([^{}]+)\}",expand_smart_refs,thetitle)
                component.environment[sha1key]['title'] = thetitle

        except KeyError:   # component does not have a title
            pass

        try:
            thesqgroup = component.environment[sha1key]['sqgroup']
            if "\\fullref" in thesqgroup or "\\autoref" in thesqgroup:
                thesqgroup = re.sub(r"\\(full|auto)ref\s*\{([^{}]+)\}",expand_smart_refs,thesqgroup)
                component.environment[sha1key]['sqgroup'] = thesqgroup

        except KeyError:   # component does not have a sqgroup
            pass

def expand_smart_refs(txt):

    thelabel = txt.group(2)   # (full|auto) is group(1)

    thelabel = re.sub(r" *\n *"," ",thelabel)  # labels can have extraneous \n's
    thelabel = re.sub(r"\s+"," ",thelabel)  # maybe don't need the previous sub
    thelabel = utilities.safe_name(thelabel)

    try:
        this_sha1 = component.label[thelabel]["sha1"]
    except KeyError:
        logging.error("unknown label %s", thelabel)
        return "EEEE"  + r"~\ref{"+thelabel+"}"

    this_marker = component.environment[this_sha1]['marker']
    if this_marker == "blob":
        this_marker = "section"

    the_answer = this_marker.title() + r"~\ref{"+thelabel+"}"

    return the_answer

###################

def convert_author_terminology():

    # guess that highlighted words in a definition are terms being defined

    for sha1key in component.environment:
        if component.environment[sha1key]['marker'] in component.definitionlikeenvironments:
            thetext = component.environment[sha1key]['component_separated']
            thetext = re.sub(r"\\(emph|textit|textbf)",r"\\terminology",thetext)
            component.environment[sha1key]['component_separated'] = thetext
        elif 'parent' in component.environment[sha1key]:
            the_parent = component.environment[sha1key]['parent']
            if the_parent and component.environment[the_parent]['marker'] in component.definitionlikeenvironments:
                thetext = component.environment[sha1key]['component_separated']
                thetext = re.sub(r"\\(emph|textit|textbf)",r"\\terminology",thetext)
                component.environment[sha1key]['component_separated'] = thetext

def extract_index_and_terminology():

    logging.info("extracting index entries")

    for sha1key in component.environment:
        thetext = component.environment[sha1key]['component_separated']
        while "\\index{" in thetext:
            thetext = re.sub(r"\\index\b(.*)",
                  lambda match: extract_ind(sha1key,match),thetext,1,re.DOTALL)
            component.environment[sha1key]['component_separated'] = thetext

        while "\\terminology{" in thetext:
            thetext = re.sub(r"\\terminology\b(.*)",
                  lambda match: extract_term(sha1key,match),thetext,1,re.DOTALL)
            # we don't completely remove the \terminology entries, because they are still needed
            # so we change them to \knownterminology
            component.environment[sha1key]['component_separated'] = thetext

def extract_term(sha1key,txt):

    term_entry_and_more = txt.group(1).lstrip()
    this_term, therest = utilities.first_bracketed_string(term_entry_and_more)
    this_term = utilities.strip_brackets(this_term)

    logging.debug("this_term: %s, is in %s", this_term, sha1key)

    this_term_entry = {"parent": sha1key,
                        "entry": this_term}

    component.terminology.append(this_term_entry)

    # as explained above, we don't completely remove the \terminology entries:
    # we change them to \knownterminology so that we can style them later

    return r"\knownterminology{" + this_term + "}" + therest

def extract_ind(sha1key,txt):

    index_entry_and_more = txt.group(1).lstrip()
    this_entry, therest = utilities.first_bracketed_string(index_entry_and_more)
    this_entry = utilities.strip_brackets(this_entry)

    logging.debug("this_index_entry %s for %s", this_entry, sha1key)

    this_index_entry = {"parent": sha1key,
                        "entry": this_entry}

    component.index.append(this_index_entry)

    if component.target == 'ptx':
        # currently only handle 2 levels in the index
        if "!" in this_entry:
            this_entry = re.sub(r"^([^!]*)!(.*)",r"<h>\1</h><h>\2</h>",this_entry,0,re.DOTALL)
        else:
            this_entry = "<h>" + this_entry + "</h>"

    return r"\knownindex{" + this_entry + "}" +therest

#################

def preprocess_terminology():

    logging.info("preprocessing the terminology")
# mostly copied from makeoutput.indexpage()
# see if they can be unified

    for entry_number, entry in enumerate(component.terminology):
        this_item_original = entry['entry']
        this_item_original = re.sub("("+component.sha1heads_all+")([0-9a-f]{40})END",
                                      makeoutput.expandhtml,this_item_original,1)
        this_item_original = this_item_original.strip()
        this_item = this_item_original

        this_item = utilities.strip_brackets(this_item,"(",")")
        # remove punctuation
        this_item = re.sub("[:;,.]$","",this_item)
        # replace \n or "  " by single spaces
        this_item = re.sub(r"\s"," ",this_item)
        # remove plural 's' from long words
        # actually, the 's' from the end of any long word, but not if it ends in 'ss'
        this_item = re.sub(r"([a-z]{2}[a-rt-z])s\b",r"\1",this_item)
        component.terminology[entry_number]['entry'] = this_item
    

    # sort by length so that we can substitute for long terms first
    component.terminology = sorted(component.terminology, key=lambda k: len(k['entry']))
    component.terminology.reverse()

    # now find the appropriate parent environment
    for entry_number, entry in enumerate(component.terminology):
        this_item = entry['entry']
        this_parent = entry['parent']
        this_knowl_target = this_parent
        this_environment = component.environment[this_parent]

        logging.debug("Processing Terminology: %s, which lives in %s",
                       entry['entry'], this_environment)
        try:
            this_marker = this_environment['marker']
        except KeyError:
            logging.error("missing marker %s", this_item)
            this_marker = "Unknown Marker"
        try:
            logging.debug("which had marker %s of marker type %s",
                          this_marker, component.environment_types[this_marker])
        except KeyError:
            logging.critical("unknown marker: %s", this_marker)
            continue
        if this_marker == "text":
             try:
                 this_parents_parent = this_environment['parent']
                 parents_parent_marker = component.environment[this_parents_parent]['marker']
                 logging.debug("parents_parent_marker %s", parents_parent_marker)
                 if parents_parent_marker not in ['blob',
                                 'section','subsection','subsubsection']:
                     this_marker = parents_parent_marker
                     this_knowl_target = this_parents_parent
                     component.terminology[entry_number]['context_parent'] = this_parents_parent
             except KeyError:
                 logging.error("no parent of %s", this_environment)
                 logging.error("or maybe I mean %s", component.environment[this_parents_parent])
                 this_marker += "NP"
        elif component.environment_types[this_marker]['class'].startswith('math'):
             try:
                 this_parents_parent = this_environment['parent']
                 logging.debug("now look at this_parents_parent: %s", this_parents_parent)
                 parents_parent_marker = component.environment[this_parents_parent]['marker']
                 logging.debug("elif parents_parent_marker %s of environment: %s",
                                parents_parent_marker, component.environment[this_parents_parent])
                 if parents_parent_marker not in ['blob',
                                 'section','subsection','subsubsection','enumerate','itemize','descriptionlist']:
                     this_marker = parents_parent_marker
                     this_knowl_target = this_parents_parent
                     component.terminology[entry_number]['context_parent'] = this_parents_parent
             except KeyError:
                 logging.error("no parent of %s", this_environment)
                 logging.error("or maybe I mean %s", component.environment[this_parents_parent])
                 this_marker += "NP"

    logging.info("Done preprocessing terminology")

#################

def section_containing(sha1,section_type="section"):

    this_sha1 = sha1
    this_environment = component.environment[sha1]
    this_marker = this_environment['marker']

    while this_marker != section_type:
            previous_sha1 = this_sha1
            try:
                this_sha1 = this_environment['parent']
            except KeyError:
                logging.warning("no parent in %s, %s",
                                 this_environment['marker'], this_environment['codenumber'])
                return previous_sha1
            if not this_sha1:
                logging.warning("missing parent in %s, %s",
                                this_environment['marker'], this_environment['codenumber'])
                return previous_sha1
            this_environment = component.environment[this_sha1]
            this_marker = this_environment['marker']

    return this_sha1

