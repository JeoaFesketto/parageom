def log(msg):
	f=open(_LOG_FILE_, 'a')
	print >> f, msg
	f.close()

f=open(_LOG_FILE_, 'w')
print >> f, 'starting script'
f.close()

log('loading project file')
FT.open_project(_PROJECT_FILE_)
log('project loaded')

FT.set_active_computations([0])


computations = _COMPUTATIONS_LIST_
log('computations to be added')
log(computations)

n = FT.get_nb_computations()

for computation in computations:
	rpm, pressure = computation
	FT.new_computation() 
	FT.set_active_computations([n]) 
	name = "{rpm}rpm_{pressure}kp".format(rpm=rpm, pressure=pressure/1000)
	log('creating new computation:')
	log(name)
	FT.set_computation_name(n, name)
	FT.get_rotating_block_group(0).set_rotational_speed(rpm) 
	FT.get_bc_group(FT.get_bc_patch(0, 0, 0)).set_parameter_value("Static_Pressure", pressure) 
	FT.get_bc_group(FT.get_bc_patch(1, 2, 0)).set_parameter_value("Rotational Speed 1", rpm) 
	FT.get_bc_group(FT.get_bc_patch(6, 2, 0)).set_parameter_value("Rotational Speed 1", rpm) 
	n += 1
	FT.save_selected_computations()

log('saving project')
FT.save_project()
log('project saved')


log('script executed successfully')






