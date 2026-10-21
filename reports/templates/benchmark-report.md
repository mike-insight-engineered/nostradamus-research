# Translation Benchmark Report

${banner}

Generated: ${generated_at}

## 1. Pipeline configuration

${pipeline_table}

## 2. Dataset version

${dataset_table}

## 3. Reference translations

${reference_summary}

## 4. Results by pipeline and target language

Automated metrics are reported with percentile-bootstrap intervals; acceptance rates (from human
review, where available) with Wilson intervals. chrF is a surface-similarity measure and is not
proof of correctness.

${results_table}

## 5. Per-category results

${category_table}

## 6. Error distributions (MQM categories)

${error_table}

## 7. Staging analysis (Pipeline B vs A)

${staging_analysis}

## 8. Runtime and API cost

${cost_table}

## 9. Limitations

${limitations}
