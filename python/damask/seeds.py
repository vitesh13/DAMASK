from scipy import spatial as _spatial
import numpy as _np

from . import util
from . import grid_filters


def from_random(size,N_seeds,grid=None,seed=None):
    """
    Random seeding in space.

    Parameters
    ----------
    size : numpy.ndarray of shape (3)
        Physical size of the seeding domain.
    N_seeds : int
        Number of seeds.
    grid : numpy.ndarray of shape (3), optional.
        If given, ensures that all seeds initiate one grain if using a
        standard Voronoi tessellation.
    seed : {None, int, array_like[ints], SeedSequence, BitGenerator, Generator}, optional
        A seed to initialize the BitGenerator. Defaults to None.
        If None, then fresh, unpredictable entropy will be pulled from the OS.

    """
    rng = _np.random.default_rng(seed)
    if grid is None:
        coords = rng.random((N_seeds,3)) * size
    else:
        grid_coords = grid_filters.cell_coord0(grid,size).reshape(-1,3,order='F')
        coords = grid_coords[rng.choice(_np.prod(grid),N_seeds, replace=False)] \
               + _np.broadcast_to(size/grid,(N_seeds,3))*(rng.random((N_seeds,3))*.5-.25)           # wobble without leaving grid

    return coords


def from_Poisson_disc(size,N_seeds,N_candidates,distance,periodic=True,seed=None):
    """
    Seeding in space according to a Poisson disc distribution.

    Parameters
    ----------
    size : numpy.ndarray of shape (3)
        Physical size of the seeding domain.
    N_seeds : int
        Number of seeds.
    N_candidates : int
        Number of candidates to consider for finding best candidate.
    distance : float
        Minimum acceptable distance to other seeds.
    periodic : boolean, optional
        Calculate minimum distance for periodically repeated grid.
    seed : {None, int, array_like[ints], SeedSequence, BitGenerator, Generator}, optional
        A seed to initialize the BitGenerator. Defaults to None.
        If None, then fresh, unpredictable entropy will be pulled from the OS.

    """
    rng = _np.random.default_rng(seed)
    coords = _np.empty((N_seeds,3))
    coords[0] = rng.random(3) * size

    i = 1
    progress = util._ProgressBar(N_seeds+1,'',50)
    while i < N_seeds:
        candidates = rng.random((N_candidates,3))*_np.broadcast_to(size,(N_candidates,3))
        tree = _spatial.cKDTree(coords[:i],boxsize=size) if periodic else \
               _spatial.cKDTree(coords[:i])
        distances, dev_null = tree.query(candidates)
        best = distances.argmax()
        if distances[best] > distance:                                                              # require minimum separation
            coords[i] = candidates[best]                                                            # maximum separation to existing point cloud
            i += 1
            progress.update(i)

    return coords


def from_geom(geom,selection=None,invert=False,average=False,periodic=True):
    """
    Create seed from existing geometry description.

    Parameters
    ----------
    geom : damask.Geom
        Geometry, from which the material IDs are used as seeds.
    selection : iterable of integers, optional
        Material IDs to consider.
    invert : boolean, false
        Do not consider the material IDs given in selection. Defaults to False.
    average : boolean, optional
        Seed corresponds to center of gravity of material ID cloud.
    periodic : boolean, optional
        Center of gravity with periodic boundaries.

    """
    material = geom.material.reshape((-1,1),order='F')
    mask = _np.full(geom.grid.prod(),True,dtype=bool) if selection is None else \
           _np.isin(material,selection,invert=invert).flatten()
    coords = grid_filters.cell_coord0(geom.grid,geom.size).reshape(-1,3,order='F')

    if not average:
        return (coords[mask],material[mask])
    else:
        materials = _np.unique(material[mask])
        coords_ = _np.zeros((materials.size,3),dtype=float)
        for i,mat in enumerate(materials):
            pc = (2*_np.pi*coords[material[:,0]==mat,:]-geom.origin)/geom.size
            coords_[i] = geom.origin + geom.size / 2 / _np.pi * (_np.pi +
                         _np.arctan2(-_np.average(_np.sin(pc),axis=0),
                                     -_np.average(_np.cos(pc),axis=0))) \
                         if periodic else \
                         _np.average(coords[material[:,0]==mat,:],axis=0)
        return (coords_,materials)
