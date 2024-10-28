### Follow instructions to setup and run the test with docker:

https://github.com/lhvu2/deepvariant/blob/r1.6.1/docs/deepvariant-quick-start.md


### Setting env variables:
export BIN_VERSION="1.6.1"
export OUTPUT_DIR=/home/lhvu/bio/deepvariant/tests/quickstart-output
export INPUT_DI=/home/lhvu/bio/deepvariant/tests/quickstart-testdata


### Dry-run:
```
sudo docker run \
  -v "${INPUT_DIR}":"/home/lhvu/bio/deepvariant/tests/quickstart-testdata" \
  -v "${OUTPUT_DIR}":"/home/lhvu/bio/deepvariant/tests/quickstart-output" \
  google/deepvariant:"${BIN_VERSION}" \
  /opt/deepvariant/bin/run_deepvariant \
  --model_type=WGS \
  --ref=/home/lhvu/bio/deepvariant/tests/quickstart-testdata/ucsc.hg19.chr20.unittest.fasta \
  --reads=/home/lhvu/bio/deepvariant/tests/quickstart-testdata/NA12878_S1.chr20.10_10p1mb.bam \
  --regions "chr20:10,000,000-10,010,000" \
  --output_vcf=/home/lhvu/bio/deepvariant/tests/quickstart-output/output.vcf.gz \
  --output_gvcf=/home/lhvu/bio/deepvariant/tests/quickstart-output/output.g.vcf.gz \
  --intermediate_results_dir /home/lhvu/bio/deepvariant/tests/quickstart-output/intermediate_results_dir \
  --num_shards=1 \
  --dry_run=true
```

### Real run: 
- Removing dry_run=true from command line:

```
sudo docker run \
  -v "${INPUT_DIR}":"/home/lhvu/bio/deepvariant/tests/quickstart-testdata" \
  -v "${OUTPUT_DIR}":"/home/lhvu/bio/deepvariant/tests/quickstart-output" \
  google/deepvariant:"${BIN_VERSION}" \
  /opt/deepvariant/bin/run_deepvariant \
  --model_type=WGS \
  --ref=/home/lhvu/bio/deepvariant/tests/quickstart-testdata/ucsc.hg19.chr20.unittest.fasta \
  --reads=/home/lhvu/bio/deepvariant/tests/quickstart-testdata/NA12878_S1.chr20.10_10p1mb.bam \
  --regions "chr20:10,000,000-10,010,000" \
  --output_vcf=/home/lhvu/bio/deepvariant/tests/quickstart-output/output.vcf.gz \
  --output_gvcf=/home/lhvu/bio/deepvariant/tests/quickstart-output/output.g.vcf.gz \
  --intermediate_results_dir /home/lhvu/bio/deepvariant/tests/quickstart-output/intermediate_results_dir \
  --num_shards=1 
```

Output of real run:
```
/usr/local/lib/python3.8/dist-packages/tensorflow_addons/utils/tfa_eol_msg.py:23: UserWarning:

TensorFlow Addons (TFA) has ended development and introduction of new features.
TFA has entered a minimal maintenance and release mode until a planned end of life in May 2024.
Please modify downstream libraries to take dependencies from other repositories in our TensorFlow community (e.g. Keras, Keras-CV, and Keras-NLP).

For more information see: https://github.com/tensorflow/addons/issues/2807

  warnings.warn(
I1028 17:28:05.500074 140409568839488 call_variants.py:563] Total 1 writing processes started.
I1028 17:28:05.504122 140409568839488 dv_utils.py:370] From /home/lhvu/bio/deepvariant/tests/quickstart-output/intermediate_results_dir/make_examples.tfrecord-00000-of-00001.gz.example_info.json: Shape of input examples: [100, 221, 7], Channels of input examples: [1, 2, 3, 4, 5, 6, 19].
I1028 17:28:05.504324 140409568839488 call_variants.py:588] Shape of input examples: [100, 221, 7]
I1028 17:28:05.505603 140409568839488 call_variants.py:592] Use saved model: True
I1028 17:28:19.183455 140409568839488 dv_utils.py:370] From /opt/models/wgs/example_info.json: Shape of input examples: [100, 221, 7], Channels of input examples: [1, 2, 3, 4, 5, 6, 19].
I1028 17:28:19.183785 140409568839488 dv_utils.py:370] From /home/lhvu/bio/deepvariant/tests/quickstart-output/intermediate_results_dir/make_examples.tfrecord-00000-of-00001.gz.example_info.json: Shape of input examples: [100, 221, 7], Channels of input examples: [1, 2, 3, 4, 5, 6, 19].
I1028 17:28:21.121918 140409568839488 call_variants.py:716] Predicted 84 examples in 1 batches [1.798 sec per 100].
I1028 17:28:21.438545 140409568839488 call_variants.py:779] Complete: call_variants.

real    0m24.119s
user    0m36.780s
sys     0m12.514s

***** Running the command:*****
time /opt/deepvariant/bin/postprocess_variants --ref "/home/lhvu/bio/deepvariant/tests/quickstart-testdata/ucsc.hg19.chr20.unittest.fasta" --infile "/home/lhvu/bio/deepvariant/tests/quickstart-output/intermediate_results_dir/call_variants_output.tfrecord.gz" --outfile "/home/lhvu/bio/deepvariant/tests/quickstart-output/output.vcf.gz" --cpus "1" --gvcf_outfile "/home/lhvu/bio/deepvariant/tests/quickstart-output/output.g.vcf.gz" --nonvariant_site_tfrecord_path "/home/lhvu/bio/deepvariant/tests/quickstart-output/intermediate_results_dir/gvcf.tfrecord@1.gz"

I1028 17:28:30.006106 140638474241856 postprocess_variants.py:1211] Using sample name from call_variants output. Sample name: NA12878
2024-10-28 17:28:30.007748: I deepvariant/postprocess_variants.cc:94] Read from: /home/lhvu/bio/deepvariant/tests/quickstart-output/intermediate_results_dir/call_variants_output-00000-of-00001.tfrecord.gz
2024-10-28 17:28:30.009032: I deepvariant/postprocess_variants.cc:109] Total #entries in single_site_calls = 84
I1028 17:28:30.009931 140638474241856 postprocess_variants.py:1313] CVO sorting took 4.022518793741862e-05 minutes
I1028 17:28:30.010364 140638474241856 postprocess_variants.py:1316] Transforming call_variants_output to variants.
I1028 17:28:30.013167 140638474241856 postprocess_variants.py:1211] Using sample name from call_variants output. Sample name: NA12878
I1028 17:28:30.050335 140638474241856 postprocess_variants.py:1386] Processing variants (and writing to temporary file) took 0.000658722718556722 minutes
I1028 17:28:30.888808 140638474241856 postprocess_variants.py:1407] Finished writing VCF and gVCF in 0.01397002140680949 minutes.

real    0m8.139s
user    0m12.987s
sys     0m6.478s

***** Running the command:*****
time /opt/deepvariant/bin/vcf_stats_report --input_vcf "/home/lhvu/bio/deepvariant/tests/quickstart-output/output.vcf.gz" --outfile_base "/home/lhvu/bio/deepvariant/tests/quickstart-output/output"

I1028 17:28:37.621751 140393560844096 genomics_reader.py:222] Reading /home/lhvu/bio/deepvariant/tests/quickstart-output/output.vcf.gz with NativeVcfReader

real    0m7.032s
user    0m11.820s
sys     0m6.552s
```
