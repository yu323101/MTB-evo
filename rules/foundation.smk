rule foundation_prepare_outputs:
    input:
        samplesheet=str(SAMPLESHEET),
    output:
        done=result_path("logs", "workflow", "foundation_prepare.done"),
        status_run=FOUNDATION_STATUS_RUN,
        status_latest=FOUNDATION_STATUS_LATEST,
    log:
        result_path("logs", "rules", "foundation_prepare_outputs.log"),
    params:
        results_dir=RESULTS_DIR,
        python_bin=PYTHON_BIN,
        cli_module=CLI_MODULE,
        verbose_flag=VERBOSE_FLAG,
        run_id=RUN_ID,
    shell:
        r'''
        set -euo pipefail
        mkdir -p "$(dirname {log})" "$(dirname {output.done})"
        {params.python_bin} -m {params.cli_module} prepare-downstream-inputs \
            --samplesheet {input.samplesheet} \
            --output-dir {params.results_dir} \
            --foundation-status-output {output.status_run} \
            --mode foundation \
            --run-id {params.run_id} \
            {params.verbose_flag} \
            > {log} 2>&1
        cp {output.status_run} {output.status_latest}
        touch {output.done}
        '''
