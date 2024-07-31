from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from random import Random
from typing import Sequence, Union

from dagster import ConfigurableResource
from faker import Faker
from pydantic import Field

# This file holds a resource you'll use in the tutorial
# You won't need to use this file/class until the Connecting to External Services section of the tutorial (Part 8).
# Once you are on Part 8, you will the contents of this file, but you don't need to understand the underlying code.


# To the curious user: This is the underlying code to generate the signups
@dataclass
class Signup:
    name: str
    email: str
    country: str
    signup_source: str
    referral: str
    signup_purpose: str
    subscription_level: str
    payment_method: str
    sso_id: str
    email_verified: bool
    enabled: bool
    registered_at: datetime

    def to_dict(self) -> dict:
        props = {k: v for k, v in asdict(self).items() if not k.startswith("_")}
        props["registered_at"] = self.registered_at.isoformat()
        return props

    def properties(self):
        return (
            self.name,
            self.email,
            self.country,
            self.signup_source,
            self.referral,
            self.signup_purpose,
            self.subscription_level,
            self.payment_method,
            self.sso_id,
            self.email_verified,
            self.enabled,
            self.registered_at,
        )

    def __eq__(self, other):
        if type(other) is type(self):
            return self.properties() == other.properties()
        else:
            return False

    def __hash__(self):
        return hash(self.properties())

    def __getitem__(self, key):
        return getattr(self, key)


class DataGenerator:
    def __init__(self, seed: int = 0):
        self.seed = seed
        self.fake = Faker()
        self.random = Random(seed)

    def generate_signup(self, date) -> Signup:
        registered_at = self.fake.date_time_between_dates(date, date + timedelta(days=1))

        return Signup(
            name=self.fake.name(),
            email=self.fake.email(),
            country=self.fake.country(),
            signup_source=self.fake.random_element(["google", "facebook", "twitter", "other"]),
            referral=self.fake.uri(),
            signup_purpose=self.fake.random_element(["personal", "business", "education", "other"]),
            subscription_level=self.fake.random_element(["trial", "free", "premium", "enterprise"]),
            payment_method=self.fake.random_element(["credit_card", "paypal", "check", "other"]),
            sso_id=self.fake.uuid4(),
            email_verified=self.fake.boolean(),
            enabled=self.fake.boolean(),
            registered_at=registered_at,
        )

    def get_signups_for_date(self, date: datetime) -> Sequence[Signup]:
        date_to_seed = date.strftime("%Y%m%d")
        Faker.seed(date_to_seed)
        self.random = Random(date_to_seed)

        signups = []
        num_signups = self.random.randint(25, 100)

        for i in range(num_signups):
            signup = self.generate_signup(date)
            signups.append(signup.to_dict())

        new_seed = self.random.randint(0, 100000)
        Faker.seed(new_seed)
        self.random = Random(new_seed)
        return sorted(signups, key=lambda x: x["registered_at"])

    def get_signups_for_dates(
        self, start_date: datetime, end_date: Union[datetime, None] = None
    ) -> Sequence[Signup]:
        signups = []

        end_date_to_use = end_date or (datetime.now() - timedelta(days=1))
        current_date = start_date

        while current_date < end_date_to_use:
            signups.extend(self.get_signups_for_date(current_date))
            current_date += timedelta(days=1)

        return signups

    def get_signups(self, num_days: int = 7) -> Sequence[Signup]:
        start_date = datetime.now() - timedelta(days=num_days)

        return self.get_signups_for_dates(start_date)


class DataGeneratorResource(ConfigurableResource):
    """Resource for generating simulated data for experimenting with Dagster.

    Examples:
        .. code-block:: python
            from dagster import Definitions, asset
            from dagster_data_generator import DataGeneratorResource, DataGeneratorConfig

            @asset
            def my_table(data_gen: DataGeneratorConfig):
                return data_gen.get_signups()

            defs = Definitions(
                assets=[my_table],
                resources={"data_gen": DataGeneratorResource()}
            )
    """

    seed: int = Field(
        description=(
            "Seed for the random number generator. If not provided, a static seed will be used."
        ),
        default=0,
    )

    num_days: int = Field(
        description="Number of days to generate data for. Defaults to 7", default=7
    )

    @property
    def generator(self) -> DataGenerator:
        return DataGenerator(self.seed)

    def get_signups(self):
        result = []
        today = datetime.now()

        for i in range(self.num_days):
            yday = today - timedelta(days=i)
            result.extend(self.generator.get_signups_for_date(yday))

        return result

    def get_signups_for_date(self, date: str):
        date_obj = datetime.strptime(date, "%m-%d-%Y")
        return self.generator.get_signups_for_date(date_obj)
