#!/usr/bin/env python3
"""
Generate SNP calling pipeline script with auto-detected tool paths.

Usage: python3 pair_fixed_nostrandbias.py <strain_list.txt>

Example strain list format:
MD601.cleaned
MD602.cleaned
"""

import shutil
import sys
from pathlib import Path


def find_tool(tool_name, required=True):
    """Find tool in PATH."""
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
    script_dir = Path(__file__).parent
    data_path = script_dir.parent / "data" / filename
    if data_path.exists():
        return str(data_path)
    else:
        print(f"Error: {filename} not found in data/ directory")
        print("Please ensure reference data is downloaded:")
        print("  git pull origin main")
        sys.exit(1)


def check_bowtie2_index(ref_fasta, bowtie2_path):
    """Check if bowtie2 index exists, create if needed."""
    script_dir = Path(__file__).parent
    index_dir = script_dir.parent / "data" / "bowtie2_index"
    index_prefix = index_dir / "tb_h37rv.fasta"
    
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
            
            import subprocess
            cmd = [
                bowtie2_path,
                "-build",
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
            print(f"  mkdir -p data/bowtie2_index")
            print(f"  bowtie2-build {ref_fasta} data/bowtie2_index/tb_h37rv.fasta")
            sys.exit(1)
    
    return str(index_prefix)


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 pair_fixed_nostrandbias.py <strain_list.txt>")
        sys.exit(1)
    
    strain_list_file = sys.argv[1]
    
    # Auto-detect tool paths
    print("Detecting tools...")
    tools = {
        'sickle': find_tool('sickle'),
        'bowtie2': find_tool('bowtie2'),
        'samtools': find_tool('samtools'),
        'java': find_tool('java'),
    }
    
    # Find scripts and data files
    varscan_jar = find_script("VarScan.v2.3.9.jar")
    ppe_filter_pl = find_script("0.1_PE_IS_filt_Rv.pl")
    format_trans_pl = find_script("1_format_trans.pl")
    ppe_list = find_data_file("PPE_INS_loci_Rv.list")
    ref_fasta = find_data_file("tb_h37rv.fasta")
    ref_fai = find_data_file("tb_h37rv.fasta.fai")
    
    print(f"Found sickle: {tools['sickle']}")
    print(f"Found bowtie2: {tools['bowtie2']}")
    print(f"Found samtools: {tools['samtools']}")
    print(f"Found java: {tools['java']}")
    print(f"Found VarScan: {varscan_jar}")
    print(f"Found reference: {ref_fasta}")
    print()
    
    # Check and create bowtie2 index if needed
    bowtie2_index = check_bowtie2_index(ref_fasta, tools['bowtie2'])
    print(f"Found bowtie2 index: {bowtie2_index}")
    print()
    
    # Read strain list
    try:
        with open(strain_list_file) as f:
            strains = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Error: {strain_list_file} not found")
        sys.exit(1)
    
    print(f"Processing {len(strains)} strains...")
    print()
    
    # Check if results/ directory exists
    results_dir = Path("results")
    if not results_dir.exists():
        print("Error: results/ directory not found")
        print("Please create it first: mkdir results")
        sys.exit(1)
    
    # Generate pipeline script
    output_file = results_dir / "pair_end.sh"
    
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
        out.write("echo 'Starting SNP calling pipeline...'\n")
        out.write(f"echo 'Processing {len(strains)} strains'\n\n")
        
        for i, strain in enumerate(strains, 1):
            out.write(f"echo '[{i}/{len(strains)}] Processing {strain}...'\n")
            
            # Step 1: Quality trimming with sickle
            step1 = f"{tools['sickle']} pe -t sanger -f {strain}_1.fastq.gz -r {strain}_2.fastq.gz -o {strain}_1.fastq -p {strain}_2.fastq -s {strain}_s.fastq\n"
            out.write(step1)
            
            # Step 2: Alignment with bowtie2
            step2 = f"{tools['bowtie2']} -x {bowtie2_index} -1 {strain}_1.fastq -2 {strain}_2.fastq -U {strain}_s.fastq -S {strain}.sam\n"
            out.write(step2)
            
            # Step 3: Convert SAM to BAM
            step3 = f"{tools['samtools']} view -bhSt {ref_fai} {strain}.sam -o {strain}.paired.bam\n"
            out.write(step3)
            
            # Step 4: Sort BAM
            step4 = f"{tools['samtools']} sort {strain}.paired.bam -o {strain}.sort.bam\n"
            out.write(step4)
            
            # Step 5: Calculate depth and call variants
            step5 = f"""depth=$({tools['samtools']} depth {strain}.sort.bam | awk '{{s+=$3}}END{{print s/NR}}')
coverage=$({tools['samtools']} depth {strain}.sort.bam | awk 'END{{print NR/4411532}}')
a=$(($(echo $depth | awk '{{printf ("%.f",$1)}}')))
if [ "$a" -ge 10 ] && (echo ${{coverage}} 0.95 | awk '!($1>=$2){{exit 1}}'); then
	{tools['samtools']} mpileup -q 30 -Q 30 -Bf {ref_fasta} {strain}.sort.bam > {strain}.pileup
	b=$(($(echo $depth | awk '{{printf ("%.f",$1)}}')/10))
	if [ $b -lt 5 ]; then
		{tools['java']} -jar {varscan_jar} mpileup2snp {strain}.pileup --min-coverage 5 --min-reads2 2 --min-avg-qual 30 --min-var-freq 0.75 --p-value 99e-02 > {strain}.varscan
	else
		{tools['java']} -jar {varscan_jar} mpileup2snp {strain}.pileup --min-coverage $b --min-reads2 2 --min-avg-qual 30 --min-var-freq 0.75 --p-value 99e-02 > {strain}.varscan
	fi
	{tools['java']} -jar {varscan_jar} mpileup2cns {strain}.pileup --min-coverage 3 --min-avg-qual 20 --min-var-freq 0.75 --strand-filter 0 --min-reads2 2 > {strain}.cns
	awk -F '[:]' '{{if($9==0 || $10==0)$0="";else print $0}}' {strain}.varscan > {strain}.vars
	perl {ppe_filter_pl} {ppe_list} {strain}.vars > {strain}.var.ppe
	perl {format_trans_pl} {strain}.var.ppe > {strain}.var.for
	cut -f2,3,4 {strain}.var.for > {strain}.snp
	rm -f {strain}.sam {strain}.varscan {strain}.paired.bam {strain}_s.fastq {strain}_1.fastq {strain}_2.fastq {strain}.var.for {strain}.var.ppe {strain}.pileup
	echo '[{i}/{len(strains)}] {strain} completed successfully'
else
	echo "{strain} do not meet criteria: ${{depth}} ${{coverage}}" >> discard
	rm -f {strain}.sam {strain}.varscan {strain}.paired.bam {strain}_s.fastq {strain}_1.fastq {strain}_2.fastq {strain}.var.for {strain}.var.ppe {strain}.pileup
	echo '[{i}/{len(strains)}] {strain} discarded (low coverage)'
fi
"""
            out.write(step5)
            out.write("\n")
        
        out.write("echo 'All strains processed!'\n")
    
    print(f"Generated {output_file}")
    print(f"  Strains: {len(strains)}")
    print()
    print("To run the pipeline:")
    print("  cd results && bash pair_end.sh")
    print()
    print("Or run in background:")
    print("  cd results && nohup bash pair_end.sh > pair_end.log 2>&1 &")


if __name__ == "__main__":
    main()
