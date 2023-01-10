FT.new_computation() 
FT.set_active_computations([6]) 
FT.set_computation_name(6, "12000rpm_90kp") 
FT.get_rotating_block_group(0).set_rotational_speed(12000) 
FT.get_bc_group(FT.get_bc_patch(0, 0, 0)).set_parameter_value("Static_Pressure", 90000) 
FT.get_bc_group(FT.get_bc_patch(1, 2, 0)).set_parameter_value("Rotational Speed 1", 12000) 
FT.get_bc_group(FT.get_bc_patch(6, 2, 0)).set_parameter_value("Rotational Speed 1", 12000) 


