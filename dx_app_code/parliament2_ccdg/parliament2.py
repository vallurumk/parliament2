#!/usr/bin/env python

import dxpy
import subprocess
import os.path
import glob

@dxpy.entry_point('main')
def main(**job_inputs):

    if 'prefix' not in job_inputs:
        bam_name = dxpy.describe(job_inputs['illumina_bam'])['name']
        if bam_name.endswith("cram"):
            prefix = bam_name[:-5]
        else:
            prefix = bam_name[:-4]
    else:
        prefix = job_inputs['prefix']

    # Running Docker image
    subprocess.check_call(['mkdir', '-p', '/home/dnanexus/in', '/home/dnanexus/out'])

    print "Starting Docker"

    input_bam = dxpy.open_dxfile(job_inputs['illumina_bam'])
    bam_name = "/home/dnanexus/in/{0}".format(input_bam.name)
    dxpy.download_dxfile(input_bam, bam_name)
    
    ref_genome = dxpy.open_dxfile(job_inputs['ref_fasta'])
    ref_name = "/home/dnanexus/in/{0}".format(ref_genome.name)
    dxpy.download_dxfile(ref_genome, ref_name)
    docker_call = ['dx-docker', 'run', '-v', '/home/dnanexus/in/:/home/dnanexus/in/', '-v', '/home/dnanexus/out/:/home/dnanexus/out/', 'parliament2_ccdg', '--bam', bam_name, '-r', ref_name, '--prefix', str(prefix)]

    if 'illumina_bai' in job_inputs:
        input_bai = dxpy.open_dxfile(job_inputs['illumina_bai'])
        bai_name = "/home/dnanexus/in/{0}".format(input_bai.name)
        dxpy.download_dxfile(input_bai, bai_name)

        docker_call.extend(['--bai', bai_name])

    if 'gatk_jar' in job_inputs:
        gatk_jar = dxpy.open_dxfile(job_inputs['gatk_jar'])
        gatk_name = "/home/dnanexus/in/{0}".format(gatk_jar.name)
        dxpy.download_dxfile(gatk_jar, gatk_name)

        docker_call.extend(['--gatk_jar', gatk_name])
        
    if job_inputs['filter_short_contigs']:
        docker_call.append('--filter_short_contigs')
    if job_inputs['run_breakdancer']:
        docker_call.append('--breakdancer')
    if job_inputs['run_breakseq']:
        docker_call.append('--breakseq')
    if job_inputs['run_manta']:
        docker_call.append('--manta')
    if job_inputs['run_cnvnator']:
        docker_call.append('--cnvnator')
    if job_inputs['run_lumpy']:
        docker_call.append('--lumpy')
    if job_inputs['run_delly_inversion']:
        docker_call.append('--delly_inversion')
    if job_inputs['run_delly_insertion']:
        docker_call.append('--delly_insertion')
    if job_inputs['run_delly_deletion']:
        docker_call.append('--delly_deletion')
    if job_inputs['run_delly_duplication']:
        docker_call.append('--delly_duplication')
    if job_inputs['run_genotype_candidates']:
        docker_call.append('--genotype')
    if job_inputs['run_atlas']:
        docker_call.append('--atlas')
    if job_inputs['run_stats']:
        docker_call.append('--stats')
    if job_inputs['run_svviz']:
        docker_call.append('--svviz')
    if job_inputs['svviz_only_validated_candidates']:
        docker_call.append('--svviz_only_validated_candidates')

    subprocess.check_call(docker_call)

    print "Docker image finished"

    # Uploading SV caller outputs
    sv_caller_results_names = glob.glob('/home/dnanexus/out/sv_caller_results/*')
    sv_caller_results_upload = []
    for name in sv_caller_results_names:
        sv_caller_results_upload.append(dxpy.dxlink(dxpy.upload_local_file(name)))

    output = {
        'sv_caller_results' : sv_caller_results_upload
    }

    # Uploading xAtlas outputs
    if job_inputs['run_atlas']:
        atlas_file_names = glob.glob('/home/dnanexus/out/atlas/*')
        atlas_file_uploads = []
        for name in atlas_file_names:
            atlas_file_uploads.append(dxpy.dxlink(dxpy.upload_local_file(name)))
        output['atlas_output'] = atlas_file_uploads
    

    # Uploading samtools flagstat outputs
    if job_inputs['run_stats']:
        stats_file_names = glob.glob('/home/dnanexus/out/stats/*')
        stats_file_uploads = []
        for name in stats_file_names:
            stats_file_uploads.append(dxpy.dxlink(dxpy.upload_local_file(name)))
        output['align_stats_output'] = stats_file_uploads

    # Uploading log files generated
    if job_inputs['output_log_files'] and os.listdir('/home/dnanexus/out/log_files/'):
        log_file_names = glob.glob('/home/dnanexus/out/log_files/*')
        log_file_upload = []
        for name in log_file_names:
            log_file_upload.append(dxpy.dxlink(dxpy.upload_local_file(name)))
        output['log_files'] = log_file_upload

    # Uploading SVTyper outputs
    if job_inputs['run_genotype_candidates']:
        svtyped_vcf_names = glob.glob('/home/dnanexus/out/svtyped_vcfs/*')
        svtyped_vcfs_upload = []
        for name in svtyped_vcf_names:
            svtyped_vcfs_upload.append(dxpy.dxlink(dxpy.upload_local_file(name)))

        output['svtyped_vcfs'] = svtyped_vcfs_upload
        output['combined_genotypes'] = dxpy.dxlink(dxpy.upload_local_file('/home/dnanexus/out/{0}.combined.genotyped.vcf'.format(prefix)))
        
    # Uploading svviz outputs
    if job_inputs['run_svviz'] and os.path.isfile('/home/dnanexus/out/{0}.svviz_outputs.tar.gz'.format(prefix)):
        output['svviz_outputs'] = dxpy.dxlink(dxpy.upload_local_file('/home/dnanexus/out/{0}.svviz_outputs.tar.gz'.format(prefix)))

    return output

dxpy.run()