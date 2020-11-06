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

#include <cmath>
#include <iostream>
#include "lsst/geom/SpherePoint.h"
#include "lsst/jointcal/ProperMotion.h"
#include "lsst/jointcal/MeasuredStar.h"

namespace lsst {
namespace jointcal {

std::shared_ptr<FittedStar> ProperMotion::apply(std::shared_ptr<FittedStar> star,
                                                double timeDeltaYears) const {
    std::cout << "HERE!!!!!!!!!!!!:   " << star->x << " " << star->y << std::endl;
    geom::SpherePoint spherePoint(star->x, star->y, geom::degrees);
    std::cout << "now here" << std::endl;
    double amount = std::hypot(_ra * timeDeltaYears, _dec * timeDeltaYears);
    std::cout << "hypot " << amount << std::endl;
    auto result = spherePoint.offset(_offsetBearing * geom::radians, amount * geom::radians);
    auto newStar = std::make_shared<MeasuredStar>(*star);
    std::cout << "%%%%%%%%%%%%%%%%%%%%%%" << std::endl;
    std::cout << spherePoint << " " << result << std::endl;
    std::cout << "RA: " << result.getRa().asDegrees() << std::endl;
    newStar->x = result.getRa().asDegrees();
    newStar->y = result.getDec().asDegrees();
    return newStar;
}

}  // namespace jointcal
}  // namespace lsst
