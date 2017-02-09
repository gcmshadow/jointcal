// -*- C++ -*-
#ifndef MEASUREDSTAR__H
#define MEASUREDSTAR__H

#include <iostream>

#include "lsst/jointcal/BaseStar.h"
#include "lsst/jointcal/FittedStar.h"
#include "lsst/jointcal/StarList.h"

namespace lsst {
namespace jointcal {



class CcdImage;

//! objects measured on actual images. Coordinates and uncertainties are expressed in pixel image frame. Flux expressed in ADU/s.
class MeasuredStar : public BaseStar
{
  public :
  double mag;
  double wmag;
  double eflux;
  double aperrad;
  double chi2;
  const CcdImage *ccdImage;

  private :

    CountedRef<const FittedStar> fittedStar;
    bool   valid;



  public :

    //!
  MeasuredStar()
    : BaseStar(),
      mag(0.), wmag(0.), eflux(0.), aperrad(0.),
      ccdImage(0),
      valid(true) {}

  MeasuredStar(const BaseStar &B, const FittedStar *F = nullptr) :
    BaseStar(B),
    mag(0.), wmag(0.), eflux(0.), aperrad(0.),
    ccdImage(0),
    valid(true) {}

  void SetFittedStar(FittedStar *F)
      { if (F)  F->MeasurementCount()++; fittedStar = F;
      }

  double FluxSig() const { return eflux;}

  double Mag() const { return mag;}
  double AperRad() const { return aperrad; }

  //! the inverse of the mag variance
  double MagWeight() const { return (flux*flux/(eflux*eflux));}

  const FittedStar* GetFittedStar() const { return fittedStar.get();};

  const CcdImage &GetCcdImage()  const { return *ccdImage;};

  void setCcdImage(const CcdImage *C) { ccdImage = C;};

  //! Fits may use that to discard outliers
  bool  IsValid() const { return valid; }
  //! Fits may use that to discard outliers
  void  SetValid(bool v) { valid=v; }

  // No longer decrement counter of associated fitted star in destructor (P. El-Hage le 10/04/2012)
  // ~MeasuredStar() { if (fittedStar) fittedStar->MeasurementCount()--;}

  std::string WriteHeader_(std::ostream & pr = std::cout, const char* i = nullptr) const;
  void writen(std::ostream& s) const;
static BaseStar*  read(std::istream &s, const char* format);
};


typedef CountedRef<MeasuredStar> MeasuredStarRef;


/****** MeasuredStarList */

//! A list of MeasuredStar. They are usually filled in Associations::AddImage
class MeasuredStarList : public StarList<MeasuredStar> {

  public :
    MeasuredStarList() {};

  void setCcdImage(const CcdImage *C);
};

typedef MeasuredStarList::const_iterator MeasuredStarCIterator;
typedef MeasuredStarList::iterator MeasuredStarIterator;
typedef CountedRef<MeasuredStar> MeasuredStarRef;

BaseStarList& Measured2Base(MeasuredStarList &This);
BaseStarList* Measured2Base(MeasuredStarList *This);
const BaseStarList& Measured2Base(const MeasuredStarList &This);
const BaseStarList* Measured2Base(const MeasuredStarList *This);

}}  // end of namespaces

#endif /* MEASUREDSTAR__H */

