import os
import parageom.ressources.path as pg_path

init_f_path = os.path.dirname(pg_path.__file__)
ag_script = "autogrid_script_template.py"
computations_script_DGEN = "new_computation_DGEN_mesh.py"

# TODO make this a single file by having it inside functions.py directly.

default_options = {
    '_CASE_NAME_': 'case',
    '_TEMPLATE_': '/scratch/daep/j.fesquet/r37_del_later/bs.trb',
    '_GEOMTURBO_': '/scratch/daep/j.fesquet/rotor_DGEN_5.geomTurbo',
    '_OUTPUT_DIR_': '/scratch/daep/j.fesquet/r37_del_later/test/',
}

def make_ag_script(options, script_output_file='ag_script.py'):

    with open(f'{init_f_path}/{ag_script}', 'r') as f: data = f.read()

    for key, value in options.items():
        data = data.replace(key, value)

    with open(script_output_file, 'w') as f: f.write(data)


def make_new_computations_script(options, script_output_file = 'fine_script.py', mesh = 'DGEN'):

    if mesh == 'DGEN':
        with open(f'{init_f_path}/{computations_script_DGEN}', 'r') as f: data = f.read()
    
    for key, value in options.items():
        data = data.replace(key, value)
    
    with open(script_output_file, 'w') as f: f.write(data)


