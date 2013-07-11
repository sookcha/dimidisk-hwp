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
def hello(filename):
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
					
	#print str(generate_htmldir_files(hwp5file, outdir))
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
			
			html_path = os.path.join(base_dir, 'index.html')
			css_path = os.path.join(base_dir, 'styles.css')
			#generate_css_file(xslt, path, css_path)
			html_xsl = hwp5_resources_filename('xsl/hwp5html.xsl')
			
			xslt_ext_tree = etree.XML(open(html_xsl).read())
			my_extension = MyExtElement()
			extensions = { ('testns', 'ext') : my_extension }
			transform = etree.XSLT(xslt_ext_tree, extensions = extensions)
						
			file = open(path)
			root = etree.XML(file.read())
			
			result = transform(root)
			return result
		finally:
			xhwp5.close()
		
			
	finally:
		os.unlink(path)

def generate_css_file(xslt, xhwp5_path, css_path):
	from hwp5.hwp5odt import hwp5_resources_filename

	css_xsl = hwp5_resources_filename('xsl/hwp5css.xsl')
	xslt(css_xsl, xhwp5_path, css_path)

if __name__ == "__main__":
	app.run()
