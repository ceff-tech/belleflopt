from belleflopt import support

from pyinstrument import Profiler

profiler = Profiler()
profiler.start()

support.run_optimize_new(NFE=25, popsize=5, use_comet=False)

profiler.stop()

print(profiler.output_text(unicode=False, color=False))

