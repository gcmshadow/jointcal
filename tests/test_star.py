# This file is part of jointcal.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import astropy.units as u
import astropy.time
from astropy.coordinates import SkyCoord

import unittest
import lsst.utils.tests

import lsst.jointcal.star


class TestProperMotion(lsst.utils.tests.TestCase):
    def setUp(self):
        self.ra = 10 * u.degree
        self.dec = 20 * u.degree
        self.pm_ra = 30 * u.mas / u.yr  # ra*cos(dec)
        self.pm_dec = 40 * u.mas / u.yr
        flux = 10
        self.epoch1 = astropy.time.Time("2000-01-01 00:00:05", scale="tai")
        self.epoch2 = astropy.time.Time("2010-01-01 00:00:05", scale="tai")
        self.dt = (self.epoch2.tai - self.epoch1.tai).to(astropy.units.yr)
        self.coord = SkyCoord(self.ra, self.dec, frame="icrs",
                              pm_ra_cosdec=self.pm_ra, pm_dec=self.pm_dec,
                              obstime=self.epoch1, distance=10000*u.pc)
        self.refStar = lsst.jointcal.star.RefStar(self.ra.value, self.dec.value,
                                                  flux, flux*0.001)
        self.measuredStar = lsst.jointcal.star.MeasuredStar(self.refStar)
        self.measuredStar.vx = self.ra.to_value(u.degree) * 0.01
        self.measuredStar.vy = self.dec.to_value(u.degree) * 0.01
        self.properMotion = lsst.jointcal.star.ProperMotion(self.pm_ra.to_value(u.radian/u.yr),
                                                            self.pm_dec.to_value(u.radian/u.yr),
                                                            self.pm_ra.to_value(u.radian/u.yr)*0.01,
                                                            self.pm_dec.to_value(u.radian/u.yr)*0.01)

    def test_apply_no_proper_motion(self):
        """If refCat as no ProperMotion set, applyProperMotion() should change
        nothing.
        """
        result = self.refStar.applyProperMotion(self.measuredStar, self.dt.value)
        self.assertEqual(result.x, self.measuredStar.x)
        self.assertEqual(result.y, self.measuredStar.y)
        # TODO? astropy SkyCoord does not include coordinate errors, or error propogation.
        # How do I test it?
        # self.assertEqual(result.vx, self.measuredStar.vx)
        # self.assertEqual(result.vy, self.measuredStar.vy)

    def test_apply(self):
        expect = self.coord.apply_space_motion(dt=self.dt)

        self.refStar.setProperMotion(self.properMotion)
        result = self.refStar.applyProperMotion(self.measuredStar, self.dt.value)
        # original star should not be changed:
        self.assertEqual(self.ra.to_value(u.degree), self.measuredStar.x)
        self.assertEqual(self.dec.to_value(u.degree), self.measuredStar.y)
        self.assertEqual(self.ra.to_value(u.degree)*0.01, self.measuredStar.vx)
        self.assertEqual(self.dec.to_value(u.degree)*0.01, self.measuredStar.vy)
        print("")
        print("ref:", self.refStar)
        print("meas:", self.measuredStar)
        print("coord:", self.coord)
        print("PM:", self.properMotion)
        print("expect:", expect)
        print("result:", result)

        self.assertEqual(result.x, expect.ra.to_value(u.degree))
        self.assertEqual(result.y, expect.dec.to_value(u.degree))
        # TODO? astropy SkyCoord does not include coordinate errors, or error propogation.
        # How do I test it?
        # self.assertEqual(result.vx, expect.vx)
        # self.assertEqual(result.vy, expect.vy)


class MemoryTester(lsst.utils.tests.MemoryTestCase):
    pass


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()
