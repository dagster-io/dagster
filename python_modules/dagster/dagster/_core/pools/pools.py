import logging
import os

from sqlalchemy import (BigInteger, create_engine, Column, String,
                        ForeignKey)
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import declarative_base, relationship, Session
from tenacity import (retry, retry_if_exception_type, wait_exponential, stop_after_attempt,
                      before_sleep_log, retry_if_exception)
from psycopg2.errors import LockNotAvailable
from sqlalchemy.exc import OperationalError


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if bool(os.environ.get("DEBUG", False)):
    logger.setLevel(logging.DEBUG)


host = (f"postgresql://{os.environ['DAGSTER_POSTGRES_USER']}:{os.environ['DAGSTER_POSTGRES_PASSWORD']}"
        f"@{os.environ.get('DAGSTER_POSTGRES_HOSTNAME', 'docker_example_postgresql')}:5432/{os.environ['DAGSTER_POSTGRES_DB']}")

engine = create_engine(host, echo=True, future=True)
Base = declarative_base()

class Pools(Base):
	__tablename__ = "pools"

	name = Column(String(255), primary_key=True)
	total_slots = Column(BigInteger())
	occupied_slot = relationship("OccupiedSlots", back_populates="pool", cascade="all", uselist=False)


class OccupiedSlots(Base):
	__tablename__ = "occupied_slots"

	name = Column(String(255), ForeignKey("pools.name"), primary_key=True)
	occupied_slots = Column(BigInteger())
	pool = relationship("Pools", back_populates="occupied_slot", uselist=False)


def populate_pools(engine, pools):
	""" Populates pool table based on config. Idempotent action. """
	with Session(engine) as session:         
		for pool in pools:
			pool_name = pool["name"]
			total_slots = pool["total_slots"]

			pool = session.query(Pools).filter_by(name=pool_name).first()

			if pool is None:
				occupied_slot = OccupiedSlots(occupied_slots=0)
				pool = Pools(name=pool_name, total_slots=total_slots, occupied_slot=occupied_slot)
			else:
				pool.total_slots = total_slots

			session.add(pool)

		deleted_pool_names  = {pool.name for pool in session.query(Pools.name).all()} - {pool["name"] for pool in pools}
		for deleted_pool_name in deleted_pool_names:
			# Remove pools which have been removed. Cascades deletion to occupied slots table.
			session.delete(session.query(Pools).filter_by(name=deleted_pool_name).first())

		session.commit()


@retry(retry=retry_if_exception(
            lambda exc: isinstance(exc, OperationalError)
            and not isinstance(exc.orig, LockNotAvailable)),
        wait=wait_exponential(), stop=stop_after_attempt(11),
        before_sleep=before_sleep_log(logger, logging.WARN))
def increment_pool(pool_name, engine):
	""" Increments pool in one transaction. """
	with Session(engine) as session:
		occupied_pool_stat = session.query(OccupiedSlots).filter(OccupiedSlots.name==pool_name) \
			.with_for_update(nowait=True).one()
		total_pool = session.query(Pools).filter(Pools.name==pool_name).one()
		if occupied_pool_stat.occupied_slots > total_pool.total_slots:
			raise RuntimeError("Occupied slots greater than total slots")

		if occupied_pool_stat.occupied_slots < total_pool.total_slots:
			occupied_pool_stat.occupied_slots += 1
			session.commit()
			return True

		session.commit()
		return False


@retry(retry=retry_if_exception_type((OperationalError)),
        wait=wait_exponential(), stop=stop_after_attempt(11),
        before_sleep=before_sleep_log(logger, logging.WARN))
def decrement_pool(pool_name, engine):
	""" Decrements pool in one transaction """
	with Session(engine) as session:
		# Will hang until the lock from increment is released then execute
		session.query(OccupiedSlots).filter(OccupiedSlots.name==pool_name) \
			.update({"occupied_slots": OccupiedSlots.occupied_slots - 1})
		session.commit()


# We use a K8s deployment, so this function gets called as an
# init container - setting up the tables for the pools
def main():
    pools = [
        {"name": "example_pool_1", "total_slots": 10},
        {"name": "example_pool_2", "total_slots": 2},
    ]
    Base.metadata.create_all(engine)
    populate_pools(engine, pools)


if __name__ == "__main__":
    main()
