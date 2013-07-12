# -*- coding: utf-8 -*-

import os
import os.path
import logging
import sys
import urllib
import urllib2
import tempfile
import StringIO

from flask import Flask
from flask import Response
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

@app.route("/<session>/<diskId>/<fileId>/<filename>")
def getHTML(session,diskId,fileId,filename):
	from hwp5.dataio import ParseError
	from hwp5.xmlmodel import Hwp5File
	from tempfile import mkstemp
	
	url = 'http://disk.dimigo.hs.kr:8282/WebFileDownloader.do'
	values = {'id' : fileId,
	          'diskType' : 'sharedisk',
	          'diskId' : diskId }
						
	headers = {
	  'Origin' : 'http://disk.dimigo.hs.kr:8282',
	  'Accept-Encoding' : 'gzip,deflate',
	  'Content-Type' : 'application/x-www-form-urlencoded',
	  'Accept' : 'image/gif, image/x-xbitmap, image/jpeg, image/pjpeg, */*',
	  'User-Agent' : 'DimiDisk',
	  'Cookie' : 'JSESSIONID=' + session
	}
	
	data = urllib.urlencode(values)
	req = urllib2.Request(url, data, headers)
	
	response = urllib2.urlopen(req)
	downloadedHWP = response.read()
	
	tempHWP, tempPath = tempfile.mkstemp()
	realHWP = os.fdopen(tempHWP, 'w')
	realHWP.write(downloadedHWP)	
	realHWP.close()
	
	try:
		hwp5file = Hwp5File(tempPath)
	except ParseError, e:
		e.print_to_logger(logger)
	except InvalidHwp5FileError, e:
		logger.error('%s', e)
	else:
		outdir = './'
		if outdir is None:
			outdir, ext = os.path.splitext(os.path.basename(tempPath))	
	return hwpToHTML(hwp5file, outdir)
			
def hwpToHTML(hwp5file, base_dir):
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
			
			return str(html)
		finally:
			xhwp5.close()
	finally:
		os.unlink(path)

if __name__ == "__main__":
	app.run(debug=True)
