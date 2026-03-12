import pickle
import re
import requests
import os
import pandas as pd
import numpy as np


def obtain_ncit_concepts(ncit_search_term, page_size=500):
    url = 'https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/search'  # NCIt is NCI Thesaurus

    start = 0  # This will be gradually increased in the loop to move the search window
    all_concepts = []

    while True:

        params = {
            'term': ncit_search_term,
            'type': 'contains',
            'include': 'minimal',
            'fromRecord': start,
            'pageSize': page_size
        }

        r = requests.get(url, params=params)
        data = r.json()

        if 'concepts' in data:
            concepts = data['concepts']

            all_concepts.extend(concepts)

            print(f'Concepts obtained: {start} to {start + len(concepts)}')

            start += page_size

        else:  # This means you've reached to the end of all the possible results
            break

    print(f'Total NCIt code(s) retrieved for {ncit_search_term}:', len(all_concepts))
    return all_concepts


def obtain_taxonomy_id(species_search_term):
    url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'

    params = {
        'db': 'taxonomy',
        'term': species_search_term,
        'retmode': 'json'
    }

    r = requests.get(url, params=params)
    data = r.json()

    tax_id = data['esearchresult']['idlist'][0]

    print(f'Taxonomy ID for {species_search_term}: {tax_id}')

    return tax_id


def obtain_all_cell_lines(cell_line_search_term, search_term_type, tax_id=9606, rows_size=1000):
    url = 'https://api.cellosaurus.org/search/cell-line'

    start = 0
    all_cell_lines_data = []

    while True:

        params = {
            'q': f'{search_term_type}:{cell_line_search_term} ox:{tax_id}',
            'start': start,
            'rows': rows_size,
            'format': 'json'
        }

        r = requests.get(url, params=params)
        data = r.json()

        if len(data['Cellosaurus']['cell-line-list']) != 0:
            all_cell_lines_data.extend(data['Cellosaurus']['cell-line-list'])

            print(f'Concepts obtained: {start} to {start + len(data['Cellosaurus']['cell-line-list'])}')

            start += rows_size
        else:
            break

    print(f'Total cell line(s) retrieved for {cell_line_search_term}:', len(all_cell_lines_data))
    return all_cell_lines_data


def warn(cell_line_id, data_field):
    print(f'{cell_line_id} lacks {data_field}')
    return np.nan


def cell_lines_df_clear_save(all_cell_lines_data, save_dir_cell_line_csv):
    cell_line_dict_list = []

    for cell_line_data in all_cell_lines_data:
        cell_line_dict = {}

        cell_line_id = cell_line_data['accession-list'][0]['value']  # This data field will definitely be avaiable

        cell_line_dict['cell_line_id'] = cell_line_id

        # Some cell lines might lack some data fields so the basic ideas for the following lines are like using try blocks on each data field retrieve
        cell_line_dict['age'] = cell_line_data.get('age') or warn(cell_line_id, 'age')
        cell_line_dict['sex'] = cell_line_data.get('sex') or warn(cell_line_id, 'sex')
        cell_line_dict['category'] = cell_line_data.get('category') or warn(cell_line_id, 'category')

        name_list = cell_line_data.get('name-list')
        cell_line_dict['cell_line_name'] = (
            ','.join([name_dict['value'] for name_dict in name_list]) if name_list else warn(cell_line_id, 'name-list')
        )

        species_list = cell_line_data.get('species-list')
        cell_line_dict['species'] = (
            ','.join([species_dict['label'] for species_dict in species_list]) if species_list else warn(
                cell_line_id,
                'species-list')
        )

        organ_list = cell_line_data.get('derived-from-site-list')
        cell_line_dict['organ'] = (
            ','.join([organ_dict['site']['value'] for organ_dict in organ_list]) if organ_list else warn(
                cell_line_id,
                'derived-from-site-list')
        )
        cell_line_dict['site_type'] = (
            ','.join([organ_dict['site']['site-type'] for organ_dict in organ_list]) if organ_list else warn(
                cell_line_id, 'derived-from-site-list')
        )

        disease_list = cell_line_data.get('disease-list')
        cell_line_dict['disease'] = (
            ','.join([disease_dict['label'] for disease_dict in disease_list]) if disease_list else warn(
                cell_line_id,
                'disease-list')
        )

        cell_line_dict_list.append(cell_line_dict)

    cell_line_df = pd.DataFrame(cell_line_dict_list)

    cell_line_df = cell_line_df[[
        'cell_line_id',
        'cell_line_name',
        'organ',
        'site_type',
        'disease',
        'age',
        'sex',
        'category',
        'species'
    ]]  # Reorder the columns

    cell_line_df.to_csv(save_dir_cell_line_csv, index=False)

    return cell_line_df


def extract_cell_line_names(input_cell_line_df):
    cell_line_names = [name for name_list in input_cell_line_df['cell_line_name'] for name in
                       name_list.split(',')]  # Pool all the names into a 1D list
    cell_line_names_stripped = [re.sub(r'[^A-Za-z0-9]', '', name) for name in
                                cell_line_names]  # It seems like the stripped cell line names are just the original names with all the special char and spaces removed

    cell_line_names_total = cell_line_names + cell_line_names_stripped
    cell_line_names_total = list(set(cell_line_names_total))  # Remove duplicated names

    cell_line_names_total.sort()
    return cell_line_names_total


def cell_line_names_to_model_id(cell_line_names, model_df):
    model_df_filtered = model_df[
        model_df["CellLineName"].isin(cell_line_names) |
        model_df["StrippedCellLineName"].isin(cell_line_names)
        ]

    model_df_filtered = model_df_filtered.reset_index(drop=True)
    model_id = model_df_filtered['ModelID'].tolist()

    return model_id


def strip_col_gene_name(col_name):
    match = re.match(r"^(.+?)\s*\(\d+\)$", str(col_name))

    if match:
        return match.group(1)
    else:
        return col_name


def expression_df_filterd_by_cell_lines(whole_expression_df, model_id_cell_lines):
    expression_df_cell_lines = whole_expression_df[whole_expression_df['Unnamed: 0'].isin(model_id_cell_lines)]
    expression_df_cell_lines = expression_df_cell_lines.reset_index(
        drop=True)  # expression_df_cell_lines now contains all the cell lines ModelID and expressed proteins

    expression_df_cell_lines.columns = [strip_col_gene_name(col) for col in
                                        expression_df_cell_lines.columns]  # Clean the col title so expression_df_cell_lines's col now only have the gene name
    expression_df_cell_lines = expression_df_cell_lines.rename(columns={
        'Unnamed: 0': 'ModelID'})  # Rename the first col into 'ModelID'. expression_df_cell_lines now has all the genes expressed by melanoma cell lines

    return expression_df_cell_lines


def expression_df_cell_lines_filtered_by_tf(expression_df_cell_lines, whole_tf_names):
    expression_tf_df_cell_lines = expression_df_cell_lines.loc[:, expression_df_cell_lines.columns.isin(
        whole_tf_names + ['ModelID'])].copy()  # expression_tf_df_cell_lines has all the TF expressed in cell lines

    return expression_tf_df_cell_lines


def expression_tf_df_cell_lines_to_tf_list(expression_tf_df_cell_lines, TPM_LOGP1_threshold, FRACTION_REQUIRED,
                                           cell_name):
    expr_only = expression_tf_df_cell_lines.iloc[:, 1:]  # Exclude the 1st col which are the ModelID

    frac_expressed = (expr_only >= TPM_LOGP1_threshold).sum(axis=0) / expr_only.shape[0]

    expressed_mask = frac_expressed >= FRACTION_REQUIRED
    expressed_tf = expr_only.columns[expressed_mask].tolist()
    expressed_tf = sorted(expressed_tf)

    print(
        f'Found {len(expressed_tf)} TF from JASPAR dataset for TF expressed in specific {cell_name.upper()} cell lines')
    # print(expressed_tf)

    with open(f'input/filters/tf_{cell_name}.pkl', 'wb') as file:
        pickle.dump(expressed_tf, file)
    with open(f'input/filters/tf_{cell_name}.txt', 'w') as file:
        if len(expressed_tf) != 0:
            for tf in expressed_tf:
                file.write(tf + '\n')
        else:
            file.write('')

    print(f'Files saved for names of TF expressed in {cell_name.upper()} cell lines')

    del expressed_tf


def expression_df_to_expression_tf_df_cell_lines(whole_expression_df, model_id_cell_lines, whole_tf_names,
                                                 TPM_LOGP1_threshold, FRACTION_REQUIRED, cell_name):
    expression_df_cell_lines = expression_df_filterd_by_cell_lines(whole_expression_df, model_id_cell_lines)

    expression_tf_df_cell_lines = expression_df_cell_lines_filtered_by_tf(expression_df_cell_lines, whole_tf_names)

    expression_tf_df_cell_lines_to_tf_list(expression_tf_df_cell_lines, TPM_LOGP1_threshold, FRACTION_REQUIRED,
                                           cell_name)

    del expression_df_cell_lines, expression_tf_df_cell_lines
