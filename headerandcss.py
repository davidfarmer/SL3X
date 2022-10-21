# -*- coding: utf-8 -*-

import component
import utilities


def add_on_js():
   """Patch for MathJax errors."""

   # genfrac in subscript of \sum or \prod
   thejs = '''
  MathJax.Hub.Register.StartupHook("TeX mathchoice Ready",function () {
    MathJax.ElementJax.mml.TeXmathchoice.Augment({
      choice: function () {
        if (this.selection != null) return this.selection;
        if (this.choosing) return 2; // prevent infinite loops:  see issue #1151
        this.choosing = true;
        var selection = 0, values = this.getValues("displaystyle","scriptlevel");
        if (values.scriptlevel > 0) {selection = Math.min(3,values.scriptlevel+1)}
          else {selection = (values.displaystyle ? 0 : 1)}
        // only cache the result if we are actually in place in a <math> tag.
        var node = this.inherit; while (node && node.type !== "math") node = node.inherit;
        if (node) this.selection = selection;
        this.choosing = false;
        return selection;
      }
    });
  });
'''

   return thejs

####################

def add_on_css():
   """CSS which is missing from mathbook.css."""

   thecss= ""

   return thecss

################

def header():

    if component.target == 'ptx':
        theheader = '<?xml version="1.0" encoding="UTF-8" ?>' + '\n'
        theheader += '<pretext xmlns:xi="http://www.w3.org/2001/XInclude" xml:lang="en-US">' + '\n'
        theheader += '<docinfo>' + '\n'

        return theheader

    theheader='''
<!DOCTYPE html>
<html>
<head>
'''
    theheader += '<title>'+utilities.tex_to_html(component.title)+'</title>'
    theheader += '''
<meta name="Keywords" content="Math paper converted by sl2x">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=0, minimum-scale=1.0 maximum-scale=1.0">
<script type="text/javascript" src="https://sagecell.sagemath.org/embedded_sagecell.js"></script>

<script type="text/x-mathjax-config">
      MathJax.Hub.Config({
        extensions: ["tex2jax.js", "TeX/AMSmath.js", "TeX/AMSsymbols.js", "https://aimath.org/mathbook/mathjaxknowl_new.js"],
        jax: ["input/TeX", "output/HTML-CSS"],
        displayAlign: "center",
        tex2jax: {
          inlineMath: [ ['$','$'], ["\\\\(","\\\\)"] ],
          displayMath: [ ['$$','$$'], ["\\\\[","\\\\]"] ],
          processEscapes: true
      },
      TeX: {
        MultLineWidth: "99%"
      },
        "HTML-CSS": {  scale: 90
      }
      });
</script>
<script type="text/javascript"
  src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.1/MathJax.js?config=TeX-AMS-MML_HTMLorMML-full">
</script>

<script>$(function () {
    // Make *any* div with class 'sagecell-sage' an executable Sage cell
    // Their results will be linked, only within language type
    sagecell.makeSagecell({inputLocation: 'div.sagecell-sage',
                           linked: true,
                           languages: ['sage'],
                           evalButtonText: 'Evaluate Sage Code'});
});
</script>
<script type="text/javascript" src="https://code.jquery.com/jquery-latest.min.js"></script> 
<script type="text/javascript" src="https://aimath.org/knowl.js"></script>
<link href="https://aimath.org/knowlstyle.css" rel="stylesheet" type="text/css" /> 

<script src="https://aimath.org/mathbook/js/lib/jquery.sticky.js"></script>
<script src="https://aimath.org/mathbook/js/lib/jquery.espy.min.js"></script>
<script src="https://aimath.org/mathbook/js/Mathbook.js"></script>
'''

    theheader += '<link href="https://aimath.org/mathbook/stylesheets/mathbook-'+component.style_number+'.css" rel="stylesheet" type="text/css" />\n'

    theheader += '<link href="https://aimath.org/mathbook/mathbook-add-on.css" rel="stylesheet" type="text/css" />\n'

    theheader += '<link href="add-on.css" rel="stylesheet" type="text/css" />\n' 
    theheader += '<script type="text/javascript" src="add-on.js"></script>\n'
    theheader += '<script type="text/javascript" src="https://aimath.org/mathbook/mathbook-add-on.js"></script>\n'

    theheader +='''
</head>
<body class="has-sidebar-left">
<a class="assistive" href="#content">Skip to main content</a>

'''

    return theheader

############

def arrowleft():

    thearrow = '''
<svg height="50" width="60"
 viewBox="-10 50 110 100"
   xmlns="https://www.w3.org/2000/svg" >
<polygon points="-10,100 25,75 100,75 100,125 25,125 "
style="fill:blanchedalmond;stroke:burlywood;stroke-width:1" />
<text x="28" y="108" fill="maroon" font-size="32">prev</text>
</svg>
'''
    return thearrow

############

def arrowright():

    thearrow = '''
<svg height="50" width="60"
 viewBox="0 50 110 100"
   xmlns="https://www.w3.org/2000/svg" >
<polygon points="110,100 75,75 0,75 0,125 75,125 "
style="fill:darkred;stroke:maroon;stroke-width:1"
/>
<text x="13" y="108" fill="blanchedalmond" font-size="32">next</text>
</svg>
'''
    return thearrow

