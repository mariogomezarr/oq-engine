# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2018 GEM Foundation
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

"""
Module exports :class:`MontalvaEtAl2016SInter`
               :class:`MontalvaEtAl2016SSlab`
"""

from __future__ import division

import numpy as np

from openquake.hazardlib.gsim.base import CoeffsTable
from openquake.hazardlib.imt import PGA
from openquake.hazardlib.gsim.abrahamson_2015 import (AbrahamsonEtAl2015SInter,
                                                      AbrahamsonEtAl2015SSlab)


class MontalvaEtAl2016SInter(AbrahamsonEtAl2015SInter):
    """
    Adaptation of the Abrahamson et al. (2015) BC Hydro subduction interface
    GMPE, calibrated to Chilean strong motion data.

    GMPE and related coefficients published by:
    Montalva, G., Bastias, N., Rodriguez-Marek, A. (2016), 'Ground Motion
    Prediction Equation for the Chilean Subduction Zone'. Submitted to
    Seismological Research Letters
    """
    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # extract dictionaries of coefficients specific to required
        # intensity measure type and for PGA
        C = self.COEFFS[imt]
        C_PGA = self.COEFFS[PGA()]
        dc1_pga = C_PGA["DC1"]
        # compute median pga on rock (vs30=1000), needed for site response
        # term calculation
        pga1000 = np.exp(
            self._compute_pga_rock(C_PGA, dc1_pga, sites, rup, dists))
        mean = (self._compute_magnitude_term(C, C["DC1"], rup.mag) +
                self._compute_distance_term(C, rup.mag, dists) +
                self._compute_focal_depth_term(C, rup) +
                self._compute_forearc_backarc_term(C, sites, dists) +
                self._compute_site_response_term(C, sites, pga1000))
        stddevs = self._get_stddevs(C, stddev_types, len(sites.vs30))
        return mean, stddevs

    def _compute_magnitude_term(self, C, dc1, mag):
        """
        Computes the magnitude scaling term given by equation (2)
        """
        base = C['theta1'] + (C['theta4'] * dc1)
        dmag = self.CONSTS["C1"] + dc1
        if mag > dmag:
            f_mag = (C['theta5'] * (mag - dmag)) +\
                C['theta13'] * ((10. - mag) ** 2.)

        else:
            f_mag = (C['theta4'] * (mag - dmag)) +\
                C['theta13'] * ((10. - mag) ** 2.)

        return base + f_mag

    def _compute_distance_term(self, C, mag, dists):
        """
        Computes the distance scaling term, as contained within equation (1)
        """
        return (C['theta2'] + C['theta3'] * (mag - 7.8)) *\
            np.log(dists.rrup + self.CONSTS['c4'] * np.exp((mag - 6.) *
                   self.CONSTS['theta9'])) + (C['theta6'] * dists.rrup)

    COEFFS = CoeffsTable(sa_damping=5, table="""\
    imt              DC1     vlin       b        theta1         theta2        theta3         theta4         theta5         theta6    theta7  theta8       theta10        theta11        theta12        theta13        theta14  theta15 theta16           phi           tau         sigma       phi_s2s
    pga      0.200000000    865.1  -1.186   4.935754758   -1.319716122   0.156954813   -1.038307042   -0.200134154   -0.002064757    1.0988   -1.42   4.559632568    0.004375202    0.914271114   -0.203185487   -0.694459960   0.9969   -1.00   0.676804137   0.436356919   0.805277096   0.547434071
    0.010    0.200000000    865.1  -1.186   4.935754758   -1.319716122   0.156954813   -1.038307042   -0.200134154   -0.002064757    1.0988   -1.42   4.559632568    0.004375202    0.914271114   -0.203185487   -0.694459960   0.9969   -1.00   0.676804137   0.436356919   0.805277096   0.547434071
    0.020    0.200000000    865.1  -1.186   4.963548267   -1.321501153   0.142973041   -0.925888135   -0.148739101   -0.002188725    1.0988   -1.42   4.654806348    0.004263109    0.934182754   -0.197899904   -0.710342148   0.9969   -1.00   0.683243196   0.430880779   0.807762039   0.554691749
    0.050    0.200000000   1053.5  -1.346   7.358115618   -1.825715240   0.093914961   -0.555849306    0.129797026   -0.000431630    1.2536   -1.65   5.105622455    0.005100764    1.188485184   -0.183201116   -0.737586413   1.1030   -1.18   0.671606746   0.483036109   0.827272328   0.545045472
    0.075    0.200000000   1085.7  -1.471   7.558603177   -1.810050104   0.103239851   -0.561904402    0.151637804   -0.001102941    1.4175   -1.80   4.514166186    0.005820798    1.395007124   -0.174729372   -0.615517435   1.2732   -1.36   0.697383068   0.508098624   0.862848397   0.582340972
    0.100    0.200000000   1032.5  -1.624   7.027657583   -1.633492535   0.088844200   -0.525502325    0.265136034   -0.002397453    1.3997   -1.80   3.827080246    0.004236026    1.560949356   -0.176264079   -0.487079351   1.3042   -1.36   0.722361027   0.504635520   0.881171074   0.616096154
    0.150    0.200000000    877.6  -1.931   6.049355161   -1.335645478   0.073754755   -0.567044631    0.294956394   -0.003942231    1.3582   -1.69   2.880273890    0.002951253    1.824536435   -0.193149712   -0.343522351   1.2600   -1.30   0.741411715   0.475224629   0.880641687   0.629331025
    0.200    0.200000000    748.2  -2.188   4.179750788   -0.885470585   0.065604603   -0.659648456    0.359088006   -0.005638198    1.1648   -1.49   3.257747522    0.002516425    1.976696142   -0.214467130   -0.452888442   1.2230   -1.25   0.759426634   0.429788781   0.872609425   0.637577298
    0.250    0.200000000    654.3  -2.381   3.999581211   -0.821066204   0.055367666   -0.643078011    0.352583884   -0.005484494    0.9940   -1.30   3.545595708    0.000888426    2.152539829   -0.226122818   -0.531334245   1.1600   -1.17   0.743380316   0.401651257   0.844948535   0.606641527
    0.300    0.200000000    587.1  -2.518   3.343521294   -0.678019870   0.070313635   -0.816717363    0.236089761   -0.005490803    0.8821   -1.18   3.711884196    0.001562756    2.179000482   -0.238785185   -0.601073843   1.0500   -1.06   0.750620673   0.389053205   0.845454783   0.609833032
    0.400    0.143682921    503.0  -2.657   3.342528747   -0.674981502   0.071624870   -1.123522692    0.103008688   -0.004346784    0.7046   -0.98   4.125701638   -0.001119565    2.225720730   -0.284536574   -0.702111182   0.8000   -0.78   0.741503989   0.383488689   0.834800419   0.589961066
    0.500    0.100000000    456.6  -2.669   3.714706072   -0.770820923   0.073623537   -1.330962172   -0.019664088   -0.003028097    0.5799   -0.82   4.507163580   -0.000434645    2.265272475   -0.318116722   -0.800834677   0.6620   -0.62   0.688862082   0.384159164   0.788739014   0.513251109
    0.600    0.073696559    430.3  -2.599   4.425108150   -0.939459680   0.062188731   -1.569443919   -0.014606735   -0.001675340    0.5021   -0.70   5.255072487   -0.000097416    2.200898990   -0.365330018   -0.966147926   0.5800   -0.50   0.665479640   0.394271020   0.773506812   0.486626176
    0.750    0.041503750    410.5  -2.401   4.372165283   -0.933761671   0.053771754   -1.730788918   -0.031408137   -0.001524349    0.3687   -0.54   5.074522171   -0.001350443    1.918279398   -0.401223910   -0.937019824   0.4800   -0.34   0.637244299   0.414109647   0.759978352   0.443006934
    1.000    0.000000000    400.0  -1.955   4.021211151   -0.924917589   0.054326150   -1.908027335   -0.138131804   -0.001101517    0.1746   -0.34   5.211831136   -0.002283504    1.509910061   -0.433435346   -0.964846571   0.3300   -0.14   0.611337571   0.442015583   0.754394725   0.421636418
    1.500   -0.058496250    400.0  -1.025   3.946972058   -1.002244695   0.049918773   -2.307833569   -0.412376757   -0.000261255   -0.0820   -0.05   5.561359279   -0.000996882    0.656237153   -0.502990059   -1.057548381   0.3100    0.00   0.617840247   0.436708751   0.756598377   0.448028967
    2.000   -0.100000000    400.0  -0.299   3.763370770   -1.048406811   0.049945027   -2.218316295   -0.488347011   -0.000156404   -0.2821    0.12   5.310311721   -0.000289011   -0.148288073   -0.501824964   -1.007661553   0.3000    0.00   0.586452050   0.429957558   0.727179144   0.424207890
    2.500   -0.155033971    400.0   0.000   3.279573476   -0.991842986   0.095212751   -2.496506471   -0.770828569   -0.000738153   -0.4108    0.25   4.764778613   -0.001039535   -0.459995635   -0.517128864   -0.886704977   0.3000    0.00   0.567864698   0.442678828   0.720024208   0.416230786
    3.000   -0.200000000    400.0   0.000   3.407135085   -1.079312405   0.092359656   -2.425045547   -0.883889211   -0.000357658   -0.4466    0.30   4.800502846   -0.000395577   -0.450645670   -0.514638813   -0.901051441   0.3000    0.00   0.559253514   0.420099114   0.699462478   0.418794658
    4.000   -0.200000000    400.0   0.000   2.789669400   -1.072279505   0.148258197   -2.792416051   -1.282315047    0.000409730   -0.4344    0.30   5.011985606   -0.000308830   -0.512937685   -0.529022902   -0.939796651   0.3000    0.00   0.569097474   0.408117852   0.700308586   0.435934346
    5.000   -0.200000000    400.0   0.000   2.700791140   -1.202536653   0.172625283   -2.741020801   -1.141773134    0.001833647   -0.4368    0.30   5.457710792    0.000255165   -0.503538042   -0.504799612   -1.025705989   0.3000    0.00   0.558540211   0.387890193   0.680019095   0.418174855
    6.000   -0.200000000    400.0   0.000   2.630174552   -1.303101604   0.127044195   -1.863112205   -0.727779859    0.002185845   -0.4586    0.30   5.826483564    0.001637500   -0.497674025   -0.423978007   -1.110103433   0.3000    0.00   0.502062640   0.394614799   0.638582598   0.346222778
    7.500   -0.200000000    400.0   0.000   2.520418211   -1.399368154   0.084904399   -0.930694380   -0.212014425    0.002325451   -0.4433    0.30   6.332273436    0.001046880   -0.481585300   -0.334701563   -1.195826518   0.3000    0.00   0.482570602   0.373377912   0.610151990   0.321745366
    10.00   -0.200000000    400.0   0.000   3.266979586   -1.707902316   0.068210457   -0.967817098    0.253077379    0.004736644   -0.4828    0.30   7.382937906    0.000738462   -0.423369635   -0.347713953   -1.409670235   0.3000    0.00   0.466924628   0.376696614   0.599932452   0.300789811
    """)

    CONSTS = {
        # Period-Independent Coefficients (Table 2)
        'n': 1.18,
        'c': 1.88,
        'c4': 10.0,
        'C1': 7.8,
        'theta9': 0.4
        }


class MontalvaEtAl2016SSlab(AbrahamsonEtAl2015SSlab):
    """
    Adaptation of the Abrahamson et al. (2015) BC Hydro subduction in-slab
    GMPE, calibrated to Chilean strong motion data
    """
    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        # extract dictionaries of coefficients specific to required
        # intensity measure type and for PGA
        C = self.COEFFS[imt]
        # For inslab GMPEs the correction term is fixed at -0.3
        dc1 = -0.3
        C_PGA = self.COEFFS[PGA()]
        # compute median pga on rock (vs30=1000), needed for site response
        # term calculation
        pga1000 = np.exp(
            self._compute_pga_rock(C_PGA, dc1, sites, rup, dists))
        mean = (self._compute_magnitude_term(C, dc1, rup.mag) +
                self._compute_distance_term(C, rup.mag, dists) +
                self._compute_focal_depth_term(C, rup) +
                self._compute_forearc_backarc_term(C, sites, dists) +
                self._compute_site_response_term(C, sites, pga1000))
        stddevs = self._get_stddevs(C, stddev_types, len(sites.vs30))
        return mean, stddevs

    def _compute_magnitude_term(self, C, dc1, mag):
        """
        Computes the magnitude scaling term given by equation (2)
        corrected by a local adjustment factor
        """
        base = C['theta1'] + (C['theta4'] * dc1)
        dmag = self.CONSTS["C1"] + dc1
        if mag > dmag:
            f_mag = (C['theta5'] * (mag - dmag)) +\
                C['theta13'] * ((10. - mag) ** 2.)

        else:
            f_mag = (C['theta4'] * (mag - dmag)) +\
                C['theta13'] * ((10. - mag) ** 2.)

        return base + f_mag

    def _compute_distance_term(self, C, mag, dists):
        """
        Computes the distance scaling term, as contained within equation (1b)
        """
        return ((C['theta2'] + C['theta14'] + C['theta3'] *
                (mag - 7.8)) * np.log(dists.rhypo + self.CONSTS['c4'] *
                np.exp((mag - 6.) * self.CONSTS['theta9'])) +
                (C['theta6'] * dists.rhypo)) + C["theta10"]

    COEFFS = CoeffsTable(sa_damping=5, table="""\
    imt              DC1    vlin        b        theta1         theta2        theta3         theta4         theta5         theta6    theta7  theta8       theta10        theta11        theta12        theta13        theta14  theta15 theta16           phi           tau         sigma       phi_s2s
    pga     -0.300000000   865.1   -1.186   4.935754758   -1.319716122   0.156954813   -1.038307042   -0.200134154   -0.002064757    1.0988   -1.42   4.559632568    0.004375202    0.914271114   -0.203185487   -0.694459960   0.9969   -1.00   0.676804137   0.436356919   0.805277096   0.547434071
    0.010   -0.300000000   865.1   -1.186   4.935754758   -1.319716122   0.156954813   -1.038307042   -0.200134154   -0.002064757    1.0988   -1.42   4.559632568    0.004375202    0.914271114   -0.203185487   -0.694459960   0.9969   -1.00   0.676804137   0.436356919   0.805277096   0.547434071
    0.020   -0.300000000   865.1   -1.186   4.963548267   -1.321501153   0.142973041   -0.925888135   -0.148739101   -0.002188725    1.0988   -1.42   4.654806348    0.004263109    0.934182754   -0.197899904   -0.710342148   0.9969   -1.00   0.683243196   0.430880779   0.807762039   0.554691749
    0.050   -0.300000000  1053.5   -1.346   7.358115618   -1.825715240   0.093914961   -0.555849306    0.129797026   -0.000431630    1.2536   -1.65   5.105622455    0.005100764    1.188485184   -0.183201116   -0.737586413   1.1030   -1.18   0.671606746   0.483036109   0.827272328   0.545045472
    0.075   -0.300000000  1085.7   -1.471   7.558603177   -1.810050104   0.103239851   -0.561904402    0.151637804   -0.001102941    1.4175   -1.80   4.514166186    0.005820798    1.395007124   -0.174729372   -0.615517435   1.2732   -1.36   0.697383068   0.508098624   0.862848397   0.582340972
    0.100   -0.300000000  1032.5   -1.624   7.027657583   -1.633492535   0.088844200   -0.525502325    0.265136034   -0.002397453    1.3997   -1.80   3.827080246    0.004236026    1.560949356   -0.176264079   -0.487079351   1.3042   -1.36   0.722361027   0.504635520   0.881171074   0.616096154
    0.150   -0.300000000   877.6   -1.931   6.049355161   -1.335645478   0.073754755   -0.567044631    0.294956394   -0.003942231    1.3582   -1.69   2.880273890    0.002951253    1.824536435   -0.193149712   -0.343522351   1.2600   -1.30   0.741411715   0.475224629   0.880641687   0.629331025
    0.200   -0.300000000   748.2   -2.188   4.179750788   -0.885470585   0.065604603   -0.659648456    0.359088006   -0.005638198    1.1648   -1.49   3.257747522    0.002516425    1.976696142   -0.214467130   -0.452888442   1.2230   -1.25   0.759426634   0.429788781   0.872609425   0.637577298
    0.250   -0.300000000   654.3   -2.381   3.999581211   -0.821066204   0.055367666   -0.643078011    0.352583884   -0.005484494    0.9940   -1.30   3.545595708    0.000888426    2.152539829   -0.226122818   -0.531334245   1.1600   -1.17   0.743380316   0.401651257   0.844948535   0.606641527
    0.300   -0.300000000   587.1   -2.518   3.343521294   -0.678019870   0.070313635   -0.816717363    0.236089761   -0.005490803    0.8821   -1.18   3.711884196    0.001562756    2.179000482   -0.238785185   -0.601073843   1.0500   -1.06   0.750620673   0.389053205   0.845454783   0.609833032
    0.400   -0.300000000   503.0   -2.657   3.342528747   -0.674981502   0.071624870   -1.123522692    0.103008688   -0.004346784    0.7046   -0.98   4.125701638   -0.001119565    2.225720730   -0.284536574   -0.702111182   0.8000   -0.78   0.741503989   0.383488689   0.834800419   0.589961066
    0.500   -0.300000000   456.6   -2.669   3.714706072   -0.770820923   0.073623537   -1.330962172   -0.019664088   -0.003028097    0.5799   -0.82   4.507163580   -0.000434645    2.265272475   -0.318116722   -0.800834677   0.6620   -0.62   0.688862082   0.384159164   0.788739014   0.513251109
    0.600   -0.300000000   430.3   -2.599   4.425108150   -0.939459680   0.062188731   -1.569443919   -0.014606735   -0.001675340    0.5021   -0.70   5.255072487   -0.000097416    2.200898990   -0.365330018   -0.966147926   0.5800   -0.50   0.665479640   0.394271020   0.773506812   0.486626176
    0.750   -0.300000000   410.5   -2.401   4.372165283   -0.933761671   0.053771754   -1.730788918   -0.031408137   -0.001524349    0.3687   -0.54   5.074522171   -0.001350443    1.918279398   -0.401223910   -0.937019824   0.4800   -0.34   0.637244299   0.414109647   0.759978352   0.443006934
    1.000   -0.300000000   400.0   -1.955   4.021211151   -0.924917589   0.054326150   -1.908027335   -0.138131804   -0.001101517    0.1746   -0.34   5.211831136   -0.002283504    1.509910061   -0.433435346   -0.964846571   0.3300   -0.14   0.611337571   0.442015583   0.754394725   0.421636418
    1.500   -0.300000000   400.0   -1.025   3.946972058   -1.002244695   0.049918773   -2.307833569   -0.412376757   -0.000261255   -0.0820   -0.05   5.561359279   -0.000996882    0.656237153   -0.502990059   -1.057548381   0.3100    0.00   0.617840247   0.436708751   0.756598377   0.448028967
    2.000   -0.300000000   400.0   -0.299   3.763370770   -1.048406811   0.049945027   -2.218316295   -0.488347011   -0.000156404   -0.2821    0.12   5.310311721   -0.000289011   -0.148288073   -0.501824964   -1.007661553   0.3000    0.00   0.586452050   0.429957558   0.727179144   0.424207890
    2.500   -0.300000000   400.0    0.000   3.279573476   -0.991842986   0.095212751   -2.496506471   -0.770828569   -0.000738153   -0.4108    0.25   4.764778613   -0.001039535   -0.459995635   -0.517128864   -0.886704977   0.3000    0.00   0.567864698   0.442678828   0.720024208   0.416230786
    3.000   -0.300000000   400.0    0.000   3.407135085   -1.079312405   0.092359656   -2.425045547   -0.883889211   -0.000357658   -0.4466    0.30   4.800502846   -0.000395577   -0.450645670   -0.514638813   -0.901051441   0.3000    0.00   0.559253514   0.420099114   0.699462478   0.418794658
    4.000   -0.300000000   400.0    0.000   2.789669400   -1.072279505   0.148258197   -2.792416051   -1.282315047    0.000409730   -0.4344    0.30   5.011985606   -0.000308830   -0.512937685   -0.529022902   -0.939796651   0.3000    0.00   0.569097474   0.408117852   0.700308586   0.435934346
    5.000   -0.300000000   400.0    0.000   2.700791140   -1.202536653   0.172625283   -2.741020801   -1.141773134    0.001833647   -0.4368    0.30   5.457710792    0.000255165   -0.503538042   -0.504799612   -1.025705989   0.3000    0.00   0.558540211   0.387890193   0.680019095   0.418174855
    6.000   -0.300000000   400.0    0.000   2.630174552   -1.303101604   0.127044195   -1.863112205   -0.727779859    0.002185845   -0.4586    0.30   5.826483564    0.001637500   -0.497674025   -0.423978007   -1.110103433   0.3000    0.00   0.502062640   0.394614799   0.638582598   0.346222778
    7.500   -0.300000000   400.0    0.000   2.520418211   -1.399368154   0.084904399   -0.930694380   -0.212014425    0.002325451   -0.4433    0.30   6.332273436    0.001046880   -0.481585300   -0.334701563   -1.195826518   0.3000    0.00   0.482570602   0.373377912   0.610151990   0.321745366
    10.00   -0.300000000   400.0    0.000   3.266979586   -1.707902316   0.068210457   -0.967817098    0.253077379    0.004736644   -0.4828    0.30   7.382937906    0.000738462   -0.423369635   -0.347713953   -1.409670235   0.3000    0.00   0.466924628   0.376696614   0.599932452   0.300789811
    """)
