#!/bin/bash

discover_conda() {
    if command -v conda >/dev/null 2>&1; then
        return 0
    fi

    local candidate
    for candidate in \
        "$HOME/miniconda3" \
        "$HOME/anaconda3" \
        "$HOME/mambaforge" \
        "$HOME/miniforge3"
    do
        if [ -f "$candidate/etc/profile.d/conda.sh" ]; then
            export PATH="$candidate/bin:$PATH"
            # shellcheck disable=SC1090
            source "$candidate/etc/profile.d/conda.sh"
            if command -v conda >/dev/null 2>&1; then
                return 0
            fi
        fi
    done

    return 1
}
