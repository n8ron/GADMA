import unittest

from .test_data import YRI_CEU_DATA
from gadma import *
import gadma
from gadma import *
import dadi
import copy
import pickle
import shutil

DATA_PATH = os.path.join(os.path.dirname(__file__), "test_data")


def rmdir(dirname):
    if not os.path.exists(dirname):
        return
    for filename in os.listdir(dirname):
        path = os.path.join(dirname, filename)
        if os.path.isdir(path):
            rmdir(path)
        else:
            os.remove(path)
    os.rmdir(dirname)


def rosenbrock(X):
    """
    This R^2 -> R^1 function should be compatible with algopy.
    http://en.wikipedia.org/wiki/Rosenbrock_function
    A generalized implementation is available
    as the scipy.optimize.rosen function
    """
    x = X[0]
    y = X[1]
    a = 1. - x
    b = y - x*x
    return a*a + b*b*100.


class TestRestore(unittest.TestCase):
    def test_ga_restore(self):
        ga = get_global_optimizer("Genetic_algorithm")
        f = rosenbrock
        variables = [ContinuousVariable('var1', [-1, 2]),
                     ContinuousVariable('var2', [-2, 3])]
        save_file = "save_file"
        report_file = "report_file"
        res1 = ga.optimize(f, variables, maxiter=5, verbose=1,
                           report_file=report_file,
                           save_file=save_file)

        res2 = ga.optimize(f, variables, maxiter=10, verbose=1,
                           report_file=report_file,
                           restore_file=save_file)

        res3 = ga.optimize(f, variables, maxiter=5, verbose=1,
                           report_file=report_file,
                           restore_file=save_file)

        self.assertEqual(res1.y, res3.y, msg=f"{res1}\n{res3}")
        self.assertTrue(res1.y >= res2.y, msg=f"{res1}\n{res2}")

    def test_ls_restore(self):
        for opt in all_local_optimizers():
            f = rosenbrock
            # positive domain because we check log scaling optimizations too
            variables = [ContinuousVariable('var1', [10, 20]),
                         ContinuousVariable('var2', [1, 2])]
            x0 = [var.resample() for var in variables]
            save_file = "save_file"
            report_file = "report_file"
            res1 = opt.optimize(f, variables, x0=x0, maxiter=5, verbose=1,
                                report_file=report_file,
                                save_file=save_file)
            res2 = opt.optimize(f, variables, x0=x0, maxiter=5, verbose=1,
                                report_file=report_file,
                                restore_file=save_file,
                                restore_models_only=True)
            res3 = opt.optimize(f, variables, x0=x0, maxiter=5, verbose=1,
                                report_file=report_file,
                                restore_file=save_file)
            res4 = opt.optimize(f, variables, x0=x0, maxiter=10, verbose=1,
                                report_file=report_file,
                                restore_file=save_file,
                                restore_models_only=True)
            self.assertEqual(res1.y, res3.y)
            self.assertTrue(res1.y >= res2.y)
            self.assertTrue(res2.y >= res4.y)
            for res in [res1, res2, res3, res4]:
                self.assertEqual(res.y, f(res.x))

    def test_gs_and_ls_restore(self):
        param_file = os.path.join(DATA_PATH, 'another_test_params')
        base_out_dir = "test_gs_and_ls_restore_output"
        sys.argv = ['gadma', '-p', param_file, '-o', base_out_dir]
        settings, _ = get_settings()
        settings.linked_snp_s = False
        out_dir = 'some_not_existed_dir'
        shared_dict = gadma.shared_dict.SharedDictForCoreRun(multiprocessing=False)
        if os.path.exists(out_dir):
            rmdir(out_dir)
        for ls_opt in all_local_optimizers():
            if os.path.exists(settings.output_directory):
                rmdir(settings.output_directory)
            if os.path.exists(out_dir):
                rmdir(out_dir)
            settings.local_optimizer = ls_opt.id
            core_run = CoreRun(0, shared_dict, settings)
            res1 = core_run.run()

            restore_settings = copy.copy(settings)
            restore_settings.output_directory = out_dir
            restore_settings.resume_from = settings.output_directory

            restore_core_run = CoreRun(0, shared_dict, restore_settings)
            res2 = restore_core_run.run()

            self.assertEqual(res1.y, res2.y)
            if os.path.exists(out_dir):
                rmdir(out_dir)

            restore_settings.only_models = True
            restore_core_run = CoreRun(0, shared_dict, restore_settings)
            res3 = restore_core_run.run()

            self.assertTrue(res3.y >= res2.y)
        if os.path.exists(settings.output_directory):
            rmdir(settings.output_directory)

    def test_restore_finished_run(self):
        finished_run_dir = os.path.join(DATA_PATH, 'my_example_run')
        params_file = 'params'
        with open(params_file, 'w') as fl:
            fl.write("Linked SNP's: False")
        sys.argv = ['gadma', '--resume', finished_run_dir, '-p', params_file]
        try:
            core.main()
        finally:
            if check_dir_existence(finished_run_dir + '_resumed'):
                shutil.rmtree(finished_run_dir + '_resumed')
            os.remove(params_file)

    def test_restore_models_from_finished_run(self):
        finished_run_dir = os.path.join(DATA_PATH, 'my_example_run')
        params_file = 'params'
        with open(params_file, 'w') as fl:
            fl.write("Stuck generation number: 2\n"
                     "Only models: True\n"
                     "Projections: [4,4]")
        sys.argv = ['gadma', '--resume', finished_run_dir, '-p', params_file]
        try:
            core.main()
        finally:
            if check_dir_existence(finished_run_dir + '_resumed'):
                shutil.rmtree(finished_run_dir + '_resumed')
            os.remove(params_file)

    def test_restore_with_different_options_1(self):
        finished_run_dir = os.path.join(DATA_PATH, 'my_example_run')
        params_file = 'params'
        with open(params_file, 'w') as fl:
            fl.write("Stuck generation number: 2\n"
                     "Symmetric migrations: True\n"
                     "Only sudden: True\n"
                     "Split fractions: False\n"
                     "Projections: 4,4")
        sys.argv = ['gadma', '--resume', finished_run_dir, '-p', params_file]
        try:
            core.main()
        finally:
            if check_dir_existence(finished_run_dir + '_resumed'):
                shutil.rmtree(finished_run_dir + '_resumed')
            os.remove(params_file)

    def test_restore_with_different_options_2(self):
        finished_run_dir = os.path.join(DATA_PATH, 'my_example_run')
        params_file = 'params'
        with open(params_file, 'w') as fl:
            fl.write("Stuck generation number: 2\n"
                     "Engine: dadi\n"
                     "Projections: 4,4")
        sys.argv = ['gadma', '--resume', finished_run_dir, '-p', params_file]
        try:
            core.main()
        finally:
            if check_dir_existence(finished_run_dir + '_resumed'):
                shutil.rmtree(finished_run_dir + '_resumed')
            os.remove(params_file)