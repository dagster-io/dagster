# ruff: noqa: A001, A002
from typing import List, Optional, Union

import dagster._check as check
from dagster._annotations import public

from dagster_airbyte.managed.types import GeneratedAirbyteSource


class StravaSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        athlete_id: int,
        start_date: str,
        auth_type: Optional[str] = None,
    ):
        """Airbyte Source for Strava.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/strava

        Args:
            name (str): The name of the destination.
            client_id (str): The Client ID of your Strava developer application.
            client_secret (str): The Client Secret of your Strava developer application.
            refresh_token (str): The Refresh Token with the activity: read_all permissions.
            athlete_id (int): The Athlete ID of your Strava developer application.
            start_date (str): UTC date and time. Any data before this date will not be replicated.
        """
        self.auth_type = check.opt_str_param(auth_type, "auth_type")
        self.client_id = check.str_param(client_id, "client_id")
        self.client_secret = check.str_param(client_secret, "client_secret")
        self.refresh_token = check.str_param(refresh_token, "refresh_token")
        self.athlete_id = check.int_param(athlete_id, "athlete_id")
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Strava", name)


class AppsflyerSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        app_id: str,
        api_token: str,
        start_date: str,
        timezone: Optional[str] = None,
    ):
        """Airbyte Source for Appsflyer.

        Args:
            name (str): The name of the destination.
            app_id (str): App identifier as found in AppsFlyer.
            api_token (str): Pull API token for authentication. If you change the account admin, the token changes, and you must update scripts with the new token. Get the API token in the Dashboard.
            start_date (str): The default value to use if no bookmark exists for an endpoint. Raw Reports historical lookback is limited to 90 days.
            timezone (Optional[str]): Time zone in which date times are stored. The project timezone may be found in the App settings in the AppsFlyer console.
        """
        self.app_id = check.str_param(app_id, "app_id")
        self.api_token = check.str_param(api_token, "api_token")
        self.start_date = check.str_param(start_date, "start_date")
        self.timezone = check.opt_str_param(timezone, "timezone")
        super().__init__("Appsflyer", name)


class GoogleWorkspaceAdminReportsSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self, name: str, credentials_json: str, email: str, lookback: Optional[int] = None
    ):
        """Airbyte Source for Google Workspace Admin Reports.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/google-workspace-admin-reports

        Args:
            name (str): The name of the destination.
            credentials_json (str): The contents of the JSON service account key. See the docs for more information on how to generate this key.
            email (str): The email of the user, who has permissions to access the Google Workspace Admin APIs.
            lookback (Optional[int]): Sets the range of time shown in the report. The maximum value allowed by the Google API is 180 days.
        """
        self.credentials_json = check.str_param(credentials_json, "credentials_json")
        self.email = check.str_param(email, "email")
        self.lookback = check.opt_int_param(lookback, "lookback")
        super().__init__("Google Workspace Admin Reports", name)


class CartSource(GeneratedAirbyteSource):
    class CentralAPIRouter:
        @public
        def __init__(self, user_name: str, user_secret: str, site_id: str):
            self.auth_type = "CENTRAL_API_ROUTER"
            self.user_name = check.str_param(user_name, "user_name")
            self.user_secret = check.str_param(user_secret, "user_secret")
            self.site_id = check.str_param(site_id, "site_id")

    class SingleStoreAccessToken:
        @public
        def __init__(self, access_token: str, store_name: str):
            self.auth_type = "SINGLE_STORE_ACCESS_TOKEN"
            self.access_token = check.str_param(access_token, "access_token")
            self.store_name = check.str_param(store_name, "store_name")

    @public
    def __init__(
        self,
        name: str,
        credentials: Union["CartSource.CentralAPIRouter", "CartSource.SingleStoreAccessToken"],
        start_date: str,
    ):
        """Airbyte Source for Cart.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/cart

        Args:
            name (str): The name of the destination.
            start_date (str): The date from which you'd like to replicate the data
        """
        self.credentials = check.inst_param(
            credentials,
            "credentials",
            (CartSource.CentralAPIRouter, CartSource.SingleStoreAccessToken),
        )
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Cart", name)


class LinkedinAdsSource(GeneratedAirbyteSource):
    class OAuth20:
        @public
        def __init__(
            self,
            client_id: str,
            client_secret: str,
            refresh_token: str,
            auth_method: Optional[str] = None,
        ):
            self.auth_method = check.opt_str_param(auth_method, "auth_method")
            self.client_id = check.str_param(client_id, "client_id")
            self.client_secret = check.str_param(client_secret, "client_secret")
            self.refresh_token = check.str_param(refresh_token, "refresh_token")

    class AccessToken:
        @public
        def __init__(self, access_token: str, auth_method: Optional[str] = None):
            self.auth_method = check.opt_str_param(auth_method, "auth_method")
            self.access_token = check.str_param(access_token, "access_token")

    @public
    def __init__(
        self,
        name: str,
        credentials: Union["LinkedinAdsSource.OAuth20", "LinkedinAdsSource.AccessToken"],
        start_date: str,
        account_ids: Optional[List[int]] = None,
    ):
        """Airbyte Source for Linkedin Ads.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/linkedin-ads

        Args:
            name (str): The name of the destination.
            start_date (str): UTC date in the format 2020-09-17. Any data before this date will not be replicated.
            account_ids (Optional[List[int]]): Specify the account IDs separated by a space, to pull the data from. Leave empty, if you want to pull the data from all associated accounts. See the LinkedIn Ads docs for more info.
        """
        self.credentials = check.inst_param(
            credentials, "credentials", (LinkedinAdsSource.OAuth20, LinkedinAdsSource.AccessToken)
        )
        self.start_date = check.str_param(start_date, "start_date")
        self.account_ids = check.opt_nullable_list_param(account_ids, "account_ids", int)
        super().__init__("Linkedin Ads", name)


class MongodbSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        auth_source: str,
        replica_set: Optional[str] = None,
        ssl: Optional[bool] = None,
    ):
        """Airbyte Source for Mongodb.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/mongodb

        Args:
            name (str): The name of the destination.
            host (str): Host of a Mongo database to be replicated.
            port (int): Port of a Mongo database to be replicated.
            database (str): Database to be replicated.
            user (str): User
            password (str): Password
            auth_source (str): Authentication source where user information is stored. See  the Mongo docs for more info.
            replica_set (Optional[str]): The name of the set to filter servers by, when connecting to a replica set (Under this condition, the 'TLS connection' value automatically becomes 'true'). See  the Mongo docs  for more info.
            ssl (Optional[bool]): If this switch is enabled, TLS connections will be used to connect to MongoDB.
        """
        self.host = check.str_param(host, "host")
        self.port = check.int_param(port, "port")
        self.database = check.str_param(database, "database")
        self.user = check.str_param(user, "user")
        self.password = check.str_param(password, "password")
        self.auth_source = check.str_param(auth_source, "auth_source")
        self.replica_set = check.opt_str_param(replica_set, "replica_set")
        self.ssl = check.opt_bool_param(ssl, "ssl")
        super().__init__("Mongodb", name)


class TimelySource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, account_id: str, start_date: str, bearer_token: str):
        """Airbyte Source for Timely.

        Args:
            name (str): The name of the destination.
            account_id (str): Timely account id
            start_date (str): start date
            bearer_token (str): Timely bearer token
        """
        self.account_id = check.str_param(account_id, "account_id")
        self.start_date = check.str_param(start_date, "start_date")
        self.bearer_token = check.str_param(bearer_token, "bearer_token")
        super().__init__("Timely", name)


class StockTickerApiTutorialSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, stock_ticker: str, api_key: str):
        """Airbyte Source for Stock Ticker Api Tutorial.

        Documentation can be found at https://polygon.io/docs/stocks/get_v2_aggs_grouped_locale_us_market_stocks__date

        Args:
            name (str): The name of the destination.
            stock_ticker (str): The stock ticker to track
            api_key (str): The Polygon.io Stocks API key to use to hit the API.
        """
        self.stock_ticker = check.str_param(stock_ticker, "stock_ticker")
        self.api_key = check.str_param(api_key, "api_key")
        super().__init__("Stock Ticker Api Tutorial", name)


class WrikeSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self, name: str, access_token: str, wrike_instance: str, start_date: Optional[str] = None
    ):
        """Airbyte Source for Wrike.

        Args:
            name (str): The name of the destination.
            access_token (str): Permanent access token. You can find documentation on how to acquire a permanent access token  here
            wrike_instance (str): Wrike's instance such as `app-us2.wrike.com`
            start_date (Optional[str]): UTC date and time in the format 2017-01-25T00:00:00Z. Only comments after this date will be replicated.
        """
        self.access_token = check.str_param(access_token, "access_token")
        self.wrike_instance = check.str_param(wrike_instance, "wrike_instance")
        self.start_date = check.opt_str_param(start_date, "start_date")
        super().__init__("Wrike", name)


class CommercetoolsSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        region: str,
        host: str,
        start_date: str,
        project_key: str,
        client_id: str,
        client_secret: str,
    ):
        """Airbyte Source for Commercetools.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/commercetools

        Args:
            name (str): The name of the destination.
            region (str): The region of the platform.
            host (str): The cloud provider your shop is hosted. See: https://docs.commercetools.com/api/authorization
            start_date (str): The date you would like to replicate data. Format: YYYY-MM-DD.
            project_key (str): The project key
            client_id (str): Id of API Client.
            client_secret (str): The password of secret of API Client.
        """
        self.region = check.str_param(region, "region")
        self.host = check.str_param(host, "host")
        self.start_date = check.str_param(start_date, "start_date")
        self.project_key = check.str_param(project_key, "project_key")
        self.client_id = check.str_param(client_id, "client_id")
        self.client_secret = check.str_param(client_secret, "client_secret")
        super().__init__("Commercetools", name)


class GutendexSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        author_year_start: Optional[str] = None,
        author_year_end: Optional[str] = None,
        copyright: Optional[str] = None,
        languages: Optional[str] = None,
        search: Optional[str] = None,
        sort: Optional[str] = None,
        topic: Optional[str] = None,
    ):
        """Airbyte Source for Gutendex.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/gutendex

        Args:
            name (str): The name of the destination.
            author_year_start (Optional[str]): (Optional) Defines the minimum birth year of the authors. Books by authors born prior to the start year will not be returned. Supports both positive (CE) or negative (BCE) integer values
            author_year_end (Optional[str]): (Optional) Defines the maximum birth year of the authors. Books by authors born after the end year will not be returned. Supports both positive (CE) or negative (BCE) integer values
            copyright (Optional[str]): (Optional) Use this to find books with a certain copyright status - true for books with existing copyrights, false for books in the public domain in the USA, or null for books with no available copyright information.
            languages (Optional[str]): (Optional) Use this to find books in any of a list of languages. They must be comma-separated, two-character language codes.
            search (Optional[str]): (Optional) Use this to search author names and book titles with given words. They must be separated by a space (i.e. %20 in URL-encoded format) and are case-insensitive.
            sort (Optional[str]): (Optional) Use this to sort books - ascending for Project Gutenberg ID numbers from lowest to highest, descending for IDs highest to lowest, or popular (the default) for most popular to least popular by number of downloads.
            topic (Optional[str]): (Optional) Use this to search for a case-insensitive key-phrase in books' bookshelves or subjects.
        """
        self.author_year_start = check.opt_str_param(author_year_start, "author_year_start")
        self.author_year_end = check.opt_str_param(author_year_end, "author_year_end")
        self.copyright = check.opt_str_param(copyright, "copyright")
        self.languages = check.opt_str_param(languages, "languages")
        self.search = check.opt_str_param(search, "search")
        self.sort = check.opt_str_param(sort, "sort")
        self.topic = check.opt_str_param(topic, "topic")
        super().__init__("Gutendex", name)


class IterableSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, api_key: str, start_date: str):
        """Airbyte Source for Iterable.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/iterable

        Args:
            name (str): The name of the destination.
            api_key (str): Iterable API Key. See the docs for more information on how to obtain this key.
            start_date (str): The date from which you'd like to replicate data for Iterable, in the format YYYY-MM-DDT00:00:00Z. All data generated after this date will be replicated.
        """
        self.api_key = check.str_param(api_key, "api_key")
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Iterable", name)


class QuickbooksSingerSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        realm_id: str,
        user_agent: str,
        start_date: str,
        sandbox: bool,
    ):
        """Airbyte Source for Quickbooks Singer.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/quickbooks

        Args:
            name (str): The name of the destination.
            client_id (str): Identifies which app is making the request. Obtain this value from the Keys tab on the app profile via My Apps on the developer site. There are two versions of this key: development and production.
            client_secret (str):  Obtain this value from the Keys tab on the app profile via My Apps on the developer site. There are two versions of this key: development and production.
            refresh_token (str): A token used when refreshing the access token.
            realm_id (str): Labeled Company ID. The Make API Calls panel is populated with the realm id and the current access token.
            user_agent (str): Process and email for API logging purposes. Example: tap-quickbooks .
            start_date (str): The default value to use if no bookmark exists for an endpoint (rfc3339 date string). E.g, 2021-03-20T00:00:00Z. Any data before this date will not be replicated.
            sandbox (bool): Determines whether to use the sandbox or production environment.
        """
        self.client_id = check.str_param(client_id, "client_id")
        self.client_secret = check.str_param(client_secret, "client_secret")
        self.refresh_token = check.str_param(refresh_token, "refresh_token")
        self.realm_id = check.str_param(realm_id, "realm_id")
        self.user_agent = check.str_param(user_agent, "user_agent")
        self.start_date = check.str_param(start_date, "start_date")
        self.sandbox = check.bool_param(sandbox, "sandbox")
        super().__init__("Quickbooks Singer", name)


class BigcommerceSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, start_date: str, store_hash: str, access_token: str):
        """Airbyte Source for Bigcommerce.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/bigcommerce

        Args:
            name (str): The name of the destination.
            start_date (str): The date you would like to replicate data. Format: YYYY-MM-DD.
            store_hash (str): The hash code of the store. For https://api.bigcommerce.com/stores/HASH_CODE/v3/, The store's hash code is 'HASH_CODE'.
            access_token (str): Access Token for making authenticated requests.
        """
        self.start_date = check.str_param(start_date, "start_date")
        self.store_hash = check.str_param(store_hash, "store_hash")
        self.access_token = check.str_param(access_token, "access_token")
        super().__init__("Bigcommerce", name)


class ShopifySource(GeneratedAirbyteSource):
    class APIPassword:
        @public
        def __init__(self, api_password: str):
            self.auth_method = "api_password"
            self.api_password = check.str_param(api_password, "api_password")

    class OAuth20:
        @public
        def __init__(
            self,
            client_id: Optional[str] = None,
            client_secret: Optional[str] = None,
            access_token: Optional[str] = None,
        ):
            self.auth_method = "oauth2.0"
            self.client_id = check.opt_str_param(client_id, "client_id")
            self.client_secret = check.opt_str_param(client_secret, "client_secret")
            self.access_token = check.opt_str_param(access_token, "access_token")

    @public
    def __init__(
        self,
        name: str,
        shop: str,
        credentials: Union["ShopifySource.APIPassword", "ShopifySource.OAuth20"],
        start_date: str,
    ):
        """Airbyte Source for Shopify.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/shopify

        Args:
            name (str): The name of the destination.
            shop (str): The name of your Shopify store found in the URL. For example, if your URL was https://NAME.myshopify.com, then the name would be 'NAME'.
            credentials (Union[ShopifySource.APIPassword, ShopifySource.OAuth20]): The authorization method to use to retrieve data from Shopify
            start_date (str): The date you would like to replicate data from. Format: YYYY-MM-DD. Any data before this date will not be replicated.
        """
        self.shop = check.str_param(shop, "shop")
        self.credentials = check.inst_param(
            credentials, "credentials", (ShopifySource.APIPassword, ShopifySource.OAuth20)
        )
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Shopify", name)


class AppstoreSingerSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self, name: str, key_id: str, private_key: str, issuer_id: str, vendor: str, start_date: str
    ):
        """Airbyte Source for Appstore Singer.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/appstore

        Args:
            name (str): The name of the destination.
            key_id (str): Appstore Key ID. See the docs for more information on how to obtain this key.
            private_key (str): Appstore Private Key. See the docs for more information on how to obtain this key.
            issuer_id (str): Appstore Issuer ID. See the docs for more information on how to obtain this ID.
            vendor (str): Appstore Vendor ID. See the docs for more information on how to obtain this ID.
            start_date (str): UTC date and time in the format 2017-01-25T00:00:00Z. Any data before this date will not be replicated.
        """
        self.key_id = check.str_param(key_id, "key_id")
        self.private_key = check.str_param(private_key, "private_key")
        self.issuer_id = check.str_param(issuer_id, "issuer_id")
        self.vendor = check.str_param(vendor, "vendor")
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Appstore Singer", name)


class GreenhouseSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, api_key: str):
        """Airbyte Source for Greenhouse.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/greenhouse

        Args:
            name (str): The name of the destination.
            api_key (str): Greenhouse API Key. See the docs for more information on how to generate this key.
        """
        self.api_key = check.str_param(api_key, "api_key")
        super().__init__("Greenhouse", name)


class ZoomSingerSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, jwt: str):
        """Airbyte Source for Zoom Singer.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/zoom

        Args:
            name (str): The name of the destination.
            jwt (str): Zoom JWT Token. See the docs for more information on how to obtain this key.
        """
        self.jwt = check.str_param(jwt, "jwt")
        super().__init__("Zoom Singer", name)


class TiktokMarketingSource(GeneratedAirbyteSource):
    class OAuth20:
        @public
        def __init__(
            self, app_id: str, secret: str, access_token: str, auth_type: Optional[str] = None
        ):
            self.auth_type = check.opt_str_param(auth_type, "auth_type")
            self.app_id = check.str_param(app_id, "app_id")
            self.secret = check.str_param(secret, "secret")
            self.access_token = check.str_param(access_token, "access_token")

    class SandboxAccessToken:
        @public
        def __init__(self, advertiser_id: str, access_token: str, auth_type: Optional[str] = None):
            self.auth_type = check.opt_str_param(auth_type, "auth_type")
            self.advertiser_id = check.str_param(advertiser_id, "advertiser_id")
            self.access_token = check.str_param(access_token, "access_token")

    @public
    def __init__(
        self,
        name: str,
        credentials: Union[
            "TiktokMarketingSource.OAuth20", "TiktokMarketingSource.SandboxAccessToken"
        ],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        report_granularity: Optional[str] = None,
    ):
        """Airbyte Source for Tiktok Marketing.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/tiktok-marketing

        Args:
            name (str): The name of the destination.
            credentials (Union[TiktokMarketingSource.OAuth20, TiktokMarketingSource.SandboxAccessToken]): Authentication method
            start_date (Optional[str]): The Start Date in format: YYYY-MM-DD. Any data before this date will not be replicated. If this parameter is not set, all data will be replicated.
            end_date (Optional[str]): The date until which you'd like to replicate data for all incremental streams, in the format YYYY-MM-DD. All data generated between start_date and this date will be replicated. Not setting this option will result in always syncing the data till the current date.
            report_granularity (Optional[str]): The granularity used for aggregating performance data in reports. See the docs.
        """
        self.credentials = check.inst_param(
            credentials,
            "credentials",
            (TiktokMarketingSource.OAuth20, TiktokMarketingSource.SandboxAccessToken),
        )
        self.start_date = check.opt_str_param(start_date, "start_date")
        self.end_date = check.opt_str_param(end_date, "end_date")
        self.report_granularity = check.opt_str_param(report_granularity, "report_granularity")
        super().__init__("Tiktok Marketing", name)


class ZendeskChatSource(GeneratedAirbyteSource):
    class OAuth20:
        @public
        def __init__(
            self,
            client_id: Optional[str] = None,
            client_secret: Optional[str] = None,
            access_token: Optional[str] = None,
            refresh_token: Optional[str] = None,
        ):
            self.credentials = "oauth2.0"
            self.client_id = check.opt_str_param(client_id, "client_id")
            self.client_secret = check.opt_str_param(client_secret, "client_secret")
            self.access_token = check.opt_str_param(access_token, "access_token")
            self.refresh_token = check.opt_str_param(refresh_token, "refresh_token")

    class AccessToken:
        @public
        def __init__(self, access_token: str):
            self.credentials = "access_token"
            self.access_token = check.str_param(access_token, "access_token")

    @public
    def __init__(
        self,
        name: str,
        start_date: str,
        credentials: Union["ZendeskChatSource.OAuth20", "ZendeskChatSource.AccessToken"],
        subdomain: Optional[str] = None,
    ):
        """Airbyte Source for Zendesk Chat.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/zendesk-chat

        Args:
            name (str): The name of the destination.
            start_date (str): The date from which you'd like to replicate data for Zendesk Chat API, in the format YYYY-MM-DDT00:00:00Z.
            subdomain (Optional[str]): Required if you access Zendesk Chat from a Zendesk Support subdomain.
        """
        self.start_date = check.str_param(start_date, "start_date")
        self.subdomain = check.opt_str_param(subdomain, "subdomain")
        self.credentials = check.inst_param(
            credentials, "credentials", (ZendeskChatSource.OAuth20, ZendeskChatSource.AccessToken)
        )
        super().__init__("Zendesk Chat", name)


class AwsCloudtrailSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self, name: str, aws_key_id: str, aws_secret_key: str, aws_region_name: str, start_date: str
    ):
        """Airbyte Source for Aws Cloudtrail.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/aws-cloudtrail

        Args:
            name (str): The name of the destination.
            aws_key_id (str): AWS CloudTrail Access Key ID. See the docs for more information on how to obtain this key.
            aws_secret_key (str): AWS CloudTrail Access Key ID. See the docs for more information on how to obtain this key.
            aws_region_name (str): The default AWS Region to use, for example, us-west-1 or us-west-2. When specifying a Region inline during client initialization, this property is named region_name.
            start_date (str): The date you would like to replicate data. Data in AWS CloudTrail is available for last 90 days only. Format: YYYY-MM-DD.
        """
        self.aws_key_id = check.str_param(aws_key_id, "aws_key_id")
        self.aws_secret_key = check.str_param(aws_secret_key, "aws_secret_key")
        self.aws_region_name = check.str_param(aws_region_name, "aws_region_name")
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Aws Cloudtrail", name)


class OktaSource(GeneratedAirbyteSource):
    class OAuth20:
        @public
        def __init__(self, client_id: str, client_secret: str, refresh_token: str):
            self.auth_type = "oauth2.0"
            self.client_id = check.str_param(client_id, "client_id")
            self.client_secret = check.str_param(client_secret, "client_secret")
            self.refresh_token = check.str_param(refresh_token, "refresh_token")

    class APIToken:
        @public
        def __init__(self, api_token: str):
            self.auth_type = "api_token"
            self.api_token = check.str_param(api_token, "api_token")

    @public
    def __init__(
        self,
        name: str,
        credentials: Union["OktaSource.OAuth20", "OktaSource.APIToken"],
        domain: Optional[str] = None,
        start_date: Optional[str] = None,
    ):
        """Airbyte Source for Okta.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/okta

        Args:
            name (str): The name of the destination.
            domain (Optional[str]): The Okta domain. See the docs for instructions on how to find it.
            start_date (Optional[str]): UTC date and time in the format YYYY-MM-DDTHH:MM:SSZ. Any data before this date will not be replicated.
        """
        self.domain = check.opt_str_param(domain, "domain")
        self.start_date = check.opt_str_param(start_date, "start_date")
        self.credentials = check.inst_param(
            credentials, "credentials", (OktaSource.OAuth20, OktaSource.APIToken)
        )
        super().__init__("Okta", name)


class InsightlySource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, token: Optional[str] = None, start_date: Optional[str] = None):
        """Airbyte Source for Insightly.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/insightly

        Args:
            name (str): The name of the destination.
            token (Optional[str]): Your Insightly API token.
            start_date (Optional[str]): The date from which you'd like to replicate data for Insightly in the format YYYY-MM-DDT00:00:00Z. All data generated after this date will be replicated. Note that it will be used only for incremental streams.
        """
        self.token = check.opt_str_param(token, "token")
        self.start_date = check.opt_str_param(start_date, "start_date")
        super().__init__("Insightly", name)


class LinkedinPagesSource(GeneratedAirbyteSource):
    class OAuth20:
        @public
        def __init__(
            self,
            client_id: str,
            client_secret: str,
            refresh_token: str,
            auth_method: Optional[str] = None,
        ):
            self.auth_method = check.opt_str_param(auth_method, "auth_method")
            self.client_id = check.str_param(client_id, "client_id")
            self.client_secret = check.str_param(client_secret, "client_secret")
            self.refresh_token = check.str_param(refresh_token, "refresh_token")

    class AccessToken:
        @public
        def __init__(self, access_token: str, auth_method: Optional[str] = None):
            self.auth_method = check.opt_str_param(auth_method, "auth_method")
            self.access_token = check.str_param(access_token, "access_token")

    @public
    def __init__(
        self,
        name: str,
        org_id: int,
        credentials: Union["LinkedinPagesSource.OAuth20", "LinkedinPagesSource.AccessToken"],
    ):
        """Airbyte Source for Linkedin Pages.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/linkedin-pages/

        Args:
            name (str): The name of the destination.
            org_id (int): Specify the Organization ID
        """
        self.org_id = check.int_param(org_id, "org_id")
        self.credentials = check.inst_param(
            credentials,
            "credentials",
            (LinkedinPagesSource.OAuth20, LinkedinPagesSource.AccessToken),
        )
        super().__init__("Linkedin Pages", name)


class PersistiqSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, api_key: str):
        """Airbyte Source for Persistiq.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/persistiq

        Args:
            name (str): The name of the destination.
            api_key (str): PersistIq API Key. See the docs for more information on where to find that key.
        """
        self.api_key = check.str_param(api_key, "api_key")
        super().__init__("Persistiq", name)


class FreshcallerSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        domain: str,
        api_key: str,
        start_date: str,
        requests_per_minute: Optional[int] = None,
        sync_lag_minutes: Optional[int] = None,
    ):
        """Airbyte Source for Freshcaller.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/freshcaller

        Args:
            name (str): The name of the destination.
            domain (str): Used to construct Base URL for the Freshcaller APIs
            api_key (str): Freshcaller API Key. See the docs for more information on how to obtain this key.
            requests_per_minute (Optional[int]): The number of requests per minute that this source allowed to use. There is a rate limit of 50 requests per minute per app per account.
            start_date (str): UTC date and time. Any data created after this date will be replicated.
            sync_lag_minutes (Optional[int]): Lag in minutes for each sync, i.e., at time T, data for the time range [prev_sync_time, T-30] will be fetched
        """
        self.domain = check.str_param(domain, "domain")
        self.api_key = check.str_param(api_key, "api_key")
        self.requests_per_minute = check.opt_int_param(requests_per_minute, "requests_per_minute")
        self.start_date = check.str_param(start_date, "start_date")
        self.sync_lag_minutes = check.opt_int_param(sync_lag_minutes, "sync_lag_minutes")
        super().__init__("Freshcaller", name)


class AppfollowSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, ext_id: str, cid: str, api_secret: str, country: str):
        """Airbyte Source for Appfollow.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/appfollow

        Args:
            name (str): The name of the destination.
            ext_id (str): for App Store — this is 9-10 digits identification number; for Google Play — this is bundle name;
            cid (str): client id provided by Appfollow
            api_secret (str): api secret provided by Appfollow
            country (str): getting data by Country
        """
        self.ext_id = check.str_param(ext_id, "ext_id")
        self.cid = check.str_param(cid, "cid")
        self.api_secret = check.str_param(api_secret, "api_secret")
        self.country = check.str_param(country, "country")
        super().__init__("Appfollow", name)


class FacebookPagesSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, access_token: str, page_id: str):
        """Airbyte Source for Facebook Pages.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/facebook-pages

        Args:
            name (str): The name of the destination.
            access_token (str): Facebook Page Access Token
            page_id (str): Page ID
        """
        self.access_token = check.str_param(access_token, "access_token")
        self.page_id = check.str_param(page_id, "page_id")
        super().__init__("Facebook Pages", name)


class JiraSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        api_token: str,
        domain: str,
        email: str,
        projects: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        additional_fields: Optional[List[str]] = None,
        expand_issue_changelog: Optional[bool] = None,
        render_fields: Optional[bool] = None,
        enable_experimental_streams: Optional[bool] = None,
    ):
        """Airbyte Source for Jira.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/jira

        Args:
            name (str): The name of the destination.
            api_token (str): Jira API Token. See the docs for more information on how to generate this key.
            domain (str): The Domain for your Jira account, e.g. airbyteio.atlassian.net
            email (str): The user email for your Jira account.
            projects (Optional[List[str]]): List of Jira project keys to replicate data for.
            start_date (Optional[str]): The date from which you'd like to replicate data for Jira in the format YYYY-MM-DDT00:00:00Z. All data generated after this date will be replicated. Note that it will be used only in the following incremental streams: issues.
            additional_fields (Optional[List[str]]): List of additional fields to include in replicating issues.
            expand_issue_changelog (Optional[bool]): Expand the changelog when replicating issues.
            render_fields (Optional[bool]): Render issue fields in HTML format in addition to Jira JSON-like format.
            enable_experimental_streams (Optional[bool]): Allow the use of experimental streams which rely on undocumented Jira API endpoints. See https://docs.airbyte.com/integrations/sources/jira#experimental-tables for more info.
        """
        self.api_token = check.str_param(api_token, "api_token")
        self.domain = check.str_param(domain, "domain")
        self.email = check.str_param(email, "email")
        self.projects = check.opt_nullable_list_param(projects, "projects", str)
        self.start_date = check.opt_str_param(start_date, "start_date")
        self.additional_fields = check.opt_nullable_list_param(
            additional_fields, "additional_fields", str
        )
        self.expand_issue_changelog = check.opt_bool_param(
            expand_issue_changelog, "expand_issue_changelog"
        )
        self.render_fields = check.opt_bool_param(render_fields, "render_fields")
        self.enable_experimental_streams = check.opt_bool_param(
            enable_experimental_streams, "enable_experimental_streams"
        )
        super().__init__("Jira", name)


class GoogleSheetsSource(GeneratedAirbyteSource):
    class AuthenticateViaGoogleOAuth:
        @public
        def __init__(self, client_id: str, client_secret: str, refresh_token: str):
            self.auth_type = "Client"
            self.client_id = check.str_param(client_id, "client_id")
            self.client_secret = check.str_param(client_secret, "client_secret")
            self.refresh_token = check.str_param(refresh_token, "refresh_token")

    class ServiceAccountKeyAuthentication:
        @public
        def __init__(self, service_account_info: str):
            self.auth_type = "Service"
            self.service_account_info = check.str_param(
                service_account_info, "service_account_info"
            )

    @public
    def __init__(
        self,
        name: str,
        spreadsheet_id: str,
        credentials: Union[
            "GoogleSheetsSource.AuthenticateViaGoogleOAuth",
            "GoogleSheetsSource.ServiceAccountKeyAuthentication",
        ],
        row_batch_size: Optional[int] = None,
    ):
        """Airbyte Source for Google Sheets.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/google-sheets

        Args:
            name (str): The name of the destination.
            spreadsheet_id (str): Enter the link to the Google spreadsheet you want to sync
            row_batch_size (Optional[int]): Number of rows fetched when making a Google Sheet API call. Defaults to 200.
            credentials (Union[GoogleSheetsSource.AuthenticateViaGoogleOAuth, GoogleSheetsSource.ServiceAccountKeyAuthentication]): Credentials for connecting to the Google Sheets API
        """
        self.spreadsheet_id = check.str_param(spreadsheet_id, "spreadsheet_id")
        self.row_batch_size = check.opt_int_param(row_batch_size, "row_batch_size")
        self.credentials = check.inst_param(
            credentials,
            "credentials",
            (
                GoogleSheetsSource.AuthenticateViaGoogleOAuth,
                GoogleSheetsSource.ServiceAccountKeyAuthentication,
            ),
        )
        super().__init__("Google Sheets", name)


class DockerhubSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, docker_username: str):
        """Airbyte Source for Dockerhub.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/dockerhub

        Args:
            name (str): The name of the destination.
            docker_username (str): Username of DockerHub person or organization (for https://hub.docker.com/v2/repositories/USERNAME/ API call)
        """
        self.docker_username = check.str_param(docker_username, "docker_username")
        super().__init__("Dockerhub", name)


class UsCensusSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self, name: str, query_path: str, api_key: str, query_params: Optional[str] = None
    ):
        """Airbyte Source for Us Census.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/us-census

        Args:
            name (str): The name of the destination.
            query_params (Optional[str]): The query parameters portion of the GET request, without the api key
            query_path (str): The path portion of the GET request
            api_key (str): Your API Key. Get your key here.
        """
        self.query_params = check.opt_str_param(query_params, "query_params")
        self.query_path = check.str_param(query_path, "query_path")
        self.api_key = check.str_param(api_key, "api_key")
        super().__init__("Us Census", name)


class KustomerSingerSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, api_token: str, start_date: str):
        """Airbyte Source for Kustomer Singer.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/kustomer

        Args:
            name (str): The name of the destination.
            api_token (str): Kustomer API Token. See the docs on how to obtain this
            start_date (str): The date from which you'd like to replicate the data
        """
        self.api_token = check.str_param(api_token, "api_token")
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Kustomer Singer", name)


class AzureTableSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        storage_account_name: str,
        storage_access_key: str,
        storage_endpoint_suffix: Optional[str] = None,
    ):
        """Airbyte Source for Azure Table.

        Args:
            name (str): The name of the destination.
            storage_account_name (str): The name of your storage account.
            storage_access_key (str): Azure Table Storage Access Key. See the docs for more information on how to obtain this key.
            storage_endpoint_suffix (Optional[str]): Azure Table Storage service account URL suffix. See the docs for more information on how to obtain endpoint suffix
        """
        self.storage_account_name = check.str_param(storage_account_name, "storage_account_name")
        self.storage_access_key = check.str_param(storage_access_key, "storage_access_key")
        self.storage_endpoint_suffix = check.opt_str_param(
            storage_endpoint_suffix, "storage_endpoint_suffix"
        )
        super().__init__("Azure Table", name)


class ScaffoldJavaJdbcSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        database: str,
        username: str,
        replication_method: str,
        password: Optional[str] = None,
        jdbc_url_params: Optional[str] = None,
    ):
        """Airbyte Source for Scaffold Java Jdbc.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/scaffold_java_jdbc

        Args:
            name (str): The name of the destination.
            host (str): Hostname of the database.
            port (int): Port of the database.
            database (str): Name of the database.
            username (str): Username to use to access the database.
            password (Optional[str]): Password associated with the username.
            jdbc_url_params (Optional[str]): Additional properties to pass to the JDBC URL string when connecting to the database formatted as 'key=value' pairs separated by the symbol '&'. (example: key1=value1&key2=value2&key3=value3)
            replication_method (str): Replication method to use for extracting data from the database. STANDARD replication requires no setup on the DB side but will not be able to represent deletions incrementally. CDC uses the Binlog to detect inserts, updates, and deletes. This needs to be configured on the source database itself.
        """
        self.host = check.str_param(host, "host")
        self.port = check.int_param(port, "port")
        self.database = check.str_param(database, "database")
        self.username = check.str_param(username, "username")
        self.password = check.opt_str_param(password, "password")
        self.jdbc_url_params = check.opt_str_param(jdbc_url_params, "jdbc_url_params")
        self.replication_method = check.str_param(replication_method, "replication_method")
        super().__init__("Scaffold Java Jdbc", name)


class TidbSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        database: str,
        username: str,
        password: Optional[str] = None,
        jdbc_url_params: Optional[str] = None,
        ssl: Optional[bool] = None,
    ):
        """Airbyte Source for Tidb.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/tidb

        Args:
            name (str): The name of the destination.
            host (str): Hostname of the database.
            port (int): Port of the database.
            database (str): Name of the database.
            username (str): Username to use to access the database.
            password (Optional[str]): Password associated with the username.
            jdbc_url_params (Optional[str]): Additional properties to pass to the JDBC URL string when connecting to the database formatted as 'key=value' pairs separated by the symbol '&'. (example: key1=value1&key2=value2&key3=value3)
            ssl (Optional[bool]): Encrypt data using SSL.
        """
        self.host = check.str_param(host, "host")
        self.port = check.int_param(port, "port")
        self.database = check.str_param(database, "database")
        self.username = check.str_param(username, "username")
        self.password = check.opt_str_param(password, "password")
        self.jdbc_url_params = check.opt_str_param(jdbc_url_params, "jdbc_url_params")
        self.ssl = check.opt_bool_param(ssl, "ssl")
        super().__init__("Tidb", name)


class QualarooSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        token: str,
        key: str,
        start_date: str,
        survey_ids: Optional[List[str]] = None,
    ):
        """Airbyte Source for Qualaroo.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/qualaroo

        Args:
            name (str): The name of the destination.
            token (str): A Qualaroo token. See the docs for instructions on how to generate it.
            key (str): A Qualaroo token. See the docs for instructions on how to generate it.
            start_date (str): UTC date and time in the format 2017-01-25T00:00:00Z. Any data before this date will not be replicated.
            survey_ids (Optional[List[str]]): IDs of the surveys from which you'd like to replicate data. If left empty, data from all surveys to which you have access will be replicated.
        """
        self.token = check.str_param(token, "token")
        self.key = check.str_param(key, "key")
        self.start_date = check.str_param(start_date, "start_date")
        self.survey_ids = check.opt_nullable_list_param(survey_ids, "survey_ids", str)
        super().__init__("Qualaroo", name)


class YahooFinancePriceSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self, name: str, tickers: str, interval: Optional[str] = None, range: Optional[str] = None
    ):
        """Airbyte Source for Yahoo Finance Price.

        Args:
            name (str): The name of the destination.
            tickers (str): Comma-separated identifiers for the stocks to be queried. Whitespaces are allowed.
            interval (Optional[str]): The interval of between prices queried.
            range (Optional[str]): The range of prices to be queried.
        """
        self.tickers = check.str_param(tickers, "tickers")
        self.interval = check.opt_str_param(interval, "interval")
        self.range = check.opt_str_param(range, "range")
        super().__init__("Yahoo Finance Price", name)


class GoogleAnalyticsV4Source(GeneratedAirbyteSource):
    class AuthenticateViaGoogleOauth:
        @public
        def __init__(
            self,
            client_id: str,
            client_secret: str,
            refresh_token: str,
            auth_type: Optional[str] = None,
            access_token: Optional[str] = None,
        ):
            self.auth_type = check.opt_str_param(auth_type, "auth_type")
            self.client_id = check.str_param(client_id, "client_id")
            self.client_secret = check.str_param(client_secret, "client_secret")
            self.refresh_token = check.str_param(refresh_token, "refresh_token")
            self.access_token = check.opt_str_param(access_token, "access_token")

    class ServiceAccountKeyAuthentication:
        @public
        def __init__(self, credentials_json: str, auth_type: Optional[str] = None):
            self.auth_type = check.opt_str_param(auth_type, "auth_type")
            self.credentials_json = check.str_param(credentials_json, "credentials_json")

    @public
    def __init__(
        self,
        name: str,
        credentials: Union[
            "GoogleAnalyticsV4Source.AuthenticateViaGoogleOauth",
            "GoogleAnalyticsV4Source.ServiceAccountKeyAuthentication",
        ],
        start_date: str,
        view_id: str,
        custom_reports: Optional[str] = None,
        window_in_days: Optional[int] = None,
    ):
        """Airbyte Source for Google Analytics V4.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/google-analytics-universal-analytics

        Args:
            name (str): The name of the destination.
            credentials (Union[GoogleAnalyticsV4Source.AuthenticateViaGoogleOauth, GoogleAnalyticsV4Source.ServiceAccountKeyAuthentication]): Credentials for the service
            start_date (str): The date in the format YYYY-MM-DD. Any data before this date will not be replicated.
            view_id (str): The ID for the Google Analytics View you want to fetch data from. This can be found from the Google Analytics Account Explorer.
            custom_reports (Optional[str]): A JSON array describing the custom reports you want to sync from Google Analytics. See the docs for more information about the exact format you can use to fill out this field.
            window_in_days (Optional[int]): The time increment used by the connector when requesting data from the Google Analytics API. More information is available in the the docs. The bigger this value is, the faster the sync will be, but the more likely that sampling will be applied to your data, potentially causing inaccuracies in the returned results. We recommend setting this to 1 unless you have a hard requirement to make the sync faster at the expense of accuracy. The minimum allowed value for this field is 1, and the maximum is 364.
        """
        self.credentials = check.inst_param(
            credentials,
            "credentials",
            (
                GoogleAnalyticsV4Source.AuthenticateViaGoogleOauth,
                GoogleAnalyticsV4Source.ServiceAccountKeyAuthentication,
            ),
        )
        self.start_date = check.str_param(start_date, "start_date")
        self.view_id = check.str_param(view_id, "view_id")
        self.custom_reports = check.opt_str_param(custom_reports, "custom_reports")
        self.window_in_days = check.opt_int_param(window_in_days, "window_in_days")
        super().__init__("Google Analytics V4", name)


class JdbcSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        username: str,
        jdbc_url: str,
        password: Optional[str] = None,
        jdbc_url_params: Optional[str] = None,
    ):
        """Airbyte Source for Jdbc.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/postgres

        Args:
            name (str): The name of the destination.
            username (str): The username which is used to access the database.
            password (Optional[str]): The password associated with this username.
            jdbc_url (str): JDBC formatted URL. See the standard here.
            jdbc_url_params (Optional[str]): Additional properties to pass to the JDBC URL string when connecting to the database formatted as 'key=value' pairs separated by the symbol '&'. (example: key1=value1&key2=value2&key3=value3).
        """
        self.username = check.str_param(username, "username")
        self.password = check.opt_str_param(password, "password")
        self.jdbc_url = check.str_param(jdbc_url, "jdbc_url")
        self.jdbc_url_params = check.opt_str_param(jdbc_url_params, "jdbc_url_params")
        super().__init__("Jdbc", name)


class FakerSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        count: int,
        seed: Optional[int] = None,
        records_per_sync: Optional[int] = None,
        records_per_slice: Optional[int] = None,
    ):
        """Airbyte Source for Faker.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/faker

        Args:
            name (str): The name of the destination.
            count (int): How many users should be generated in total.  This setting does not apply to the purchases or products stream.
            seed (Optional[int]): Manually control the faker random seed to return the same values on subsequent runs (leave -1 for random)
            records_per_sync (Optional[int]): How many fake records will be returned for each sync, for each stream?  By default, it will take 2 syncs to create the requested 1000 records.
            records_per_slice (Optional[int]): How many fake records will be in each page (stream slice), before a state message is emitted?
        """
        self.count = check.int_param(count, "count")
        self.seed = check.opt_int_param(seed, "seed")
        self.records_per_sync = check.opt_int_param(records_per_sync, "records_per_sync")
        self.records_per_slice = check.opt_int_param(records_per_slice, "records_per_slice")
        super().__init__("Faker", name)


class TplcentralSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        url_base: str,
        client_id: str,
        client_secret: str,
        user_login_id: Optional[int] = None,
        user_login: Optional[str] = None,
        tpl_key: Optional[str] = None,
        customer_id: Optional[int] = None,
        facility_id: Optional[int] = None,
        start_date: Optional[str] = None,
    ):
        """Airbyte Source for Tplcentral.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/tplcentral

        Args:
            name (str): The name of the destination.
            user_login_id (Optional[int]): User login ID and/or name is required
            user_login (Optional[str]): User login ID and/or name is required
            start_date (Optional[str]): Date and time together in RFC 3339 format, for example, 2018-11-13T20:20:39+00:00.
        """
        self.url_base = check.str_param(url_base, "url_base")
        self.client_id = check.str_param(client_id, "client_id")
        self.client_secret = check.str_param(client_secret, "client_secret")
        self.user_login_id = check.opt_int_param(user_login_id, "user_login_id")
        self.user_login = check.opt_str_param(user_login, "user_login")
        self.tpl_key = check.opt_str_param(tpl_key, "tpl_key")
        self.customer_id = check.opt_int_param(customer_id, "customer_id")
        self.facility_id = check.opt_int_param(facility_id, "facility_id")
        self.start_date = check.opt_str_param(start_date, "start_date")
        super().__init__("Tplcentral", name)


class ClickhouseSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        database: str,
        username: str,
        password: Optional[str] = None,
        jdbc_url_params: Optional[str] = None,
        ssl: Optional[bool] = None,
    ):
        """Airbyte Source for Clickhouse.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/clickhouse

        Args:
            name (str): The name of the destination.
            host (str): The host endpoint of the Clickhouse cluster.
            port (int): The port of the database.
            database (str): The name of the database.
            username (str): The username which is used to access the database.
            password (Optional[str]): The password associated with this username.
            jdbc_url_params (Optional[str]): Additional properties to pass to the JDBC URL string when connecting to the database formatted as 'key=value' pairs separated by the symbol '&'. (Eg. key1=value1&key2=value2&key3=value3). For more information read about JDBC URL parameters.
            ssl (Optional[bool]): Encrypt data using SSL.
        """
        self.host = check.str_param(host, "host")
        self.port = check.int_param(port, "port")
        self.database = check.str_param(database, "database")
        self.username = check.str_param(username, "username")
        self.password = check.opt_str_param(password, "password")
        self.jdbc_url_params = check.opt_str_param(jdbc_url_params, "jdbc_url_params")
        self.ssl = check.opt_bool_param(ssl, "ssl")
        super().__init__("Clickhouse", name)


class FreshserviceSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, domain_name: str, api_key: str, start_date: str):
        """Airbyte Source for Freshservice.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/freshservice

        Args:
            name (str): The name of the destination.
            domain_name (str): The name of your Freshservice domain
            api_key (str): Freshservice API Key. See here. The key is case sensitive.
            start_date (str): UTC date and time in the format 2020-10-01T00:00:00Z. Any data before this date will not be replicated.
        """
        self.domain_name = check.str_param(domain_name, "domain_name")
        self.api_key = check.str_param(api_key, "api_key")
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Freshservice", name)


class ZenloopSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        api_token: str,
        date_from: Optional[str] = None,
        survey_id: Optional[str] = None,
        survey_group_id: Optional[str] = None,
    ):
        """Airbyte Source for Zenloop.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/zenloop

        Args:
            name (str): The name of the destination.
            api_token (str): Zenloop API Token. You can get the API token in settings page here
            date_from (Optional[str]): Zenloop date_from. Format: 2021-10-24T03:30:30Z or 2021-10-24. Leave empty if only data from current data should be synced
            survey_id (Optional[str]): Zenloop Survey ID. Can be found here. Leave empty to pull answers from all surveys
            survey_group_id (Optional[str]): Zenloop Survey Group ID. Can be found by pulling All Survey Groups via SurveyGroups stream. Leave empty to pull answers from all survey groups
        """
        self.api_token = check.str_param(api_token, "api_token")
        self.date_from = check.opt_str_param(date_from, "date_from")
        self.survey_id = check.opt_str_param(survey_id, "survey_id")
        self.survey_group_id = check.opt_str_param(survey_group_id, "survey_group_id")
        super().__init__("Zenloop", name)


class OracleSource(GeneratedAirbyteSource):
    class ServiceName:
        @public
        def __init__(self, service_name: str, connection_type: Optional[str] = None):
            self.connection_type = check.opt_str_param(connection_type, "connection_type")
            self.service_name = check.str_param(service_name, "service_name")

    class SystemIDSID:
        @public
        def __init__(self, sid: str, connection_type: Optional[str] = None):
            self.connection_type = check.opt_str_param(connection_type, "connection_type")
            self.sid = check.str_param(sid, "sid")

    class Unencrypted:
        @public
        def __init__(
            self,
        ):
            self.encryption_method = "unencrypted"

    class NativeNetworkEncryptionNNE:
        @public
        def __init__(self, encryption_algorithm: Optional[str] = None):
            self.encryption_method = "client_nne"
            self.encryption_algorithm = check.opt_str_param(
                encryption_algorithm, "encryption_algorithm"
            )

    class TLSEncryptedVerifyCertificate:
        @public
        def __init__(self, ssl_certificate: str):
            self.encryption_method = "encrypted_verify_certificate"
            self.ssl_certificate = check.str_param(ssl_certificate, "ssl_certificate")

    @public
    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        connection_data: Union["OracleSource.ServiceName", "OracleSource.SystemIDSID"],
        username: str,
        encryption: Union[
            "OracleSource.Unencrypted",
            "OracleSource.NativeNetworkEncryptionNNE",
            "OracleSource.TLSEncryptedVerifyCertificate",
        ],
        password: Optional[str] = None,
        schemas: Optional[List[str]] = None,
        jdbc_url_params: Optional[str] = None,
    ):
        """Airbyte Source for Oracle.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/oracle

        Args:
            name (str): The name of the destination.
            host (str): Hostname of the database.
            port (int): Port of the database. Oracle Corporations recommends the following port numbers: 1521 - Default listening port for client connections to the listener.  2484 - Recommended and officially registered listening port for client connections to the listener using TCP/IP with SSL
            connection_data (Union[OracleSource.ServiceName, OracleSource.SystemIDSID]): Connect data that will be used for DB connection
            username (str): The username which is used to access the database.
            password (Optional[str]): The password associated with the username.
            schemas (Optional[List[str]]): The list of schemas to sync from. Defaults to user. Case sensitive.
            jdbc_url_params (Optional[str]): Additional properties to pass to the JDBC URL string when connecting to the database formatted as 'key=value' pairs separated by the symbol '&'. (example: key1=value1&key2=value2&key3=value3).
            encryption (Union[OracleSource.Unencrypted, OracleSource.NativeNetworkEncryptionNNE, OracleSource.TLSEncryptedVerifyCertificate]): The encryption method with is used when communicating with the database.
        """
        self.host = check.str_param(host, "host")
        self.port = check.int_param(port, "port")
        self.connection_data = check.inst_param(
            connection_data, "connection_data", (OracleSource.ServiceName, OracleSource.SystemIDSID)
        )
        self.username = check.str_param(username, "username")
        self.password = check.opt_str_param(password, "password")
        self.schemas = check.opt_nullable_list_param(schemas, "schemas", str)
        self.jdbc_url_params = check.opt_str_param(jdbc_url_params, "jdbc_url_params")
        self.encryption = check.inst_param(
            encryption,
            "encryption",
            (
                OracleSource.Unencrypted,
                OracleSource.NativeNetworkEncryptionNNE,
                OracleSource.TLSEncryptedVerifyCertificate,
            ),
        )
        super().__init__("Oracle", name)


class KlaviyoSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, api_key: str, start_date: str):
        """Airbyte Source for Klaviyo.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/klaviyo

        Args:
            name (str): The name of the destination.
            api_key (str): Klaviyo API Key. See our docs if you need help finding this key.
            start_date (str): UTC date and time in the format 2017-01-25T00:00:00Z. Any data before this date will not be replicated.
        """
        self.api_key = check.str_param(api_key, "api_key")
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Klaviyo", name)


class GoogleDirectorySource(GeneratedAirbyteSource):
    class SignInViaGoogleOAuth:
        @public
        def __init__(
            self,
            client_id: str,
            client_secret: str,
            refresh_token: str,
            credentials_title: Optional[str] = None,
        ):
            self.credentials_title = check.opt_str_param(credentials_title, "credentials_title")
            self.client_id = check.str_param(client_id, "client_id")
            self.client_secret = check.str_param(client_secret, "client_secret")
            self.refresh_token = check.str_param(refresh_token, "refresh_token")

    class ServiceAccountKey:
        @public
        def __init__(
            self, credentials_json: str, email: str, credentials_title: Optional[str] = None
        ):
            self.credentials_title = check.opt_str_param(credentials_title, "credentials_title")
            self.credentials_json = check.str_param(credentials_json, "credentials_json")
            self.email = check.str_param(email, "email")

    @public
    def __init__(
        self,
        name: str,
        credentials: Union[
            "GoogleDirectorySource.SignInViaGoogleOAuth", "GoogleDirectorySource.ServiceAccountKey"
        ],
    ):
        """Airbyte Source for Google Directory.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/google-directory

        Args:
            name (str): The name of the destination.
            credentials (Union[GoogleDirectorySource.SignInViaGoogleOAuth, GoogleDirectorySource.ServiceAccountKey]): Google APIs use the OAuth 2.0 protocol for authentication and authorization. The Source supports Web server application and Service accounts scenarios.
        """
        self.credentials = check.inst_param(
            credentials,
            "credentials",
            (GoogleDirectorySource.SignInViaGoogleOAuth, GoogleDirectorySource.ServiceAccountKey),
        )
        super().__init__("Google Directory", name)


class InstagramSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, start_date: str, access_token: str):
        """Airbyte Source for Instagram.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/instagram

        Args:
            name (str): The name of the destination.
            start_date (str): The date from which you'd like to replicate data for User Insights, in the format YYYY-MM-DDT00:00:00Z. All data generated after this date will be replicated.
            access_token (str): The value of the access token generated. See the docs for more information
        """
        self.start_date = check.str_param(start_date, "start_date")
        self.access_token = check.str_param(access_token, "access_token")
        super().__init__("Instagram", name)


class ShortioSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, domain_id: str, secret_key: str, start_date: str):
        """Airbyte Source for Shortio.

        Documentation can be found at https://developers.short.io/reference

        Args:
            name (str): The name of the destination.
            secret_key (str): Short.io Secret Key
            start_date (str): UTC date and time in the format 2017-01-25T00:00:00Z. Any data before this date will not be replicated.
        """
        self.domain_id = check.str_param(domain_id, "domain_id")
        self.secret_key = check.str_param(secret_key, "secret_key")
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Shortio", name)


class SquareSource(GeneratedAirbyteSource):
    class OauthAuthentication:
        @public
        def __init__(self, client_id: str, client_secret: str, refresh_token: str):
            self.auth_type = "Oauth"
            self.client_id = check.str_param(client_id, "client_id")
            self.client_secret = check.str_param(client_secret, "client_secret")
            self.refresh_token = check.str_param(refresh_token, "refresh_token")

    class APIKey:
        @public
        def __init__(self, api_key: str):
            self.auth_type = "Apikey"
            self.api_key = check.str_param(api_key, "api_key")

    @public
    def __init__(
        self,
        name: str,
        is_sandbox: bool,
        credentials: Union["SquareSource.OauthAuthentication", "SquareSource.APIKey"],
        start_date: Optional[str] = None,
        include_deleted_objects: Optional[bool] = None,
    ):
        """Airbyte Source for Square.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/square

        Args:
            name (str): The name of the destination.
            is_sandbox (bool): Determines whether to use the sandbox or production environment.
            start_date (Optional[str]): UTC date in the format YYYY-MM-DD. Any data before this date will not be replicated. If not set, all data will be replicated.
            include_deleted_objects (Optional[bool]): In some streams there is an option to include deleted objects (Items, Categories, Discounts, Taxes)
        """
        self.is_sandbox = check.bool_param(is_sandbox, "is_sandbox")
        self.start_date = check.opt_str_param(start_date, "start_date")
        self.include_deleted_objects = check.opt_bool_param(
            include_deleted_objects, "include_deleted_objects"
        )
        self.credentials = check.inst_param(
            credentials, "credentials", (SquareSource.OauthAuthentication, SquareSource.APIKey)
        )
        super().__init__("Square", name)


class DelightedSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, since: str, api_key: str):
        """Airbyte Source for Delighted.

        Args:
            name (str): The name of the destination.
            since (str): The date from which you'd like to replicate the data
            api_key (str): A Delighted API key.
        """
        self.since = check.str_param(since, "since")
        self.api_key = check.str_param(api_key, "api_key")
        super().__init__("Delighted", name)


class AmazonSqsSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        queue_url: str,
        region: str,
        delete_messages: bool,
        max_batch_size: Optional[int] = None,
        max_wait_time: Optional[int] = None,
        attributes_to_return: Optional[str] = None,
        visibility_timeout: Optional[int] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
    ):
        """Airbyte Source for Amazon Sqs.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/amazon-sqs

        Args:
            name (str): The name of the destination.
            queue_url (str): URL of the SQS Queue
            region (str): AWS Region of the SQS Queue
            delete_messages (bool): If Enabled, messages will be deleted from the SQS Queue after being read. If Disabled, messages are left in the queue and can be read more than once. WARNING: Enabling this option can result in data loss in cases of failure, use with caution, see documentation for more detail.
            max_batch_size (Optional[int]): Max amount of messages to get in one batch (10 max)
            max_wait_time (Optional[int]): Max amount of time in seconds to wait for messages in a single poll (20 max)
            attributes_to_return (Optional[str]): Comma separated list of Mesage Attribute names to return
            visibility_timeout (Optional[int]): Modify the Visibility Timeout of the individual message from the Queue's default (seconds).
            access_key (Optional[str]): The Access Key ID of the AWS IAM Role to use for pulling messages
            secret_key (Optional[str]): The Secret Key of the AWS IAM Role to use for pulling messages
        """
        self.queue_url = check.str_param(queue_url, "queue_url")
        self.region = check.str_param(region, "region")
        self.delete_messages = check.bool_param(delete_messages, "delete_messages")
        self.max_batch_size = check.opt_int_param(max_batch_size, "max_batch_size")
        self.max_wait_time = check.opt_int_param(max_wait_time, "max_wait_time")
        self.attributes_to_return = check.opt_str_param(
            attributes_to_return, "attributes_to_return"
        )
        self.visibility_timeout = check.opt_int_param(visibility_timeout, "visibility_timeout")
        self.access_key = check.opt_str_param(access_key, "access_key")
        self.secret_key = check.opt_str_param(secret_key, "secret_key")
        super().__init__("Amazon Sqs", name)


class YoutubeAnalyticsSource(GeneratedAirbyteSource):
    class AuthenticateViaOAuth20:
        @public
        def __init__(self, client_id: str, client_secret: str, refresh_token: str):
            self.client_id = check.str_param(client_id, "client_id")
            self.client_secret = check.str_param(client_secret, "client_secret")
            self.refresh_token = check.str_param(refresh_token, "refresh_token")

    @public
    def __init__(self, name: str, credentials: "YoutubeAnalyticsSource.AuthenticateViaOAuth20"):
        """Airbyte Source for Youtube Analytics.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/youtube-analytics

        Args:
            name (str): The name of the destination.

        """
        self.credentials = check.inst_param(
            credentials, "credentials", YoutubeAnalyticsSource.AuthenticateViaOAuth20
        )
        super().__init__("Youtube Analytics", name)


class ScaffoldSourcePythonSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, fix_me: Optional[str] = None):
        """Airbyte Source for Scaffold Source Python.

        Args:
            name (str): The name of the destination.
            fix_me (Optional[str]): describe me
        """
        self.fix_me = check.opt_str_param(fix_me, "fix_me")
        super().__init__("Scaffold Source Python", name)


class LookerSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        domain: str,
        client_id: str,
        client_secret: str,
        run_look_ids: Optional[List[str]] = None,
    ):
        """Airbyte Source for Looker.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/looker

        Args:
            name (str): The name of the destination.
            domain (str): Domain for your Looker account, e.g. airbyte.cloud.looker.com,looker.[clientname].com,IP address
            client_id (str): The Client ID is first part of an API3 key that is specific to each Looker user. See the docs for more information on how to generate this key.
            client_secret (str): The Client Secret is second part of an API3 key.
            run_look_ids (Optional[List[str]]): The IDs of any Looks to run
        """
        self.domain = check.str_param(domain, "domain")
        self.client_id = check.str_param(client_id, "client_id")
        self.client_secret = check.str_param(client_secret, "client_secret")
        self.run_look_ids = check.opt_nullable_list_param(run_look_ids, "run_look_ids", str)
        super().__init__("Looker", name)


class GitlabSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        api_url: str,
        private_token: str,
        start_date: str,
        groups: Optional[str] = None,
        projects: Optional[str] = None,
    ):
        """Airbyte Source for Gitlab.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/gitlab

        Args:
            name (str): The name of the destination.
            api_url (str): Please enter your basic URL from GitLab instance.
            private_token (str): Log into your GitLab account and then generate a personal Access Token.
            groups (Optional[str]): Space-delimited list of groups. e.g. airbyte.io.
            projects (Optional[str]): Space-delimited list of projects. e.g. airbyte.io/documentation meltano/tap-gitlab.
            start_date (str): The date from which you'd like to replicate data for GitLab API, in the format YYYY-MM-DDT00:00:00Z. All data generated after this date will be replicated.
        """
        self.api_url = check.str_param(api_url, "api_url")
        self.private_token = check.str_param(private_token, "private_token")
        self.groups = check.opt_str_param(groups, "groups")
        self.projects = check.opt_str_param(projects, "projects")
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Gitlab", name)


class ExchangeRatesSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        start_date: str,
        access_key: str,
        base: Optional[str] = None,
        ignore_weekends: Optional[bool] = None,
    ):
        """Airbyte Source for Exchange Rates.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/exchangeratesapi

        Args:
            name (str): The name of the destination.
            start_date (str): Start getting data from that date.
            access_key (str): Your API Key. See here. The key is case sensitive.
            base (Optional[str]): ISO reference currency. See here. Free plan doesn't support Source Currency Switching, default base currency is EUR
            ignore_weekends (Optional[bool]): Ignore weekends? (Exchanges don't run on weekends)
        """
        self.start_date = check.str_param(start_date, "start_date")
        self.access_key = check.str_param(access_key, "access_key")
        self.base = check.opt_str_param(base, "base")
        self.ignore_weekends = check.opt_bool_param(ignore_weekends, "ignore_weekends")
        super().__init__("Exchange Rates", name)


class AmazonAdsSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        auth_type: Optional[str] = None,
        region: Optional[str] = None,
        report_wait_timeout: Optional[int] = None,
        report_generation_max_retries: Optional[int] = None,
        start_date: Optional[str] = None,
        profiles: Optional[List[int]] = None,
        state_filter: Optional[List[str]] = None,
    ):
        """Airbyte Source for Amazon Ads.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/amazon-ads

        Args:
            name (str): The name of the destination.
            client_id (str): The client ID of your Amazon Ads developer application. See the docs for more information.
            client_secret (str): The client secret of your Amazon Ads developer application. See the docs for more information.
            refresh_token (str): Amazon Ads refresh token. See the docs for more information on how to obtain this token.
            region (Optional[str]): Region to pull data from (EU/NA/FE). See docs for more details.
            report_wait_timeout (Optional[int]): Timeout duration in minutes for Reports. Default is 60 minutes.
            report_generation_max_retries (Optional[int]): Maximum retries Airbyte will attempt for fetching report data. Default is 5.
            start_date (Optional[str]): The Start date for collecting reports, should not be more than 60 days in the past. In YYYY-MM-DD format
            profiles (Optional[List[int]]): Profile IDs you want to fetch data for. See docs for more details.
            state_filter (Optional[List[str]]): Reflects the state of the Display, Product, and Brand Campaign streams as enabled, paused, or archived. If you do not populate this field, it will be ignored completely.
        """
        self.auth_type = check.opt_str_param(auth_type, "auth_type")
        self.client_id = check.str_param(client_id, "client_id")
        self.client_secret = check.str_param(client_secret, "client_secret")
        self.refresh_token = check.str_param(refresh_token, "refresh_token")
        self.region = check.opt_str_param(region, "region")
        self.report_wait_timeout = check.opt_int_param(report_wait_timeout, "report_wait_timeout")
        self.report_generation_max_retries = check.opt_int_param(
            report_generation_max_retries, "report_generation_max_retries"
        )
        self.start_date = check.opt_str_param(start_date, "start_date")
        self.profiles = check.opt_nullable_list_param(profiles, "profiles", int)
        self.state_filter = check.opt_nullable_list_param(state_filter, "state_filter", str)
        super().__init__("Amazon Ads", name)


class MixpanelSource(GeneratedAirbyteSource):
    class ServiceAccount:
        @public
        def __init__(self, username: str, secret: str):
            self.username = check.str_param(username, "username")
            self.secret = check.str_param(secret, "secret")

    class ProjectSecret:
        @public
        def __init__(self, api_secret: str):
            self.api_secret = check.str_param(api_secret, "api_secret")

    @public
    def __init__(
        self,
        name: str,
        credentials: Union["MixpanelSource.ServiceAccount", "MixpanelSource.ProjectSecret"],
        project_id: Optional[int] = None,
        attribution_window: Optional[int] = None,
        project_timezone: Optional[str] = None,
        select_properties_by_default: Optional[bool] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        region: Optional[str] = None,
        date_window_size: Optional[int] = None,
    ):
        """Airbyte Source for Mixpanel.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/mixpanel

        Args:
            name (str): The name of the destination.
            credentials (Union[MixpanelSource.ServiceAccount, MixpanelSource.ProjectSecret]): Choose how to authenticate to Mixpanel
            project_id (Optional[int]): Your project ID number. See the docs for more information on how to obtain this.
            attribution_window (Optional[int]):  A period of time for attributing results to ads and the lookback period after those actions occur during which ad results are counted. Default attribution window is 5 days.
            project_timezone (Optional[str]): Time zone in which integer date times are stored. The project timezone may be found in the project settings in the Mixpanel console.
            select_properties_by_default (Optional[bool]): Setting this config parameter to TRUE ensures that new properties on events and engage records are captured. Otherwise new properties will be ignored.
            start_date (Optional[str]): The date in the format YYYY-MM-DD. Any data before this date will not be replicated. If this option is not set, the connector will replicate data from up to one year ago by default.
            end_date (Optional[str]): The date in the format YYYY-MM-DD. Any data after this date will not be replicated. Left empty to always sync to most recent date
            region (Optional[str]): The region of mixpanel domain instance either US or EU.
            date_window_size (Optional[int]): Defines window size in days, that used to slice through data. You can reduce it, if amount of data in each window is too big for your environment.
        """
        self.credentials = check.inst_param(
            credentials,
            "credentials",
            (MixpanelSource.ServiceAccount, MixpanelSource.ProjectSecret),
        )
        self.project_id = check.opt_int_param(project_id, "project_id")
        self.attribution_window = check.opt_int_param(attribution_window, "attribution_window")
        self.project_timezone = check.opt_str_param(project_timezone, "project_timezone")
        self.select_properties_by_default = check.opt_bool_param(
            select_properties_by_default, "select_properties_by_default"
        )
        self.start_date = check.opt_str_param(start_date, "start_date")
        self.end_date = check.opt_str_param(end_date, "end_date")
        self.region = check.opt_str_param(region, "region")
        self.date_window_size = check.opt_int_param(date_window_size, "date_window_size")
        super().__init__("Mixpanel", name)


class OrbitSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, api_token: str, workspace: str, start_date: Optional[str] = None):
        """Airbyte Source for Orbit.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/orbit

        Args:
            name (str): The name of the destination.
            api_token (str): Authorizes you to work with Orbit workspaces associated with the token.
            workspace (str): The unique name of the workspace that your API token is associated with.
            start_date (Optional[str]): Date in the format 2022-06-26. Only load members whose last activities are after this date.
        """
        self.api_token = check.str_param(api_token, "api_token")
        self.workspace = check.str_param(workspace, "workspace")
        self.start_date = check.opt_str_param(start_date, "start_date")
        super().__init__("Orbit", name)


class AmazonSellerPartnerSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        lwa_app_id: str,
        lwa_client_secret: str,
        refresh_token: str,
        aws_access_key: str,
        aws_secret_key: str,
        role_arn: str,
        replication_start_date: str,
        aws_environment: str,
        region: str,
        app_id: Optional[str] = None,
        auth_type: Optional[str] = None,
        replication_end_date: Optional[str] = None,
        period_in_days: Optional[int] = None,
        report_options: Optional[str] = None,
        max_wait_seconds: Optional[int] = None,
    ):
        """Airbyte Source for Amazon Seller Partner.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/amazon-seller-partner

        Args:
            name (str): The name of the destination.
            app_id (Optional[str]): Your Amazon App ID
            lwa_app_id (str): Your Login with Amazon Client ID.
            lwa_client_secret (str): Your Login with Amazon Client Secret.
            refresh_token (str): The Refresh Token obtained via OAuth flow authorization.
            aws_access_key (str): Specifies the AWS access key used as part of the credentials to authenticate the user.
            aws_secret_key (str): Specifies the AWS secret key used as part of the credentials to authenticate the user.
            role_arn (str): Specifies the Amazon Resource Name (ARN) of an IAM role that you want to use to perform operations requested using this profile. (Needs permission to 'Assume Role' STS).
            replication_start_date (str): UTC date and time in the format 2017-01-25T00:00:00Z. Any data before this date will not be replicated.
            replication_end_date (Optional[str]): UTC date and time in the format 2017-01-25T00:00:00Z. Any data after this date will not be replicated.
            period_in_days (Optional[int]): Will be used for stream slicing for initial full_refresh sync when no updated state is present for reports that support sliced incremental sync.
            report_options (Optional[str]): Additional information passed to reports. This varies by report type. Must be a valid json string.
            max_wait_seconds (Optional[int]): Sometimes report can take up to 30 minutes to generate. This will set the limit for how long to wait for a successful report.
            aws_environment (str): An enumeration.
            region (str): An enumeration.
        """
        self.app_id = check.opt_str_param(app_id, "app_id")
        self.auth_type = check.opt_str_param(auth_type, "auth_type")
        self.lwa_app_id = check.str_param(lwa_app_id, "lwa_app_id")
        self.lwa_client_secret = check.str_param(lwa_client_secret, "lwa_client_secret")
        self.refresh_token = check.str_param(refresh_token, "refresh_token")
        self.aws_access_key = check.str_param(aws_access_key, "aws_access_key")
        self.aws_secret_key = check.str_param(aws_secret_key, "aws_secret_key")
        self.role_arn = check.str_param(role_arn, "role_arn")
        self.replication_start_date = check.str_param(
            replication_start_date, "replication_start_date"
        )
        self.replication_end_date = check.opt_str_param(
            replication_end_date, "replication_end_date"
        )
        self.period_in_days = check.opt_int_param(period_in_days, "period_in_days")
        self.report_options = check.opt_str_param(report_options, "report_options")
        self.max_wait_seconds = check.opt_int_param(max_wait_seconds, "max_wait_seconds")
        self.aws_environment = check.str_param(aws_environment, "aws_environment")
        self.region = check.str_param(region, "region")
        super().__init__("Amazon Seller Partner", name)


class CourierSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, api_key: str):
        """Airbyte Source for Courier.

        Documentation can be found at https://docs.airbyte.io/integrations/sources/courier

        Args:
            name (str): The name of the destination.
            api_key (str): Courier API Key to retrieve your data.
        """
        self.api_key = check.str_param(api_key, "api_key")
        super().__init__("Courier", name)


class CloseComSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, api_key: str, start_date: Optional[str] = None):
        r"""Airbyte Source for Close Com.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/close-com

        Args:
            name (str): The name of the destination.
            api_key (str): Close.com API key (usually starts with 'api\\_'; find yours here).
            start_date (Optional[str]): The start date to sync data. Leave blank for full sync. Format: YYYY-MM-DD.
        """
        self.api_key = check.str_param(api_key, "api_key")
        self.start_date = check.opt_str_param(start_date, "start_date")
        super().__init__("Close Com", name)


class BingAdsSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        client_id: str,
        refresh_token: str,
        developer_token: str,
        reports_start_date: str,
        auth_method: Optional[str] = None,
        tenant_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ):
        """Airbyte Source for Bing Ads.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/bing-ads

        Args:
            name (str): The name of the destination.
            tenant_id (Optional[str]): The Tenant ID of your Microsoft Advertising developer application. Set this to "common" unless you know you need a different value.
            client_id (str): The Client ID of your Microsoft Advertising developer application.
            client_secret (Optional[str]): The Client Secret of your Microsoft Advertising developer application.
            refresh_token (str): Refresh Token to renew the expired Access Token.
            developer_token (str): Developer token associated with user. See more info  in the docs.
            reports_start_date (str): The start date from which to begin replicating report data. Any data generated before this date will not be replicated in reports. This is a UTC date in YYYY-MM-DD format.
        """
        self.auth_method = check.opt_str_param(auth_method, "auth_method")
        self.tenant_id = check.opt_str_param(tenant_id, "tenant_id")
        self.client_id = check.str_param(client_id, "client_id")
        self.client_secret = check.opt_str_param(client_secret, "client_secret")
        self.refresh_token = check.str_param(refresh_token, "refresh_token")
        self.developer_token = check.str_param(developer_token, "developer_token")
        self.reports_start_date = check.str_param(reports_start_date, "reports_start_date")
        super().__init__("Bing Ads", name)


class PrimetricSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, client_id: str, client_secret: str):
        """Airbyte Source for Primetric.

        Args:
            name (str): The name of the destination.
            client_id (str): The Client ID of your Primetric developer application. The Client ID is visible here.
            client_secret (str): The Client Secret of your Primetric developer application. You can manage your client's credentials here.
        """
        self.client_id = check.str_param(client_id, "client_id")
        self.client_secret = check.str_param(client_secret, "client_secret")
        super().__init__("Primetric", name)


class PivotalTrackerSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, api_token: str):
        """Airbyte Source for Pivotal Tracker.

        Args:
            name (str): The name of the destination.
            api_token (str): Pivotal Tracker API token
        """
        self.api_token = check.str_param(api_token, "api_token")
        super().__init__("Pivotal Tracker", name)


class ElasticsearchSource(GeneratedAirbyteSource):
    class None_:
        @public
        def __init__(
            self,
        ):
            self.method = "none"

    class ApiKeySecret:
        @public
        def __init__(self, apiKeyId: str, apiKeySecret: str):
            self.method = "secret"
            self.apiKeyId = check.str_param(apiKeyId, "apiKeyId")
            self.apiKeySecret = check.str_param(apiKeySecret, "apiKeySecret")

    class UsernamePassword:
        @public
        def __init__(self, username: str, password: str):
            self.method = "basic"
            self.username = check.str_param(username, "username")
            self.password = check.str_param(password, "password")

    @public
    def __init__(
        self,
        name: str,
        endpoint: str,
        authenticationMethod: Union[
            "ElasticsearchSource.None_",
            "ElasticsearchSource.ApiKeySecret",
            "ElasticsearchSource.UsernamePassword",
        ],
    ):
        r"""Airbyte Source for Elasticsearch.

        Documentation can be found at https://docs.airbyte.com/integrations/source/elasticsearch

        Args:
            name (str): The name of the destination.
            endpoint (str): The full url of the Elasticsearch server
            authenticationMethod (Union[ElasticsearchSource.None\\_, ElasticsearchSource.ApiKeySecret, ElasticsearchSource.UsernamePassword]): The type of authentication to be used
        """
        self.endpoint = check.str_param(endpoint, "endpoint")
        self.authenticationMethod = check.inst_param(
            authenticationMethod,
            "authenticationMethod",
            (
                ElasticsearchSource.None_,
                ElasticsearchSource.ApiKeySecret,
                ElasticsearchSource.UsernamePassword,
            ),
        )
        super().__init__("Elasticsearch", name)


class BigquerySource(GeneratedAirbyteSource):
    @public
    def __init__(
        self, name: str, project_id: str, credentials_json: str, dataset_id: Optional[str] = None
    ):
        """Airbyte Source for Bigquery.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/bigquery

        Args:
            name (str): The name of the destination.
            project_id (str): The GCP project ID for the project containing the target BigQuery dataset.
            dataset_id (Optional[str]): The dataset ID to search for tables and views. If you are only loading data from one dataset, setting this option could result in much faster schema discovery.
            credentials_json (str): The contents of your Service Account Key JSON file. See the docs for more information on how to obtain this key.
        """
        self.project_id = check.str_param(project_id, "project_id")
        self.dataset_id = check.opt_str_param(dataset_id, "dataset_id")
        self.credentials_json = check.str_param(credentials_json, "credentials_json")
        super().__init__("Bigquery", name)


class WoocommerceSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        shop: str,
        start_date: str,
        api_key: str,
        api_secret: str,
        conversion_window_days: Optional[int] = None,
    ):
        """Airbyte Source for Woocommerce.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/woocommerce

        Args:
            name (str): The name of the destination.
            shop (str): The name of the store. For https://EXAMPLE.com, the shop name is 'EXAMPLE.com'.
            start_date (str): The date you would like to replicate data. Format: YYYY-MM-DD.
            api_key (str): The CUSTOMER KEY for API in WooCommerce shop.
            api_secret (str): The CUSTOMER SECRET for API in WooCommerce shop.
            conversion_window_days (Optional[int]): A conversion window is the period of time after an ad interaction (such as an ad click or video view) during which a conversion, such as a purchase, is recorded in Google Ads.
        """
        self.shop = check.str_param(shop, "shop")
        self.start_date = check.str_param(start_date, "start_date")
        self.api_key = check.str_param(api_key, "api_key")
        self.api_secret = check.str_param(api_secret, "api_secret")
        self.conversion_window_days = check.opt_int_param(
            conversion_window_days, "conversion_window_days"
        )
        super().__init__("Woocommerce", name)


class SearchMetricsSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self, name: str, api_key: str, client_secret: str, country_code: str, start_date: str
    ):
        """Airbyte Source for Search Metrics.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/seacrh-metrics

        Args:
            name (str): The name of the destination.
            country_code (str): The region of the S3 staging bucket to use if utilising a copy strategy.
            start_date (str): Data generated in SearchMetrics after this date will be replicated. This date must be specified in the format YYYY-MM-DDT00:00:00Z.
        """
        self.api_key = check.str_param(api_key, "api_key")
        self.client_secret = check.str_param(client_secret, "client_secret")
        self.country_code = check.str_param(country_code, "country_code")
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Search Metrics", name)


class TypeformSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self, name: str, start_date: str, token: str, form_ids: Optional[List[str]] = None
    ):
        """Airbyte Source for Typeform.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/typeform

        Args:
            name (str): The name of the destination.
            start_date (str): UTC date and time in the format: YYYY-MM-DDTHH:mm:ss[Z]. Any data before this date will not be replicated.
            token (str): The API Token for a Typeform account.
            form_ids (Optional[List[str]]): When this parameter is set, the connector will replicate data only from the input forms. Otherwise, all forms in your Typeform account will be replicated. You can find form IDs in your form URLs. For example, in the URL "https://mysite.typeform.com/to/u6nXL7" the form_id is u6nXL7. You can find form URLs on Share panel
        """
        self.start_date = check.str_param(start_date, "start_date")
        self.token = check.str_param(token, "token")
        self.form_ids = check.opt_nullable_list_param(form_ids, "form_ids", str)
        super().__init__("Typeform", name)


class WebflowSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, site_id: str, api_key: str):
        """Airbyte Source for Webflow.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/webflow

        Args:
            name (str): The name of the destination.
            site_id (str): The id of the Webflow site you are requesting data from. See https://developers.webflow.com/#sites
            api_key (str): The API token for authenticating to Webflow. See https://university.webflow.com/lesson/intro-to-the-webflow-api
        """
        self.site_id = check.str_param(site_id, "site_id")
        self.api_key = check.str_param(api_key, "api_key")
        super().__init__("Webflow", name)


class FireboltSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        username: str,
        password: str,
        database: str,
        account: Optional[str] = None,
        host: Optional[str] = None,
        engine: Optional[str] = None,
    ):
        """Airbyte Source for Firebolt.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/firebolt

        Args:
            name (str): The name of the destination.
            username (str): Firebolt email address you use to login.
            password (str): Firebolt password.
            account (Optional[str]): Firebolt account to login.
            host (Optional[str]): The host name of your Firebolt database.
            database (str): The database to connect to.
            engine (Optional[str]): Engine name or url to connect to.
        """
        self.username = check.str_param(username, "username")
        self.password = check.str_param(password, "password")
        self.account = check.opt_str_param(account, "account")
        self.host = check.opt_str_param(host, "host")
        self.database = check.str_param(database, "database")
        self.engine = check.opt_str_param(engine, "engine")
        super().__init__("Firebolt", name)


class FaunaSource(GeneratedAirbyteSource):
    class Disabled:
        @public
        def __init__(
            self,
        ):
            self.deletion_mode = "ignore"

    class Enabled:
        @public
        def __init__(self, column: str):
            self.deletion_mode = "deleted_field"
            self.column = check.str_param(column, "column")

    class Collection:
        @public
        def __init__(
            self, page_size: int, deletions: Union["FaunaSource.Disabled", "FaunaSource.Enabled"]
        ):
            self.page_size = check.int_param(page_size, "page_size")
            self.deletions = check.inst_param(
                deletions, "deletions", (FaunaSource.Disabled, FaunaSource.Enabled)
            )

    @public
    def __init__(
        self,
        name: str,
        domain: str,
        port: int,
        scheme: str,
        secret: str,
        collection: "FaunaSource.Collection",
    ):
        """Airbyte Source for Fauna.

        Documentation can be found at https://github.com/fauna/airbyte/blob/source-fauna/docs/integrations/sources/fauna.md

        Args:
            name (str): The name of the destination.
            domain (str): Domain of Fauna to query. Defaults db.fauna.com. See the docs.
            port (int): Endpoint port.
            scheme (str): URL scheme.
            secret (str): Fauna secret, used when authenticating with the database.
            collection (FaunaSource.Collection): Settings for the Fauna Collection.
        """
        self.domain = check.str_param(domain, "domain")
        self.port = check.int_param(port, "port")
        self.scheme = check.str_param(scheme, "scheme")
        self.secret = check.str_param(secret, "secret")
        self.collection = check.inst_param(collection, "collection", FaunaSource.Collection)
        super().__init__("Fauna", name)


class IntercomSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, start_date: str, access_token: str):
        """Airbyte Source for Intercom.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/intercom

        Args:
            name (str): The name of the destination.
            start_date (str): UTC date and time in the format 2017-01-25T00:00:00Z. Any data before this date will not be replicated.
            access_token (str): Access token for making authenticated requests. See the Intercom docs for more information.
        """
        self.start_date = check.str_param(start_date, "start_date")
        self.access_token = check.str_param(access_token, "access_token")
        super().__init__("Intercom", name)


class FreshsalesSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, domain_name: str, api_key: str):
        """Airbyte Source for Freshsales.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/freshsales

        Args:
            name (str): The name of the destination.
            domain_name (str): The Name of your Freshsales domain
            api_key (str): Freshsales API Key. See here. The key is case sensitive.
        """
        self.domain_name = check.str_param(domain_name, "domain_name")
        self.api_key = check.str_param(api_key, "api_key")
        super().__init__("Freshsales", name)


class AdjustSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        api_token: str,
        dimensions: List[str],
        ingest_start: str,
        metrics: List[str],
        additional_metrics: Optional[List[str]] = None,
        until_today: Optional[bool] = None,
    ):
        """Airbyte Source for Adjust.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/adjust

        Args:
            name (str): The name of the destination.
            additional_metrics (Optional[List[str]]): Metrics names that are not pre-defined, such as cohort metrics or app specific metrics.
            api_token (str): Adjust API key, see https://help.adjust.com/en/article/report-service-api-authentication
            dimensions (List[str]): Dimensions allow a user to break down metrics into groups using one or several parameters. For example, the number of installs by date, country and network. See https://help.adjust.com/en/article/reports-endpoint#dimensions for more information about the dimensions.
            ingest_start (str): Data ingest start date.
            metrics (List[str]): Select at least one metric to query.
            until_today (Optional[bool]): Syncs data up until today. Useful when running daily incremental syncs, and duplicates are not desired.
        """
        self.additional_metrics = check.opt_nullable_list_param(
            additional_metrics, "additional_metrics", str
        )
        self.api_token = check.str_param(api_token, "api_token")
        self.dimensions = check.list_param(dimensions, "dimensions", str)
        self.ingest_start = check.str_param(ingest_start, "ingest_start")
        self.metrics = check.list_param(metrics, "metrics", str)
        self.until_today = check.opt_bool_param(until_today, "until_today")
        super().__init__("Adjust", name)


class BambooHrSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        subdomain: str,
        api_key: str,
        custom_reports_fields: Optional[str] = None,
        custom_reports_include_default_fields: Optional[bool] = None,
    ):
        """Airbyte Source for Bamboo Hr.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/bamboo-hr

        Args:
            name (str): The name of the destination.
            subdomain (str): Sub Domain of bamboo hr
            api_key (str): Api key of bamboo hr
            custom_reports_fields (Optional[str]): Comma-separated list of fields to include in custom reports.
            custom_reports_include_default_fields (Optional[bool]): If true, the custom reports endpoint will include the default fields defined here: https://documentation.bamboohr.com/docs/list-of-field-names.
        """
        self.subdomain = check.str_param(subdomain, "subdomain")
        self.api_key = check.str_param(api_key, "api_key")
        self.custom_reports_fields = check.opt_str_param(
            custom_reports_fields, "custom_reports_fields"
        )
        self.custom_reports_include_default_fields = check.opt_bool_param(
            custom_reports_include_default_fields, "custom_reports_include_default_fields"
        )
        super().__init__("Bamboo Hr", name)


class GoogleAdsSource(GeneratedAirbyteSource):
    class GoogleCredentials:
        @public
        def __init__(
            self,
            developer_token: str,
            client_id: str,
            client_secret: str,
            refresh_token: str,
            access_token: Optional[str] = None,
        ):
            self.developer_token = check.str_param(developer_token, "developer_token")
            self.client_id = check.str_param(client_id, "client_id")
            self.client_secret = check.str_param(client_secret, "client_secret")
            self.refresh_token = check.str_param(refresh_token, "refresh_token")
            self.access_token = check.opt_str_param(access_token, "access_token")

    class CustomGAQLQueriesEntry:
        @public
        def __init__(self, query: str, table_name: str):
            self.query = check.str_param(query, "query")
            self.table_name = check.str_param(table_name, "table_name")

    @public
    def __init__(
        self,
        name: str,
        credentials: "GoogleAdsSource.GoogleCredentials",
        customer_id: str,
        start_date: str,
        end_date: Optional[str] = None,
        custom_queries: Optional[List[CustomGAQLQueriesEntry]] = None,
        login_customer_id: Optional[str] = None,
        conversion_window_days: Optional[int] = None,
    ):
        """Airbyte Source for Google Ads.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/google-ads

        Args:
            name (str): The name of the destination.
            customer_id (str): Comma separated list of (client) customer IDs. Each customer ID must be specified as a 10-digit number without dashes. More instruction on how to find this value in our docs. Metrics streams like AdGroupAdReport cannot be requested for a manager account.
            start_date (str): UTC date and time in the format 2017-01-25. Any data before this date will not be replicated.
            end_date (Optional[str]): UTC date and time in the format 2017-01-25. Any data after this date will not be replicated.
            login_customer_id (Optional[str]): If your access to the customer account is through a manager account, this field is required and must be set to the customer ID of the manager account (10-digit number without dashes). More information about this field you can see here
            conversion_window_days (Optional[int]): A conversion window is the period of time after an ad interaction (such as an ad click or video view) during which a conversion, such as a purchase, is recorded in Google Ads. For more information, see Google's documentation.
        """
        self.credentials = check.inst_param(
            credentials, "credentials", GoogleAdsSource.GoogleCredentials
        )
        self.customer_id = check.str_param(customer_id, "customer_id")
        self.start_date = check.str_param(start_date, "start_date")
        self.end_date = check.opt_str_param(end_date, "end_date")
        self.custom_queries = check.opt_nullable_list_param(
            custom_queries, "custom_queries", GoogleAdsSource.CustomGAQLQueriesEntry
        )
        self.login_customer_id = check.opt_str_param(login_customer_id, "login_customer_id")
        self.conversion_window_days = check.opt_int_param(
            conversion_window_days, "conversion_window_days"
        )
        super().__init__("Google Ads", name)


class HellobatonSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, api_key: str, company: str):
        """Airbyte Source for Hellobaton.

        Args:
            name (str): The name of the destination.
            api_key (str): authentication key required to access the api endpoints
            company (str): Company name that generates your base api url
        """
        self.api_key = check.str_param(api_key, "api_key")
        self.company = check.str_param(company, "company")
        super().__init__("Hellobaton", name)


class SendgridSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, apikey: str, start_time: Union[int, str]):
        """Airbyte Source for Sendgrid.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/sendgrid

        Args:
            name (str): The name of the destination.
            apikey (str): API Key, use admin to generate this key.
            start_time (Union[int, str]): Start time in ISO8601 format. Any data before this time point will not be replicated.
        """
        self.apikey = check.str_param(apikey, "apikey")
        self.start_time = check.inst_param(start_time, "start_time", (int, str))
        super().__init__("Sendgrid", name)


class MondaySource(GeneratedAirbyteSource):
    class OAuth20:
        @public
        def __init__(
            self,
            client_id: str,
            client_secret: str,
            access_token: str,
            subdomain: Optional[str] = None,
        ):
            self.auth_type = "oauth2.0"
            self.subdomain = check.opt_str_param(subdomain, "subdomain")
            self.client_id = check.str_param(client_id, "client_id")
            self.client_secret = check.str_param(client_secret, "client_secret")
            self.access_token = check.str_param(access_token, "access_token")

    class APIToken:
        @public
        def __init__(self, api_token: str):
            self.auth_type = "api_token"
            self.api_token = check.str_param(api_token, "api_token")

    @public
    def __init__(
        self, name: str, credentials: Union["MondaySource.OAuth20", "MondaySource.APIToken"]
    ):
        """Airbyte Source for Monday.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/monday

        Args:
            name (str): The name of the destination.

        """
        self.credentials = check.inst_param(
            credentials, "credentials", (MondaySource.OAuth20, MondaySource.APIToken)
        )
        super().__init__("Monday", name)


class DixaSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self, name: str, api_token: str, start_date: str, batch_size: Optional[int] = None
    ):
        """Airbyte Source for Dixa.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/dixa

        Args:
            name (str): The name of the destination.
            api_token (str): Dixa API token
            start_date (str): The connector pulls records updated from this date onwards.
            batch_size (Optional[int]): Number of days to batch into one request. Max 31.
        """
        self.api_token = check.str_param(api_token, "api_token")
        self.start_date = check.str_param(start_date, "start_date")
        self.batch_size = check.opt_int_param(batch_size, "batch_size")
        super().__init__("Dixa", name)


class SalesforceSource(GeneratedAirbyteSource):
    class FilterSalesforceObjectsEntry:
        @public
        def __init__(self, criteria: str, value: str):
            self.criteria = check.str_param(criteria, "criteria")
            self.value = check.str_param(value, "value")

    @public
    def __init__(
        self,
        name: str,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        is_sandbox: Optional[bool] = None,
        auth_type: Optional[str] = None,
        start_date: Optional[str] = None,
        streams_criteria: Optional[List[FilterSalesforceObjectsEntry]] = None,
    ):
        """Airbyte Source for Salesforce.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/salesforce

        Args:
            name (str): The name of the destination.
            is_sandbox (Optional[bool]): Toggle if you're using a Salesforce Sandbox
            client_id (str): Enter your Salesforce developer application's Client ID
            client_secret (str): Enter your Salesforce developer application's Client secret
            refresh_token (str): Enter your application's Salesforce Refresh Token used for Airbyte to access your Salesforce account.
            start_date (Optional[str]): Enter the date in the YYYY-MM-DD format. Airbyte will replicate the data added on and after this date. If this field is blank, Airbyte will replicate all data.
            streams_criteria (Optional[List[SalesforceSource.FilterSalesforceObjectsEntry]]): Filter streams relevant to you
        """
        self.is_sandbox = check.opt_bool_param(is_sandbox, "is_sandbox")
        self.auth_type = check.opt_str_param(auth_type, "auth_type")
        self.client_id = check.str_param(client_id, "client_id")
        self.client_secret = check.str_param(client_secret, "client_secret")
        self.refresh_token = check.str_param(refresh_token, "refresh_token")
        self.start_date = check.opt_str_param(start_date, "start_date")
        self.streams_criteria = check.opt_nullable_list_param(
            streams_criteria, "streams_criteria", SalesforceSource.FilterSalesforceObjectsEntry
        )
        super().__init__("Salesforce", name)


class PipedriveSource(GeneratedAirbyteSource):
    class SignInViaPipedriveOAuth:
        @public
        def __init__(self, client_id: str, client_secret: str, refresh_token: str):
            self.auth_type = "Client"
            self.client_id = check.str_param(client_id, "client_id")
            self.client_secret = check.str_param(client_secret, "client_secret")
            self.refresh_token = check.str_param(refresh_token, "refresh_token")

    class APIKeyAuthentication:
        @public
        def __init__(self, api_token: str):
            self.auth_type = "Token"
            self.api_token = check.str_param(api_token, "api_token")

    @public
    def __init__(
        self,
        name: str,
        authorization: Union[
            "PipedriveSource.SignInViaPipedriveOAuth", "PipedriveSource.APIKeyAuthentication"
        ],
        replication_start_date: str,
    ):
        """Airbyte Source for Pipedrive.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/pipedrive

        Args:
            name (str): The name of the destination.
            authorization (Union[PipedriveSource.SignInViaPipedriveOAuth, PipedriveSource.APIKeyAuthentication]): Choose one of the possible authorization method
            replication_start_date (str): UTC date and time in the format 2017-01-25T00:00:00Z. Any data before this date will not be replicated. When specified and not None, then stream will behave as incremental
        """
        self.authorization = check.inst_param(
            authorization,
            "authorization",
            (PipedriveSource.SignInViaPipedriveOAuth, PipedriveSource.APIKeyAuthentication),
        )
        self.replication_start_date = check.str_param(
            replication_start_date, "replication_start_date"
        )
        super().__init__("Pipedrive", name)


class FileSource(GeneratedAirbyteSource):
    class HTTPSPublicWeb:
        @public
        def __init__(self, user_agent: Optional[bool] = None):
            self.storage = "HTTPS"
            self.user_agent = check.opt_bool_param(user_agent, "user_agent")

    class GCSGoogleCloudStorage:
        @public
        def __init__(self, service_account_json: Optional[str] = None):
            self.storage = "GCS"
            self.service_account_json = check.opt_str_param(
                service_account_json, "service_account_json"
            )

    class S3AmazonWebServices:
        @public
        def __init__(
            self,
            aws_access_key_id: Optional[str] = None,
            aws_secret_access_key: Optional[str] = None,
        ):
            self.storage = "S3"
            self.aws_access_key_id = check.opt_str_param(aws_access_key_id, "aws_access_key_id")
            self.aws_secret_access_key = check.opt_str_param(
                aws_secret_access_key, "aws_secret_access_key"
            )

    class AzBlobAzureBlobStorage:
        @public
        def __init__(
            self,
            storage_account: str,
            sas_token: Optional[str] = None,
            shared_key: Optional[str] = None,
        ):
            self.storage = "AzBlob"
            self.storage_account = check.str_param(storage_account, "storage_account")
            self.sas_token = check.opt_str_param(sas_token, "sas_token")
            self.shared_key = check.opt_str_param(shared_key, "shared_key")

    class SSHSecureShell:
        @public
        def __init__(
            self, user: str, host: str, password: Optional[str] = None, port: Optional[str] = None
        ):
            self.storage = "SSH"
            self.user = check.str_param(user, "user")
            self.password = check.opt_str_param(password, "password")
            self.host = check.str_param(host, "host")
            self.port = check.opt_str_param(port, "port")

    class SCPSecureCopyProtocol:
        @public
        def __init__(
            self, user: str, host: str, password: Optional[str] = None, port: Optional[str] = None
        ):
            self.storage = "SCP"
            self.user = check.str_param(user, "user")
            self.password = check.opt_str_param(password, "password")
            self.host = check.str_param(host, "host")
            self.port = check.opt_str_param(port, "port")

    class SFTPSecureFileTransferProtocol:
        @public
        def __init__(
            self, user: str, host: str, password: Optional[str] = None, port: Optional[str] = None
        ):
            self.storage = "SFTP"
            self.user = check.str_param(user, "user")
            self.password = check.opt_str_param(password, "password")
            self.host = check.str_param(host, "host")
            self.port = check.opt_str_param(port, "port")

    class LocalFilesystemLimited:
        @public
        def __init__(
            self,
        ):
            self.storage = "local"

    @public
    def __init__(
        self,
        name: str,
        dataset_name: str,
        format: str,
        url: str,
        provider: Union[
            "FileSource.HTTPSPublicWeb",
            "FileSource.GCSGoogleCloudStorage",
            "FileSource.S3AmazonWebServices",
            "FileSource.AzBlobAzureBlobStorage",
            "FileSource.SSHSecureShell",
            "FileSource.SCPSecureCopyProtocol",
            "FileSource.SFTPSecureFileTransferProtocol",
            "FileSource.LocalFilesystemLimited",
        ],
        reader_options: Optional[str] = None,
    ):
        """Airbyte Source for File.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/file

        Args:
            name (str): The name of the destination.
            dataset_name (str): The Name of the final table to replicate this file into (should include letters, numbers dash and underscores only).
            format (str): The Format of the file which should be replicated (Warning: some formats may be experimental, please refer to the docs).
            reader_options (Optional[str]): This should be a string in JSON format. It depends on the chosen file format to provide additional options and tune its behavior.
            url (str): The URL path to access the file which should be replicated.
            provider (Union[FileSource.HTTPSPublicWeb, FileSource.GCSGoogleCloudStorage, FileSource.S3AmazonWebServices, FileSource.AzBlobAzureBlobStorage, FileSource.SSHSecureShell, FileSource.SCPSecureCopyProtocol, FileSource.SFTPSecureFileTransferProtocol, FileSource.LocalFilesystemLimited]): The storage Provider or Location of the file(s) which should be replicated.
        """
        self.dataset_name = check.str_param(dataset_name, "dataset_name")
        self.format = check.str_param(format, "format")
        self.reader_options = check.opt_str_param(reader_options, "reader_options")
        self.url = check.str_param(url, "url")
        self.provider = check.inst_param(
            provider,
            "provider",
            (
                FileSource.HTTPSPublicWeb,
                FileSource.GCSGoogleCloudStorage,
                FileSource.S3AmazonWebServices,
                FileSource.AzBlobAzureBlobStorage,
                FileSource.SSHSecureShell,
                FileSource.SCPSecureCopyProtocol,
                FileSource.SFTPSecureFileTransferProtocol,
                FileSource.LocalFilesystemLimited,
            ),
        )
        super().__init__("File", name)


class GlassfrogSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, api_key: str):
        """Airbyte Source for Glassfrog.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/glassfrog

        Args:
            name (str): The name of the destination.
            api_key (str): API key provided by Glassfrog
        """
        self.api_key = check.str_param(api_key, "api_key")
        super().__init__("Glassfrog", name)


class ChartmogulSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, api_key: str, start_date: str, interval: str):
        """Airbyte Source for Chartmogul.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/chartmogul

        Args:
            name (str): The name of the destination.
            api_key (str): Chartmogul API key
            start_date (str): UTC date and time in the format 2017-01-25T00:00:00Z. When feasible, any data before this date will not be replicated.
            interval (str): Some APIs such as Metrics require intervals to cluster data.
        """
        self.api_key = check.str_param(api_key, "api_key")
        self.start_date = check.str_param(start_date, "start_date")
        self.interval = check.str_param(interval, "interval")
        super().__init__("Chartmogul", name)


class OrbSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        api_key: str,
        start_date: Optional[str] = None,
        lookback_window_days: Optional[int] = None,
        string_event_properties_keys: Optional[List[str]] = None,
        numeric_event_properties_keys: Optional[List[str]] = None,
    ):
        """Airbyte Source for Orb.

        Documentation can be found at https://docs.withorb.com/

        Args:
            name (str): The name of the destination.
            api_key (str): Orb API Key, issued from the Orb admin console.
            start_date (Optional[str]): UTC date and time in the format 2022-03-01T00:00:00Z. Any data with created_at before this data will not be synced.
            lookback_window_days (Optional[int]): When set to N, the connector will always refresh resources created within the past N days. By default, updated objects that are not newly created are not incrementally synced.
            string_event_properties_keys (Optional[List[str]]): Property key names to extract from all events, in order to enrich ledger entries corresponding to an event deduction.
            numeric_event_properties_keys (Optional[List[str]]): Property key names to extract from all events, in order to enrich ledger entries corresponding to an event deduction.
        """
        self.api_key = check.str_param(api_key, "api_key")
        self.start_date = check.opt_str_param(start_date, "start_date")
        self.lookback_window_days = check.opt_int_param(
            lookback_window_days, "lookback_window_days"
        )
        self.string_event_properties_keys = check.opt_nullable_list_param(
            string_event_properties_keys, "string_event_properties_keys", str
        )
        self.numeric_event_properties_keys = check.opt_nullable_list_param(
            numeric_event_properties_keys, "numeric_event_properties_keys", str
        )
        super().__init__("Orb", name)


class CockroachdbSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        database: str,
        username: str,
        password: Optional[str] = None,
        jdbc_url_params: Optional[str] = None,
        ssl: Optional[bool] = None,
    ):
        """Airbyte Source for Cockroachdb.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/cockroachdb

        Args:
            name (str): The name of the destination.
            host (str): Hostname of the database.
            port (int): Port of the database.
            database (str): Name of the database.
            username (str): Username to use to access the database.
            password (Optional[str]): Password associated with the username.
            jdbc_url_params (Optional[str]): Additional properties to pass to the JDBC URL string when connecting to the database formatted as 'key=value' pairs separated by the symbol '&'. (Eg. key1=value1&key2=value2&key3=value3). For more information read about JDBC URL parameters.
            ssl (Optional[bool]): Encrypt client/server communications for increased security.
        """
        self.host = check.str_param(host, "host")
        self.port = check.int_param(port, "port")
        self.database = check.str_param(database, "database")
        self.username = check.str_param(username, "username")
        self.password = check.opt_str_param(password, "password")
        self.jdbc_url_params = check.opt_str_param(jdbc_url_params, "jdbc_url_params")
        self.ssl = check.opt_bool_param(ssl, "ssl")
        super().__init__("Cockroachdb", name)


class ConfluenceSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, api_token: str, domain_name: str, email: str):
        """Airbyte Source for Confluence.

        Args:
            name (str): The name of the destination.
            api_token (str): Please follow the Jira confluence for generating an API token: https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/
            domain_name (str): Your Confluence domain name
            email (str): Your Confluence login email
        """
        self.api_token = check.str_param(api_token, "api_token")
        self.domain_name = check.str_param(domain_name, "domain_name")
        self.email = check.str_param(email, "email")
        super().__init__("Confluence", name)


class PlaidSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        access_token: str,
        api_key: str,
        client_id: str,
        plaid_env: str,
        start_date: Optional[str] = None,
    ):
        """Airbyte Source for Plaid.

        Documentation can be found at https://plaid.com/docs/api/

        Args:
            name (str): The name of the destination.
            access_token (str): The end-user's Link access token.
            api_key (str): The Plaid API key to use to hit the API.
            client_id (str): The Plaid client id
            plaid_env (str): The Plaid environment
            start_date (Optional[str]): The date from which you'd like to replicate data for Plaid in the format YYYY-MM-DD. All data generated after this date will be replicated.
        """
        self.access_token = check.str_param(access_token, "access_token")
        self.api_key = check.str_param(api_key, "api_key")
        self.client_id = check.str_param(client_id, "client_id")
        self.plaid_env = check.str_param(plaid_env, "plaid_env")
        self.start_date = check.opt_str_param(start_date, "start_date")
        super().__init__("Plaid", name)


class SnapchatMarketingSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ):
        """Airbyte Source for Snapchat Marketing.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/snapchat-marketing

        Args:
            name (str): The name of the destination.
            client_id (str): The Client ID of your Snapchat developer application.
            client_secret (str): The Client Secret of your Snapchat developer application.
            refresh_token (str): Refresh Token to renew the expired Access Token.
            start_date (Optional[str]): Date in the format 2022-01-01. Any data before this date will not be replicated.
            end_date (Optional[str]): Date in the format 2017-01-25. Any data after this date will not be replicated.
        """
        self.client_id = check.str_param(client_id, "client_id")
        self.client_secret = check.str_param(client_secret, "client_secret")
        self.refresh_token = check.str_param(refresh_token, "refresh_token")
        self.start_date = check.opt_str_param(start_date, "start_date")
        self.end_date = check.opt_str_param(end_date, "end_date")
        super().__init__("Snapchat Marketing", name)


class MicrosoftTeamsSource(GeneratedAirbyteSource):
    class AuthenticateViaMicrosoftOAuth20:
        @public
        def __init__(
            self,
            tenant_id: str,
            client_id: str,
            client_secret: str,
            refresh_token: str,
            auth_type: Optional[str] = None,
        ):
            self.auth_type = check.opt_str_param(auth_type, "auth_type")
            self.tenant_id = check.str_param(tenant_id, "tenant_id")
            self.client_id = check.str_param(client_id, "client_id")
            self.client_secret = check.str_param(client_secret, "client_secret")
            self.refresh_token = check.str_param(refresh_token, "refresh_token")

    class AuthenticateViaMicrosoft:
        @public
        def __init__(
            self,
            tenant_id: str,
            client_id: str,
            client_secret: str,
            auth_type: Optional[str] = None,
        ):
            self.auth_type = check.opt_str_param(auth_type, "auth_type")
            self.tenant_id = check.str_param(tenant_id, "tenant_id")
            self.client_id = check.str_param(client_id, "client_id")
            self.client_secret = check.str_param(client_secret, "client_secret")

    @public
    def __init__(
        self,
        name: str,
        period: str,
        credentials: Union[
            "MicrosoftTeamsSource.AuthenticateViaMicrosoftOAuth20",
            "MicrosoftTeamsSource.AuthenticateViaMicrosoft",
        ],
    ):
        """Airbyte Source for Microsoft Teams.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/microsoft-teams

        Args:
            name (str): The name of the destination.
            period (str): Specifies the length of time over which the Team Device Report stream is aggregated. The supported values are: D7, D30, D90, and D180.
            credentials (Union[MicrosoftTeamsSource.AuthenticateViaMicrosoftOAuth20, MicrosoftTeamsSource.AuthenticateViaMicrosoft]): Choose how to authenticate to Microsoft
        """
        self.period = check.str_param(period, "period")
        self.credentials = check.inst_param(
            credentials,
            "credentials",
            (
                MicrosoftTeamsSource.AuthenticateViaMicrosoftOAuth20,
                MicrosoftTeamsSource.AuthenticateViaMicrosoft,
            ),
        )
        super().__init__("Microsoft Teams", name)


class LeverHiringSource(GeneratedAirbyteSource):
    class OAuthCredentials:
        @public
        def __init__(
            self,
            refresh_token: str,
            auth_type: Optional[str] = None,
            client_id: Optional[str] = None,
            client_secret: Optional[str] = None,
        ):
            self.auth_type = check.opt_str_param(auth_type, "auth_type")
            self.client_id = check.opt_str_param(client_id, "client_id")
            self.client_secret = check.opt_str_param(client_secret, "client_secret")
            self.refresh_token = check.str_param(refresh_token, "refresh_token")

    @public
    def __init__(
        self,
        name: str,
        credentials: "LeverHiringSource.OAuthCredentials",
        start_date: str,
        environment: Optional[str] = None,
    ):
        """Airbyte Source for Lever Hiring.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/lever-hiring

        Args:
            name (str): The name of the destination.
            credentials (LeverHiringSource.OAuthCredentials): Choose how to authenticate to Lever Hiring.
            start_date (str): UTC date and time in the format 2017-01-25T00:00:00Z. Any data before this date will not be replicated. Note that it will be used only in the following incremental streams: comments, commits, and issues.
            environment (Optional[str]): The environment in which you'd like to replicate data for Lever. This is used to determine which Lever API endpoint to use.
        """
        self.credentials = check.inst_param(
            credentials, "credentials", LeverHiringSource.OAuthCredentials
        )
        self.start_date = check.str_param(start_date, "start_date")
        self.environment = check.opt_str_param(environment, "environment")
        super().__init__("Lever Hiring", name)


class TwilioSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        account_sid: str,
        auth_token: str,
        start_date: str,
        lookback_window: Optional[int] = None,
    ):
        """Airbyte Source for Twilio.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/twilio

        Args:
            name (str): The name of the destination.
            account_sid (str): Twilio account SID
            auth_token (str): Twilio Auth Token.
            start_date (str): UTC date and time in the format 2020-10-01T00:00:00Z. Any data before this date will not be replicated.
            lookback_window (Optional[int]): How far into the past to look for records. (in minutes)
        """
        self.account_sid = check.str_param(account_sid, "account_sid")
        self.auth_token = check.str_param(auth_token, "auth_token")
        self.start_date = check.str_param(start_date, "start_date")
        self.lookback_window = check.opt_int_param(lookback_window, "lookback_window")
        super().__init__("Twilio", name)


class StripeSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        account_id: str,
        client_secret: str,
        start_date: str,
        lookback_window_days: Optional[int] = None,
        slice_range: Optional[int] = None,
    ):
        r"""Airbyte Source for Stripe.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/stripe

        Args:
            name (str): The name of the destination.
            account_id (str): Your Stripe account ID (starts with 'acct\\_', find yours here).
            client_secret (str): Stripe API key (usually starts with 'sk_live\\_'; find yours here).
            start_date (str): UTC date and time in the format 2017-01-25T00:00:00Z. Only data generated after this date will be replicated.
            lookback_window_days (Optional[int]): When set, the connector will always re-export data from the past N days, where N is the value set here. This is useful if your data is frequently updated after creation. More info here
            slice_range (Optional[int]): The time increment used by the connector when requesting data from the Stripe API. The bigger the value is, the less requests will be made and faster the sync will be. On the other hand, the more seldom the state is persisted.
        """
        self.account_id = check.str_param(account_id, "account_id")
        self.client_secret = check.str_param(client_secret, "client_secret")
        self.start_date = check.str_param(start_date, "start_date")
        self.lookback_window_days = check.opt_int_param(
            lookback_window_days, "lookback_window_days"
        )
        self.slice_range = check.opt_int_param(slice_range, "slice_range")
        super().__init__("Stripe", name)


class Db2Source(GeneratedAirbyteSource):
    class Unencrypted:
        @public
        def __init__(
            self,
        ):
            self.encryption_method = "unencrypted"

    class TLSEncryptedVerifyCertificate:
        @public
        def __init__(self, ssl_certificate: str, key_store_password: Optional[str] = None):
            self.encryption_method = "encrypted_verify_certificate"
            self.ssl_certificate = check.str_param(ssl_certificate, "ssl_certificate")
            self.key_store_password = check.opt_str_param(key_store_password, "key_store_password")

    @public
    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        db: str,
        username: str,
        password: str,
        encryption: Union["Db2Source.Unencrypted", "Db2Source.TLSEncryptedVerifyCertificate"],
        jdbc_url_params: Optional[str] = None,
    ):
        """Airbyte Source for Db2.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/db2

        Args:
            name (str): The name of the destination.
            host (str): Host of the Db2.
            port (int): Port of the database.
            db (str): Name of the database.
            username (str): Username to use to access the database.
            password (str): Password associated with the username.
            jdbc_url_params (Optional[str]): Additional properties to pass to the JDBC URL string when connecting to the database formatted as 'key=value' pairs separated by the symbol '&'. (example: key1=value1&key2=value2&key3=value3).
            encryption (Union[Db2Source.Unencrypted, Db2Source.TLSEncryptedVerifyCertificate]): Encryption method to use when communicating with the database
        """
        self.host = check.str_param(host, "host")
        self.port = check.int_param(port, "port")
        self.db = check.str_param(db, "db")
        self.username = check.str_param(username, "username")
        self.password = check.str_param(password, "password")
        self.jdbc_url_params = check.opt_str_param(jdbc_url_params, "jdbc_url_params")
        self.encryption = check.inst_param(
            encryption,
            "encryption",
            (Db2Source.Unencrypted, Db2Source.TLSEncryptedVerifyCertificate),
        )
        super().__init__("Db2", name)


class SlackSource(GeneratedAirbyteSource):
    class DefaultOAuth20Authorization:
        @public
        def __init__(
            self,
            client_id: str,
            client_secret: str,
            access_token: str,
            refresh_token: Optional[str] = None,
        ):
            self.client_id = check.str_param(client_id, "client_id")
            self.client_secret = check.str_param(client_secret, "client_secret")
            self.access_token = check.str_param(access_token, "access_token")
            self.refresh_token = check.opt_str_param(refresh_token, "refresh_token")

    class APITokenCredentials:
        @public
        def __init__(self, api_token: str):
            self.api_token = check.str_param(api_token, "api_token")

    @public
    def __init__(
        self,
        name: str,
        start_date: str,
        lookback_window: int,
        join_channels: bool,
        credentials: Union[
            "SlackSource.DefaultOAuth20Authorization", "SlackSource.APITokenCredentials"
        ],
        channel_filter: Optional[List[str]] = None,
    ):
        """Airbyte Source for Slack.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/slack

        Args:
            name (str): The name of the destination.
            start_date (str): UTC date and time in the format 2017-01-25T00:00:00Z. Any data before this date will not be replicated.
            lookback_window (int): How far into the past to look for messages in threads.
            join_channels (bool): Whether to join all channels or to sync data only from channels the bot is already in.  If false, you'll need to manually add the bot to all the channels from which you'd like to sync messages.
            channel_filter (Optional[List[str]]): A channel name list (without leading '#' char) which limit the channels from which you'd like to sync. Empty list means no filter.
            credentials (Union[SlackSource.DefaultOAuth20Authorization, SlackSource.APITokenCredentials]): Choose how to authenticate into Slack
        """
        self.start_date = check.str_param(start_date, "start_date")
        self.lookback_window = check.int_param(lookback_window, "lookback_window")
        self.join_channels = check.bool_param(join_channels, "join_channels")
        self.channel_filter = check.opt_nullable_list_param(channel_filter, "channel_filter", str)
        self.credentials = check.inst_param(
            credentials,
            "credentials",
            (SlackSource.DefaultOAuth20Authorization, SlackSource.APITokenCredentials),
        )
        super().__init__("Slack", name)


class RechargeSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, start_date: str, access_token: str):
        """Airbyte Source for Recharge.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/recharge

        Args:
            name (str): The name of the destination.
            start_date (str): The date from which you'd like to replicate data for Recharge API, in the format YYYY-MM-DDT00:00:00Z. Any data before this date will not be replicated.
            access_token (str): The value of the Access Token generated. See the docs for more information.
        """
        self.start_date = check.str_param(start_date, "start_date")
        self.access_token = check.str_param(access_token, "access_token")
        super().__init__("Recharge", name)


class OpenweatherSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        lat: str,
        lon: str,
        appid: str,
        units: Optional[str] = None,
        lang: Optional[str] = None,
    ):
        """Airbyte Source for Openweather.

        Args:
            name (str): The name of the destination.
            lat (str): Latitude for which you want to get weather condition from. (min -90, max 90)
            lon (str): Longitude for which you want to get weather condition from. (min -180, max 180)
            appid (str): Your OpenWeather API Key. See here. The key is case sensitive.
            units (Optional[str]): Units of measurement. standard, metric and imperial units are available. If you do not use the units parameter, standard units will be applied by default.
            lang (Optional[str]): You can use lang parameter to get the output in your language. The contents of the description field will be translated. See here for the list of supported languages.
        """
        self.lat = check.str_param(lat, "lat")
        self.lon = check.str_param(lon, "lon")
        self.appid = check.str_param(appid, "appid")
        self.units = check.opt_str_param(units, "units")
        self.lang = check.opt_str_param(lang, "lang")
        super().__init__("Openweather", name)


class RetentlySource(GeneratedAirbyteSource):
    class AuthenticateViaRetentlyOAuth:
        @public
        def __init__(
            self,
            client_id: str,
            client_secret: str,
            refresh_token: str,
            auth_type: Optional[str] = None,
        ):
            self.auth_type = check.opt_str_param(auth_type, "auth_type")
            self.client_id = check.str_param(client_id, "client_id")
            self.client_secret = check.str_param(client_secret, "client_secret")
            self.refresh_token = check.str_param(refresh_token, "refresh_token")

    class AuthenticateWithAPIToken:
        @public
        def __init__(self, api_key: str, auth_type: Optional[str] = None):
            self.auth_type = check.opt_str_param(auth_type, "auth_type")
            self.api_key = check.str_param(api_key, "api_key")

    @public
    def __init__(
        self,
        name: str,
        credentials: Union[
            "RetentlySource.AuthenticateViaRetentlyOAuth", "RetentlySource.AuthenticateWithAPIToken"
        ],
    ):
        """Airbyte Source for Retently.

        Args:
            name (str): The name of the destination.
            credentials (Union[RetentlySource.AuthenticateViaRetentlyOAuth, RetentlySource.AuthenticateWithAPIToken]): Choose how to authenticate to Retently
        """
        self.credentials = check.inst_param(
            credentials,
            "credentials",
            (RetentlySource.AuthenticateViaRetentlyOAuth, RetentlySource.AuthenticateWithAPIToken),
        )
        super().__init__("Retently", name)


class ScaffoldSourceHttpSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, TODO: str):
        """Airbyte Source for Scaffold Source Http.

        Args:
            name (str): The name of the destination.
            TODO (str): describe me
        """
        self.TODO = check.str_param(TODO, "TODO")
        super().__init__("Scaffold Source Http", name)


class YandexMetricaSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, auth_token: str, counter_id: str, start_date: str, end_date: str):
        """Airbyte Source for Yandex Metrica.

        Args:
            name (str): The name of the destination.
            auth_token (str): Your Yandex Metrica API access token
            counter_id (str): Counter ID
            start_date (str): UTC date and time in the format YYYY-MM-DD.
            end_date (str): UTC date and time in the format YYYY-MM-DD.
        """
        self.auth_token = check.str_param(auth_token, "auth_token")
        self.counter_id = check.str_param(counter_id, "counter_id")
        self.start_date = check.str_param(start_date, "start_date")
        self.end_date = check.str_param(end_date, "end_date")
        super().__init__("Yandex Metrica", name)


class TalkdeskExploreSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        start_date: str,
        auth_url: str,
        api_key: str,
        timezone: Optional[str] = None,
    ):
        """Airbyte Source for Talkdesk Explore.

        Args:
            name (str): The name of the destination.
            start_date (str): The date from which you'd like to replicate data for Talkdesk Explore API, in the format YYYY-MM-DDT00:00:00. All data generated after this date will be replicated.
            timezone (Optional[str]): Timezone to use when generating reports. Only IANA timezones are supported (https://nodatime.org/TimeZones)
            auth_url (str): Talkdesk Auth URL. Only 'client_credentials' auth type supported at the moment.
            api_key (str): Talkdesk API key.
        """
        self.start_date = check.str_param(start_date, "start_date")
        self.timezone = check.opt_str_param(timezone, "timezone")
        self.auth_url = check.str_param(auth_url, "auth_url")
        self.api_key = check.str_param(api_key, "api_key")
        super().__init__("Talkdesk Explore", name)


class ChargifySource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, api_key: str, domain: str):
        """Airbyte Source for Chargify.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/chargify

        Args:
            name (str): The name of the destination.
            api_key (str): Chargify API Key.
            domain (str): Chargify domain. Normally this domain follows the following format companyname.chargify.com
        """
        self.api_key = check.str_param(api_key, "api_key")
        self.domain = check.str_param(domain, "domain")
        super().__init__("Chargify", name)


class RkiCovidSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, start_date: str):
        """Airbyte Source for Rki Covid.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/rki-covid

        Args:
            name (str): The name of the destination.
            start_date (str): UTC date in the format 2017-01-25. Any data before this date will not be replicated.
        """
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Rki Covid", name)


class PostgresSource(GeneratedAirbyteSource):
    class Disable:
        @public
        def __init__(
            self,
        ):
            self.mode = "disable"

    class Allow:
        @public
        def __init__(
            self,
        ):
            self.mode = "allow"

    class Prefer:
        @public
        def __init__(
            self,
        ):
            self.mode = "prefer"

    class Require:
        @public
        def __init__(
            self,
        ):
            self.mode = "require"

    class VerifyCa:
        @public
        def __init__(
            self,
            ca_certificate: str,
            client_certificate: Optional[str] = None,
            client_key: Optional[str] = None,
            client_key_password: Optional[str] = None,
        ):
            self.mode = "verify-ca"
            self.ca_certificate = check.str_param(ca_certificate, "ca_certificate")
            self.client_certificate = check.opt_str_param(client_certificate, "client_certificate")
            self.client_key = check.opt_str_param(client_key, "client_key")
            self.client_key_password = check.opt_str_param(
                client_key_password, "client_key_password"
            )

    class VerifyFull:
        @public
        def __init__(
            self,
            ca_certificate: str,
            client_certificate: Optional[str] = None,
            client_key: Optional[str] = None,
            client_key_password: Optional[str] = None,
        ):
            self.mode = "verify-full"
            self.ca_certificate = check.str_param(ca_certificate, "ca_certificate")
            self.client_certificate = check.opt_str_param(client_certificate, "client_certificate")
            self.client_key = check.opt_str_param(client_key, "client_key")
            self.client_key_password = check.opt_str_param(
                client_key_password, "client_key_password"
            )

    class Standard:
        @public
        def __init__(
            self,
        ):
            self.method = "Standard"

    class LogicalReplicationCDC:
        @public
        def __init__(
            self,
            replication_slot: str,
            publication: str,
            plugin: Optional[str] = None,
            initial_waiting_seconds: Optional[int] = None,
        ):
            self.method = "CDC"
            self.plugin = check.opt_str_param(plugin, "plugin")
            self.replication_slot = check.str_param(replication_slot, "replication_slot")
            self.publication = check.str_param(publication, "publication")
            self.initial_waiting_seconds = check.opt_int_param(
                initial_waiting_seconds, "initial_waiting_seconds"
            )

    class NoTunnel:
        @public
        def __init__(
            self,
        ):
            self.tunnel_method = "NO_TUNNEL"

    class SSHKeyAuthentication:
        @public
        def __init__(self, tunnel_host: str, tunnel_port: int, tunnel_user: str, ssh_key: str):
            self.tunnel_method = "SSH_KEY_AUTH"
            self.tunnel_host = check.str_param(tunnel_host, "tunnel_host")
            self.tunnel_port = check.int_param(tunnel_port, "tunnel_port")
            self.tunnel_user = check.str_param(tunnel_user, "tunnel_user")
            self.ssh_key = check.str_param(ssh_key, "ssh_key")

    class PasswordAuthentication:
        @public
        def __init__(
            self, tunnel_host: str, tunnel_port: int, tunnel_user: str, tunnel_user_password: str
        ):
            self.tunnel_method = "SSH_PASSWORD_AUTH"
            self.tunnel_host = check.str_param(tunnel_host, "tunnel_host")
            self.tunnel_port = check.int_param(tunnel_port, "tunnel_port")
            self.tunnel_user = check.str_param(tunnel_user, "tunnel_user")
            self.tunnel_user_password = check.str_param(
                tunnel_user_password, "tunnel_user_password"
            )

    @public
    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        database: str,
        username: str,
        ssl_mode: Union[
            "PostgresSource.Disable",
            "PostgresSource.Allow",
            "PostgresSource.Prefer",
            "PostgresSource.Require",
            "PostgresSource.VerifyCa",
            "PostgresSource.VerifyFull",
        ],
        replication_method: Union[
            "PostgresSource.Standard", "PostgresSource.LogicalReplicationCDC"
        ],
        tunnel_method: Union[
            "PostgresSource.NoTunnel",
            "PostgresSource.SSHKeyAuthentication",
            "PostgresSource.PasswordAuthentication",
        ],
        schemas: Optional[List[str]] = None,
        password: Optional[str] = None,
        jdbc_url_params: Optional[str] = None,
        ssl: Optional[bool] = None,
    ):
        """Airbyte Source for Postgres.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/postgres

        Args:
            name (str): The name of the destination.
            host (str): Hostname of the database.
            port (int): Port of the database.
            database (str): Name of the database.
            schemas (Optional[List[str]]): The list of schemas (case sensitive) to sync from. Defaults to public.
            username (str): Username to access the database.
            password (Optional[str]): Password associated with the username.
            jdbc_url_params (Optional[str]): Additional properties to pass to the JDBC URL string when connecting to the database formatted as 'key=value' pairs separated by the symbol '&'. (Eg. key1=value1&key2=value2&key3=value3). For more information read about JDBC URL parameters.
            ssl (Optional[bool]): Encrypt data using SSL. When activating SSL, please select one of the connection modes.
            ssl_mode (Union[PostgresSource.Disable, PostgresSource.Allow, PostgresSource.Prefer, PostgresSource.Require, PostgresSource.VerifyCa, PostgresSource.VerifyFull]): SSL connection modes.   disable - Disables encryption of communication between Airbyte and source database  allow - Enables encryption only when required by the source database  prefer - allows unencrypted connection only if the source database does not support encryption  require - Always require encryption. If the source database server does not support encryption, connection will fail   verify-ca - Always require encryption and verifies that the source database server has a valid SSL certificate   verify-full - This is the most secure mode. Always require encryption and verifies the identity of the source database server  Read more  in the docs.
            replication_method (Union[PostgresSource.Standard, PostgresSource.LogicalReplicationCDC]): Replication method for extracting data from the database.
            tunnel_method (Union[PostgresSource.NoTunnel, PostgresSource.SSHKeyAuthentication, PostgresSource.PasswordAuthentication]): Whether to initiate an SSH tunnel before connecting to the database, and if so, which kind of authentication to use.
        """
        self.host = check.str_param(host, "host")
        self.port = check.int_param(port, "port")
        self.database = check.str_param(database, "database")
        self.schemas = check.opt_nullable_list_param(schemas, "schemas", str)
        self.username = check.str_param(username, "username")
        self.password = check.opt_str_param(password, "password")
        self.jdbc_url_params = check.opt_str_param(jdbc_url_params, "jdbc_url_params")
        self.ssl = check.opt_bool_param(ssl, "ssl")
        self.ssl_mode = check.inst_param(
            ssl_mode,
            "ssl_mode",
            (
                PostgresSource.Disable,
                PostgresSource.Allow,
                PostgresSource.Prefer,
                PostgresSource.Require,
                PostgresSource.VerifyCa,
                PostgresSource.VerifyFull,
            ),
        )
        self.replication_method = check.inst_param(
            replication_method,
            "replication_method",
            (PostgresSource.Standard, PostgresSource.LogicalReplicationCDC),
        )
        self.tunnel_method = check.inst_param(
            tunnel_method,
            "tunnel_method",
            (
                PostgresSource.NoTunnel,
                PostgresSource.SSHKeyAuthentication,
                PostgresSource.PasswordAuthentication,
            ),
        )
        super().__init__("Postgres", name)


class TrelloSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        token: str,
        key: str,
        start_date: str,
        board_ids: Optional[List[str]] = None,
    ):
        """Airbyte Source for Trello.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/trello

        Args:
            name (str): The name of the destination.
            token (str): Trello v API token. See the docs for instructions on how to generate it.
            key (str): Trello API key. See the docs for instructions on how to generate it.
            start_date (str): UTC date and time in the format 2017-01-25T00:00:00Z. Any data before this date will not be replicated.
            board_ids (Optional[List[str]]): IDs of the boards to replicate data from. If left empty, data from all boards to which you have access will be replicated.
        """
        self.token = check.str_param(token, "token")
        self.key = check.str_param(key, "key")
        self.start_date = check.str_param(start_date, "start_date")
        self.board_ids = check.opt_nullable_list_param(board_ids, "board_ids", str)
        super().__init__("Trello", name)


class PrestashopSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, url: str, access_key: str):
        """Airbyte Source for Prestashop.

        Args:
            name (str): The name of the destination.
            url (str): Shop URL without trailing slash (domain name or IP address)
            access_key (str): Your PrestaShop access key. See  the docs  for info on how to obtain this.
        """
        self.url = check.str_param(url, "url")
        self.access_key = check.str_param(access_key, "access_key")
        super().__init__("Prestashop", name)


class PaystackSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        secret_key: str,
        start_date: str,
        lookback_window_days: Optional[int] = None,
    ):
        r"""Airbyte Source for Paystack.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/paystack

        Args:
            name (str): The name of the destination.
            secret_key (str): The Paystack API key (usually starts with 'sk_live\\_'; find yours here).
            start_date (str): UTC date and time in the format 2017-01-25T00:00:00Z. Any data before this date will not be replicated.
            lookback_window_days (Optional[int]): When set, the connector will always reload data from the past N days, where N is the value set here. This is useful if your data is updated after creation.
        """
        self.secret_key = check.str_param(secret_key, "secret_key")
        self.start_date = check.str_param(start_date, "start_date")
        self.lookback_window_days = check.opt_int_param(
            lookback_window_days, "lookback_window_days"
        )
        super().__init__("Paystack", name)


class S3Source(GeneratedAirbyteSource):
    class CSV:
        @public
        def __init__(
            self,
            filetype: Optional[str] = None,
            delimiter: Optional[str] = None,
            infer_datatypes: Optional[bool] = None,
            quote_char: Optional[str] = None,
            escape_char: Optional[str] = None,
            encoding: Optional[str] = None,
            double_quote: Optional[bool] = None,
            newlines_in_values: Optional[bool] = None,
            additional_reader_options: Optional[str] = None,
            advanced_options: Optional[str] = None,
            block_size: Optional[int] = None,
        ):
            self.filetype = check.opt_str_param(filetype, "filetype")
            self.delimiter = check.opt_str_param(delimiter, "delimiter")
            self.infer_datatypes = check.opt_bool_param(infer_datatypes, "infer_datatypes")
            self.quote_char = check.opt_str_param(quote_char, "quote_char")
            self.escape_char = check.opt_str_param(escape_char, "escape_char")
            self.encoding = check.opt_str_param(encoding, "encoding")
            self.double_quote = check.opt_bool_param(double_quote, "double_quote")
            self.newlines_in_values = check.opt_bool_param(newlines_in_values, "newlines_in_values")
            self.additional_reader_options = check.opt_str_param(
                additional_reader_options, "additional_reader_options"
            )
            self.advanced_options = check.opt_str_param(advanced_options, "advanced_options")
            self.block_size = check.opt_int_param(block_size, "block_size")

    class Parquet:
        @public
        def __init__(
            self,
            filetype: Optional[str] = None,
            columns: Optional[List[str]] = None,
            batch_size: Optional[int] = None,
            buffer_size: Optional[int] = None,
        ):
            self.filetype = check.opt_str_param(filetype, "filetype")
            self.columns = check.opt_nullable_list_param(columns, "columns", str)
            self.batch_size = check.opt_int_param(batch_size, "batch_size")
            self.buffer_size = check.opt_int_param(buffer_size, "buffer_size")

    class Avro:
        @public
        def __init__(self, filetype: Optional[str] = None):
            self.filetype = check.opt_str_param(filetype, "filetype")

    class Jsonl:
        @public
        def __init__(
            self,
            filetype: Optional[str] = None,
            newlines_in_values: Optional[bool] = None,
            unexpected_field_behavior: Optional[str] = None,
            block_size: Optional[int] = None,
        ):
            self.filetype = check.opt_str_param(filetype, "filetype")
            self.newlines_in_values = check.opt_bool_param(newlines_in_values, "newlines_in_values")
            self.unexpected_field_behavior = check.opt_str_param(
                unexpected_field_behavior, "unexpected_field_behavior"
            )
            self.block_size = check.opt_int_param(block_size, "block_size")

    class S3AmazonWebServices:
        @public
        def __init__(
            self,
            bucket: str,
            aws_access_key_id: Optional[str] = None,
            aws_secret_access_key: Optional[str] = None,
            path_prefix: Optional[str] = None,
            endpoint: Optional[str] = None,
        ):
            self.bucket = check.str_param(bucket, "bucket")
            self.aws_access_key_id = check.opt_str_param(aws_access_key_id, "aws_access_key_id")
            self.aws_secret_access_key = check.opt_str_param(
                aws_secret_access_key, "aws_secret_access_key"
            )
            self.path_prefix = check.opt_str_param(path_prefix, "path_prefix")
            self.endpoint = check.opt_str_param(endpoint, "endpoint")

    @public
    def __init__(
        self,
        name: str,
        dataset: str,
        path_pattern: str,
        format: Union["S3Source.CSV", "S3Source.Parquet", "S3Source.Avro", "S3Source.Jsonl"],
        provider: "S3Source.S3AmazonWebServices",
        schema: Optional[str] = None,
    ):
        """Airbyte Source for S3.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/s3

        Args:
            name (str): The name of the destination.
            dataset (str): The name of the stream you would like this source to output. Can contain letters, numbers, or underscores.
            path_pattern (str): A regular expression which tells the connector which files to replicate. All files which match this pattern will be replicated. Use | to separate multiple patterns. See this page to understand pattern syntax (GLOBSTAR and SPLIT flags are enabled). Use pattern ** to pick up all files.
            format (Union[S3Source.CSV, S3Source.Parquet, S3Source.Avro, S3Source.Jsonl]): The format of the files you'd like to replicate
            schema (Optional[str]): Optionally provide a schema to enforce, as a valid JSON string. Ensure this is a mapping of { "column" : "type" }, where types are valid JSON Schema datatypes. Leave as {} to auto-infer the schema.
            provider (S3Source.S3AmazonWebServices): Use this to load files from S3 or S3-compatible services
        """
        self.dataset = check.str_param(dataset, "dataset")
        self.path_pattern = check.str_param(path_pattern, "path_pattern")
        self.format = check.inst_param(
            format, "format", (S3Source.CSV, S3Source.Parquet, S3Source.Avro, S3Source.Jsonl)
        )
        self.schema = check.opt_str_param(schema, "schema")
        self.provider = check.inst_param(provider, "provider", S3Source.S3AmazonWebServices)
        super().__init__("S3", name)


class SnowflakeSource(GeneratedAirbyteSource):
    class OAuth20:
        @public
        def __init__(
            self,
            client_id: str,
            client_secret: str,
            access_token: Optional[str] = None,
            refresh_token: Optional[str] = None,
        ):
            self.auth_type = "OAuth"
            self.client_id = check.str_param(client_id, "client_id")
            self.client_secret = check.str_param(client_secret, "client_secret")
            self.access_token = check.opt_str_param(access_token, "access_token")
            self.refresh_token = check.opt_str_param(refresh_token, "refresh_token")

    class UsernameAndPassword:
        @public
        def __init__(self, username: str, password: str):
            self.auth_type = "username/password"
            self.username = check.str_param(username, "username")
            self.password = check.str_param(password, "password")

    @public
    def __init__(
        self,
        name: str,
        credentials: Union["SnowflakeSource.OAuth20", "SnowflakeSource.UsernameAndPassword"],
        host: str,
        role: str,
        warehouse: str,
        database: str,
        schema: str,
        jdbc_url_params: Optional[str] = None,
    ):
        """Airbyte Source for Snowflake.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/snowflake

        Args:
            name (str): The name of the destination.
            host (str): The host domain of the snowflake instance (must include the account, region, cloud environment, and end with snowflakecomputing.com).
            role (str): The role you created for Airbyte to access Snowflake.
            warehouse (str): The warehouse you created for Airbyte to access data.
            database (str): The database you created for Airbyte to access data.
            schema (str): The source Snowflake schema tables.
            jdbc_url_params (Optional[str]): Additional properties to pass to the JDBC URL string when connecting to the database formatted as 'key=value' pairs separated by the symbol '&'. (example: key1=value1&key2=value2&key3=value3).
        """
        self.credentials = check.inst_param(
            credentials,
            "credentials",
            (SnowflakeSource.OAuth20, SnowflakeSource.UsernameAndPassword),
        )
        self.host = check.str_param(host, "host")
        self.role = check.str_param(role, "role")
        self.warehouse = check.str_param(warehouse, "warehouse")
        self.database = check.str_param(database, "database")
        self.schema = check.str_param(schema, "schema")
        self.jdbc_url_params = check.opt_str_param(jdbc_url_params, "jdbc_url_params")
        super().__init__("Snowflake", name)


class AmplitudeSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, api_key: str, secret_key: str, start_date: str):
        """Airbyte Source for Amplitude.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/amplitude

        Args:
            name (str): The name of the destination.
            api_key (str): Amplitude API Key. See the setup guide for more information on how to obtain this key.
            secret_key (str): Amplitude Secret Key. See the setup guide for more information on how to obtain this key.
            start_date (str): UTC date and time in the format 2021-01-25T00:00:00Z. Any data before this date will not be replicated.
        """
        self.api_key = check.str_param(api_key, "api_key")
        self.secret_key = check.str_param(secret_key, "secret_key")
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Amplitude", name)


class PosthogSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, start_date: str, api_key: str, base_url: Optional[str] = None):
        """Airbyte Source for Posthog.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/posthog

        Args:
            name (str): The name of the destination.
            start_date (str): The date from which you'd like to replicate the data. Any data before this date will not be replicated.
            api_key (str): API Key. See the docs for information on how to generate this key.
            base_url (Optional[str]): Base PostHog url. Defaults to PostHog Cloud (https://app.posthog.com).
        """
        self.start_date = check.str_param(start_date, "start_date")
        self.api_key = check.str_param(api_key, "api_key")
        self.base_url = check.opt_str_param(base_url, "base_url")
        super().__init__("Posthog", name)


class PaypalTransactionSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        start_date: str,
        is_sandbox: bool,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ):
        """Airbyte Source for Paypal Transaction.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/paypal-transactions

        Args:
            name (str): The name of the destination.
            client_id (Optional[str]): The Client ID of your Paypal developer application.
            client_secret (Optional[str]): The Client Secret of your Paypal developer application.
            refresh_token (Optional[str]): The key to refresh the expired access token.
            start_date (str): Start Date for data extraction in ISO format. Date must be in range from 3 years till 12 hrs before present time.
            is_sandbox (bool): Determines whether to use the sandbox or production environment.
        """
        self.client_id = check.opt_str_param(client_id, "client_id")
        self.client_secret = check.opt_str_param(client_secret, "client_secret")
        self.refresh_token = check.opt_str_param(refresh_token, "refresh_token")
        self.start_date = check.str_param(start_date, "start_date")
        self.is_sandbox = check.bool_param(is_sandbox, "is_sandbox")
        super().__init__("Paypal Transaction", name)


class MssqlSource(GeneratedAirbyteSource):
    class Unencrypted:
        @public
        def __init__(
            self,
        ):
            self.ssl_method = "unencrypted"

    class EncryptedTrustServerCertificate:
        @public
        def __init__(
            self,
        ):
            self.ssl_method = "encrypted_trust_server_certificate"

    class EncryptedVerifyCertificate:
        @public
        def __init__(self, hostNameInCertificate: Optional[str] = None):
            self.ssl_method = "encrypted_verify_certificate"
            self.hostNameInCertificate = check.opt_str_param(
                hostNameInCertificate, "hostNameInCertificate"
            )

    class Standard:
        @public
        def __init__(
            self,
        ):
            self.method = "STANDARD"

    class LogicalReplicationCDC:
        @public
        def __init__(
            self, data_to_sync: Optional[str] = None, snapshot_isolation: Optional[str] = None
        ):
            self.method = "CDC"
            self.data_to_sync = check.opt_str_param(data_to_sync, "data_to_sync")
            self.snapshot_isolation = check.opt_str_param(snapshot_isolation, "snapshot_isolation")

    @public
    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        database: str,
        username: str,
        ssl_method: Union[
            "MssqlSource.Unencrypted",
            "MssqlSource.EncryptedTrustServerCertificate",
            "MssqlSource.EncryptedVerifyCertificate",
        ],
        replication_method: Union["MssqlSource.Standard", "MssqlSource.LogicalReplicationCDC"],
        schemas: Optional[List[str]] = None,
        password: Optional[str] = None,
        jdbc_url_params: Optional[str] = None,
    ):
        """Airbyte Source for Mssql.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/mssql

        Args:
            name (str): The name of the destination.
            host (str): The hostname of the database.
            port (int): The port of the database.
            database (str): The name of the database.
            schemas (Optional[List[str]]): The list of schemas to sync from. Defaults to user. Case sensitive.
            username (str): The username which is used to access the database.
            password (Optional[str]): The password associated with the username.
            jdbc_url_params (Optional[str]): Additional properties to pass to the JDBC URL string when connecting to the database formatted as 'key=value' pairs separated by the symbol '&'. (example: key1=value1&key2=value2&key3=value3).
            ssl_method (Union[MssqlSource.Unencrypted, MssqlSource.EncryptedTrustServerCertificate, MssqlSource.EncryptedVerifyCertificate]): The encryption method which is used when communicating with the database.
            replication_method (Union[MssqlSource.Standard, MssqlSource.LogicalReplicationCDC]): The replication method used for extracting data from the database. STANDARD replication requires no setup on the DB side but will not be able to represent deletions incrementally. CDC uses {TBC} to detect inserts, updates, and deletes. This needs to be configured on the source database itself.
        """
        self.host = check.str_param(host, "host")
        self.port = check.int_param(port, "port")
        self.database = check.str_param(database, "database")
        self.schemas = check.opt_nullable_list_param(schemas, "schemas", str)
        self.username = check.str_param(username, "username")
        self.password = check.opt_str_param(password, "password")
        self.jdbc_url_params = check.opt_str_param(jdbc_url_params, "jdbc_url_params")
        self.ssl_method = check.inst_param(
            ssl_method,
            "ssl_method",
            (
                MssqlSource.Unencrypted,
                MssqlSource.EncryptedTrustServerCertificate,
                MssqlSource.EncryptedVerifyCertificate,
            ),
        )
        self.replication_method = check.inst_param(
            replication_method,
            "replication_method",
            (MssqlSource.Standard, MssqlSource.LogicalReplicationCDC),
        )
        super().__init__("Mssql", name)


class ZohoCrmSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        dc_region: str,
        environment: str,
        edition: str,
        start_datetime: Optional[str] = None,
    ):
        """Airbyte Source for Zoho Crm.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/zoho-crm

        Args:
            name (str): The name of the destination.
            client_id (str): OAuth2.0 Client ID
            client_secret (str): OAuth2.0 Client Secret
            refresh_token (str): OAuth2.0 Refresh Token
            dc_region (str): Please choose the region of your Data Center location. More info by this Link
            environment (str): Please choose the environment
            start_datetime (Optional[str]): ISO 8601, for instance: `YYYY-MM-DD`, `YYYY-MM-DD HH:MM:SS+HH:MM`
            edition (str): Choose your Edition of Zoho CRM to determine API Concurrency Limits
        """
        self.client_id = check.str_param(client_id, "client_id")
        self.client_secret = check.str_param(client_secret, "client_secret")
        self.refresh_token = check.str_param(refresh_token, "refresh_token")
        self.dc_region = check.str_param(dc_region, "dc_region")
        self.environment = check.str_param(environment, "environment")
        self.start_datetime = check.opt_str_param(start_datetime, "start_datetime")
        self.edition = check.str_param(edition, "edition")
        super().__init__("Zoho Crm", name)


class RedshiftSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
        schemas: Optional[List[str]] = None,
        jdbc_url_params: Optional[str] = None,
    ):
        """Airbyte Source for Redshift.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/redshift

        Args:
            name (str): The name of the destination.
            host (str): Host Endpoint of the Redshift Cluster (must include the cluster-id, region and end with .redshift.amazonaws.com).
            port (int): Port of the database.
            database (str): Name of the database.
            schemas (Optional[List[str]]): The list of schemas to sync from. Specify one or more explicitly or keep empty to process all schemas. Schema names are case sensitive.
            username (str): Username to use to access the database.
            password (str): Password associated with the username.
            jdbc_url_params (Optional[str]): Additional properties to pass to the JDBC URL string when connecting to the database formatted as 'key=value' pairs separated by the symbol '&'. (example: key1=value1&key2=value2&key3=value3).
        """
        self.host = check.str_param(host, "host")
        self.port = check.int_param(port, "port")
        self.database = check.str_param(database, "database")
        self.schemas = check.opt_nullable_list_param(schemas, "schemas", str)
        self.username = check.str_param(username, "username")
        self.password = check.str_param(password, "password")
        self.jdbc_url_params = check.opt_str_param(jdbc_url_params, "jdbc_url_params")
        super().__init__("Redshift", name)


class AsanaSource(GeneratedAirbyteSource):
    class PATCredentials:
        @public
        def __init__(self, personal_access_token: str):
            self.personal_access_token = check.str_param(
                personal_access_token, "personal_access_token"
            )

    class OAuthCredentials:
        @public
        def __init__(self, client_id: str, client_secret: str, refresh_token: str):
            self.client_id = check.str_param(client_id, "client_id")
            self.client_secret = check.str_param(client_secret, "client_secret")
            self.refresh_token = check.str_param(refresh_token, "refresh_token")

    @public
    def __init__(
        self,
        name: str,
        credentials: Union["AsanaSource.PATCredentials", "AsanaSource.OAuthCredentials"],
    ):
        """Airbyte Source for Asana.

        Args:
            name (str): The name of the destination.
            credentials (Union[AsanaSource.PATCredentials, AsanaSource.OAuthCredentials]): Choose how to authenticate to Github
        """
        self.credentials = check.inst_param(
            credentials, "credentials", (AsanaSource.PATCredentials, AsanaSource.OAuthCredentials)
        )
        super().__init__("Asana", name)


class SmartsheetsSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        access_token: str,
        spreadsheet_id: str,
        start_datetime: Optional[str] = None,
    ):
        """Airbyte Source for Smartsheets.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/smartsheets

        Args:
            name (str): The name of the destination.
            access_token (str): The access token to use for accessing your data from Smartsheets. This access token must be generated by a user with at least read access to the data you'd like to replicate. Generate an access token in the Smartsheets main menu by clicking Account > Apps & Integrations > API Access. See the setup guide for information on how to obtain this token.
            spreadsheet_id (str): The spreadsheet ID. Find it by opening the spreadsheet then navigating to File > Properties
            start_datetime (Optional[str]): Only rows modified after this date/time will be replicated. This should be an ISO 8601 string, for instance: `2000-01-01T13:00:00`
        """
        self.access_token = check.str_param(access_token, "access_token")
        self.spreadsheet_id = check.str_param(spreadsheet_id, "spreadsheet_id")
        self.start_datetime = check.opt_str_param(start_datetime, "start_datetime")
        super().__init__("Smartsheets", name)


class MailchimpSource(GeneratedAirbyteSource):
    class OAuth20:
        @public
        def __init__(
            self,
            access_token: str,
            client_id: Optional[str] = None,
            client_secret: Optional[str] = None,
        ):
            self.auth_type = "oauth2.0"
            self.client_id = check.opt_str_param(client_id, "client_id")
            self.client_secret = check.opt_str_param(client_secret, "client_secret")
            self.access_token = check.str_param(access_token, "access_token")

    class APIKey:
        @public
        def __init__(self, apikey: str):
            self.auth_type = "apikey"
            self.apikey = check.str_param(apikey, "apikey")

    @public
    def __init__(
        self, name: str, credentials: Union["MailchimpSource.OAuth20", "MailchimpSource.APIKey"]
    ):
        """Airbyte Source for Mailchimp.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/mailchimp

        Args:
            name (str): The name of the destination.

        """
        self.credentials = check.inst_param(
            credentials, "credentials", (MailchimpSource.OAuth20, MailchimpSource.APIKey)
        )
        super().__init__("Mailchimp", name)


class SentrySource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        auth_token: str,
        organization: str,
        project: str,
        hostname: Optional[str] = None,
        discover_fields: Optional[List[str]] = None,
    ):
        """Airbyte Source for Sentry.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/sentry

        Args:
            name (str): The name of the destination.
            auth_token (str): Log into Sentry and then create authentication tokens.For self-hosted, you can find or create authentication tokens by visiting "{instance_url_prefix}/settings/account/api/auth-tokens/"
            hostname (Optional[str]): Host name of Sentry API server.For self-hosted, specify your host name here. Otherwise, leave it empty.
            organization (str): The slug of the organization the groups belong to.
            project (str): The name (slug) of the Project you want to sync.
            discover_fields (Optional[List[str]]): Fields to retrieve when fetching discover events
        """
        self.auth_token = check.str_param(auth_token, "auth_token")
        self.hostname = check.opt_str_param(hostname, "hostname")
        self.organization = check.str_param(organization, "organization")
        self.project = check.str_param(project, "project")
        self.discover_fields = check.opt_nullable_list_param(
            discover_fields, "discover_fields", str
        )
        super().__init__("Sentry", name)


class MailgunSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        private_key: str,
        domain_region: Optional[str] = None,
        start_date: Optional[str] = None,
    ):
        """Airbyte Source for Mailgun.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/mailgun

        Args:
            name (str): The name of the destination.
            private_key (str): Primary account API key to access your Mailgun data.
            domain_region (Optional[str]): Domain region code. 'EU' or 'US' are possible values. The default is 'US'.
            start_date (Optional[str]): UTC date and time in the format 2020-10-01 00:00:00. Any data before this date will not be replicated. If omitted, defaults to 3 days ago.
        """
        self.private_key = check.str_param(private_key, "private_key")
        self.domain_region = check.opt_str_param(domain_region, "domain_region")
        self.start_date = check.opt_str_param(start_date, "start_date")
        super().__init__("Mailgun", name)


class OnesignalSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, user_auth_key: str, start_date: str, outcome_names: str):
        """Airbyte Source for Onesignal.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/onesignal

        Args:
            name (str): The name of the destination.
            user_auth_key (str): OneSignal User Auth Key, see the docs for more information on how to obtain this key.
            start_date (str): The date from which you'd like to replicate data for OneSignal API, in the format YYYY-MM-DDT00:00:00Z. All data generated after this date will be replicated.
            outcome_names (str): Comma-separated list of names and the value (sum/count) for the returned outcome data. See the docs for more details
        """
        self.user_auth_key = check.str_param(user_auth_key, "user_auth_key")
        self.start_date = check.str_param(start_date, "start_date")
        self.outcome_names = check.str_param(outcome_names, "outcome_names")
        super().__init__("Onesignal", name)


class PythonHttpTutorialSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, start_date: str, base: str, access_key: Optional[str] = None):
        """Airbyte Source for Python Http Tutorial.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/exchangeratesapi

        Args:
            name (str): The name of the destination.
            access_key (Optional[str]): API access key used to retrieve data from the Exchange Rates API.
            start_date (str): UTC date and time in the format 2017-01-25. Any data before this date will not be replicated.
            base (str): ISO reference currency. See here.
        """
        self.access_key = check.opt_str_param(access_key, "access_key")
        self.start_date = check.str_param(start_date, "start_date")
        self.base = check.str_param(base, "base")
        super().__init__("Python Http Tutorial", name)


class AirtableSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, api_key: str, base_id: str, tables: List[str]):
        """Airbyte Source for Airtable.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/airtable

        Args:
            name (str): The name of the destination.
            api_key (str): The API Key for the Airtable account. See the Support Guide for more information on how to obtain this key.
            base_id (str): The Base ID to integrate the data from. You can find the Base ID following the link Airtable API, log in to your account, select the base you need and find Base ID in the docs.
            tables (List[str]): The list of Tables to integrate.
        """
        self.api_key = check.str_param(api_key, "api_key")
        self.base_id = check.str_param(base_id, "base_id")
        self.tables = check.list_param(tables, "tables", str)
        super().__init__("Airtable", name)


class MongodbV2Source(GeneratedAirbyteSource):
    class StandaloneMongoDbInstance:
        @public
        def __init__(self, instance: str, host: str, port: int, tls: Optional[bool] = None):
            self.instance = check.str_param(instance, "instance")
            self.host = check.str_param(host, "host")
            self.port = check.int_param(port, "port")
            self.tls = check.opt_bool_param(tls, "tls")

    class ReplicaSet:
        @public
        def __init__(self, instance: str, server_addresses: str, replica_set: Optional[str] = None):
            self.instance = check.str_param(instance, "instance")
            self.server_addresses = check.str_param(server_addresses, "server_addresses")
            self.replica_set = check.opt_str_param(replica_set, "replica_set")

    class MongoDBAtlas:
        @public
        def __init__(self, instance: str, cluster_url: str):
            self.instance = check.str_param(instance, "instance")
            self.cluster_url = check.str_param(cluster_url, "cluster_url")

    @public
    def __init__(
        self,
        name: str,
        instance_type: Union[
            "MongodbV2Source.StandaloneMongoDbInstance",
            "MongodbV2Source.ReplicaSet",
            "MongodbV2Source.MongoDBAtlas",
        ],
        database: str,
        user: Optional[str] = None,
        password: Optional[str] = None,
        auth_source: Optional[str] = None,
    ):
        """Airbyte Source for Mongodb V2.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/mongodb-v2

        Args:
            name (str): The name of the destination.
            instance_type (Union[MongodbV2Source.StandaloneMongoDbInstance, MongodbV2Source.ReplicaSet, MongodbV2Source.MongoDBAtlas]): The MongoDb instance to connect to. For MongoDB Atlas and Replica Set TLS connection is used by default.
            database (str): The database you want to replicate.
            user (Optional[str]): The username which is used to access the database.
            password (Optional[str]): The password associated with this username.
            auth_source (Optional[str]): The authentication source where the user information is stored.
        """
        self.instance_type = check.inst_param(
            instance_type,
            "instance_type",
            (
                MongodbV2Source.StandaloneMongoDbInstance,
                MongodbV2Source.ReplicaSet,
                MongodbV2Source.MongoDBAtlas,
            ),
        )
        self.database = check.str_param(database, "database")
        self.user = check.opt_str_param(user, "user")
        self.password = check.opt_str_param(password, "password")
        self.auth_source = check.opt_str_param(auth_source, "auth_source")
        super().__init__("Mongodb V2", name)


class FileSecureSource(GeneratedAirbyteSource):
    class HTTPSPublicWeb:
        @public
        def __init__(self, user_agent: Optional[bool] = None):
            self.storage = "HTTPS"
            self.user_agent = check.opt_bool_param(user_agent, "user_agent")

    class GCSGoogleCloudStorage:
        @public
        def __init__(self, service_account_json: Optional[str] = None):
            self.storage = "GCS"
            self.service_account_json = check.opt_str_param(
                service_account_json, "service_account_json"
            )

    class S3AmazonWebServices:
        @public
        def __init__(
            self,
            aws_access_key_id: Optional[str] = None,
            aws_secret_access_key: Optional[str] = None,
        ):
            self.storage = "S3"
            self.aws_access_key_id = check.opt_str_param(aws_access_key_id, "aws_access_key_id")
            self.aws_secret_access_key = check.opt_str_param(
                aws_secret_access_key, "aws_secret_access_key"
            )

    class AzBlobAzureBlobStorage:
        @public
        def __init__(
            self,
            storage_account: str,
            sas_token: Optional[str] = None,
            shared_key: Optional[str] = None,
        ):
            self.storage = "AzBlob"
            self.storage_account = check.str_param(storage_account, "storage_account")
            self.sas_token = check.opt_str_param(sas_token, "sas_token")
            self.shared_key = check.opt_str_param(shared_key, "shared_key")

    class SSHSecureShell:
        @public
        def __init__(
            self, user: str, host: str, password: Optional[str] = None, port: Optional[str] = None
        ):
            self.storage = "SSH"
            self.user = check.str_param(user, "user")
            self.password = check.opt_str_param(password, "password")
            self.host = check.str_param(host, "host")
            self.port = check.opt_str_param(port, "port")

    class SCPSecureCopyProtocol:
        @public
        def __init__(
            self, user: str, host: str, password: Optional[str] = None, port: Optional[str] = None
        ):
            self.storage = "SCP"
            self.user = check.str_param(user, "user")
            self.password = check.opt_str_param(password, "password")
            self.host = check.str_param(host, "host")
            self.port = check.opt_str_param(port, "port")

    class SFTPSecureFileTransferProtocol:
        @public
        def __init__(
            self, user: str, host: str, password: Optional[str] = None, port: Optional[str] = None
        ):
            self.storage = "SFTP"
            self.user = check.str_param(user, "user")
            self.password = check.opt_str_param(password, "password")
            self.host = check.str_param(host, "host")
            self.port = check.opt_str_param(port, "port")

    @public
    def __init__(
        self,
        name: str,
        dataset_name: str,
        format: str,
        url: str,
        provider: Union[
            "FileSecureSource.HTTPSPublicWeb",
            "FileSecureSource.GCSGoogleCloudStorage",
            "FileSecureSource.S3AmazonWebServices",
            "FileSecureSource.AzBlobAzureBlobStorage",
            "FileSecureSource.SSHSecureShell",
            "FileSecureSource.SCPSecureCopyProtocol",
            "FileSecureSource.SFTPSecureFileTransferProtocol",
        ],
        reader_options: Optional[str] = None,
    ):
        """Airbyte Source for File Secure.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/file

        Args:
            name (str): The name of the destination.
            dataset_name (str): The Name of the final table to replicate this file into (should include letters, numbers dash and underscores only).
            format (str): The Format of the file which should be replicated (Warning: some formats may be experimental, please refer to the docs).
            reader_options (Optional[str]): This should be a string in JSON format. It depends on the chosen file format to provide additional options and tune its behavior.
            url (str): The URL path to access the file which should be replicated.
            provider (Union[FileSecureSource.HTTPSPublicWeb, FileSecureSource.GCSGoogleCloudStorage, FileSecureSource.S3AmazonWebServices, FileSecureSource.AzBlobAzureBlobStorage, FileSecureSource.SSHSecureShell, FileSecureSource.SCPSecureCopyProtocol, FileSecureSource.SFTPSecureFileTransferProtocol]): The storage Provider or Location of the file(s) which should be replicated.
        """
        self.dataset_name = check.str_param(dataset_name, "dataset_name")
        self.format = check.str_param(format, "format")
        self.reader_options = check.opt_str_param(reader_options, "reader_options")
        self.url = check.str_param(url, "url")
        self.provider = check.inst_param(
            provider,
            "provider",
            (
                FileSecureSource.HTTPSPublicWeb,
                FileSecureSource.GCSGoogleCloudStorage,
                FileSecureSource.S3AmazonWebServices,
                FileSecureSource.AzBlobAzureBlobStorage,
                FileSecureSource.SSHSecureShell,
                FileSecureSource.SCPSecureCopyProtocol,
                FileSecureSource.SFTPSecureFileTransferProtocol,
            ),
        )
        super().__init__("File Secure", name)


class ZendeskSupportSource(GeneratedAirbyteSource):
    class OAuth20:
        @public
        def __init__(self, access_token: str, credentials: Optional[str] = None):
            self.credentials = check.opt_str_param(credentials, "credentials")
            self.access_token = check.str_param(access_token, "access_token")

    class APIToken:
        @public
        def __init__(self, email: str, api_token: str, credentials: Optional[str] = None):
            self.credentials = check.opt_str_param(credentials, "credentials")
            self.email = check.str_param(email, "email")
            self.api_token = check.str_param(api_token, "api_token")

    @public
    def __init__(
        self,
        name: str,
        start_date: str,
        subdomain: str,
        credentials: Union["ZendeskSupportSource.OAuth20", "ZendeskSupportSource.APIToken"],
    ):
        """Airbyte Source for Zendesk Support.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/zendesk-support

        Args:
            name (str): The name of the destination.
            start_date (str): The date from which you'd like to replicate data for Zendesk Support API, in the format YYYY-MM-DDT00:00:00Z. All data generated after this date will be replicated.
            subdomain (str): This is your Zendesk subdomain that can be found in your account URL. For example, in https://{MY_SUBDOMAIN}.zendesk.com/, where MY_SUBDOMAIN is the value of your subdomain.
            credentials (Union[ZendeskSupportSource.OAuth20, ZendeskSupportSource.APIToken]): Zendesk service provides two authentication methods. Choose between: `OAuth2.0` or `API token`.
        """
        self.start_date = check.str_param(start_date, "start_date")
        self.subdomain = check.str_param(subdomain, "subdomain")
        self.credentials = check.inst_param(
            credentials,
            "credentials",
            (ZendeskSupportSource.OAuth20, ZendeskSupportSource.APIToken),
        )
        super().__init__("Zendesk Support", name)


class TempoSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, api_token: str):
        """Airbyte Source for Tempo.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/

        Args:
            name (str): The name of the destination.
            api_token (str): Tempo API Token. Go to Tempo>Settings, scroll down to Data Access and select API integration.
        """
        self.api_token = check.str_param(api_token, "api_token")
        super().__init__("Tempo", name)


class BraintreeSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        merchant_id: str,
        public_key: str,
        private_key: str,
        environment: str,
        start_date: Optional[str] = None,
    ):
        """Airbyte Source for Braintree.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/braintree

        Args:
            name (str): The name of the destination.
            merchant_id (str): The unique identifier for your entire gateway account. See the docs for more information on how to obtain this ID.
            public_key (str): Braintree Public Key. See the docs for more information on how to obtain this key.
            private_key (str): Braintree Private Key. See the docs for more information on how to obtain this key.
            start_date (Optional[str]): UTC date and time in the format 2017-01-25T00:00:00Z. Any data before this date will not be replicated.
            environment (str): Environment specifies where the data will come from.
        """
        self.merchant_id = check.str_param(merchant_id, "merchant_id")
        self.public_key = check.str_param(public_key, "public_key")
        self.private_key = check.str_param(private_key, "private_key")
        self.start_date = check.opt_str_param(start_date, "start_date")
        self.environment = check.str_param(environment, "environment")
        super().__init__("Braintree", name)


class SalesloftSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self, name: str, client_id: str, client_secret: str, refresh_token: str, start_date: str
    ):
        """Airbyte Source for Salesloft.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/salesloft

        Args:
            name (str): The name of the destination.
            client_id (str): The Client ID of your Salesloft developer application.
            client_secret (str): The Client Secret of your Salesloft developer application.
            refresh_token (str): The token for obtaining a new access token.
            start_date (str): The date from which you'd like to replicate data for Salesloft API, in the format YYYY-MM-DDT00:00:00Z. All data generated after this date will be replicated.
        """
        self.client_id = check.str_param(client_id, "client_id")
        self.client_secret = check.str_param(client_secret, "client_secret")
        self.refresh_token = check.str_param(refresh_token, "refresh_token")
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Salesloft", name)


class LinnworksSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self, name: str, application_id: str, application_secret: str, token: str, start_date: str
    ):
        """Airbyte Source for Linnworks.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/linnworks

        Args:
            name (str): The name of the destination.
            application_id (str): Linnworks Application ID
            application_secret (str): Linnworks Application Secret
            start_date (str): UTC date and time in the format 2017-01-25T00:00:00Z. Any data before this date will not be replicated.
        """
        self.application_id = check.str_param(application_id, "application_id")
        self.application_secret = check.str_param(application_secret, "application_secret")
        self.token = check.str_param(token, "token")
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Linnworks", name)


class ChargebeeSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self, name: str, site: str, site_api_key: str, start_date: str, product_catalog: str
    ):
        """Airbyte Source for Chargebee.

        Documentation can be found at https://apidocs.chargebee.com/docs/api

        Args:
            name (str): The name of the destination.
            site (str): The site prefix for your Chargebee instance.
            site_api_key (str): Chargebee API Key. See the docs for more information on how to obtain this key.
            start_date (str): UTC date and time in the format 2021-01-25T00:00:00Z. Any data before this date will not be replicated.
            product_catalog (str): Product Catalog version of your Chargebee site. Instructions on how to find your version you may find here under `API Version` section.
        """
        self.site = check.str_param(site, "site")
        self.site_api_key = check.str_param(site_api_key, "site_api_key")
        self.start_date = check.str_param(start_date, "start_date")
        self.product_catalog = check.str_param(product_catalog, "product_catalog")
        super().__init__("Chargebee", name)


class GoogleAnalyticsDataApiSource(GeneratedAirbyteSource):
    class AuthenticateViaGoogleOauth:
        @public
        def __init__(
            self,
            client_id: str,
            client_secret: str,
            refresh_token: str,
            auth_type: Optional[str] = None,
            access_token: Optional[str] = None,
        ):
            self.auth_type = check.opt_str_param(auth_type, "auth_type")
            self.client_id = check.str_param(client_id, "client_id")
            self.client_secret = check.str_param(client_secret, "client_secret")
            self.refresh_token = check.str_param(refresh_token, "refresh_token")
            self.access_token = check.opt_str_param(access_token, "access_token")

    class ServiceAccountKeyAuthentication:
        @public
        def __init__(self, credentials_json: str, auth_type: Optional[str] = None):
            self.auth_type = check.opt_str_param(auth_type, "auth_type")
            self.credentials_json = check.str_param(credentials_json, "credentials_json")

    @public
    def __init__(
        self,
        name: str,
        property_id: str,
        credentials: Union[
            "GoogleAnalyticsDataApiSource.AuthenticateViaGoogleOauth",
            "GoogleAnalyticsDataApiSource.ServiceAccountKeyAuthentication",
        ],
        date_ranges_start_date: str,
        custom_reports: Optional[str] = None,
        window_in_days: Optional[int] = None,
    ):
        """Airbyte Source for Google Analytics Data Api.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/google-analytics-v4

        Args:
            name (str): The name of the destination.
            property_id (str): A Google Analytics GA4 property identifier whose events are tracked. Specified in the URL path and not the body
            credentials (Union[GoogleAnalyticsDataApiSource.AuthenticateViaGoogleOauth, GoogleAnalyticsDataApiSource.ServiceAccountKeyAuthentication]): Credentials for the service
            date_ranges_start_date (str): The start date. One of the values Ndaysago, yesterday, today or in the format YYYY-MM-DD
            custom_reports (Optional[str]): A JSON array describing the custom reports you want to sync from Google Analytics. See the docs for more information about the exact format you can use to fill out this field.
            window_in_days (Optional[int]): The time increment used by the connector when requesting data from the Google Analytics API. More information is available in the the docs. The bigger this value is, the faster the sync will be, but the more likely that sampling will be applied to your data, potentially causing inaccuracies in the returned results. We recommend setting this to 1 unless you have a hard requirement to make the sync faster at the expense of accuracy. The minimum allowed value for this field is 1, and the maximum is 364.
        """
        self.property_id = check.str_param(property_id, "property_id")
        self.credentials = check.inst_param(
            credentials,
            "credentials",
            (
                GoogleAnalyticsDataApiSource.AuthenticateViaGoogleOauth,
                GoogleAnalyticsDataApiSource.ServiceAccountKeyAuthentication,
            ),
        )
        self.date_ranges_start_date = check.str_param(
            date_ranges_start_date, "date_ranges_start_date"
        )
        self.custom_reports = check.opt_str_param(custom_reports, "custom_reports")
        self.window_in_days = check.opt_int_param(window_in_days, "window_in_days")
        super().__init__("Google Analytics Data Api", name)


class OutreachSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        redirect_uri: str,
        start_date: str,
    ):
        """Airbyte Source for Outreach.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/outreach

        Args:
            name (str): The name of the destination.
            client_id (str): The Client ID of your Outreach developer application.
            client_secret (str): The Client Secret of your Outreach developer application.
            refresh_token (str): The token for obtaining the new access token.
            redirect_uri (str): A Redirect URI is the location where the authorization server sends the user once the app has been successfully authorized and granted an authorization code or access token.
            start_date (str): The date from which you'd like to replicate data for Outreach API, in the format YYYY-MM-DDT00:00:00Z. All data generated after this date will be replicated.
        """
        self.client_id = check.str_param(client_id, "client_id")
        self.client_secret = check.str_param(client_secret, "client_secret")
        self.refresh_token = check.str_param(refresh_token, "refresh_token")
        self.redirect_uri = check.str_param(redirect_uri, "redirect_uri")
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Outreach", name)


class LemlistSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, api_key: str):
        """Airbyte Source for Lemlist.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/lemlist

        Args:
            name (str): The name of the destination.
            api_key (str): Lemlist API key.
        """
        self.api_key = check.str_param(api_key, "api_key")
        super().__init__("Lemlist", name)


class ApifyDatasetSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, datasetId: str, clean: Optional[bool] = None):
        """Airbyte Source for Apify Dataset.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/apify-dataset

        Args:
            name (str): The name of the destination.
            datasetId (str): ID of the dataset you would like to load to Airbyte.
            clean (Optional[bool]): If set to true, only clean items will be downloaded from the dataset. See description of what clean means in Apify API docs. If not sure, set clean to false.
        """
        self.datasetId = check.str_param(datasetId, "datasetId")
        self.clean = check.opt_bool_param(clean, "clean")
        super().__init__("Apify Dataset", name)


class RecurlySource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        api_key: str,
        begin_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ):
        """Airbyte Source for Recurly.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/recurly

        Args:
            name (str): The name of the destination.
            api_key (str): Recurly API Key. See the  docs for more information on how to generate this key.
            begin_time (Optional[str]): ISO8601 timestamp from which the replication from Recurly API will start from.
            end_time (Optional[str]): ISO8601 timestamp to which the replication from Recurly API will stop. Records after that date won't be imported.
        """
        self.api_key = check.str_param(api_key, "api_key")
        self.begin_time = check.opt_str_param(begin_time, "begin_time")
        self.end_time = check.opt_str_param(end_time, "end_time")
        super().__init__("Recurly", name)


class ZendeskTalkSource(GeneratedAirbyteSource):
    class APIToken:
        @public
        def __init__(self, email: str, api_token: str, auth_type: Optional[str] = None):
            self.auth_type = check.opt_str_param(auth_type, "auth_type")
            self.email = check.str_param(email, "email")
            self.api_token = check.str_param(api_token, "api_token")

    class OAuth20:
        @public
        def __init__(self, access_token: str, auth_type: Optional[str] = None):
            self.auth_type = check.opt_str_param(auth_type, "auth_type")
            self.access_token = check.str_param(access_token, "access_token")

    @public
    def __init__(
        self,
        name: str,
        subdomain: str,
        credentials: Union["ZendeskTalkSource.APIToken", "ZendeskTalkSource.OAuth20"],
        start_date: str,
    ):
        """Airbyte Source for Zendesk Talk.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/zendesk-talk

        Args:
            name (str): The name of the destination.
            subdomain (str): This is your Zendesk subdomain that can be found in your account URL. For example, in https://{MY_SUBDOMAIN}.zendesk.com/, where MY_SUBDOMAIN is the value of your subdomain.
            credentials (Union[ZendeskTalkSource.APIToken, ZendeskTalkSource.OAuth20]): Zendesk service provides two authentication methods. Choose between: `OAuth2.0` or `API token`.
            start_date (str): The date from which you'd like to replicate data for Zendesk Talk API, in the format YYYY-MM-DDT00:00:00Z. All data generated after this date will be replicated.
        """
        self.subdomain = check.str_param(subdomain, "subdomain")
        self.credentials = check.inst_param(
            credentials, "credentials", (ZendeskTalkSource.APIToken, ZendeskTalkSource.OAuth20)
        )
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Zendesk Talk", name)


class SftpSource(GeneratedAirbyteSource):
    class PasswordAuthentication:
        @public
        def __init__(self, auth_user_password: str):
            self.auth_method = "SSH_PASSWORD_AUTH"
            self.auth_user_password = check.str_param(auth_user_password, "auth_user_password")

    class SSHKeyAuthentication:
        @public
        def __init__(self, auth_ssh_key: str):
            self.auth_method = "SSH_KEY_AUTH"
            self.auth_ssh_key = check.str_param(auth_ssh_key, "auth_ssh_key")

    @public
    def __init__(
        self,
        name: str,
        user: str,
        host: str,
        port: int,
        credentials: Union["SftpSource.PasswordAuthentication", "SftpSource.SSHKeyAuthentication"],
        file_types: Optional[str] = None,
        folder_path: Optional[str] = None,
        file_pattern: Optional[str] = None,
    ):
        """Airbyte Source for Sftp.

        Documentation can be found at https://docs.airbyte.com/integrations/source/sftp

        Args:
            name (str): The name of the destination.
            user (str): The server user
            host (str): The server host address
            port (int): The server port
            credentials (Union[SftpSource.PasswordAuthentication, SftpSource.SSHKeyAuthentication]): The server authentication method
            file_types (Optional[str]): Coma separated file types. Currently only 'csv' and 'json' types are supported.
            folder_path (Optional[str]): The directory to search files for sync
            file_pattern (Optional[str]): The regular expression to specify files for sync in a chosen Folder Path
        """
        self.user = check.str_param(user, "user")
        self.host = check.str_param(host, "host")
        self.port = check.int_param(port, "port")
        self.credentials = check.inst_param(
            credentials,
            "credentials",
            (SftpSource.PasswordAuthentication, SftpSource.SSHKeyAuthentication),
        )
        self.file_types = check.opt_str_param(file_types, "file_types")
        self.folder_path = check.opt_str_param(folder_path, "folder_path")
        self.file_pattern = check.opt_str_param(file_pattern, "file_pattern")
        super().__init__("Sftp", name)


class WhiskyHunterSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
    ):
        """Airbyte Source for Whisky Hunter.

        Documentation can be found at https://docs.airbyte.io/integrations/sources/whisky-hunter

        Args:
            name (str): The name of the destination.

        """
        super().__init__("Whisky Hunter", name)


class FreshdeskSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        domain: str,
        api_key: str,
        requests_per_minute: Optional[int] = None,
        start_date: Optional[str] = None,
    ):
        """Airbyte Source for Freshdesk.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/freshdesk

        Args:
            name (str): The name of the destination.
            domain (str): Freshdesk domain
            api_key (str): Freshdesk API Key. See the docs for more information on how to obtain this key.
            requests_per_minute (Optional[int]): The number of requests per minute that this source allowed to use. There is a rate limit of 50 requests per minute per app per account.
            start_date (Optional[str]): UTC date and time. Any data created after this date will be replicated. If this parameter is not set, all data will be replicated.
        """
        self.domain = check.str_param(domain, "domain")
        self.api_key = check.str_param(api_key, "api_key")
        self.requests_per_minute = check.opt_int_param(requests_per_minute, "requests_per_minute")
        self.start_date = check.opt_str_param(start_date, "start_date")
        super().__init__("Freshdesk", name)


class GocardlessSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        access_token: str,
        gocardless_environment: str,
        gocardless_version: str,
        start_date: str,
    ):
        """Airbyte Source for Gocardless.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/gocardless

        Args:
            name (str): The name of the destination.
            access_token (str): Gocardless API TOKEN
            gocardless_environment (str): Environment you are trying to connect to.
            gocardless_version (str): GoCardless version. This is a date. You can find the latest here:  https://developer.gocardless.com/api-reference/#api-usage-making-requests
            start_date (str): UTC date and time in the format 2017-01-25T00:00:00Z. Any data before this date will not be replicated.
        """
        self.access_token = check.str_param(access_token, "access_token")
        self.gocardless_environment = check.str_param(
            gocardless_environment, "gocardless_environment"
        )
        self.gocardless_version = check.str_param(gocardless_version, "gocardless_version")
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Gocardless", name)


class ZuoraSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        start_date: str,
        tenant_endpoint: str,
        data_query: str,
        client_id: str,
        client_secret: str,
        window_in_days: Optional[str] = None,
    ):
        """Airbyte Source for Zuora.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/zuora

        Args:
            name (str): The name of the destination.
            start_date (str): Start Date in format: YYYY-MM-DD
            window_in_days (Optional[str]): The amount of days for each data-chunk begining from start_date. Bigger the value - faster the fetch. (0.1 - as for couple of hours, 1 - as for a Day; 364 - as for a Year).
            tenant_endpoint (str): Please choose the right endpoint where your Tenant is located. More info by this Link
            data_query (str): Choose between `Live`, or `Unlimited` - the optimized, replicated database at 12 hours freshness for high volume extraction Link
            client_id (str): Your OAuth user Client ID
            client_secret (str): Your OAuth user Client Secret
        """
        self.start_date = check.str_param(start_date, "start_date")
        self.window_in_days = check.opt_str_param(window_in_days, "window_in_days")
        self.tenant_endpoint = check.str_param(tenant_endpoint, "tenant_endpoint")
        self.data_query = check.str_param(data_query, "data_query")
        self.client_id = check.str_param(client_id, "client_id")
        self.client_secret = check.str_param(client_secret, "client_secret")
        super().__init__("Zuora", name)


class MarketoSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self, name: str, domain_url: str, client_id: str, client_secret: str, start_date: str
    ):
        """Airbyte Source for Marketo.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/marketo

        Args:
            name (str): The name of the destination.
            domain_url (str): Your Marketo Base URL. See  the docs  for info on how to obtain this.
            client_id (str): The Client ID of your Marketo developer application. See  the docs  for info on how to obtain this.
            client_secret (str): The Client Secret of your Marketo developer application. See  the docs  for info on how to obtain this.
            start_date (str): UTC date and time in the format 2017-01-25T00:00:00Z. Any data before this date will not be replicated.
        """
        self.domain_url = check.str_param(domain_url, "domain_url")
        self.client_id = check.str_param(client_id, "client_id")
        self.client_secret = check.str_param(client_secret, "client_secret")
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Marketo", name)


class DriftSource(GeneratedAirbyteSource):
    class OAuth20:
        @public
        def __init__(
            self,
            client_id: str,
            client_secret: str,
            access_token: str,
            refresh_token: str,
            credentials: Optional[str] = None,
        ):
            self.credentials = check.opt_str_param(credentials, "credentials")
            self.client_id = check.str_param(client_id, "client_id")
            self.client_secret = check.str_param(client_secret, "client_secret")
            self.access_token = check.str_param(access_token, "access_token")
            self.refresh_token = check.str_param(refresh_token, "refresh_token")

    class AccessToken:
        @public
        def __init__(self, access_token: str, credentials: Optional[str] = None):
            self.credentials = check.opt_str_param(credentials, "credentials")
            self.access_token = check.str_param(access_token, "access_token")

    @public
    def __init__(
        self, name: str, credentials: Union["DriftSource.OAuth20", "DriftSource.AccessToken"]
    ):
        """Airbyte Source for Drift.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/drift

        Args:
            name (str): The name of the destination.

        """
        self.credentials = check.inst_param(
            credentials, "credentials", (DriftSource.OAuth20, DriftSource.AccessToken)
        )
        super().__init__("Drift", name)


class PokeapiSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, pokemon_name: str):
        """Airbyte Source for Pokeapi.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/pokeapi

        Args:
            name (str): The name of the destination.
            pokemon_name (str): Pokemon requested from the API.
        """
        self.pokemon_name = check.str_param(pokemon_name, "pokemon_name")
        super().__init__("Pokeapi", name)


class NetsuiteSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        realm: str,
        consumer_key: str,
        consumer_secret: str,
        token_key: str,
        token_secret: str,
        start_datetime: str,
        object_types: Optional[List[str]] = None,
        window_in_days: Optional[int] = None,
    ):
        """Airbyte Source for Netsuite.

        Args:
            name (str): The name of the destination.
            realm (str): Netsuite realm e.g. 2344535, as for `production` or 2344535_SB1, as for the `sandbox`
            consumer_key (str): Consumer key associated with your integration
            consumer_secret (str): Consumer secret associated with your integration
            token_key (str): Access token key
            token_secret (str): Access token secret
            object_types (Optional[List[str]]): The API names of the Netsuite objects you want to sync. Setting this speeds up the connection setup process by limiting the number of schemas that need to be retrieved from Netsuite.
            start_datetime (str): Starting point for your data replication, in format of "YYYY-MM-DDTHH:mm:ssZ"
            window_in_days (Optional[int]): The amount of days used to query the data with date chunks. Set smaller value, if you have lots of data.
        """
        self.realm = check.str_param(realm, "realm")
        self.consumer_key = check.str_param(consumer_key, "consumer_key")
        self.consumer_secret = check.str_param(consumer_secret, "consumer_secret")
        self.token_key = check.str_param(token_key, "token_key")
        self.token_secret = check.str_param(token_secret, "token_secret")
        self.object_types = check.opt_nullable_list_param(object_types, "object_types", str)
        self.start_datetime = check.str_param(start_datetime, "start_datetime")
        self.window_in_days = check.opt_int_param(window_in_days, "window_in_days")
        super().__init__("Netsuite", name)


class HubplannerSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, api_key: str):
        """Airbyte Source for Hubplanner.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/hubplanner

        Args:
            name (str): The name of the destination.
            api_key (str): Hubplanner API key. See https://github.com/hubplanner/API#authentication for more details.
        """
        self.api_key = check.str_param(api_key, "api_key")
        super().__init__("Hubplanner", name)


class Dv360Source(GeneratedAirbyteSource):
    class Oauth2Credentials:
        @public
        def __init__(
            self,
            access_token: str,
            refresh_token: str,
            token_uri: str,
            client_id: str,
            client_secret: str,
        ):
            self.access_token = check.str_param(access_token, "access_token")
            self.refresh_token = check.str_param(refresh_token, "refresh_token")
            self.token_uri = check.str_param(token_uri, "token_uri")
            self.client_id = check.str_param(client_id, "client_id")
            self.client_secret = check.str_param(client_secret, "client_secret")

    @public
    def __init__(
        self,
        name: str,
        credentials: "Dv360Source.Oauth2Credentials",
        partner_id: int,
        start_date: str,
        end_date: Optional[str] = None,
        filters: Optional[List[str]] = None,
    ):
        """Airbyte Source for Dv 360.

        Args:
            name (str): The name of the destination.
            credentials (Dv360Source.Oauth2Credentials): Oauth2 credentials
            partner_id (int): Partner ID
            start_date (str): UTC date and time in the format 2017-01-25. Any data before this date will not be replicated
            end_date (Optional[str]): UTC date and time in the format 2017-01-25. Any data after this date will not be replicated.
            filters (Optional[List[str]]): filters for the dimensions. each filter object had 2 keys: 'type' for the name of the dimension to be used as. and 'value' for the value of the filter
        """
        self.credentials = check.inst_param(
            credentials, "credentials", Dv360Source.Oauth2Credentials
        )
        self.partner_id = check.int_param(partner_id, "partner_id")
        self.start_date = check.str_param(start_date, "start_date")
        self.end_date = check.opt_str_param(end_date, "end_date")
        self.filters = check.opt_nullable_list_param(filters, "filters", str)
        super().__init__("Dv 360", name)


class NotionSource(GeneratedAirbyteSource):
    class OAuth20:
        @public
        def __init__(self, client_id: str, client_secret: str, access_token: str):
            self.auth_type = "OAuth2.0"
            self.client_id = check.str_param(client_id, "client_id")
            self.client_secret = check.str_param(client_secret, "client_secret")
            self.access_token = check.str_param(access_token, "access_token")

    class AccessToken:
        @public
        def __init__(self, token: str):
            self.auth_type = "token"
            self.token = check.str_param(token, "token")

    @public
    def __init__(
        self,
        name: str,
        start_date: str,
        credentials: Union["NotionSource.OAuth20", "NotionSource.AccessToken"],
    ):
        """Airbyte Source for Notion.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/notion

        Args:
            name (str): The name of the destination.
            start_date (str): UTC date and time in the format 2017-01-25T00:00:00.000Z. Any data before this date will not be replicated.
            credentials (Union[NotionSource.OAuth20, NotionSource.AccessToken]): Pick an authentication method.
        """
        self.start_date = check.str_param(start_date, "start_date")
        self.credentials = check.inst_param(
            credentials, "credentials", (NotionSource.OAuth20, NotionSource.AccessToken)
        )
        super().__init__("Notion", name)


class ZendeskSunshineSource(GeneratedAirbyteSource):
    class OAuth20:
        @public
        def __init__(self, client_id: str, client_secret: str, access_token: str):
            self.auth_method = "oauth2.0"
            self.client_id = check.str_param(client_id, "client_id")
            self.client_secret = check.str_param(client_secret, "client_secret")
            self.access_token = check.str_param(access_token, "access_token")

    class APIToken:
        @public
        def __init__(self, api_token: str, email: str):
            self.auth_method = "api_token"
            self.api_token = check.str_param(api_token, "api_token")
            self.email = check.str_param(email, "email")

    @public
    def __init__(
        self,
        name: str,
        subdomain: str,
        start_date: str,
        credentials: Union["ZendeskSunshineSource.OAuth20", "ZendeskSunshineSource.APIToken"],
    ):
        """Airbyte Source for Zendesk Sunshine.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/zendesk_sunshine

        Args:
            name (str): The name of the destination.
            subdomain (str): The subdomain for your Zendesk Account.
            start_date (str): The date from which you'd like to replicate data for Zendesk Sunshine API, in the format YYYY-MM-DDT00:00:00Z.
        """
        self.subdomain = check.str_param(subdomain, "subdomain")
        self.start_date = check.str_param(start_date, "start_date")
        self.credentials = check.inst_param(
            credentials,
            "credentials",
            (ZendeskSunshineSource.OAuth20, ZendeskSunshineSource.APIToken),
        )
        super().__init__("Zendesk Sunshine", name)


class PinterestSource(GeneratedAirbyteSource):
    class OAuth20:
        @public
        def __init__(
            self,
            refresh_token: str,
            client_id: Optional[str] = None,
            client_secret: Optional[str] = None,
        ):
            self.auth_method = "oauth2.0"
            self.client_id = check.opt_str_param(client_id, "client_id")
            self.client_secret = check.opt_str_param(client_secret, "client_secret")
            self.refresh_token = check.str_param(refresh_token, "refresh_token")

    class AccessToken:
        @public
        def __init__(self, access_token: str):
            self.auth_method = "access_token"
            self.access_token = check.str_param(access_token, "access_token")

    @public
    def __init__(
        self,
        name: str,
        start_date: str,
        credentials: Union["PinterestSource.OAuth20", "PinterestSource.AccessToken"],
    ):
        """Airbyte Source for Pinterest.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/pinterest

        Args:
            name (str): The name of the destination.
            start_date (str): A date in the format YYYY-MM-DD. If you have not set a date, it would be defaulted to latest allowed date by api (914 days from today).
        """
        self.start_date = check.str_param(start_date, "start_date")
        self.credentials = check.inst_param(
            credentials, "credentials", (PinterestSource.OAuth20, PinterestSource.AccessToken)
        )
        super().__init__("Pinterest", name)


class MetabaseSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        instance_api_url: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        session_token: Optional[str] = None,
    ):
        r"""Airbyte Source for Metabase.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/metabase

        Args:
            name (str): The name of the destination.
            instance_api_url (str): URL to your metabase instance API
            session_token (Optional[str]): To generate your session token, you need to run the following command: ``` curl -X POST \\   -H "Content-Type: application/json" \\   -d '{"username": "person@metabase.com", "password": "fakepassword"}' \\   http://localhost:3000/api/session ``` Then copy the value of the `id` field returned by a successful call to that API. Note that by default, sessions are good for 14 days and needs to be regenerated.
        """
        self.instance_api_url = check.str_param(instance_api_url, "instance_api_url")
        self.username = check.opt_str_param(username, "username")
        self.password = check.opt_str_param(password, "password")
        self.session_token = check.opt_str_param(session_token, "session_token")
        super().__init__("Metabase", name)


class HubspotSource(GeneratedAirbyteSource):
    class OAuth:
        @public
        def __init__(self, client_id: str, client_secret: str, refresh_token: str):
            self.credentials_title = "OAuth Credentials"
            self.client_id = check.str_param(client_id, "client_id")
            self.client_secret = check.str_param(client_secret, "client_secret")
            self.refresh_token = check.str_param(refresh_token, "refresh_token")

    class APIKey:
        @public
        def __init__(self, api_key: str):
            self.credentials_title = "API Key Credentials"
            self.api_key = check.str_param(api_key, "api_key")

    class PrivateAPP:
        @public
        def __init__(self, access_token: str):
            self.credentials_title = "Private App Credentials"
            self.access_token = check.str_param(access_token, "access_token")

    @public
    def __init__(
        self,
        name: str,
        start_date: str,
        credentials: Union[
            "HubspotSource.OAuth", "HubspotSource.APIKey", "HubspotSource.PrivateAPP"
        ],
    ):
        """Airbyte Source for Hubspot.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/hubspot

        Args:
            name (str): The name of the destination.
            start_date (str): UTC date and time in the format 2017-01-25T00:00:00Z. Any data before this date will not be replicated.
            credentials (Union[HubspotSource.OAuth, HubspotSource.APIKey, HubspotSource.PrivateAPP]): Choose how to authenticate to HubSpot.
        """
        self.start_date = check.str_param(start_date, "start_date")
        self.credentials = check.inst_param(
            credentials,
            "credentials",
            (HubspotSource.OAuth, HubspotSource.APIKey, HubspotSource.PrivateAPP),
        )
        super().__init__("Hubspot", name)


class HarvestSource(GeneratedAirbyteSource):
    class AuthenticateViaHarvestOAuth:
        @public
        def __init__(
            self,
            client_id: str,
            client_secret: str,
            refresh_token: str,
            auth_type: Optional[str] = None,
        ):
            self.auth_type = check.opt_str_param(auth_type, "auth_type")
            self.client_id = check.str_param(client_id, "client_id")
            self.client_secret = check.str_param(client_secret, "client_secret")
            self.refresh_token = check.str_param(refresh_token, "refresh_token")

    class AuthenticateWithPersonalAccessToken:
        @public
        def __init__(self, api_token: str, auth_type: Optional[str] = None):
            self.auth_type = check.opt_str_param(auth_type, "auth_type")
            self.api_token = check.str_param(api_token, "api_token")

    @public
    def __init__(
        self,
        name: str,
        account_id: str,
        replication_start_date: str,
        credentials: Union[
            "HarvestSource.AuthenticateViaHarvestOAuth",
            "HarvestSource.AuthenticateWithPersonalAccessToken",
        ],
    ):
        """Airbyte Source for Harvest.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/harvest

        Args:
            name (str): The name of the destination.
            account_id (str): Harvest account ID. Required for all Harvest requests in pair with Personal Access Token
            replication_start_date (str): UTC date and time in the format 2017-01-25T00:00:00Z. Any data before this date will not be replicated.
            credentials (Union[HarvestSource.AuthenticateViaHarvestOAuth, HarvestSource.AuthenticateWithPersonalAccessToken]): Choose how to authenticate to Harvest.
        """
        self.account_id = check.str_param(account_id, "account_id")
        self.replication_start_date = check.str_param(
            replication_start_date, "replication_start_date"
        )
        self.credentials = check.inst_param(
            credentials,
            "credentials",
            (
                HarvestSource.AuthenticateViaHarvestOAuth,
                HarvestSource.AuthenticateWithPersonalAccessToken,
            ),
        )
        super().__init__("Harvest", name)


class GithubSource(GeneratedAirbyteSource):
    class OAuthCredentials:
        @public
        def __init__(self, access_token: str):
            self.access_token = check.str_param(access_token, "access_token")

    class PATCredentials:
        @public
        def __init__(self, personal_access_token: str):
            self.personal_access_token = check.str_param(
                personal_access_token, "personal_access_token"
            )

    @public
    def __init__(
        self,
        name: str,
        credentials: Union["GithubSource.OAuthCredentials", "GithubSource.PATCredentials"],
        start_date: str,
        repository: str,
        branch: Optional[str] = None,
        page_size_for_large_streams: Optional[int] = None,
    ):
        """Airbyte Source for Github.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/github

        Args:
            name (str): The name of the destination.
            credentials (Union[GithubSource.OAuthCredentials, GithubSource.PATCredentials]): Choose how to authenticate to GitHub
            start_date (str): The date from which you'd like to replicate data from GitHub in the format YYYY-MM-DDT00:00:00Z. For the streams which support this configuration, only data generated on or after the start date will be replicated. This field doesn't apply to all streams, see the docs for more info
            repository (str): Space-delimited list of GitHub organizations/repositories, e.g. `airbytehq/airbyte` for single repository, `airbytehq/*` for get all repositories from organization and `airbytehq/airbyte airbytehq/another-repo` for multiple repositories.
            branch (Optional[str]): Space-delimited list of GitHub repository branches to pull commits for, e.g. `airbytehq/airbyte/master`. If no branches are specified for a repository, the default branch will be pulled.
            page_size_for_large_streams (Optional[int]): The Github connector contains several streams with a large amount of data. The page size of such streams depends on the size of your repository. We recommended that you specify values between 10 and 30.
        """
        self.credentials = check.inst_param(
            credentials, "credentials", (GithubSource.OAuthCredentials, GithubSource.PATCredentials)
        )
        self.start_date = check.str_param(start_date, "start_date")
        self.repository = check.str_param(repository, "repository")
        self.branch = check.opt_str_param(branch, "branch")
        self.page_size_for_large_streams = check.opt_int_param(
            page_size_for_large_streams, "page_size_for_large_streams"
        )
        super().__init__("Github", name)


class E2eTestSource(GeneratedAirbyteSource):
    class SingleSchema:
        @public
        def __init__(
            self, stream_name: str, stream_schema: str, stream_duplication: Optional[int] = None
        ):
            self.type = "SINGLE_STREAM"
            self.stream_name = check.str_param(stream_name, "stream_name")
            self.stream_schema = check.str_param(stream_schema, "stream_schema")
            self.stream_duplication = check.opt_int_param(stream_duplication, "stream_duplication")

    class MultiSchema:
        @public
        def __init__(self, stream_schemas: str):
            self.type = "MULTI_STREAM"
            self.stream_schemas = check.str_param(stream_schemas, "stream_schemas")

    @public
    def __init__(
        self,
        name: str,
        max_messages: int,
        mock_catalog: Union["E2eTestSource.SingleSchema", "E2eTestSource.MultiSchema"],
        type: Optional[str] = None,
        seed: Optional[int] = None,
        message_interval_ms: Optional[int] = None,
    ):
        """Airbyte Source for E2e Test.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/e2e-test

        Args:
            name (str): The name of the destination.
            max_messages (int): Number of records to emit per stream. Min 1. Max 100 billion.
            seed (Optional[int]): When the seed is unspecified, the current time millis will be used as the seed. Range: [0, 1000000].
            message_interval_ms (Optional[int]): Interval between messages in ms. Min 0 ms. Max 60000 ms (1 minute).
        """
        self.type = check.opt_str_param(type, "type")
        self.max_messages = check.int_param(max_messages, "max_messages")
        self.seed = check.opt_int_param(seed, "seed")
        self.message_interval_ms = check.opt_int_param(message_interval_ms, "message_interval_ms")
        self.mock_catalog = check.inst_param(
            mock_catalog, "mock_catalog", (E2eTestSource.SingleSchema, E2eTestSource.MultiSchema)
        )
        super().__init__("E2e Test", name)


class MysqlSource(GeneratedAirbyteSource):
    class Preferred:
        @public
        def __init__(
            self,
        ):
            self.mode = "preferred"

    class Required:
        @public
        def __init__(
            self,
        ):
            self.mode = "required"

    class VerifyCA:
        @public
        def __init__(
            self,
            ca_certificate: str,
            client_certificate: Optional[str] = None,
            client_key: Optional[str] = None,
            client_key_password: Optional[str] = None,
        ):
            self.mode = "verify_ca"
            self.ca_certificate = check.str_param(ca_certificate, "ca_certificate")
            self.client_certificate = check.opt_str_param(client_certificate, "client_certificate")
            self.client_key = check.opt_str_param(client_key, "client_key")
            self.client_key_password = check.opt_str_param(
                client_key_password, "client_key_password"
            )

    class VerifyIdentity:
        @public
        def __init__(
            self,
            ca_certificate: str,
            client_certificate: Optional[str] = None,
            client_key: Optional[str] = None,
            client_key_password: Optional[str] = None,
        ):
            self.mode = "verify_identity"
            self.ca_certificate = check.str_param(ca_certificate, "ca_certificate")
            self.client_certificate = check.opt_str_param(client_certificate, "client_certificate")
            self.client_key = check.opt_str_param(client_key, "client_key")
            self.client_key_password = check.opt_str_param(
                client_key_password, "client_key_password"
            )

    class Standard:
        @public
        def __init__(
            self,
        ):
            self.method = "STANDARD"

    class LogicalReplicationCDC:
        @public
        def __init__(
            self,
            initial_waiting_seconds: Optional[int] = None,
            server_time_zone: Optional[str] = None,
        ):
            self.method = "CDC"
            self.initial_waiting_seconds = check.opt_int_param(
                initial_waiting_seconds, "initial_waiting_seconds"
            )
            self.server_time_zone = check.opt_str_param(server_time_zone, "server_time_zone")

    @public
    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        database: str,
        username: str,
        ssl_mode: Union[
            "MysqlSource.Preferred",
            "MysqlSource.Required",
            "MysqlSource.VerifyCA",
            "MysqlSource.VerifyIdentity",
        ],
        replication_method: Union["MysqlSource.Standard", "MysqlSource.LogicalReplicationCDC"],
        password: Optional[str] = None,
        jdbc_url_params: Optional[str] = None,
        ssl: Optional[bool] = None,
    ):
        """Airbyte Source for Mysql.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/mysql

        Args:
            name (str): The name of the destination.
            host (str): The host name of the database.
            port (int): The port to connect to.
            database (str): The database name.
            username (str): The username which is used to access the database.
            password (Optional[str]): The password associated with the username.
            jdbc_url_params (Optional[str]): Additional properties to pass to the JDBC URL string when connecting to the database formatted as 'key=value' pairs separated by the symbol '&'. (example: key1=value1&key2=value2&key3=value3). For more information read about JDBC URL parameters.
            ssl (Optional[bool]): Encrypt data using SSL.
            ssl_mode (Union[MysqlSource.Preferred, MysqlSource.Required, MysqlSource.VerifyCA, MysqlSource.VerifyIdentity]): SSL connection modes. preferred - Automatically attempt SSL connection. If the MySQL server does not support SSL, continue with a regular connection.required - Always connect with SSL. If the MySQL server doesn`t support SSL, the connection will not be established. Certificate Authority (CA) and Hostname are not verified.verify-ca - Always connect with SSL. Verifies CA, but allows connection even if Hostname does not match.Verify Identity - Always connect with SSL. Verify both CA and Hostname.Read more  in the docs.
            replication_method (Union[MysqlSource.Standard, MysqlSource.LogicalReplicationCDC]): Replication method to use for extracting data from the database.
        """
        self.host = check.str_param(host, "host")
        self.port = check.int_param(port, "port")
        self.database = check.str_param(database, "database")
        self.username = check.str_param(username, "username")
        self.password = check.opt_str_param(password, "password")
        self.jdbc_url_params = check.opt_str_param(jdbc_url_params, "jdbc_url_params")
        self.ssl = check.opt_bool_param(ssl, "ssl")
        self.ssl_mode = check.inst_param(
            ssl_mode,
            "ssl_mode",
            (
                MysqlSource.Preferred,
                MysqlSource.Required,
                MysqlSource.VerifyCA,
                MysqlSource.VerifyIdentity,
            ),
        )
        self.replication_method = check.inst_param(
            replication_method,
            "replication_method",
            (MysqlSource.Standard, MysqlSource.LogicalReplicationCDC),
        )
        super().__init__("Mysql", name)


class MyHoursSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        email: str,
        password: str,
        start_date: str,
        logs_batch_size: Optional[int] = None,
    ):
        """Airbyte Source for My Hours.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/my-hours

        Args:
            name (str): The name of the destination.
            email (str): Your My Hours username
            password (str): The password associated to the username
            start_date (str): Start date for collecting time logs
            logs_batch_size (Optional[int]): Pagination size used for retrieving logs in days
        """
        self.email = check.str_param(email, "email")
        self.password = check.str_param(password, "password")
        self.start_date = check.str_param(start_date, "start_date")
        self.logs_batch_size = check.opt_int_param(logs_batch_size, "logs_batch_size")
        super().__init__("My Hours", name)


class KyribaSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        domain: str,
        username: str,
        password: str,
        start_date: str,
        end_date: Optional[str] = None,
    ):
        """Airbyte Source for Kyriba.

        Args:
            name (str): The name of the destination.
            domain (str): Kyriba domain
            username (str): Username to be used in basic auth
            password (str): Password to be used in basic auth
            start_date (str): The date the sync should start from.
            end_date (Optional[str]): The date the sync should end. If let empty the sync will run to the current date.
        """
        self.domain = check.str_param(domain, "domain")
        self.username = check.str_param(username, "username")
        self.password = check.str_param(password, "password")
        self.start_date = check.str_param(start_date, "start_date")
        self.end_date = check.opt_str_param(end_date, "end_date")
        super().__init__("Kyriba", name)


class GoogleSearchConsoleSource(GeneratedAirbyteSource):
    class OAuth:
        @public
        def __init__(
            self,
            client_id: str,
            client_secret: str,
            refresh_token: str,
            access_token: Optional[str] = None,
        ):
            self.auth_type = "Client"
            self.client_id = check.str_param(client_id, "client_id")
            self.client_secret = check.str_param(client_secret, "client_secret")
            self.access_token = check.opt_str_param(access_token, "access_token")
            self.refresh_token = check.str_param(refresh_token, "refresh_token")

    class ServiceAccountKeyAuthentication:
        @public
        def __init__(self, service_account_info: str, email: str):
            self.auth_type = "Service"
            self.service_account_info = check.str_param(
                service_account_info, "service_account_info"
            )
            self.email = check.str_param(email, "email")

    @public
    def __init__(
        self,
        name: str,
        site_urls: List[str],
        start_date: str,
        authorization: Union[
            "GoogleSearchConsoleSource.OAuth",
            "GoogleSearchConsoleSource.ServiceAccountKeyAuthentication",
        ],
        end_date: Optional[str] = None,
        custom_reports: Optional[str] = None,
    ):
        """Airbyte Source for Google Search Console.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/google-search-console

        Args:
            name (str): The name of the destination.
            site_urls (List[str]): The URLs of the website property attached to your GSC account. Read more here.
            start_date (str): UTC date in the format 2017-01-25. Any data before this date will not be replicated.
            end_date (Optional[str]): UTC date in the format 2017-01-25. Any data after this date will not be replicated. Must be greater or equal to the start date field.
            custom_reports (Optional[str]): A JSON array describing the custom reports you want to sync from Google Search Console. See the docs for more information about the exact format you can use to fill out this field.
        """
        self.site_urls = check.list_param(site_urls, "site_urls", str)
        self.start_date = check.str_param(start_date, "start_date")
        self.end_date = check.opt_str_param(end_date, "end_date")
        self.authorization = check.inst_param(
            authorization,
            "authorization",
            (
                GoogleSearchConsoleSource.OAuth,
                GoogleSearchConsoleSource.ServiceAccountKeyAuthentication,
            ),
        )
        self.custom_reports = check.opt_str_param(custom_reports, "custom_reports")
        super().__init__("Google Search Console", name)


class FacebookMarketingSource(GeneratedAirbyteSource):
    class InsightConfig:
        @public
        def __init__(
            self,
            name: str,
            fields: Optional[List[str]] = None,
            breakdowns: Optional[List[str]] = None,
            action_breakdowns: Optional[List[str]] = None,
            time_increment: Optional[int] = None,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            insights_lookback_window: Optional[int] = None,
        ):
            self.name = check.str_param(name, "name")
            self.fields = check.opt_nullable_list_param(fields, "fields", str)
            self.breakdowns = check.opt_nullable_list_param(breakdowns, "breakdowns", str)
            self.action_breakdowns = check.opt_nullable_list_param(
                action_breakdowns, "action_breakdowns", str
            )
            self.time_increment = check.opt_int_param(time_increment, "time_increment")
            self.start_date = check.opt_str_param(start_date, "start_date")
            self.end_date = check.opt_str_param(end_date, "end_date")
            self.insights_lookback_window = check.opt_int_param(
                insights_lookback_window, "insights_lookback_window"
            )

    @public
    def __init__(
        self,
        name: str,
        account_id: str,
        start_date: str,
        access_token: str,
        end_date: Optional[str] = None,
        include_deleted: Optional[bool] = None,
        fetch_thumbnail_images: Optional[bool] = None,
        custom_insights: Optional[List[InsightConfig]] = None,
        page_size: Optional[int] = None,
        insights_lookback_window: Optional[int] = None,
        max_batch_size: Optional[int] = None,
    ):
        """Airbyte Source for Facebook Marketing.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/facebook-marketing

        Args:
            name (str): The name of the destination.
            account_id (str): The Facebook Ad account ID to use when pulling data from the Facebook Marketing API.
            start_date (str): The date from which you'd like to replicate data for all incremental streams, in the format YYYY-MM-DDT00:00:00Z. All data generated after this date will be replicated.
            end_date (Optional[str]): The date until which you'd like to replicate data for all incremental streams, in the format YYYY-MM-DDT00:00:00Z. All data generated between start_date and this date will be replicated. Not setting this option will result in always syncing the latest data.
            access_token (str): The value of the access token generated. See the docs for more information
            include_deleted (Optional[bool]): Include data from deleted Campaigns, Ads, and AdSets
            fetch_thumbnail_images (Optional[bool]): In each Ad Creative, fetch the thumbnail_url and store the result in thumbnail_data_url
            custom_insights (Optional[List[FacebookMarketingSource.InsightConfig]]): A list which contains insights entries, each entry must have a name and can contains fields, breakdowns or action_breakdowns)
            page_size (Optional[int]): Page size used when sending requests to Facebook API to specify number of records per page when response has pagination. Most users do not need to set this field unless they specifically need to tune the connector to address specific issues or use cases.
            insights_lookback_window (Optional[int]): The attribution window
            max_batch_size (Optional[int]): Maximum batch size used when sending batch requests to Facebook API. Most users do not need to set this field unless they specifically need to tune the connector to address specific issues or use cases.
        """
        self.account_id = check.str_param(account_id, "account_id")
        self.start_date = check.str_param(start_date, "start_date")
        self.end_date = check.opt_str_param(end_date, "end_date")
        self.access_token = check.str_param(access_token, "access_token")
        self.include_deleted = check.opt_bool_param(include_deleted, "include_deleted")
        self.fetch_thumbnail_images = check.opt_bool_param(
            fetch_thumbnail_images, "fetch_thumbnail_images"
        )
        self.custom_insights = check.opt_nullable_list_param(
            custom_insights, "custom_insights", FacebookMarketingSource.InsightConfig
        )
        self.page_size = check.opt_int_param(page_size, "page_size")
        self.insights_lookback_window = check.opt_int_param(
            insights_lookback_window, "insights_lookback_window"
        )
        self.max_batch_size = check.opt_int_param(max_batch_size, "max_batch_size")
        super().__init__("Facebook Marketing", name)


class SurveymonkeySource(GeneratedAirbyteSource):
    @public
    def __init__(
        self, name: str, access_token: str, start_date: str, survey_ids: Optional[List[str]] = None
    ):
        """Airbyte Source for Surveymonkey.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/surveymonkey

        Args:
            name (str): The name of the destination.
            access_token (str): Access Token for making authenticated requests. See the docs for information on how to generate this key.
            start_date (str): UTC date and time in the format 2017-01-25T00:00:00Z. Any data before this date will not be replicated.
            survey_ids (Optional[List[str]]): IDs of the surveys from which you'd like to replicate data. If left empty, data from all boards to which you have access will be replicated.
        """
        self.access_token = check.str_param(access_token, "access_token")
        self.start_date = check.str_param(start_date, "start_date")
        self.survey_ids = check.opt_nullable_list_param(survey_ids, "survey_ids", str)
        super().__init__("Surveymonkey", name)


class PardotSource(GeneratedAirbyteSource):
    @public
    def __init__(
        self,
        name: str,
        pardot_business_unit_id: str,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        start_date: Optional[str] = None,
        is_sandbox: Optional[bool] = None,
    ):
        """Airbyte Source for Pardot.

        Args:
            name (str): The name of the destination.
            pardot_business_unit_id (str): Pardot Business ID, can be found at Setup > Pardot > Pardot Account Setup
            client_id (str): The Consumer Key that can be found when viewing your app in Salesforce
            client_secret (str): The Consumer Secret that can be found when viewing your app in Salesforce
            refresh_token (str): Salesforce Refresh Token used for Airbyte to access your Salesforce account. If you don't know what this is, follow this guide to retrieve it.
            start_date (Optional[str]): UTC date and time in the format 2017-01-25T00:00:00Z. Any data before this date will not be replicated. Leave blank to skip this filter
            is_sandbox (Optional[bool]): Whether or not the the app is in a Salesforce sandbox. If you do not know what this, assume it is false.
        """
        self.pardot_business_unit_id = check.str_param(
            pardot_business_unit_id, "pardot_business_unit_id"
        )
        self.client_id = check.str_param(client_id, "client_id")
        self.client_secret = check.str_param(client_secret, "client_secret")
        self.refresh_token = check.str_param(refresh_token, "refresh_token")
        self.start_date = check.opt_str_param(start_date, "start_date")
        self.is_sandbox = check.opt_bool_param(is_sandbox, "is_sandbox")
        super().__init__("Pardot", name)


class FlexportSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, api_key: str, start_date: str):
        """Airbyte Source for Flexport.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/flexport

        Args:
            name (str): The name of the destination.

        """
        self.api_key = check.str_param(api_key, "api_key")
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Flexport", name)


class ZenefitsSource(GeneratedAirbyteSource):
    @public
    def __init__(self, name: str, token: str):
        """Airbyte Source for Zenefits.

        Args:
            name (str): The name of the destination.
            token (str): Use Sync with Zenefits button on the link given on the readme file, and get the token to access the api
        """
        self.token = check.str_param(token, "token")
        super().__init__("Zenefits", name)


class KafkaSource(GeneratedAirbyteSource):
    class JSON:
        @public
        def __init__(self, deserialization_type: Optional[str] = None):
            self.deserialization_type = check.opt_str_param(
                deserialization_type, "deserialization_type"
            )

    class AVRO:
        @public
        def __init__(
            self,
            deserialization_type: Optional[str] = None,
            deserialization_strategy: Optional[str] = None,
            schema_registry_url: Optional[str] = None,
            schema_registry_username: Optional[str] = None,
            schema_registry_password: Optional[str] = None,
        ):
            self.deserialization_type = check.opt_str_param(
                deserialization_type, "deserialization_type"
            )
            self.deserialization_strategy = check.opt_str_param(
                deserialization_strategy, "deserialization_strategy"
            )
            self.schema_registry_url = check.opt_str_param(
                schema_registry_url, "schema_registry_url"
            )
            self.schema_registry_username = check.opt_str_param(
                schema_registry_username, "schema_registry_username"
            )
            self.schema_registry_password = check.opt_str_param(
                schema_registry_password, "schema_registry_password"
            )

    class ManuallyAssignAListOfPartitions:
        @public
        def __init__(self, topic_partitions: str):
            self.subscription_type = "assign"
            self.topic_partitions = check.str_param(topic_partitions, "topic_partitions")

    class SubscribeToAllTopicsMatchingSpecifiedPattern:
        @public
        def __init__(self, topic_pattern: str):
            self.subscription_type = "subscribe"
            self.topic_pattern = check.str_param(topic_pattern, "topic_pattern")

    class PLAINTEXT:
        @public
        def __init__(self, security_protocol: str):
            self.security_protocol = check.str_param(security_protocol, "security_protocol")

    class SASLPLAINTEXT:
        @public
        def __init__(self, security_protocol: str, sasl_mechanism: str, sasl_jaas_config: str):
            self.security_protocol = check.str_param(security_protocol, "security_protocol")
            self.sasl_mechanism = check.str_param(sasl_mechanism, "sasl_mechanism")
            self.sasl_jaas_config = check.str_param(sasl_jaas_config, "sasl_jaas_config")

    class SASLSSL:
        @public
        def __init__(self, security_protocol: str, sasl_mechanism: str, sasl_jaas_config: str):
            self.security_protocol = check.str_param(security_protocol, "security_protocol")
            self.sasl_mechanism = check.str_param(sasl_mechanism, "sasl_mechanism")
            self.sasl_jaas_config = check.str_param(sasl_jaas_config, "sasl_jaas_config")

    @public
    def __init__(
        self,
        name: str,
        MessageFormat: Union["KafkaSource.JSON", "KafkaSource.AVRO"],
        bootstrap_servers: str,
        subscription: Union[
            "KafkaSource.ManuallyAssignAListOfPartitions",
            "KafkaSource.SubscribeToAllTopicsMatchingSpecifiedPattern",
        ],
        protocol: Union[
            "KafkaSource.PLAINTEXT", "KafkaSource.SASLPLAINTEXT", "KafkaSource.SASLSSL"
        ],
        test_topic: Optional[str] = None,
        group_id: Optional[str] = None,
        max_poll_records: Optional[int] = None,
        polling_time: Optional[int] = None,
        client_id: Optional[str] = None,
        enable_auto_commit: Optional[bool] = None,
        auto_commit_interval_ms: Optional[int] = None,
        client_dns_lookup: Optional[str] = None,
        retry_backoff_ms: Optional[int] = None,
        request_timeout_ms: Optional[int] = None,
        receive_buffer_bytes: Optional[int] = None,
        auto_offset_reset: Optional[str] = None,
        repeated_calls: Optional[int] = None,
        max_records_process: Optional[int] = None,
    ):
        """Airbyte Source for Kafka.

        Documentation can be found at https://docs.airbyte.com/integrations/sources/kafka

        Args:
            name (str): The name of the destination.
            MessageFormat (Union[KafkaSource.JSON, KafkaSource.AVRO]): The serialization used based on this
            bootstrap_servers (str): A list of host/port pairs to use for establishing the initial connection to the Kafka cluster. The client will make use of all servers irrespective of which servers are specified here for bootstrapping&mdash;this list only impacts the initial hosts used to discover the full set of servers. This list should be in the form host1:port1,host2:port2,.... Since these servers are just used for the initial connection to discover the full cluster membership (which may change dynamically), this list need not contain the full set of servers (you may want more than one, though, in case a server is down).
            subscription (Union[KafkaSource.ManuallyAssignAListOfPartitions, KafkaSource.SubscribeToAllTopicsMatchingSpecifiedPattern]): You can choose to manually assign a list of partitions, or subscribe to all topics matching specified pattern to get dynamically assigned partitions.
            test_topic (Optional[str]): The Topic to test in case the Airbyte can consume messages.
            group_id (Optional[str]): The Group ID is how you distinguish different consumer groups.
            max_poll_records (Optional[int]): The maximum number of records returned in a single call to poll(). Note, that max_poll_records does not impact the underlying fetching behavior. The consumer will cache the records from each fetch request and returns them incrementally from each poll.
            polling_time (Optional[int]): Amount of time Kafka connector should try to poll for messages.
            protocol (Union[KafkaSource.PLAINTEXT, KafkaSource.SASLPLAINTEXT, KafkaSource.SASLSSL]): The Protocol used to communicate with brokers.
            client_id (Optional[str]): An ID string to pass to the server when making requests. The purpose of this is to be able to track the source of requests beyond just ip/port by allowing a logical application name to be included in server-side request logging.
            enable_auto_commit (Optional[bool]): If true, the consumer's offset will be periodically committed in the background.
            auto_commit_interval_ms (Optional[int]): The frequency in milliseconds that the consumer offsets are auto-committed to Kafka if enable.auto.commit is set to true.
            client_dns_lookup (Optional[str]): Controls how the client uses DNS lookups. If set to use_all_dns_ips, connect to each returned IP address in sequence until a successful connection is established. After a disconnection, the next IP is used. Once all IPs have been used once, the client resolves the IP(s) from the hostname again. If set to resolve_canonical_bootstrap_servers_only, resolve each bootstrap address into a list of canonical names. After the bootstrap phase, this behaves the same as use_all_dns_ips. If set to default (deprecated), attempt to connect to the first IP address returned by the lookup, even if the lookup returns multiple IP addresses.
            retry_backoff_ms (Optional[int]): The amount of time to wait before attempting to retry a failed request to a given topic partition. This avoids repeatedly sending requests in a tight loop under some failure scenarios.
            request_timeout_ms (Optional[int]): The configuration controls the maximum amount of time the client will wait for the response of a request. If the response is not received before the timeout elapses the client will resend the request if necessary or fail the request if retries are exhausted.
            receive_buffer_bytes (Optional[int]): The size of the TCP receive buffer (SO_RCVBUF) to use when reading data. If the value is -1, the OS default will be used.
            auto_offset_reset (Optional[str]): What to do when there is no initial offset in Kafka or if the current offset does not exist any more on the server - earliest: automatically reset the offset to the earliest offset, latest: automatically reset the offset to the latest offset, none: throw exception to the consumer if no previous offset is found for the consumer's group, anything else: throw exception to the consumer.
            repeated_calls (Optional[int]): The number of repeated calls to poll() if no messages were received.
            max_records_process (Optional[int]): The Maximum to be processed per execution
        """
        self.MessageFormat = check.inst_param(
            MessageFormat, "MessageFormat", (KafkaSource.JSON, KafkaSource.AVRO)
        )
        self.bootstrap_servers = check.str_param(bootstrap_servers, "bootstrap_servers")
        self.subscription = check.inst_param(
            subscription,
            "subscription",
            (
                KafkaSource.ManuallyAssignAListOfPartitions,
                KafkaSource.SubscribeToAllTopicsMatchingSpecifiedPattern,
            ),
        )
        self.test_topic = check.opt_str_param(test_topic, "test_topic")
        self.group_id = check.opt_str_param(group_id, "group_id")
        self.max_poll_records = check.opt_int_param(max_poll_records, "max_poll_records")
        self.polling_time = check.opt_int_param(polling_time, "polling_time")
        self.protocol = check.inst_param(
            protocol,
            "protocol",
            (KafkaSource.PLAINTEXT, KafkaSource.SASLPLAINTEXT, KafkaSource.SASLSSL),
        )
        self.client_id = check.opt_str_param(client_id, "client_id")
        self.enable_auto_commit = check.opt_bool_param(enable_auto_commit, "enable_auto_commit")
        self.auto_commit_interval_ms = check.opt_int_param(
            auto_commit_interval_ms, "auto_commit_interval_ms"
        )
        self.client_dns_lookup = check.opt_str_param(client_dns_lookup, "client_dns_lookup")
        self.retry_backoff_ms = check.opt_int_param(retry_backoff_ms, "retry_backoff_ms")
        self.request_timeout_ms = check.opt_int_param(request_timeout_ms, "request_timeout_ms")
        self.receive_buffer_bytes = check.opt_int_param(
            receive_buffer_bytes, "receive_buffer_bytes"
        )
        self.auto_offset_reset = check.opt_str_param(auto_offset_reset, "auto_offset_reset")
        self.repeated_calls = check.opt_int_param(repeated_calls, "repeated_calls")
        self.max_records_process = check.opt_int_param(max_records_process, "max_records_process")
        super().__init__("Kafka", name)
