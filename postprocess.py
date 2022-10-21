# -*- coding: utf-8 -*-

import re
import logging

import utilities
import component

def ptx_minipage_sidebyside(text):
    """ Two successive sidebyside's  are just one big sidebyside.
        A hack to take care of minipage nonsense.

    """

    thetext = text

    thetext = re.sub(r"\s*</sidebyside>\s*<sidebyside>\s*", "\n", thetext)

    return thetext

def ptx_wrap_statements(text):
    """ Add missing <statement> wrappers.

    """

    thetext = text

    for tag in ('theorem|proposition|lemma|corollary|definition|axiom','example','exercise','problem','question'):
        find_env = r"\s*<(" + tag + r")\b([^>]*)>\s*(.*?)\s*</\s*(" + tag + r")\s*>\s*"
        thetext = re.sub(find_env, ptx_wrap_state, thetext, 0, re.DOTALL)

        thetext = re.sub(r"\s*</\s*(" + tag + r")\s*>\s*","\n" + r"</\1>" + "\n\n", thetext)

        thetext = re.sub(r"\s*<(" + tag + r")\b([^>]*)>\s*","\n\n" + r"<\1\2>" + "\n", thetext)

    return thetext

def ptx_wrap_state(txt):

    opening_tag = txt.group(1)
    opening_parameters = txt.group(2)
    environment_body = txt.group(3).strip()
    closing_tag = txt.group(4)

    if opening_tag != closing_tag:
        logging.error("tag mismatch: %s and %s", opening_tag, closing_tag)
        return txt.group(0)

    elif "<statement>" in environment_body:
        logging.info("environment already contains <statement>")
        return txt.group(0)

    logging.debug("wrapping statement on %s", environment_body)

    if environment_body.startswith("<title>"):
        the_title, environment_body = utilities.text_before(environment_body, "</title>")
        the_title += "</title>"
        environment_body = environment_body[8:]  # remove </title>
    else:
        the_title = ""


    # figure out the general case and rewrite this cleanly.
    # can there be more than one "extra"?
    if environment_body.endswith("</proof>"):
        environment_body, environment_extras = utilities.text_before(environment_body, "<proof")
    elif environment_body.endswith("</solution>"):
        environment_body, environment_extras = utilities.text_before(environment_body, "<solution")
    elif environment_body.endswith("</answer>"):
        environment_body, environment_extras = utilities.text_before(environment_body, "<answer")
    elif environment_body.endswith("</hint>"):
        environment_body, environment_extras = utilities.text_before(environment_body, "<hint")
    else:
        environment_extras = ""

    the_answer = "<" + opening_tag + opening_parameters + ">"
    the_answer += the_title
    the_answer += "<statement>" + environment_body + "</statement>" 
    the_answer += environment_extras
    the_answer += "</" + closing_tag + ">" 

    return the_answer

###################

def ptx_wrap_p(txt):
    """ Wrap the contents in <p>, if it isn't already.

    """

    # not implemented yet

    return txt

###################

def ptx_wrap_CDATA(text):
    """ Wrap CDATA around some environments.

    """

    logging.debug("in ptx_wrap_CDATA: %s", text[:20])

    thetext = text

    for tag in ['overpic','tikzpicture', 'circuitikz']:
        thetext = re.sub(r"\s*(\\begin{" + tag + r"})", "\n<image>\n<latex-image>\n          <![CDATA[" + r"\1", thetext)
        thetext = re.sub(r"(\\end{" + tag + "})\s*", r"\1" + "]]>\n</latex-image>\n</image>\n", thetext)

    return thetext


###################

def ptx_change_math_markup(text):
    """ Switch back to $ delimiters in certain cases, and other.

    """

    thetext = text

    thetext = re.sub("<latex-image>(.*?)</(latex-image)>",ptx_change_math_mk,thetext,0,re.DOTALL)

    thetext = re.sub("<mrow>(.*?)</(mrow)>",ptx_change_math_mk,thetext,0,re.DOTALL)

    thetext = re.sub("<me>(.*?)</(me)>",ptx_change_math_mk,thetext,0,re.DOTALL)
    thetext = re.sub("<men>(.*?)</(men)>",ptx_change_math_mk,thetext,0,re.DOTALL)
    thetext = re.sub("<m>(.*?)</(m)>",ptx_change_math_mk,thetext,0,re.DOTALL)

    thetext = re.sub(r"\\text\{([^{}]+)(\})",ptx_change_math_mk,thetext,0,re.DOTALL)

    return thetext

#-----------------#

def ptx_change_math_mk(txt):

    the_text = txt.group(1)
    the_marker = txt.group(2)

    # problem with <m>...\text{...<m>...</m>}...</m>
    if the_marker != 'm':
        the_text = re.sub("<m>",r"\(",the_text)
        the_text = re.sub("</m>",r"\)",the_text)

    the_text = re.sub("<nbsp */>",r"\ ",the_text)

    if the_marker == "}":
        return r"\text{" + the_text + "}"

    else:
        return "<" + the_marker + ">" + the_text + "</" + the_marker + ">"

###################

def ptx_change_figure_wrapping(text):
    """ change figure --> tabular   to   table --> tabular

    """

    thetext = text

    thetext = re.sub("<figure(.*?)</figure>",ptx_change_figure_wrap,thetext,0,re.DOTALL)

    return thetext

#------------------#

def ptx_change_figure_wrap(txt):

    the_text = txt.group(1)

    if "<tabular" in the_text and "<figure" not in the_text:
        return "<table" + the_text + "</table>"

    else:
        return "<figure" + the_text + "</figure>"

###################

def ptx_unwrap_sidebyside(text):
    """ remove sidebyside when it only contins one list

    """

    thetext = text

    thetext = re.sub("\s*<sidebyside>\s*<ol(.*?)</ol>\s*</sidebyside>\s*",ptx_unwrap_sbs,thetext,0,re.DOTALL)

    return thetext

#------------------#

def ptx_unwrap_sbs(txt):

    the_text = txt.group(1)

    if "<ol" in the_text:
        return "\n<sidebyside>\n<ol" + the_text + "</ol>\n</sidebyside>\n"

    else:
        return "\n<ol" + the_text + "</ol>\n"

##################

def ptx_unwrap_p_images(text):
    """ images should be outside p

    """

    thetext = text

    # this seems to have mabe imbalanced p tags
    # thetext = re.sub(r"\s*<p>\s*<!-- START","\n\n" + "<!-- START",thetext)
    # thetext = re.sub(r"END -->\s*</p>\s*","END -->\n\n",thetext)

    thetext = re.sub(r"\s*<p>\s*<!-- START(.*?)END -->\s*</p>\s*", ptx_unwrap_p_im, thetext, 0, re.DOTALL)

    return thetext

#------------#

def ptx_unwrap_p_im(txt):

    thetext = txt.group(1)

    if "<!-- START" in thetext:
        return "\n<p>\n<!-- START" + r"\1" + "END -->\n</p>\n"

    else:
        return "\n<!-- START" + r"\1" + "END -->\n"

###################

def ptx_fixworkspace(txt):

   the_tag = txt.group(1)
   the_text = txt.group(2)

   if "<solution" in the_text and "<statement" not in the_text:
       the_text = re.sub("(.*)<solution", "<statement>" + r"\1" + "</statement>\n<solution", the_text, 1, re.DOTALL)

   if "flexskip" not in the_text:
       return "<" + the_tag + ">" + the_text + "</" + the_tag + ">"
   else:
 #      print "             flexskip"
 #      print the_text
       the_skip = re.search(r"\\flexskip{([^{}]+)}",the_text).group(1)
       the_text = re.sub(r"\\flexskip{([^{}]+)}", "", the_text)

   return '<' + the_tag + ' workspace="' + the_skip + '0%">' + the_text + '</' + the_tag + '>'

###################

def fix_various_tags(text):

    the_text = text

    # br at end of p is meaningless
    the_text = re.sub(r"\s*<br */>\s*</p>","\n</p>",the_text)
    # or at end of li
    the_text = re.sub(r"\s*<br */>\s*</li>","</li>",the_text)
    # or before ol or ul
    the_text = re.sub(r"\s*<br */>\s*<(ol|ul)",r"\n<\1",the_text)
    # br before beginning or at end of anything is meaningless
    the_text = re.sub(r"\s*<br */>\s*\\(begin|end){","\n\\\1{",the_text)
#    the_text = re.sub(r"\s*<br */>\s*\\begin{","\n\\begin{",the_text)
#    the_text = re.sub(r"\s*<br */>\s*\\end{","\n\\end{",the_text)
    # br is the wrong way to arrange images
    the_text = re.sub(r"\s*<br */>\s*<image","\n<image",the_text)
    the_text = re.sub(r"<image ([^>]+)>\s*<br */>\s*",r"<image \1>" + "\n",the_text)
    # or figures
    the_text = re.sub(r"\s*<br */>\s*<figure","\n<figure",the_text)

    the_text = re.sub(r"\\addtocontents\{[^{}]*\}","",the_text)

    the_text = re.sub(r"\\renewcommand\{\s*\}\{[^{}]*\}","",the_text)
    the_text = re.sub(r"\\renewcommand\{\s*\}","",the_text)
    the_text = re.sub(r"\\newcommand\{\s*\}\{[^{}]*\}","",the_text)
    the_text = re.sub(r"\\newcommand\{\s*\}","",the_text)

 #   if "outcomes" in the_text:
 #        print "found objectives", the_text
    the_text = re.sub(r"<p>\s*\\begin\{(objectives|outcomes)\}\s*\[([^\[\]]+)\]\s*</p>",r"<\1><title>\2</title>",the_text)
    the_text = re.sub(r"<p>\\begin\{(objectives|outcomes|project|investigation|exploration|annotation|program|commentary|project)\}\s*</p>",r"<\1>",the_text)
    the_text = re.sub(r"<p>\s*\\end\{(objectives|outcomes|project|investigation|exploration|annotation|program|commentary|project)\}\s*</p>",r"</\1>",the_text)
    the_text = re.sub(r"\\begin\{(objectives|outcomes|project|investigation|exploration|annotation|program|commentary|project)\}",r"<\1>",the_text)
    the_text = re.sub(r"\\end\{(objectives|outcomes|project|investigation|exploration|annotation|program|commentary|project)\}",r"</\1>",the_text)

    the_text = re.sub(r"\\normalfont\b","",the_text)

    the_text = re.sub(r"<(em|idx|h)>\s+",r"<\1>",the_text)
    the_text = re.sub(r"\s+</(em|idx|h)>",r"</\1>",the_text)

    # center is not longer an extracted environment, so now need to remove it by hand
    the_text = re.sub(r"\\begin\s*\{center\}\s*","",the_text)
    the_text = re.sub(r"\\end\s*\{center\}\s*","",the_text)

    # argument of text shoudl start and end with a space
    # and should not contain \ or \,
    the_text = re.sub(r"\\text\{\s*\\(,| )",r"\\text{ ",the_text)
    the_text = re.sub(r"\\text\{([^{} ][^{}]+)\}",r"\\text{ \1}",the_text)
    the_text = re.sub(r"\\text\{([^{}]+[^{} ])\}",r"\\text{\1 }",the_text)

    # delete paragraphs with useless content
#    the_text = re.sub(r"\s*(<p>|<p id[^<>]+>)\s*</p>\s*","\n",the_text)
    the_text = re.sub(r"\s*(<p>|<p id[^<>]+>)(\{|\}|\s)*</p>\s*","\n",the_text)
#    # is this too agressive?  (covers the above two cases)
#    the_text = re.sub(r"\s*<p>[^a-zA-Z0-9]*</p>\s*","\n",the_text)

    # temporary for Anne Schilling's book
    the_text = re.sub(r"\\squaresize\s*=\s*[0-9a-z]+\s*", "\n", the_text)

    the_text = re.sub(r"\s*(\\mbox|\\hbox){\s*}\s*","",the_text)


    return the_text

def ptx_fix_various_tags(text):  # including particular authors

    the_text = text

# the first thing is a hack to replace me/md  by  men/mdn  in the
# case where there is an xml:id .  This should be caught earlier
    the_text = re.sub("<me (xml:id.*?)</me>", r"<men \1</men>", the_text, 0, re.DOTALL)
    the_text = re.sub("<md (xml:id.*?)</md>", r"<mdn \1</mdn>", the_text, 0, re.DOTALL)
#    if component.writer.lower() in ["geochem"]:
#        the_text = re.sub(r"\bmd>", r"men>", the_text)

    # tags which are no longer special in ptx
    the_text = re.sub("<hash */>", "#", the_text)
    the_text = re.sub("<percent */>", "%", the_text)
    the_text = re.sub("<dollar */>", "$", the_text)
    the_text = re.sub(r"\\dollar\b", "$", the_text)
    the_text = re.sub("<ampersand */>", "&amp;", the_text)

    the_text = utilities.replacemacro(the_text,"code",1, r'<c>#1</c>')

#    the_text = re.sub(r"<p>\s*\\begin{(program)}", r"<\1>", the_text)
#    the_text = re.sub(r"\\end{(program)}\s*</p>", r"</\1>", the_text)
#    the_text = re.sub(r"\\begin{(program)}", r"<\1>", the_text)
#    the_text = re.sub(r"\\end{(program)}", r"</\1>", the_text)


    # if the width is more than 100%, set to 92.5%
    the_text = re.sub(r'width="[1-9][0-9][0-9][.0-9]*%"', 'width="92.5%"', the_text)

    the_text = re.sub("_<ndash/>_", "_-_", the_text)
    the_text = re.sub("_-_", "___", the_text)

    the_text = re.sub(r"<=", r"&lt;=", the_text) 

    the_text = re.sub(r"<p>\s*\\paragraphs{([^{}]*)}\s*</p>",r"<paragraphs><title>\1</title>",the_text)
    the_text = re.sub(r"<p>\s*\\endparagraphs\s*</p>",r"</paragraphs>",the_text)


    the_text = re.sub(r"<p>\s*\\paragraphs{([^{}]*)}\s*(.*?)</p>",r"<paragraphs><title>\1</title><p>\2</p></paragraphs>",the_text,0, re.DOTALL)

#    the_text = re.sub(r"&Scaron;",r"Š",the_text)
    the_text = re.sub(r"&Scaron;",r"S",the_text)  #wrong!
    the_text = re.sub(r"&scaron;",r"s",the_text)  #wrong!
    the_text = re.sub(r"&ccaron;",r"c",the_text)  #wrong!
    the_text = re.sub(r"&cacute;",r"c",the_text)  #wrong!

    the_text = re.sub(r"myampersand",r"&amp;",the_text)
    the_text = re.sub(r"<p>\s*startofproof\s*</p>",r"<proof>",the_text)
    the_text = re.sub(r"<p>\s*endofproof\s*</p>",r"</proof>",the_text)

# from beamer, and others
    the_text = re.sub(r"<p>\s+\\alert{([^{}]+)}\.?\s*(.*?)</p>",
                      r"<paragraphs><title>\1</title><p>\2</p></paragraphs>",
                       the_text, 0, re.DOTALL)
    the_text = re.sub(r"<p>\s*<paragraphs>", "<paragraphs>", the_text)
    the_text = re.sub(r"</paragraphs>\s*</p>", "</paragraphs>", the_text)

    if component.writer.lower() in ["mckenna"]:
        the_text = re.sub("&([a-zA-Z]+( |\\||\\\\|/|\n|\t|&|,|\(|\.))", r"&amp;\1", the_text)
        the_text = re.sub("&([a-zA-Z]+( |\\||\\\\|/|\n|\t|&|,|\(|\.))", r"&amp;\1", the_text)

    if component.writer == "javajavajava":
        the_text = re.sub(r'<lt/>', r'&lt;', the_text)
        the_text = re.sub(r'\[\[\[', r'&lt;', the_text)
        the_text = re.sub(r'\]\]\]', r'&gt;', the_text)
        the_text = re.sub(r'\\PeRcEnT', r'%', the_text)
        the_text = re.sub(r'PeRcEnT', r'%', the_text)
        the_text = re.sub(r'<[%]', r'&lt;%', the_text)
        the_text = re.sub(r'[%]>', r'%&gt;', the_text)

    if component.writer == "yong":
        the_text = re.sub(r'<sq>ohana', r'`ohana', the_text)
        the_text = re.sub(r'Honua voyage and it</sq>', r"Honua voyage and it'", the_text)
        the_text = re.sub(r'month=3&year', r'month=3&amp;year', the_text)
        the_text = utilities.replacemacro(the_text,"url", 1, r'"<url href="\1"/>')

    if component.writer == "mulberry":
        the_text = re.sub(r'(<image width=)"[0-9]+%"', r'\1"60%"', the_text)
        the_text = re.sub(r'<image>"', '<image width="60%">', the_text)
        the_text = re.sub(r'<([\-0-9]+pt)', r'&lt;\1', the_text)
        the_text = re.sub(r'([\-0-9]+pt)>', r'\1&gt;', the_text)
        # twice, because of <4pt> .  Better way?
        the_text = re.sub(r'<([\-0-9]+pt)', r'&lt;\1', the_text)
        the_text = re.sub(r'([\-0-9]+pt)>', r'\1&gt;', the_text)
        the_text = re.sub(r'<([\-0-9.]+true)', r'&lt;\1', the_text)
        the_text = re.sub(r'(true(mm|cm|in))>', r'\1&gt;', the_text)
        the_text = re.sub(r'<([\-0-9.]+(mm|cm|in))', r'&lt;\1', the_text)
        the_text = re.sub(r'([\-0-9.]+(mm|cm|in))>', r'\1&gt;', the_text)

    if component.writer == "doob":
        the_text = re.sub(r'(<section xml:id="[^"]+F")', r'\1 xml:lang="fr-FR"', the_text)
        the_text = re.sub(r'<problem (.*?)</problem>', makesolidunique, the_text,0, re.DOTALL)
        the_text = re.sub(r'\\textit{Solution by ([^{}]+)}', r"<author>\1</author>", the_text)
        the_text = re.sub(r'\\textit{([^{},]+,[^{}]+)}', r"<author>\1</author>", the_text)
#        the_text = re.sub(r'&#xea;', r"ê", the_text)
#        the_text = re.sub(r"\\'e", r"é", the_text)
#        the_text = re.sub(r"\\`e", r"è", the_text)

    if component.writer == "zbornik":
        the_text = re.sub(r'\\itemtitle{([^{}]*)}', r'<title>\1</title>', the_text)

    if component.writer == "thron":
        the_text = re.sub(r'\\vvideohref{[^{}]+?list=([^&{}]+)&*[^{}]*}(</title>)',
                      r'\2<figure><video youtubeplaylist="\1"/></figure>' ,the_text)
   # next should not happen
        the_text = re.sub(r'(\\vvideohref{[^{}]+})', lambda match: utilities.replacein(match,r"&",r"&amp;"),the_text)

        for letter in ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S']:
            the_text = re.sub(r'id="exercise_further_crypt_"', 'id="exercise_further_crypt_' + letter + '"',
                              the_text, 1)
        for repid in ['(id="sec_ECA2)"', '(id="example_EquivalenceRelationsChap_bbal)"', '(id="DrawBinRelExer-son)"', '(id="DrawBinRelExer-sister)"', '(id="DrawBinRelExer-married)"', '(id="DrawBinRelExer-lived)"', '(id="DrawBinRelExer-son)"', '(id="DrawBinRelExer-sister)"', '(id="EquivRelComplex1)"', '(id="exercise_isomorph_prodCycProp)"', '(id="exercise_rings_zdzp)"', '(id="additive_table)"', '(id="example_bases_121_base_3)"', '(id="exercise_crypt_brute)"', '(id="example_poly_poly_division)"', '(id="exercise_poly_complexroots)"', '(id="exercise_symmetries_Darb)"', '(id="exercise_further_crypt_D)"', '(id="DrawBinRelExer-sonX)"', '(id="DrawBinRelExer-sisterX)"']:
            the_text = re.sub(repid, r'\1X"', the_text, 1)
    if component.writer == "sundstrom":
        the_text = re.sub(r'preview activity>', r'exploration>', the_text)
        the_text = re.sub(r'<preview activity', r'<exploration', the_text)
        the_text = re.sub(r'&fcirc;', r'composition ', the_text)

    if component.writer == "morris":
        the_text = re.sub(r'<li class="custom-list-style-type" label=" (.{,80})\)" >', r'<li><title>\1</title>', the_text)
        the_text = re.sub(r'\solutionsfor{([^{}]+)}', r'Solutions for <xref ref="\1"/>', the_text)
        the_text = re.sub(r'\exersoln{([^{}]+)}', r'<xref ref="\1"/>', the_text)

    if component.writer == 'apex':
        the_text = re.sub("<key idea","<keyidea",the_text)
        the_text = re.sub("key idea>","keyidea>",the_text)
        the_text = re.sub("Key <xref ([^>]+)>",r"<xref \1>Key ",the_text)
        the_text = re.sub("keyidea","insight",the_text)
        the_text = utilities.replacemacro(the_text,"apexincludegraphics",1, r'<img src="#1"/>')

    if component.writer == 'active':
        the_text = re.sub("<preview activity","<previewactivity",the_text)
        the_text = re.sub("preview activity>","previewactivity>",the_text)
        the_text = re.sub("Preview <xref ([^>]+)>",r"<xref \1>Preview ",the_text)
        the_text = re.sub("previewactivity","exploration",the_text)
        the_text = re.sub("\.png","",the_text)

    the_text = re.sub(r"\\begin{genericpreformat}\s*\[([^\[\]]+)\]", r'<pre class="\1">',the_text)
    the_text = re.sub(r"\\begin{genericpreformat}",'<pre>',the_text)
    the_text = re.sub(r"\\end{genericpreformat}","</pre>",the_text)

    if component.writer == 'schmitt':
        the_text = re.sub("<challenge","<exploration",the_text)
        the_text = re.sub("challenge>","exploration>",the_text)
        the_text = re.sub("<problem","<exploration",the_text)
        the_text = re.sub("problem>","exploration>",the_text)
        the_text = re.sub("<exercise","<exploration",the_text)
        the_text = re.sub("exercise>","exploration>",the_text)
        the_text = re.sub(r"\\ensuremath","",the_text)

    if component.writer == 'mahavier':
        the_text = re.sub("{xxpicture}","{picture}",the_text)
        the_text = re.sub(r"<p>\s*(<figure[^>]*>\s*<caption>.*?</caption>)\s*</p>",
                          "\n\n" + r"\1" + "\n", the_text)
        the_text = re.sub(r"\s*(<p>)\s*(</figure>)\s*", "\n" + r"\2" + "\n\n" + r"\1" + "\n", the_text)
        the_text = re.sub(r"<p>\s*</p>", "", the_text)

    if component.writer == 'bartlett':
       pass
#       the_text = re.sub(r"\\begin{ramanujansays}", r"<assemblage>", the_text)
#       the_text = re.sub(r"\\end{ramanujansays}", r"</assemblage>", the_text)
#
#       the_text = re.sub(r"<p>\s*<assemblage>","<assemblage>\n<p>", the_text)
#       the_text = re.sub(r"</assemblage>\s*</p>","</p>\n</assemblage>", the_text)
#
#       the_text = re.sub(r"</assemblage>\s*<assemblage>","", the_text)

    if component.writer in ['exam', 'rosoff']:
        the_text = re.sub(r"<(subtask)>(.*?)</\1>", ptx_fixworkspace, the_text, 0, re.DOTALL)
        the_text = re.sub(r"<(task)>(.*?)</\1>", ptx_fixworkspace, the_text, 0, re.DOTALL)
        the_text = re.sub(r"<(exercise)>(.*?)</\1>", ptx_fixworkspace, the_text, 0, re.DOTALL)

        the_text = re.sub(r"\s*<p>\s*\\(begin|end){(sidebyside|parts)}\s*</p>\s*", "\n\n", the_text)
        the_text = re.sub(r"\s*\\(begin|end){(sidebyside|parts)}\s*", "\n\n", the_text)

        if "\\flexskip" in the_text:
            print("ERROR: \\flexskip in", component.inputfilename)

  #      the_text = re.sub(r"<subtask","<task",the_text)
  #      the_text = re.sub(r"subtask>","task>",the_text)

        the_text = re.sub(r"\\flexskip{[^{}]*}","",the_text)
        the_text = re.sub(r"\\answerline\b","",the_text)

           # structural figures should already be converted
        the_text = re.sub(r"\\begin{figure}\[.*?\]","",the_text)
        the_text = re.sub(r"\\end{figure}","",the_text)

        the_text = re.sub(r'<section (xml:id="([^"]*)")>\s*<title>xx</title>\s*<p>\s*<worksheet>\s*<title>Missing Title</title>',
                            r'<worksheet \1>', the_text)
        the_text = re.sub(r'</worksheet>\s*</p>\s*</section>', '</worksheet>', the_text)

    if component.writer == 'openintro':
        the_text = utilities.replacemacro(the_text,"vvideohref",1, r"MISSINGVIDEOLINK #1")
  #      the_text = utilities.replacemacro(the_text,"answer",1, r"<answer>#1</answer>")
        the_text = re.sub(r"(\s*)<p>\s*\\begin{onebox}\s*{([^{}]+)}", r"\1<assemblage><title>\2</title>" + "\n<p>\n", the_text)
        the_text = re.sub(r"(\s*)<p>\s*\\begin{onebox}", r"\1<assemblage>" + "\n<p>\n", the_text)
        the_text = re.sub(r"\\begin{onebox}", r"</p><assemblage>" + "\n<p>\n", the_text)
        the_text = re.sub(r"\\end{onebox}\s*</p>\s*", "\n</p>\n</assemblage>\n", the_text)
        the_text = re.sub(r"\\end{onebox}", "\n</p>\n</assemblage>\n<p>\n", the_text)
        the_text = re.sub(r"<table", "<figure", the_text)
        the_text = re.sub(r"</table", "</figure", the_text)
        the_text = re.sub(r"\|textbf", "", the_text)
        the_text = re.sub(r"<-", "&lt;-", the_text)
        the_text = re.sub(r"\\mbox{\\texttt{([^{}]*)}}", r"<c>\1</c>", the_text)

    the_text = re.sub(r'<c>(.*?)</c>', ptx_fix_c, the_text, 0, re.DOTALL)

    if component.writer == 'bogart':
        the_text = re.sub("<problem([^>]*)>\s*<p>\s*\(([^\)]+)\)\s*",
            r'<problem\1 category="\2">' + '\n<p>\n',the_text)

    if component.writer in ['sally', 'phys211', 'phys212']:
        the_text = utilities.replacemacro(the_text,"boxittext",1, r"<assemblage><p>#1</p></assemblage>")
        # not sure why the extension is .png instead of .svg (and why the png files contain svg content)
        the_text = re.sub('\.png"', '"', the_text)
        the_text = re.sub('\.</title>', '</title>', the_text)

    # math mode labels not allowed (because they are parameters)
#### maybe they are allowed in PreTeXt, so comment out???
    #  the_text = re.sub(' label="<.*?"',' label="invalidlabel"',the_text)

    the_text = re.sub(r"\\notag\b","",the_text)
    the_text = re.sub(r"\\quad\b","",the_text)
    the_text = re.sub(r"\\hfill\b","",the_text)
    the_text = re.sub(r"\\null\b","",the_text)

# chemistry
    the_text = re.sub(r"\\begin{reaction\*?}",r'<me class="reaction">',the_text)
    the_text = re.sub(r"\\end{reaction\*?}",r'</me>',the_text)
    the_text = re.sub(r"\\begin{reactions\*?}",r'<md class="reaction">',the_text)
    the_text = re.sub(r"\\end{reactions\*?}",r'</md>',the_text)

# careful, because can occur in math mode
#    the_text = utilities.replacemacro(the_text,"ch",1, r'<m class="chem">#1</m>')



    the_text = re.sub(r"<u>\s*</u>","<fillin/>",the_text)
    the_text = re.sub(r"<u>","<em>",the_text)
    the_text = re.sub(r"</u>","</em>",the_text)
    the_text = re.sub(r"<sup>\s*\\textregistered\s*</sup>","<trademark/>",the_text)

    # maybe these should be earlier, in a [square bracket], because they might
    # end up inside the statement or a paragraph?
    the_text = utilities.replacemacro(the_text,"exercisetitle",1, r"<title>#1</title>")
    # only occurs in openintro
    the_text = utilities.replacemacro(the_text,"tipBoxTitle",1, r"<title>#1</title>")

    the_text = re.sub(r"<nbsp/>(</title>)", r"\1", the_text)
    the_text = re.sub(r"<nbsp/>(</title>)", r"\1", the_text)
    the_text = re.sub(r" +(</title>)", r"\1", the_text)


    #the_text = re.sub(r"&($|[^a-zA-Z#])",r"<amp />\1",the_text)
    # apparently it should be
    the_text = re.sub(r"&($|[^a-zA-Z#])",r"&amp;\1",the_text)
        # twice, for &&
    the_text = re.sub(r"&($|[^a-zA-Z#])",r"&amp;\1",the_text)
    the_text = re.sub(r"< ",r"&lt; ",the_text)

    the_text = re.sub(r"&copy;",r"<copyright/>",the_text)
    the_text = re.sub(r"\\textregistered",r"<registered/>",the_text)

    the_text = re.sub(r"\\calckey([^{])",r"\\calckey{\1}",the_text)
    the_text = utilities.replacemacro(the_text,"calckey",1, r"<kbd>#1</kbd>")

    #\text{} only containing math, should not be wrapped in \text{}
    the_text = re.sub(r"\\text\{\s*\$([^{}\$]+)\$\s*(\.*)\s*\}",r"$\1$\2",the_text)

    # delete paragraphs with useless content
    the_text = re.sub(r"\s*<p>\s*</p>\s*","\n",the_text)
    the_text = re.sub(r"\s*<p>\s*\{\s*</p>\s*","\n",the_text)
    # is this too agressive?  (covers the above two cases)
    the_text = re.sub(r"\s*<p>[^a-zA-Z]*</p>\s*","\n",the_text)

    the_text = utilities.replacemacro(the_text,"href",2,
                                      '<url href="#1">#2</url>')
    # hash in target URL should be literal hash
    the_text = re.sub(r'href="([^"]*)<hash */>([^"]*)"',r'href="\1#\2"',the_text)
    # but & should be &amp;
    # This is dangerous, because applying it twice makes nonsense
    # need a way to thwart the second substitution
    the_text = re.sub(r'href="([^"]*)<nbsp */>([^"]*)"',r'href="\1~\2"',the_text)
  #  the_text = re.sub(r'href="([^"]*)&([^"]*)"',r'href="\1&amp;\2"',the_text)
    the_text = re.sub(r'(href="[^"]*")', lambda match: utilities.replacein(match,r"&",r"&amp;"),the_text)
    the_text = re.sub(r'(href="[^"]*")', lambda match: utilities.replacein(match,r"<percent/>",r"%"),the_text)

    the_text = utilities.replacemacro(the_text,"intertext",1,
        "</mrow>" + "\n" + r"<intertext>#1</intertext>" + "\n" + "<mrow>")
    # above makes empty <mrow></mrow> , which are then deleted
    the_text = re.sub(r"\s*<mrow>\s*</mrow>\s*","\n",the_text)

    the_text = re.sub(r"<intertext>(.*?)</intertext>",fixintertext,the_text,0,re.DOTALL)

    if component.writer == 'oscarlevin':
        the_text = re.sub(r"<m>\\gls\{([^{}]+)\}</m>",r"<m>\\\1</m><idx><h><m>\\\1</m></h></idx>",the_text)
        the_text = re.sub(r"\\gls\{([^{}]+)\}",r"<m>\\\1</m><idx><h><m>\\\1</m></h></idx>",the_text)
    else:  # this occurs in Chris Hughes' ORCCA source
        the_text = re.sub(r"\\(Gls|gls)\{([^{}]+)\}",r"\2<idx><h>\2</h></idx>",the_text)

    return the_text

###################
def ptx_fix_c(txt):

    the_content = txt.group(1)

    print("in ptx_fix_c the_content was", the_content)

    the_content = re.sub("<nbsp */*>", " ", the_content)
    the_content = re.sub("</*b>", "", the_content)
    the_content = re.sub("</*em>", " ", the_content)
    the_content = re.sub("</*fillin */*>", "____", the_content)
    the_content = re.sub("</*m>", " ", the_content)  # how to handle math in c?

    print("in ptx_fix_c the_content is", the_content)
    return "<c>" + the_content + "</c>"

###################
def ptx_remove_empty_tags(text):

    the_text = text

    # remove empty p paragraphs
    the_text = re.sub(r"\s*<p>\s*</p>\s*","\n",the_text)
    the_text = re.sub(r"\s*<p>\s*<nbsp\s*/>\s*</p>\s*","\n",the_text)

    # and empty index entries
    the_text = re.sub(r"\s<idx><h>\s*</h></idx>\s*","\n",the_text)

    return the_text

###################

def makesolidunique(txt):

    the_text = txt.group(1)

    abcs = ["a", "b", "c", "d", "e", "f", "g", "h", "i"]

    try:
        first_sol_id = re.search(r'<solution xml:id="([^"]+)"', the_text).group(1);
        print("found solution id", first_sol_id)

        for j in range(0,8):
            the_text = re.sub(r'<solution xml:id="' + first_sol_id + '"', r'<solution xml:id="\1' + abcs[j] + '"', the_text, 1)
    except:
        print("no solution in", the_text)

    return '<problem ' + the_text + '</problem>'

###################


def fixintertext(txt):
    # a crude way to patch up intertext, which had been hidden in a math environment

    the_text = txt.group(1)

    the_text = utilities.tex_to_ptx_fonts(the_text)

    while r"$" in the_text:
        the_text = re.sub("\$","<m>",the_text,1)
        the_text = re.sub("\$","</m>",the_text,1)

    the_text = re.sub(r"\\\(","<m>",the_text)
    the_text = re.sub(r"\\\)","</m>",the_text)

    return "<intertext>" + the_text + "</intertext>"

###################

# rename this because it has nothing to do with br
def ptx_fix_p_and_br_in_li(text):

    the_text = text

    the_text = re.sub(r'<li\s+class="[^"]*"\s+label="([^"]+)"\s*>',r"<li><title>\1</title>",the_text)
    the_text = re.sub('\.</title>', '</title>', the_text)

    # bug if li has parameters
#    the_text = re.sub(r"<li\b([^<>]*)>(.*?)(</li>|<ul>|<ol>)",fix_li,the_text,0,re.DOTALL)
    the_text = re.sub(r"<li\b([^<>]*)>(.*?)(</li>|<ul\b[^>]*>|<ol\b[^>]*>)",fix_li,the_text,0,re.DOTALL)

    return the_text

###################

def fix_li(txt):

    the_param = txt.group(1)
    the_text = txt.group(2)
    the_ending_tag = txt.group(3)

    the_text = the_text.strip()

    if not the_text:
        pass   # nothing to do, except return the enclosing tags
    elif the_text.startswith("<p>"):
        pass     # already in <p> so don't do anything
    else:
        the_text = "<p>" + the_text + "</p>"

    return "<li" + the_param + ">" + the_text + the_ending_tag

################

def ptx_fix_hint(text):
    """ Maybe make a version of this that is like ptx_fix_p_and_br_in_li

    """

    the_text = text

    the_text = re.sub(r"<(hint|solution)>(.*?)</\1>", ptx_fix_hi, the_text, 0, re.DOTALL)

    return the_text

def ptx_fix_hi(txt):

    the_tag = txt.group(1)
    the_inside = txt.group(2)

# need to make this more robust

    the_answer = "<" + the_tag + ">" + the_inside + "</" + the_tag + ">"

    the_inside = the_inside.strip()

    if the_inside.startswith("<ol") and the_inside.endswith("ol>"):
        the_inside = "\n" + "<p>" + the_inside + "</p>\n"
        the_answer = "<" + the_tag + ">" + the_inside + "</" + the_tag + ">"

    return the_answer

################

def ptx_fix_answer(text):
    """ answer should contain paragraphs.  not sure why they don't
        probably the issue is when they are jsut one formula
    """

    the_text = text

    # check this does not introduce errors on longer answers
    # the_text = re.sub(r"<answer>\s*(<m.*?)\s*</answer>","<answer>\n<p>" + r"\1" + "</p>\n</answer>",the_text,0,re.DOTALL)
    for tag in ['answer','blockquote']:
        the_text = re.sub("<" + tag + r">\s*(<m.*?)\s*</" + tag + ">",
                          "<" + tag + ">\n<p>" + r"\1" + "</p>\n</" + tag + ">",
                          the_text,0,re.DOTALL)

    return the_text

###################

def convert_br_to_line(txt_or_text):

    # could be called in a re.sub or as function
    try:
        thetext = txt_or_text.group(1)
    except AttributeError:
        thetext = txt_or_text

    thetext = re.sub("<br +/>", "<br/>", thetext)

    if "<br/>" not in thetext:
        return thetext

    if "ul>" in thetext or "ol>" in thetext or "<sidebyside" in thetext:
        thetext = re.sub("<br */>","\n",thetext)
        return thetext

    logging.debug("replacing <br */> by <line>s\n %s \n============", thetext)

    lines = thetext.split("<br/>")

    ans = ""
    for line in lines:
        if line:
            ans += "<line>" + line.strip() + "</line>" + "\n"

    return ans

###################

def put_math_in_paragraphs(text):

    thetext = text

    thetext = re.sub(r"</p>\s*<(me|men|md|mdn)\b(.*?)</\1>\s*","\n" + r"<\1" + r"\2" + r"</\1>" + "\n" + "</p>" + "\n", thetext, 0, re.DOTALL)
    # think about whether that needs to be done twice, when there are successive alternating blocks

    # yes, do it twice!
    thetext = re.sub(r"</p>\s*<(me|men|md|mdn)\b(.*?)</\1>\s*","\n" + r"<\1" + r"\2" + r"</\1>" + "\n" + "</p>" + "\n", thetext, 0, re.DOTALL)
    # actually, three times!
    thetext = re.sub(r"</p>\s*<(me|men|md|mdn)\b(.*?)</\1>\s*","\n" + r"<\1" + r"\2" + r"</\1>" + "\n" + "</p>" + "\n", thetext, 0, re.DOTALL)
    # or 4!
    thetext = re.sub(r"</p>\s*<(me|men|md|mdn)\b(.*?)</\1>\s*","\n" + r"<\1" + r"\2" + r"</\1>" + "\n" + "</p>" + "\n", thetext, 0, re.DOTALL)

    # when you have words - math - words - math, is that one paragraph or two?
    # could be either, but if the second set of words starts with lower case,
    # then surely it is one big paragraph

    thetext = re.sub(r"</(me|men|md|mdn)>\s*</p>\s*<p>\s*([a-z]+)",r"</\1>" + "\n"+ r"\2", thetext, 0, re.DOTALL)

    thetext = re.sub(r"</(figure)>\s*<me>(.*?)</me>\s*",r"</\1>" + "\n<p>\n<me>" + r"\2" + "</me>\n</p>\n", thetext, 0, re.DOTALL)

    return thetext

###################

def put_lists_in_paragraphs(text):

    thetext = text

    thetext = re.sub(r"(</p>\s*<(ol|ul|dl)\b(.*?)</\2>\s*)", put_lists_in_par, thetext, 0, re.DOTALL)
    # think about whether that needs to be done twice, when there are successive alternating blocks

    # yes, do it twice! (in case of consecutive lists)
    thetext = re.sub(r"(</p>\s*<(ol|ul|dl)\b(.*?)</\2>\s*)", put_lists_in_par, thetext, 0, re.DOTALL)

    return thetext

def put_lists_in_par(txt):

    the_everything = txt.group(1)
    the_tag = txt.group(2)
    the_inside = txt.group(3)

    # problem if <ol ... <ol ... </ol>
    # so this only works for non-nested lists
    if "<" + the_tag in the_inside:
        the_answer = the_everything
#        print "skipping nested", the_tag, "in", the_inside

    else:
        the_answer = "\n" + "<" + the_tag + the_inside + "</" + the_tag + ">" + "\n" + "</p>" + "\n"

    return the_answer

###################

def ptx_put_hints_in_activities(text):
# same function put_lists_in_paragraphs
    thetext = text

    thetext = re.sub(r"(</(activity|exploration|example|exercise|question)>\s*<(hint|answer|solution)\b(.*?)</\3>\s*)", ptx_put_hints_in_act, thetext, 0, re.DOTALL)
    thetext = re.sub(r"(</(activity|exploration|example|exercise|question)>\s*<(hint|answer|solution)\b(.*?)</\3>\s*)", ptx_put_hints_in_act, thetext, 0, re.DOTALL)
    thetext = re.sub(r"(</(activity|exploration|example|exercise|question)>\s*<(hint|answer|solution)\b(.*?)</\3>\s*)", ptx_put_hints_in_act, thetext, 0, re.DOTALL)

    return thetext

def ptx_put_hints_in_act(txt):

    the_everything = txt.group(1)
    the_outer_tag = txt.group(2)
    the_inner_tag = txt.group(3)
    the_inside = txt.group(4)

    # problem if <ol ... <ol ... </ol>
    # so this only works for non-nested lists
    if "<" + the_inner_tag in the_inside:
        the_answer = the_everything
        print("skipping nested", the_tag, "in", the_inside)

    else:
        the_answer = "\n" + "<" + the_inner_tag + the_inside + "</" + the_inner_tag + ">"
        the_answer += "\n" + "</" + the_outer_tag + ">" + "\n"

    return the_answer

###################

def titles_outside_paragraphs(text):
    # fix artifact from changing li classes from html-style markup.

    thetext = text

    thetext = re.sub(r"<p>\s*<title>(.*?)</title>",r"<title>\1</title>" + "\n" + "<p>", thetext, 0, re.DOTALL)

    return thetext


###################

def ptx_normalize_whitespace(text):
    """ Normalize some white space.

    """

#
# if we want blank lines between ceratin environments, probably we need
# to first put all the starting tags at the beginning of a line, and
# then normalize all the closing tags.
#


    thetext = text

    # m should not start or end with a space
    # same for row, cell
    thetext = re.sub(r"<(m|row|cell)>\s+", r"<\1>", thetext)
    thetext = re.sub(r"\s+</(m|row|cell)>", r"</\1>", thetext)

    # me and men should be alone on a line
    # \2 is things like xml:id (which can happen for me but not men.  Think about this more.
    thetext = re.sub(r"\s*<(me|men|md|mdn)\b([^>]*)>\s*","\n" + r"<\1\2>" + "\n" + "  ", thetext)
    thetext = re.sub(r"\s*</\s*(me|men|md|mdn)\s*>\s*","\n" + r"</\1>" + "\n", thetext)

    # mrows need some carriage returns and spacing for clarity
    # note we have to do the closing tag first
  # Mitch says LaTeX does not like the carriage return at the end of the last mrow in an align
  #  thetext = re.sub(r"\s*</\s*(mrow)\s*>\s*","\n" + "      " + r"</\1>" + "\n", thetext)
    thetext = re.sub(r"\s*</\s*(mrow)\s*>\s*", r"</\1>" + "\n", thetext)
    thetext = re.sub(r"\s*<(mrow)\b([^>]*)>\s*","\n" + "  " + r"<\1\2>" + "  ", thetext)

    # p should be alone on a line (see the DTD for more things that should be here)
    thetext = re.sub(r"\s*<(p|ul|ol|dl|blockquote|pre|sidebyside|figure|table|image)>\s*",
                     "\n" + r"<\1>" + "\n", thetext)
    thetext = re.sub(r"\s*</\s*(p|ul|ol|dl|blockquote|pre|sidebyside|figure|table|image)>\s*",
                     "\n" + r"</\1>" + "\n", thetext)

    # same for theorem, statement, proof, etc
    for tag in ('theorem|proposition|lemma|corollary','proof', 'example'):
        thetext = re.sub(r"\s*</\s*(" + tag + r")\s*>\s*","\n" + r"</\1>" + "\n\n", thetext)
        thetext = re.sub(r"\s*<(" + tag + r")\b([^>]*)>\s*","\n\n" + r"<\1\2>" + "\n", thetext)

    for tag in ('statement', 'tabular'):
        thetext = re.sub(r"\s*</\s*(" + tag + r")\s*>\s*","\n" + r"</\1>" + "\n", thetext)
        thetext = re.sub(r"\s*<(" + tag + r")\b([^>]*)>\s*","\n" + r"<\1\2>" + "\n", thetext)



    # title should be one line, including tags
    thetext = re.sub(r"\s*<(title|caption)>\s*",
                     "\n" + r"<\1>", thetext)
    thetext = re.sub(r"\s*</\s*(title|caption)>\s*",
                     r"</\1>" + "\n", thetext)

    # the next two have to be in this order (think about it)
    # close (sub)sections alone on a line
    thetext = re.sub(r"\s*</\s*(chapter|section|subsection|subsubsection|introduction|exercises)>\s*",
                     "\n" + r"</\1>" + "\n", thetext)
    # space above (sub)sections
    thetext = re.sub(r"\s*<(chapter|section|subsection|subsubsection|introduction|exercises)\b([^>]*)>\s*",
                     "\n\n\n" + r"<\1\2>" + "\n", thetext)

    # rethink, because PTX uses different syntax
    # tr shold start on a new line, and /tr should be like mrow
    thetext = re.sub(r"\s*<(tr)\b([^>]*)>\s*","\n" + r"<\1\2>", thetext)
    thetext = re.sub(r"\s*</\s*(tr)\s*>\s*","\n" + "    " + r"</\1>" + "\n", thetext)


    # add some gratuitous blank lines between paragraphs and similar
    thetext = re.sub(r"\s*</(p|ul|ol)>\s*<(p|ul|ol)\b",
                     "\n" + r"</\1>" + "\n\n" + r"<\2", thetext)

    # include on its own line, flush left
    thetext = re.sub(r"\s*<(xi:include)",
                     "\n" + r"<\1", thetext)

    # p in li should not be on its own line
    thetext = re.sub(r"\s*<li>\s*<p>\s*","\n<li><p>",thetext)
    thetext = re.sub(r"\s*</p>\s*</li>\s*","</p></li>\n",thetext)
    thetext = thetext.lstrip()  # remove initial blank lines

    return thetext

#################

def ptx_revert_tikzpicture(text):
    # tikzpicture is in CDATA, so we need to un-convert things like <ndash /> to --
    # later go back at treat tikzpicture like a verbatim environment

    the_text = text

    the_text = re.sub(r"\\begin{(tikzpicture)}(.*?)\\end{tikzpicture}",ptx_revert_tikz,the_text,0,re.DOTALL)
    the_text = re.sub(r"\\begin{(circuitikz)}(.*?)\\end{circuitikz}",ptx_revert_tikz,the_text,0,re.DOTALL)

    return the_text

def ptx_revert_tikz(txt):

    thetikz = txt.group(1) # tikzpicture or circuitikz
    thetext = txt.group(2)

    thetext = re.sub(r"<mdash */>","---", thetext)
    thetext = re.sub(r"<ndash */>","--", thetext)
    thetext = re.sub(r"<nbsp */>"," ", thetext)
    thetext = re.sub(r"<amp */>","&", thetext)
    thetext = re.sub(r"<br */>","\\\\", thetext)

    return r"\begin{" + thetikz + "}" + thetext + r"\end{" + thetikz + "}"

################

def ptx_final_hacks(text):

    the_text = text

    the_text = re.sub(r"<br */>","\n",the_text)
#    the_text = re.sub(r'<li\s+class="[^"]*"\s+label="([^"]+)"\s*>',r"<li><title>\1</title>",the_text)
    the_text = re.sub(r"<b>","<em>",the_text)
    the_text = re.sub(r"</b>","</em>",the_text)

    the_text = re.sub(r"<p>\s*<pagebreak\s*/>\s*</p>","<pagebreak/>",the_text)

    the_text = re.sub(r"<m>\s*\\times\s*</m>","<times/>",the_text)
    the_text = re.sub(r"\s<ndash */>\s"," <mdash/> ",the_text)

    return the_text

##############

def ptx_paired_lists(text):

    the_text = text

    the_text = re.sub(r"\s*</ol>\s*<ol>\s*","SQUASHEDLIST\n",the_text)

    the_text = re.sub(r"<(ol|ul)>(.*?)</\1>",ptx_paired_lis,the_text,0,re.DOTALL)

    return the_text

#--------------#

def ptx_paired_lis(txt):

    list_type = txt.group(1)
    list_content = txt.group(2)

    if "SQUASHEDLIST" not in list_content:
        return "<" + list_type + ">" + list_content + "</" + list_type + ">"

    num_cols = list_content.count("SQUASHEDLIST")

    if not num_cols:
        logging.error("no num_cols in squashed list %s", list_content)
    if num_cols > 5:
        logging.error("too many columns .  possibly unrecognized nested lists", list_content)
        num_cols = 1  # meaning 2 actual columns

    list_content = re.sub("SQUASHEDLIST","",list_content)

    return '<' + list_type + ' cols="' + str(num_cols + 1) + '" >' + list_content + '</' + list_type + '>'

###################

def ptx_unwrap_sidebyside(text):
    """ If a sidebyside only contains an ol, then no reason to have the sidebyside

    """

    the_text = text

    the_text = re.sub(r"<sidebyside>\s*<sidebyside>(.*?)</sidebyside>\s*</sidebyside>",ptx_unwrap_sbs,the_text,0,re.DOTALL)

    the_text = re.sub(r"<sidebyside>(.*?)</sidebyside>",ptx_unwrap_sbs,the_text,0,re.DOTALL)

    return the_text

#----------------#

def ptx_unwrap_sbs(txt):

    thetext = txt.group(1)

    thetext = thetext.strip()

    # I think this is because of possible nested sidebysides
    if "<sidebyside" in thetext:
        return "<sidebyside>" + thetext + "</sidebyside>"

    for tag in ['ol', 'ul', 'definition', 'theorem', 'md', 'figure']:
        if (thetext.startswith("<" + tag) and thetext.count("<" + tag) == 1 and 
            (thetext.endswith(tag + ">") or thetext.endswith("index>"))):
            return thetext

    return "<sidebyside>" + thetext + "</sidebyside>"

 #   if thetext.startswith("<ol") and thetext.count("<ol") == 1 and thetext.endswith("ol>"):
 #       return thetext
 #   elif thetext.startswith("<md") and thetext.count("<md") == 1 and thetext.endswith("md>"):
 #       return thetext
 #   else:
 #       return "<sidebyside>" + thetext + "</sidebyside>"

################

def apex_exercise_group(text):

    thetext = text

    thetext = re.sub(r"<subsection(.{,30})<title>Terms and Concepts</title>",
                      r"<exercises\1" + "\n" + "<exercisegroup>" + "\n" + "<title>Terms and Concepts</title>",
                      thetext, 0, re.DOTALL)

    thetext = re.sub(r"</subsection>\s*<subsection(.{,30})<title>(Problems|Review)</title>",
                      "</exercisegroup>\n\n" + r"<exercisegroup\1" + "\n" + r"<title>\2</title>",
                      thetext, 0, re.DOTALL)

    thetext = re.sub(r"</exercise>\s*</subsection>\s*",
                      "</exercise>\n</exercisegroup>\n\n" + "</exercises>",
                      thetext, 0, re.DOTALL)

    return thetext

################

def active_hacks(text):

    return text
