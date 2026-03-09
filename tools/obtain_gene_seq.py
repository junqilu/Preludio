import os, requests
import xml.etree.ElementTree as ET


def gene_name_to_id(gene_name):  # Return gene_uid with a given gene_name (it has to be the name of the gene)
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "gene",
        "term": f"{gene_name}[sym] AND human[orgn]",
        "retmode": "json"
    }

    try:
        r = requests.get(search_url, params=params, timeout=10)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"NCBI request failed: {e}")

    data = r.json()

    # check if gene exists
    id_list = data.get("esearchresult", {}).get("idlist", [])

    if not id_list:
        raise ValueError(f"Gene '{gene_name}' not found in NCBI database")
    else:
        gene_uid = id_list[0]

        return gene_uid


def gene_uid_to_gene_summary(gene_uid):  # Return very informational gene_summary with given gene_uid
    summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    params = {
        "db": "gene",  # Asking for gene metadata
        "id": gene_uid,
        "retmode": "json"
    }

    try:
        r = requests.get(summary_url, params=params, timeout=10)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise (RuntimeError(f"NCBI request failed: {e}"))

    gene_json = r.json()

    if not gene_json:
        raise ValueError(f"Gene '{gene_uid}' not found in NCBI database")
    else:
        gene_summary = gene_json["result"][gene_uid]

        print(f'>>>> Gene summary found for {gene_summary['description']}')
        return gene_summary


def get_strand_from_gene_efetch(entrez_id: str, timeout: int = 30) -> str:
    """
    Returns 'plus', 'minus', or 'unknown' from NCBI Gene EFetch XML by reading <Na-strand value="...">.

    entrez_id is the same as gene_uid
    """
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "gene",
        "id": str(entrez_id),
        "retmode": "xml"
    }

    r = requests.get(url, params=params, timeout=timeout)
    r.raise_for_status()

    root = ET.fromstring(r.text)

    # Find first Na-strand with a "value" attribute, like TFinder does
    for elem in root.iter():
        if elem.tag == "Na-strand":
            val = elem.attrib.get("value", "").strip()
            if val:
                return val  # typically "plus" or "minus". "minus" means on the compliment strand

    return "unknown"  # Whether a gene is on the complimentary strand can be verified by its NCBI information page. Under the Genomic context section, if the Location is something like EGFR's NC_000007.14 (55019017..55211628), then it's on the + strand; if it's something like TP53's NC_000017.11 (7668421..7687490, complement), then it's on the - strand


def determine_TSS_from_gene_summary(gene_summary):
    chromosome = gene_summary["genomicinfo"][0]["chraccver"]
    start = gene_summary["genomicinfo"][0]["chrstart"] + 1  # Plus one to match the TFinder style
    end = gene_summary["genomicinfo"][0]["chrstop"]

    tss = start  # NIH might have some updates such that now TSS is always the chrstart and you can use the relative relationship between chrstart and chrstop to determine the strand direction--this might be the reason why strand information isn't in genomicinfo anymore

    if start > end:
        strand = 'minus'
    elif start < end:
        strand = 'plus'
    else:
        gene_uid = gene_summary['uid']
        print(f"Gene ID '{gene_uid}' might have an issue on determining the strand information")

    if strand != get_strand_from_gene_efetch(
            gene_summary['uid']):  # This function for sure will return the strand direction of the gene
        raise ValueError("Inferred strand information doesn't match the gene documentation")
    else:
        return chromosome, strand, tss


def retrieve_seq(gene_name, gene_uid, chromosome, strand, tss, seq_type='promoter', upstream_bp=5000,
                 downstream_bp=2000):
    tss_1based = tss + 1

    if strand == 'plus':
        seq_start = tss - upstream_bp
        seq_end = tss + downstream_bp - 1  # Minus 1 to mtahc the TFinder style
        strand_num = 1
    elif strand == 'minus':
        seq_start = tss_1based - downstream_bp
        seq_end = tss + upstream_bp
        strand_num = 2
    else:
        print('Somehting is wrong')

    efetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "nuccore",
        "id": chromosome,
        "seq_start": seq_start,
        "seq_stop": seq_end,
        "strand": strand_num,  # It uses 1 to represent plus strand and 2 for minus strand
        "rettype": "fasta",
        "retmode": "text"
    }

    fasta = requests.get(efetch_url, params=params).text

    lines = fasta.splitlines()

    header = lines[0][1:]
    header_mine = f'>NIH gene ID: {gene_uid} {gene_name} | {header} | Strand: {strand} | Type: {seq_type} | TSS (on chromosome): {tss} | TSS (on sequence): {upstream_bp}'

    seq = "".join(lines[1:])

    seq_clean = header_mine + '\n' + seq

    return seq_clean


def gene_name_to_download_seq(gene_name, seq_type='promoter',
                              upstream_bp=5000, downstream_bp=2000, save_file=True):
    # By default, the obtained .fna will be saved into the input/obtained_seq folder
    gene_uid = gene_name_to_id(gene_name)
    gene_summary = gene_uid_to_gene_summary(gene_uid)
    chromosome, strand, tss = determine_TSS_from_gene_summary(gene_summary)

    seq_clean = retrieve_seq(
        gene_name,
        gene_uid,
        chromosome,
        strand,
        tss,
        seq_type,
        upstream_bp,
        downstream_bp
    )

    os.makedirs('input/obtained_seq', exist_ok=True)

    if save_file:
        save_file_directory = f'input/obtained_seq/seq_{gene_name}_{seq_type}_{upstream_bp}_{downstream_bp}.fna'
        with open(save_file_directory, "w") as f:
            f.write(seq_clean)

    return seq_clean
