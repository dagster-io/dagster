import sqlalchemy


def create_redshift_db_url(username, password, hostname, db_name, jdbc=True):
    if jdbc:
        db_url = (
            'jdbc:postgresql://{hostname}:5432/{db_name}?'
            'user={username}&password={password}'.format(
                username=username, password=password, hostname=hostname, db_name=db_name
            )
        )
    else:
        db_url = "redshift_psycopg2://{username}:{password}@{hostname}:5439/{db_name}".format(
            username=username, password=password, hostname=hostname, db_name=db_name
        )
    return db_url


def create_redshift_engine(db_url):
    return sqlalchemy.create_engine(db_url)


def create_postgres_db_url(username, password, hostname, db_name, jdbc=True):
    if jdbc:
        db_url = (
            'jdbc:postgresql://{hostname}:5432/{db_name}?'
            'user={username}&password={password}'.format(
                username=username, password=password, hostname=hostname, db_name=db_name
            )
        )
    else:
        db_url = 'postgresql://{username}:{password}@{hostname}:5432/{db_name}'.format(
            username=username, password=password, hostname=hostname, db_name=db_name
        )
    return db_url


def create_postgres_engine(db_url):
    return sqlalchemy.create_engine(db_url)
