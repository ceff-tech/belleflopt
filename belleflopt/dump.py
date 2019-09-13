"""
	For dumping fixtures. Our code is designed so that it can run from the very beginning with data load
	and network building each time, but that's slower than running that once, dumping some fixtures and loading them,
	which matters once we hit Azure Pipelines. This code handles the database population and dumping.
"""

"python manage.py dumpdata belleflopt.StreamSegment -o ./belleflopt/fixtures/stream_segment.csv"