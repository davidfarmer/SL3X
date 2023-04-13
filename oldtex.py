# -*- coding: utf-8 -*-

import re
import logging

import utilities
import mapping

# AMS TeX tags of the form \xxx ... \endxxx.
#
# Some of them are converted to \begin{xxx}...\end{xxx}
ams_to_beginend = ["abstract","document"]

# and some to \begin{yyy}...\end{yyy} where yyy depends on xxx
ams_to_beginend_renamed = [ ["Refs","thebibliography"] ]

# and others convert to \xxx{...}
ams_to_macro = ["title","author","address","email","keywords"]

# and some become \yyy{...} where yyy depends on xxx
ams_to_macro_renamed = [["head","section*"],
                        ["specialhead","chapter*"],   # ????
                        ["subhead","subsection*"],
                        ["subhead","subsubsection*"]
                       ]

def convert_ams_tex_math(text):

    newtext = text

    # subscripts
    newtext = re.sub(r"\\Sb\b",r"_{",newtext)
    newtext = re.sub(r"\\endSb\b",r"}",newtext)

    newtext = re.sub(r"\\Cal\b",r"\\mathcal ",newtext)

    newtext = re.sub(r"\$\$\s*\\align\b",r"\\begin{align}",newtext)
    newtext = re.sub(r"\\endalign\s*\$\$",r"\\end{align}",newtext)
    newtext = re.sub(r"\\\[\s*\\align\b",r"\\begin{align}",newtext)
    newtext = re.sub(r"\\endalign\s*\\\]",r"\\end{align}",newtext)
    newtext = re.sub(r"\$\$\s*\\aligned\b",r"\\begin{align}",newtext)
    newtext = re.sub(r"\\endaligned\s*\$\$",r"\\end{align}",newtext)
    newtext = re.sub(r"\\\[\s*\\aligned\b",r"\\begin{align}",newtext)
    newtext = re.sub(r"\\endaligned\s*\\\]",r"\\end{align}",newtext)

#3x    for tag in ["cases", "matrix", "vmatrix", "smallmatrix"]:
#3x        newtext = re.sub(r"\\" + tag + r"\b(.*?)\\end" + tag + r"\b",
#3x                         r"\\begin{" + tag + "}\1\\end{" + tag + "}",
#3x                         newtext, 0, re.DOTALL)
    newtext = re.sub(r"\\(begin|end){smallmatrix}",r"\\\1{matrix}",newtext)

#    newtext = re.sub(r"\\cases\b",r"\\begin{cases}",newtext)
#    newtext = re.sub(r"\\endcases\b",r"\\end{cases}",newtext)
#    newtext = re.sub(r"\\matrix\b",r"\\begin{matrix}",newtext)
#    newtext = re.sub(r"\\endmatrix\b",r"\\end{matrix}",newtext)
#    newtext = re.sub(r"\\smallmatrix\b",r"\\begin{matrix}",newtext)
#    newtext = re.sub(r"\\endsmallmatrix\b",r"\\end{matrix}",newtext)

    return newtext

def convert_ams_tex_references(text):

    newtext = text

    # subscripts
    newtext = re.sub(r"\\ref\s*\\no\s*(\S+)",r"\\bibitem[\1]{\1}",newtext)
    newtext = re.sub(r"\\ref\s*\\key\s*(\S+)",r"\\bibitem[\1]{\1}",newtext)
    newtext = re.sub(r"\\endref\b",r"",newtext)

    return newtext

def convert_ams_tex(text):

    newtext = text

    newtext = re.sub(r"\\toc\b.*\\endtoc","", newtext,1,re.DOTALL)
    # delete toc first because it could contain \head

    # hack:  specialhead should be "chapter"
    #  then the \\document before the first \\head should try \\specialhead first
    newtext = re.sub(r"\\specialhead\b",r"\\head",newtext)
    newtext = re.sub(r"\\endspecialhead\b",r"\\endhead",newtext)

    logging.debug("looking for \\document")

    if re.match(r"\\document\b",newtext) is None:
        # if they left out \document, put it before the first \head
        logging.warning("ADDING \document before \\head")
        newtext = re.sub(r"\\head\b",r"\\document\n\n\\head",newtext,1)

    for tag in ams_to_beginend:
        newtext = re.sub(r"\\" + tag + r"\b",r"\\begin{" + tag + "}",newtext)
        newtext = re.sub(r"\\end" + tag + r"\b",r"\\end{" + tag + "}",newtext)

    for tag, newtag in ams_to_beginend_renamed:
        newtext = re.sub(r"\\" + tag + r"\b",r"\\begin{" + newtag + "}",newtext)
        newtext = re.sub(r"\\end" + tag + r"\b",r"\\end{" + newtag + "}",newtext)

    for tag in ams_to_macro:
        newtext = re.sub(r"\\" + tag + r"\b(.*?)\\end" + tag + r"\b" ,r"\\" + tag + "{" + r"\1" + "}",newtext,0,re.DOTALL)

    for tag, newtag in ams_to_macro_renamed:
           # need a more robust way to strip surrounding brackets
        lookfor = r"\\" + tag + r"\b\s*\{?\s*(.*?)\s*\}?\s*\\end" + tag + r"\b"
        logging.debug("looking for %s", lookfor)
        newtext = re.sub(lookfor ,r"\\" + newtag + "{" + r"\1" + "}",newtext,0,re.DOTALL)

 #   newtext = re.sub(r"\\section\*?{References}",r"\\begin{thebibliography}",newtext)

    newtext = utilities.replacemacro(newtext,"demo",1,r"\begin{proof}[#1]")
    newtext = re.sub(r"\\enddemo\b",r"\\end{proof}",newtext)

    newtext = utilities.replacemacro(newtext,"proclaim",1,r"\begin{generictheorem}[#1]")
    newtext = re.sub(r"\\endproclaim\b",r"\\end{generictheorem}",newtext)
    newtext = utilities.replacemacro(newtext,"remark",1,r"\begin{generictheorem}[#1]")
    newtext = re.sub(r"\\endremark\b",r"\\end{generictheorem}",newtext)

    newtext = convert_ams_tex_references(newtext)

    return newtext

def convert_archaic_tex(text):
# try to convert old TeX-style commands to the proper LaTeX form
# note that many of these are not literally archaic.
# in some cases I just think that no author should do it.

    newtext = text

    newtext = convert_ams_tex_math(newtext)

    if r"\begin{document}" not in newtext or r"\documentstyle" in newtext:  # maybe a mistake.  See math_0409365
        newtext = convert_ams_tex(newtext)

    # revery the "up" letters and others from [a package]
    for letter in utilities.greek_letters:
        the_sub =  r"\\" + "(" + letter + ")" + r"up"
        logging.debug("Greek letters up:" + the_sub)
   #     newtext = re.sub(the_sub, r"\\\1",newtext,re.I)
        newtext = re.sub(the_sub, r"\\\1",newtext)
        if letter != "epsilon":
            the_sub =  r"\\" +"var" + "(" + letter + ")"
            newtext = re.sub(the_sub,r"\\\1",newtext)
        the_sub =  r"\\" +"v" + "(" + letter + ")"
        newtext = re.sub(the_sub,r"\\\1",newtext)
        the_sub =  r"\\" +"s" + "(" + letter + ")"
        newtext = re.sub(the_sub,r"\\\1",newtext)

    # macros that are not really archaic, but are not needed for HTML
    newtext = utilities.replacemacro(newtext,"maxtocdepth",1,"")
    newtext = utilities.replacemacro(newtext,"hypersetup",1,"")
    newtext = utilities.replacemacro(newtext,"texorpdfstring",2,"#1")
    newtext = utilities.replacemacro(newtext,"vadjust",1,"")
    newtext = utilities.replacemacro(newtext,"AtBeginDocument",1,"#1")
    newtext = utilities.replacemacro(newtext,"makeop",1,r"\DeclareMathOperator{\#1}{#1}")

    newtext = utilities.replacemacro(newtext,"thanksref",1,"")
    newtext = re.sub(r"\\bolds\b",r"\\boldsymbol",newtext)

    newtext = re.sub(r"\\vspace\*",r"\\vspace",newtext)   
                     # vecause \vspace* means to put white space even in those places where
                     # there is nothing to space (end of a page, say), but for html
                     # this is not needed.

    newtext = re.sub(r"\\mainmatter","",newtext)
    newtext = re.sub(r"\\dominitoc","",newtext)

    newtext = re.sub(r"\\tableofcontents\b",r"",newtext)
    newtext = re.sub(r"\\onehalfspacing\b",r"",newtext)
    newtext = utilities.replacemacro(newtext,"phantom",1,"")
    newtext = utilities.replacemacro(newtext,"hphantom",1,"")
    newtext = utilities.replacemacro(newtext,"vphantom",1,"")
    newtext = re.sub(r"\\bgroup\b",r"{",newtext)
    newtext = re.sub(r"\\egroup\b",r"}",newtext)

    newtext = re.sub(r"\\long\\def", r"\\def", newtext)
    newtext = re.sub(r"\\global\\long", "", newtext)
    newtext = re.sub(r"\\global\\(def|edef)", r"\1", newtext)

    # why do people put in stupid spaces and carriage returns?
    newtext = re.sub(r"(\\(ref|cite|eqref|begin|end))\s+{",r"\1{",newtext)

    newtext = re.sub(r"\\IEEEnonumber\b",r" ",newtext)
    newtext = re.sub(r"\\begin{IEEEproof}",r"\\begin{proof}",newtext)  
    newtext = re.sub(r"\\end{IEEEproof}",r"\\end{proof}",newtext)  
    newtext = re.sub(r"\\begin{IEEEeqnarray}",r"\\begin{eqnarray}",newtext)  
    newtext = re.sub(r"\\end{IEEEeqnarray}",r"\\end{eqnarray}",newtext)  
    newtext = re.sub(r"\\begin{IEEEkeywords}",r"\\begin{keywords}",newtext)  
    newtext = re.sub(r"\\end{IEEEkeywords}",r"\\end{keywords}",newtext)  
    newtext = re.sub(r"\\IEEEPARstart{([^{}]*)}{([^{}]*)}",r"\1\2",newtext)

    newtext = re.sub(r"\\begin{subequations}","",newtext)  
    newtext = re.sub(r"\\end{subequations}","",newtext)  

    newtext = re.sub(r"\\begin{bibliography}",r"\\begin{thebibliography}\n\\bibliography{biblio}\n",newtext)  
    newtext = re.sub(r"\\end{bibliography}",r"\\end{thebibliography}",newtext)  

    newtext = re.sub(r"\\begin{bibsection}",r"\\begin{thebibliography}\n",newtext)  
    newtext = re.sub(r"\\end{bibsection}",r"\\end{thebibliography}",newtext)  

    newtext = re.sub(r"\\bibselect{([^{}]+)}",r"\\include{\1.ltb}",newtext)  

    newtext = re.sub(r"\\begin{displayquote}",r"\\begin{quote}\n",newtext)  
    newtext = re.sub(r"\\end{displayquote}",r"\\end{quote}",newtext)  

    newtext = re.sub(r"\\printbibliography",r"\\bibliography{biblio}",newtext)  

    newtext = re.sub(r"\\begin{smallmatrix}",r"\\begin{matrix}",newtext)  
    newtext = re.sub(r"\\end{smallmatrix}",r"\\end{matrix}",newtext)  

    newtext = re.sub(r"\\begin{numlist}",r"\\begin{enumerate}",newtext)
    newtext = re.sub(r"\\end{numlist}",r"\\end{enumerate}",newtext)
    newtext = re.sub(r"\\begin{enumlist}",r"\\begin{enumerate}",newtext)
    newtext = re.sub(r"\\end{enumlist}",r"\\end{enumerate}",newtext)

    newtext = re.sub(r"\\begin{multicols}{[0-9]}",r"",newtext)  
    newtext = re.sub(r"\\end{multicols}",r"",newtext)  

    newtext = re.sub(r"\\long\s*\\def",r"\\def",newtext)

    newtext = re.sub(r"\\iffalse\b.*?\\fi\b",r"",newtext,0,re.DOTALL)

    newtext = re.sub(r"\\xspace\b",r" ",newtext)
    newtext = re.sub(r"\\nobreakdash\b",r"-",newtext)
    newtext = re.sub(r"\\nobreak\b","",newtext)
    newtext = re.sub(r"\\penalty\s*-?[0-9]+","",newtext)

    newtext = re.sub(r"\\textemdash\b",r" -- ",newtext)

    newtext = utilities.replacemacro(newtext,"AtBeginDocument",1,r"#1")

    if r"\\endabstract" in newtext:
        newtext = re.sub(r"\\abstract\b",r"\\begin{abstract}",newtext)
        newtext = re.sub(r"\\endabstract\b",r"\\end{abstract}",newtext)
    else:
        newtext = utilities.replacemacro(newtext,"abstract",1,r"\begin{abstract}#1\end{abstract}" + "\n\n")


    if r"\proof" in newtext or r"\demo" in newtext:
        # note that a lonely \qed will just be deleted later
  #      newtext = re.sub(r"\\proof\b",r"\\begin{proof}",newtext)
  #      newtext = re.sub(r"\\demo\b",r"\\begin{proof}",newtext)
  #      newtext = re.sub(r"\\qed\b",r"\\end{proof}",newtext)
  #      newtext = re.sub(r"\\endproof\b",r"\\end{proof}",newtext)
  #      newtext = re.sub(r"\\enddemo\b",r"\\end{proof}",newtext)
        newtext = re.sub(r"\\(proof|demo)(.*?)\\(qed|endproof|enddemo)\b",
                         r"\\begin{proof}\2\\end{proof}",newtext,0,re.DOTALL)

# eliminate italic correction:  \/} --> }
    newtext = re.sub(r"\\/\s*}",r"}",newtext)
    newtext = re.sub(r"\\/\s",r" ",newtext)
    newtext = re.sub(r"([a-zA-Z])\\/([a-zA-Z])",r"\1\2",newtext)

    newtext = re.sub(r"\\begin{compactenum}",r"\\begin{enumerate}",newtext)  
    newtext = re.sub(r"\\end{compactenum}",r"\\end{enumerate}",newtext)  

    newtext = re.sub(r"\\begin{displaymath}",r"\\begin{equation}",newtext)  
    newtext = re.sub(r"\\end{displaymath}",r"\\end{equation}",newtext)  

    newtext = re.sub(r"\\begin{longlist}",r"\\begin{enumerate}",newtext)  
    newtext = re.sub(r"\\end{longlist}",r"\\end{enumerate}",newtext)  

    newtext = re.sub(r"\\begin{acknowledgements}",r"\\begin{acknowledgement}",newtext)  
    newtext = re.sub(r"\\end{acknowledgements}",r"\\end{acknowledgement}",newtext)  

    newtext = re.sub(r"\\begin{flalign(\*?)}",r"\\begin{align\1}",newtext)  
    newtext = re.sub(r"\\end{flalign(\*?)}",r"\\end{align\1}",newtext)  

    newtext = re.sub(r"\\roster\b",r"\\begin{enumerate}",newtext)  
    newtext = re.sub(r"\\endroster\b",r"\\end{enumerate}",newtext)  

    newtext = re.sub(r"\\tag\s*([0-9.]+)",r"\\tag{\1}",newtext)

    newtext = re.sub(r"\\QTR\s*{([a-zA-Z]+)}",r"\\\1",newtext)

    newtext = re.sub(r"\\xref\b",r"\\ref",newtext)
    newtext = re.sub(r"\\(c|C)ref\b",r"\\autoref",newtext)
    newtext = re.sub(r"\\thref\b",r"\\autoref",newtext)
    newtext = re.sub(r"\\thlabel\b",r"\\label",newtext)

    # (\ref{...}) usually should be \eqref{...}
    newtext = re.sub(r"\(\\ref{([^{}]+)}\)",r"\\eqref{\1}",newtext)  

    newtext = utilities.replacemacro(newtext,"addtocounter",2,"")
    newtext = re.sub(r"\\setcounter{[^{}]+}\s*[0-9]+",r"",newtext)  # later should implement autoref properly

    newtext = re.sub(r"\\paragraph\*",r"\\paragraph",newtext)    # 1407.3851

    newtext = re.sub(r"\\(section|subsection)\s*\\[a-z]+\s*\{",r"\\\1{",newtext)    # \section \textbf{title}

      # check if there is anthing to salvage from hyperref
    newtext = re.sub(r"\\hyperref\[[^\[\]]*\]",r"\\hyperrefxxxxxx",newtext)  
    newtext = utilities.replacemacro(newtext,"hyperrefxxxxxx",1,"#1")

    newtext = re.sub(r"\\mathaccent\s*19",r"\\acute",newtext)  # mathjax doesn't know the former

    newtext = re.sub(r"\\citet\b",r"\\cite",newtext)   # in LaTeX, puts author name, then date in parentheses
    newtext = re.sub(r"\\citep\b",r"\\cite",newtext)   # in LaTeX, puts parentheses around the author name and date
    newtext = re.sub(r"\\cites\b",r"\\cite",newtext)  
    newtext = re.sub(r"\\citem\b",r"\\cite",newtext)  # don't know what that means http://sl2x.aimath.org/development/collectedworks/htmlpaper/1007.4357/section1.html
    newtext = re.sub(r"\\citeyear\b",r"\\cite",newtext)  

    newtext = re.sub(r"\\cite{([^{}]+)}\*{([^{}]+)}",r"\\cite[\2]{\1}",newtext)  

#    newtext = re.sub(r"\\centerline\{("+utilities.one_level_of_brackets+r")\}",
#                     r"\\begin{center}\1\\end{center}",newtext,0,re.DOTALL)
    newtext = utilities.replacemacro(newtext,"centerline",1,r"\begin{center}#1\end{center}")
    newtext = re.sub(r"\\(begin|end){tightcenter}", r"\\\1{center}", newtext)


    newtext = re.sub(r"\\fpsbox\[[0-9 ]+\]",r"\\epsfbox",newtext)    # hep-ph_9509234

    newtext = re.sub(r"\\smallmatrix\b",r"\\begin{matrix}",newtext)
    newtext = re.sub(r"\\endsmallmatrix\b",r"\\end{matrix}",newtext)

    newtext = re.sub(r"\\pmatrix\b",r"\\begin{pmatrix}",newtext)
    newtext = re.sub(r"\\endpmatrix\b",r"\\end{pmatrix}",newtext)

    newtext = re.sub(r"\\notdivide",r"\\nmid",newtext)
    newtext = re.sub(r"\\textsection",r"\\S",newtext)
    newtext = re.sub(r"\\medspace",r"\\:",newtext)     # if not this conversion, then needs to be a MathJax macro
    newtext = re.sub(r"\\thickspace",r"\\;",newtext)   #  --ditto--
    newtext = re.sub(r"\\thinspace",r"\\,",newtext)   #  --ditto--

    newtext = re.sub(r"\\xspace\b",r" ",newtext)

    newtext = re.sub(r"\\openone\b",r"{\\mathbb 1}",newtext)   # from REVTeX

    newtext = re.sub(r"\\begingroup\b",r"",newtext)
    newtext = re.sub(r"\\endgroup\b",r"",newtext)

    newtext = re.sub(r"\\empty\b",r"",newtext)
    newtext = re.sub(r"\\pageref\b",r"\\ref",newtext)
    newtext = re.sub(r"\\textnormal\b",r"\\text",newtext)

    newtext = re.sub(r"\\footnotesize\b","",newtext)
    newtext = utilities.replacemacro(newtext,"obeylines",1,"#1")
    newtext = utilities.replacemacro(newtext,"raisebox",2,"#2")

    newtext = re.sub(r"\\FloatBarrier\b",r"",newtext)

    newtext = re.sub(r"\\\\\s*\[[0-9]+(pt|in|cm)\]",r"\\\\",newtext)
    newtext = re.sub(r"\\\\\s*\[[0-9]+(pt|in|cm)\]",r"\\\\",newtext)

    newtext = re.sub(r"\\(text|hbox|mbox){{([^{}]+)}}",r"\\\1{\2}",newtext)    # as in  \def\R{\mbox{{\bf R}}}  %  math_0104087

    # correct common failures to write things like \textbf{...}
    # e.g., \newcommand{\textmod}{{\text {\rm mod}}} from 1201.5400 
    # this needs to be more clever, because people can use {\bf k} in math mode,
    # so that needs to be mathbf, not textbf
    newtext = re.sub(r"\\text(up)?\s*{\s*\\(text)?bf{([^{}]+)}",r"\\textbf{\3",newtext)
    newtext = re.sub(r"\\text(up)?\s*{\s*\\(text)?rm(\s+|{)",r"\\text{\3",newtext)
    newtext = re.sub(r"\\text(up)?\s*{\s*\\(text)?(\s+|{)",r"\\textit{\3",newtext)
    newtext = re.sub(r"\\text(up)?\s*{\s*\\em(ph)?(\s+|{)",r"\\textit{\3",newtext)
    newtext = re.sub(r"\\text(up)?\s*{\s*\\(text)?bf(\s+|{)",r"\\textbf{\3",newtext)
    newtext = re.sub(r"\\(m|h)box\s*{\s*\\em(ph)?(\s+|{)",r"\\textit{\3",newtext)
    newtext = re.sub(r"\\(m|h)box\s*{\s*\\(text)?rm(\s+|{)",r"\\mathrm{\3",newtext)
    newtext = re.sub(r"\\(m|h)box\s*{\s*\\(text)?bf(\s+|{)",r"\\mathbf{\3",newtext)
    # Need a more general version of the following, because mathjax treats the argument of \text{...} literally.
    newtext = re.sub(r"\\text(\b|rm|bf|it)?\s*{\s*\\quad\b",r"\\ \\ \\text\1{",newtext)

    newtext = re.sub(r"\\mathds\b",r"\\mathbb",newtext)  # mathds is from the dsfont package.  seems pretty useless to me.

    newtext = re.sub(r"\\define(\\|{)",r"\\def\1",newtext)
    newtext = re.sub(r"\\redefine(\\|{)",r"\\def\1",newtext)
    newtext = re.sub(r"\\predefine(\\|{)",r"\\def\1",newtext)
    newtext = re.sub(r"\\heading\b\s*(.*?)\s*\\endheading",r"\\section*{\1}",newtext)

    newtext = re.sub(r"\\begin{section}",r"\\section",newtext)
    newtext = re.sub(r"\\end{section}",r"",newtext)
    newtext = re.sub(r"\\begin{subsection}",r"\\subsection",newtext)
    newtext = re.sub(r"\\end{subsection}",r"",newtext)
    newtext = re.sub(r"\\begin{subsubsection}",r"\\subsubsection",newtext)
    newtext = re.sub(r"\\end{subsubsection}",r"",newtext)

    newtext = re.sub(r"\\begin{par}","\n\n",newtext)
    newtext = re.sub(r"\\end{par}","\n\n",newtext)

    newtext = re.sub(r"\\begin{caption}\s*(.*?)\s*\\end{caption}",r"\\caption{\1}",newtext)

  # This is not archaic: it is for in-line lists.  We convert it to
  # a displayed list, but that decision should be revisited.
    newtext = re.sub(r"\\begin{inparaenum}",r"\\begin{enumerate}",newtext)
    newtext = re.sub(r"\\end{inparaenum}",r"\\end{enumerate}",newtext)

    newtext = re.sub(r"\\begin{flushenumerate}",r"\\begin{enumerate}",newtext)
    newtext = re.sub(r"\\end{flushenumerate}",r"\\end{enumerate}",newtext)

#    newtext = re.sub(r"\\DeclareMathSymbol{([^{}]+)}{[^{}]+}{[^{}]+}{\"58}",r"\\newcommand{\1}{\mathbf{Sha}}",newtext) 
    # the usual LaTeX font magic to make a Tate-Shafarevich III (sha) does not work in MathJax
    newtext = re.sub(r"\\DeclareMathSymbol{([^{}]+)}{[^{}]+}{[^{}]+}{\"58}",r"\\newcommand{\1}{{III}}",newtext) 
    newtext = re.sub(r"\\fontencoding\{OT2\}\\selectfont\\char88",r"III",newtext)   # 1006.1002

    newtext = re.sub(r"\\mathop\\mathrm",r"\\operatorname",newtext)  # used in some definitions

    newtext = re.sub(r"\\arraycolsep\s*=\s*(\S+)",r"\\setlength{\arraycolsep}{\1}",newtext)
    return(newtext)

############

def convert_bibtex(text):
# try to convert old TeX-style commands to the proper LaTeX form

    if r"begin{bibdiv}" not in text and "begin{biblist}" not in text:
        return text

    newtext = text

    newtext = re.sub(r"\\begin{bibdiv}",r"\\begin{thebibliography}",newtext)
    newtext = re.sub(r"\\end{bibdiv}",r"\\end{thebibliography}",newtext)

    if "begin{thebibliography}" in newtext:
        newtext = re.sub(r"\\begin{biblist}",r"",newtext)
        newtext = re.sub(r"\\end{biblist}",r"",newtext)
    else:
        newtext = re.sub(r"\\begin{biblist}",r"\\begin{thebibliography}",newtext)
        newtext = re.sub(r"\\end{biblist}",r"\\end{thebibliography}",newtext)

    newtext = utilities.replacemacro(newtext,"bib",3,"\\bibitem{#1} #3")

    return newtext
