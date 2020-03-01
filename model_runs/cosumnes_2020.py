from belleflopt import support

from pyinstrument import Profiler

profiler = Profiler()
profiler.start()

support.run_optimize_new(NFE=50, popsize=10, use_comet=False)

profiler.stop()

print(profiler.output_text(unicode=False, color=False))

