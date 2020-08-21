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

#ifndef LSST_JOINTCAL_REF_STAR_H
#define LSST_JOINTCAL_REF_STAR_H

#include <vector>
#include <fstream>

#include "lsst/jointcal/FittedStar.h"
#include "lsst/jointcal/ProperMotion.h"
#include "lsst/jointcal/StarList.h"

namespace lsst {
namespace jointcal {

class MeasuredStar;

/**
 * Objects used as position/flux anchors (e.g. Gaia DR2 stars). Coordinate system should match that of the
 * fittedStars these are associated with; typically the common tangent plane.
 *
 * RefStars should have their proper motion and parallax corrections pre-applied, so that they are at
 * the same epoch as is stored in Associations.
 */
class RefStar : public BaseStar {
public:
    RefStar(double xx, double yy, double flux, double fluxErr)
            : BaseStar(xx, yy, flux, fluxErr), _properMotion(nullptr) {}

    /// No move or copy: each RefStar is unique, and should be accessed/managed via shared_ptr.
    RefStar(RefStar const&) = delete;
    RefStar(RefStar&&) = delete;
    RefStar& operator=(RefStar const&) = delete;
    RefStar& operator=(RefStar&&) = delete;

    // pybind11 cannot handle unique_ptr as arguments, so provide this for python-level testing.
    void setProperMotion(ProperMotion const& properMotion) {
        _properMotion = std::make_unique<ProperMotion>(properMotion);
    }
    // NOTE: we're storing a `ProperMotion const` here: is this a problem?
    void setProperMotion(std::unique_ptr<ProperMotion const>& properMotion) {
        _properMotion = std::move(properMotion);
    }

    /**
     * Apply proper motion correction to the input star, returning a star with PM-corrected coordinates and
     * coordinate errors.
     *
     * @param star The star to correct for this proper motion.
     * @param timeDeltaYears The difference in time from the correction epoch to correct for, in years.
     *
     * @return The star with corrected coordinates.
     */
    std::shared_ptr<MeasuredStar> applyProperMotion(std::shared_ptr<MeasuredStar> star,
                                                    double timeDeltaYears) const;

private:
    // RefStars are PM corrected to a common epoch: this is to correct associated MeasuredStars
    // post-association.
    // NOTE: I want this to be unique_ptr, but am having trouble with that causing
    // FittedStar to have implicitly deleted copy constructor...
    std::unique_ptr<ProperMotion const> _properMotion;
};

/****** RefStarList ***********/

// typedef StarList<RefStar> RefStarList;
class RefStarList : public StarList<RefStar> {};

typedef RefStarList::const_iterator RefStarCIterator;
typedef RefStarList::iterator RefStarIterator;

BaseStarList& Ref2Base(RefStarList& This);
BaseStarList* Ref2Base(RefStarList* This);
const BaseStarList& Ref2Base(const RefStarList& This);
const BaseStarList* Ref2Base(const RefStarList* This);
}  // namespace jointcal
}  // namespace lsst

#endif  // LSST_JOINTCAL_REF_STAR_H
