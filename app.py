# -*- coding: utf-8 -*-

import os
import os.path
import logging

from flask import Flask
import sys
from hwp5 import __version__ as version
from hwp5.proc import rest_to_docopt
from hwp5.proc import init_logger
from hwp5.errors import InvalidHwp5FileError
from docopt import docopt

app = Flask(__name__)

@app.route("/")
def hello():
		filename = args['idea.hwp']
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
		    outdir = args['./']
		    if outdir is None:
		        outdir, ext = os.path.splitext(os.path.basename(filename))
		    generate_htmldir(hwp5file, outdir)
	
	
    return "Hello World!"

if __name__ == "__main__":
    app.run()
		
def generate_htmldir(hwp5file, base_dir):
    if not os.path.exists(base_dir):
        os.mkdir(base_dir)
    generate_htmldir_files(hwp5file, base_dir)


def generate_htmldir_files(hwp5file, base_dir):
    import os
    from tempfile import mkstemp
    from hwp5.plat import get_xslt

    xslt = get_xslt()
    fd, path = mkstemp()
    try:
        xhwp5 = os.fdopen(fd, 'w')
        try:
            hwp5file.xmlevents(embedbin=False).dump(xhwp5)
        finally:
            xhwp5.close()

        html_path = os.path.join(base_dir, 'index.html')
        generate_html_file(xslt, path, html_path)

        css_path = os.path.join(base_dir, 'styles.css')
        generate_css_file(xslt, path, css_path)
    finally:
        os.unlink(path)

    bindata_dir = os.path.join(base_dir, 'bindata')
    extract_bindata_dir(hwp5file, bindata_dir)


def generate_css_file(xslt, xhwp5_path, css_path):
    from hwp5.hwp5odt import hwp5_resources_filename

    css_xsl = hwp5_resources_filename('xsl/hwp5css.xsl')
    xslt(css_xsl, xhwp5_path, css_path)


def generate_html_file(xslt, xhwp5_path, html_path):
    from hwp5.hwp5odt import hwp5_resources_filename

    html_xsl = hwp5_resources_filename('xsl/hwp5html.xsl')
    xslt(html_xsl, xhwp5_path, html_path)


def extract_bindata_dir(hwp5file, bindata_dir):
    if 'BinData' not in hwp5file:
        return
    bindata_stg = hwp5file['BinData']
    if not os.path.exists(bindata_dir):
        os.mkdir(bindata_dir)

    from hwp5.storage import unpack
    unpack(bindata_stg, bindata_dir)
