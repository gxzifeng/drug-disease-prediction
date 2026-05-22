-- Drug-Disease Association Prediction System - Enriched Data Import
-- Contains 30 drugs, 33 diseases, 52 associations with detailed information

-- Clear existing data
DELETE FROM drug_disease_associations;
DELETE FROM diseases;
DELETE FROM drugs;

-- ============================================================================
-- 1. DRUGS (30 drugs with type and description)
-- ============================================================================
INSERT INTO drugs (id, name, type, description) VALUES
('DB00001', 'Lepirudin', 'Anticoagulant', 'Direct thrombin inhibitor for HIT treatment'),
('DB00002', 'Cetuximab', 'Monoclonal Antibody', 'EGFR inhibitor for colorectal and head/neck cancer'),
('DB00003', 'Dornase alfa', 'Mucolytic', 'Recombinant DNase for cystic fibrosis'),
('DB00004', 'Denileukin diftitox', 'Immunotoxin', 'IL-2 fusion toxin for T-cell lymphoma'),
('DB00005', 'Etanercept', 'Fusion Protein', 'TNF-alpha inhibitor for autoimmune diseases'),
('DB00006', 'Bivalirudin', 'Anticoagulant', 'Direct thrombin inhibitor for PCI'),
('DB00007', 'Leuprolide', 'GnRH Agonist', 'Hormone therapy for prostate/breast cancer'),
('DB00008', 'Peginterferon alfa-2a', 'Interferon', 'Pegylated interferon for hepatitis B/C'),
('DB00009', 'Alteplase', 'Thrombolytic', 'tPA for MI, stroke, and PE'),
('DB00010', 'Sermorelin', 'Growth Hormone Releasing Factor', 'GHRH analog for GH deficiency'),
('DB00011', 'Interferon alfa-n1', 'Interferon', 'Natural interferon for hepatitis C'),
('DB00012', 'Darbepoetin alfa', 'Erythropoiesis Stimulating Agent', 'EPO analog for anemia in CKD'),
('DB00013', 'Urokinase', 'Thrombolytic', 'Plasminogen activator for PE'),
('DB00014', 'Goserelin', 'GnRH Agonist', 'Hormone therapy for hormone-sensitive cancers'),
('DB00015', 'Reteplase', 'Thrombolytic', 'Recombinant tPA for acute MI'),
('DB00016', 'Erythropoietin', 'Erythropoiesis Stimulating Agent', 'EPO for anemia treatment'),
('DB00017', 'Salmon calcitonin', 'Calcitonin', 'Hormone for osteoporosis and Paget disease'),
('DB00018', 'Interferon alfa-n3', 'Interferon', 'Natural interferon for genital warts'),
('DB00019', 'Pegfilgrastim', 'Colony Stimulating Factor', 'Pegylated G-CSF for neutropenia'),
('DB00020', 'Sargramostim', 'Colony Stimulating Factor', 'GM-CSF for bone marrow recovery'),
('DB00021', 'Abciximab', 'Antiplatelet', 'GP IIb/IIIa inhibitor for PCI'),
('DB00022', 'Peginterferon alfa-2b', 'Interferon', 'Pegylated interferon for hepatitis C and melanoma'),
('DB00023', 'Tenecteplase', 'Thrombolytic', 'Modified tPA for acute MI'),
('DB00024', 'Thyrotropin alfa', 'Thyroid Stimulating Hormone', 'Recombinant TSH for thyroid cancer'),
('DB00025', 'Antihemophilic factor', 'Coagulation Factor', 'Factor VIII for hemophilia A'),
('DB00026', 'Anakinra', 'Interleukin Receptor Antagonist', 'IL-1 receptor antagonist for RA'),
('DB00027', 'Gramicidin D', 'Antibiotic', 'Peptide antibiotic for topical infections'),
('DB00028', 'Interferon beta-1b', 'Interferon', 'Recombinant interferon beta for MS'),
('DB00029', 'Anistreplase', 'Thrombolytic', 'Streptokinase-plasminogen complex for MI'),
('DB00030', 'Interferon beta-1a', 'Interferon', 'Recombinant interferon beta for MS');

-- ============================================================================
-- 2. DISEASES (33 diseases with category and description)
-- ============================================================================
INSERT INTO diseases (id, name, category, description) VALUES
('DOID:2349', 'Arteriosclerosis', 'Cardiovascular Disease', 'Hardening and thickening of arterial walls'),
('DOID:9352', 'Type 2 diabetes mellitus', 'Metabolic Disease', 'Insulin resistance metabolic disorder'),
('DOID:1612', 'Breast cancer', 'Cancer', 'Malignant tumor of breast tissue'),
('DOID:9256', 'Colorectal cancer', 'Cancer', 'Malignant tumor of colon or rectum'),
('DOID:1485', 'Cystic fibrosis', 'Genetic Disease', 'Hereditary disease affecting lungs and pancreas'),
('DOID:3083', 'Chronic obstructive pulmonary disease', 'Respiratory Disease', 'Progressive lung disease with airflow limitation'),
('DOID:0060500', 'Cutaneous T-cell lymphoma', 'Cancer', 'T-cell lymphoma affecting the skin'),
('DOID:0050745', 'Diffuse large B-cell lymphoma', 'Cancer', 'Aggressive B-cell non-Hodgkin lymphoma'),
('DOID:7148', 'Rheumatoid arthritis', 'Autoimmune Disease', 'Chronic autoimmune joint inflammation'),
('DOID:8893', 'Psoriasis', 'Autoimmune Disease', 'Chronic skin condition with scaly patches'),
('DOID:332', 'Multiple sclerosis', 'Autoimmune Disease', 'CNS demyelinating autoimmune disease'),
('DOID:9471', 'Myocardial infarction', 'Cardiovascular Disease', 'Heart attack due to coronary artery blockage'),
('DOID:10283', 'Prostate cancer', 'Cancer', 'Malignant tumor of prostate gland'),
('DOID:11612', 'Polycystic ovary syndrome', 'Endocrine Disease', 'Hormonal disorder in women'),
('DOID:2237', 'Hepatitis C', 'Infectious Disease', 'Liver infection caused by HCV'),
('DOID:2043', 'Hepatitis B', 'Infectious Disease', 'Liver infection caused by HBV'),
('DOID:3526', 'Pulmonary embolism', 'Cardiovascular Disease', 'Blood clot in pulmonary artery'),
('DOID:6713', 'Stroke', 'Cerebrovascular Disease', 'Brain damage from blocked or ruptured blood vessel'),
('DOID:0080169', 'Growth hormone deficiency', 'Endocrine Disease', 'Insufficient growth hormone production'),
('DOID:934', 'Viral disease', 'Infectious Disease', 'Disease caused by viral infection'),
('DOID:2355', 'Anemia', 'Hematologic Disease', 'Decreased red blood cells or hemoglobin'),
('DOID:3620', 'Chronic kidney disease', 'Kidney Disease', 'Progressive loss of kidney function'),
('DOID:289', 'Endometriosis', 'Gynecological Disease', 'Endometrial tissue outside the uterus'),
('DOID:11476', 'Osteoporosis', 'Bone Disease', 'Decreased bone density and strength'),
('DOID:14221', 'Paget disease of bone', 'Bone Disease', 'Abnormal bone remodeling disorder'),
('DOID:11960', 'Condyloma acuminatum', 'Infectious Disease', 'Genital warts caused by HPV'),
('DOID:9952', 'Neutropenia', 'Hematologic Disease', 'Low neutrophil count in blood'),
('DOID:8552', 'Aplastic anemia', 'Hematologic Disease', 'Bone marrow failure syndrome'),
('DOID:3393', 'Coronary artery disease', 'Cardiovascular Disease', 'Atherosclerosis of coronary arteries'),
('DOID:1909', 'Melanoma', 'Cancer', 'Aggressive skin cancer from melanocytes'),
('DOID:3963', 'Thyroid carcinoma', 'Cancer', 'Malignant tumor of thyroid gland'),
('DOID:12134', 'Hemophilia A', 'Hematologic Disease', 'X-linked bleeding disorder from Factor VIII deficiency'),
('DOID:11252', 'Bacterial disease', 'Infectious Disease', 'Disease caused by bacterial infection');

-- ============================================================================
-- 3. ASSOCIATIONS (52 records with confidence scores)
-- known = label 1 (established), predicted = label 0 (potential)
-- ============================================================================
INSERT INTO drug_disease_associations (drug_id, disease_id, association_type, confidence_score) VALUES
('DB00001', 'DOID:2349', 'known', 0.95),
('DB00001', 'DOID:9352', 'predicted', 0.42),
('DB00002', 'DOID:1612', 'known', 0.92),
('DB00002', 'DOID:9256', 'known', 0.98),
('DB00003', 'DOID:1485', 'known', 0.99),
('DB00003', 'DOID:3083', 'known', 0.78),
('DB00004', 'DOID:0060500', 'known', 0.96),
('DB00004', 'DOID:0050745', 'predicted', 0.61),
('DB00005', 'DOID:7148', 'known', 0.97),
('DB00005', 'DOID:8893', 'known', 0.95),
('DB00005', 'DOID:332', 'predicted', 0.38),
('DB00006', 'DOID:2349', 'known', 0.91),
('DB00006', 'DOID:9471', 'known', 0.94),
('DB00007', 'DOID:10283', 'known', 0.98),
('DB00007', 'DOID:1612', 'known', 0.89),
('DB00007', 'DOID:11612', 'predicted', 0.55),
('DB00008', 'DOID:2237', 'known', 0.99),
('DB00008', 'DOID:2043', 'known', 0.97),
('DB00009', 'DOID:9471', 'known', 0.99),
('DB00009', 'DOID:3526', 'known', 0.98),
('DB00009', 'DOID:6713', 'known', 0.97),
('DB00010', 'DOID:0080169', 'known', 0.96),
('DB00011', 'DOID:2237', 'known', 0.93),
('DB00011', 'DOID:934', 'known', 0.85),
('DB00012', 'DOID:2355', 'known', 0.98),
('DB00012', 'DOID:3620', 'known', 0.97),
('DB00013', 'DOID:3526', 'known', 0.94),
('DB00014', 'DOID:10283', 'known', 0.96),
('DB00014', 'DOID:1612', 'known', 0.91),
('DB00014', 'DOID:289', 'known', 0.95),
('DB00015', 'DOID:9471', 'known', 0.96),
('DB00016', 'DOID:2355', 'known', 0.99),
('DB00016', 'DOID:3620', 'known', 0.98),
('DB00017', 'DOID:11476', 'known', 0.95),
('DB00017', 'DOID:14221', 'known', 0.97),
('DB00018', 'DOID:11960', 'known', 0.96),
('DB00019', 'DOID:9952', 'known', 0.99),
('DB00020', 'DOID:9952', 'known', 0.94),
('DB00020', 'DOID:8552', 'predicted', 0.52),
('DB00021', 'DOID:9471', 'known', 0.97),
('DB00021', 'DOID:3393', 'known', 0.95),
('DB00022', 'DOID:2237', 'known', 0.98),
('DB00022', 'DOID:1909', 'known', 0.87),
('DB00023', 'DOID:9471', 'known', 0.97),
('DB00024', 'DOID:3963', 'known', 0.96),
('DB00025', 'DOID:12134', 'known', 0.99),
('DB00026', 'DOID:7148', 'known', 0.93),
('DB00027', 'DOID:11252', 'known', 0.91),
('DB00028', 'DOID:332', 'known', 0.98),
('DB00029', 'DOID:9471', 'known', 0.92),
('DB00030', 'DOID:332', 'known', 0.97);

-- ============================================================================
-- 4. Validation
-- ============================================================================
SELECT '=== Import Complete ===' as status;
SELECT 'Drugs' as type, COUNT(*) as count FROM drugs
UNION ALL SELECT 'Diseases', COUNT(*) FROM diseases
UNION ALL SELECT 'Associations', COUNT(*) FROM drug_disease_associations
UNION ALL SELECT 'Known (label=1)', COUNT(*) FROM drug_disease_associations WHERE association_type='known'
UNION ALL SELECT 'Predicted (label=0)', COUNT(*) FROM drug_disease_associations WHERE association_type='predicted';

SELECT '=== Drug Types ===' as info;
SELECT type, COUNT(*) as cnt FROM drugs GROUP BY type ORDER BY cnt DESC;

SELECT '=== Disease Categories ===' as info;
SELECT category, COUNT(*) as cnt FROM diseases GROUP BY category ORDER BY cnt DESC;

