"""
This module defines an Enum class to determine visualization and wiedget functionality 
for NumPy data ingested for this toolkit.

These labels should be used in defining data in a dictionary in the file reading process.

Then is later used when layers are added to the tool in the create_tool() call.
"""
from enum import Enum


class LayerType(Enum):
    """
    Class LayerType is an enum to indicate what the use case is for ingested data during the instrument
    data ingestment pipeline, such that this should be used to define data layer types... Then, during
    the creation of the tool and visualization, these enum types will be used to determine how to add
    the data layers to the tool and what extra functionality can be used for them.

    Type (Enum) Definitions and Functionality:
        GRAY_BAND       : A single band's radiance or reflectance values. This will be added as imagery
                        so that users can look at specific pixel values and filter imagery based on
                        min/max values.
        CLOUD_MASK      : A cloud mask to indicated clouds vs clear-sky. This layer can be added as a
                        a non-editable layer, or loaded as a starting point for an editable layer.
        NAN_MASK        : A mask indicating when NaN values are detected for pixels. This will always be
                        added as a non-editable layer.
        MANUAL_LABELS   : A layer loaded with prior labels created by a user, such as CLOUD_MASK labels.
                        This layer may be added as a editable or non-editable layer... or both.
        DTT             : "Distance to Threshold" (DTT) metric that is used within the MAIA cloud detection
                        algorithm. This metric describes how for away an observable is from the threshold
                        found within the decision tree. This will be added as an image layer and can be
                        connected to DTT widgets to addjust threshold value cut-offs.
        OBSERVABLE      : An observable used within a cloud detection algorithm. Can be added to the tool
                        as an image and can be connect to DTT widget functionality, or threshold widget
                        functionality.
        THRESHOLDS      : Layers that are created from manual threshold operations. See ThresholdPanel.py
                        for more details on how users can create threshold label layers.
        COMBINED        : Layers that have been created by joining two other label layers from the napari
                        viewer. These joined operations are defined by logic gate operations, for more
                        details, see LogicGatesPanel.py.
        SURFACE_ID      : A classifier stating the underlying surface type. Would be added as labels to
                        the tool that are not-editable. Note that the colormap loaded by the toolkit for
                        surfave ids should have sufficient colors for the # of ids loaded.
        VIEW_GEO        : Viewing Geometery (i.e., Viewing Zentih Angle, Solar Zenith Angle, etc.). Can
                        be added as a image layer. No other functionality yet.
    """
    MANUAL_LABELS = "Editing Labels"
    GRAY_BAND = "Band Data"
    RGB = "RGB"
    CLOUD_MASK = "Cloud Mask(s)"
    NAN_MASK = "NaN Values"
    DTT = "Distance to Thresholds"
    OBSERVABLE = "Observables"
    THRESHOLDS = "Thresholds"
    COMBINED = "Combined Labels"
    SURFACE_ID = "Surface Ids"
    VIEW_GEO = "Viewing Geometery"
    LAT_LON = "Latitude/Longitude"
