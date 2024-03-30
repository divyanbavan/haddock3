# Generates only one plan based on one selection of residues
haddock3-restraints z_surface_restraints --pdb data/protein.pdb --residues 19,83,145,119,83,145,167 --output data/one_z_surface_selection

# Generates two plans based on the two residues selections
haddock3-restraints z_surface_restraints --pdb data/protein.pdb --residues 19,83,145,119,83,145,167 98,101,126,129 --output data/protein_z_restraints

# Generates two plans based on the two residues selections and reduce both area of the surface and space between beads
haddock3-restraints z_surface_restraints --pdb data/protein.pdb --residues 19,83,145,119,83,145,167 98,101,126,129 --output data/protein_z_restraints_smallspacing --spacing 4 --x-size 20 --y-size 20

# Generates two plans based on the two residues selections and reduce both area of the surface and space between beads
haddock3-restraints z_surface_restraints --pdb data/protein.pdb --residues 19,83,145,119,83,145,167 98,101,126,129 23,62,87,111,116,153,163 --output data/three_z_restraints
