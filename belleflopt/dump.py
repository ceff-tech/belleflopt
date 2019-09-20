"""
	For dumping fixtures. Our code is designed so that it can run from the very beginning with data load
	and network building each time, but that's slower than running that once, dumping some fixtures and loading them,
	which matters once we hit Azure Pipelines. This code handles the database population and dumping.
"""

from eflows_optimization import settings
import zipfile
import os
from io import StringIO

from django.core import management

import belleflopt


def dump_all():
	"""
		Dumps bz2-compressed stream segment fixtures
	:return:
	"""
	filename = "belleflopt.json"
	output_location = os.path.join(settings.BASE_DIR, "belleflopt", "fixtures", "{}.zip".format(filename))

	with zipfile.ZipFile(output_location, 'w', compression=zipfile.ZIP_LZMA) as zip_filehandle:
		with StringIO() as single_filehandle:
			management.call_command('dumpdata', 'belleflopt', stdout=single_filehandle)
			zip_filehandle.writestr(filename, single_filehandle.getvalue())
