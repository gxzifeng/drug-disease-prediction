-- Initialize Sample Dataset
-- This creates a dataset record and links the existing drug-disease data

-- Insert sample dataset
INSERT INTO datasets (
    name, 
    description, 
    source, 
    original_filename, 
    file_path, 
    file_size,
    drug_count, 
    disease_count, 
    association_count, 
    positive_count, 
    negative_count,
    is_parsed, 
    created_at, 
    updated_at
) VALUES (
    'DrugBank Sample Dataset',
    'Sample drug-disease association dataset from DrugBank database containing 30 drugs and 33 diseases with 52 association records.',
    'drugbank',
    'sample_drug_disease.csv',
    '/app/uploads/sample_drug_disease.csv',
    2048,
    30,
    33,
    52,
    46,
    6,
    1,
    NOW(),
    NOW()
);

-- Get the dataset ID
SET @dataset_id = LAST_INSERT_ID();

-- Insert dataset records from existing associations
INSERT INTO dataset_records (dataset_id, drug_id, drug_name, disease_id, disease_name, label)
SELECT 
    @dataset_id,
    dda.drug_id,
    d.name as drug_name,
    dda.disease_id,
    ds.name as disease_name,
    CASE WHEN dda.association_type = 'known' THEN 1 ELSE 0 END as label
FROM drug_disease_associations dda
JOIN drugs d ON dda.drug_id = d.id
JOIN diseases ds ON dda.disease_id = ds.id;

-- Verify the data
SELECT '=== Dataset Created ===' as status;
SELECT id, name, drug_count, disease_count, association_count, is_parsed FROM datasets;
SELECT '=== Dataset Records ===' as status;
SELECT COUNT(*) as record_count FROM dataset_records WHERE dataset_id = @dataset_id;
