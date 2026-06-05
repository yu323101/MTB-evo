rule prepare_downstream_inputs:
    input:
        samplesheet=str(SAMPLESHEET),
        foundation_done=rules.foundation_prepare_outputs.output.done,
        core_done=rules.run_core.output.done,
    output:
        done=result_path("logs", "workflow", "prepare_downstream_inputs.done"),
        status_run=DOWNSTREAM_STATUS_RUN,
        status_latest=DOWNSTREAM_STATUS_LATEST,
    log:
        result_path("logs", "rules", "prepare_downstream_inputs.log"),
    params:
        results_dir=RESULTS_DIR,
        python_bin=PYTHON_BIN,
        cli_module=CLI_MODULE,
        verbose_flag=VERBOSE_FLAG,
        run_id=RUN_ID,
    shell:
        r'''
        mkdir -p "$(dirname {log})" "$(dirname {output.done})"
        {params.python_bin} -m {params.cli_module} prepare-downstream-inputs \
            --samplesheet {input.samplesheet} \
            --output-dir {params.results_dir} \
            --downstream-status-output {output.status_run} \
            --mode light \
            --run-id {params.run_id} \
            {params.verbose_flag} \
            &> {log}
        cp {output.status_run} {output.status_latest}
        touch {output.done}
        '''
