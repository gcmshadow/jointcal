from __future__ import division, absolute_import
#
# LSST Data Management System
# Copyright 2008, 2009, 2010, 2011, 2012 LSST Corporation.
#
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the LSST License Statement and
# the GNU General Public License along with this program.  If not,
# see <http://www.lsstcorp.org/LegalNotices/>.
#

import os
import numpy as np

import lsst.utils
import lsst.pex.config as pexConfig
#useful ?
import lsst.coadd.utils as coaddUtils
import lsst.pipe.base as pipeBase
import lsst.afw.image as afwImage
import lsst.afw.table as afwTable
import lsst.afw.geom as afwGeom
import lsst.afw.coord as afwCoord
import lsst.pex.exceptions as pexExceptions

#from lsst.afw.fits import FitsError
#from lsst.pipe.tasks.selectImages import WcsSelectImagesTask, SelectStruct
#from lsst.coadd.utils import CoaddDataIdContainer
#from lsst.pipe.tasks.getRepositoryData import DataRefListRunner
#from lsst.meas.astrom.loadAstrometryNetObjects import LoadAstrometryNetObjectsTask
#from lsst.meas.astrom import AstrometryNetDataConfig

#from .dataIds import PerTractCcdDataIdContainer

from lsst.jointcal.jointcalLib import JointcalControl, ExposureCatalog, PolyMappingArrangement, ChipArrangement, MatchExposure, Point

__all__ = ["MatchExposureConfig", "MatchExposureTask"]

class MatchExposureRunner(pipeBase.TaskRunner):
    """Subclass of TaskRunner for MatchExposureTask (copied from the HSC MosaicRunner)

    MatchExposureTask.run() takes a number of arguments, one of which is a list of dataRefs
    extracted from the command line (whereas most CmdLineTasks' run methods take
    single dataRef, are are called repeatedly).  This class transforms the processed
    arguments generated by the ArgumentParser into the arguments expected by
    MosaicTask.run().

    See pipeBase.TaskRunner for more information, but note that the multiprocessing
    code path does not apply, because MosaicTask.canMultiprocess == False.
    """

    @staticmethod
    def getTargetList(parsedCmd, **kwargs):
        return [(parsedCmd.id.refList, 0)]
        # organize data IDs by tract
        refListDict = {}
        for ref in parsedCmd.id.refList:
            refListDict.setdefault(ref.dataId["tract"], []).append(ref)
        # we call run() once with each tract
        return [(refListDict[tract],
                 tract
                 ) for tract in sorted(refListDict.keys())]

    def __call__(self, args):
        task = self.TaskClass(config=self.config, log=self.log)
        result = task.run(*args)

from lsst.pex.config import wrap
# with this decorator, MatchExposureConfig also contains JointcalControl
@wrap(JointcalControl)
class MatchExposureConfig(pexConfig.Config):
    """Config for JointcalTask
    """

# Keep this config parameter as a place holder
    doWrite = pexConfig.Field(
        doc = "persist SimAstrom output...",
        dtype = bool,
        default = True,
    )
    polyOrder = pexConfig.Field(
        doc = "Polynomial order for fitting distorsion",
        dtype = int,
        default = 3,
    )
    sourceFluxField = pexConfig.Field(
        doc = "Type of source flux",
        dtype = str,
        default = "base_CircularApertureFlux_17_0",   # base_CircularApertureFlux_17_0 in recent stack version 
    )
    maxMag = pexConfig.Field(
        doc = "Maximum magnitude for sources to be included in the fit",
        dtype = float,
        default = 22.5, 
    )
    coaddName = pexConfig.Field(
        doc = "Mandatory for getSkymap",
        dtype = str,
        default = "deep",
    ) 
    centroid = pexConfig.Field(
        doc = "Centroid type for position estimation",
        dtype = str,
        default = "base_SdssCentroid", 
    )
    shape = pexConfig.Field(
        doc = "Shape for error estimation",
        dtype = str,
        default = "base_SdssShape", 
    )

class MatchExposureTask(pipeBase.CmdLineTask):
 
    ConfigClass = MatchExposureConfig
    RunnerClass = MatchExposureRunner
    _DefaultName = "matchExposure"
    
    def __init__(self, *args, **kwargs):
        pipeBase.Task.__init__(self, *args, **kwargs)
#        self.makeSubtask("select")

# We don't need to persist config and metadata at this stage. In this way, we don't need to put a specific entry in the
# camera mapper policy file
    def _getConfigName(self):
        return None
        
    def _getMetadataName(self):
        return None
        
    @classmethod
    def _makeArgumentParser(cls):
        """Create an argument parser
        """
        parser = pipeBase.ArgumentParser(name=cls._DefaultName)

        parser.add_id_argument("--id", "calexp", help="data ID, e.g. --selectId visit=6789 ccd=0..9")
#                                ContainerClass=PerTractCcdDataIdContainer)

        return parser

    @pipeBase.timeMethod
    def run(self, ref, tract):
        
        configSel = StarSelectorConfig()
        # by default, we prefer having saturated sources for the 
        # combinatorial match. They should be ignored later when fitting.
        # try w/o flags
        configSel.badFlags = []
        ss = StarSelector(configSel, self.config.sourceFluxField, self.config.maxMag,self.config.centroid,self.config.shape)
                
        print self.config.sourceFluxField,self.config.shape
        # The C++ SimAstromControl:
        astromControl = self.config.makeControl()

        # The file path has to come from the butler presumably. 
        # For the time being:
        chipArrangement = PolyMappingArrangement("my_arrangement.txt")
        expCat = ExposureCatalog(chipArrangement)
        tangentPoint = Point(-1,0)
        
        for dataRef in ref :
            
            print dataRef.dataId
            
            src = dataRef.get("src", immediate=True, flags=afwTable.SOURCE_IO_NO_FOOTPRINTS)
            # pick a tangent point in the first image
            if tangentPoint.x ==-1. :
                md = dataRef.get("calexp_md", immediate=True)
                ra = md.get("RA")
                ra = afwGeom.radToDeg(float(afwCoord.hmsStringToAngle(ra)))
                dec = md.get("DEC")
                dec = afwGeom.radToDeg(float(afwCoord.dmsStringToAngle(dec)))

#                tanwcs = afwImage.TanWcs.cast(afwImage.makeWcs(md))
#                tp = tanwcs.getSkyOrigin().getPosition()
#                tangentPoint.x ,tangentPoint.y  = tp[0], tp[1]
                tangentPoint.x ,tangentPoint.y  = ra, dec
                print "assumed tangent point ra=%f dec=%f"%(tangentPoint.x, tangentPoint.y)

            newSrc = ss.select(src, None)
            if len(newSrc) == 0 :
                print "no source selected in ", dataRef.dataId["visit"], dataRef.dataId["ccd"]
                continue
            print "%d sources selected in visit %d - ccd %d (out of %d)"%(len(newSrc), dataRef.dataId["visit"], dataRef.dataId["ccd"], len(src))
            
            expCat.AddCalexp(newSrc, dataRef.dataId['ccd'], astromControl.sourceFluxField)


        sol = MatchExposure(expCat, tangentPoint, astromControl)
        # code to write WCS's here


class StarSelectorConfig(pexConfig.Config):
    
    badFlags = pexConfig.ListField(
        doc = "List of flags which cause a source to be rejected as bad",
        dtype = str,
        default = [ "base_PixelFlags_flag_saturated", 
                    "base_PixelFlags_flag_cr",
                    "base_PixelFlags_flag_interpolated",
                    "base_SdssCentroid_flag",
                    "base_SdssShape_flag"],
    )

class StarSelector(object) :
    
    ConfigClass = StarSelectorConfig

    def __init__(self, config, sourceFluxField, maxMag,centroid,shape):
        """Construct a star selector
        
        @param[in] config: An instance of StarSelectorConfig
        """
        self.config = config
        self.sourceFluxField = sourceFluxField
        self.maxMag = maxMag
        self.centroid=centroid
        self.shape=shape
    
    def select(self, srcCat, calib):
# Return a catalog containing only reasonnable stars / galaxies
# DEBUG for timing:
        schema = srcCat.getSchema()
        #print schema.getOrderedNames()
        fluxKey = schema[self.sourceFluxField+"_flux"].asKey()
        fluxErrKey = schema[self.sourceFluxField+"_fluxSigma"].asKey()
        parentKey = schema["parent"].asKey()
        cuts = []
# these flags discard essentially all useful sources ?!
        if False :
            for f in self.config.badFlags :
                key = schema[f].asKey()
                cuts.append(srcCat.get(key))
            fluxFlagKey = schema[self.sourceFluxField+"_flag"].asKey()
            cuts.append(srcCat.get(fluxFlagKey))
        # grab fluxes
        fluxes = srcCat.get(fluxKey)
        # negative fluxes
        cuts.append(fluxes>0)
        # S/N : 
        snCut = 20 # should be an argument
        cuts.append(fluxes/srcCat.get(fluxErrKey)> snCut)
        # finite sizes
        cuts.append(np.isfinite(srcCat.get(self.centroid + "_xSigma")))
        cuts.append(np.isfinite(srcCat.get(self.centroid + "_ySigma")))
        # apply cuts: 
        mask = np.logical_and.reduce(cuts)
        return srcCat[mask]
        # DEBUG
        flagKeys = []
        for src in srcCat :
            # Do not consider sources with bad flags
            rej = 0
            for f in flagKeys :
                rej = 0
                if src.get(f) :
                    rej = 1
                    break
            if rej == 1 :
                continue
            # Reject negative flux
            flux = src.get(fluxKey)
            if flux < 0 :
                continue
            fluxErr = src.get(fluxErrKey)
            # S/N cut (cut should be in config....)
            if flux/fluxErr < 20 :
                continue
            if calib != None:
                mag, magErr = calib.getMagnitude(flux, fluxErr)
                # Reject objects with too large magnitude
                if mag > self.maxMag or magErr > 0.1 :
                    continue
            # Reject blends (No: it removes most bright objects)
#            if src.get(parentKey) != 0 :
#                continue
            footprint = src.getFootprint()
            if footprint is not None and len(footprint.getPeaks()) > 1 :
                continue
            vx = np.square(src.get(self.centroid + "_xSigma"))
            vy = np.square(src.get(self.centroid + "_ySigma"))
            mxx = src.get(self.shape + "_xx")  
            myy = src.get(self.shape + "_yy")
            mxy = src.get(self.shape + "_xy") 
            vxy = mxy*(vx+vy)/(mxx+myy);

            
            if vx < 0 or vy< 0 or (vxy*vxy)>(vx*vy) or np.isnan(vx) or np.isnan(vy):
                continue
            
            newCat.append(src)
            
        return newCat
