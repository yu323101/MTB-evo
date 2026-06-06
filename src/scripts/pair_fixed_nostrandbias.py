#!/usr/bin/env python3
"""Generate a legacy SNP-calling shell script from sample inputs."""

import argparse
import csv
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.tools import ToolManager

REFERENCE_PROFILES = {
    "tb_ancestor": {
        "fasta": "tb.ancestor.fasta",
        "fai": "tb.ancestor.fasta.fai",
        "bowtie2_index_prefix": "tb.ancestor.fasta",
        "genome_length": 4411532,
    },
    "tb_h37rv": {
        "fasta": "tb_h37rv.fasta",
        "fai": "tb_h37rv.fasta.fai",
        "bowtie2_index_prefix": "tb_h37rv.fasta",
        "genome_length": 4411532,
    },
}


def find_tool(tool_name, required=True):
    """Find tool in PATH (legacy function, kept for compatibility)."""
    path = shutil.which(tool_name)
    if path:
        return path
    elif required:
        print(f"Error: {tool_name} not found in PATH")
        print("Please ensure conda environment is activated:")
        print("  conda activate mtb-evo")
        sys.exit(1)
    else:
        return None


def find_script(script_name):
    """Find script in scripts/ directory."""
    script_dir = Path(__file__).parent
    script_path = script_dir / script_name
    if script_path.exists():
        return str(script_path)
    else:
        print(f"Error: {script_name} not found in {script_dir}")
        sys.exit(1)


def find_data_file(filename):
    """Find data file in data/ directory."""
    # 从 src/scripts/ 向上找到项目根目录
    script_dir = Path(__file__).parent
    data_path = script_dir.parent.parent / "data" / filename
    if data_path.exists():
        return str(data_path)
    else:
        print(f"Error: {filename} not found in data/ directory")
        print("Please ensure reference data is downloaded:")
        print("  git pull origin main")
        sys.exit(1)


def check_bowtie2_index(ref_fasta, bowtie2_path, index_prefix):
    """Check if bowtie2 index exists, create if needed."""
    index_prefix = Path(index_prefix).resolve()
    index_dir = index_prefix.parent

    # Check if index files exist
    index_files = [
        f"{index_prefix}.1.bt2",
        f"{index_prefix}.2.bt2",
        f"{index_prefix}.3.bt2",
        f"{index_prefix}.4.bt2",
        f"{index_prefix}.rev.1.bt2",
        f"{index_prefix}.rev.2.bt2"
    ]

    index_exists = all(Path(f).exists() for f in index_files)

    if not index_exists:
        print("Bowtie2 index not found in data/bowtie2_index/")
        response = input("Create index now? This may take a few minutes. (y/n): ")

        if response.lower() == 'y':
            print("Creating bowtie2 index...")
            index_dir.mkdir(parents=True, exist_ok=True)

            # Find bowtie2-build command
            bowtie2_build = shutil.which('bowtie2-build')
            if not bowtie2_build:
                # Fallback: try to find it in the same directory as bowtie2
                bowtie2_dir = Path(bowtie2_path).parent
                bowtie2_build = str(bowtie2_dir / 'bowtie2-build')
                if not Path(bowtie2_build).exists():
                    print("Error: bowtie2-build not found in PATH")
                    print("Please ensure bowtie2 is properly installed")
                    sys.exit(1)

            cmd = [
                bowtie2_build,
                ref_fasta,
                str(index_prefix)
            ]

            try:
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                print("Index created successfully!")
            except subprocess.CalledProcessError as e:
                print(f"Error creating index: {e}")
                print(f"stdout: {e.stdout}")
                print(f"stderr: {e.stderr}")
                sys.exit(1)
        else:
            print("Aborted. To create index manually, run:")
            print(f"  mkdir -p {index_dir}")
            print(f"  bowtie2-build {ref_fasta} {index_prefix}")
            sys.exit(1)

    return str(index_prefix)


def get_default_threads():
    """Get default thread count (50% of CPU cores)."""
    try:
        cpu_count = os.cpu_count() or 4
        return max(1, cpu_count // 2)
    except:
        return 4


def parse_samples_input(sample_input: str):
    """Parse legacy list or CSV samplesheet.

    Legacy format (one prefix/path per line):
      SampleA
      /path/to/SampleB

    CSV format:
      sample_id,r1,r2
      SampleA,/path/SampleA_1.fastq.gz,/path/SampleA_2.fastq.gz
    """
    path = Path(sample_input)
    if not path.exists():
        raise FileNotFoundError(sample_input)

    with open(path, "r", encoding="utf-8") as f:
        first = f.readline().strip()

    rows = []
    if "," in first and "sample_id" in first.lower() and "r1" in first.lower() and "r2" in first.lower():
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sample_id = (row.get("sample_id") or "").strip()
                r1 = (row.get("r1") or "").strip()
                r2 = (row.get("r2") or "").strip()
                if not sample_id or not r1 or not r2:
                    continue
                rows.append({"sample_id": sample_id, "r1": r1, "r2": r2})
    else:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                prefix = line.strip()
                if not prefix:
                    continue
                sample_id = os.path.basename(prefix)
                rows.append(
                    {
                        "sample_id": sample_id,
                        "r1": f"{prefix}_1.fastq.gz",
                        "r2": f"{prefix}_2.fastq.gz",
                    }
                )
    return rows


def main():
    parser = argparse.ArgumentParser(
        description='Generate SNP calling pipeline script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 pair_fixed_nostrandbias.py samples.txt
  python3 pair_fixed_nostrandbias.py samples.txt --threads 16
  python3 pair_fixed_nostrandbias.py samples.txt --threads 16 --sort-threads 8
  python3 pair_fixed_nostrandbias.py samples.txt --results-dir /path/to/results --script-path /path/to/results/logs/workflow/pair_end.sh
        """
    )
    
    parser.add_argument('strain_list', help='Sample input file (legacy list or CSV samplesheet)')
    parser.add_argument(
        '--threads', '-t',
        type=int,
        default=get_default_threads(),
        help=f'Number of threads for bowtie2 (default: {get_default_threads()}, 50%% of CPU cores)'
    )
    parser.add_argument(
        '--sort-threads', '-s',
        type=int,
        default=None,
        help='Number of threads for samtools sort (default: threads/2)'
    )
    parser.add_argument(
        "--reference-profile",
        choices=sorted(REFERENCE_PROFILES.keys()),
        default="tb_ancestor",
        help="Reference profile (default: tb_ancestor)",
    )
    parser.add_argument(
        "--reference-fasta",
        default=None,
        help="Override reference FASTA path",
    )
    parser.add_argument(
        "--reference-fai",
        default=None,
        help="Override reference FASTA index (.fai) path",
    )
    parser.add_argument(
        "--bowtie2-index",
        default=None,
        help="Override bowtie2 index prefix path",
    )
    parser.add_argument(
        "--genome-length",
        type=int,
        default=None,
        help="Override genome length used by coverage gate (default from profile)",
    )
    parser.add_argument(
        '--results-dir',
        default='results',
        help='Results directory to write pipeline outputs into (default: results)'
    )
    parser.add_argument(
        '--script-path',
        default=None,
        help='Path to write the generated shell workflow script (default: <results-dir>/pair_end.sh)'
    )
    
    args = parser.parse_args()
    
    strain_list_file = args.strain_list
    bowtie_threads = args.threads
    sort_threads = args.sort_threads or max(1, bowtie_threads // 2)
    results_dir = Path(args.results_dir).resolve()
    
    # Auto-detect tool paths using ToolManager
    print("Detecting tools...")
    tool_manager = ToolManager()
    
    if not tool_manager.validate_all():
        sys.exit(1)
    
    # Get tool paths
    tools = {
        'sickle': str(tool_manager.get_path('sickle')),
        'bowtie2': str(tool_manager.get_path('bowtie2')),
        'samtools': str(tool_manager.get_path('samtools')),
        'java': str(tool_manager.get_path('java')),
    }
    
    # Find scripts and data files
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "data"

    varscan_jar = find_script("VarScan.v2.3.9.jar")
    ppe_list = find_data_file("PPE_INS_loci_Rv.list")
    profile = REFERENCE_PROFILES[args.reference_profile]

    if args.reference_fasta:
        ref_fasta = str(Path(args.reference_fasta).resolve())
    else:
        ref_fasta = find_data_file(profile["fasta"])

    if args.reference_fai:
        ref_fai = str(Path(args.reference_fai).resolve())
    else:
        default_fai = data_dir / profile["fai"]
        ref_fai = str(default_fai if default_fai.exists() else Path(f"{ref_fasta}.fai"))

    if args.bowtie2_index:
        bowtie2_index_prefix = Path(args.bowtie2_index).resolve()
    else:
        bowtie2_index_prefix = data_dir / "bowtie2_index" / profile["bowtie2_index_prefix"]

    genome_length = args.genome_length if args.genome_length else int(profile["genome_length"])

    if not Path(ref_fasta).exists():
        print(f"Error: reference FASTA not found: {ref_fasta}")
        sys.exit(1)

    print(f"Found sickle: {tools['sickle']}")
    print(f"Found bowtie2: {tools['bowtie2']}")
    print(f"Found samtools: {tools['samtools']}")
    print(f"Found java: {tools['java']}")
    print(f"Found VarScan: {varscan_jar}")
    print(f"Reference profile: {args.reference_profile}")
    print(f"Found reference: {ref_fasta}")
    print(f"Found/expected FAI: {ref_fai}")
    print()

    if not Path(ref_fai).exists():
        print(f"FAI not found, generating: {ref_fai}")
        try:
            subprocess.run([tools["samtools"], "faidx", ref_fasta], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error generating FAI: {e}")
            sys.exit(1)
        generated_fai = Path(f"{ref_fasta}.fai")
        if generated_fai.exists():
            ref_fai = str(generated_fai)

    # Check and create bowtie2 index if needed
    bowtie2_index = check_bowtie2_index(ref_fasta, tools['bowtie2'], bowtie2_index_prefix)
    print(f"Found bowtie2 index: {bowtie2_index}")
    print()
    
    # Read samples input
    try:
        samples = parse_samples_input(strain_list_file)
    except FileNotFoundError:
        print(f"Error: {strain_list_file} not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error parsing sample input {strain_list_file}: {e}")
        sys.exit(1)
    
    print(f"Processing {len(samples)} strains...")
    print()
    
    # Check if results directory exists
    if not results_dir.exists():
        print(f"Error: results directory not found: {results_dir}")
        print("Please create it first")
        sys.exit(1)

    # Generate pipeline script
    output_file = Path(args.script_path).resolve() if args.script_path else results_dir / "pair_end.sh"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    logs_dir = results_dir / "logs"
    sample_logs_dir = logs_dir / "samples"
    logs_dir.mkdir(parents=True, exist_ok=True)
    sample_logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if file already exists
    if output_file.exists():
        response = input(f"File {output_file} already exists. Overwrite? (y/n): ")
        if response.lower() != 'y':
            print("Aborted.")
            sys.exit(0)
    
    with open(output_file, "w") as out:
        # Write header
        out.write("#!/bin/bash\n")
        out.write("set -e\n\n")
        out.write(f'RESULTS_DIR={shlex.quote(str(results_dir))}\n')
        out.write('LOGS_DIR="$RESULTS_DIR/logs"\n')
        out.write('mkdir -p "$LOGS_DIR" "$LOGS_DIR/samples"\n\n')
        out.write("echo 'Starting SNP calling pipeline...'\n")
        out.write(f"echo 'Processing {len(samples)} strains'\n\n")
        
        for i, sample in enumerate(samples, 1):
            strain_name = sample["sample_id"]
            r1 = sample["r1"]
            r2 = sample["r2"]
            
            out.write(f'SAMPLE_LOG="$LOGS_DIR/samples/{strain_name}.step2.log"\n')
            out.write(f"echo '[{i}/{len(samples)}] Processing {strain_name}...'\n")
            out.write(f'echo \'[{i}/{len(samples)}] Processing {strain_name}...\' > "$SAMPLE_LOG"\n')
            out.write("{\n")

            # Step 1: Quality trimming with sickle
            # Input uses explicit R1/R2 paths from samples input
            step1 = (
                f"{tools['sickle']} pe -t sanger "
                f"-f {shlex.quote(r1)} -r {shlex.quote(r2)} "
                f'-o "$RESULTS_DIR/{strain_name}_1.fastq" -p "$RESULTS_DIR/{strain_name}_2.fastq" '
                f'-s "$RESULTS_DIR/{strain_name}_s.fastq"\n'
            )
            out.write(step1)
            
            # Step 2: Alignment with bowtie2 (multi-threaded)
            step2 = f'{tools["bowtie2"]} -p {bowtie_threads} -x {bowtie2_index} -1 "$RESULTS_DIR/{strain_name}_1.fastq" -2 "$RESULTS_DIR/{strain_name}_2.fastq" -U "$RESULTS_DIR/{strain_name}_s.fastq" -S "$RESULTS_DIR/{strain_name}.sam"\n'
            out.write(step2)

            # Step 3: Convert SAM to BAM
            step3 = f'{tools["samtools"]} view -bhSt {shlex.quote(ref_fai)} "$RESULTS_DIR/{strain_name}.sam" -o "$RESULTS_DIR/{strain_name}.paired.bam"\n'
            out.write(step3)

            # Step 4: Sort BAM (multi-threaded)
            step4 = f'{tools["samtools"]} sort -@ {sort_threads} "$RESULTS_DIR/{strain_name}.paired.bam" -o "$RESULTS_DIR/{strain_name}.sort.bam"\n'
            out.write(step4)
            
            # Step 5: Calculate depth and call variants
            step5 = f"""depth=$({tools['samtools']} depth $RESULTS_DIR/{strain_name}.sort.bam | awk '{{s+=$3}}END{{print s/NR}}')
coverage=$({tools['samtools']} depth $RESULTS_DIR/{strain_name}.sort.bam | awk 'END{{print NR/{genome_length}}}')
a=$(($(echo $depth | awk '{{printf ("%.f",$1)}}')))
if [ "$a" -ge 10 ] && (echo ${{coverage}} 0.95 | awk '!($1>=$2){{exit 1}}'); then
	{tools['samtools']} mpileup -q 30 -Q 30 -Bf {ref_fasta} $RESULTS_DIR/{strain_name}.sort.bam > $RESULTS_DIR/{strain_name}.pileup
	b=$(($(echo $depth | awk '{{printf ("%.f",$1)}}')/10))
	if [ $b -lt 5 ]; then
		{tools['java']} -jar {varscan_jar} mpileup2snp $RESULTS_DIR/{strain_name}.pileup --min-coverage 5 --min-reads2 2 --min-avg-qual 30 --min-var-freq 0.75 --p-value 99e-02 > $RESULTS_DIR/{strain_name}.varscan
	else
		{tools['java']} -jar {varscan_jar} mpileup2snp $RESULTS_DIR/{strain_name}.pileup --min-coverage $b --min-reads2 2 --min-avg-qual 30 --min-var-freq 0.75 --p-value 99e-02 > $RESULTS_DIR/{strain_name}.varscan
	fi
	{tools['java']} -jar {varscan_jar} mpileup2cns $RESULTS_DIR/{strain_name}.pileup --min-coverage 3 --min-avg-qual 20 --min-var-freq 0.75 --strand-filter 0 --min-reads2 2 > $RESULTS_DIR/{strain_name}.cns
	awk -F '[:]' '{{if($9==0 || $10==0)$0="";else print $0}}' $RESULTS_DIR/{strain_name}.varscan > $RESULTS_DIR/{strain_name}.vars
	mtb-evo ppe-filter --ppe-list {ppe_list} --input $RESULTS_DIR/{strain_name}.vars --output $RESULTS_DIR/{strain_name}.var.ppe
	mtb-evo format-trans --input $RESULTS_DIR/{strain_name}.var.ppe --output $RESULTS_DIR/{strain_name}.var.for
	cut -f2,3,4 $RESULTS_DIR/{strain_name}.var.for > $RESULTS_DIR/{strain_name}.snp
	rm -f $RESULTS_DIR/{strain_name}.sam $RESULTS_DIR/{strain_name}.varscan $RESULTS_DIR/{strain_name}.paired.bam $RESULTS_DIR/{strain_name}_s.fastq $RESULTS_DIR/{strain_name}_1.fastq $RESULTS_DIR/{strain_name}_2.fastq $RESULTS_DIR/{strain_name}.var.for $RESULTS_DIR/{strain_name}.var.ppe $RESULTS_DIR/{strain_name}.pileup
	echo '[{i}/{len(samples)}] {strain_name} completed successfully'
else
	echo "{strain_name} do not meet criteria: ${{depth}} ${{coverage}}" >> $LOGS_DIR/discard.txt
	rm -f $RESULTS_DIR/{strain_name}.sam $RESULTS_DIR/{strain_name}.varscan $RESULTS_DIR/{strain_name}.paired.bam $RESULTS_DIR/{strain_name}_s.fastq $RESULTS_DIR/{strain_name}_1.fastq $RESULTS_DIR/{strain_name}_2.fastq $RESULTS_DIR/{strain_name}.var.for $RESULTS_DIR/{strain_name}.var.ppe $RESULTS_DIR/{strain_name}.pileup
	echo '[{i}/{len(samples)}] {strain_name} discarded (low coverage)'
fi
"""
            out.write(step5)
            out.write('} >> "$SAMPLE_LOG" 2>&1\n')
            out.write('tail -n 1 "$SAMPLE_LOG" || true\n')
            out.write("\n")
        
        out.write("echo 'All strains processed!'\n")
    
    print(f"Generated workflow script: {output_file}")
    print(f"  Strains: {len(samples)}")
    print(f"  Bowtie2 threads: {bowtie_threads}")
    print(f"  Samtools sort threads: {sort_threads}")
    print()
    print("To run the pipeline:")
    print(f"  bash {output_file}")


if __name__ == "__main__":
    main()
