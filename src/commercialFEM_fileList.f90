!--------------------------------------------------------------------------------------------------
!> @author Martin Diehl, Max-Planck-Institut für Eisenforschung GmbH
!> @brief all DAMASK files without solver
!> @details List of files needed by MSC.Marc
!--------------------------------------------------------------------------------------------------
#include "IO.f90"
#include "numerics.f90"
#include "debug.f90"
#include "list.f90"
#include "future.f90"
#include "config.f90"
#include "LAPACK_interface.f90"
#include "math.f90"
#include "quaternions.f90"
#include "Lambert.f90"
#include "rotations.f90"
#include "FEsolving.f90"
#include "element.f90"
#include "HDF5_utilities.f90"
#include "results.f90"
#include "geometry_plastic_nonlocal.f90"
#include "discretization.f90"
#ifdef Marc4DAMASK
#include "marc/discretization_marc.f90"
#endif
#include "material.f90"
#include "lattice.f90"
#include "source_thermal_dissipation.f90"
#include "source_thermal_externalheat.f90"
#include "source_damage_isoBrittle.f90"
#include "source_damage_isoDuctile.f90"
#include "source_damage_anisoBrittle.f90"
#include "source_damage_anisoDuctile.f90"
#include "kinematics_cleavage_opening.f90"
#include "kinematics_slipplane_opening.f90"
#include "kinematics_thermal_expansion.f90"
#include "constitutive.f90"
#include "constitutive_plastic_none.f90"
#include "constitutive_plastic_isotropic.f90"
#include "constitutive_plastic_phenopowerlaw.f90"
#include "constitutive_plastic_kinehardening.f90"
#include "constitutive_plastic_dislotwin.f90"
#include "constitutive_plastic_disloUCLA.f90"
#include "constitutive_plastic_nonlocal.f90"
#include "crystallite.f90"
#include "thermal_isothermal.f90"
#include "thermal_adiabatic.f90"
#include "thermal_conduction.f90"
#include "damage_none.f90"
#include "damage_local.f90"
#include "damage_nonlocal.f90"
#include "homogenization.f90"
#include "homogenization_mech_none.f90"
#include "homogenization_mech_isostrain.f90"
#include "homogenization_mech_RGC.f90"
#include "CPFEM.f90"
