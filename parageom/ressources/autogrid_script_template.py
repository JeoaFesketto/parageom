output_dir = '_OUTPUT_DIR_'
case_name =	'_CASE_NAME_'

def log(msg):
	f=open(output_dir+'/'+'script.log', 'a')
	print >> f, msg
	f.close()

def get_values_hub_fillet(row_i):
        m = []
        hub_fillet = row(row_i).blade(1).get_hub_fillet()
        if hub_fillet != 0:
                for fn in dir(hub_fillet):
                        if callable(getattr(hub_fillet, fn)):
                                if fn.startswith('get') and fn != 'get_defined_shape':
                                        m.append([fn, getattr(hub_fillet, fn)()])
                return m

def make_hub_fillet(row_i, params):
        row(row_i).blade(1).get_hub_fillet().delete()
        row(row_i).add_hub_fillet()
        for elem in params:
                getattr(row(row_i).blade(1).get_hub_fillet(), elem[0].replace('get', 'set'))(elem[1])
        log('new hub fillet created')

def get_values_shroud_gap(row_i):
        m = []
        shroud_gap = row(row_i).blade(1).get_shroud_gap()
        if shroud_gap != 0:
                for fn in dir(shroud_gap):
                        if callable(getattr(shroud_gap, fn)):
                                if fn.startswith('get') and fn != 'get_defined_shape':
                                        m.append([fn, getattr(shroud_gap, fn)()])
                return m

def make_shroud_gap(row_i, params):
        row(row_i).blade(1).get_shroud_gap().delete()
        row(row_i).add_shroud_gap()
        shroud_gap = row(1).blade(1).get_shroud_gap()
        for elem in params:
                if elem[0] == 'get_topology_type':
                        if elem[1] == 0:
                                shroud_gap.set_topology_HO()
                        elif elem[1] == 1:
                                shroud_gap.set_topology_O()
                        elif elem[1] == 3:
                                shroud_gap.set_topology_O2H()
                else:
                        getattr(shroud_gap, elem[0].replace('get', 'set'))(elem[1])
        log('new shroud gap created')


f=open(output_dir+'/'+'script.log', 'w')
print >> f, 'starting'
f.close()

a5_open_project('_TEMPLATE_')
log('opened project')

a5_save_project(output_dir+'/'+case_name+'.trb')

m = get_values_hub_fillet(1)

row(1).load_geometry('_GEOMTURBO_')
log('replaced geometry')

make_hub_fillet(1, m)

log('saving project')
a5_save_project(output_dir+'/'+case_name+'.trb')
log('project saved')

log('generating 3D mesh')
a5_generate_3d()
log('3D mesh generated')

log('saving project')
a5_save_project(output_dir+'/'+case_name+'.trb')
log('done')

