from enum import Enum


class LayerType(Enum):
    """
    Class LayerType is an enum to indicate what the use case is for ingested data during the instrument
    data ingestment pipeline, such that this should be used to define data layer types... Then, during
    the creation of the tool and visualization, these enum types will be used to determine how to add
    the data layers to the tool and what extra functionality can be used for them.

    Type (Enum) Definitions and Functionality:
        GRAY_BAND       : A single band's radiance or reflectance values. This will be added as imagery
            so that users can look at specific pixel values and filter imagery based on min/max values.
        CLOUD_MASK      : A cloud mask to indicated clouds vs clear-sky. This layer can be added as a
            a non-editable layer, or loaded as a starting point for an editable layer.
        NAN_MASK        : A mask indicating when NaN values are detected for pixels. This will always be
            added as a non-editable layer.
        MANUAL_LABELS   : A layer loaded with prior labels created by a user, such as CLOUD_MASK labels.
            This layer may be added as a editable or non-editable layer... or both.
    """
    GRAY_BAND = 1
    CLOUD_MASK = 2
    NAN_MASK = 3
    MANUAL_LABELS = 4
    DTT = 5
    OBSERVABLE = 6
    SURFACE_ID = 7
    SZA = 8
    VZA = 9
