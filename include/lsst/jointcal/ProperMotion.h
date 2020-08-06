// -*- LSST-C++ -*-
/*
 * This file is part of jointcal.
 *
 * Developed for the LSST Data Management System.
 * This product includes software developed by the LSST Project
 * (https://www.lsst.org).
 * See the COPYRIGHT file at the top-level directory of this distribution
 * for details of code ownership.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */

#ifndef LSST_JOINTCAL_PROPER_MOTION_H
#define LSST_JOINTCAL_PROPER_MOTION_H

#include <math.h>

#include "lsst/jointcal/FatPoint.h"

namespace lsst {
namespace jointcal {

/**
 * Proper motion data for a reference star or fitted star.
 *
 * Whether to just use these values or fit them is determined by the RefStar and FittedStar they belong to.
 * Similarly,
 */
class ProperMotion {
public:
    ProperMotion(double ra, double dec, double raErr, double decErr, double raDecCov = 0)
            : _ra(ra), _dec(dec), _raErr(raErr), _decErr(decErr), _raDecCov(raDecCov) {
        _offsetBearing = atan2(dec, ra);
    };

    // No copy or move: PM data is stored as shared_ptr, and is immutable.
    // PM data is stored as unique_ptr, and we need to move when assigning
    ProperMotion(ProperMotion const &) = delete;
    ProperMotion(ProperMotion &&) = delete;
    ProperMotion &operator=(ProperMotion const &) = delete;
    ProperMotion &operator=(ProperMotion &&) = delete;
    ~ProperMotion() = default;

    /**
     * Apply proper motion correction to the input star, returning a star with PM-corrected coordinates and
     * coordinate errors.
     *
     * @param star The star to correct for this proper motion.
     * @param timeDeltaYears The difference in time from the correction epoch to correct for, in years.
     *
     * @return The star with corrected coordinates.
     */
    FatPoint &apply(FatPoint &star, double timeDeltaYears);

    // double getRa() { return _ra; }
    // double getDec() { return _dec; }

private:
    // Proper motion in ra and dec. Units are mas/year
    double _ra, _dec;
    double _raErr, _decErr, _raDecCov;

    // Cache the bearing along-which to offset.
    double _offsetBearing;
};
}  // namespace jointcal
}  // namespace lsst

#endif  // LSST_JOINTCAL_PROPER_MOTION_H
