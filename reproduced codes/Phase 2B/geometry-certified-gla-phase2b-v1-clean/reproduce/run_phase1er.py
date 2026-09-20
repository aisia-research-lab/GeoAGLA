from experiments.phase1er_repair.run import run
import runpy
if __name__=='__main__':
    run()
    runpy.run_module('experiments.phase1er_repair.horizon',run_name='__main__')
