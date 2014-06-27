!--------------------------------------------------------------------------------------------------
! $Id: constitutive_thermal.f90 3205 2014-06-17 06:54:49Z MPIE\m.diehl $
!--------------------------------------------------------------------------------------------------
!> @author Pratheek Shanthraj, Max-Planck-Institut für Eisenforschung GmbH
!> @author Franz Roters, Max-Planck-Institut für Eisenforschung GmbH
!> @brief thermal internal microstructure state
!--------------------------------------------------------------------------------------------------
module constitutive_thermal
 use prec, only: &
   pInt, &
   pReal
 
 implicit none
 private
 integer(pInt), public, dimension(:,:,:), allocatable :: &
   constitutive_thermal_sizePostResults                                                                      !< size of postResults array per grain
 integer(pInt), public, protected :: &
   constitutive_thermal_maxSizePostResults, &
   constitutive_thermal_maxSizeDotState
 public :: & 
   constitutive_thermal_init, &
   constitutive_thermal_microstructure, &
   constitutive_thermal_collectDotState, &
   constitutive_thermal_collectDeltaState, &
   constitutive_thermal_postResults
 
contains


!--------------------------------------------------------------------------------------------------
!> @brief allocates arrays pointing to array of the various constitutive modules
!--------------------------------------------------------------------------------------------------
subroutine constitutive_thermal_init

 use, intrinsic :: iso_fortran_env                                                                  ! to get compiler_version and compiler_options (at least for gfortran 4.6 at the moment)
 use IO, only: &
   IO_open_file, &
   IO_open_jobFile_stat, &
   IO_write_jobFile, &
   IO_timeStamp
 use mesh, only: &
   mesh_maxNips, &
   mesh_NcpElems, &
   mesh_element, &
   FE_Nips, &
   FE_geomtype
 use material, only: &
   material_phase, &
   material_Nphase, &
   material_localFileExt, &    
   material_configFile, &    
   phase_name, &
   phase_thermal, &
   phase_thermalInstance, &
   phase_Noutput, &
   homogenization_Ngrains, &
   homogenization_maxNgrains, &
   thermalState, &
   THERMAL_none_ID, &
   THERMAL_NONE_label, &
   THERMAL_conduction_ID, &
   THERMAL_CONDUCTION_label
 use thermal_none
 use thermal_conduction
   
 implicit none
 integer(pInt), parameter :: FILEUNIT = 200_pInt
 integer(pInt) :: &
  g, &                                                                                              !< grain number
  i, &                                                                                              !< integration point number
  e, &                                                                                              !< element number
  cMax, &                                                                                           !< maximum number of grains
  iMax, &                                                                                           !< maximum number of integration points
  eMax, &                                                                                           !< maximum number of elements
  phase, &
  s, &
  p, &
  instance,&
  myNgrains

 integer(pInt), dimension(:,:), pointer :: thisSize
 logical :: knownThermal
 character(len=64), dimension(:,:), pointer :: thisOutput
 character(len=32) :: outputName                                                                    !< name of output, intermediate fix until HDF5 output is ready
 
!--------------------------------------------------------------------------------------------------
! parse from config file
 if (.not. IO_open_jobFile_stat(FILEUNIT,material_localFileExt)) &                                  ! no local material configuration present...
   call IO_open_file(FILEUNIT,material_configFile)                                                  ! ... open material.config file
 if (any(phase_thermal == THERMAL_none_ID))       call thermal_none_init(FILEUNIT)
 if (any(phase_thermal == THERMAL_conduction_ID)) call thermal_conduction_init(FILEUNIT)
 close(FILEUNIT)
 
 write(6,'(/,a)')   ' <<<+-  constitutive_thermal init  -+>>>'
 write(6,'(a)')     ' $Id: constitutive_thermal.f90 3205 2014-06-17 06:54:49Z MPIE\m.diehl $'
 write(6,'(a15,a)') ' Current time: ',IO_timeStamp()
#include "compilation_info.f90"
 
!--------------------------------------------------------------------------------------------------
! write description file for constitutive phase output
 call IO_write_jobFile(FILEUNIT,'outputThermal') 
 do phase = 1_pInt,material_Nphase
   instance = phase_thermalInstance(phase)                                                           ! which instance is present phase
   knownThermal = .true.
   select case(phase_thermal(phase))                                                                 ! split per constititution
     case (THERMAL_none_ID)
       outputName = THERMAL_NONE_label
       thisOutput => null()
       thisSize   => null()
     case (THERMAL_conduction_ID)
       outputName = THERMAL_CONDUCTION_label
       thisOutput => thermal_conduction_output
       thisSize   => thermal_conduction_sizePostResult
     case default
       knownThermal = .false.
   end select   
   write(FILEUNIT,'(/,a,/)') '['//trim(phase_name(phase))//']'
   if (knownThermal) then
     write(FILEUNIT,'(a)') '(thermal)'//char(9)//trim(outputName)
     if (phase_thermal(phase) /= THERMAL_none_ID) then
       do e = 1_pInt,phase_Noutput(phase)
         write(FILEUNIT,'(a,i4)') trim(thisOutput(e,instance))//char(9),thisSize(e,instance)
       enddo
     endif
   endif
 enddo
 close(FILEUNIT)
 
!--------------------------------------------------------------------------------------------------
! allocation of states
 cMax = homogenization_maxNgrains
 iMax = mesh_maxNips
 eMax = mesh_NcpElems
 allocate(constitutive_thermal_sizePostResults(cMax,iMax,eMax), source=0_pInt)
 
 ElemLoop:do e = 1_pInt,mesh_NcpElems                                                               ! loop over elements
   myNgrains = homogenization_Ngrains(mesh_element(3,e)) 
   IPloop:do i = 1_pInt,FE_Nips(FE_geomtype(mesh_element(2,e)))                                     ! loop over IPs
     GrainLoop:do g = 1_pInt,myNgrains                                                              ! loop over grains
       phase = material_phase(g,i,e)
       instance = phase_thermalInstance(phase)
       select case(phase_thermal(phase))
         case (THERMAL_conduction_ID) 
           constitutive_thermal_sizePostResults(g,i,e) =    thermal_conduction_sizePostResults(instance)
       end select
     enddo GrainLoop
   enddo IPloop
 enddo ElemLoop
 
 constitutive_thermal_maxSizePostResults = maxval(constitutive_thermal_sizePostResults)
 constitutive_thermal_maxSizeDotState = 0_pInt
 do p = 1, size(thermalState)
  constitutive_thermal_maxSizeDotState = max(constitutive_thermal_maxSizeDotState, thermalState(p)%sizeDotState)
 enddo
end subroutine constitutive_thermal_init


!--------------------------------------------------------------------------------------------------
!> @brief calls microstructure function of the different constitutive models
!--------------------------------------------------------------------------------------------------
subroutine constitutive_thermal_microstructure(Tstar_v, Lp, ipc, ip, el)
 use material, only: &
   material_phase, &
   phase_thermal, &
   THERMAL_conduction_ID
 use thermal_conduction, only: &
   thermal_conduction_microstructure

 implicit none
 integer(pInt), intent(in) :: &
   ipc, &                                                                                           !< grain number
   ip, &                                                                                            !< integration point number
   el                                                                                               !< element number
 real(pReal),  intent(in), dimension(6) :: &
   Tstar_v                                                                                          !< 2nd Piola Kirchhoff stress tensor (Mandel)
 real(pReal),  intent(in), dimension(3,3) :: &
   Lp

 select case (phase_thermal(material_phase(ipc,ip,el)))
   case (THERMAL_conduction_ID)
     call thermal_conduction_microstructure(Tstar_v, Lp, ipc, ip, el)
 end select

end subroutine constitutive_thermal_microstructure


!--------------------------------------------------------------------------------------------------
!> @brief contains the constitutive equation for calculating the rate of change of microstructure 
!--------------------------------------------------------------------------------------------------
subroutine constitutive_thermal_collectDotState(Tstar_v, Lp, ipc, ip, el)
 use material, only: &
   material_phase, &
   phase_thermal, &
   THERMAL_adiabatic_ID
! use thermal_conduction, only: &
!   thermal_adiabatic_microstructure

 implicit none
 integer(pInt), intent(in) :: &
   ipc, &                                                                                           !< grain number
   ip, &                                                                                            !< integration point number
   el                                                                                               !< element number
 real(pReal),  intent(in), dimension(6) :: &
   Tstar_v                                                                                          !< 2nd Piola Kirchhoff stress tensor (Mandel)
 real(pReal),  intent(in), dimension(3,3) :: &
   Lp
 
 select case (phase_thermal(material_phase(ipc,ip,el)))
   case (THERMAL_adiabatic_ID)
!     call thermal_adiabatic_dotState(Tstar_v, Lp, ipc, ip, el)
 end select

end subroutine constitutive_thermal_collectDotState

!--------------------------------------------------------------------------------------------------
!> @brief for constitutive models having an instantaneous change of state (so far, only nonlocal)
!> will return false if delta state is not needed/supported by the constitutive model
!--------------------------------------------------------------------------------------------------
logical function constitutive_thermal_collectDeltaState(ipc, ip, el)
 use material, only: &
   material_phase, &
   phase_thermal
 
 implicit none
 integer(pInt), intent(in) :: &
   ipc, &                                                                                           !< grain number
   ip, &                                                                                            !< integration point number
   el                                                                                               !< element number

 select case (phase_thermal(material_phase(ipc,ip,el)))

 end select

end function constitutive_thermal_collectDeltaState


!--------------------------------------------------------------------------------------------------
!> @brief returns array of constitutive results
!--------------------------------------------------------------------------------------------------
function constitutive_thermal_postResults(ipc, ip, el)
 use material, only: &
   material_phase, &
   phase_thermal, &
   THERMAL_conduction_ID
 use thermal_conduction, only:  &
   thermal_conduction_postResults

 implicit none
 integer(pInt), intent(in) :: &
   ipc, &                                                                                           !< grain number
   ip, &                                                                                            !< integration point number
   el                                                                                               !< element number
 real(pReal), dimension(constitutive_thermal_sizePostResults(ipc,ip,el)) :: &
   constitutive_thermal_postResults

 constitutive_thermal_postResults = 0.0_pReal
 
 select case (phase_thermal(material_phase(ipc,ip,el)))
   case (THERMAL_conduction_ID)
     constitutive_thermal_postResults = thermal_conduction_postResults(ipc,ip,el)
 end select
  
end function constitutive_thermal_postResults


end module constitutive_thermal