# -*- coding: utf-8 -*-

import os
import os.path
import logging
import sys

from flask import Flask
import sys
from hwp5 import __version__ as version
from hwp5.proc import rest_to_docopt
from hwp5.proc import init_logger
from hwp5.errors import InvalidHwp5FileError
from lxml import etree
from docopt import docopt

app = Flask(__name__)

class MyExtElement(etree.XSLTExtension):
	def execute(self, context, self_node, input_node, output_parent):
		print("Hello from XSLT!")
		output_parent.text = "I did it!"
		output_parent.extend(list(self_node))

@app.route("/<filename>")
def getHTML(filename):
	from hwp5.dataio import ParseError
	from hwp5.xmlmodel import Hwp5File
	try:
	    hwp5file = Hwp5File(filename)
	except ParseError, e:
	    e.print_to_logger(logger)
	    sys.exit(1)
	except InvalidHwp5FileError, e:
	    logger.error('%s', e)
	    sys.exit(1)
	else:
	    outdir = './'
	    if outdir is None:
	        outdir, ext = os.path.splitext(os.path.basename(filename))
					
	return str(generate_htmldir_files(hwp5file, outdir))
			
def generate_htmldir_files(hwp5file, base_dir):
	import os
	from tempfile import mkstemp
	from hwp5.plat import get_xslt
	from hwp5.hwp5odt import hwp5_resources_filename

	xslt = get_xslt()
	
	fd, path = mkstemp()
	try:
		xhwp5 = os.fdopen(fd, 'w')
		try:
			hwp5file.xmlevents(embedbin=False).dump(xhwp5)			
			
			htmlXSL = hwp5_resources_filename('xsl/hwp5html.xsl')
			cssXSL = hwp5_resources_filename('xsl/hwp5css.xsl')
			
			htmlxslTree = etree.XML(open(htmlXSL).read())
			cssxslTree = etree.XML(open(cssXSL).read())
			
			transformHTML = etree.XSLT(htmlxslTree)
			transformCSS = etree.XSLT(cssxslTree)
						
			file = open(path)
			
			originHTML = etree.XML(file.read())
			css = transformCSS(originHTML)
			html = transformHTML(originHTML)
			
			html = str(html).replace("</head>", "\t<style>" + str(css) + "</style>\n</head>")
			
			return html
		finally:
			xhwp5.close()
	finally:
		os.unlink(path)

if __name__ == "__main__":
	app.run()
