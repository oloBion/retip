import numpy as np
import pandas as pd
import tqdm

from typing import Union

from mordred import Calculator, descriptors
from rdkit import Chem
from sklearn.model_selection import train_test_split


class Dataset:
    NAME_COLUMN = 'Name'
    RT_COLUMN = 'RT'
    IDENTIFIER_COLUMNS = ['PubChem CID', 'SMILES']

    def __init__(self, data: Union[str, pd.DataFrame], test_size: float = 0.2, seed: int = None, sheet_name: str = None):
        # load and validate data set
        self._load_dataframe(data, sheet_name)

        self.seed = seed
        self.test_size = test_size
        self.data = None

        # create mordred calculator
        self.calc = Calculator(descriptors, ignore_3D=True)
        self.descriptor_names = [str(d) for d in self.calc.descriptors]


    def _load_dataframe(self, data: Union[str, pd.DataFrame], sheet_name: str = None):
        """
        """

        if isinstance(data, str):
            if data.lower().endswith('.csv'):
                self.df = pd.read_csv(data)
            elif data.lower().endswith('.xls') or data.lower().endswith('.xlsx'):
                self.df = pd.read_excel(data, sheet_name=sheet_name)
            else:
                extension = data.split('.')[-1]
                raise Exception(f'{extension} is not a supported data format')

        elif isinstance(data, pd.DataFrame):
            self.df = data

        else:
            raise Exception(f'{type(data)} is not a supported data type')

        self._validate_dataframe()

    def _validate_dataframe(self):
        """
        """

        # ensure that the data frame contains required columns
        if self.NAME_COLUMN not in self.df.columns:
            raise Exception(f'{self.NAME_COLUMN} column was not found in the data frame')

        if self.RT_COLUMN not in self.df.columns:
            raise Exception(f'{self.RT_COLUMN} column was not found in the data frame')

        if not any(x in self.df.columns for x in self.IDENTIFIER_COLUMNS):
            valid_columns = ', '.join(self.IDENTIFIER_COLUMNS)
            raise Exception(f'No identifier columns were not found in the data frame: {valid_columns}')

    def head(self):
        """
        """

        return self.df.head()

    def describe(self):
        """
        """

        print('Shape:', self.df.shape)
        print(self.df[self.df.columns.difference(self.descriptor_names)].describe())


    def load_structures(self):
        """
        """


    def calculate_descriptors(self):
        """
        """

        assert('SMILES' in self.df.columns)

        if all(d in self.df.columns for d in self.descriptor_names):
            print('Skipping molecular descriptor calculation, descriptors have already been calculated')
            return

        descs = []
        smiles = set(self.df.SMILES)

        print(f'Calculating descriptors for {len(smiles)} structures')

        for smi in tqdm.tqdm(smiles):
            try:
                mol = Chem.MolFromSmiles(smi)

                desc = self.calc(mol)
                desc = desc.fill_missing()

                desc = desc.asdict()
                desc['SMILES'] = smi

                descs.append(desc)
            except:
                print(f'Parsing SMILES {smi} failed')

        descs = pd.DataFrame(descs)
        self.df = pd.merge(self.df, descs, how='left', on='SMILES')


    def build_dataset(self):
        if not all(d in self.df.columns for d in self.descriptor_names):
            self.calculate_descriptors()
        
        self.data = self.df[[self.RT_COLUMN] + self.descriptor_names]
        self.data = self.data.dropna(how='all', subset=self.descriptor_names)
        self.data = self.data.dropna(how='any', axis=1)

        if self.test_size > 0:
            self.training_data, self.test_data = train_test_split(self.data, test_size=self.test_size, random_state=self.seed)
        else:
            self.training_data, self.test_data = self.data, self.data.loc[[]]
    
    def save_dataset(self, filename: str, include_descriptors: bool = True):
        if include_descriptors:
            output = self.df
        else:
            output = self.df[self.df.columns.difference(self.descriptor_names)]

        if filename.lower().endswith('.csv'):
            output.to_csv(filename, index=False)
        elif filename.lower().endswith('.xls') or filename.lower().endswith('.xlsx'):
            output.to_excel(filename, index=False)
        else:
            extension = filename.split('.')[-1]
            raise Exception(f'{extension} is not a supported data format')

        print(f'Saved dataset to {filename}')


    def get_data(self):
        if self.data is None:
            self.build_dataset()

        return self.data

    def get_training_data(self):
        if self.data is None:
            self.build_dataset()
        
        return self.training_data
    
    def get_test_data(self):
        if self.data is None:
            self.build_dataset()
        
        return self.test_data
