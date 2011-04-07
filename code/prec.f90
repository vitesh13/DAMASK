! Copyright 2011 Max-Planck-Institut für Eisenforschung GmbH
!
! This file is part of DAMASK,
! the Düsseldorf Advanced MAterial Simulation Kit.
!
! DAMASK is free software: you can redistribute it and/or modify
! it under the terms of the GNU General Public License as published by
! the Free Software Foundation, either version 3 of the License, or
! (at your option) any later version.
!
! DAMASK is distributed in the hope that it will be useful,
! but WITHOUT ANY WARRANTY; without even the implied warranty of
! MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
! GNU General Public License for more details.
!
! You should have received a copy of the GNU General Public License
! along with DAMASK. If not, see <http://www.gnu.org/licenses/>.
!
!##############################################################
!* $Id$
!##############################################################
 MODULE prec
!##############################################################

implicit none
 
!    *** Precision of real and integer variables ***
integer, parameter :: pReal = selected_real_kind(15,300)     ! 15 significant digits, up to 1e+-300
integer, parameter :: pInt  = selected_int_kind(9)           ! up to +- 1e9
integer, parameter :: pLongInt  = 8                          ! should be 64bit
real(pReal), parameter :: tol_math_check = 1.0e-8_pReal
real(pReal), parameter :: tol_gravityNodePos = 1.0e-100_pReal
 
type :: p_vec
  real(pReal), dimension(:), pointer :: p
end type p_vec

CONTAINS

subroutine prec_init
implicit none

!$OMP CRITICAL (write2out)
  write(6,*)
  write(6,*) '<<<+-  prec init  -+>>>'
  write(6,*) '$Id$'
  write(6,*)
!$OMP END CRITICAL (write2out)

end subroutine

END MODULE prec
