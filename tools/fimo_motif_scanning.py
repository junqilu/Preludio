import os
import pickle
import shlex
import subprocess

import pandas as pd


def motif_scanning(fimo_output_direct, motif_database_direct, dna_seq_direct, p_threshold):
    os.makedirs(fimo_output_direct, exist_ok=True)

    # ! fimo --oc output/ --verbosity 1 --bgfile --nrdb-- --thresh 1.0E-4 --no-pgc JASPAR2024_CORE_vertebrates_redundant_pfms_meme.txt input/ncbi_51601_promoter_-5000_2000.fna # This is the fimo line that you can directly run in WSL

    search_command = [
        'fimo',
        '--oc', fimo_output_direct,  # Define output directory
        '--verbosity', '1',  # Control how much fimo prints to the console. 1 means minimal
        '--bgfile', '--nrdb--',
        # Don’t use an external background file; instead calculate base frequencies (A,C,G,T) from my FASTA input
        '--thresh', str(p_threshold),  # Only report motif matches with a p-value p_threshold
        '--no-pgc',
        # “No p-value/gc correction.” Disables a correction step that accounts for local GC content variation when calculating motif significance
        motif_database_direct,
        dna_seq_direct
    ]

    print('Running command:', ' '.join(search_command))

    try:
        res = subprocess.run(
            search_command,
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        print("RETURN CODE:", e.returncode)
        print("STDOUT:\n", e.stdout)
        print("STDERR:\n", e.stderr)

    if res.returncode != 0:  # This is less effective than the try block since if something is wrong with subprocess.run(), the code won't get to this line
        print("Command failed:", " ".join(shlex.quote(a) for a in search_command))
        print(res.stderr)  # This message pinpoints the issue
    else:
        result_direct = os.path.join(fimo_output_direct, 'fimo.tsv').replace('\\', '/')
        print("Motif scanning result saved as {}".format(result_direct))

    return result_direct


def filter_fimo_output_by_tf_list(tf_pkl_direct, fimo_df):  # Filter fimo_df by a list of TF given by tf_pkl_direct
    with open(tf_pkl_direct, 'rb') as f:
        tf_list = pickle.load(f)

    fimo_df_filtered = fimo_df[fimo_df['TF_stripped'].isin(tf_list)]
    print(f'Before filtering, df has a shape as {fimo_df.shape}')
    print(f'After filtering, df has a shape as {fimo_df_filtered.shape}')

    return fimo_df_filtered


def rank_by_count(
        input_df):  # Simple: rank by number of sites per TF. Rank the TF by the most possible sites (but noisy motifs inflate this)
    rank_count_df = (
        input_df.groupby("TF")
        .size()
        .sort_values(ascending=False)
        .rename("site_count")
    )

    rank_count_df = rank_count_df.reset_index(drop=False)

    return rank_count_df


def rank_by_best_q(
        input_df):  # Stringency: rank by best (lowest) q-value (adjusted p-values) per TF. Rank the TF by the single strongest site (good for TFs with a sharp binding site)
    # A TF might have just one perfect site in your sequence. It won’t win by count, but that one site might be biologically very relevant

    rank_best_q_df = (
        input_df.groupby('TF')['q-value']
        .min()  # Use the smallest q as the best q for thta TF
        .sort_values()
        .rename('best_q_per_tf')
    )

    rank_best_q_df = rank_best_q_df.reset_index(drop=False)

    return rank_best_q_df


def merge_rank_by_count_best_q(input_df, df_save_direct):
    rank_count_df = rank_by_count(input_df)
    rank_best_q_df = rank_by_best_q(input_df)

    merged_df = pd.merge(rank_count_df, rank_best_q_df, on='TF', how='inner')
    merged_df = merged_df.sort_values(by='best_q_per_tf')
    merged_df = merged_df.reset_index(drop=True)

    merged_df.to_csv(df_save_direct, index=False)
    return merged_df
