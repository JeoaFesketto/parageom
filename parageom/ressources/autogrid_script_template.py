output_dir = '_OUTPUT_DIR_'
case_name =	'_CASE_NAME_'
row_number = _ROW_NUMBER_

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

def get_values_shroud_fillet(row_i):
        m = []
        shroud_fillet = row(row_i).blade(1).get_shroud_fillet()
        if shroud_fillet != 0:
                for fn in dir(shroud_fillet):
                        if callable(getattr(shroud_fillet, fn)):
                                if fn.startswith('get') and fn != 'get_defined_shape':
                                        m.append([fn, getattr(shroud_fillet, fn)()])
                return m

def make_shroud_fillet(row_i, params):
        row(row_i).blade(1).get_shroud_fillet().delete()
        row(row_i).add_shroud_fillet()
        for elem in params:
                getattr(row(row_i).blade(1).get_shroud_fillet(), elem[0].replace('get', 'set'))(elem[1])
        log('new shroud fillet created')

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

def get_values_hub_gap(row_i):
        m = []
        hub_gap = row(row_i).blade(1).get_hub_gap()
        if hub_gap != 0:
                for fn in dir(hub_gap):
                        if callable(getattr(hub_gap, fn)):
                                if fn.startswith('get') and fn != 'get_defined_shape':
                                        m.append([fn, getattr(hub_gap, fn)()])
                return m

def make_hub_gap(row_i, params):
        row(row_i).blade(1).get_hub_gap().delete()
        row(row_i).add_hub_gap()
        hub_gap = row(1).blade(1).get_hub_gap()
        for elem in params:
                if elem[0] == 'get_topology_type':
                        if elem[1] == 0:
                                hub_gap.set_topology_HO()
                        elif elem[1] == 1:
                                hub_gap.set_topology_O()
                        elif elem[1] == 3:
                                hub_gap.set_topology_O2H()
                else:
                        getattr(hub_gap, elem[0].replace('get', 'set'))(elem[1])
        log('new hub gap created')

f=open(output_dir+'/'+'script.log', 'w')
print >> f, 'starting'
f.close()

a5_open_project('_TEMPLATE_')
log('opened project')

a5_save_project(output_dir+'/'+case_name+'.trb')

m = row(row_i).blade(1).get_hub_fillet()
n = row(row_i).blade(1).get_shroud_fillet()
g = row(row_i).blade(1).get_hub_gap()
p = row(row_i).blade(1).get_shroud_gap()

if m != 0:
	m = get_values_hub_fillet(row_number)
if n != 0:
	n = get_values_shroud_fillet(row_number)
if g != 0:
	g = get_values_hub_gap(row_number)
if p != 0:
	p = get_values_shroud_gap(row_number)

row(row_number).load_geometry('_GEOMTURBO_')
log('replaced geometry')

if m != 0:
	make_hub_fillet(row_number, m)
if n != 0:
	make_shroud_fillet(row_number, n)
if g != 0:
	make_hub_gap(row_number, g)
if p != 0:
	make_shroud_gap(row_number, p)

log('saving project')
a5_save_project(output_dir+'/'+case_name+'.trb')
log('project saved')

log('generating 3D mesh')
a5_generate_3d()
log('3D mesh generated')

log('saving project')
a5_save_project(output_dir+'/'+case_name+'.trb')
log('done')

