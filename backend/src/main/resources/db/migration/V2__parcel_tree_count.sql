-- M6: result of the last tree count saved on the parcel (tree_count already exists).
ALTER TABLE parcels ADD COLUMN density_per_ha DOUBLE PRECISION;
ALTER TABLE parcels ADD COLUMN density_estimated BOOLEAN;
ALTER TABLE parcels ADD COLUMN tree_counted_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE parcels ADD COLUMN tree_count_source VARCHAR(20);
