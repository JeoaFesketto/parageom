output_dir = '_OUTPUT_DIR_'
case_name =	'_CASE_NAME_'

def log(msg):
	f=open(output_dir+'/'+'script.log', 'a')
	print >> f, msg
	f.close()

f=open(output_dir+'/'+'script.log', 'w')
print >> f, 'starting'
f.close()

a5_open_project('_TEMPLATE_')
log('opened project')

a5_save_project(output_dir+'/'+case_name+'.trb')

m = []
for fn in dir(row(1).blade(1).get_hub_fillet()):
	if callable(getattr(row(1).blade(1).get_hub_fillet(), fn)):
		if fn.startswith('get') and fn != 'get_defined_shape':
			m.append([fn, getattr(row(1).blade(1).get_hub_fillet(), fn)()])
log(m)

row(1).load_geometry('_GEOMTURBO_')
log('replaced geometry')

row(1).blade(1).get_hub_fillet().delete()
row(1).add_hub_fillet()
for elem in m:
	getattr(row(1).blade(1).get_hub_fillet(), elem[0].replace('get', 'set'))(elem[1])
log('new hub fillet created')

log('saving project')
a5_save_project(output_dir+'/'+case_name+'.trb')
log('project saved')

log('generating 3D mesh')
a5_generate_3d()
log('3D mesh generated')

log('saving project')
a5_save_project(output_dir+'/'+case_name+'.trb')
log('done')

