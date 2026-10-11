package tn.zitouna.parcel;

/** Where the parcel's tree count comes from. */
public enum TreeCountSource {
    /** M6 count saved as detected. */
    MODEL,
    /** M6 count corrected by the farmer (boxes removed or added) before saving. */
    CORRECTED,
    /** Typed in the parcel form. */
    MANUAL
}
