#
# Copyright (C) 2014-2018 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

import unittest
import numpy as np
from openquake.hazardlib.imt import PGA, SA
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
from openquake.hazardlib.gsim.can15.western import (get_sigma,
                                                    WesternCan15Mid,
                                                    WesternCan15Low,
                                                    WesternCan15Upp)


class WesternRuptureDimensionTestCase(unittest.TestCase):
    """
    This class tests the calculation of sigma values for the GMPEs included
    in the NRCan15 model
    """

    def test_get_sigma_pga(self):
        """ Test the calculation of sigma for short periods"""
        imt = PGA()
        computed = get_sigma(imt)
        expected = 0.23
        np.testing.assert_almost_equal(computed, expected)

    def test_get_sigma_sa0(self):
        """ Test the calculation of sigma for short periods"""
        imt = SA(0.6)
        computed = get_sigma(imt)
        expected = 0.25
        np.testing.assert_almost_equal(computed, expected)
        #
        imt = SA(0.4)
        computed = get_sigma(imt)
        expected = 0.24
        np.testing.assert_almost_equal(computed, expected)
        #
        imt = SA(1.2)
        computed = get_sigma(imt)
        expected = 0.27
        np.testing.assert_almost_equal(computed, expected)


class WesternCan15MidTestCase(BaseGSIMTestCase):
    GSIM_CLASS = WesternCan15Mid

    def test_mean(self):
        self.check('CAN15/GMPEt_Wcrust_med.csv',
                   max_discrep_percentage=0.4)
    """
    def test_std_total(self):
        self.check('SILVA02/SILVA02MblgAB1987NSHMP_STD_TOTAL.csv',
                   max_discrep_percentage=0.1)
    """

