# -*- coding: utf-8 -*-

import os
import sys
import re
import logging

import utilities
import component
import dandr
import oldtex
import mapping
import separatecomponents

############
#
# These "throw away" environments will be handled properly in the future,
# by saving them to an environment-like dictionary.
#
##########

def throw_away_environments(text):

    logging.info("throwing away these environments: %s",
                  mapping.environments_to_delete)
    thetext = text

    for env in mapping.environments_to_delete:
        thetext = utilities.delete_one_environment(env, thetext)

    thetext = re.sub(r"\\labellist\s*\\endlabellist", "", thetext)

    return thetext

def throw_away_environments_later(text):

    logging.info("throwing away these environments: %s",
                  mapping.environments_to_delete_later)
    thetext = text

    for env in mapping.environments_to_delete_later:
        thetext = utilities.delete_one_environment(env, thetext)

    return thetext

############

def terminology_no_cr(txt):

    theterm = txt.group(1)

    theterm = re.sub("\s{2,}"," ",theterm)

    return r"\terminology{"+theterm+"}"

###########

def conversion_for_particular_authors(text):  
    """ A bunch of stuff that wouldn't be necessary if people wrote good LaTeX.
        Much of this was just hacks in the early development of the program:
        should be deleted or at least re-thought.

    """

    newtext = text

    logging.info("in conversion_for_particular_authors, writer is %s",
                  component.writer)

    if component.publisher == "MSP":
        newtext = conversion_for_msp(newtext)  # deleted, is in Archive

    inputfilenamestub = re.sub(r"[^.]*$","",component.inputfilename)
    inputfilenamestub = re.sub(".*/","",inputfilenamestub)

    # note sure what the purpose of \caption[words]{more words} is,
    # so delete the first argument
    newtext = re.sub(r"\\caption\[[^\[\]]*\]",
                     r"\\caption",newtext)

    # put label after caption (need a more robust version of these,
    # because the caption could contain curly brackets).
    newtext = re.sub(r"\\caption{\s*\\label{([^{}]+)}\s*([^{}]+)}",
                     r"\\caption{\2}\\label{\1}",newtext)
    newtext = re.sub(r"\\caption{\s*([^{}]+)\\label{([^{}]+)}\s*}",
                     r"\\caption{\1}\\label{\2}",newtext)

    # delete meaningless end of lines
    newtext = re.sub(r"\s*\\\\\s*\\begin{", "\n" + r"\\begin{", newtext)
    newtext = re.sub(r"\s*\\\\\s*\\end{", "\n" + r"\\end{", newtext)

    newtext = re.sub(r"\\citenamefont",r"",newtext)
    newtext = re.sub(r"\\bibnamefont",r"",newtext)
    newtext = re.sub(r"\\normalfont",r"",newtext)

    newtext = re.sub(r"\\phantomsection",r"", newtext)

    # since we don't support reptheorem, make it be an unnumbered theorem
    newtext = re.sub(r"\\begin{reptheorem}{[^{}]*}",r"\\begin{theorem*}",newtext)
    newtext = re.sub(r"\\end{reptheorem}",r"\\end{theorem*}",newtext)

    newtext = re.sub(r"\\begin{enumalph}",r"\\begin{enumerate}[a]",newtext)
    newtext = re.sub(r"\\end{enumalph}",r"\\end{enumerate}",newtext)
    newtext = re.sub(r"\\fontfamily{[^{}]+}\s*\\selectfont\s*", r" ", newtext)
    newtext = re.sub(r"\\fontfamily{[^{}]+}\s*\\fontsize{[^{}]*}{[^{}]*}\s*\\selectfont\s*", r" ", newtext)

    # \operators in 1601.06821/texmac.sty
    newtext = re.sub(r"\\def\\operators.*",r"",newtext)
    newtext = re.sub(r"\\operators({.*)", makeoperators, newtext, 1, re.DOTALL)
    newtext = re.sub(r"\\operators({.*)", makeoperators, newtext, 1, re.DOTALL)

    newtext = re.sub(r".*autorefname.*", "", newtext)

    newtext = re.sub(r"\\mathpzc",r"\\emph",newtext)

    newtext = re.sub(r"\\mypart\b",r"\\part",newtext)
    newtext = re.sub(r"\\mychapter\b",r"\\chapter",newtext)
    newtext = re.sub(r"\\mysection\b",r"\\section",newtext)

      # Kirby, 1203.1608
    newtext = re.sub(r"\\huge\$",r"$",newtext)

    newtext = re.sub(r"\\citealt\b",r"\\cite",newtext)
    newtext = re.sub(r"\\protect\\citeauthoryear",r"\\citeauthoryear",newtext)
    newtext = utilities.replacemacro(newtext,"citeauthoryear",3,"#1")

    newtext = re.sub(r"\\footnotesize{}",r"",newtext)

    newtext = utilities.delete_one_environment("noncompile", newtext)
    newtext = re.sub(r"\\begin{proof2}",r"\\begin{proof}",newtext)
    newtext = re.sub(r"\\end{proof2}",r"\\end{proof}",newtext)

    newtext = re.sub(r"\$\$\$\$",r"$$\n$$",newtext)  # |F|,2^{2n}|E|\}$$$$\lesssim|E|^{ from 1311.4092 .  I am not making that up.

    newtext = re.sub(r"\\newop{([^{}]+)}",r"\\DeclareMathOperator{\\\1}{\1}",newtext)
    newtext = re.sub(r"\\operatornamewithlimits",r"\\operatorname",newtext)

    newtext = re.sub(r"\\lbl\b",r"\\label",newtext)
    newtext = re.sub(r"\\ilabel",r"\\label",newtext)
    newtext = re.sub(r"\\mylabel",r"\\label",newtext)
    newtext = re.sub(r"\\iref",r"\\ref",newtext)
    newtext = re.sub(r"\\vref\b",r"\\ref",newtext)

    newtext = re.sub(r"\\textup",r"\\mbox",newtext)

    newtext = re.sub(r"\\tag\*",r"\\tag",newtext)
    newtext = re.sub(r"\\tag\{\\[a-z]+\}",r"",newtext)    #???

    newtext = re.sub(r"\\item\s*\[\]\s*\\item",r"\\item",newtext)

    newtext = re.sub(r"\\pazocal",r"\\mathcal",newtext)
    newtext = re.sub(r"\\itemsep\s*=?\s*[0-9\.]+\s*(pt|in)\s*",r"",newtext)

    newtext = re.sub(r"\\captionsetup\{type=([a-z]+)\}\s*\\caption{",r"\\captionof{\1}{",newtext)
    newtext = re.sub(r"\\caution *{([^\{\}]*)}",r"\\begin{caution}\1\\end{caution}",newtext)

    newtext = re.sub(r"\\hdots",r"\\cdots",newtext)

    newtext = re.sub(r"\\begin{compactitem}",r"\\begin{itemize}",newtext)
    newtext = re.sub(r"\\end{compactitem}",r"\\end{itemize}",newtext)

    newtext = re.sub(r"\\begin{(pp|myp)roof}",r"\\begin{proof}",newtext)
    newtext = re.sub(r"\\end{(pp|myp)roof}",r"\\end{proof}",newtext)
    newtext = re.sub(r"\\begin{proof.}",r"\\begin{proof}",newtext)
    newtext = re.sub(r"\\end{proof.}",r"\\end{proof}",newtext)
    newtext = re.sub(r"{myexample}",r"{example}",newtext)
    newtext = re.sub(r"{mytitle}",r"{title}",newtext)
    newtext = re.sub(r"\\begin{center}\s*Tasho\s*Kaletha\s*\\end{center}", "", newtext)
    newtext = re.sub(r"{myDefinition}",r"{definition}",newtext)

    newtext = re.sub(r"\\def\\replace",r"\\def\\Xreplace",newtext)
    newtext = utilities.replacemacro(newtext,"replace",1,"#1")

    # special for math_9809054
    newtext = re.sub(r".*makecubictable.*", "", newtext)

    newtext = re.sub(r"\\begin{efig}",r"\\begin{figure}",newtext)
    newtext = re.sub(r"\\end{efig}",r"\\end{figure}",newtext)
    newtext = re.sub(r"\\begin{impeqn}",r"\\begin{equation}",newtext)
    newtext = re.sub(r"\\end{impeqn}",r"\\end{equation}",newtext)

    newtext = re.sub(r"\\itshape",r"\\textit",newtext)
    newtext = re.sub(r"\\enskip",r" ",newtext)
    newtext = re.sub(r"\\og\{\}",r"",newtext)
    newtext = re.sub(r"\\og" + "\b",r"",newtext)
    newtext = re.sub(r"\\fg\{\}",r"",newtext)
    newtext = re.sub(r"\\fg" + "\b\s*",r"",newtext)
    newtext = re.sub(r"\\begin{sageverbatim}",r"\\begin{sageexample}",newtext)
    newtext = re.sub(r"\\end{sageverbatim}",r"\\end{sageexample}",newtext)
    newtext = re.sub(r"\\begin{Verbatim}",r"\\begin{sageexample}",newtext)
    newtext = re.sub(r"\\end{Verbatim}",r"\\end{sageexample}",newtext)
    newtext = re.sub(r"\\begin{alltt}",r"\\begin{sageexample}",newtext)
    newtext = re.sub(r"\\end{alltt}",r"\\end{sageexample}",newtext)
    newtext = re.sub(r"\\begin{lstlisting}",r"\\begin{sageexample}",newtext)
    newtext = re.sub(r"\\end{lstlisting}",r"\\end{sageexample}",newtext)
       # but see how we do an error check on sageexample in makeoutput.py

    # for \newenvironment{Gal}{{\rm Gal\,}}{}  M. Manes

    newtext = re.sub(r"\\newenvironment{([^}]+)}{{\\[a-z]+ ([a-zA-Z]+)[\\, ]*}}{}\s",
                     r"\\DeclareMathOperator{\\\1}{\2}" + "\n",newtext)

    if component.writer.lower() in ["singalakha"]:
        newtext = re.sub(r"\\textbf{\s*Definition\s+[0-9.]+: ", r"\\sdefinition{",newtext)
        newtext = utilities.replacemacro(newtext,"sdefinition",1,"\\begin{definition}[#1]DeFiN")
        newtext = re.sub(r"DeFiN(.*?)\\end{tcolorbox}",r"\1\\end{definition}",newtext,0,re.DOTALL)

        newtext = re.sub(r"\\textbf{\s*Worked Examples\s+[0-9.]+:}", r"\\begin{example}ExAmP",newtext)
        newtext = re.sub(r"\\textbf{\s*Worked Examples\s+[0-9.]+}:", r"\\begin{example}ExAmP",newtext)
        newtext = re.sub(r"ExAmP(.*?)\\end{tcolorbox}",r"\1\\end{example}",newtext,0,re.DOTALL)
        newtext = re.sub(r"\\textbf{\s*Solutions to worked examples\s*:}", r"\\begin{solution}SoLuT",newtext)
        newtext = re.sub(r"\\textbf{\s*Solutions to worked examples\s*}:", r"\\begin{solution}SoLuT",newtext)
        newtext = re.sub(r"SoLuT(.*?)\\begin{tcolorbox}",r"\1\\end{solution}\\begin{tcolorbox}",newtext,0,re.DOTALL)

        newtext = re.sub(r"\\textbf{\s*Check your understanding\s+[0-9.]+:}", r"\\begin{exercise}ExERc",newtext)
        newtext = re.sub(r"\\textbf{\s*Check your understanding\s+[0-9.]+}:", r"\\begin{exercise}ExERc",newtext)
        newtext = re.sub(r"ExERc(.*?)\\end{tcolorbox}",r"\1\\end{exercise}",newtext,0,re.DOTALL)

        newtext = re.sub(r"\\textbf{\s*Section[^{}]+hecklist\s*}\s*\\begin{todolist}",
                   r"\\begin{outcomes}[Checklist for this section]\\begin{enumerate}",newtext)
        newtext = re.sub(r"\\end{todolist}",r"\\end{enumerate}\\end{outcomes}",newtext,0,re.DOTALL)

        newtext = re.sub(r"\\textbf{\s*Properties\s+[0-9:\.]+\s*([^{}]+)}",
                   r"\\begin{proposition}[\1]PrOpOs",newtext)
        newtext = re.sub(r"PrOpOs(.*?)\\end{tcolorbox}",r"\1\\end{proposition}",newtext,0,re.DOTALL)

        newtext = re.sub(r"\\textbf{\s*Theorem\s+[0-9:\.]+\s*([^{}]+)}",
                   r"\\begin{theorem}[\1]ThEoRe",newtext)
        newtext = re.sub(r"ThEoRe(.*?)\\end{tcolorbox}",r"\1\\end{theorem}",newtext,0,re.DOTALL)

        newtext = re.sub(r"\\textbf{\s*Proof of[^{}]+}+", r"\\begin{proof}PrOoF",newtext)
        newtext = re.sub(r"PrOoF(.*?)\\end{tcolorbox}",r"\1\\end{proof}",newtext,0,re.DOTALL)

        newtext = re.sub(r"\\begin{tcolorbox}\s*\[[^\[\]]*\]","\n\n",newtext)
        newtext = re.sub(r"\\begin{tcolorbox}",r"\n\n",newtext)
        newtext = re.sub(r"\\end{tcolorbox}",r"",newtext)
        newtext = re.sub(r"\\begin{CJK\*}{UTF8}{gbsn}",r" ",newtext)
        newtext = re.sub(r"\\end{CJK\*}",r" ",newtext)

        newtext = re.sub(r"\$\$([^\$]+)\$\$\s*\.",r"\\begin{equation}\1.\\end{equation}",newtext)

        newtext = re.sub(r"\\hspace{[^{}]+}", "", newtext)
        newtext = re.sub(r"\$\\Box\$", "", newtext)


    if component.writer.lower() in ["austin"]:
    #    newtext = re.sub(r"textbf", r"term", newtext)
        newtext = re.sub(r"(\\cite{[^,}]+), *",r"\1}\\cite{", newtext)
        newtext = re.sub(r"(\\cite{[^,}]+), *",r"\1}\\cite{", newtext)
        newtext = re.sub(r"(\\cite{[^,}]+), *",r"\1}\\cite{", newtext)
        newtext = re.sub(r"(\\cite{[^,}]+), *",r"\1}\\cite{", newtext)

    if component.writer.lower() in ["cremona"]:
        logging.warning("author-specific conversion for %s", component.writer)
        component.counter['section'] = -1  # his book has sections, not chapters

    if component.writer.lower() in ["foundations"]:
        logging.warning("author-specific conversion for %s", component.writer)
        newtext = re.sub(r"\\begin{center}(.*?)\\end{center}", r"\\begin{figure}\1\\end{figure}", newtext,0,re.DOTALL)
        newtext = re.sub(r"\\captionof{figure}{}", r"", newtext)
        newtext = utilities.replacemacro(newtext,"captionof",1,"\\caption")

    if component.writer.lower() in ["keb"]:
        newtext = re.sub(r"} *\\ ", "} ", newtext)
        newtext = re.sub(r"(\\chapter)\[[^\[\]]+\]", r"\1", newtext)
        newtext = re.sub(r"(\\index){[a-z]+}{", r"\1{", newtext)
        newtext = re.sub(r"\\begin{detail}\s*{[^{}]+}", r"\\begin{remark}", newtext)
        newtext = re.sub(r"(\\begin|\\end){detail}", r"\1{remark}", newtext)
        newtext = re.sub(r"\hfill *\$\\Box\$", "", newtext)
        newtext = re.sub(r" on page\s*\\pageref{[^{}]+}", "", newtext)
        newtext = re.sub(r" from page\s*\\pageref{[^{}]+}", "", newtext)
        newtext = re.sub(r"& *= *&", r"=\\mathstrut&", newtext)
        newtext = re.sub(r"& *&", r"&", newtext)
        newtext = re.sub(r"{\\bf +Theorem: +([^{}]+)}\s*(.*?)" + "\n\n", r"\\begin{theorem}[\1] \2 \\end{theorem}" + "\n\n", newtext, 0, re.DOTALL)
        newtext = re.sub(r"{\\bf +([^{}]+Theorem):*}\s*(.*?)" + "\n\n", r"\\begin{theorem}[\1] \2 \\end{theorem}" + "\n\n", newtext, 0, re.DOTALL)
        newtext = re.sub(r"{\\bf +Definition: +([^{}]+)}\s*(.*?)" + "\n\n", r"\\begin{definition}[\1] \2 \\end{definition}" + "\n\n", newtext, 0, re.DOTALL)
        newtext = re.sub(r"{\\bf +Illustration: +([^{}]+)}\s*(.*?)" + "\n\n", r"\\begin{exploration}[\1] \2 \\end{exploration}" + "\n\n", newtext, 0, re.DOTALL)

   #     newtext = re.sub(r"{\\bf +Theorem: +([^{}]+)}\s(.*?)" + "\n\n", r"\\begin{theorem}[\1]\2 \\end{theorem}" + "\n\n", newtext, 0, re.DOTALL)
   #     newtext = re.sub(r"{\\bf +([^{}]+Theorem):*}\s(.*?)" + "\n\n", r"\\begin{theorem}[\1]\2 \\end{theorem}" + "\n\n", newtext, 0, re.DOTALL)
   #     newtext = re.sub(r"{\\bf +Definition: +([^{}]+)}\s(.*?)" + "\n\n", r"\\begin{definition}[\1]\2 \\end{definition}" + "\n\n", newtext, 0, re.DOTALL)
   #     newtext = re.sub(r"{\\bf +Illustration: +([^{}]+)}\s(.*?)" + "\n\n", r"\\begin{exploration}[\1]\2 \\end{exploration}" + "\n\n", newtext, 0, re.DOTALL)


        newtext = re.sub(r"Proof}:", "Proof: }", newtext)
        newtext = re.sub(r"{\\em Proof: *}(.*?)" + "\n\n", r"\\begin{proof}\1\\end{proof}" + "\n\n", newtext, 0, re.DOTALL)
        newtext = re.sub(r"\\begin{example}\s*{\\bf *([^{}]+)} *\\*", r"\\begin{example}[\1]", newtext)
     #   newtext = re.sub(r"\\begin{example}\s*\\textbf{([^{}]+)} *\\*", r"\\begin{example}[\1]", newtext)
     #   newtext = re.sub(r"\\begin{example}\s*{\\bf *([^{}]+)}", r"\\begin{example}[\1]", newtext)
     #   newtext = re.sub(r"\\begin{example}\s*\\textbf{([^{}]+)}", r"\\begin{example}[\1]", newtext)
        newtext = re.sub(r"\\fbox *{\\parbox{[^{}]+}{ *{\\bf +([^{}]+)}\\*", r"\\myfbox{{[\1]", newtext)
        newtext = utilities.replacemacro(newtext,"sectionmark",1,"")
        newtext = utilities.replacemacro(newtext,"myfbox",1,"\\mygbox{#1}")
        newtext = utilities.replacemacro(newtext,"mygbox",1,"\\begin{assemblage}#1\\end{assemblage}")
        newtext = re.sub(r"continued from page\s+\\pageref{[^{}]+}\)}\\", "continued)}", newtext)

    if component.writer.lower() in ["mckenna"]:
        newtext = re.sub(r"(\\paragraph){", r"\1s{", newtext)
        newtext = re.sub(r"{quotation}", r"{quote}", newtext)
        newtext = utilities.replacemacro(newtext,"epigraph",2,"#1\n\n#2")
        newtext = utilities.replacemacro(newtext,"tnote",1," ")

    if component.writer.lower() in ["rodman"]:
        newtext = re.sub(r" (\\vect{.} *\+ * \\vect{.}) ", r" $\1$ ", newtext)
        newtext = re.sub(r" (\\vect{.} *= * \\[^ ]+) ", r" $\1$ ", newtext)
        newtext = re.sub(r" (\\vect{.})( |\.|,) ", r" $\1$\2", newtext)
        newtext = re.sub(r"\\noindent *\\bd{Challenge[^{}]*}(.*)", r"\\begin{project}\1\\end{project}", newtext)
        newtext = re.sub(r"\\noindent *\\textbf{Discussion[^{}]*}(.*)", r"\\begin{investigation}\1\\end{investigation}", newtext)
        newtext = re.sub(r"\\begin{tabbing}\s*(.*?)\\end{tabbing}", tabtolist, newtext, 0, re.DOTALL)
        newtext = re.sub(r"\[\\bd{.}\]", "", newtext)
        newtext = re.sub(r"\[\\bd{.}\]", "", newtext)
        newtext = re.sub(r" \\bd{(.)}(\.|,) ", r" $\\mathbf{\1}$\2 ", newtext)
        newtext = re.sub(r" \\bd{(.)} ([a-z])", r" $\\mathbf{\1}$ \2", newtext)
        newtext = re.sub(r"\\bd{(.)}", r"\\mathbf{\1}", newtext)
        newtext = utilities.replacemacro(newtext,"bd",0,"\\term")
        newtext = utilities.replacemacro(newtext,"endnote",1,"\\begin{commentary}#1\\end{commentary}")
        newtext = re.sub(r"\\(begin){pyth}", r"\\\1{theorem}[Pythagorean Theorem]", newtext)
        newtext = re.sub(r"\\(end){pyth}", r"\\\1{theorem}", newtext)
        newtext = re.sub(r"\\(begin|end){myex(|b|c)}", r"\\\1{exercise}", newtext)
        newtext = re.sub(r"\\(begin|end){annotation}", "", newtext)

    if component.writer.lower() in ["geochem"]:
        newtext = utilities.replacemacro(newtext,"sidenote",1,"\\aside{#1}")
        newtext = re.sub(r"\){}", r")", newtext)
        newtext = re.sub(r"<=>", r"&lt;=&gt;", newtext)
        newtext = re.sub(r"<->", r"&lt;-&gt;", newtext)
        newtext = re.sub(r"->", r"-&gt;", newtext)
        newtext = re.sub(r"<-", r"&lt;-", newtext)
        newtext = re.sub(r"\\newcolumntype.*", r"", newtext)
        newtext = re.sub(r"\\(begin|end){practice}", r"\\\1{problem}", newtext)
        newtext = re.sub(r"\\(begin|end){rules}", r"\\\1{principle}", newtext)
        newtext = re.sub(r"(\\begin{(practice|example|principle|problem)}){([^{}]+)}", r"\\\1[\3]", newtext)
        newtext = re.sub(r"{marginfigure}", r"{figure}", newtext)

    if component.writer.lower() in ["geodesics"]:
        newtext = re.sub(r"{ *\\it\s+", r"\\talics{", newtext)
        newtext = utilities.replacemacro(newtext,"talics",1,"#1")

    if component.writer.lower() in ["gentop"]:
        newtext = re.sub(r"{\\ss}", "ss", newtext)
        newtext = re.sub(r"{\\bf Point to ponder:}(.*)", r"\\begin{problem}\1\\end{problem}", newtext)
        newtext = re.sub(r"\\(begin|end){nul}", r"", newtext)
        newtext = re.sub(r"\\(begin|end){ctrexm}", r"\\\1{counterexample}", newtext)
        newtext = re.sub(r"\\(begin){protip}\s*{\\bf *([^{}]*):}", r"\\\1{note}[\2]", newtext)
        newtext = re.sub(r"\\(begin|end){protip}", r"\\\1{note}", newtext)
        newtext = utilities.replacemacro(newtext,"newthought",1,"#1 ")
        newtext = re.sub(r"{\\it ", r"\\emph{", newtext)
        newtext = utilities.replacemacro(newtext,"emph",1,"\\term{#1}")
        newtext = utilities.replacemacro(newtext,"defn",1,"\\term{#1}")
        newtext = utilities.replacemacro(newtext,"sidenote",1,"\\begin{aside} #1 \\end{aside}")
        newtext = utilities.replacemacro(newtext,"period",0,".")
        newtext = utilities.replacemacro(newtext,"comma",0,",")
        newtext = utilities.replacemacro(newtext,"semicolon",0,";")

    if component.writer.lower() in ["simiode"]:
        newtext = utilities.replacemacro(newtext,"kdef",1,"\\term{#1}")
        newtext = re.sub(r"\\(begin|end){reex}", r"\\\1{problem}", newtext)
        newtext = re.sub(r"\\(begin|end){modexer}", r"\\\1{question}", newtext)
         # to uniformize tabular layout description
        newtext = re.sub(r"\\nonumber", "", newtext)
        newtext = re.sub(r" *@{} *", "", newtext)
        newtext = re.sub(r"<=", r"&lt;=", newtext)
        newtext = re.sub(r" *<([0-9])", r" < \1", newtext)
        newtext = re.sub(r"\\ \\\\\[[^\[\]]+pt\]", r"", newtext)
        newtext = re.sub(r"\[label={\(\\alph\*\)}\]", r"", newtext)
        newtext = re.sub(r"\\(top|mid|bottom)rule", r"", newtext)
          # the "upper" below does not seem to do anything
        newtext = re.sub(r"Hint: *([^ ])(.*?)(\n(\n|\\end|\\item|%))", r"\\begin{hint}" + (r"\1").upper() + r"\2\\end{hint}\4", newtext,0,re.DOTALL)
        newtext = re.sub(r"(\\begin{equation})(\\index.*)", r"\2" + "\n" + r"\1", newtext)
   #     newtext = re.sub(r"\(\\(ref{[^{}]+})\)", r"\\eq\1", newtext)

    if component.writer.lower() in ["greicius"]:
        newtext = re.sub("\n *\\\\\n", "\n\n", newtext)
        newtext = re.sub(r"\\ii\b", "\n\\item", newtext)
        newtext = re.sub(r"<beamer>", r"", newtext)
        newtext = re.sub(r"([a-z.,]) \\alert{([^{}]+)}", r"\1 \\emph{\2}", newtext)
        newtext = re.sub(r"\\onslide.*", r"", newtext)
        newtext = re.sub(r"{s:", r"{c:", newtext)
        if not component.preprocess_counter:
            newtext = re.sub(r"\\section", r"\\chapter", newtext)
            newtext = re.sub(r"\\subsection", r"\\section", newtext)
        newtext = re.sub(r"\\(pause|apause|bpause)", "\n", newtext)
        newtext = re.sub(r"\\begin{frame}{", r"\\bbeeginframe{", newtext)
        newtext = re.sub(r"\\begin{frame}(.*?)\\end{frame}", r"\1", newtext, 0, re.DOTALL)
        newtext = utilities.replacemacro(newtext,"bbeeginframe",1,"\\begin{paragraphs}[#1]")
        newtext = utilities.replacemacro(newtext,"textbf",1,"\\term{#1}")
        newtext = utilities.replacemacro(newtext,"frametitle",1,"")
        newtext = re.sub(r"\\end{frame}", r"\\end{paragraphs}", newtext)
        newtext = re.sub(r"\\(begin|end){overprint}", r"", newtext)
        newtext = re.sub(r"(\\begin|\\end){comments}", r"\1{remark}", newtext)

        newtext = re.sub(r"\\begin{block}{([^{}]+)}",r"\\begin{paragraphs}[\1]",newtext)
        newtext = re.sub(r"\\end{block}",r"\\end{paragraphs}",newtext)

        newtext = re.sub(r"\\begin{paragraphs}\[([^\[\]]+)\]",r"\\begin{paragraphs}[\1]",newtext)
        newtext = re.sub(r"\\begin{paragraphs}",r"\\begin{paragraphs}",newtext)
        newtext = re.sub(r"\\end{paragraphs}",r"\\end{paragraphs}",newtext)

    if component.writer.lower() in ["cft"]:
        newtext = re.sub(r"\\head{Reference}(.*?)(\n\n)",
                         r"\\alert{Reference} \1\2",
                         newtext, 0, re.DOTALL)
        newtext = re.sub(r"\\head{", r"\\subsection{", newtext)
 #       newtext = re.sub(r"\\chapter{", r"\\section{", newtext)
 #       newtext = re.sub(r"\\part{", r"\\chapter{", newtext)
        newtext = re.sub(r"chap:", r"sec:", newtext)
        newtext = re.sub(r"\\'e", r"&#xe8;", newtext)
        newtext = re.sub(r"\\item\[[^\[\]]*\]", r"\\item ", newtext)
        newtext = re.sub(r"\\Chapter~", r"Section~", newtext)

    if component.writer.lower() in ["yong"]:
       newtext = re.sub(r"\\makegapedcells", "", newtext)
       newtext = re.sub(r" \\textbf{([a-z]{5,})}", r" \\term{\1}", newtext)

    if component.writer.lower() in ["jvbutter"]:
       newtext = re.sub(r"\\emph{([a-z]{5,})}", r"\\term{\1}", newtext)
       newtext = re.sub(r" \\textbf{([a-z]{5,})}", r" \\term{\1}", newtext)
       newtext = re.sub(r" \\textless", r" < ", newtext)
       newtext = re.sub(r"label{section-", r"label{sec_", newtext)
       newtext = re.sub(r"label{section", r"label{sec", newtext)

    if component.writer.lower() in ["kdc"]:
       newtext = re.sub(r"\\ifproofs", r"", newtext)
       newtext = re.sub(r"\\fi\b", r"", newtext)
       newtext = utilities.replacemacro(newtext,"ex",1,"\\begin{example}#1\\end{example}")
       newtext = utilities.replacemacro(newtext,"pf",1,"\\begin{proof}#1\\end{proof}")
       newtext = utilities.replacemacro(newtext,"prob",1,"\\begin{problem}#1\\end{problem}")
       newtext = utilities.replacemacro(newtext,"defn",1,"\\begin{definition}#1\\end{definition}")

    if component.writer.lower() in ["fitch"]:
       newtext = re.sub(r"(figure=[a-zA-Z]+)/", r"\1XYZW", newtext)
       newtext = re.sub(r"(\\begin{[^{}]+})([A-Z][a-zA-Z ]+?) *\\\\", r"\1[\2] ", newtext)

    if component.writer.lower() in ["poritz"]:
       newtext = re.sub(r"\\begin{adjustbox}{center}", r"", newtext)
       newtext = re.sub(r"\\end{adjustbox}", r"", newtext)
       newtext = re.sub(r"\\(begin|end){preface}", r"", newtext)
       newtext = re.sub(r"\\colorbox{lg}", r"\\codebox", newtext)
       newtext = utilities.replacemacro(newtext,"codebox",1,"\\code{#1}")
       newtext = re.sub(r"\\colorbox{lg}{([^{}]+)}", r"\\code{\1}", newtext)
       newtext = re.sub(r"\\textbf{\\ix{([^{}]+)}}", r"\\term{\1}\index{\1}", newtext)
       newtext = re.sub(r"{\\bf ", r"\\textbf{", newtext)
       newtext = re.sub(r"{\\textbf{(Alice|Bob|Eve)} ", r"\\emph{\1}", newtext)
       newtext = re.sub(r"\\textbf{", r"\\term{", newtext)
       newtext = re.sub(r"\\Python\\", r"Python", newtext)
       newtext = utilities.replacemacro(newtext,"ix",1,"#1\\index{#1}")
       newtext = re.sub(r"\\(begin){AZtcb}\[([^\[\]]*)=([^\[\]]*)\]{}{}", r"\\\1{question}\\\2{\3}", newtext)
       newtext = re.sub(r"\\(end){AZtcb}", r"\\\1{question}", newtext)
       newtext = re.sub(r"\\(begin){CTtcb}\[([^\[\]]*)=([^\[\]]*)\]{}{}", r"\\\1{exercise}\\\2{\3}", newtext)
       newtext = re.sub(r"\\(end){CTtcb}", r"\\\1{exercise}", newtext)
       newtext = re.sub(r"\\(begin){BTtcb}\[([^\[\]]*)=([^\[\]]*)\]{}{}", r"\\\1{problem}\\\2{\3}", newtext)
       newtext = re.sub(r"\\(end){BTtcb}", r"\\\1{problem}", newtext)
       newtext = re.sub(r"\\(begin|end){codedisp}", r"\\\1{program}", newtext)

    if component.writer.lower() in ["javajavajava"]:
          # next intentionally omits re.DOTALL
 #      newtext = re.sub(r"(begin|end){jjjlisting}", r"\1{lstlisting}", newtext)

       newtext = re.sub(" && ", r" AmPaMp ", newtext)
       newtext = re.sub(" [%] ", r" PeRcEnT ", newtext)
       newtext = re.sub("<[%]", r"<PeRcEnT", newtext)
       newtext = re.sub("[%]>", r"PeRcEnT>", newtext)
       # dangerous: to amake macro handling better
       newtext = re.sub("\n[%].*", r"", newtext)
       newtext = re.sub("\n +[%].*", r"", newtext)
       newtext = re.sub(" +[%].*", r"", newtext)
       newtext = re.sub("} +{", r"}{", newtext)
       newtext = re.sub("}\n{", r"}{", newtext)
       newtext = re.sub("\n}", r"}", newtext)

       newtext = newtext.replace("\\label{introduction}", r"\label{introduction" + str(component.preprocess_counter) + "}", 1)
       newtext = newtext.replace("\\label{chapter-summary}", r"\label{chapter-summary" + str(component.preprocess_counter) + "}", 1)
       newtext = newtext.replace("\\label{self-study-exercises}", r"\label{self-study-exercisesA" + str(component.preprocess_counter) + "}", 1)
       newtext = newtext.replace("\\label{self-study-exercises}", r"\label{self-study-exercisesB" + str(component.preprocess_counter) + "}", 1)
       newtext = newtext.replace("\\label{self-study-exercises}", r"\label{self-study-exercisesC" + str(component.preprocess_counter) + "}", 1)
       newtext = newtext.replace("\\label{self-study-exercises}", r"\label{self-study-exercisesD" + str(component.preprocess_counter) + "}", 1)
       newtext = newtext.replace("\\label{self-study-exercises}", r"\label{self-study-exercisesE" + str(component.preprocess_counter) + "}", 1)
       newtext = newtext.replace("\\label{self-study-exercises}", r"\label{self-study-exercisesF" + str(component.preprocess_counter) + "}", 1)
       newtext = newtext.replace("\\label{self-study-exercises}", r"\label{self-study-exercisesG" + str(component.preprocess_counter) + "}", 1)
       newtext = newtext.replace("\\label{self-study-exercises}", r"\label{self-study-exercisesH" + str(component.preprocess_counter) + "}", 1)
       newtext = newtext.replace("\\label{self-study-exercises}", r"\label{self-study-exercisesI" + str(component.preprocess_counter) + "}", 1)
       newtext = newtext.replace("\\label{self-study-exercises}", r"\label{self-study-exercisesJ" + str(component.preprocess_counter) + "}", 1)
       newtext = newtext.replace("\\label{self-study-exercises}", r"\label{self-study-exercisesJ" + str(component.preprocess_counter) + "}", 1)
       newtext = newtext.replace("\\label{self-study-exercises}", r"\label{self-study-exercisesL" + str(component.preprocess_counter) + "}", 1)
       newtext = newtext.replace("\\label{self-study-exercises}", r"\label{self-study-exercisesM" + str(component.preprocess_counter) + "}", 1)
       newtext = newtext.replace("\\label{self-study-exercise}", r"\label{self-study-exerciseN" + str(component.preprocess_counter) + "}", 1)
       newtext = newtext.replace("\\label{self-study-exercise}", r"\label{self-study-exerciseO" + str(component.preprocess_counter) + "}", 1)
       newtext = newtext.replace("\\label{self-study-exercise}", r"\label{self-study-exerciseP" + str(component.preprocess_counter) + "}", 1)
       newtext = newtext.replace("\\label{self-study-exercise}", r"\label{self-study-exerciseQ" + str(component.preprocess_counter) + "}", 1)
       newtext = newtext.replace("\\label{self-study-exercise}", r"\label{self-study-exerciseR" + str(component.preprocess_counter) + "}", 1)
       newtext = newtext.replace("\\label{self-study-exercise}", r"\label{self-study-exerciseS" + str(component.preprocess_counter) + "}", 1)
       newtext = newtext.replace("\\label{self-study-exercise}", r"\label{self-study-exerciseT" + str(component.preprocess_counter) + "}", 1)
       newtext = newtext.replace("\\label{self-study-exercise}", r"\label{self-study-exerciseU" + str(component.preprocess_counter) + "}", 1)
       newtext = newtext.replace("\\label{self-study-exercise}", r"\label{self-study-exerciseV" + str(component.preprocess_counter) + "}", 1)
       newtext = newtext.replace("\\label{self-study-exercise}", r"\label{self-study-exerciseW" + str(component.preprocess_counter) + "}", 1)
       newtext = newtext.replace("\\label{self-study-exercise}", r"\label{self-study-exerciseX" + str(component.preprocess_counter) + "}", 1)
       newtext = newtext.replace("\\label{self-study-exercise}", r"\label{self-study-exerciseY" + str(component.preprocess_counter) + "}", 1)
       newtext = newtext.replace("\\label{self-study-exercise}", r"\label{self-study-exerciseZ" + str(component.preprocess_counter) + "}", 1)

       component.preprocess_counter += 1

       newtext = re.sub("\\label{introduction}", r"\\label{introductionL}", newtext, 1)
       newtext = re.sub("\\label{introduction}", r"\\label{introductionM}", newtext, 1)

       newtext = re.sub("\\secEXRHone", r"\\section", newtext)

       newtext = re.sub(r"(begin|end){jjjlisting}", r"", newtext)
       newtext = re.sub(r"(begin|end){jjjlisting(left|right)}.*", r"", newtext)

       newtext = re.sub(r"\\begin{COBL}", r"\\begin{objectives}\\begin{itemize}", newtext)
       newtext = re.sub(r"\\end{COBL}", r"\\end{itemize}\\end{objectives}", newtext)

       newtext = re.sub(r"(begin|end){(ANS|BL|SMBL|SMBLlarge|BSE|SMBSE)}", r"\1{itemize}", newtext)
       newtext = re.sub(r"(begin|end){(SSTUDY|COL|COBLEXRcount|EXRtwo|EXRLL|EXRtwocount|EXRtwoLL)}", r"\1{enumerate}", newtext)
       newtext = re.sub(r"\\jjjprogstart", r"", newtext)
       newtext = utilities.replacemacro(newtext,"color",1,"")
       newtext = utilities.replacemacro(newtext,"jjjprogstop",2,"\\caption{#1 \\label{#2}}")
       newtext = re.sub(r"\\JavaRule\[false\]", r"\\JavaRule", newtext)
       newtext = utilities.replacemacro(newtext,"JavaRule",2,"\\begin{principle}[#1] #2\\end{principle}\n\n")
       newtext = utilities.replacemacro(newtext,"JavaTIP",3,"\\begin{principle}[#1:#2] #3\\end{principle}\n\n")
       newtext = utilities.replacemacro(newtext,"color",1,"#1")
       newtext = re.sub(r"\par\small\item\[\]", r"", newtext)
       newtext = re.sub(r"\\item *{([^{}]*)}", r" \1", newtext)
       newtext = re.sub(r"\\secCOLH.*?\\COend", r"", newtext,0, re.DOTALL)
       newtext = re.sub(r"{\\bf ([^{}]+)}", r"\\term{\1}", newtext)
       newtext = re.sub(r"<(E|K,V|V,K|applet|Object|String)>", r"[[[\1]]]", newtext)

    if component.writer.lower() in ["putnam"]:
          # next intentionally omits re.DOTALL
       newtext = re.sub(r"{\\bf Scratch:}\s*(.*)", r"\\begin{hint}\1\\end{hint}", newtext)
       newtext = re.sub(r"(begin|end){sol}", r"\1{solution}", newtext)
       newtext = re.sub(r"fbox", r"emph", newtext)

    if component.writer.lower() in ["beaver"]:
 #      newtext = re.sub(r"\\label{[^{}]+\-[^{}]+}", r"", newtext)
       newtext = re.sub(r"\\shadowbox", r"", newtext)
       newtext = re.sub(r"\\allowdisplaybreaks", r"", newtext)
       newtext = re.sub(r"\\begin{aligned}", r"", newtext)
       newtext = re.sub(r"\\end{aligned}", r"", newtext)
       newtext = re.sub(r"\$\\hspace{-.08in}\${\bf{.}}\$\\,\\,\\,\$}?", r"", newtext)
       newtext = re.sub(r"\$\\hspace{-.08in}\${{.}}\$\\,\\,\\,\$", r"", newtext)
       newtext = re.sub(r"{\\vspace{[^{}]+}", r"{", newtext)
       newtext = re.sub(r"commentout[a-z]+", r"commentout", newtext)
       newtext = re.sub(r"commentout{\w+", r"commentout{", newtext)
       newtext = re.sub(r"{{\\bf Solution:}", r"solution{", newtext)
       newtext = re.sub(r"{{\\bf Proof:}", r"proof{", newtext)
       newtext = re.sub(r"{\\em Hint: ", r"\\hint{", newtext)
       newtext = utilities.replacemacro(newtext,"commentoutsolution",1,"\\begin{solution}#1\\end{solution}")
       newtext = utilities.replacemacro(newtext,"commentoutproof",1,"\\begin{proof}#1\\end{proof}")
       newtext = utilities.replacemacro(newtext,"hint",1,"\\begin{hint}#1\\end{hint}")
#       newtext = re.sub(r"{\\bf Directions:} *(.*?)\w*\\vhh*", r"\\begin{paragraphs}[Directions] \1 \\end{paragraphs}", newtext,0,re.DOTALL)
#       newtext = re.sub(r"\textbf{Directions:} *(.*?)\n\n", r"\\begin{paragraphs}[Directions] \1 \\end{paragraphs}", newtext,0,re.DOTALL)
###       newtext = re.sub(r"{\\bf Proof:} *(.*?)\w*\\vhh*", r"\\begin{proof}\1\\end{proof}", newtext,0,re.DOTALL)

       newtext = re.sub(r"\\if *0", r"", newtext)
       newtext = utilities.replacemacro(newtext,"fi",0,"")

    if component.writer.lower() in ["gvsu"]:
       newtext = re.sub(r'\\newtheorem.*', r"", newtext)
       newtext = re.sub(r' "', r" ``", newtext)
       newtext = re.sub(r'([a-z\"\.\,\?])"', r"\1''", newtext)
       newtext = re.sub(r'\\LARGE', "", newtext)
       newtext = re.sub(r'\\Huge', "", newtext)
       newtext = re.sub(r'{alphalist}', "{itemize}", newtext)
       newtext = re.sub(r'{pactivity}', "{activity}", newtext)
       newtext = re.sub(r'(\\begin|\\end){pa}', r"\1{activity}", newtext)
       newtext = re.sub(r'\\begin{fqs}', r"\\begin{objectives}\\begin{itemize}", newtext)
       newtext = re.sub(r'\\end{fqs}', r"\\end{itemize}\\end{objectives}", newtext)
       newtext = re.sub(r'\\achapter{[0-9]+}', r"\\chapter", newtext)
       newtext = re.sub(r'\\csection', r"\\section", newtext)
       newtext = re.sub(r'\(Hint: *([^\(\)]+)\)', r"\\begin{hint}\1\\end{hint}", newtext)
       newtext = re.sub(r'\\hspace{[^{}]*}', "", newtext)
       newtext = re.sub(r'\\vspace{[^{}]*}', "", newtext)
       newtext = re.sub(r'\\resizebox{[^{}]*}{[^{}]*}', r"\\Xresizebox", newtext)
       newtext = utilities.replacemacro(newtext,"Xresizebox",1,"#1")
       newtext = utilities.replacemacro(newtext,"parbox",2,"#2")

    if component.writer.lower() in ["bergen"]:
       newtext = re.sub(r"\\ifsolns\b(.*?)\\fi\b", r"\\begin{solution}\1\\end{solution}", newtext, 0, re.DOTALL)
       newtext = utilities.replacemacro(newtext,"fillwithlines",1,"")
       newtext = utilities.replacemacro(newtext,"fbox",1,"#1")
       newtext = re.sub(r"\\renewcommand{\\arraystretch}{[^{}]*}",r"",newtext)
       newtext = re.sub(r"\\esolution",r"\\solution",newtext)
       newtext = re.sub(r"(\\solution)\*",r"\1",newtext)
       newtext = utilities.replacemacro(newtext,"solution",1,"\\begin{solution}#1\\end{solution}")
       newtext = utilities.replacemacro(newtext,"studentsoln",1,"\\begin{solution}#1\\end{solution}")
       newtext = re.sub(r"(V|F|R|D)enumerate",r"enumerate",newtext)
       newtext = re.sub(r"\\par\\soln",r"",newtext)
       newtext = re.sub(r"\\soln",r"",newtext)
       newtext = re.sub(r"\\myblank",r"",newtext)
       newtext = re.sub(r"(\\boxedblank)\[[^\[\]*]\]",r"\1",newtext)
       newtext = utilities.replacemacro(newtext,"boxedblank",1,"#1")
       newtext = re.sub(r"\\defnstyle",r"\\term",newtext)
       newtext = re.sub(r"\[\\height\]\[([^\[\]]+)\]",r"\1",newtext)
       newtext = utilities.replacemacro(newtext,"value",1,"")
       newtext = re.sub(r"\\ifodd\s*\\else",r"",newtext)
       newtext = re.sub(r"\\ifsolns\s*Student page{[^{}]*}\s*\\fi",r"",newtext)
       newtext = re.sub(r"\\hwnewpage",r"",newtext)
       newtext = re.sub(r"{solution}",r"{answer}",newtext)

    if component.writer.lower() in ["sally", "phys211", "phys212"]:
       newtext = re.sub(r"\\mainmatter",r"\\title{Bucknell Physics 212 Supplement}\\author{Spring, 2022}",newtext)
       newtext = re.sub(r"\\chapter\[[^\[\]]*\]",r"\\chapter",newtext)
       newtext = re.sub(r"\\\\\[[^\[\]]*\]",r"\\\\",newtext)
       newtext = re.sub(r"Fig\.(\s|~)",r"Figure\1",newtext)
       newtext = re.sub(r"Eq\.(\s|~)",r"",newtext)
       newtext = re.sub(r"{aproblem}{([^{}]+)}",r"{exercise}[\1]",newtext)
       newtext = re.sub(r"{aproblem}",r"{exercise}",newtext)
       newtext = re.sub(r"{problem}",r"{exercise}",newtext)
#       newtext = re.sub(r"{boxittext}",r"{aside}",newtext)
       newtext = re.sub(r"{exampleb}",r"{example}",newtext)
       newtext = re.sub(r"{example}\s*{([^{}]+)}",r"{example}[\1]",newtext)

# in postprocess       newtext = re.sub(r"(\\begin{example}\[[^\[\]]+)\.(\])",r"\1\2",newtext)
#       newtext = re.sub(r"\\units{([^{}\$]*)\$(\\[^{}\$]*)\$([^{}\$]*)}","\\Xunits{" + r"\1 \2 \3}",newtext)
       newtext = re.sub(r"\\units{([^{}\$]*)\$([^{}\$]*)\$([^{}\$]*)}","\\Xunits{" + r"\1 \2 \3}",newtext)
       newtext = re.sub(r"\\units","\\Xunits",newtext)
       newtext = re.sub(r"\\mbox{\$([^{}\$]+)\$}", r" \1 ",newtext)
       newtext = re.sub(r"& *= *&", "=\\mathstrut &",newtext)
       newtext = re.sub(r"\\nonumber", "",newtext)
       newtext = re.sub(r"section(:|_)", r"sec\1",newtext)
       newtext = re.sub(r"chapter(:|_)", r"chap\1",newtext)
 # not needed?      newtext = re.sub(r"Fig\.( |~)*", "",newtext) # Fig.~\ref{fig:phasor13}.

    if component.writer.lower() in ["jungic"]:
       newtext = re.sub(r"\\newpage", r"\n\n\n", newtext)
       newtext = re.sub(r"\\(begin|end){center}", r"\n\n\n", newtext)
       newtext = re.sub(r"\\newpage", r"\n\n\n", newtext)
       newtext = re.sub(r"} +\\textbf{([^{}])}", r"}[\1]", newtext)
       newtext = re.sub(r"\\textbf{Example: *}(.*?)\n\n", r"\\begin{example}\1\\end{example}", newtext)
       newtext = re.sub(r"\\textbf{Question: *}(.*?)\n\n", r"\\begin{question}\1\\end{question}", newtext)
       newtext = utilities.replacemacro(newtext,"textcolor",2,"#2") 

    if component.writer.lower() in ["mcconnell"]:
       newtext = re.sub(r"\\subsection\*{[0-9]\.[0-9]+ ", r"\\section{", newtext)
       newtext = re.sub(r"\\subsection\*", r"\\section", newtext)
       newtext = utilities.replacemacro(newtext,"addcontentsline",3,"") 
       newtext = re.sub(r"\\noindent\\textbf{Definition.}(.*?)\n\n", r"\\begin{definition}\1\\end{definition}", newtext,0, re.DOTALL)
       newtext = re.sub(r"\\noindent\\textbf{Proposition[^{}]*}(.*?)\\begin{proof}", r"\\begin{proposition}\1\\end{proposition}\\\\begin{proof}", newtext,0, re.DOTALL)

    if component.writer.lower() in ["chih"]:
       newtext = re.sub(r"\$\$(\\begin{tikz)", r"\1", newtext)
       newtext = re.sub(r"(end{tikzpicture})\$\$", r"\1", newtext)
       newtext = re.sub(r"\\section\*{Introduction}.*", "", newtext)
       newtext = re.sub(r"(url{[^{}]+)&([^{}]+})", r"\1&amp;\2", newtext)
       newtext = re.sub(r"{Chapter:", "{Chap:", newtext)
       newtext = re.sub(r"{Section:", "{Sec:", newtext)
       newtext = re.sub(r"\\textbf{Question:}", "", newtext)
       newtext = re.sub(r"\\textbf{Solution:}(.*?)(\\end{example})", r"\\begin{solution}\1\\end{solution}\2", newtext,0, re.DOTALL)
       newtext = utilities.replacemacro(newtext,"textbf",1,"\\term{#1}") 
       newtext = utilities.replacemacro(newtext,"textit",1,"\\emph{#1}") 

    if component.writer.lower() in ["duckworth"]:
       newtext = re.sub(r"\\end{example}((\s*)\\begin{solution}.*?\\end{solution})",
                   r"\1\2\\end{example}\2",newtext, 0, re.DOTALL)

    if component.writer.lower() in ["zbornik"]:
       newtext = re.sub(r"(\\item) *\\textbf{([^{}\.\:]+)[\.:]*}",
                   r"\1\\itemtitle{\2}",newtext)
       newtext = re.sub(r"(label|ref){ *Section: *",
                   r"\1{sec ",newtext)
       newtext = re.sub(r"(label|ref){ *Chapter: *",
                   r"\1{chap ",newtext)

    if component.writer.lower() in ["xhumari"]:
       newtext = re.sub(r"\\begin{center}\s*\\hfill\s+Sandi X.*?\\end{center}",
                   r"",newtext, 0, re.DOTALL)
       newtext = utilities.replacemacro(newtext,"vspace",1,"\\worksheetspace{#1}") 
       if "textbf{Purpose:}" in newtext:
           print("newtext", newtext)
           x_purpose = re.search(r"\\textbf{Purpose:}\s*(.*?)\s*\\\\", newtext).group(1)
           print("x_purpose", x_purpose)
           newtext = re.sub(r"\\textbf{Purpose:}\s*(.*?)\s*\\\\", "", newtext)
           x_objectives = re.search(r"\\textbf{Knowledge[^{}]*}\s*(.*?)\s*\\textbf{Task:}", newtext, re.DOTALL).group(1)
           print("x_objectives", x_objectives)
           newtext = re.sub(r"\\textbf{Knowledge[^{}]*}\s*(.*?)\s*\\textbf{Task:}", "", newtext, 1, re.DOTALL)
    
           x_objectives = re.sub(r"\\item *" + "\n", "", x_objectives)

           newtext = re.sub(r"(\\begin{questions})", 
                        r"\\begin{objectives}" + "\n" + x_purpose + x_objectives + r"\\end{objectives}" + "\n\n" + r"\1",
                        newtext)

           # some weird bug above
           newtext = re.sub(r"($|\b)egin{enumerate}\[[^\[\]]+\]", r"\\begin{enumerate}", newtext)

           print("newtext again", newtext)

    if component.writer.lower() in ["sz"]:
       newtext = re.sub(r"\\raggedcolumns", "", newtext)
       newtext = re.sub(r"\\closegraphsfile", "", newtext)
       newtext = re.sub(r"\\normalsize *", "", newtext)
       newtext = re.sub(r"\\scriptsize *", "", newtext)
       newtext = re.sub(r" *\\mbox{\\tiny *\\\(([^\(\)]+)\\\) *} *", r"\1", newtext)
       newtext = re.sub(r" *\\mbox{\\tiny *\$([0-9]+)\$ *} *", r"\1", newtext)
       newtext = re.sub(r" *\\mbox{\\tiny *\$([a-z])\$ *} *", r"\1", newtext)
       newtext = re.sub(r"\\vspace\**{[^{}]+}", "", newtext)
       newtext = re.sub(r"\\hspace\**{[^{}]+}", "", newtext)
         # move footnote out of title
       newtext = re.sub(r"\{([^{}]+)(\\footnote\{[^{}]+\})([^{}]*)\}",r"{\1\3}\2",newtext)
       newtext = utilities.replacemacro(newtext,"import",2,"\\input{#1#2}") 
       newtext = utilities.replacemacro(newtext,"colorbox",2,"#2") 
       newtext = utilities.replacemacro(newtext,"mfpicnumber",1,"") 
       newtext = utilities.replacemacro(newtext,"opengraphsfile",1,"") 
       newtext = utilities.replacemacro(newtext,"setcounter",2,"") 
       newtext = utilities.replacemacro(newtext,"extrarowheight",1,"") 
       newtext = re.sub(r"\\begin{boxedminipage}{[^{}]*}}", "", newtext)
       newtext = re.sub(r"\\end{boxedminipage}", "", newtext)
       newtext = re.sub(r"\\begin{eqn}", r"\\begin{proposition}", newtext)
       newtext = re.sub(r"\\end{eqn}", r"\\end{proposition}", newtext)
       newtext = re.sub(r"\\begin{proposition}(.*?)\\end{proposition}", szprop, newtext, 0, re.DOTALL)
       newtext = re.sub(r"\\begin{ex}", r"\\begin{example}", newtext)
       newtext = re.sub(r"\\end{ex}", r"\\end{example}", newtext)
       newtext = re.sub(r"\\begin{example}(.*?)\\end{example}", szex, newtext, 0, re.DOTALL)
       newtext = re.sub(r"{mycases}",r"{cases}",newtext)

    if component.writer.lower() in ["dray"]:
       newtext = re.sub(r"\\expandafter\\ifx\\csname\s+Book.*?\\begin{document}\s*\\fi\s*","",newtext,0,re.DOTALL)
       newtext = re.sub(r"\\input\s+\\TOP\s+macros.*","",newtext)
       newtext = re.sub(r"\\TOP\s+",r"../",newtext)
       newtext = re.sub(r"\\chapter\s*\[([^[]*)\]\s*",r"\\chapter",newtext)
       newtext = re.sub(r"\\section\s*\[([^[]*)\]\s*",r"\\section",newtext)
       newtext = re.sub(r"\\subsection\s*\[([^[]*)\]\s*",r"\\subsection",newtext)

    if component.writer.lower() in ["gorkin"]:
       newtext = re.sub(r"{\\bf",r"\\textbf{",newtext)
       newtext = re.sub(r"\\tt\b",r"\\mathbb{T}",newtext)
       newtext = re.sub(r"\\color{[^{}]+}",r"",newtext)

    if component.writer.lower() in ["rosulek"]:
       newtext = re.sub(r"\\constructionref{([^{}]+)}",r"Construction~\\ref{\1}",newtext)
       newtext = re.sub(r"\\definitionref{([^{}]+)}",r"Definition~\\ref{\1}",newtext)
       newtext = re.sub(r"\\(begin|end){construction}",r"\\\1{exploration}",newtext) # later renamed as Construction 
       newtext = utilities.replacemacro(newtext,"constructionbox",1,"#1")  # what should it be?
       newtext = utilities.replacemacro(newtext,"titlecodebox",2,"\\begin{genericpreformat}[#1]#2\\end{genericpreformat}")
       newtext = utilities.replacemacro(newtext,"hltitlecodebox",2,"\\begin{genericpreformat}[#1]#2\\end{genericpreformat}")
       newtext = utilities.replacemacro(newtext,"fcodebox",1,"\\begin{genericpreformat}[fcode]#1\\end{genericpreformat}")
       newtext = utilities.replacemacro(newtext,"codebox",1,"\\begin{genericpreformat}[code]#1\\end{genericpreformat}")

    if component.writer.lower() in ["mulberry"]:
       newtext = re.sub(r"\\begin{example}{([^{}]+)}{([^{}]+)}",
                        r"\\begin{example}[\1]\\label{exa:\2}",newtext)
       newtext = re.sub(r"\\begin{definition}{([^{}]+)}{([^{}]+)}",
                        r"\\begin{definition}[\1]\\label{def:\2}",newtext)
       newtext = re.sub(r"\\begin{theorem}{([^{}]+)}{([^{}]+)}",
                        r"\\begin{theorem}[\1]\\label{thm:\2}",newtext)
       newtext = re.sub(r'label=(\alph\*)', 'label=(a)', newtext)
       newtext = re.sub(r'\\item\[([0-9]+\.[0-9]+\.[0-9]+)\]', '\n\nOLDNUMBER ' + r'\1' + '\n\n', newtext)
       newtext = re.sub(r'\\\\\[[0-9]ex\]', '\n\n', newtext)

       newtext = re.sub(r"\\(begin|end){enumialphparenastyle}","",newtext)
       newtext = re.sub(r"\\(begin|end){ex}",r"\\\1{exercise}",newtext)
       newtext = re.sub(r"\\(begin|end){sol}",r"\\\1{solution}",newtext)
       newtext = re.sub(r"\\(begin|end){formulabox}",r"\\\1{assemblage}",newtext)
       newtext = re.sub(r"\\ifont{",r"\\emph{",newtext)
       newtext = re.sub(r"\\ffont{",r"\\emph{",newtext)
       newtext = re.sub(r"\\dfont{",r"\\term{",newtext)
       newtext = re.sub(r"\\deffont{",r"\\term{",newtext)
       newtext = re.sub(r"\\begin{adjustbox}{[^{}]+}","",newtext)
       newtext = re.sub(r"\\end{adjustbox}{[^{}]+}","",newtext)
       newtext = re.sub(r"\\\[(\\incl[^{}]+{[^{}]+})\\\]",r"\1",newtext)

    if component.writer.lower() in ["mma"]:
       newtext = re.sub(r"\\pmb{ Theorem:}(.*)",r"\\begin{theorem}\1\\end{theorem}",newtext)
       newtext = re.sub(r"\\pmb{ Example:}(.*)",r"\\begin{example}\1\\end{example}",newtext)
       newtext = re.sub(r"\n\n\\\(",r"\\(",newtext)
       newtext = re.sub(r"\\\)\n+",r"\\)",newtext)
       newtext = re.sub(r"\?\\\)",r"\\)?",newtext)
       newtext = re.sub(r"{ }","",newtext)
       newtext = re.sub(r"{('|''|``)}",r"\1",newtext)

    if component.writer.lower() in ["janssen"]:
       newtext = re.sub(r"\\(begin|end){unnumberedtheorem}",r"\\\1{theorem}",newtext)

    if component.writer.lower() in ["tengeley"]:
       newtext = re.sub(r"\\item\[\s*(\\ref{[^{}]*})\s*\]", r"\item \1", newtext)
       newtext = re.sub(r"\\begin{sideways}", r"", newtext)
       newtext = re.sub(r"\\end{sideways}", r"", newtext)
       newtext = re.sub(r"includegraphics\[width=50mm\]", r"includegraphics", newtext)

    if component.writer.lower() in ["elsz"]:
       newtext = re.sub(r"\\centering\b", "", newtext)
       newtext = re.sub(r"\\captionof\{figure\}", r"\\caption", newtext)
       newtext = re.sub(r"\\(chapter|section|subsection)\[[^\[\]]+\]", r"\1", newtext)
       newtext = re.sub(r"\\begin{minipage}\{[^{}]+\}(.{1,70})(includegraphics)(.{1,60})(caption)(.{1,100})\\end{minipage}}",
            r"\\begin{figure}\1\2\3\4\\end{figure}", newtext,0, re.DOTALL)
       newtext = re.sub(r"\\begin{minipage}{[^{}]+}", r"", newtext)
       newtext = re.sub(r"\\end{minipage}", r"", newtext)
       newtext = re.sub(r"\\\\\[[^\[\]]+\]", r"", newtext)
       newtext = utilities.replacemacro(newtext,"solution",1,"\\begin{solution} #1 \\end{solution}")
       newtext = utilities.replacemacro(newtext,"fbox",1,"#1")

    if component.writer.lower() in ["morris"]:
       newtext = re.sub(r"\\begin{summary}", r"\paragraphs{Summary}" + "\n\n" + r"\\begin{itemize}", newtext)
       newtext = re.sub(r"\\end{summary}", r"\\end{itemize}\\endparagraphs", newtext)
       newtext = re.sub(r"\\define\[([^\[\]]+)\]", r"\\index{\1}\\define", newtext)
       newtext = re.sub(r"\\define{([^{}]+)}", r"\\term{\1}", newtext)
       newtext = re.sub(r"\\begin{problist}", r"\\begin{enumerate}", newtext)
       newtext = re.sub(r"\\end{problist}", r"\\end{enumerate}", newtext)

    if component.writer.lower() in ["kooistra"]:
       newtext = re.sub(r"\\colvec{([^{}]+)}\s*{([^{}]+)}\s*{([^{}]+)}\s*{([^{}]+)}\s*{([^{}]+)}\s*{([^{}]+)}",
                        r"\\begin{pmatrix}\2\\\\\3\\\\\4\\\\\5\\\\\6\\end{pmatrix}", newtext)
       newtext = re.sub(r"\\colvec{([^{}]+)}\s*{([^{}]+)}\s*{([^{}]+)}\s*{([^{}]+)}\s*{([^{}]+)}",
                        r"\\begin{pmatrix}\2\\\\\3\\\\\4\\\\\5\\end{pmatrix}", newtext)
       newtext = re.sub(r"\\colvec{([^{}]+)}\s*{([^{}]+)}\s*{([^{}]+)}\s*{([^{}]+)}",
                        r"\\begin{pmatrix}\2\\\\\3\\\\\4\\end{pmatrix}", newtext)
       newtext = re.sub(r"\\colvec{([^{}]+)}\s*{([^{}]+)}\s*{([^{}]+)}",
                        r"\\begin{pmatrix}\2\\\\\3\\end{pmatrix}", newtext)
       newtext = re.sub(r"\\colvec{([^{}]+)}\s*{([^{}]+)}",
                        r"\\begin{pmatrix}\2\\end{pmatrix}", newtext)
       newtext = re.sub(r"smallitemize", "itemize", newtext)
       newtext = re.sub(r"smallenumerate", "enumerate", newtext)
       newtext = re.sub(r"smallparts", "enumerate", newtext)

    if component.writer.lower() in ["bartlett"]:
       newtext = re.sub(r"\\begin{ramanujansays}", r"\\begin{assemblage}", newtext)
       newtext = re.sub(r"\\end{ramanujansays}", r"\\end{assemblage}", newtext)

    if component.writer.lower() in ["kyp44"]:
       newtext = utilities.replacemacro(newtext,"insec",1,"\\input{sections/sec_#1}")
       newtext = re.sub(r"\\exercise{", r"\\kypexercise{", newtext);
       newtext = re.sub(r"enumerate}\[[^\[\]]*\]", r"enumerate}", newtext);
       newtext = utilities.replacemacro(newtext,"hint",1,"\\begin{hint}#1 \\end{exercise}")
       newtext = re.sub(r"\[ *Hint: *([^\[\]]+)\]*", r"\\begin{hint}\1\\end{hint}", newtext);
       newtext = utilities.replacemacro(newtext,"kypexercise",2,"\\begin{exercise}[#1] #2 \\end{exercise}")
       newtext = utilities.replacemacro(newtext,"sol",1,"\\begin{solution} #1 \\end{solution}")
       newtext = utilities.replacemacro(newtext,"qproof",1,"\\begin{proof} #1 \\end{proof}")
       newtext = utilities.replacemacro(newtext,"proof",1,"\\begin{proof} #1 \\end{proof}")
       newtext = utilities.replacemacro(newtext,"ali",1,"\\begin{align*} #1 \\end{align*}")
       newtext = utilities.replacemacro(newtext,"eparts",1,"\\begin{itemize} #1 \\end{itemize}")

    if component.writer.lower() in ["petry"]:
       newtext = utilities.replacemacro(newtext,"textbook",1,"#1")
       newtext = utilities.replacemacro(newtext,"problemgrouptitle",1,"[#1]")
       newtext = utilities.replacemacro(newtext,"answer",1,"\\begin{answer}#1\\end{answer}")
       newtext = re.sub(r"(\\ref)\*", r"\1", newtext)
       newtext = re.sub(r"(\\[a-z]+{)(\\index{[^{}]+})", r"\2\1", newtext)
       newtext = re.sub(r"\\textsuperscript{th}", r"th", newtext)
       newtext = re.sub(r"\\begin{furtherquestion}", r"\\begin{question}", newtext)
       newtext = re.sub(r"\\end{furtherquestion}", r"\\end{question}", newtext)
       newtext = re.sub(r"\\begin{method}", r"\\begin{algorithm}", newtext)
       newtext = re.sub(r"\\end{method}", r"\\end{algorithm}", newtext)
       newtext = re.sub(r"\\begin{problemblock}{([^{}]+)}", r"\\begin{problem}\1\\begin{enumerate}", newtext)
       newtext = re.sub(r"\\end{problemblock}", r"\\end{enumerate}\\end{problem}", newtext)

       newtext = re.sub(r"\\begin{minipage}{[^{}]+}", r"", newtext)
       newtext = re.sub(r"\\end{minipage}", r"", newtext)

    if component.writer.lower() in ["pauli"]:
       newtext = utilities.replacemacro(newtext,"slos",1,
                     "\\begin{objectives}\\begin{enumerate}#1\\end{enumerate}\\end{objectives}")
       newtext = re.sub(r"\\indemph\b", r"\\emph", newtext)
       newtext = re.sub(r"\\(label|ref)\{([^{}]+) ([^{}]+)\}", r"\\\1{\2\3}", newtext)
       newtext = re.sub(r"\\(label|ref)\{([^{}]+) ([^{}]+)\}", r"\\\1{\2\3}", newtext)
       newtext = re.sub(r"\\(label|ref)\{([^{}]+) ([^{}]+)\}", r"\\\1{\2\3}", newtext)
       newtext = re.sub(r"\\(label|ref)\{([^{}]+) ([^{}]+)\}", r"\\\1{\2\3}", newtext)
       newtext = re.sub(r"\\caption\[[^\[\]]*\]\s*", r"\\caption", newtext)
       newtext = re.sub(r"\\begin\{enumerate\}\[[^\[\]]*\]\s*", r"\\begin{enumerate}", newtext)
       newtext = re.sub(r"\\item\[([^\[\]]*)(\\ref)([^\[\]]*)\]", r"\\item \\title{\1\2\3}", newtext)

    if component.writer.lower() in ["boman"]:
       newtext = re.sub(r"\\index{general}", r"\\index", newtext)
       newtext = utilities.replacemacro(newtext,"IndexDefinitionGeneral",2,"\\index{#2}")
       newtext = utilities.replacemacro(newtext,"IndexDefinitionDefinitions",2,"\\index{#2}")
       newtext = utilities.replacemacro(newtext,"IndexTheoremGeneral",2,"\\index{#2}")
       newtext = utilities.replacemacro(newtext,"IndexTheoremTheorems",2,"\\index{#2}")
       newtext = utilities.replacemacro(newtext,"IndexProblemGeneral",2,"\\index{#2}")
       newtext = utilities.replacemacro(newtext,"IndexProblem",2,"\\index{#2}")
       newtext = utilities.replacemacro(newtext,"LabelProblem",2,"\\index{#2}")

       newtext = utilities.replacemacro(newtext,"sal",1,"\\emph{Salviati}:")
       newtext = utilities.replacemacro(newtext,"sim",1,"\\emph{Simplicio}:")
       newtext = utilities.replacemacro(newtext,"sag",1,"\\emph{Sagredo}:")

       newtext = utilities.replacemacro(newtext,"}\\ ",1,"} ")

       newtext = re.sub(r"\\begin{wrapfigure}\[[^\[\]]*\]{[^{}]+}{[^{}]+}", r"\\begin{wrapfigure}", newtext)
       newtext = re.sub(r"\\begin{wrapfigure}{[^{}]+}{[^{}]+}", r"\\begin{wrapfigure}", newtext)
       newtext = re.sub(r"{wrapfigure}", "{figure}", newtext)
       newtext = re.sub(r"{embeddedproblem}", "{problem}", newtext)
       newtext = re.sub(r"\\begin{ProblemSection}", r"\\section{exercises}", newtext)
       newtext = re.sub(r"\\end{ProblemSection}", r"", newtext)
       newtext = re.sub(r"{myproblem}", "{exercise}", newtext)
       newtext = re.sub(r"\\captionsetup{[^{}]+}", "", newtext)

       newtext = re.sub(r"\\xqedhere{[^{}]*}{[^{}]*}", "", newtext)

       newtext = re.sub(r"\\\\\[[0-9]+mm\]", r"\\\\", newtext)
       newtext = re.sub(r"\\begin{center}\s*\\begin{minipage}[t]{[^{}]+}(.{,1000}?)\\end{minipage}\s*\\end{center}",
                        r"\\begin{quote}\1\\end{quote}", newtext, 0, re.DOTALL)
   #    newtext = re.sub(r"\\begin{center}\s*\\begin{minipage}[t]{[^{}]+}", r"\\begin{quote}", newtext)
   #    newtext = re.sub(r"\\end{minipage}\s*\\end{center}", r"\\end{quote}", newtext)

    if component.writer.lower() in ["apex"]:
        logging.warning("author-specific conversion for %s", component.writer)
        newtext = apex_conversions(newtext)

    if component.writer.lower() in ["daom"]:
        logging.warning("author-specific conversion for %s", component.writer)
        newtext = re.sub(r"\\Chapter",r"\\chapter",newtext)

    if component.writer.lower() in ["spivak"]:
        logging.warning("author-specific conversion for %s", component.writer)
        newtext = re.sub(r"\\sexc\b",r"\\begin{enumerate}[a.]\n\item ",newtext)
   #     newtext = utilities.replacemacro(newtext,"makesolution",1,r"\\begin{solution}\n#1\n\\end{solution}")
        newtext = re.sub(r"\\begin{solution}[~]*\s*",r"\\begin{solution}" + "\n", newtext)
        newtext = re.sub(r"\\smiley",r"\\unicode{x263A}",newtext)
        newtext = re.sub(r"ForestGreen",r"green",newtext)

    if component.writer.lower() in ["sundstrom"]:
        newtext = re.sub(r"\\begin{defbox}",r"\\begindefbox",newtext)
        newtext = utilities.replacemacro(newtext,"begindefbox",2,'\\begin{definition}\\label{#1} #2 ')
        newtext = utilities.replacemacro(newtext,"fbox",1,'#1')
        newtext = utilities.replacemacro(newtext,"parbox",2,'#2')
        newtext = utilities.replacemacro(newtext,"setcounter",2,'')
        newtext = utilities.replacemacro(newtext,"setlength",2,'')
        newtext = re.sub(r"(\\chapter)\[[^\[\]]*\]",r"\1",newtext)
        newtext = re.sub(r"\\section\**{Exercises",r"\\exercises{Exercises",newtext)
        newtext = re.sub(r"\\end{defbox}",r"\\end{definition}",newtext)
        newtext = re.sub(r"\\begin{prog}",r"\\begin{investigation}",newtext)
        newtext = re.sub(r"\\end{prog}",r"\\end{investigation}",newtext)
        newtext = re.sub(r"\$\$\s*\\BeginTable",r"\\BeginTable",newtext)
        newtext = re.sub(r"\\EndTable\s*\$\$",r"\\EndTable",newtext)
        newtext = re.sub(r"\\BeginTable",r"\\begin{tabular}",newtext)
        newtext = re.sub(r"\s*\\BeginFormat\s*(.*)\s*\\EndFormat",r"{\1}\\EndFormat",newtext)
        newtext = re.sub(r"\\EndFormat(.*?)\\EndTable",tableformat,newtext,0,re.DOTALL)
        newtext = re.sub(r"nametheorem","theorem",newtext)
        newtext = re.sub(r"myproof","proof",newtext)
        newtext = re.sub(r"\\newpar","\n",newtext)
        newtext = re.sub(r"\\indent","\n",newtext)
        newtext = re.sub(r"\\hbreak","\n",newtext)
        newtext = re.sub(r"\\(x|y)item",r"\\item",newtext)

    if component.writer.lower() in ["beezer","oscarlevin"]:
        logging.warning("author-specific conversion for %s", component.writer)
        newtext = re.sub(r"\\chapter\[([^[]*)\]",r"\\chapter",newtext)
        newtext = re.sub(r"\\((sub)*)section\[([^\[\]]*)\]",r"\\\1section",newtext)
        newtext = re.sub(r"\\index{([^}]+)}(}|])",r"\2\\index{\1}",newtext)
        # experiment: put the proof inside the theorems
        newtext = re.sub(r"\\end{theorem}\s*\\begin{proof}(.*?)\\end{proof}",r"\\begin{proof}\1\\end{proof}\n\\end{theorem}",newtext,0,re.DOTALL)

          # temporary hack for math mode list labels
        newtext = re.sub(r"\[\$G_(.)\$:\]",r"[G\1:]",newtext)

    if component.writer.lower() in ["orcca"]:
        newtext = re.sub(r"\\minitoc","",newtext)
        newtext = re.sub(r"\\begin{myProof}",r"\\begin{solution}",newtext)
        newtext = re.sub(r"\\end{myProof}",r"\\end{solution}",newtext)
        newtext = utilities.replacemacro(newtext,"textref",2,'')
        newtext = re.sub(r"\\(begin|end){steps}",r"\\\1{enumerate}",newtext)
        newtext = re.sub(r"\\(top|mid|bottom)rule",r"\\hline",newtext)
        newtext = re.sub(r"{minipage}\[[a-z]*\]{[^{}]*}",r"{minipage}",newtext)
        newtext = re.sub(r"{minipage}{[^{}]*}",r"{minipage}",newtext)

    if component.writer.lower() in ["orcca"]:
        newtext = re.sub(r"\\unless\\ifvalpo","",newtext)
        newtext = re.sub(r"\\minitoc","",newtext)
        newtext = re.sub(r"\\mtcskip","",newtext)
        newtext = re.sub(r"{\$u\$}",r"$u$",newtext)

    if component.writer.lower() in ["doob"]:
        newtext = re.sub(r"%.*", "\n", newtext)
        newtext = re.sub(r"\\newpage", "\n", newtext)
        newtext = re.sub(r"\\titleformat", "\n", newtext)
        newtext = re.sub(r"\\mybreak", "\n", newtext)
        newtext = re.sub(r"\\break", " ", newtext)
        newtext = re.sub(r"\\hfuzz.*", "\n", newtext)
        newtext = re.sub(r"\\vbadness.*", "\n", newtext)
        newtext = re.sub(r"\\hbadness.*", "\n", newtext)
        newtext = re.sub(r"\\parindent.*", "\n", newtext)
        newtext = re.sub(r"\\noindent *", "", newtext)
        newtext = re.sub(r"\\eject *", "", newtext)
        newtext = re.sub(r"\\endgraf *", "", newtext)
        newtext = utilities.replacemacro(newtext,"sidefigure",2,'#1\n\n#2')
        newtext = re.sub(r"\\endproblem(\s+\\beginsolution.*?\\endsolution)", "\n" + r"\1" + "\n\\endproblem\n",newtext,0, re.DOTALL)
        newtext = re.sub(r"\\endproblem(\s+\\beginsolution.*?\\endsolution)", "\n" + r"\1" + "\n\\endproblem\n",newtext,0, re.DOTALL)
        newtext = re.sub(r"\\endproblem(\s+\\beginsolution.*?\\endsolution)", "\n" + r"\1" + "\n\\endproblem\n",newtext,0, re.DOTALL)
        newtext = re.sub(r"\\endproblem(\s+\\beginsolution.*?\\endsolution)", "\n" + r"\1" + "\n\\endproblem\n",newtext,0, re.DOTALL)
        newtext = re.sub(r"\\endproblem(\s+\\beginsolution.*?\\endsolution)", "\n" + r"\1" + "\n\\endproblem\n",newtext,0, re.DOTALL)
        newtext = re.sub(r"\\endproblem(\s+\\beginsolution.*?\\endsolution)", "\n" + r"\1" + "\n\\endproblem\n",newtext,0, re.DOTALL)
        newtext = re.sub(r"\\endproblem(\s+\\beginsolution.*?\\endsolution)", "\n" + r"\1" + "\n\\endproblem\n",newtext,0, re.DOTALL)
   # can there be more than 7 solutions?
        newtext = re.sub(r"\\newsection +([^\s]+)",r"\\section{\1}\\label{\1}",newtext)
        newtext = re.sub(r"\\beginproblem +([^\s]+)",r"\\begin{problem}[\1]\\label{p\1}",newtext)
        newtext = re.sub(r"\\endproblem",r"\\end{problem}",newtext)
        newtext = re.sub(r"(\\ref{)([^p])",r"\1p\2",newtext)  # assule all references are to problems
        newtext = re.sub(r"\\beginsolution +([^\n]+)",r"\\begin{solution}[\1]\\label{s\1}",newtext)
        newtext = re.sub(r"\\endsolution",r"\\end{solution}",newtext)

    if component.writer.lower() in ["sklaraa"]:
        for (Tag, ptxtag) in [
                  ("Definitions", "definition"),
                  ("Definition", "definition"),
                  ("Definitions and notation", "definition"),
                  ("Definition and notation", "definition"),
                  ("Remarks", "remark"),
                  ("Remark", "remark"),
                  ("Notation and terminology", "notation"),
                  ("Notation", "notation"),
                  ("Note", "note"),
                  ("Nota bene", "note")]:
            newtext = re.sub(r"\\begin{df}{" + Tag + "}(.*?)\\end{df}", r"\\begin{" + ptxtag + r"}\1\\end{" + ptxtag + r"}", newtext, 0, re.DOTALL)
        newtext = utilities.replacemacro(newtext,"warn",1,'\\begin{warning}#1\\end{warning}')
        newtext = re.sub(r"\\begin{exercise}\[([^{}]+)\]",r"\\begin{exercise}",newtext)
        newtext = re.sub(r"\\begin{example}{\s*}",r"\\begin{example}",newtext)
        newtext = re.sub(r"\\begin{example}{([^{}]+)}",r"\\begin{example}\\label{\1}",newtext)

    if component.writer.lower() in ["hitchman"]:
        newtext = re.sub(r"\\subsubsection\*?",r"\\subsection",newtext)
        newtext = re.sub(r"\\bigskip","",newtext)
        newtext = re.sub(r"\\medskip","",newtext)
        newtext = re.sub(r"\\begin{hmk}",r"\\begin{exercise}",newtext)
        newtext = re.sub(r"\\end{hmk}",r"\\end{exercise}",newtext)
        newtext = re.sub(r"\\begin{center}{*\\underline{Exercises}}*\\end{center}",r"\\subsection{Exercises}",newtext)
        newtext = re.sub(r"\\centerline{\\underline{Exercises}}",r"\\subsection{Exercises}",newtext)

    if component.writer.lower() in ["braille"]:
        newtext = re.sub(r"\\gammaup",r"\\gamma",newtext)

    if component.writer.lower() in ["bernoff"]:
        newtext = utilities.replacemacro(newtext,"resizebox",3,"#3")
        newtext = re.sub(r"{\\bf (unless|not|only|into|every|exists|unique|density|Hint|Example|Theorem)",
                          r"\\emph{\1", newtext)
        newtext = re.sub(r"{\\bf ([^{}]+)}", r"\\term{\1}", newtext)
        newtext = re.sub(r"{\\em ([^{}]+)}", r"\\term{\1}", newtext)
        newtext = re.sub(r"{\\scshape *", r"\\paragraphs{", newtext)
        newtext = re.sub(r"\\exercise *(.*?)" + "\n\n", r"\\begin{exercise}\1\\end{exercise}" + "\n\n", newtext, 0, re.DOTALL)
        newtext = re.sub(r"\\definition *(.*?)" + "\n\n", r"\\begin{definition}\1\\end{definition}" + "\n\n", newtext, 0, re.DOTALL)
        newtext = re.sub(r"\\chapter\s*\[([^[]*)\]\s*",r"\\chapter",newtext)
        newtext = re.sub(r"\\section\s*\[([^[]*)\]\s*",r"\\section",newtext)
        newtext = re.sub(r"\\subsection\s*\[([^[]*)\]\s*",r"\\subsection",newtext)
        newtext = re.sub(r"\\(subsection|section|chapter)","\n\n" + r"\\\1",newtext)
        newtext = re.sub(r"\s*\\\\}",r"}",newtext)
        newtext = re.sub(r"\s*\\medskip}",r"}",newtext)
        newtext = utilities.replacemacro(newtext,"addtolength",2,'')
        newtext = re.sub(r"\\endexample",r"\\endsol \\endexample",newtext)
        newtext = re.sub(r"\\example\b",r"\\begin{example}",newtext)
        newtext = re.sub(r"\\endexample\b",r"\\end{example}",newtext)
        newtext = re.sub(r"\\sol\b",r"\\begin{solution}",newtext)
        newtext = re.sub(r"\\endsol\b",r"\\end{solution}" + "\n",newtext)

    if component.writer.lower() in ["joefields"]:
        newtext = re.sub(r"\\wbvfill\b","",newtext)
        newtext = re.sub(r"\\wbitemsep\b","",newtext)
        newtext = utilities.replacemacro(newtext,"twsvspace",3,'')
        newtext = utilities.replacemacro(newtext,"hint",1, r'\begin{hint}#1\end{hint}')
        newtext = re.sub(r"\\(hints|textbook|workbook)pagebreak\b","",newtext)
        newtext = re.sub(r"\\rule\[-?[0-9.]+pt\]{[0-9.]+pt}{[0-9.]+pt}","",newtext)
        newtext = re.sub(r"\\hspace\{[^\{\}]+\}","",newtext)
        newtext = re.sub(r"\\begin{minipage}{.25\\textwidth}","",newtext)
        newtext = re.sub(r"\\end{minipage}","",newtext)
        newtext = re.sub(r"\\chapter\*",r"\\chapter",newtext)
        newtext = re.sub(r"\\chapter\[([^[]*)\]",r"\\chapter",newtext)
        newtext = re.sub(r"\\((sub)*)section\[([^\[\]]*)\]",r"\\\1section",newtext)
        newtext = re.sub(r"\s*{\s*(\\large)*\s*(\\bf)*\s*Exercises\s*-*\s*\\thesection\\*\s*}([^}]{2,60}\})",
                         r"\\begin{exercises}\3" + "\n\\end{exercises}",newtext,0, re.DOTALL)

        newtext = re.sub(r"\\begin{exercises}(.*?)\\begin{enumerate}(.*?)\\end{enumerate}\s*\\end{exercises}",
                         joefields_exer, newtext,0,re.DOTALL)

    if component.writer.lower() in ["erdman"]:
        newtext = re.sub(r"(\\(chapter|section|subsection)\**{\s*)(.)([^{}]+)(})", title_lower, newtext)
        newtext = re.sub(r"\\newtheorem\**({[^{}]+})\[.*?\]", r"\\newtheorem\1", newtext)
        newtext = utilities.replacemacro(newtext,"newtheorem",2,"")
        newtext = re.sub(r"\\begin{prf}",r"\\begin{solution}", newtext)
        newtext = re.sub(r"\\end{prf}",r"\\end{solution}", newtext)
        newtext = re.sub(r"\\begin{cau}",r"\\begin{caution}", newtext)
        newtext = re.sub(r"\\end{cau}",r"\\end{caution}", newtext)
        newtext = re.sub(r"\\quad\s*}",r"}", newtext)
        newtext = re.sub(r"\\cleardoublepage",r"", newtext)
        newtext = re.sub(r"\\df\{",r"\\term{", newtext)
        newtext = re.sub(r"\\vskip\s*[0-9]+\s*(true)*\s*[a-z]+",r"", newtext)

        component.guess_terminology = False

    if component.writer.lower() in ["vega"]:
        newtext = re.sub(r"{\\normalsize\s*",r"\\normalsize{", newtext)
        newtext = utilities.replacemacro(newtext,"normalsize",1,'#1')
        newtext = utilities.replacemacro(newtext,"scriptsize",1,'#1')
        newtext = re.sub(r"\footnotesize\s*","", newtext)

    if component.writer.lower() in ["graves"]:
        newtext = re.sub(r"\\lecture{",r"\\input{", newtext)
        newtext = re.sub(r"\\smallskip\s*{\s*\\fn\b",r"", newtext)
        newtext = re.sub(r"}\\noindent",r"", newtext)
        newtext = re.sub(r"}\s*\\smallskip\s*\\noindent",r"", newtext)
        newtext = re.sub(r"\\begin{ipython}",r"", newtext)
        newtext = re.sub(r"\\end{ipython}",r"", newtext)
        newtext = re.sub(r"\\begin{tlp}",r"\\tlp", newtext)
        newtext = re.sub(r"\\end{tlp}",r"", newtext)
        newtext = re.sub(r"\\begin{bmr}",r"\\begin{bmatrix}", newtext)
        newtext = re.sub(r"\\end{bmr}",r"\\end{bmatrix}", newtext)
        newtext = re.sub(r"\\begin{abmr}",r"\\left[\\begin{array}", newtext)
        newtext = re.sub(r"\\end{abmr}",r"\\end{array}\\right]", newtext)
        newtext = utilities.replacemacro(newtext,"tlp",3,r"\begin{tikzpicture}[scale=12/26]\node [left] at (0,0) {\( #1 = \)};{\footnotesize\draw[anchor=mid] (0,-1) grid (#2,1) \foreach \x/\y/\z in {#3}{(\x+1/2,1/2) node {\y} (\x+1/2,-1/2) node {\z}};}\end{tikzpicture}")
        newtext = re.sub(r"{\s*\\tiny\s*\\\[\s*\\begin\{tikz",r"\\begin{tikz", newtext)
        newtext = re.sub(r"\\\[\s*\\begin\{tikz",r"\\begin{tikz", newtext)
        newtext = re.sub(r"\\end\{tikzpicture\}\s*([,.]*)\s*\\\]\s*\}",r"\\end{tikzpicture}\1", newtext)
        newtext = re.sub(r"\\end\{tikzpicture\}\s*([,.]*)\s*\\\]",r"\\end{tikzpicture}\1", newtext)

    if component.writer.lower() in ["oscarlevin"]:
        newtext = re.sub(r"\\begin{parts}",r"\\begin{enumerate}" + "\n", newtext)
        newtext = re.sub(r"\\end{parts}",r"\\end{enumerate}" + "\n", newtext)
        newtext = re.sub(r"\\begin{defbox}{([^{}]+)}",r"\\begin{convention}[\1]" + "\n", newtext)
        newtext = re.sub(r"\\end{defbox}",r"\\end{convention}" + "\n", newtext)
        newtext = re.sub(r"\\vfill\s*","", newtext)
        newtext = re.sub(r"\\noanswers\s*","", newtext)
        newtext = re.sub(r"\\withanswers\s*","", newtext)
        newtext = re.sub(r"\\starthwsol\s*","", newtext)
        newtext = re.sub(r"\\finishhwsol\s*","", newtext)
        newtext = re.sub(r"\\part ",r"\item ", newtext)
        newtext = utilities.replacemacro(newtext,"tikz",1,"\\begin{tikzpicture}#1\\end{tikzpicture}")

        findquestions = "\\\\begin\{questions\}(.*?)\\\\end{questions}"
        newtext = re.sub(findquestions,convertquestions,newtext,0,re.DOTALL)

    # probably obsolete because of how questions_to_exercises handles parts and subparts
    if component.writer.lower() in ["exam"]:
        newtext = re.sub(r"\\part ",r"\item ", newtext)
        newtext = re.sub(r"\\subpart ",r"\item ", newtext)

    if component.writer.lower() in ["rosoff"]:
        newtext = separatecomponents.killcomments(newtext)
        try:
            this_title = re.search(r"\\textbf{{\\large (.*?)}}", newtext, re.DOTALL).group(1)
            this_title = re.sub(r"\s+", " ", this_title)
        except:
            print("Error: no title in")
            print(component.inputfilename)
            die()
            
        print("found the title:  ", this_title)

        # probably this shoudl be later?
        newtext = re.sub(r"\\SI{([^{}]*)}{([^{}]*)}", utilities.SItoPTX, newtext)
        newtext = re.sub(r"\\si{([^{}]*)}", utilities.sitoPTX, newtext)
        newtext = re.sub(r"\$(<quantity>.{,20}</quantity>)\$", r"\1", newtext)
        newtext = re.sub(r"\$(<quantity>.{,50}</quantity>)\$", r"\1", newtext)
        newtext = re.sub(r"\$(<quantity>.{,100}</quantity>)\$", r"\1", newtext)
        newtext = re.sub(r"\$(<quantity>.{,300}</quantity>)\$", r"\1", newtext)
     #   this_title = "aBcDeF"
   #     newtext = re.sub(r"\\textbf{{\\large (.*?)}}",r"\\title{\1}", newtext)
        newtext = re.sub(r"\s*\\raggedleft\b","", newtext)
        newtext = re.sub(r"\s*\\shortlines\b","", newtext)
        newtext = re.sub(r"\s*\\longlines\b","", newtext)
        newtext = re.sub(r"\s*\\hrulefill\b","", newtext)
        newtext = re.sub(r"\s*\\enspace\b","", newtext)
        newtext = re.sub(r"subsubsection\*", "subsubsection", newtext)
        newtext = utilities.replacemacro(newtext,"subsubsection",1,"#1")

        newtext = re.sub(r"\\begin{tabularx}", r"\\starttabularx", newtext)
        newtext = utilities.replacemacro(newtext,"starttabularx",2,r"\\begintabularx")
        newtext = re.sub(r"\\end{tabularx}", r"\\endtabularx", newtext)
        newtext = re.sub(r"\\begintabularx(.*?)\\endtabularx", undo_tabularx, newtext, 0, re.DOTALL)

        newtext = utilities.replacemacro(newtext,"titledquestion",1,"\\question <title>#1</title>")

        newtext = re.sub(r"\\makebox\[\\linewidth\]\s*\{(.{,100})\}\}\}", r"\1}}", newtext)
        newtext = re.sub(r"\\makebox\[.{,5}\\linewidth\]\s*\{(.{,100})\}\}", r"\1}}", newtext)
        newtext = re.sub(r"\$\s*\\underline{\\hspace{[^{}]*}}\s*\$",'<fillin characters="10"/>', newtext)
        newtext = re.sub(r"\\underline{\\hspace{[^{}]*}}",'<fillin characters="10"/>', newtext)

        newtext = re.sub(r"\.PNG",".png", newtext)

        newtext = re.sub(r"\s*\\vspace{0pt}","", newtext)
        newtext = re.sub(r"\s*\\vspace{[^{}]*}","", newtext)

        this_filestub = re.sub(".*/", "", component.inputfilename)
        this_filestub = re.sub("\..*", "", this_filestub)

           # maybe this should be handled by more general code:
        newtext = re.sub(r"(\\begin{questions})",
                         r"\\section{xx}\\label{" + this_filestub + "}" + "\n" 
                              + r"\\begin{worksheet}" + "\n" + "<title>" + this_title + "</title>\n" + r"\1",
                         newtext)
        newtext = re.sub(r"(\\end{questions})",
                         r"\1" + "\n" + r"\\end{worksheet}" + "\n",
                         newtext)

          # the boundary between two (presumably sidebyside) minipages
        newtext = re.sub(r"\\end{minipage}\s*\\hspace{[^{}]*}\s*\\begin{minipage}\[t\]{0\.[0-9]*\s*\\[a-z]*}","", newtext)
        newtext = re.sub(r"\\end{minipage}\s*\\begin{minipage}\[t\]{0\.[0-9]*\s*\\[a-z]*}","", newtext)
        newtext = re.sub(r"\\end{minipage}\s*\\hspace{[^{}]*}\s*\\begin{minipage}\[t\]\[[^\[\]]*\]{0\.[0-9]*\s*\\[a-z]*}","", newtext)
        newtext = re.sub(r"\\end{minipage}\s*\\begin{minipage}\[t\]\[[^\[\]]*\]{0\.[0-9]*\s*\\[a-z]*}","", newtext)

        newtext = re.sub(r"\\begin{minipage}\[t\]{0\.[0-9]*\s*\\[a-z]*}","\n\n" + r"\\begin{sidebyside}" + "\n\n", newtext)
        newtext = re.sub(r"\\begin{minipage}\[t\]\[[^\[\]]*\]{0\.[0-9]*\s*\\[a-z]*}","\n\n" + r"\\begin{sidebyside}" + "\n\n", newtext)
        newtext = re.sub(r"\\end{minipage}\s*\\hspace{[^{}]*}","ERROR ERROR ERROR", newtext)
        newtext = re.sub(r"\\end{minipage}","\n\n" + r"\\end{sidebyside}" + "\n\n", newtext)

        newtext = re.sub(r"\\begin{multicols\**}\{2\}", "\n\n" + r"\\begin{sidebyside}" + "\n\n", newtext)
        newtext = re.sub(r"\\columnbreak", "\n\n" + r"\\end{sidebyside}" + "\n\n" + r"\\begin{sidebyside}" + "\n\n", newtext)
        newtext = re.sub(r"\\end{multicols\**}", "\n\n" + r"\\end{sidebyside}" + "\n\n", newtext)

        newtext = re.sub(r"(\\begin{questions})(.*?)(\\end{questions})", lambda match: questions_to_exercises(match, ""), newtext, 0, re.DOTALL)

        newtext = utilities.replacemacro(newtext,"fullwidth",1,"#1")
        newtext = re.sub(r"\\newpage", "<pagebreak/>", newtext)

    # conversion for Tom Judson's AATA
    if component.writer.lower() in ["judson", "thron"]:
        logging.warning("author-specific conversion for %s", component.writer)

        # thron's hints
        newtext = re.sub(r"\\hyperref\[([a-z]+):([a-zA-Z_]+):hints\]{\(\*Hint\*\)}",r"Hint~\\ref{\1:\2:hints}",newtext)

        newtext = re.sub(r"\\newcommand{\\terminology}.*","",newtext)
        newtext = re.sub(r"(\\underline{)-<[^<>]+>-}",r"\1}",newtext)

        newtext = utilities.replacemacro(newtext,"chaptermark",1,"")

        newtext = re.sub(r"\\rule{5.00in}{.5pt}","",newtext)
        newtext = re.sub(r"\\rule\[-1.2ex\]{0pt}{0pt}","",newtext)

        newtext = re.sub(r"\\begin{dialogue}",r"",newtext)
        newtext = re.sub(r"\\end{dialogue}",r"",newtext)
        newtext = re.sub(r"\\speak\b","\n\n" + r"\\textbf",newtext)

        newtext = re.sub(r"\\term\*",r"\\termx",newtext)

        # Judson's chapters
        # assuming no {} in chapter titles
        newtext = re.sub(r"\\chap\b{([^{}]*)}{([^{}]*)}",r"\\chapter{\1}\\label{\2}",newtext)

        # when terms are being defined
        newtext = re.sub(r"\\boldemph{([^{}])+}",terminology_no_cr,newtext)   # Judson

        # a special conversion for Judson's examples
        filenamestub = re.search("([a-zA-Z0-9]*)(\.tex)*",component.inputfilename).group(1)
        newtext = re.sub(r"\\begin\s*{example}{([^{}]+)}",
                     r"\\begin{example}\\label{example:"+filenamestub+r":\1}",newtext)

        # not sure if this location is too late

        for jj in range (100):
            newtext = re.sub(r"(\\begin\s*{exercise}){}", r"\1{x" + str(jj) + "}", newtext)

        # similar for exercises  # need to fix the source in 13.3
        newtext = re.sub(r"\\begin\s*{exercise}{([^{}]+)}",
                     r"\\begin{exercise}\\label{exercise:"+filenamestub+r":\1}",newtext)

        # similar for exercises  # need to fix the source in 13.3
        newtext = re.sub(r"\\begin\s*{prop}{([^{}]+)}",
                     r"\\begin{proposition}\\label{proposition:"+filenamestub+r":\1}",newtext)
        newtext = re.sub(r"\\end\s*{prop}",r"\\end{proposition}",newtext)

        # convert Judson's exercises from a list to theorem-like markup
        # excersises are in \section*{Exercises}
        newtext = re.sub(r"\\markright\{Exercises\}","",newtext,0,re.I)

        findexercisesection = "\\\\section\*?\{Exercises\}(.*?)(\\\\subsection|$)"
        newtext = re.sub(findexercisesection,convertexercises,newtext,1,re.DOTALL)

        newtext = re.sub(r"\\nonumfootnote",r"\\numfootnote",newtext)

        # Judson's historical notes
        newtext = re.sub(r"\\histhead",r"\\begin{historicalnote}",newtext)
        newtext = re.sub(r"\\histbox\s*\n}",r"}\n\\end{historicalnote}",newtext)
        newtext = re.sub(r"\\histbox",r"\\end{historicalnote}",newtext)
        newtext = re.sub(r"{\s*\\small\s*\\histf",r"\\donothing{ \\histf",newtext)
        newtext = utilities.replacemacro(newtext,"donothing",1,"#1")
        newtext = re.sub(r"\\histf",r"",newtext)

        # font size directives for tables.  (Would be good to fix the LaTeX source.)
        newtext = re.sub(r"{\\small[ \n]*\\begin",r"\\begin",newtext)  
        newtext = re.sub(r"\n *} *\n *(\\end{table})",r"\1",newtext)  

        newtext = re.sub(r"\\tikzpreface\{([^{}]*)\}\s*","",newtext,0,re.DOTALL)

        newtext = re.sub(r"\\begin{summary}","\\paragraphs{Summary} \\\\begin{itemize}\n",newtext)
        newtext = re.sub(r"\\end{summary}","\\end{itemize}\n",newtext)

        newtext = re.sub(r"{\\hspace\\fill\$\\square\$\\par\\medskip}","",newtext)

    newtext = re.sub(r"\\Dfn\b",r"\\terminology",newtext)

    #spacing in formulas, to un-confuse MathJax
#    newtext = re.sub(r"\\hspace\**\{-*[0-9]+pt\}",r"\\ ",newtext)

    # I have no idea what this next thing is supposed to do
    newtext = re.sub(r"\\\\\[[&\]]\]*",r"\\\\ ",newtext)

    newtext = utilities.replacemacro(newtext,"aside",1,r"\begin{aside}#1\end{aside}")


    # conversion for Boman's real analysis

      # markers for end of theorem, example, proof, etc.
      # these should be part of the macros
    newtext = re.sub(r"\\xqed\{\\[a-z]*\}{}",r"",newtext)
    newtext = re.sub(r"\\xqedhere\{[^{}]*\}\{[^{}]*\}{}",r"",newtext)

    newtext = re.sub(r"\\LabelProblem\{([^{}]*)\}\{[^{}]*\}",r"\\label{\1}",newtext)
    newtext = re.sub(r"\\LabelProblem\{([^{}]*)\}\{"+utilities.one_level_of_brackets+r"\}",r"\\label{\1}",newtext,0,re.DOTALL)
    newtext = re.sub(r"\\IndexTheorem\{([^{}]*)\}\{[^{}]*\}",r"\\index{\1}",newtext)
    newtext = re.sub(r"\\IndexTheorem\{([^{}]*)\}\{"+utilities.one_level_of_brackets+r"\}",r"\\index{\1}",newtext)
    newtext = re.sub(r"\\IndexCorollary\{([^{}]*)\}\{[^{}]*\}",r"\\index{\1}",newtext)
    newtext = re.sub(r"\\IndexLemma\{([^{}]*)\}\{[^{}]*\}",r"\\index{\1}",newtext)
    newtext = re.sub(r"\\IndexLemma\{([^{}]*)\}",r"\\index{\1}",newtext)
    newtext = re.sub(r"\\IndexDefinition\{([^{}]*)\}\{[^{}]*\}",r"\\index{\1}",newtext)

    newtext = re.sub(r"\\begin{ProofOutline}",r"\\begin{proofsketch}",newtext)
    newtext = re.sub(r"\\end{ProofOutline}",r"\\end{proofsketch}",newtext)

    newtext = re.sub(r"\\break\b",r" ",newtext)

    newtext = re.sub(r"\\(begin|end){landscape}", "", newtext)
    newtext = re.sub(r"\\(begin|end){onehalfspace}", "", newtext)

    newtext = re.sub(r"\\underbar\b",r"\\emph",newtext)

    newtext = re.sub(r"\\((sub)*)section\[[^\[\]]*\]",r"\\\1section",newtext)

    # Cremona's MA257 notes
    logging.debug("deleting ifshowproofs")
    newtext = re.sub(r"\\ifshowproofs(.*?)\\fi",r"\1",newtext,0,re.DOTALL)
    # need to do the following in math mode, and something else in text
    newtext = re.sub(r"{\\emcol\s+([^}]+)}",r"\\emph{\1}",newtext)

    if component.writer == "mitchkeller":
        newtext = re.sub(r"\[\\smallskipamount\]","",newtext)

    if component.writer == "loek":
        newtext = re.sub(r"item\[\$","item[",newtext)
        newtext = re.sub(r"\$\] ","] ",newtext)
        newtext = re.sub(r"\$\)\] ",")] ",newtext)

    if component.writer == "mahavier":
        newtext = re.sub(r"\\hspace{[^{}]*}", "", newtext)
        newtext = re.sub(r"\\vspace{[^{}]*}", "", newtext)
        newtext = re.sub(r"\\begin{chapterannotation}", "", newtext)
        newtext = re.sub(r"\\end{chapterannotation}", "", newtext)
        newtext = re.sub(r"\\begin{annotation}", " EXTRA", newtext)
        newtext = re.sub(r"\\end{annotation}", "", newtext)
        newtext = re.sub(r"\\endnote", r"\\footnote", newtext)
        newtext = re.sub(r"\$<\$", r"$ \lt $", newtext)
        newtext = utilities.replacemacro(newtext,"newtheorem",2,"")
        newtext = utilities.replacemacro(newtext,"caption",1,"XXcaptionXX#1YY")

             # this deletes the setlength, which it shouldn't
        newtext = re.sub(r"\s*(\\setlength{\\unitlength}{[^{}]*}\s*)\\begin{picture}(.*?)\\end{picture}\s*",
                          "\n\n" + r"\\begin{lateximage}" + "\n" + r"\1" +
                               r"\\begin{xxpicture}" + r"\2" + r"\\end{xxpicture}" + "\n" + r"\\end{lateximage}" + "\n\n",
                          newtext, 0, re.DOTALL)

    #    newtext = re.sub(r"\\begin{figure}\s*(\\begin{lateximage})(.*?)(\\end{lateximage})\s*\\caption{([^{}]*)}\s*\\label{([^{}]*)}\s*\\end{figure}\s*",
        newtext = re.sub(r"\\begin{figure}\s*(\\begin{lateximage})(.*?)(\\end{lateximage})\s*XXcaptionXX(.*?)YY\s*\\label{([^{}]*)}\s*\\end{figure}\s*",
                         "\n\n" + r'<figure xml:id="\5"><caption>\4</caption>\1\2\3</figure>',
                         newtext, 0, re.DOTALL) 
        newtext = re.sub(r"\\begin{figure}\[[^\[\]]*\]\s*(\\begin{lateximage})(.*?)(\\end{lateximage})\s*XXcaptionXX(.*?)YY\s*\\label{([^{}]*)}\s*\\end{figure}\s*",
                         "\n\n" + r'<figure xml:id="\5"><caption>\4</caption>\1\2\3</figure>',
                         newtext, 0, re.DOTALL) 

    if component.writer == "schmitt":
        newtext = re.sub(r"\\marginpar{\s*}", "", newtext)
        newtext = re.sub(r"\\marginparbmw", r"\\marginpar", newtext)
        newtext = re.sub(r"\\marginpar", r" EXTRA\\footnote", newtext)
 #       newtext = utilities.replacemacro(newtext,"thomasee",1,"Thomas: #1\n\n")
 #       newtext = utilities.replacemacro(newtext,"larsonfive",1,"Larson: #1\n\n")
 #       newtext = utilities.replacemacro(newtext,"stewarts",1,"Stewart: #1\n\n")
 #       newtext = utilities.replacemacro(newtext,"bmw",1,"BMW: #1\n\n")
 #       newtext = utilities.replacemacro(newtext,"valpo",1,"Valpo: #1\n\n")

        newtext = utilities.replacemacro(newtext,"fi",0,"")
        newtext = utilities.replacemacro(newtext,"unless",0,"")
        newtext = utilities.replacemacro(newtext,"ifvalpo",0,"")
        newtext = utilities.replacemacro(newtext,"minitoc",0,"")
        newtext = utilities.replacemacro(newtext,"mtcskip",0,"")
        newtext = re.sub(r"\\vskip[0-9\.]+in\s*\\hrule", "", newtext)
        newtext = re.sub(r"\\hrule\s*\\vskip[0-9\.]+", "", newtext)
        newtext = re.sub(r"\\hrule\s", "", newtext)
        newtext = re.sub(r"\[\s*Hint\s*[0-9]*:\s*([^\]]+)\]", r"\\hint{\1}", newtext)
        newtext = utilities.replacemacro(newtext,"hint",1, r"\begin{hint}#1\end{hint}")

    if component.writer == "bogart":
  #      newtext = re.sub(r"\\itemitemh", r"\\item", newtext)
        newtext = re.sub(r"\\Chi\b", r"\\chi", newtext)
        newtext = re.sub(r"\\Chi_", r"\\chi_", newtext)
        newtext = utilities.replacemacro(newtext,"solution",1, r"\begin{solution}#1\end{solution}")
        newtext = utilities.replacemacro(newtext,"tallstrut",1, " ")
        problem_type = {'m':'motivation',
                    'e':'essential',
                    's':'summary',
                    'i':'interesting',
                    'ei':'essential and interesting',
                    'es':'essential for this or the next section',
                    'esi':'essential for this or the next section, and interesting',
                    'h':'difficult',
                    'ih':'interesting and difficult',
                    'x':'',
                    '':''}
        for pt in problem_type:
            the_letter = pt
            the_description = problem_type[pt]
            if the_letter:
                newtext = re.sub(r"\\item" + the_letter + r"\s",
                                 r"\\item " + "(" + the_description + ")" + "\n", newtext)



    if component.writer == "atchison":
        newtext = re.sub(r"\\import{\./([^}]+)}{([^}]+)}",r"\\import{\1\2}",newtext)
        newtext = re.sub(r"\\vspace{[^{}]*}\s*~*\\\\",r"",newtext)
        newtext = re.sub(r"}~+",r"}",newtext)
        newtext = re.sub(r"{\\tmstrong{Objectives*:\s*([^{}]+)}}\s*(\\pp)*",r"\\begin{objectives}\1\end{objectives}",newtext)
        newtext = re.sub(r"\\pp\b",r"",newtext)

    if component.writer == "openintro":


        newtext = re.sub(r"\\appendix.*", r"", newtext, 1, re.DOTALL)
        newtext = re.sub(r"\\setlength{\\itemsep}{[0-9\-.]+mm}", r"", newtext, 1, re.DOTALL)

        newtext = re.sub(r"\\color{oiB}", r"", newtext)

        newtext = re.sub(r"\\begin{chapterpage}", r"\\chapter", newtext)
        newtext = re.sub(r"\\end{chapterpage}", r"", newtext)

        newtext = re.sub(r"\\begin{spacing}{[^{}]+}", r"", newtext)
        newtext = re.sub(r"\\end{spacing}", r"", newtext)

        newtext = re.sub(r"(\\index{[^{}]+)\|(\(|\))}", r"\1}", newtext)

        newtext = re.sub(r"\\section\[[^\[\]]+\]", r"\\section", newtext)
        newtext = re.sub(r"\\noindent *", r"", newtext)
        newtext = re.sub(r"\\footnotemark *", r"", newtext)
        newtext = re.sub(r"\\MakeLowercase *", r"", newtext)

        newtext = re.sub(r"\\qt{([^{}]+)(\\label{[^{}]+})}", r"[\1]\2", newtext)

        newtext = re.sub(r"{\\small\b", r"\\makeitsmall{", newtext)
        newtext = utilities.replacemacro(newtext,"makeitsmall",1, r"#1")

        newtext = utilities.replacemacro(newtext,"pmb",1, r"#1")
        newtext = utilities.replacemacro(newtext,"chapterintro",1, r"#1")
        newtext = utilities.replacemacro(newtext,"sectionintro",1, r"#1")
        newtext = utilities.replacemacro(newtext,"D",1, r"#1")
        newtext = utilities.replacemacro(newtext,"chaptertitle",1, r"")

        newtext = utilities.replacemacro(newtext,"chaptersection",1, r"")

        newtext = re.sub(r"\\begin{eqnarray\*}\s+(.+)\s+\\end{eqnarray\*}",
                         r"\\begin{equation}" + "\n" + r"\1" + "\n" + r"\\end{equation}",
                         newtext)
        newtext = re.sub(r"\\begin{eqnarray\*}\s+(.+)\s+(\\label{[^{}]+})\s+\\end{eqnarray\*}",
                         r"\\begin{equation}\2" + "\n" + r"\1" + "\n" + r"\\end{equation}",
                         newtext)

        newtext = utilities.replacemacro(newtext,"eocesol",1, "\\begin{solution}#1\\end{solution}")

        # these occur inside examples
        newtext = re.sub(r"\\(begin|end){description}", r"\\\1{solution}", newtext)

        newtext = re.sub(r"\\(begin|end){exercisewrap}", r"", newtext)
        newtext = re.sub(r"\\(begin|end){nexercise}", r"\\\1{exercise}", newtext)
        newtext = re.sub(r"\\addtocounter{footnote}{[^{}]*}\s*", "", newtext)
        newtext = re.sub(r"\\end{exercise}\s*\\footnotetext{([^{}]+)}", r"\\answer{\1}\\end{exercise}" + "\n\n", newtext)
        newtext = utilities.replacemacro(newtext,"answer",1,"beginAnswer#1endAnswer")
        newtext = re.sub(r"\\end{exercise}\s*beginAnswer(.*?)endAnswer", r"\\begin{answer}\1\\end{answer}\\end{exercise}" + "\n\n", newtext,0, re.DOTALL)
        newtext = re.sub(r"beginAnswer(.*?)endAnswer", r"\\begin{answer}\1\\end{answer}" + "\n", newtext,0, re.DOTALL)
        newtext = re.sub(r"\\(begin|end){examplewrap}", r"", newtext)
        newtext = re.sub(r"\\begin{nexample}\s*{([^{}]+)}(.*?)\\end{nexample}", r"\\begin{example}\1\\begin{solution}\2\\end{solution}\\end{example}", newtext, 0, re.DOTALL)
        newtext = re.sub(r"\\(begin|end){nexample}", r"\\\1{example}", newtext)

   #     newtext = re.sub(r"\\includechapter{[0-9]*}{([^{}]+)}",r"\\include{\1/TeX/\1.tex}" + "\n" + r"\\include{\1/TeX/\1_ex.tex}",newtext)
        newtext = re.sub(r"\\includechapter{[0-9]*}{([^{}]+)}",r"\\include{\1/TeX/\1.tex}" + "\n",newtext)
        newtext = re.sub(r"(\\raisebox\{[^\{\}]+\})\[[^\[\]]+\]",r"\1",newtext)

        # delete the page range option on the index
        newtext = re.sub(r"\|\)}",r"}",newtext)
        newtext = re.sub(r"\|\(}",r"}",newtext)

        newtext = re.sub(r"\\begin{tipBox}\s*{",r"\\begin{aside}",newtext)
        newtext = re.sub(r"}\s*\\end{tipBox}",r"\\end{aside}",newtext)

        newtext = re.sub(r"{minipage}\[[a-z]*\]{[^{}]*}",r"{minipage}",newtext)
        newtext = re.sub(r"{minipage}{[^{}]*}",r"{minipage}",newtext)

        newtext = re.sub(r"\\_\\hspace\{[^{}]+\}",r"\\_",newtext)

        newtext = re.sub(r"\\begin{adjustwidth}{[^{}]*}{[^{}]*}", "", newtext)
        newtext = re.sub(r"\\end{adjustwidth}", "", newtext)

        newtext = re.sub(r"\\(calcbutton|calctext)",r"\\texttt",newtext)
        newtext = utilities.replacemacro(newtext,"calctextmath",1, r"\texttt{$#1$}")

        newtext = utilities.replacemacro(newtext,"oiRedirect",2, " XXoiRedirect{#1}{**}XX ")
    #    newtext = utilities.replacemacro(newtext,"oiRedirect",2, "<!--MISSING{#1}{#2}oiRedirect-->")

        # eoce means "end of chapter exercise", which should be moved to the appropriate place
     #   newtext = re.sub(r"\\eoce\s*\{\s*\\qt\{([^{}]+)\}", r"\\eoce{\\exercisetitle{\1}", newtext)
        newtext = re.sub(r"\\eoce\s*\{\s*\\qt\{([^{}]+)\}", r"\\eoce{[\1]", newtext)
        newtext = utilities.replacemacro(newtext,"eoce",1, r"\begin{exercise}#1\end{exercise}")

        newtext = re.sub(r"\\marginpar\[.*?\]",r"\\footnote",newtext,0,re.DOTALL)

        newtext = re.sub(r"\\begin{parts}",r"\\begin{enumerate}",newtext)
        newtext = re.sub(r"\\end{parts}",r"\\end{enumerate}",newtext)

  #      newtext = re.sub(r"\\begin{caution}",r"\\begin{warning}",newtext)
  #      newtext = re.sub(r"\\end{caution}",r"\\end{warning}",newtext)

        newtext = re.sub(r"(\\tBoxTitle)\[\]",r"\1",newtext)

        # recheck this
        newtext = re.sub(r"\\tBoxTitle{\\videohref{([^{}]+)}([^{}]*)}",r"\\tBoxTitle{\2}\\vvideohref{\1}",newtext)

        newtext = re.sub(r"\s*{\s*\\tBoxTitle{([^{}]+)}",r"[\1]",newtext)
        newtext = re.sub(r"}\s*\\end{termBox}",r"\\end{definition}",newtext)
        newtext = re.sub(r"\\begin{termBox}",r"\\begin{definition}",newtext)
        newtext = re.sub(r"\\end{termBox}",r"\\end{definition}",newtext)

        newtext = utilities.replacemacro(newtext,"tipBoxTitle",1,r"[#1]")

        # this only catches the simplest examples:  need to change the source
        # it misses examples with labels, which is good because the label need to be moved.
        newtext = re.sub(r"\\begin{example}\s*\{([^{}]+)\}\s*([^{}]*)\\end{example}",
                  r"\\begin{example}\1\\begin{solution}\2\\end{solution}\\end{example}\n",newtext)
        newtext = re.sub(r"\\begin{warning}\s*\{([^{}]+)\}\s*(.*?)\\end{warning}",
                  r"\\begin{warning}[\1]\2\\end{warning}\n",newtext,0, re.DOTALL)

        newtext = remap_example(newtext)

        # only the simplest exercises.  need something like remap_example
        newtext = re.sub(r"\\begin{exercise}\s*(.*?)\s*\\footnote{([^{}]*)}\s*\\end{exercise}",
                  r"\\begin{exercise}\1\\begin{hint}\2\\end{hint}\\end{exercise}\n",newtext,0,re.DOTALL)

        newtext = re.sub(r"\\highlightT\b",r"\\textbf",newtext)
        newtext = re.sub(r"\\highlightO\b",r"\\textbf",newtext)
        newtext = re.sub(r"\\highlight\b",r"\\textbf",newtext)

        newtext = re.sub(r"\\var{",r"\\texttt{",newtext)
        newtext = re.sub(r"\\data{",r"\\texttt{",newtext)
        newtext = re.sub(r"\\resp{",r"\\texttt{",newtext)

        newtext = re.sub(r"<\s*http","http",newtext)

        newtext = re.sub(r"\\section\[[^\]]*\]",r"\\section",newtext)

        newtext = re.sub(r"\\exercisesheader{}",r"\\section{Exercises}",newtext)

        newtext = re.sub(r"\\chapter\*",r"\\chapter",newtext)

        newtext = re.sub(r"\\us{}",r"_",newtext)

        newtext = re.sub(r"{ *\\addvspace{[0-9]+mm} *{{\\titlerule\[[0-9.]+mm\]}[<>em/ ]*}",r"",newtext)
        newtext = re.sub(r"\\addvspace{[0-9]+mm} *{{\\titlerule\[[0-9]+mm\]} \*\setupfont *{\\titlerule\[[0-9.]+mm\]} *}", "", newtext)

    if component.writer == "active":

        newtext = utilities.replacemacro(newtext,"framebox",1,"#1")

   #     newtext = re.sub(r"{\\begin{goals}",r"In this section, we strive to understand the ideas generated by the following important questions:" + "\n" + r"\\begin{objectives}" + "\n" + r"\\begin{itemize}",newtext)
        newtext = re.sub(r"{\\begin{goals}",r"\\begin{objectives}" + "\n" + r"\\begin{itemize}",newtext)
        newtext = re.sub(r"\\end{goals}}",r"\\end{itemize}\\end{objectives}",newtext)
        newtext = re.sub(r"\\begin{alphalist}",r"\\begin{enumerate}",newtext)
        newtext = re.sub(r"\\end{alphalist}",r"\\end{enumerate}",newtext)
        newtext = re.sub(r"\\begin{smallhint}",r"\\begin{hint}[smallhint]",newtext)
        newtext = re.sub(r"\\end{smallhint}",r"\\end{hint}",newtext)
        newtext = re.sub(r"\\begin{bighint}.*?\\end{bighint}","",newtext, 0, re.DOTALL)
        newtext = re.sub(r"\\begin{activitySolution}",r"\\begin{solution}",newtext)
        newtext = re.sub(r"\\end{activitySolution}",r"\\end{solution}",newtext)
        newtext = re.sub(r"\\begin{exerciseSolution}",r"\\begin{solution}",newtext)
        newtext = re.sub(r"\\end{exerciseSolution}",r"\\end{solution}",newtext)
        newtext = re.sub(r"\\begin{pa}",r"\\begin{previewactivity}",newtext)
        newtext = re.sub(r"\\end{pa}",r"\\end{previewactivity}",newtext)
        newtext = re.sub(r"\\begin{summary}",r"\\subsection{Summary}" +
                          "\n" + r"\\begin{itemize}" + "\n",newtext)
        newtext = re.sub(r"\\end{summary}",r"\\end{itemize}",newtext)

#        newtext = re.sub(r"\\begin{exercises}" + "\n\n",
#                         r"\\begin{exercises}" + "\n" + r"\\begin{enumerate}" + "\n\n",newtext)
#        newtext = re.sub("\n\n" + r"\\end{exercises}","\n\n" + r"\\end{enumerate}" + "\n" + r"\\end{exercises}",newtext)

        newtext = re.sub(r"\\parbox{\\boxwidth}","\\donothing",newtext)
        newtext = re.sub(r"\\parbox{6.25\s*in}","\\donothing",newtext)
        newtext = utilities.replacemacro(newtext,"donothing",1,"#1")
        newtext = re.sub(r"\\donothing","",newtext)
        newtext = re.sub(r"\s\\afterpa","",newtext)
        newtext = re.sub(r"\s\\aftera","",newtext)
        newtext = re.sub(r"\s\\afterexercises","",newtext)
        newtext = re.sub(r"\s\\afterex\b","",newtext)
        newtext = re.sub(r"\s\\nin\b","",newtext)
        newtext = re.sub(r"\s\\hrulefill","",newtext)
        newtext = re.sub(r"\\hspace\{[^\{\}]+\}","",newtext)
        newtext = re.sub(r"\\bex\b",r"\\begin{example}",newtext)
        newtext = re.sub(r"\\eex\b",r"\\end{example}",newtext)
        newtext = re.sub(r"&\s*=\s*&\s*",r"=\mathstrut & ",newtext)
        newtext = re.sub(r"\\ds\b\s*","",newtext)
        newtext = re.sub(r"\\subsection\*{Introduction}","",newtext)

        newtext = utilities.replacemacro(newtext,"resizebox",3,"#3")
 #       newtext = utilities.replacemacro(newtext,"raisebox",2,"#2")

        # trickiness below
        newtext = re.sub(r"(\\ba\b.*?\\ea\b)",
                         lambda match: utilities.replacein(match,r"\\item",r"\\hideitem"),
                         newtext,0,re.DOTALL)
        newtext = re.sub(r"(\\begin{itemize}.*?\\end{itemize})",
                         lambda match: utilities.replacein(match,r"\\item",r"\\hideitem"),
                         newtext,0,re.DOTALL)
        newtext = re.sub(r"((\\begin{exercises}).*?(\\end{exercises}))",
                         lambda match: utilities.replacein(match,r"\\item",
                              r"\\end{exercise} \\begin{exercise} ",
                              r"\\begin{exercise}\n","","",r"\\end{exercise}\n"),
                         newtext,0,re.DOTALL)
        newtext = re.sub(r"(\\begin{itemize}.*?\\end{itemize})",
                         lambda match: utilities.replacein(match,r"\\hideitem",r"\\item"),
                         newtext,0,re.DOTALL)
        newtext = re.sub(r"(\\ba\b.*?\\ea\b)",
                         lambda match: utilities.replacein(match,r"\\hideitem",r"\\item"),
                         newtext,0,re.DOTALL)

        newtext = re.sub(r"\begin{smallhint}\s*\ba\s*\item\s*Small hints for each of the prompts above.\s*\ea\s*\end{smallhint}","",newtext)
        newtext = re.sub(r"\begin{bighint}\s*\ba\s*\item Big hints for each of the prompts above.\s*\ea\s*\end{bighint}","",newtext)

    newtext = re.sub(r"\\sectionvideohref{([^{}]+)}([^{}]*)}",r"\2\\vvideohref{\1}}",newtext)
    newtext = re.sub(r"\\videohref{([^{}]+)}",r"\\vvideohref{\1}",newtext)

    if component.target == 'ptx':
        newtext = re.sub(r"\\underline\{\s*\\hskip\s*[^{}]+\}","<fillin/>",newtext)

    component.preprocess_counter += 1

    return(newtext)

###############
def tabtolist(txt):

    the_inside = txt.group(1)

    the_inside = re.sub(r" *\\indent +[a-z]+\. *\\[^ ]", r"\\item ", the_inside)
    return "\\begin{enumerate}\n" + the_inside + "\n" + "\\end{enumerate}"

###############

def tableformat(txt):

    the_inside = txt.group(1)

    the_inside = re.sub(r"\\_6", "", the_inside)
    the_inside = re.sub(r"\+[0-9]+", "", the_inside)
    the_inside = re.sub(r"\\\|6", "&", the_inside)
    the_inside = re.sub(r"\\_[0-9]*", "", the_inside)
    the_inside = re.sub(r"\|", "&", the_inside)

    return the_inside + "\n" + "\\end{tabular}"

###############

def undo_tabularx(txt):

    the_text = txt.group(1)

    the_text = re.sub(r"&", "\n\n", the_text)
    the_text = re.sub(r"\\\\\[[^\[\]]*\]", "\n\n", the_text)
    the_text = re.sub(r"\\\\", "\n\n", the_text)

    return "\n\n" + the_text + "\n\n"

def questions_to_exercises(txt, keeptags):

    opening_tag = txt.group(1)
    the_text = txt.group(2)
    closing_tag = txt.group(3)

    print("============== questions_to_exercises")
 #   print the_text

    # note that this step is not actually necessary, because the other steps cancel each other
    if "\\question" not in the_text:
        return the_text

    while "\\question " in the_text:
        the_text = re.sub(r"\\question\b(.*?)(\\question|\\end{minipage}|\\newpage|\\begin{minipage}|$)",
                          r"\\beginquestion\1\\endquestion\2",
                          the_text,1,re.DOTALL)

    while "\\part " in the_text:
        the_text = re.sub(r"\\part\b(.*?)(\\part |\\end{parts}|\\newpage|\\end{minipage}|\\endquestion|\\end{tab)",
                          r"\\beginpart\1\\endpart\2",
                          the_text,1,re.DOTALL)

    while "\\subpart " in the_text:
        the_text = re.sub(r"\\subpart\b(.*?)(\\subpart|\\end{subparts}|\\newpage|\\end{minipage})",
                          r"\\beginsubpart\1\\endsubpart\2",
                          the_text,1,re.DOTALL)


    # twice, because \question is in the re

#    the_text = re.sub(r"\\question\b", r"\\endquestion" + "\n" + r"\\beginquestion", the_text)
#    the_text += "\\endquestion\n"
#      # we now have beginquestion-endquestion pairs, with an extra endquestion:
#    the_text = re.sub(r"\\endquestion", "", the_text, 1)
#
#    # not sure if this should be inside or outside this function.
#    # or if this problem applies to anything else
#    the_text = re.sub(r"(\\newpage|<pagebreak\s*/>|<sidebyside[^>]*>|</sidebyside>)\s*(\\endquestion)", r"\2" + "\n" + r"\1", the_text)
#    the_text = re.sub(r"(\\newpage|<pagebreak\s*/>|<sidebyside[^>]*>|</sidebyside>)\s*(\\endquestion)", r"\2" + "\n" + r"\1", the_text)
#
#    the_text = re.sub(r"(\\beginquestion)\s*(\\newpage|<pagebreak\s*/>|<sidebyside[^>]*>|</sidebyside>)", r"\2" + "\n" + r"\1", the_text)

#    the_text = re.sub(r"(\\beginquestion)\s*(\\newpage|<pagebreak\s*/>|<sidebyside[^>]*>|</sidebyside>)", r"\2" + "\n" + r"\1", the_text)

    the_text = re.sub(r"(\\begin{sidebyside}|\\end{sidebyside}|\\newpage|<pagebreak\s*/>|)\s*(\\endquestion)", r"\2" + "\n" + r"\1", the_text)

#    the_text = re.sub(r"\\begin{parts}", "", the_text)
#    the_text = re.sub(r"\\end{parts}", "", the_text)
#    the_text = re.sub(r"\\begin{subparts}", "", the_text)
#    the_text = re.sub(r"\\end{subparts}", "", the_text)

    the_text = re.sub(r"\\beginquestion", r"\\begin{exercise}", the_text)
    the_text = re.sub(r"\\endquestion", r"\\end{exercise}", the_text)

    the_text = re.sub(r"\\beginpart", r"\\begin{task}", the_text)
    the_text = re.sub(r"\\endpart", r"\\end{task}", the_text)
    the_text = re.sub(r"\\beginsubpart", r"\\begin{subtask}", the_text)
    the_text = re.sub(r"\\endsubpart", r"\\end{subtask}", the_text)

    print("+++++++++++++ questions_to_exercises")
 #   print the_text

    if keeptags:
        return opening_tag + the_text + closing_tag
    else:
        return the_text

###############

def joefields_exer(txt):

    the_start = txt.group(1)
    the_text = txt.group(2)

    the_text = re.sub(r"\\item", r"\\end{exercise}" + "\n\n" + r"\\begin{exercise}", the_text)

    the_text = the_text + r"\end{exercise}"
    the_text = re.sub(r"^\s*\\end{exercise}", "", the_text)

    return r"\begin{exercises}" + "\n" + the_start + the_text + "\n" + r"\end{exercises}"

###############

def apex_conversions(text):

    newtext = text

    newtext = separatecomponents.killcomments(newtext)

    newtext = utilities.replacemacro(newtext,"ifthenelse",3,"#2")
    newtext = utilities.replacemacro(newtext,"protect",0,"")
    newtext = re.sub(r"mycaption", r"caption", newtext)

    newtext = re.sub(r"(\\caption{[^{}]+)}\w*(\\label{[^{}]+})", r"\1\2} ", newtext)

    newtext = re.sub(r"(\.|,)(\$+)", r"\2\1", newtext)
    newtext = re.sub(r"\$\\ttaxb\$", r"A \\vec{x} = \\vec{b}", newtext)
    newtext = re.sub(r"\\ev\\ ", r"eigenvector ", newtext)
    newtext = re.sub(r"\\ev ", r"eigenvector", newtext)
    newtext = re.sub(r"\\el\\ ", r"eigenvalue ", newtext)
    newtext = re.sub(r"\\el ", r"eigenvalue", newtext)
    newtext = re.sub(r"\\lda\\ ", r"$\\lambd$ ", newtext)
    newtext = re.sub(r"\\vx\\ ", r"$\\vec{x}$ ", newtext)
    newtext = re.sub(r"\\vx(\.|,)", r"$\\vec{x}$\1", newtext)
    newtext = re.sub(r"\\vy\\ ", r"$\\vec{y}$ ", newtext)
    newtext = re.sub(r"\\vy(\.|,)", r"$\\vec{y}$\1", newtext)
    newtext = re.sub(r"\\vu\\ ", r"$\\vec{u}$ ", newtext)
    newtext = re.sub(r"\\vu(\.|,)", r"$\\vec{u}$\1", newtext)
    newtext = re.sub(r"\\vv\\ ", r"$\\vec{v}$ ", newtext)
    newtext = re.sub(r"\\vv(\.|,)", r"$\\vec{v}$\1", newtext)
    newtext = re.sub(r"\\tta\\ ", r"$A$ ", newtext)
    newtext = re.sub(r"\\tta(\.|,)", r"$A$\1", newtext)
    newtext = re.sub(r"\\ttai\\ ", r"$A^{-1}$ ", newtext)
    newtext = re.sub(r"\\ttai(\.|,)", r"$A^{-1}$\1", newtext)
    newtext = utilities.replacemacro(newtext,"ttaxb",0,"$A \\vec{x} = \\vec{b}$")
    newtext = re.sub(r"\\tta_", r"A_", newtext)
    newtext = re.sub(r"\\lda_", r"\\lambd_", newtext)
    newtext = re.sub(r"\\tti_", r"I_", newtext)
    newtext = utilities.replacemacro(newtext,"tta",0," A")
    newtext = utilities.replacemacro(newtext,"ttat",0," A^T")
    newtext = utilities.replacemacro(newtext,"ttb",0," B")
    newtext = utilities.replacemacro(newtext,"ttbt",0," B^T")
    newtext = utilities.replacemacro(newtext,"ttc",0," C")
    newtext = utilities.replacemacro(newtext,"ttx",0," X")
    newtext = utilities.replacemacro(newtext,"tto",0," O")
    newtext = utilities.replacemacro(newtext,"ttai",0," A^{-1}")
    newtext = utilities.replacemacro(newtext,"tti",0," I")
    newtext = utilities.replacemacro(newtext,"zero",0,"\\vec{0}")
    newtext = utilities.replacemacro(newtext,"lda",0,"\\lambd")
    newtext = utilities.replacemacro(newtext,"vb",0,"\\vec{b}")
    newtext = utilities.replacemacro(newtext,"vx",0,"\\vec{x}")
    newtext = utilities.replacemacro(newtext,"vy",0,"\\vec{y}")
    newtext = utilities.replacemacro(newtext,"vu",0,"\\vec{u}")
    newtext = utilities.replacemacro(newtext,"vv",0,"\\vec{v}")

    newtext = utilities.replacemacro(newtext,"realn",0,"\\mathbb{R}^n")
    newtext = utilities.replacemacro(newtext,"realm",0,"\\mathbb{R}^m")
    newtext = utilities.replacemacro(newtext,"realnm",0,"\\mathbb{R}^n \\to \\mathbb{R}^m")

    newtext = utilities.replacemacro(newtext,"vect",1,"\\vec{#1}")
    newtext = utilities.replacemacro(newtext,"arref",0,"\\overrightarrow{\\text{rref}}")
    newtext = utilities.replacemacro(newtext,"rrr",2,"\\mathbb{R}^{#1}\\rightarrow\\mathbb{R}^{#2}")

    newtext = utilities.replacemacro(newtext,"setcounter",2,"")
    newtext = utilities.replacemacro(newtext,"ensuremath",1,"")

    newtext = utilities.replacemacro(newtext,"asyouread",1,"\\begin{objectives}\\begin{enumerate}#1\\end{enumerate}\\end{objectives}")

    newtext = re.sub(r"\\(begin|end){myfigure}", r"\\\1{figure}", newtext)

    newtext = re.sub(r"\\appendixexample", r"\\example", newtext)
    newtext = re.sub(r"\\appendixmfigure", r"\\mfigure", newtext)
    newtext = re.sub(r"\\noindent\\textbf{\\large\s*",r"\\subsection{",newtext)
    newtext = re.sub(r"\\vskip\s*[0-9]*\s*\\baselineskip\s*\\noindent\\textbf{",r"\\subsection{",newtext)

    newtext = re.sub(r"\\vskip\s*[0-9\-\.]*\s*(pt|in|mm|cm|\\baselineskip)\s*","\n\n",newtext)
    newtext = re.sub(r"\\hskip\s*[0-9\-\.]*\s*(pt|in|mm|cm|\\marginparwidth|\\marginparsep|\\textwidth)\s*","",newtext)
    newtext = re.sub(r"\\columnbreak","",newtext)
    newtext = re.sub(r"\\drawexampleline","",newtext)

    newtext = re.sub(r"\{\s*\\centering\s+","{",newtext)

    newtext = re.sub(r"\s*\\begin{center}\s*","\n\n",newtext)
    newtext = re.sub(r"\s*\\end{center}\s*","\n\n",newtext)

    newtext = re.sub(r"\\exinput *{([^{}]+)}",exinput,newtext)
    newtext = re.sub(r"\\exsetinput\b",r"\\input",newtext)
    newtext = re.sub(r"\\printexercises",r"\\include",newtext)
    newtext = re.sub(r"\\printconcepts",r"\\subsection*{Terms and Concepts}",newtext)
    newtext = re.sub(r"\\printproblems",r"\\subsection*{Problems}",newtext)
    newtext = re.sub(r"\\printreview",r"\\subsection*{Review}",newtext)

    newtext = re.sub(r"\\boolean{xetex}",r"true",newtext)
    newtext = re.sub(r"\\btz",r"\\begin{tikzpicture}" + "\n",newtext)
    newtext = re.sub(r"\\etz",r"\\end{tikzpicture}" + "\n",newtext)

    newtext = apexexample(newtext)  # this messes up some documents

    mnote_def = "\\begin{marginalnote}#2\\end{marginalnote}\n"
    newtext = utilities.replacemacro(newtext,"mnote",2,mnote_def)

 #   myincludegraphicsthree_def = "\\begin{figure}\n\\apexincludemedia{#1}"
    myincludegraphicsthree_def = "\n\\apexincludemedia{#1}"
 #   myincludegraphicsthree_def += "\n\\includegraphics[#2]{#3_3D}\n"
    myincludegraphicsthree_def += "\n\\apexincludegraphics{#3_3D}\n"
#    myincludegraphicsthree_def += "\\end{figure}\n"
    newtext = utilities.replacemacro(newtext,"myincludegraphicsthree",3,myincludegraphicsthree_def)

    newtext = re.sub(r"\\phantomsection", r"\\subsection{PLACEHOLDER}", newtext)

    mfigurethree_def = "\\begin{figure}\n\\label{#5}\n"
#    mfigurethree_def += "\\includemedia[#1]\n\\includegraphics[#2]{#6}\n"
    mfigurethree_def += "\\apexincludemedia{#1}\n\\apexincludegraphics{#6_3D}\n"
    mfigurethree_def += "\\caption{#4}\n\\end{figure}\n"
    newtext = utilities.replacemacro(newtext,"mfigurethree",6,mfigurethree_def)

 #   mfigure_def = "\\begin{figure}\n\\includegraphics[#1]{#4}\n"
    mfigure_def = "\\begin{figure}\n\\apexincludegraphics{#4}\n"
    mfigure_def += "\\caption{#2}\n\\label{#3}\n\\end{figure}\n"
    newtext = utilities.replacemacro(newtext,"mfigure",4,mfigure_def)

    mtable_def = "\\begin{figure}\n#4\n"                   # "#1" is the scale
    mtable_def += "\\caption{#2}\n\\label{#3}\n\\end{figure}\n"
    if component.target == 'ptx':
        mtable_def = "\\begin{table}\n#4\n" 
        mtable_def += "\\caption{#2}\n\\label{#3}\n\\end{table}\n"
    newtext = utilities.replacemacro(newtext,"mtable",4,mtable_def)

    definition_def = "\\begin{definition} \\label{#1}\n#2\n\\end{definition}\n"
    newtext = utilities.replacemacro(newtext,"definition",2,definition_def)
#    definition_def = "\\begin{definition}[#2] \\label{#1}\n#3\n\\end{definition}\n"
#    newtext = utilities.replacemacro(newtext,"definition",3,definition_def)
#    newtext = utilities.replacemacro(newtext,"definition",4,definition_def)

    theorem_def = "\\begin{theorem}\\label{#1}\n#2\n\\end{theorem}\n"
    newtext = utilities.replacemacro(newtext,"theorem",2,theorem_def)
#    theorem_def = "\\begin{theorem}[#2] \\label{#1}\n#3\n\\end{theorem}\n"
#    newtext = utilities.replacemacro(newtext,"theorem",3,theorem_def)
#    newtext = utilities.replacemacro(newtext,"theorem",4,theorem_def)

    keyidea_def = "\\begin{keyidea}\\label{#1}\n#2\n\\end{keyidea}\n"
    newtext = utilities.replacemacro(newtext,"keyidea",2,keyidea_def)

#    keyidea_def = "\\begin{keyidea}[#2] \\label{#1}\n#3\n\\end{keyidea}\n"
#    newtext = utilities.replacemacro(newtext,"keyidea",3,keyidea_def)

    exerciseandanswer_def = "\\begin{exercise}\n#1\n\\begin{answer}\n#2\n\\end{answer}\n\\end{exercise}\n"
    newtext = utilities.replacemacro(newtext,"exerciseandanswer",2,exerciseandanswer_def)

#    newtext = re.sub(r"\\rule\s*{[^{}]*}{[^{}]*}","",newtext)
    newtext = re.sub(r"\\rule\s*\[[^\[]*\]{[^{}]*}{[^{}]*}","",newtext)

    newtext = re.sub(r"{minipage}\[[a-z]*\]{[^{}]*}",r"{minipage}",newtext)
    newtext = re.sub(r"{minipage}{[^{}]*}",r"{minipage}",newtext)

    newtext = re.sub(r"{\s*\\noindent\s+In Exercises\s*}\s+{",r"\\doesnothing{In the following exercises",newtext)
    newtext = re.sub(r"{\s*\\noindent\s+Exercises\s*}\s+{",r"\\doesnothing{The following exercises",newtext)
    newtext = re.sub(r"{\s*(\\noindent\s+)?([^{}]+)\s+Exercises\s*}\s+{",r"\\doesnothing{\2 the following exercises",newtext)
    newtext = utilities.replacemacro(newtext,"doesnothing",1,"#1")

    newtext = re.sub(r"\\sword\b",r"\\emph",newtext)
    newtext = re.sub(r"\\restoreboxwidth","",newtext)
    newtext = re.sub(r"\\exercisegeometry","",newtext)
    newtext = re.sub(r"\\exerciseheader","",newtext)
    newtext = re.sub(r"\\restoregeometry","",newtext)
    newtext = re.sub(r"\\regularheader","",newtext)
    newtext = utilities.replacemacro(newtext,"enlargethispage",1,"")

    newtext = re.sub(r"\\myincludegraphics\b",r"\\apexincludegraphics",newtext)
    newtext = re.sub(r"\\includegraphics\[[^\]]*\]",r"\\includegraphics",newtext)
    newtext = re.sub(r"\\includegraphics\b",r"\\apexincludegraphics",newtext)

    newtext = re.sub(r"\\mbox\{\\tiny\s*\$([^\$]{1,6})\$\}",r"\1",newtext)
    newtext = re.sub(r"\\mbox\{\\tiny\s*\\\(([^\$]{1,6})\\\)\}",r"\1",newtext)

    newtext = apexlayouttabular(newtext)

    return newtext

###############

def makeoperators(txt):

    the_text = txt.group(1)

    the_args, everythingelse = utilities.first_bracketed_string(the_text)

    print("making operators", the_args[:20])

    the_args = the_args[1:-1]  # remove the { and }
    arglis = the_args.split(",")
    args_converted = ""
    for arg in arglis:
        arg = arg.strip()
        args_converted += r"\DeclareMathOperator{" + "\\" + arg + "}{" + arg + "}" + "\n"
    print("made", args_converted)
    return args_converted + everythingelse

###############

def exinput(txt):

  # this function is a lot like input_and_preprocess_a_file

       # mostly copied from input_and_preprocess_a_file
    filestub = txt.group(1)
    if "." in filestub:   # a hack because I am doing bibliographies stupidly
        filename = filestub
    else:
        filename = filestub + ".tex"

    newinputfilename = component.inputdirectory + "/" + filename
    component.inputfilename = newinputfilename

    if os.path.exists(newinputfilename):
        newinputfile = open(newinputfilename,'r')
    else:
        logging.error('input file %s does not exist', newinputfilename)
        return "EEEE"

    newcontents = newinputfile.read()
    newinputfile.close()

    newcontents = dandr.initial_preparations(newcontents)
    newcontents = newcontents.strip()

    return "\\exerciseandanswer"+newcontents

###############

def apexincludegraphics(text):

    thetext = text

    while r"\apexincludegraphics" in thetext:
        thetext = re.sub(r"\\apexincludegraphics\*? *(.*)",
                         apexincludegraph,
                         thetext,1,re.DOTALL)

    # this shoudl be handled properly, and at another time in the conversion
    thetext = utilities.replacemacro(thetext,"apexincludemedia",1,"<!-- \n \\includemedia[#1] \n -->\n")


    return thetext

###############

def apexincludegraph(txt):

    filestub = txt.group(1)
    if filestub.startswith('['):
        squaregroup, filestub = utilities.first_bracketed_string(filestub,0,"[","]")

    if filestub.startswith('{'):
        filestub, everything_else = utilities.first_bracketed_string(filestub)
        filestub = utilities.strip_brackets(filestub)

    ptx_extension = ".pdf"   # need to rethink this
    filestub2 = ""
    if filestub.endswith("3D"):
        ptxtype = "asymptote"
        ptx_extension = ".asy"
        filestub2 = ""
    elif filestub.startswith('fig'):
        ptxtype = "latex-image"
        ptx_extension = ".tex"
        filestub2 = re.sub("/fig","/fig_",filestub)

    filename1 = filestub + ptx_extension
    filenames = [filename1,filename1.lower()]
    if filestub2:
        filename2 = filestub2 + ptx_extension
        filenames.extend([filename2, filename2.lower()])

    alternate_filenames = {
'figures/figZoomSinXOverX.tex':'figures/sinx_over_x_1.tex',
'figures/figXMinusCosX.tex':'figures/fig_xminuscosx.tex',
'figures/figSqueeze1c.tex':'figures/fig_squeeze1c.tex',
'figures/figSqueeze1b.tex':'figures/fig_squeeze1b.tex',
'figures/figSqueeze1a.tex':'figures/fig_squeeze1a.tex',
'figures/figSqueeze1.tex':'figures/fig_squeeze1.tex',
'figures/figSinXOverX.tex':'figures/sinx_over_x_2.tex',
'figures/figOneSidedLimits4.tex':'figures/fig_one_sidedlimit4.tex',
'figures/figOneSidedLimits3.tex':'figures/fig_one_sidedlimit3.tex',
'figures/figOneSidedLimits2.tex':'figures/fig_one_sidedlimit2.tex',
'figures/figOneSidedLimits1.tex':'figures/fig_one_sidedlimit1.tex',
'figures/figNoLimit3b.tex':'figures/fig_nolimit3b.tex',
'figures/figNoLimit3a.tex':'figures/fig_nolimit3a.tex',
'figures/figLimitProof2a.tex':'figures/fig_limit_proof2a.tex',
'figures/figLimitProof1b.tex':'figures/fig_limit_proof1b.tex',
'figures/figLimitProof1a.tex':'figures/fig_limit_proof1a.tex',
'figures/figlimit_proof2a.tex':'figures/fig_limit_proof2a.tex',
'figures/figDiffQuotSmallhc.tex':'figures/fig_diff_quot_smallhc.tex',
'figures/figDiffQuotSmallhb.tex':'figures/fig_diff_quot_smallhb.tex',
'figures/figDiffQuotSmallha.tex':'figures/fig_diff_quot_smallha.tex',
'figures/figDiffQuot1.tex':'figures/fig_diff_quot1.tex',
'figures/figcrosspparallelpiped.tex':'figures/fig_crossp_parallelpiped.tex',
'figures/figContinuous3.tex':'figures/fig_continuous3.tex',
'figures/figContinuous2.tex':'figures/fig_continuous2.tex',
'figures/figContinuous1.tex':'figures/fig_continuous1.tex',
'figures/figchainrulegears.tex':'figures/fig_chainrule_gears.tex',
'figures/figa_color_test.tex':'figures/a_color_test.tex',
'figures/fig_LimitXplus1.tex':'figures/figLimitXplus1.tex'
}
    inputfile = ""

    the_filename = "MISSING_FILENAME"
    for filename in filenames:
        if filename in alternate_filenames:
            filename = alternate_filenames[filename]
        inputfilename = component.inputdirectory + filename
        if os.path.exists(inputfilename):
            logging.info("inputting the apex graphics file: %s", inputfilename)
            the_filename = filename
            inputfile = open(inputfilename,'r')
            break

    if not inputfile:
        logging.critical("apex graphics file does not exist: %s", filestub)
        component.image_errors += 1
        return everything_else

    newcontents = inputfile.read()
    inputfile.close()

#  need to reconstruct what is happening below
    wrapped_image = newcontents.strip()
    # need the \n at the end of wrapped_image, in case the image ends with a comment
#    wrapped_image = "<![CDATA[" + "\n" + wrapped_image + "\n" + "]]>"
#    wrapped_image = "<" + ptxtype + ">" + wrapped_image + "</" + ptxtype + ">"
#    wrapped_image = "<image>" + wrapped_image + "</image>"
    wrapped_image = "\n<!-- START " + the_filename + " -->\n" + wrapped_image + "<!-- " + the_filename + " END -->\n"

    return  wrapped_image + everything_else

###############

def apexlayouttabular(text):

    if r"{tabular}" not in text:
        return text

    thetext = text

    thetext = re.sub(r"(\\begin\{tabular\}\{c\}(.*?)\\end{tabular})",apexlayouttab,thetext,0,re.DOTALL)

    return thetext
#---------------#

def apexlayouttab(txt):

    everything = txt.group(1)
    the_inside = txt.group(2)

    if r"{tabular}" in the_inside:
        return everything
    if r"apexincludegraphics" not in the_inside:
        return everything

    figsandcaptions = the_inside.split("\\\\")

    new_inside = ""
    try:
        while figsandcaptions:
            this_figure = figsandcaptions.pop(0)
            this_caption = figsandcaptions.pop(0)
            new_inside += r"\begin{figure}" + "\n" + this_figure + "\n"
            new_inside += r"\caption{" + this_caption + "}" + "\n"
            new_inside += r"\end{figure}" + "\n" 

    except:
        print("problem with figure in table", everything)
        return everything

    component.debug_counter += 1

    return r"\begin{minipage}" + "\n" + new_inside + r"\end{minipage}"

    

###############

def apexexample(text):
    r"""Convert APEX \example{}{}{}{} to standard form.

    """

    if r"\example" not in text:
        return text

    thetext = text

    utilities.something_changed = 1
 
    while utilities.something_changed:

        utilities.something_changed = 0
        thetext = re.sub(r"\\example\*?(.*)",apexex,thetext,1,re.DOTALL)

    return thetext

######################

def apexex(txt):
    """ These examples look like
    \example{label}{title}{statement}{solution}

    For matrix algebra, there is no title (so, 3 arguments)

    """

    utilities.something_changed += 1

    text_after = txt.group(1)

    thelabel, text_after = utilities.first_bracketed_string(text_after)
    thelabel = utilities.strip_brackets(thelabel)

    thetitle = ""
#    thetitle, text_after = utilities.first_bracketed_string(text_after)
#    thetitle = utilities.strip_brackets(thetitle).strip()

    thestatement, text_after = utilities.first_bracketed_string(text_after)
    thestatement = utilities.strip_brackets(thestatement)
    thestatement = thestatement.strip()
#    if thestatement.startswith(r"\textbf"):
#        thestatement = re.sub(r"^\\textbf *","",thestatement)
#        thetitle, thestatement = utilities.first_bracketed_string(thestatement)
#        thetitle = utilities.strip_brackets(thetitle)
#        thetitle = thetitle.strip()
#    else:
#        thetitle = ""

    thesolution, text_after = utilities.first_bracketed_string(text_after)
    thesolution = utilities.strip_brackets(thesolution)
 
    if thetitle: 
        returnstring = "\\"+"begin{example}[" + thetitle + r"]"
    else:
        returnstring = "\\"+"begin{example}"

    return (returnstring +
            r"\label{" + thelabel + "}" + "\n" +
            thestatement +
            "\\"+"begin{solution}" + "\n" +
            thesolution +
            r"\end{solution}" + "\n" +
            r"\end{example}" + "\n" +
            text_after )
                
######################

def szex(txt):
    """These look like
        ...
        {\bf Solution.} ...
    """

    thetext = txt.group(1)

    if "{\\bf Solution.}" not in thetext:
        return "\\begin{example}\n" + thetext + "\n\\end{example}"

    the_statement, the_solution = thetext.split("{\\bf Solution.}")

    the_statement = the_statement.strip()
    the_solution = the_solution.strip()

    return "\\begin{example}\n" + the_statement + "\n\\begin{solution}\n" + the_solution + "\n\\end{solution}\n\\end{example}"

#-------------#

def szprop(txt):
    """These eventually end up in a titles box.
    """

    thetext = txt.group(1)

    if "\\textbf" in thetext:
        try:
            thetitle = re.search(r"\\textbf{([^{}]+)}", thetext).group(1)
            thetitle = thetitle.strip()
        except:
            print("missing title in", thetext)
            thetitle = "Title not found in Source"
        titlebrackets = "[" + thetitle + "]"
    else:
        titlebrackets=""

    return "\\begin{proposition}" + titlebrackets + "\n" + thetext + "\n\\end{proposition}"

######################
# from openintro stats
def remap_example(text):
    thetext = text

    thetext = re.sub(r"\\begin{example}\s*{(.*?)\s*\\end{example}",remap_ex,thetext,0,re.DOTALL)

    return thetext

#--------------------#

def remap_ex(txt):
    thetext = txt.group(1)

    theexample,therest = utilities.first_bracketed_string(thetext,depth=1)
    theexample = utilities.strip_brackets("{"+theexample)
    theanswer = re.sub(r"\s*\\end{example}","",therest)

    if r"\label{" in theanswer:
        thelabel = re.search(r"\\label{([^{}]+)}",theanswer).group(1)
        theanswer = re.sub(r"\\label{([^{}]+)}","",theanswer)
        theexample += r"\label{" + thelabel + "}"

    remapped_example = r"\begin{example}" + theexample 
    remapped_example += r"\begin{answer}" + theanswer + r"\end{answer}" + "\n"
    remapped_example += r"\end{example}" + "\n"

    return remapped_example

##################
def replaceautoref(txt):

    text_after = txt.group(1)

    this_label, text_after = utilities.first_bracketed_string(text_after)
    this_label = utilities.strip_brackets(this_label)

    this_label = utilities.safe_name(this_label, idname=True)

    return "\\xautoref{" + this_label + "}" + text_after

######################

def hide_figure_inputs(text):
    """An \input in a figure environment may need to be treated literally,
       so we hide the \input as a \figureinput to be expanded later.
    """

    thetext = text

    logging.debug("in hide_figure_inputs")

    thetext = re.sub(r"(\\begin{figure}.*?\\end{figure})", hide_figure_in, thetext, 0, re.DOTALL)

    return thetext

def hide_figure_in(txt):

    the_text = txt.group(1)

    the_text = re.sub(r"\\input\b", r"\\figureinput", the_text)
    the_text = re.sub(r"\\def\b", r"\\figuredef", the_text)
    the_text = re.sub(r"\\newcommand\b", r"\\figurenewcommand", the_text)
    the_text = re.sub(r"\\renewcommand\b", r"\\figurerenewcommand", the_text)

    return the_text

def hide_diagram_in_math(text):
    """A \begin{diagram} in math mode should be left in place, so that the entire
       equation can be converted to an image.  So we hide it as a "mathdiagram".
    """

    thetext = text

    logging.debug("in hide_diagram_in_math")

    thetext = re.sub(r"(\\begin{equation\*?}.*?\\end{equation\*?})", hide_diagram_in, thetext, 0, re.DOTALL)
    thetext = re.sub(r"(\\begin{align\*?}.*?\\end{align\*?})", hide_diagram_in, thetext, 0, re.DOTALL)
    thetext = re.sub(r"(\\\[.*?\\\])", hide_diagram_in, thetext, 0, re.DOTALL)
    thetext = re.sub(r"(\$\$.*?\$\$)", hide_diagram_in, thetext, 0, re.DOTALL)

    return thetext

def hide_diagram_in(txt):

    the_text = txt.group(1)

    the_text = re.sub(r"\\begin{diagram}", r"\\begin{mathdiagram}", the_text)
    the_text = re.sub(r"\\end{diagram}", r"\\end{mathdiagram}", the_text)

    return the_text

####################

def find_particular_packages(text):

    thetext = text

    logging.debug("in find_particular_packages")

    for package in mapping.latexheader_param:
        try:
            this_package = re.search(r"(\\usepackage\[[^\[\]]*\]\{" + package + "\})", thetext).group(1)
            mapping.latexheader_param[package] = this_package
        except AttributeError:
            pass
        
####################

def latexconvert(text):
    """Fix common LaTeX anomalies.

    """

    logging.info("fixing common LaTeX anomalies")
    newtext = text

    inputfilenamestub = re.sub(r"[^.]*$","",component.inputfilename)
    inputfilenamestub = re.sub(".*/","",inputfilenamestub)

    newtext = oldtex.convert_archaic_tex(newtext)
    newtext = oldtex.convert_bibtex(newtext)
    # next one repeated in dandr.separate_into_latex_components
    # so maybe we don't need to do it here?
    newtext = utilities.environment_shortcuts(newtext)
    newtext = utilities.delete_formatting(newtext)

    if component.target == 'html':
     #   newtext = re.sub(r"\\autoref\b",r"\\ref",newtext)  # later should implement autoref properly
        pass  # autoref handled properly later by processenvironments.expand_smart_references
    elif component.target == 'ptx':
        while "\\autoref{" in newtext:
            newtext = re.sub(r"\\autoref({.*)",replaceautoref,newtext,1,re.DOTALL)

    newtext = re.sub(r"\$\s*\\qed\s*\$(\s*)", r"\\qed\1", newtext)  

    newtext = re.sub(r"\\caption\s+{", r"\\caption{", newtext)  

    # kill \subfiguretopcaptrue and other thigns, so that in processsubfigures_to_html we can do
    # while r"\subfigure" in newtext:
    newtext = re.sub(r"\\subfigure[a-z]+", "", newtext)

    newtext = re.sub(r"([^\$])\$\\(emph|it|em|rm|mathit|mathrm)\{([^{}]+)\}\$", r"\1\\\2{\3}", newtext)  
                 # remove outer dollar signs from
                 # an effective divisor is said to have $\emph{rank $r(c)=r$}$ if  from 1207.7002

    # to make the $ math $ parsing easier later
    newtext = re.sub(r"\\\\\$", r"\\\\ $", newtext)   # because \\$ in latex means \\ followed by math mode
    newtext = re.sub(r"\\\$", r"\\dollar", newtext)

    for oldname, newname in mapping.macro_rename:
        thesub = r"\\" + oldname + r"\b"
        theans = r"\\" + newname
        newtext = re.sub(thesub, theans ,newtext)

    newtext = re.sub(r"\\hspace\*",r"\\hspace",newtext)

    newtext = re.sub(r"\\footnote\s*\[[^\[\]]+\]\s*",r"\\footnote",newtext)   # \footnote[1]{...}  -->  \footnote{...}
                                                                             # this breaks the author label

    newtext = re.sub(r"\\rule\s*{[0\.]*(in|pt)}{[^{}]*}","",newtext)    # delete invisible rules
    newtext = re.sub(r"\\rule\s*{[^{}]*}{[0\.]*(in|pt)}","",newtext)

    # temporary hack for simplest case of multicolumn
    # need to handle this when parsing a table
    findmulticolumn = r"\\multicolumn\{[0-9]+\}{[^{}]+}{([^{}]+)}"
    newtext = re.sub(findmulticolumn,r"\1",newtext)

    newtext = re.sub(r"\\begin{wrapfigure}{[^{}]*}{[^{}]*}",r"\\begin{wrapfigure}",newtext)

    # label inside section title
    newtext = re.sub(r"section{\\label{([^\{\}]+)}([^\{\}]+)}",r"section{\2}\\label{\1}",newtext)

    # incorrect use of ``smart quotes"
    # don't try to make this perfect
    newtext = re.sub(r'``([^`\'"\n]{,50})"', r"``\1''", newtext)

    return(newtext)

#############

def convertexercises(txt):  # this is specific to Judson's AATA book

    import separatecomponents

    theexercises = txt.group(1)
    theremainder = txt.group(2)

    #omit the TeX-style font formatting 
    theexercises = re.sub(r"^\s*\\exrule\s*\{\s*(\\small)*","",theexercises)
    theexercises = re.sub(r"\s*\}\s*$","",theexercises)

    # the tricky thing is that the entire exercise section is one big list,
    # but there also are lists inside exercises.
    # so first we hide the inner lists.
    # Start by removing the outer enumerate tags

    theexercises = re.sub(r"(.*?)\\begin{enumerate}","\1",theexercises,1)
    theexercises = re.sub(r"\\end{enumerate}(.*?)$","\1",theexercises,1)
    

    numberoflists = len(re.findall(r"\\end{enumerate}",theexercises))

    theexercises = separatecomponents.separateenvironment("enumerate",theexercises)
    # We just replaced the {enumerate}s by a sha1 hash.  Since we are just going
    # to pass the LaTeX to the main program, we don't actually need to convert
    # those sha1 hashes back to {enumerate}

    # the conversion of \item tp exercise-like environments may need to be
    # done more robustly

    theexercises = re.sub(r"\s*\n\s*\n\s*\\item",
                          r"\n\\end{exercise}\n\n\\begin{exercise}",theexercises)

    theexercises = re.sub(r"\s*\\end{exercise}","",theexercises,1)
    theexercises = re.sub(r"\s*$","\\end{exercise}",theexercises,1)

    return "\\section{Exercises}\n" + theexercises + theremainder   

def convertquestions(txt):  # this is specific to Oscar Levin's discrete math book


    thetext = txt.group(1)

    thetext = re.sub(r"\\question",r"\\endquestion\\question",thetext)
    thetext += r"\\endquestion"
    thetext = re.sub(r"\\endquestion",r"",thetext,1)

    thetext = re.sub(r"\\question",r"\\begin{exercise}",thetext)
    thetext = re.sub(r"\\endquestion",r"\\end{exercise}",thetext)

    thetext = r"\\begin{exercises}" + thetext + r"\\end{exercises}" + "\n"

    return thetext

def math_special(text):

    # currently only have one thing specific to Oscar Levin
    thetext = text

    thetext = re.sub(r"\\gls\{([^{}]+)\}",r"\\\1",thetext)

    return thetext

def title_lower(txt):

    # a hack, make it more general
    sectioning = txt.group(1)
    first_letter = txt.group(3)
    other_letters = txt.group(4)
    the_end = txt.group(5)

    other_letters = other_letters.lower()

    other_letters = re.sub(r"chapter", r"Chapter", other_letters)
    other_letters = re.sub(r"appendix", r"Appendix", other_letters)
    other_letters = re.sub(r"\\r\b", r"\\R", other_letters)
    other_letters = re.sub(r"\\lobo o", r"\\lobo O", other_letters, 1)
    other_letters = re.sub(r"b\(s,v\)", r"B(S,V)", other_letters)

    return sectioning + first_letter + other_letters + the_end

#############

def adjust_bibliography(biblio_text):
    """ Given only the bibliography, make some adjustments.

    """

    the_text = biblio_text

    logging.info("adjusting the bibliography %s", the_text[-200:])
    if "\\BibitemOpen" not in the_text:
        logging.info("nothing to adjust")
        return biblio_text

    # see 1612.02143 for an example of what we need to handle
    the_text = re.sub(r"^.*?\\bibitem( |\[)", r"\\bibitem\1", the_text, 1, re.DOTALL)

    # maybe it would be better to not throw this away
    the_text = re.sub(r"\s*\\bibitem\s*\[[^\[\]]+\]\s*", "\n\n" + r"\\bibitem", the_text)

    the_text = utilities.replacemacro(the_text, "citenamefont", 1, "#1")
    the_text = re.sub(r"\\BibitemOpen\s*", "", the_text)
    the_text = re.sub(r"\\BibitemShut\s*\{[^{}]*\}", "", the_text)
    the_text = utilities.replacemacro(the_text, "BibitemShut", 1, "")

    the_text = utilities.replacemacro(the_text, "bibnamefont", 1, "#1")
    the_text = utilities.replacemacro(the_text, "bibfnamefont", 1, "#1")

    the_text = re.sub(r"\\bibinfo\s*\{author\}", "", the_text)
    the_text = re.sub(r"\\bibinfo\s*\{pages\}", r"\\thepages", the_text)
    the_text = utilities.replacemacro(the_text, "thepages", 1, "pp.~#1  ")
    the_text = re.sub(r"\\bibinfo\s*\{year\}", r"\\theyear", the_text)
    the_text = utilities.replacemacro(the_text, "theyear", 1, "#1 ")
    the_text = re.sub(r"\\bibinfo\s*\{journal\}", r"\\thejournal", the_text)
    the_text = utilities.replacemacro(the_text, "thejournal", 1, "#1, ")
    the_text = re.sub(r"\\bibinfo\s*\{volume\}", r"\\thevolume", the_text)
    the_text = utilities.replacemacro(the_text, "thevolume", 1, "#1 ")
    the_text = re.sub(r"\\bibfield\s*\{author\}", r"\\theauthors", the_text)
    the_text = utilities.replacemacro(the_text, "theauthors", 1, "#1, ")
    the_text = re.sub(r"\\bibfield\s*\{journal\}", r"\\thejournal", the_text)
    the_text = utilities.replacemacro(the_text, "thejournal", 1, "#1. ")
    the_text = re.sub(r"\\bibfield\s*\{howpublished\}", r"\\thehowpublished", the_text)
    the_text = utilities.replacemacro(the_text, "thehowpublished", 1, "#1")
    the_text = re.sub(r"\\bibinfo\s*\{howpublished\}", r"\\thehowpublished", the_text)
    the_text = utilities.replacemacro(the_text, "thehowpublished", 1, "#1")

    the_text = utilities.replacemacro(the_text, "natexlab", 1, "#1. ")

    the_text = re.sub(r"\\href@noop\s*\{\s*\}\s*", r"\\emph", the_text)
    the_text = re.sub(r"@noop\s*", r"\\emph", the_text)
    the_text = re.sub(r"\\href", "", the_text)
    the_text = re.sub(r"\\emph\s*\{\s*\}", "", the_text)

    the_text = re.sub(r"\\ ", " ", the_text)
    the_text = re.sub(r"\\(\s)", r"\1", the_text)
    the_text = re.sub(r"~ ", "~", the_text)

    the_text = re.sub(r"\{\s*\{([^{}]+)\}\s*\}", r"\1", the_text)

    the_text = re.sub(r"(\s|~)\{\s*([a-zA-Z]+)\s*\}", r"\1\2", the_text)
    the_text = re.sub(r"(\s|~)\{\s*([a-zA-Z. \-]+)\s*\}", r"\1\2", the_text)
    the_text = re.sub(r"(\s|~)\{\s*([a-zA-Z. ~\-]+)\s*\}", r"\1\2", the_text)
    the_text = re.sub(r"(\s|~)\{\s*([a-zA-Z. \n~\-]+)\s*\}", r"\1\2", the_text)

    logging.info("done adjusting the bibliography %s", the_text)
    
    return the_text
