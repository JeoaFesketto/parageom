
FT.open_project("_IEC_FILE_")
FT.unload_mesh() 
FT.link_mesh_file("_IGG_FILE_", 0) 

n_computations = FT.get_nb_computations()

for i in range(n_computations):
    FT.set_active_computations([0]) 
    FT.save_selected_computations() 

FT.save_project() 

for i in range(n_computations):
    FT.task(i).subtask(0).set_run_file("_IEC_FILE_"+FT.get_computation_name(i)+".run")

FT.save_project() 


