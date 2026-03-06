import requests
import pandas as pd
import numpy as np


def obtain_jaspar_dataset(ncit_search_term, page_size=500):
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
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

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


def obtain_all_cell_lines(cell_line_search_term, tax_id, rows_size=1000):
    url = "https://api.cellosaurus.org/search/cell-line"

    start = 0
    all_cell_lines_data = []

    while True:

        params = {
            'q': f'di:{cell_line_search_term} ox:{tax_id}',
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


def cell_lines_df_clearing(all_cell_lines_data):
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
    return cell_line_df
