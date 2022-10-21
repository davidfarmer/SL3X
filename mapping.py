# -*- coding: utf-8 -*-

# ignore these style files, mostly from journals and commercial publishers
style_files_to_omit = ["imsart", "arximspdf", "IEEEtran", "gtpart", "gtart",
                       "birkjour", "birkjour_t2", "dmtcs", "svmult", "svjour",
                       "pnastwo", "babel", "cleveref", "lms", "HandbookOfModuli",
                       "AmsArt", "siamltex", "agtart_a", "mdpi", "e-jc",
                       "egastyle", "pinlabel", "graphs", "jtbbook", "jtbart",
                       "diagrams", "elsart", "physics", "geompsfi", "amlts", "amsppt",
                       "jheppub", "loops", "skeyval",
                       "algorithm", "algorithm2e", "algorithmic", "algpseudocode",
                       "jmlr2e", "amltd", "spconf", "amsmath", "amssymb", "amsfonts",
                       "mathtools", "url", "color", "subfigure", "graphicx", "lgrind",
                       "cite", "fancyhdr", "psfig", "pgfplots", "arximspdf",
                       "smfthm", "smfart", "smfbook", "mhequ", "mhfig", "mhenvs",
                       "subenv", "revtex", "caption", "subcaption", "ScriptFonts", "Symbols",
                       "birkmult", "elsart3-1", "revtex4-1", "aims", "aomamlt2e","ejpecp",
                       "ltexpprt", "acmsmall", "epl2", "JINST", "iopart", "iopams",
                       "mysymbol", "acmnew", "mhchem",  # check what that is needed for
                       "amsrefs", "jmlrmod", "infocom", "acmart", "natbib", "llncs", "oldllncs",
                       "ieeeconf", "acm_proc_article-sp", "aaai", "ltexpprt", "sig-alternate",
                       "tufte-book",
                       "sagetex", "tabmac", "chngcntr",
                       "gastex", "mathfont", "yjsco"
                       ]
#
# The plain TeX {\bf ... should be \textbf{ in LaTeX 
# (assuming it is used at all)
#
tex_latex_font_switch = ["it","sl","sc","tt","bf","sf"]  # sf = san serif (not implemented yet)

# obsolete: broken into the pieces below
obsolete______latexheader = [r"\documentclass{article}",
               r"\usepackage{etex}",
               r"\usepackage{amsmath}",
               r"\usepackage{graphicx}",
               r"\usepackage{amssymb}",
               r"\usepackage{amsopn}",
               r"\usepackage{pstricks,pst-text,pst-node}",
               r"\DeclareGraphicsRule{.pdftex}{pdf}{.pdftex}{}",
               r"\usepackage{color}",
               r"\usepackage{epic}",
               r"\usepackage{eepic}",
               r"\usepackage{overpic}",
               r"\usepackage{psfrag}",
               r"\usepackage{pgfplots}",
               r"\usepackage{pinlabel}",
               r"\usepackage{amscd}",
               r"\usepackage{multirow, booktabs, makecell}",
               r"\usepackage[all]{xy}",
               r"\usepackage{tikz}",
               r"\usepackage{tkz-graph}",
               r"\usetikzlibrary{patterns}",
               r"\usetikzlibrary{positioning}",
               r"\usetikzlibrary{matrix,arrows}"
              ]

latexheader_top = [r"\documentclass{article}",
               r"\usepackage{etex}",
               r"\usepackage{amsmath}",
               r"\usepackage{amssymb}",
               r"\usepackage{amsopn}",
               r"\usepackage{pstricks,pst-text,pst-node}",
              ]

latexheader_param = {"graphicx" : r"\usepackage{graphicx}",
                     "overpic" : r"\usepackage{overpic}"}

latexheader_other = [r"\DeclareGraphicsRule{.pdftex}{pdf}{.pdftex}{}",
               r"\usepackage{color}",
               r"\usepackage{epic}",
               r"\usepackage{eepic}",
               r"\usepackage{psfrag}",
               r"\usepackage{pgfplots}",
               r"\usepackage{pinlabel}",
               r"\usepackage{amscd}",
               r"\usepackage{multirow, booktabs, makecell}",
               r"\usepackage[all]{xy}",
               r"\usepackage{pb-diagram,pb-xy}"
              ]


latexheader_tikz = [r"\usepackage{tikz}",
               r"\usepackage{tkz-graph}",
               r"\usepackage{tkz-euclide}",
               r"\usetikzlibrary{patterns}",
               r"\usetikzlibrary{positioning}",
               r"\usetikzlibrary{matrix,arrows}",
               r"\usetikzlibrary{calc}",
               r"\usetikzlibrary{shapes}",
               r"\usetikzlibrary{through,intersections,decorations,shadows,fadings}"
              ]

        #       r"\usetikzlibrary{through,intersections,decorations.pathreplacing}"

# conversion like \emph{...}  to  <em>...</em>
font_styles_html = [
    ("emph","em"),
    ("termx","em"),
    ("textbf","b"),
    ("bfseries","b"),
    ("textit","i"),
    ("tmtextit","i"),
    ("textsl","em"),   # should be slant
    ("textsf","em"),   # should be sans serif
#    ("texttt","code"),
    ("texttt","tt"),
    ("textsc","span"),
    ("underline","u")
    ]

# conversion like \emph{...}  to  <em>...</em>
font_styles_ptx = [
    ("emph","em"),
    ("termx","em"),
    ("textbf","b"),
    ("bfseries","b"),
    ("textit","em"),
    ("tmtextit","em"),
    ("textsl","em"),   # should be slant
    ("textsf","em"),   # should be sans serif
#    ("texttt","code"),
    ("texttt","c"),
    ("textsc","sc"),
    ("underline","u")
    ]


# the substitutions below, and others, mimic LaTeX's habit of eating the space after
# a macro.  Therefore  "formul\ae{} " --> "formul&aelig; " requires that font
# substitutions are done before "{}" are deleted.
# see above equation 8.3 in
# http://sl2x.aimath.org/development/collectedworks/htmlpaper/math__0506455/section8.html

# Substitutions to convert non-English letters to HTML
# Note that we are in the process of converting to (ascii) unicode, which works more generally
tex_to_html_characters = [
    [r"\\~n",r"&#xf1;"],
    [r"\\`o",r"&#xf2;"],
    [r"\\'o",r"&#xf3;"],
    [r"\\\^o",r"&#xf4;"],
    [r"\\\^\s*{\\i}",r"&#xee;"],
    [r"\\\^\\i",r"&#xee;"],
    [r"\\\^{\\i}",r"&#xee;"],
    [r"\\\^i",r"&#xee;"],
    [r"\\\^e",r"&#xea;"],
    [r"\\\^a",r"&#xe2;"],
    [r"\\~o",r"&#xf5;"],
    [r'\\"o',r"&#xf6;"],   # &#xf7; is the "divides" symbol
    [r'\\o\s',r"&#xf8;"],
    [r'{\\o}',r"&#xf8;"],
    [r'\\o\b',r"&#xf8;"],
    [r'\\`u',r"&#xf9;"],
    [r"\\'u",r"&#xfa;"],
    [r"\\\^u",r"&#xfb;"],
    [r'\\"u',r"&#xfc;"],
    [r"\\'y",r"&#xfd;"],
    [r"\\\.x",r"&#x017C;"],
    [r"\\`a",r"&#xe0;"],
    [r"\\`A",r"&#xc0;"],
    [r"\\'a",r"&#xe1;"],
    [r"\\'A",r"&#xc1;"],
    [r'\\"a',r"&#xe4;"],
    [r'\\"A',r"&#xc4;"],
    [r"\\`e",r"&#xe8;"],
    [r"\\'e",r"&#xe9;"],
    [r"\\'E",r"&#xc9;"],
    [r'\\"e',r"&#xeb;"],
    [r'\\"E',r"&#xcb;"],
    [r"\\'{\\i}",r"&#xed;"],
    [r"\\'\\i(\b|\s)",r"&#xed;"],
    [r"\\'{i}",r"&#xed;"],
    [r"\\'i",r"&#xed;"],  # not proper TeX, but people do it
    [r'\\"\s*{\\i}',r"&#xef;"],   # also &iuml;
    [r'{\\"\\i}',r"&#xef;"],
    [r'\\"\\i(\b|\s)',r"&#xef;"],
    [r'\\"i',r"&#xef;"],   # not proper TeX, but people do it
    [r"\\c c",r"&#xe7;"],
    [r"\\c C",r"&#xc7;"],
    [r"\\c\{c\}",r"&#xe7;"],
    [r"\\c\{C\}",r"&#xc7;"],
    [r"\\c e",r"&#281;"],
    [r"\\c\{e\}",r"&#281;"],
    [r"\\c S",r"&#350;"],
    [r"\\c\{S\}",r"&#350;"],
    [r"\\c s",r"&#351;"],
    [r"\\c\{s\}",r"&#351;"],
    [r"\\c t",r"&#355;"],
    [r"\\c\{t\}",r"&#355;"],
    [r"\\c ([a-zA-Z])",r"\1&#807;"],   # necessary for \c{a}, which is 2 characters in html
    [r"\\c\{([a-zA-Z])\}",r"\1&#807;"],
    [r'\\"([A-Za-z])',r"&\1uml;"],
    [r'\\"([A-Za-z])',r"&\1uml;"],
    [r'\\" ([A-Za-z])',r"&\1uml;"],
    [r'\\"\{([A-Za-z])\}',r"&\1uml;"],
    [r"\\'O",r"&#211;"],
    [r"\\'o",r"&#243;"],
    [r"\\'([A-Za-z])",r"&\1acute;"],
    [r"\\' ([A-Za-z])",r"&\1acute;"],
    [r"\\'{([A-Za-z])}",r"&\1acute;"],
    [r"\\`\\i(\b|\s)",r"&igrave;"],
    [r"\\`{\\i}",r"&igrave;"],
    [r"\\`([A-Za-z])",r"&\1grave;"],
    [r"\\` ([A-Za-z])",r"&\1grave;"],
    [r"\\`{([A-Za-z])}",r"&\1grave;"],
#    [r"\\\^([A-Za-z])",r"&\1circ;"],
    [r"\\\^\s*([A-Za-z])",r"&\1circ;"],  # do the \s* instead of 2 lines for other cases?
    [r"\\\^{([A-Za-z])}",r"&\1circ;"],
    [r"\\\^{\\i}",r"&icirc;"],
    [r"\\r a",r"&#229;"],
    [r"\\r\{a\}",r"&#229;"],
    [r"\\r A",r"&#197;"],
    [r"\\r\{A\}",r"&#197;"],
    [r"\{\\aa\}",r"&#229;"],
    [r"\\aa ",r"&aring;"],
    [r"\{\\AA\}",r"&#197;"],
    [r"\\AA ",r"&#197;"],
    [r"\{\\o\}",r"&#248;"],  # &oslash;
    [r"\{\\O\}",r"&#216;"],  # &Oslash;
    [r"\\o ",r"&#248;"],
    [r"\\O ",r"&#216;"],

    [r"\\H\{o\}",r"&#337;"],
    [r"\\H o",r"&#337;"],

    [r"\\u A",r"&#258;"],
    [r"\\u\{A\}",r"&#258;"],
    [r"\\u a",r"&#259;"],
    [r"\\u\{a\}",r"&#259;"],
    [r"\\u E",r"&#276;"],
    [r"\\u\{E\}",r"&#276;"],
    [r"\\u e",r"&#277;"],
    [r"\\u\{e\}",r"&#277;"],
    [r"\\u I",r"&#300;"],
    [r"\\u\{I\}",r"&#300;"],
    [r"{\\u\s*\\i\s*}",r"&#301;"],
    [r"\\u\s*\\i(\b|\s)",r"&#301;"],
    [r"\\u\{\\i\s*\}",r"&#301;"],
    [r"\\u O",r"&#334;"],
    [r"\\u\{O\}",r"&#334;"],
    [r"\\u o",r"&#335;"],
    [r"\\u\{o\}",r"&#335;"],
    [r"\\u U",r"&#364;"],
    [r"\\u\{U\}",r"&#364;"],
    [r"\\u u",r"&#365;"],
    [r"\\u\{u\}",r"&#365;"],
    [r"\\u G",r"&#286;"],
    [r"\\u\{G\}",r"&#286;"],
    [r"\\u g",r"&#287;"],
    [r"\\u\{g\}",r"&#287;"],
    [r"\\u Z",r"&#142;"],
    [r"\\u\{Z\}",r"&#142;"],

    # other uses of \u, such as \u{C}, may be errors for \v
#    [r"\\u\b",r"\\v"],

    [r"\\(v|u){a}",r"&#462;"],     # &acaron; is not defined
    [r"\\(v|u) a",r"&#462;"],      # and should use the hex version for consistency
    [r"\\(v|u){e}",r"&#x11b;"],
    [r"\\(v|u) e",r"&#x11b;"],
    [r"\\(v|u){g}",r"&#287;"],  # this is \u g , because we assume the author made an error
    [r"\\(v|u) g",r"&#287;"],   #   " same "
    [r"\\(v|u){([A-Za-z])}",r"&\2caron;"],
    [r"\\(v|u) ([A-Za-z])",r"&\2caron;"],

    [r"\{\\=g\}",r"&#x1E21;"],
    [r"\\=g",r"&#x1E21;"],
    [r"\\= g",r"&#x1E21;"],
    [r"\\=\{g\}",r"&#x1E21;"],

    [r"\{\\=I\}",r"&#298;"],
    [r"\\=I",r"&#298;"],
    [r"\\= I",r"&#298;"],
    [r"\\=\{I\}",r"&#298;"],
    [r"\{\\=i\}",r"&#299;"],
    [r"\\=i",r"&#299;"],
    [r"\\= i",r"&#299;"],
    [r"\\=\{i\}",r"&#299;"],
    [r"\{\\=\\i\s*\}",r"&#299;"],
    [r"\\=\\i\s?",r"&#299;"],
    [r"\\= \\i\s?",r"&#299;"],
    [r"\\=\{\\i\s*\}",r"&#299;"],

    [r"\{\\=u\}",r"&#363;"],
    [r"\\=u",r"&#363;"],
    [r"\\= u",r"&#363;"],
    [r"\\=\{u\}",r"&#363;"],

    [r"\{\\=o\}",r"&#333;"],
    [r"\\=o",r"&#333;"],
    [r"\\= o",r"&#333;"],
    [r"\\=\{o\}",r"&#333;"],

    [r"\\~u",r"&#x169;"],
    [r"\\~\{u\}",r"&#x169;"],
    [r'\\~([A-Za-z])',r"&\1tilde;"],
    [r'\\~\{([A-Za-z])\}',r"&\1tilde;"],

    [r"{\\DJ}",'&#272;'],
    [r"\\DJ ",'&#272;'],
    [r"\\DJ\b",'&#272;'],
    [r"{\\dj}",'&#273;'],
    [r"\\dj ",'&#273;'],
    [r"\\dj\b",'&#273;'],
    [r"{\\Dbar}",'&#272;'],
    [r"\\Dbar ",'&#272;'],
    [r"\\Dbar\b",'&#272;'],

    [r"{\\ss}",'&#223;'], 
    [r"\\ss ",'&#223;'],
    [r"\\ss\b",'&#223;'],

    [r"\{\\cprime *\}",r"'"],
    [r"\\cprime ",r"'"],

    [r"\\textquotedblleft\s*",r'"'],
    [r"\\textquotedblright",r'"'],

    [r"{\\i}",'&#305;'],
    [r"\\i(\b|\s)",'&#305;'],
    [r"{\\l}",'&#322;'],
    [r"\\l ",'&#322;'],
    [r"\\l\b",'&#322;'],
    [r"{\\L}",'&#321;'],
    [r"\\L ",'&#321;'],
    [r"\\L\b",'&#321;'],
    [r"{\\(oe|OE|ae|AE)}",r'&\1lig;'],
    [r"\\(oe|OE|ae|AE) ",r'&\1lig;'],
    [r"\\(oe|OE|ae|AE)\b",r'&\1lig;']
    ]

########################

html_to_latex_pairs = [
    [r"&#xc1;",r"\\'A"],
    [r"&#xc4;",r'\\"A'],
    [r"&#xc8;",r"\\`E"],
    [r"&#xc9;",r"\\'E"],
    [r"&#xd6;",r'\\"O'],
    [r"&#xe1;",r"\\'a"],
    [r"&#xe4;",r'\\"a'],
    [r"&#xe8;",r"\\`e"],
    [r"&#xe9;",r"\\'e"],
    [r"&#xf3;",r"\\'o"],
    [r"&#xf8;",r"{\\o}"],
    [r"&#xfa;",r"\\'u"],
    [r"&#xfc;",r'\\"u'],
    [r"&#xf1;",r'\\~n'],
    [r"&#355;",r'\\c{t}'],
    [r"&#169;",r'\\~u'],
    [r"&#259;",r'\\u{a}'],
    [r"&#287;",r'\\u{g}'],
    [r"&#281;",r'\\c{e}'],
    [r"&#301;",r'\\u{\\i}'],
    [r"&#350;",r'\\c{S}'],
    [r"&#351;",r'\\c{s}'],
    [r"&#x107;",r"\\'c"],
    [r"&#x10c;",r"\\v{C}"],
    [r"&#x10d;",r"\\v{c}"],
    [r"&#x11a;",r"\\v{E}"],
    [r"&#x11b;",r"\\v{e}"],
    [r"&#x141;",r"\\L"],
    [r"&#x160;",r'\\v{S}'],
    [r"&#x161;",r'\\v{s}'],
    [r"&#x27;",r"'"],
    [r"&iuml;",r'\\"{\\i}'],
    [r"&szlig;",r'{\\ss}'],
    [r"&#223;",r'{\\ss}'],
    [r"&ndash;",r'--'],
    [r"&quot;",r'"']
    ]

################################################################
# These known_macros cannot be redefined by the author.
#
# also see macros_to_ignore
known_macros = [r"\ref",r"\eqref",r"\cite",r"\href",r"\emph",r"\textbf",r"\textit",r"\texttt",
                r"\mathcal",r"\mathbb",r"\Cal",
                r"\rm",r"\date",r"\address",r"\hfill",
                r"\S",r"\H",
                r"\begin",r"\end",
                r"\term",r"\terminology",r"\knownterminology",r"\index",
                r"\sum",r"\prod",r"\int",
                r"\i",r"\u"]    # need to add a lot more

# similar category, but need to understand the distinction
macros_to_ignore = ["thetitle",
"theshorttitle",
"theauthors",
"lastauthor",
"theshortauthors",
"theaddress",
"thededicatory",
"doubletitle",
"singletitle",
"lefthead",
"righthead",
"maketitle",
"bysame",
"thesection",
"thesubsection",
"thesubsubsection",
"xymatrix",
"urladdr",
"email",
"isdraft",
"newcommand",
"bar",
"frac",
"cr", "\\",
"to",
"ref", "href", "eqref", "cite",
"qed",
"big",
"mod", "bmod", "pmod",
"mid","nmid",
"label",
"longlongrightarrow", "longlonglongrightarrow",
"sum", "prod",
"mathcal", "mathbb",
"bibitem", "endbibitem",
"gamma","mu",
"begin", "end",
"address"]

################################################################
# (La)TeX commands that we delete for the HTML version
# Note: go back and think carefully about when these get deleted

throw_away_formatting0 = [
    "centering",
    "newpage",
    "newline",
    "smallskip",
    "medskip",
    "bigskip",
    "noindent",
    "nopagebreak",
    "reallynopagebreak",
    "smallbreak",
    "medbreak",
    "bigbreak",
    "raggedright",
    "pagebreak",
    "bigpagebreak",
    "newline",
    "tableofcontents"
    "frenchspacing"
    ]

throw_away_formatting1 = [
    "snug",
    "large",
    "Large",
    "LARGE",
    "huge",
    "Huge",
    "HUGE",
    "normalsize",
    "small",   # should be elsewhere?
    "newfootnote"
    ]

throw_away_formatting_environments = [
    "smaller",
    "small",
    "tiny",
    "footnotesize",
    "titlepage"
    ]


throw_away_commands_in_text_only = [
                       "nopagebreak",
                       "reallynopagebreak",
                       "pagebreak",
                       "bigpagebreak",
                       "leavevmode",
                       "goodbreak",
                       "NoBlackBoxes",
                       "nolinebreak",
                       "unskip",
                       "hfil", "hfill",
                       "vfil", "vfill",
                       "makeatletter", "makeatother",
                       "tiny",
                       "footnotesize",
                       "scriptsize",
                       "normalsize",
                       "onehalfspace",
                       "rm",
                       "itshape",
                       "slshape",
                       "upshape",
                       "protect",  # in throw_away_macros_keep_argument
                       "topmatter", "endtopmatter",
                       "eject",
                       "mathopen",   # what is that?
                       "paperintro",
                       "backmatter",  # may need some treatment later
                       "printindex",
                       "makeshorttitle",
                       "clearpage",
                       "today",
                       "boldmath",   # if \boldmath appears in text, then something is wrong, so delete it
                       "allowdisplaybreaks"]

replace_macros_in_text_only = [
    ["quad"," "],
    ["qquad"," "]
    ]

throw_away_macros = ["markleft","date"]  # how is that different than throw_away_commands ?

throw_away_macros_and_argument = ["nocite","runningtitle","runningauthor",
                                  "address","dedicatory","lstset",
                                  "adjustfootnotemark",
                                  "keywords",
                                  "pacs",
                                  "psset",
                                  "enlargethispage",
                                  "pagenumbering",
                                  "setboxwidth",
                                  "refstepcounter",
                                  "theoremstyle",
                                  "markright","markleft"]

throw_away_macros_keep_argument = ["center", "centerline",
                                   "lowercase",
                                   "framebox", "boxed"]   
                              # not textup, because we want to keep it in math mode

throw_away_macros_keep_argument_in_text_only = ["text", "mbox"]   # surely there are many more?
          # mbox is probably an artifact from a conversion in an earlier stage of the SL2X script?

environments_to_delete = ["classification","keywords", "keyword"]

environments_to_delete_later = ["frontmatter"]

############################################

#
# need to be more specific about where these macro replacements should occur (everywhere, or just text)
# and when the replacement should be done (very beginning, or after everything is separated).
#
text_macros_html = {"mbox":[1," #1 "],        # figure out how to handle \mbox within math mode differently than mbox in a paragraph.
               #space above is for things like \small{\mbox{I}}, which you don;t want to be \smallI
               "paragraph":[1,"<br /><br />\n<b>#1</b> "],     # can do better
               "paragraphs":[1,"<br /><br />\n<b>#1</b> "],     # This one is preferred
               "emph":[1,"<em>#1</em>"],
               "textbf":[1,"<b>#1</b>"],  # why is this in more than one place?
               "textup":[1,"#1"],     # currently irrelevant, because in preprocess we convert textup to mbox
     #          "scriptsize":[1,"#1"],   # failed (bottom of page)  http://sl2x.aimath.org/development/collectedworks/htmlpaper/1109.0037/section2.html
               "ensuremath":[1,"#1"],  # this also appears elsewhere.  which is used? see http://sl2x.aimath.org/development/collectedworks/htmlpaper/1106.4806/section1.html
               "hspace":[1,""],
               "vspace":[1,""],
               "hspace\*":[1,""],
               "vspace\*":[1,""],
               "textsuperscript":[1,"<sup>#1</sup>"],
 # moved to tex_to_html_other              "href":[2,'<a href="#1">#2</a>'],
      #         "textcolor":[2,'<font color="#1">#2</font>'],   # need this to not be applied in math mode
               "textcolor":[2,'#2'],
               "numberwithin":[2,''],
               "addtolength":[2,''],
               "markboth":[2,''],
               "color":[2,'#2'],
               "linebreak":[0,'<br />'],
               "newline":[0,'<br />'],
               "indent":[0,'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'],
               "hrule":[0,'\n<hr style="width:50%;" align="left" />\n'],
               "lq":[0,'`'],
               "ldots":[0,'...'],
               "dots":[0,'...'],
               "qquad":[0,"&nbsp;&nbsp;&nbsp;"]}

# need to rethink this and the previous dictionary
text_macros_ptx = {"mbox":[1,"#1"],        # figure out how to handle \mbox within math mode differently than mbox in a paragraph.
               "enquote":[1,"<q>#1</q>"],
               "emph":[1,"<em>#1</em>"],
               "textbf":[1,"<b>#1</b>"],  # why is this in more than one place?
               "textup":[1,"#1"],     # currently irrelevant, because in preprocess we convert textup to mbox
               "ensuremath":[1,"#1"],  # this also appears elsewhere.  which is used? see http://sl2x.aimath.org/development/collectedworks/htmlpaper/1106.4806/section1.html
               "hspace":[1,""],
               "vspace":[1,""],
               "hspace\*":[1,""],
               "vspace\*":[1,""],
               "textsuperscript":[1,"<sup>#1</sup>"],
 # moved to tex_to_html_other              "href":[2,'<a href="#1">#2</a>'],
      #         "textcolor":[2,'<font color="#1">#2</font>'],   # need this to not be applied in math mode
               "textcolor":[2,'#2'],
               "numberwithin":[2,''],
               "addtolength":[2,''],
               "xautoref":[1,'<xref ref="#1" autoname="yes" />'],
               "markboth":[2,''],
               "color":[2,'#2'],
               "linebreak":[0,'<br />'],
               "newline":[0,'<br />'],
               "indent":[0,''],
               "hrule":[0,'\n<hr style="width:50%;" align="left" />\n'],
               "ldots":[0,'<ellipsis />'],
               "dots":[0,'<ellipsis />'],
               "qquad":[0,""]}

# begin/end{centering}, \textup, \mbox, \texorpdfstring, \keyword
# mbox only outside of math mode:      newtext = utilities.replacemacro(newtext,"mbox",1,"#1")
# how to handle "\ " hard space, or "\/" italic correction?  Or "\\" line feed?

########################################

# need to think how these interact with processing author environments
environment_abbrev = {
    "abstract" : ["abs","abstr"],
    "acknowledgement" : ["ack"],
    "assumption" : ["assu","ass"],
    "axiom" : ["axm"],
    "center" : ["centering"],
    "claim" : ["cla"],
    "conjecture" : ["con","conj","conjec"],
    "construction" : [],   # no abbreviations, but still convert capitalization
    "convention" : ["conv"],
    "corollary" : ["cor","corr","coro","corol","corss"],
    "definition" : ["def","defn","dfn","defi","defin","de"],
    "enumerate" : ["enum","enuma","enumerit"],
    "example" : ["exam","exa","eg","exmp","expl","exm"],
    "exercise" : ["exer", "exers"],
    "hypothesis" : ["hyp"],
    "lemma" : ["lem","lma","lemm"],
    "notation" : ["no","nota","ntn","nt","notn","notat"],
    "observation" : ["obs"],
    "problem" : ["prob","prb"],
    "proof" : ["pf","prf","demo"],
    "proposition" : ["prop","pro","prp","props"],
    "question" : ["qu","ques","quest","qsn"],
    "remark" : ["rem","rmk","rema","bem","subrem"],
    "remarks" : ["rems","rmks"],
    "scholium" : ["sch","schol"],
    "theorem" : ["thm","theo","theor","thmss"],
    "verbatim" : ["python"],    # figure out something better to do with that
    "warning" : ["warn", "wrn"]
    }   

macro_rename = [
    ["upmu","mu"],
    ["upgamma","gamma"],
    ["uppsi","psi"]
    ]


###################################

name_of_index_item = {
'tabular':'table',
'definition':'defn',
'proposition':'prop',
'theorem':'thm',
'exercise':'exer',
'example':'example',
'footnote':'note',
'historicalnote':'hist',
'remark':'rmk',
'text':'par'}


###################################

table_layout_options = ['c','l','r','X']

###################################

global_parameters = ["graphicspath"]
