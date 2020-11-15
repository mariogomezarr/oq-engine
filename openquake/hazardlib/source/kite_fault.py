# The Hazard Library
# Copyright (C) 2012-2020 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
"""
Module :mod:`openquake.hazardlib.source.kite_fault` defines
:class:`KiteFaultSource`.
"""

import numpy as np
from typing import Tuple, Optional
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo.surface.base import BaseSurface
from openquake.hazardlib.source.base import ParametricSeismicSource
from openquake.hazardlib.geo.surface.kite_fault import KiteFaultSurface
from openquake.hazardlib.source.rupture import ParametricProbabilisticRupture \
    as ppr


class KiteFaultSource(ParametricSeismicSource):
    """
    Kite fault source
    """

    MODIFICATIONS = {}

    def __init__(self, source_id, name, tectonic_region_type, mfd,
                 rupture_mesh_spacing, magnitude_scaling_relationship,
                 rupture_aspect_ratio, temporal_occurrence_model,
                 # kite fault specific parameters
                 profiles, floating_x_step,
                 floating_y_step, rake):
        super().__init__(
            source_id, name, tectonic_region_type, mfd, rupture_mesh_spacing,
            magnitude_scaling_relationship, rupture_aspect_ratio,
            temporal_occurrence_model)

        # TODO add checks
        self.profiles = profiles
        self.profiles_sampling = rupture_mesh_spacing / rupture_aspect_ratio
        self.floating_x_step = floating_x_step
        self.floating_y_step = floating_y_step
        self.rake = rake

        min_mag, max_mag = self.mfd.get_min_max_mag()

    @property
    def surface(self) -> KiteFaultSurface:
        """
        :returns:
            The surface of the fault
        """
        # Get the surface of the fault
        # TODO we must automate the definition of the idl parameter
        return KiteFaultSurface.from_profiles(self.profiles,
                                              self.profiles_sampling,
                                              self.rupture_mesh_spacing,
                                              idl=False, align=False)

    # TODO
    def count_ruptures(self):
        pass

    def iter_ruptures(self):

        from openquake.hazardlib.geo import Point

        # Set magnitude scaling relationship, temporal occurrence model and
        # mesh of the fault surface
        msr = self.magnitude_scaling_relationship
        tom = self.temporal_occurrence_model
        surface = self.surface

        for mag, mag_occ_rate in self.get_annual_occurrence_rates():

            # Compute the area, length and width of the ruptures
            area = msr.get_median_area(mag=mag, rake=self.rake)
            lng, wdt = get_discrete_dimensions(area, self.rupture_mesh_spacing,
                                               self.rupture_aspect_ratio)

            # Get the number of nodes along the strike and dip
            rup_len = int(lng/self.rupture_mesh_spacing) + 1
            rup_wid = int(wdt/self.profiles_sampling) + 1

            # TODO replace
            hypocenter = Point(0, 0, 0)

            # Get the geometry of all the ruptures that the fault surface
            # accommodates
            ruptures = []
            for rup in self._get_ruptures(surface.mesh, rup_len, rup_wid):
                ruptures.append(rup)
            if len(ruptures) < 1:
                continue
            occurrence_rate = mag_occ_rate / len(ruptures)

            # Rupture generator
            for rup in ruptures:
                # TODO rup must be a surface
                rup_surf = BaseSurface(Mesh(rup[0][0], rup[0][1], rup[0][2]))
                yield ppr(mag, self.rake, self.tectonic_region_type,
                          hypocenter, rup_surf, occurrence_rate, tom)

    def _get_ruptures(self, omsh, rup_s, rup_d, f_strike=1, f_dip=1):
        """
        Returns all the ruptures admitted by a given geometry i.e. number of
        nodes along strike and dip

        :param omsh:
            A :class:`~openquake.hazardlib.geo.mesh.Mesh` instance describing
            the fault surface
        :param rup_s:
            Number of cols composing the rupture
        :param rup_d:
            Number of rows composing the rupture
        :param f_strike:
            Floating distance along strike (multiple of sampling distance)
        :param f_dip:
            Floating distance along dip (multiple of sampling distance)
        :returns:
            ADD
        """

        # When f_strike is negative, the floating distance is interpreted as
        # a fraction of the rupture length (i.e. a multiple of the sampling
        # distance)
        if f_strike < 0:
            f_strike = int(np.floor(rup_s * abs(f_strike) + 1e-5))
            if f_strike < 1:
                f_strike = 1

        # See f_strike comment above
        if f_dip < 0:
            f_dip = int(np.floor(rup_d * abs(f_dip) + 1e-5))
            if f_dip < 1:
                f_dip = 1

        # Float the rupture on the mesh describing the surface of the fault
        for i in np.arange(0, omsh.lons.shape[1] - rup_s + 1, f_strike):
            for j in np.arange(0, omsh.lons.shape[0] - rup_d + 1, f_dip):
                nel = np.size(omsh.lons[j:j + rup_d, i:i + rup_s])
                nna = np.sum(np.isfinite(omsh.lons[j:j + rup_d, i:i + rup_s]))
                prc = nna/nel*100.

                # Yield only the ruptures that do not contain NaN
                if prc > 99.99 and nna >= 4:
                    yield ((omsh.lons[j:j + rup_d, i:i + rup_s],
                            omsh.lats[j:j + rup_d, i:i + rup_s],
                            omsh.depths[j:j + rup_d, i:i + rup_s]), j, i)

    # TODO
    def get_fault_surface_area(self):
        """
        Computes the area of the
        """
        pass


def get_discrete_dimensions(area: float, sampling: float, aspr: float,
            sampling_y: Optional[float] = None) -> Tuple[float, float]:
    """
    Computes the discrete dimensions of a rupture given rupture area, sampling
    distance (along strike) and aspect ratio.

    :param area:
        The area of the rupture as obtained from a magnitude scaling
        relationship
    :param sampling:
        The sampling distance [km] along the strike
    :param aspr:
            The rupture aspect ratio [L/W]
    :param sampling_y:
        The sampling distance [km] along the dip
    :returns:
        Two lenght [km] and the width [km] of the rupture, respectively
    """

    lenghts = []
    widths = []

    # Set the sampling distance along the dip
    sampling_y = sampling if sampling_y is None else sampling_y

    # Give preference to rectangular ruptures elongated along the strike when
    # the aspect ratio is equal to 1
    if aspr % 1 < 0.01:
        aspr += 0.05

    # Computing possible length and width - length rounded up to a multiple of
    # the sampling distance along strike
    lenghts.append(np.ceil((area * aspr)**0.5/sampling)*sampling)
    widths.append(np.ceil(lenghts[-1]/aspr/sampling_y)*sampling)
    widths.append(np.floor(lenghts[-1]/aspr/sampling_y)*sampling)

    # Computing possible length and width - length rounded down to a multiple
    # of the sampling distance along strike
    lenghts.append(np.floor((area * aspr)**0.5/sampling)*sampling)
    widths.append(np.ceil(lenghts[-1]/aspr/sampling_y)*sampling)
    widths.append(np.floor(lenghts[-1]/aspr/sampling_y)*sampling)

    # Select the best combination of length and width taking into account
    # the input values of the rupture area and aspect ratio
    a = np.tile(np.array(lenghts), (1, 4)).flatten()
    b = np.tile(np.array(widths), (1, 2)).flatten()
    areas = a*b
    idx = np.argmin((abs(areas-area))**0.5 + abs(a/b-aspr)*sampling)

    assert isinstance(idx, np.int64)
    lng = a[idx]
    wdt = b[idx]

    # Check the difference between the computed and original value of the
    # rupture area
    area_error = abs(lng*wdt-area)/area

    # Check that the rupture size is compatible with the original value
    # provided. If not, we raise a Value Error
    if (abs(wdt-sampling) < 1e-10 or abs(lng-sampling) < 1e-10 and
            area_error > 0.3):
        wdt = None
        lng = None
    elif area_error > 0.25 and lng > 1e-10 and wdt > 1e-10:
        raise ValueError('Area discrepancy: ', area, lng*wdt, lng, wdt, aspr)

    return lng, wdt
