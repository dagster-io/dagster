from sqlalchemy import Column, String


class DataFrameSchema:
    meta__warnings = Column(
        'meta__warnings', String, nullable=True,
        comment="Semi-colon seperated list of data warnings detected in this rows data")

    def get_columns(self):
        columns = []
        for field_name in dir(self):
            field_value = getattr(self, field_name)
            if isinstance(field_value, Column):
                columns.append(field_value)
        return columns

    @staticmethod
    def calculate_data_quality(df_orig):
        df = df_orig.copy()
        df.loc[:, 'meta__warnings'] = ''
        return df
