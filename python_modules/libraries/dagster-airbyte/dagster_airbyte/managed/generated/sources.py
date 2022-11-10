# pylint: disable=unused-import,redefined-builtin
from typing import Any, List, Optional, Union

from dagster_airbyte.managed.types import GeneratedAirbyteSource

import dagster._check as check


class StravaSource(GeneratedAirbyteSource):
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
        """
        Airbyte Source for Strava

        Documentation can be found at https://docs.airbyte.com/integrations/sources/strava
        """
        self.auth_type = check.opt_str_param(auth_type, "auth_type")
        self.client_id = check.str_param(client_id, "client_id")
        self.client_secret = check.str_param(client_secret, "client_secret")
        self.refresh_token = check.str_param(refresh_token, "refresh_token")
        self.athlete_id = check.int_param(athlete_id, "athlete_id")
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Strava", name)


class AppsflyerSource(GeneratedAirbyteSource):
    def __init__(
        self,
        name: str,
        app_id: str,
        api_token: str,
        start_date: str,
        timezone: Optional[str] = None,
    ):
        """
        Airbyte Source for Appsflyer

        Documentation can be found at https://docsurl.com
        """
        self.app_id = check.str_param(app_id, "app_id")
        self.api_token = check.str_param(api_token, "api_token")
        self.start_date = check.str_param(start_date, "start_date")
        self.timezone = check.opt_str_param(timezone, "timezone")
        super().__init__("Appsflyer", name)


class GoogleWorkspaceAdminReportsSource(GeneratedAirbyteSource):
    def __init__(
        self, name: str, credentials_json: str, email: str, lookback: Optional[int] = None
    ):
        """
        Airbyte Source for Google Workspace Admin Reports

        Documentation can be found at https://docs.airbyte.com/integrations/sources/google-workspace-admin-reports
        """
        self.credentials_json = check.str_param(credentials_json, "credentials_json")
        self.email = check.str_param(email, "email")
        self.lookback = check.opt_int_param(lookback, "lookback")
        super().__init__("Google Workspace Admin Reports", name)


class CartSource(GeneratedAirbyteSource):
    class CentralAPIRouter:
        def __init__(self, user_name: str, user_secret: str, site_id: str):
            self.auth_type = "CENTRAL_API_ROUTER"
            self.user_name = check.str_param(user_name, "user_name")
            self.user_secret = check.str_param(user_secret, "user_secret")
            self.site_id = check.str_param(site_id, "site_id")

    class SingleStoreAccessToken:
        def __init__(self, access_token: str, store_name: str):
            self.auth_type = "SINGLE_STORE_ACCESS_TOKEN"
            self.access_token = check.str_param(access_token, "access_token")
            self.store_name = check.str_param(store_name, "store_name")

    def __init__(
        self,
        name: str,
        credentials: Union[CentralAPIRouter, SingleStoreAccessToken],
        start_date: str,
    ):
        """
        Airbyte Source for Cart

        Documentation can be found at https://docs.airbyte.com/integrations/sources/cart
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
        def __init__(self, access_token: str, auth_method: Optional[str] = None):
            self.auth_method = check.opt_str_param(auth_method, "auth_method")
            self.access_token = check.str_param(access_token, "access_token")

    def __init__(
        self,
        name: str,
        credentials: Union[OAuth20, AccessToken],
        start_date: str,
        account_ids: Optional[List[int]] = None,
    ):
        """
        Airbyte Source for Linkedin Ads

        Documentation can be found at https://docs.airbyte.com/integrations/sources/linkedin-ads
        """
        self.credentials = check.inst_param(
            credentials, "credentials", (LinkedinAdsSource.OAuth20, LinkedinAdsSource.AccessToken)
        )
        self.start_date = check.str_param(start_date, "start_date")
        self.account_ids = check.opt_nullable_list_param(account_ids, "account_ids", int)
        super().__init__("Linkedin Ads", name)


class MongodbSource(GeneratedAirbyteSource):
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
        """
        Airbyte Source for Mongodb

        Documentation can be found at https://docs.airbyte.com/integrations/sources/mongodb
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
    def __init__(self, name: str, account_id: str, start_date: str, bearer_token: str):
        """
        Airbyte Source for Timely

        Documentation can be found at https://docsurl.com
        """
        self.account_id = check.str_param(account_id, "account_id")
        self.start_date = check.str_param(start_date, "start_date")
        self.bearer_token = check.str_param(bearer_token, "bearer_token")
        super().__init__("Timely", name)


class StockTickerApiTutorialSource(GeneratedAirbyteSource):
    def __init__(self, name: str, stock_ticker: str, api_key: str):
        """
        Airbyte Source for Stock Ticker Api Tutorial

        Documentation can be found at https://polygon.io/docs/stocks/get_v2_aggs_grouped_locale_us_market_stocks__date
        """
        self.stock_ticker = check.str_param(stock_ticker, "stock_ticker")
        self.api_key = check.str_param(api_key, "api_key")
        super().__init__("Stock Ticker Api Tutorial", name)


class WrikeSource(GeneratedAirbyteSource):
    def __init__(
        self, name: str, access_token: str, wrike_instance: str, start_date: Optional[str] = None
    ):
        """
        Airbyte Source for Wrike

        Documentation can be found at https://docsurl.com
        """
        self.access_token = check.str_param(access_token, "access_token")
        self.wrike_instance = check.str_param(wrike_instance, "wrike_instance")
        self.start_date = check.opt_str_param(start_date, "start_date")
        super().__init__("Wrike", name)


class CommercetoolsSource(GeneratedAirbyteSource):
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
        """
        Airbyte Source for Commercetools

        Documentation can be found at https://docs.airbyte.com/integrations/sources/commercetools
        """
        self.region = check.str_param(region, "region")
        self.host = check.str_param(host, "host")
        self.start_date = check.str_param(start_date, "start_date")
        self.project_key = check.str_param(project_key, "project_key")
        self.client_id = check.str_param(client_id, "client_id")
        self.client_secret = check.str_param(client_secret, "client_secret")
        super().__init__("Commercetools", name)


class GutendexSource(GeneratedAirbyteSource):
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
        """
        Airbyte Source for Gutendex

        Documentation can be found at https://docs.airbyte.com/integrations/sources/gutendex
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
    def __init__(self, name: str, api_key: str, start_date: str):
        """
        Airbyte Source for Iterable

        Documentation can be found at https://docs.airbyte.com/integrations/sources/iterable
        """
        self.api_key = check.str_param(api_key, "api_key")
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Iterable", name)


class QuickbooksSingerSource(GeneratedAirbyteSource):
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
        """
        Airbyte Source for Quickbooks Singer

        Documentation can be found at https://docs.airbyte.com/integrations/sources/quickbooks
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
    def __init__(self, name: str, start_date: str, store_hash: str, access_token: str):
        """
        Airbyte Source for Bigcommerce

        Documentation can be found at https://docs.airbyte.com/integrations/sources/bigcommerce
        """
        self.start_date = check.str_param(start_date, "start_date")
        self.store_hash = check.str_param(store_hash, "store_hash")
        self.access_token = check.str_param(access_token, "access_token")
        super().__init__("Bigcommerce", name)


class ShopifySource(GeneratedAirbyteSource):
    class APIPassword:
        def __init__(self, api_password: str):
            self.auth_method = "api_password"
            self.api_password = check.str_param(api_password, "api_password")

    class OAuth20:
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

    def __init__(
        self, name: str, shop: str, credentials: Union[APIPassword, OAuth20], start_date: str
    ):
        """
        Airbyte Source for Shopify

        Documentation can be found at https://docs.airbyte.com/integrations/sources/shopify
        """
        self.shop = check.str_param(shop, "shop")
        self.credentials = check.inst_param(
            credentials, "credentials", (ShopifySource.APIPassword, ShopifySource.OAuth20)
        )
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Shopify", name)


class AppstoreSingerSource(GeneratedAirbyteSource):
    def __init__(
        self, name: str, key_id: str, private_key: str, issuer_id: str, vendor: str, start_date: str
    ):
        """
        Airbyte Source for Appstore Singer

        Documentation can be found at https://docs.airbyte.com/integrations/sources/appstore
        """
        self.key_id = check.str_param(key_id, "key_id")
        self.private_key = check.str_param(private_key, "private_key")
        self.issuer_id = check.str_param(issuer_id, "issuer_id")
        self.vendor = check.str_param(vendor, "vendor")
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Appstore Singer", name)


class GreenhouseSource(GeneratedAirbyteSource):
    def __init__(self, name: str, api_key: str):
        """
        Airbyte Source for Greenhouse

        Documentation can be found at https://docs.airbyte.com/integrations/sources/greenhouse
        """
        self.api_key = check.str_param(api_key, "api_key")
        super().__init__("Greenhouse", name)


class ZoomSingerSource(GeneratedAirbyteSource):
    def __init__(self, name: str, jwt: str):
        """
        Airbyte Source for Zoom Singer

        Documentation can be found at https://docs.airbyte.com/integrations/sources/zoom
        """
        self.jwt = check.str_param(jwt, "jwt")
        super().__init__("Zoom Singer", name)


class TiktokMarketingSource(GeneratedAirbyteSource):
    class OAuth20:
        def __init__(
            self, app_id: str, secret: str, access_token: str, auth_type: Optional[str] = None
        ):
            self.auth_type = check.opt_str_param(auth_type, "auth_type")
            self.app_id = check.str_param(app_id, "app_id")
            self.secret = check.str_param(secret, "secret")
            self.access_token = check.str_param(access_token, "access_token")

    class SandboxAccessToken:
        def __init__(self, advertiser_id: str, access_token: str, auth_type: Optional[str] = None):
            self.auth_type = check.opt_str_param(auth_type, "auth_type")
            self.advertiser_id = check.str_param(advertiser_id, "advertiser_id")
            self.access_token = check.str_param(access_token, "access_token")

    def __init__(
        self,
        name: str,
        credentials: Union[OAuth20, SandboxAccessToken],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        report_granularity: Optional[str] = None,
    ):
        """
        Airbyte Source for Tiktok Marketing

        Documentation can be found at https://docs.airbyte.com/integrations/sources/tiktok-marketing
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
        def __init__(self, access_token: str):
            self.credentials = "access_token"
            self.access_token = check.str_param(access_token, "access_token")

    def __init__(
        self,
        name: str,
        start_date: str,
        credentials: Union[OAuth20, AccessToken],
        subdomain: Optional[str] = None,
    ):
        """
        Airbyte Source for Zendesk Chat

        Documentation can be found at https://docs.airbyte.com/integrations/sources/zendesk-chat
        """
        self.start_date = check.str_param(start_date, "start_date")
        self.subdomain = check.opt_str_param(subdomain, "subdomain")
        self.credentials = check.inst_param(
            credentials, "credentials", (ZendeskChatSource.OAuth20, ZendeskChatSource.AccessToken)
        )
        super().__init__("Zendesk Chat", name)


class AwsCloudtrailSource(GeneratedAirbyteSource):
    def __init__(
        self, name: str, aws_key_id: str, aws_secret_key: str, aws_region_name: str, start_date: str
    ):
        """
        Airbyte Source for Aws Cloudtrail

        Documentation can be found at https://docs.airbyte.com/integrations/sources/aws-cloudtrail
        """
        self.aws_key_id = check.str_param(aws_key_id, "aws_key_id")
        self.aws_secret_key = check.str_param(aws_secret_key, "aws_secret_key")
        self.aws_region_name = check.str_param(aws_region_name, "aws_region_name")
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Aws Cloudtrail", name)


class OktaSource(GeneratedAirbyteSource):
    class OAuth20:
        def __init__(self, client_id: str, client_secret: str, refresh_token: str):
            self.auth_type = "oauth2.0"
            self.client_id = check.str_param(client_id, "client_id")
            self.client_secret = check.str_param(client_secret, "client_secret")
            self.refresh_token = check.str_param(refresh_token, "refresh_token")

    class APIToken:
        def __init__(self, api_token: str):
            self.auth_type = "api_token"
            self.api_token = check.str_param(api_token, "api_token")

    def __init__(
        self,
        name: str,
        credentials: Union[OAuth20, APIToken],
        domain: Optional[str] = None,
        start_date: Optional[str] = None,
    ):
        """
        Airbyte Source for Okta

        Documentation can be found at https://docs.airbyte.com/integrations/sources/okta
        """
        self.domain = check.opt_str_param(domain, "domain")
        self.start_date = check.opt_str_param(start_date, "start_date")
        self.credentials = check.inst_param(
            credentials, "credentials", (OktaSource.OAuth20, OktaSource.APIToken)
        )
        super().__init__("Okta", name)


class InsightlySource(GeneratedAirbyteSource):
    def __init__(self, name: str, token: Optional[str] = None, start_date: Optional[str] = None):
        """
        Airbyte Source for Insightly

        Documentation can be found at https://docs.airbyte.com/integrations/sources/insightly
        """
        self.token = check.opt_str_param(token, "token")
        self.start_date = check.opt_str_param(start_date, "start_date")
        super().__init__("Insightly", name)


class LinkedinPagesSource(GeneratedAirbyteSource):
    class OAuth20:
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
        def __init__(self, access_token: str, auth_method: Optional[str] = None):
            self.auth_method = check.opt_str_param(auth_method, "auth_method")
            self.access_token = check.str_param(access_token, "access_token")

    def __init__(self, name: str, org_id: int, credentials: Union[OAuth20, AccessToken]):
        """
        Airbyte Source for Linkedin Pages

        Documentation can be found at https://docs.airbyte.com/integrations/sources/linkedin-pages/
        """
        self.org_id = check.int_param(org_id, "org_id")
        self.credentials = check.inst_param(
            credentials,
            "credentials",
            (LinkedinPagesSource.OAuth20, LinkedinPagesSource.AccessToken),
        )
        super().__init__("Linkedin Pages", name)


class PersistiqSource(GeneratedAirbyteSource):
    def __init__(self, name: str, api_key: str):
        """
        Airbyte Source for Persistiq

        Documentation can be found at https://docs.airbyte.com/integrations/sources/persistiq
        """
        self.api_key = check.str_param(api_key, "api_key")
        super().__init__("Persistiq", name)


class FreshcallerSource(GeneratedAirbyteSource):
    def __init__(
        self,
        name: str,
        domain: str,
        api_key: str,
        start_date: str,
        requests_per_minute: Optional[int] = None,
        sync_lag_minutes: Optional[int] = None,
    ):
        """
        Airbyte Source for Freshcaller

        Documentation can be found at https://docs.airbyte.com/integrations/sources/freshcaller
        """
        self.domain = check.str_param(domain, "domain")
        self.api_key = check.str_param(api_key, "api_key")
        self.requests_per_minute = check.opt_int_param(requests_per_minute, "requests_per_minute")
        self.start_date = check.str_param(start_date, "start_date")
        self.sync_lag_minutes = check.opt_int_param(sync_lag_minutes, "sync_lag_minutes")
        super().__init__("Freshcaller", name)


class AppfollowSource(GeneratedAirbyteSource):
    def __init__(self, name: str, ext_id: str, cid: str, api_secret: str, country: str):
        """
        Airbyte Source for Appfollow

        Documentation can be found at https://docs.airbyte.com/integrations/sources/appfollow
        """
        self.ext_id = check.str_param(ext_id, "ext_id")
        self.cid = check.str_param(cid, "cid")
        self.api_secret = check.str_param(api_secret, "api_secret")
        self.country = check.str_param(country, "country")
        super().__init__("Appfollow", name)


class FacebookPagesSource(GeneratedAirbyteSource):
    def __init__(self, name: str, access_token: str, page_id: str):
        """
        Airbyte Source for Facebook Pages

        Documentation can be found at https://docs.airbyte.com/integrations/sources/facebook-pages
        """
        self.access_token = check.str_param(access_token, "access_token")
        self.page_id = check.str_param(page_id, "page_id")
        super().__init__("Facebook Pages", name)


class JiraSource(GeneratedAirbyteSource):
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
        """
        Airbyte Source for Jira

        Documentation can be found at https://docs.airbyte.com/integrations/sources/jira
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
        def __init__(self, client_id: str, client_secret: str, refresh_token: str):
            self.auth_type = "Client"
            self.client_id = check.str_param(client_id, "client_id")
            self.client_secret = check.str_param(client_secret, "client_secret")
            self.refresh_token = check.str_param(refresh_token, "refresh_token")

    class ServiceAccountKeyAuthentication:
        def __init__(self, service_account_info: str):
            self.auth_type = "Service"
            self.service_account_info = check.str_param(
                service_account_info, "service_account_info"
            )

    def __init__(
        self,
        name: str,
        spreadsheet_id: str,
        credentials: Union[AuthenticateViaGoogleOAuth, ServiceAccountKeyAuthentication],
        row_batch_size: Optional[int] = None,
    ):
        """
        Airbyte Source for Google Sheets

        Documentation can be found at https://docs.airbyte.com/integrations/sources/google-sheets
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
    def __init__(self, name: str, docker_username: str):
        """
        Airbyte Source for Dockerhub

        Documentation can be found at https://docs.airbyte.com/integrations/sources/dockerhub
        """
        self.docker_username = check.str_param(docker_username, "docker_username")
        super().__init__("Dockerhub", name)


class UsCensusSource(GeneratedAirbyteSource):
    def __init__(
        self, name: str, query_path: str, api_key: str, query_params: Optional[str] = None
    ):
        """
        Airbyte Source for Us Census

        Documentation can be found at https://docs.airbyte.com/integrations/sources/us-census
        """
        self.query_params = check.opt_str_param(query_params, "query_params")
        self.query_path = check.str_param(query_path, "query_path")
        self.api_key = check.str_param(api_key, "api_key")
        super().__init__("Us Census", name)


class KustomerSingerSource(GeneratedAirbyteSource):
    def __init__(self, name: str, api_token: str, start_date: str):
        """
        Airbyte Source for Kustomer Singer

        Documentation can be found at https://docs.airbyte.com/integrations/sources/kustomer
        """
        self.api_token = check.str_param(api_token, "api_token")
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Kustomer Singer", name)


class AzureTableSource(GeneratedAirbyteSource):
    def __init__(
        self,
        name: str,
        storage_account_name: str,
        storage_access_key: str,
        storage_endpoint_suffix: Optional[str] = None,
    ):
        """
        Airbyte Source for Azure Table

        Documentation can be found at https://docsurl.com
        """
        self.storage_account_name = check.str_param(storage_account_name, "storage_account_name")
        self.storage_access_key = check.str_param(storage_access_key, "storage_access_key")
        self.storage_endpoint_suffix = check.opt_str_param(
            storage_endpoint_suffix, "storage_endpoint_suffix"
        )
        super().__init__("Azure Table", name)


class ScaffoldJavaJdbcSource(GeneratedAirbyteSource):
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
        """
        Airbyte Source for Scaffold Java Jdbc

        Documentation can be found at https://docs.airbyte.com/integrations/sources/scaffold_java_jdbc
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
        """
        Airbyte Source for Tidb

        Documentation can be found at https://docs.airbyte.com/integrations/sources/tidb
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
    def __init__(
        self,
        name: str,
        token: str,
        key: str,
        start_date: str,
        survey_ids: Optional[List[str]] = None,
    ):
        """
        Airbyte Source for Qualaroo

        Documentation can be found at https://docs.airbyte.com/integrations/sources/qualaroo
        """
        self.token = check.str_param(token, "token")
        self.key = check.str_param(key, "key")
        self.start_date = check.str_param(start_date, "start_date")
        self.survey_ids = check.opt_nullable_list_param(survey_ids, "survey_ids", str)
        super().__init__("Qualaroo", name)


class YahooFinancePriceSource(GeneratedAirbyteSource):
    def __init__(
        self, name: str, tickers: str, interval: Optional[str] = None, range: Optional[str] = None
    ):
        """
        Airbyte Source for Yahoo Finance Price

        Documentation can be found at https://docsurl.com
        """
        self.tickers = check.str_param(tickers, "tickers")
        self.interval = check.opt_str_param(interval, "interval")
        self.range = check.opt_str_param(range, "range")
        super().__init__("Yahoo Finance Price", name)


class GoogleAnalyticsV4Source(GeneratedAirbyteSource):
    class AuthenticateViaGoogleOauth:
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
        def __init__(self, credentials_json: str, auth_type: Optional[str] = None):
            self.auth_type = check.opt_str_param(auth_type, "auth_type")
            self.credentials_json = check.str_param(credentials_json, "credentials_json")

    def __init__(
        self,
        name: str,
        credentials: Union[AuthenticateViaGoogleOauth, ServiceAccountKeyAuthentication],
        start_date: str,
        view_id: str,
        custom_reports: Optional[str] = None,
        window_in_days: Optional[int] = None,
    ):
        """
        Airbyte Source for Google Analytics V4

        Documentation can be found at https://docs.airbyte.com/integrations/sources/google-analytics-universal-analytics
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
    def __init__(
        self,
        name: str,
        username: str,
        jdbc_url: str,
        password: Optional[str] = None,
        jdbc_url_params: Optional[str] = None,
    ):
        """
        Airbyte Source for Jdbc

        Documentation can be found at https://docs.airbyte.com/integrations/sources/postgres
        """
        self.username = check.str_param(username, "username")
        self.password = check.opt_str_param(password, "password")
        self.jdbc_url = check.str_param(jdbc_url, "jdbc_url")
        self.jdbc_url_params = check.opt_str_param(jdbc_url_params, "jdbc_url_params")
        super().__init__("Jdbc", name)


class FakerSource(GeneratedAirbyteSource):
    def __init__(
        self,
        name: str,
        count: int,
        seed: Optional[int] = None,
        records_per_sync: Optional[int] = None,
        records_per_slice: Optional[int] = None,
    ):
        """
        Airbyte Source for Faker

        Documentation can be found at https://docs.airbyte.com/integrations/sources/faker
        """
        self.count = check.int_param(count, "count")
        self.seed = check.opt_int_param(seed, "seed")
        self.records_per_sync = check.opt_int_param(records_per_sync, "records_per_sync")
        self.records_per_slice = check.opt_int_param(records_per_slice, "records_per_slice")
        super().__init__("Faker", name)


class TplcentralSource(GeneratedAirbyteSource):
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
        """
        Airbyte Source for Tplcentral

        Documentation can be found at https://docs.airbyte.com/integrations/sources/tplcentral
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
        """
        Airbyte Source for Clickhouse

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/clickhouse
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
    def __init__(self, name: str, domain_name: str, api_key: str, start_date: str):
        """
        Airbyte Source for Freshservice

        Documentation can be found at https://docs.airbyte.com/integrations/sources/freshservice
        """
        self.domain_name = check.str_param(domain_name, "domain_name")
        self.api_key = check.str_param(api_key, "api_key")
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Freshservice", name)


class ZenloopSource(GeneratedAirbyteSource):
    def __init__(
        self,
        name: str,
        api_token: str,
        date_from: Optional[str] = None,
        survey_id: Optional[str] = None,
        survey_group_id: Optional[str] = None,
    ):
        """
        Airbyte Source for Zenloop

        Documentation can be found at https://docs.airbyte.com/integrations/sources/zenloop
        """
        self.api_token = check.str_param(api_token, "api_token")
        self.date_from = check.opt_str_param(date_from, "date_from")
        self.survey_id = check.opt_str_param(survey_id, "survey_id")
        self.survey_group_id = check.opt_str_param(survey_group_id, "survey_group_id")
        super().__init__("Zenloop", name)


class OracleSource(GeneratedAirbyteSource):
    class ServiceName:
        def __init__(self, service_name: str, connection_type: Optional[str] = None):
            self.connection_type = check.opt_str_param(connection_type, "connection_type")
            self.service_name = check.str_param(service_name, "service_name")

    class SystemIDSID:
        def __init__(self, sid: str, connection_type: Optional[str] = None):
            self.connection_type = check.opt_str_param(connection_type, "connection_type")
            self.sid = check.str_param(sid, "sid")

    class Unencrypted:
        def __init__(
            self,
        ):
            self.encryption_method = "unencrypted"

    class NativeNetworkEncryptionNNE:
        def __init__(self, encryption_algorithm: Optional[str] = None):
            self.encryption_method = "client_nne"
            self.encryption_algorithm = check.opt_str_param(
                encryption_algorithm, "encryption_algorithm"
            )

    class TLSEncryptedVerifyCertificate:
        def __init__(self, ssl_certificate: str):
            self.encryption_method = "encrypted_verify_certificate"
            self.ssl_certificate = check.str_param(ssl_certificate, "ssl_certificate")

    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        connection_data: Union[ServiceName, SystemIDSID],
        username: str,
        encryption: Union[Unencrypted, NativeNetworkEncryptionNNE, TLSEncryptedVerifyCertificate],
        password: Optional[str] = None,
        schemas: Optional[List[str]] = None,
        jdbc_url_params: Optional[str] = None,
    ):
        """
        Airbyte Source for Oracle

        Documentation can be found at https://docs.airbyte.com/integrations/sources/oracle
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
    def __init__(self, name: str, api_key: str, start_date: str):
        """
        Airbyte Source for Klaviyo

        Documentation can be found at https://docs.airbyte.com/integrations/sources/klaviyo
        """
        self.api_key = check.str_param(api_key, "api_key")
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Klaviyo", name)


class GoogleDirectorySource(GeneratedAirbyteSource):
    class SignInViaGoogleOAuth:
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
        def __init__(
            self, credentials_json: str, email: str, credentials_title: Optional[str] = None
        ):
            self.credentials_title = check.opt_str_param(credentials_title, "credentials_title")
            self.credentials_json = check.str_param(credentials_json, "credentials_json")
            self.email = check.str_param(email, "email")

    def __init__(self, name: str, credentials: Union[SignInViaGoogleOAuth, ServiceAccountKey]):
        """
        Airbyte Source for Google Directory

        Documentation can be found at https://docs.airbyte.com/integrations/sources/google-directory
        """
        self.credentials = check.inst_param(
            credentials,
            "credentials",
            (GoogleDirectorySource.SignInViaGoogleOAuth, GoogleDirectorySource.ServiceAccountKey),
        )
        super().__init__("Google Directory", name)


class InstagramSource(GeneratedAirbyteSource):
    def __init__(self, name: str, start_date: str, access_token: str):
        """
        Airbyte Source for Instagram

        Documentation can be found at https://docs.airbyte.com/integrations/sources/instagram
        """
        self.start_date = check.str_param(start_date, "start_date")
        self.access_token = check.str_param(access_token, "access_token")
        super().__init__("Instagram", name)


class ShortioSource(GeneratedAirbyteSource):
    def __init__(self, name: str, domain_id: str, secret_key: str, start_date: str):
        """
        Airbyte Source for Shortio

        Documentation can be found at https://developers.short.io/reference
        """
        self.domain_id = check.str_param(domain_id, "domain_id")
        self.secret_key = check.str_param(secret_key, "secret_key")
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Shortio", name)


class SquareSource(GeneratedAirbyteSource):
    class OauthAuthentication:
        def __init__(self, client_id: str, client_secret: str, refresh_token: str):
            self.auth_type = "Oauth"
            self.client_id = check.str_param(client_id, "client_id")
            self.client_secret = check.str_param(client_secret, "client_secret")
            self.refresh_token = check.str_param(refresh_token, "refresh_token")

    class APIKey:
        def __init__(self, api_key: str):
            self.auth_type = "Apikey"
            self.api_key = check.str_param(api_key, "api_key")

    def __init__(
        self,
        name: str,
        is_sandbox: bool,
        credentials: Union[OauthAuthentication, APIKey],
        start_date: Optional[str] = None,
        include_deleted_objects: Optional[bool] = None,
    ):
        """
        Airbyte Source for Square

        Documentation can be found at https://docs.airbyte.com/integrations/sources/square
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
    def __init__(self, name: str, since: str, api_key: str):
        """
        Airbyte Source for Delighted

        Documentation can be found at https://docsurl.com
        """
        self.since = check.str_param(since, "since")
        self.api_key = check.str_param(api_key, "api_key")
        super().__init__("Delighted", name)


class AmazonSqsSource(GeneratedAirbyteSource):
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
        """
        Airbyte Source for Amazon Sqs

        Documentation can be found at https://docs.airbyte.com/integrations/sources/amazon-sqs
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
        def __init__(self, client_id: str, client_secret: str, refresh_token: str):
            self.client_id = check.str_param(client_id, "client_id")
            self.client_secret = check.str_param(client_secret, "client_secret")
            self.refresh_token = check.str_param(refresh_token, "refresh_token")

    def __init__(self, name: str, credentials: AuthenticateViaOAuth20):
        """
        Airbyte Source for Youtube Analytics

        Documentation can be found at https://docs.airbyte.com/integrations/sources/youtube-analytics
        """
        self.credentials = check.inst_param(
            credentials, "credentials", YoutubeAnalyticsSource.AuthenticateViaOAuth20
        )
        super().__init__("Youtube Analytics", name)


class ScaffoldSourcePythonSource(GeneratedAirbyteSource):
    def __init__(self, name: str, fix_me: Optional[str] = None):
        """
        Airbyte Source for Scaffold Source Python

        Documentation can be found at https://docsurl.com
        """
        self.fix_me = check.opt_str_param(fix_me, "fix_me")
        super().__init__("Scaffold Source Python", name)


class LookerSource(GeneratedAirbyteSource):
    def __init__(
        self,
        name: str,
        domain: str,
        client_id: str,
        client_secret: str,
        run_look_ids: Optional[List[str]] = None,
    ):
        """
        Airbyte Source for Looker

        Documentation can be found at https://docs.airbyte.com/integrations/sources/looker
        """
        self.domain = check.str_param(domain, "domain")
        self.client_id = check.str_param(client_id, "client_id")
        self.client_secret = check.str_param(client_secret, "client_secret")
        self.run_look_ids = check.opt_nullable_list_param(run_look_ids, "run_look_ids", str)
        super().__init__("Looker", name)


class GitlabSource(GeneratedAirbyteSource):
    def __init__(
        self,
        name: str,
        api_url: str,
        private_token: str,
        start_date: str,
        groups: Optional[str] = None,
        projects: Optional[str] = None,
    ):
        """
        Airbyte Source for Gitlab

        Documentation can be found at https://docs.airbyte.com/integrations/sources/gitlab
        """
        self.api_url = check.str_param(api_url, "api_url")
        self.private_token = check.str_param(private_token, "private_token")
        self.groups = check.opt_str_param(groups, "groups")
        self.projects = check.opt_str_param(projects, "projects")
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Gitlab", name)


class ExchangeRatesSource(GeneratedAirbyteSource):
    def __init__(
        self,
        name: str,
        start_date: str,
        access_key: str,
        base: Optional[str] = None,
        ignore_weekends: Optional[bool] = None,
    ):
        """
        Airbyte Source for Exchange Rates

        Documentation can be found at https://docs.airbyte.com/integrations/sources/exchangeratesapi
        """
        self.start_date = check.str_param(start_date, "start_date")
        self.access_key = check.str_param(access_key, "access_key")
        self.base = check.opt_str_param(base, "base")
        self.ignore_weekends = check.opt_bool_param(ignore_weekends, "ignore_weekends")
        super().__init__("Exchange Rates", name)


class AmazonAdsSource(GeneratedAirbyteSource):
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
        """
        Airbyte Source for Amazon Ads

        Documentation can be found at https://docs.airbyte.com/integrations/sources/amazon-ads
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
        def __init__(self, username: str, secret: str):
            self.username = check.str_param(username, "username")
            self.secret = check.str_param(secret, "secret")

    class ProjectSecret:
        def __init__(self, api_secret: str):
            self.api_secret = check.str_param(api_secret, "api_secret")

    def __init__(
        self,
        name: str,
        credentials: Union[ServiceAccount, ProjectSecret],
        project_id: Optional[int] = None,
        attribution_window: Optional[int] = None,
        project_timezone: Optional[str] = None,
        select_properties_by_default: Optional[bool] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        region: Optional[str] = None,
        date_window_size: Optional[int] = None,
    ):
        """
        Airbyte Source for Mixpanel

        Documentation can be found at https://docs.airbyte.com/integrations/sources/mixpanel
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
    def __init__(self, name: str, api_token: str, workspace: str, start_date: Optional[str] = None):
        """
        Airbyte Source for Orbit

        Documentation can be found at https://docs.airbyte.com/integrations/sources/orbit
        """
        self.api_token = check.str_param(api_token, "api_token")
        self.workspace = check.str_param(workspace, "workspace")
        self.start_date = check.opt_str_param(start_date, "start_date")
        super().__init__("Orbit", name)


class AmazonSellerPartnerSource(GeneratedAirbyteSource):
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
        """
        Airbyte Source for Amazon Seller Partner

        Documentation can be found at https://docs.airbyte.com/integrations/sources/amazon-seller-partner
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
    def __init__(self, name: str, api_key: str):
        """
        Airbyte Source for Courier

        Documentation can be found at https://docs.airbyte.io/integrations/sources/courier
        """
        self.api_key = check.str_param(api_key, "api_key")
        super().__init__("Courier", name)


class CloseComSource(GeneratedAirbyteSource):
    def __init__(self, name: str, api_key: str, start_date: Optional[str] = None):
        """
        Airbyte Source for Close Com

        Documentation can be found at https://docs.airbyte.com/integrations/sources/close-com
        """
        self.api_key = check.str_param(api_key, "api_key")
        self.start_date = check.opt_str_param(start_date, "start_date")
        super().__init__("Close Com", name)


class BingAdsSource(GeneratedAirbyteSource):
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
        """
        Airbyte Source for Bing Ads

        Documentation can be found at https://docs.airbyte.com/integrations/sources/bing-ads
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
    def __init__(self, name: str, client_id: str, client_secret: str):
        """
        Airbyte Source for Primetric

        Documentation can be found at https://docsurl.com
        """
        self.client_id = check.str_param(client_id, "client_id")
        self.client_secret = check.str_param(client_secret, "client_secret")
        super().__init__("Primetric", name)


class PivotalTrackerSource(GeneratedAirbyteSource):
    def __init__(self, name: str, api_token: str):
        """
        Airbyte Source for Pivotal Tracker

        Documentation can be found at https://docsurl.com
        """
        self.api_token = check.str_param(api_token, "api_token")
        super().__init__("Pivotal Tracker", name)


class ElasticsearchSource(GeneratedAirbyteSource):
    class None_:
        def __init__(
            self,
        ):
            self.method = "none"

    class ApiKeySecret:
        def __init__(self, apiKeyId: str, apiKeySecret: str):
            self.method = "secret"
            self.apiKeyId = check.str_param(apiKeyId, "apiKeyId")
            self.apiKeySecret = check.str_param(apiKeySecret, "apiKeySecret")

    class UsernamePassword:
        def __init__(self, username: str, password: str):
            self.method = "basic"
            self.username = check.str_param(username, "username")
            self.password = check.str_param(password, "password")

    def __init__(
        self,
        name: str,
        endpoint: str,
        authenticationMethod: Union[None_, ApiKeySecret, UsernamePassword],
    ):
        """
        Airbyte Source for Elasticsearch

        Documentation can be found at https://docs.airbyte.com/integrations/source/elasticsearch
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
    def __init__(
        self, name: str, project_id: str, credentials_json: str, dataset_id: Optional[str] = None
    ):
        """
        Airbyte Source for Bigquery

        Documentation can be found at https://docs.airbyte.com/integrations/sources/bigquery
        """
        self.project_id = check.str_param(project_id, "project_id")
        self.dataset_id = check.opt_str_param(dataset_id, "dataset_id")
        self.credentials_json = check.str_param(credentials_json, "credentials_json")
        super().__init__("Bigquery", name)


class WoocommerceSource(GeneratedAirbyteSource):
    def __init__(
        self,
        name: str,
        shop: str,
        start_date: str,
        api_key: str,
        api_secret: str,
        conversion_window_days: Optional[int] = None,
    ):
        """
        Airbyte Source for Woocommerce

        Documentation can be found at https://docs.airbyte.com/integrations/sources/woocommerce
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
    def __init__(
        self, name: str, api_key: str, client_secret: str, country_code: str, start_date: str
    ):
        """
        Airbyte Source for Search Metrics

        Documentation can be found at https://docs.airbyte.com/integrations/sources/seacrh-metrics
        """
        self.api_key = check.str_param(api_key, "api_key")
        self.client_secret = check.str_param(client_secret, "client_secret")
        self.country_code = check.str_param(country_code, "country_code")
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Search Metrics", name)


class TypeformSource(GeneratedAirbyteSource):
    def __init__(
        self, name: str, start_date: str, token: str, form_ids: Optional[List[str]] = None
    ):
        """
        Airbyte Source for Typeform

        Documentation can be found at https://docs.airbyte.com/integrations/sources/typeform
        """
        self.start_date = check.str_param(start_date, "start_date")
        self.token = check.str_param(token, "token")
        self.form_ids = check.opt_nullable_list_param(form_ids, "form_ids", str)
        super().__init__("Typeform", name)


class WebflowSource(GeneratedAirbyteSource):
    def __init__(self, name: str, site_id: str, api_key: str):
        """
        Airbyte Source for Webflow

        Documentation can be found at https://docs.airbyte.com/integrations/sources/webflow
        """
        self.site_id = check.str_param(site_id, "site_id")
        self.api_key = check.str_param(api_key, "api_key")
        super().__init__("Webflow", name)


class FireboltSource(GeneratedAirbyteSource):
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
        """
        Airbyte Source for Firebolt

        Documentation can be found at https://docs.airbyte.com/integrations/sources/firebolt
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
        def __init__(
            self,
        ):
            self.deletion_mode = "ignore"

    class Enabled:
        def __init__(self, column: str):
            self.deletion_mode = "deleted_field"
            self.column = check.str_param(column, "column")

    class Collection:
        def __init__(
            self, page_size: int, deletions: Union["FaunaSource.Disabled", "FaunaSource.Enabled"]
        ):
            self.page_size = check.int_param(page_size, "page_size")
            self.deletions = check.inst_param(
                deletions, "deletions", (FaunaSource.Disabled, FaunaSource.Enabled)
            )

    def __init__(
        self, name: str, domain: str, port: int, scheme: str, secret: str, collection: Collection
    ):
        """
        Airbyte Source for Fauna

        Documentation can be found at https://github.com/fauna/airbyte/blob/source-fauna/docs/integrations/sources/fauna.md
        """
        self.domain = check.str_param(domain, "domain")
        self.port = check.int_param(port, "port")
        self.scheme = check.str_param(scheme, "scheme")
        self.secret = check.str_param(secret, "secret")
        self.collection = check.inst_param(collection, "collection", FaunaSource.Collection)
        super().__init__("Fauna", name)


class IntercomSource(GeneratedAirbyteSource):
    def __init__(self, name: str, start_date: str, access_token: str):
        """
        Airbyte Source for Intercom

        Documentation can be found at https://docs.airbyte.com/integrations/sources/intercom
        """
        self.start_date = check.str_param(start_date, "start_date")
        self.access_token = check.str_param(access_token, "access_token")
        super().__init__("Intercom", name)


class FreshsalesSource(GeneratedAirbyteSource):
    def __init__(self, name: str, domain_name: str, api_key: str):
        """
        Airbyte Source for Freshsales

        Documentation can be found at https://docs.airbyte.com/integrations/sources/freshsales
        """
        self.domain_name = check.str_param(domain_name, "domain_name")
        self.api_key = check.str_param(api_key, "api_key")
        super().__init__("Freshsales", name)


class AdjustSource(GeneratedAirbyteSource):
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
        """
        Airbyte Source for Adjust

        Documentation can be found at https://docs.airbyte.com/integrations/sources/adjust
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
    def __init__(
        self,
        name: str,
        subdomain: str,
        api_key: str,
        custom_reports_fields: Optional[str] = None,
        custom_reports_include_default_fields: Optional[bool] = None,
    ):
        """
        Airbyte Source for Bamboo Hr

        Documentation can be found at https://docs.airbyte.com/integrations/sources/bamboo-hr
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
        def __init__(self, query: str, table_name: str):
            self.query = check.str_param(query, "query")
            self.table_name = check.str_param(table_name, "table_name")

    def __init__(
        self,
        name: str,
        credentials: GoogleCredentials,
        customer_id: str,
        start_date: str,
        end_date: Optional[str] = None,
        custom_queries: Optional[List[CustomGAQLQueriesEntry]] = None,
        login_customer_id: Optional[str] = None,
        conversion_window_days: Optional[int] = None,
    ):
        """
        Airbyte Source for Google Ads

        Documentation can be found at https://docs.airbyte.com/integrations/sources/google-ads
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
    def __init__(self, name: str, api_key: str, company: str):
        """
        Airbyte Source for Hellobaton

        Documentation can be found at https://docsurl.com
        """
        self.api_key = check.str_param(api_key, "api_key")
        self.company = check.str_param(company, "company")
        super().__init__("Hellobaton", name)


class SendgridSource(GeneratedAirbyteSource):
    def __init__(self, name: str, apikey: str, start_time: Union[int, str]):
        """
        Airbyte Source for Sendgrid

        Documentation can be found at https://docs.airbyte.com/integrations/sources/sendgrid
        """
        self.apikey = check.str_param(apikey, "apikey")
        self.start_time = check.inst_param(start_time, "start_time", (int, str))
        super().__init__("Sendgrid", name)


class MondaySource(GeneratedAirbyteSource):
    class OAuth20:
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
        def __init__(self, api_token: str):
            self.auth_type = "api_token"
            self.api_token = check.str_param(api_token, "api_token")

    def __init__(self, name: str, credentials: Union[OAuth20, APIToken]):
        """
        Airbyte Source for Monday

        Documentation can be found at https://docs.airbyte.com/integrations/sources/monday
        """
        self.credentials = check.inst_param(
            credentials, "credentials", (MondaySource.OAuth20, MondaySource.APIToken)
        )
        super().__init__("Monday", name)


class DixaSource(GeneratedAirbyteSource):
    def __init__(
        self, name: str, api_token: str, start_date: str, batch_size: Optional[int] = None
    ):
        """
        Airbyte Source for Dixa

        Documentation can be found at https://docs.airbyte.com/integrations/sources/dixa
        """
        self.api_token = check.str_param(api_token, "api_token")
        self.start_date = check.str_param(start_date, "start_date")
        self.batch_size = check.opt_int_param(batch_size, "batch_size")
        super().__init__("Dixa", name)


class SalesforceSource(GeneratedAirbyteSource):
    class FilterSalesforceObjectsEntry:
        def __init__(self, criteria: str, value: str):
            self.criteria = check.str_param(criteria, "criteria")
            self.value = check.str_param(value, "value")

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
        """
        Airbyte Source for Salesforce

        Documentation can be found at https://docs.airbyte.com/integrations/sources/salesforce
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
        def __init__(self, client_id: str, client_secret: str, refresh_token: str):
            self.auth_type = "Client"
            self.client_id = check.str_param(client_id, "client_id")
            self.client_secret = check.str_param(client_secret, "client_secret")
            self.refresh_token = check.str_param(refresh_token, "refresh_token")

    class APIKeyAuthentication:
        def __init__(self, api_token: str):
            self.auth_type = "Token"
            self.api_token = check.str_param(api_token, "api_token")

    def __init__(
        self,
        name: str,
        authorization: Union[SignInViaPipedriveOAuth, APIKeyAuthentication],
        replication_start_date: str,
    ):
        """
        Airbyte Source for Pipedrive

        Documentation can be found at https://docs.airbyte.com/integrations/sources/pipedrive
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
        def __init__(self, user_agent: Optional[bool] = None):
            self.storage = "HTTPS"
            self.user_agent = check.opt_bool_param(user_agent, "user_agent")

    class GCSGoogleCloudStorage:
        def __init__(self, service_account_json: Optional[str] = None):
            self.storage = "GCS"
            self.service_account_json = check.opt_str_param(
                service_account_json, "service_account_json"
            )

    class S3AmazonWebServices:
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
        def __init__(
            self, user: str, host: str, password: Optional[str] = None, port: Optional[str] = None
        ):
            self.storage = "SSH"
            self.user = check.str_param(user, "user")
            self.password = check.opt_str_param(password, "password")
            self.host = check.str_param(host, "host")
            self.port = check.opt_str_param(port, "port")

    class SCPSecureCopyProtocol:
        def __init__(
            self, user: str, host: str, password: Optional[str] = None, port: Optional[str] = None
        ):
            self.storage = "SCP"
            self.user = check.str_param(user, "user")
            self.password = check.opt_str_param(password, "password")
            self.host = check.str_param(host, "host")
            self.port = check.opt_str_param(port, "port")

    class SFTPSecureFileTransferProtocol:
        def __init__(
            self, user: str, host: str, password: Optional[str] = None, port: Optional[str] = None
        ):
            self.storage = "SFTP"
            self.user = check.str_param(user, "user")
            self.password = check.opt_str_param(password, "password")
            self.host = check.str_param(host, "host")
            self.port = check.opt_str_param(port, "port")

    class LocalFilesystemLimited:
        def __init__(
            self,
        ):
            self.storage = "local"

    def __init__(
        self,
        name: str,
        dataset_name: str,
        format: str,
        url: str,
        provider: Union[
            HTTPSPublicWeb,
            GCSGoogleCloudStorage,
            S3AmazonWebServices,
            AzBlobAzureBlobStorage,
            SSHSecureShell,
            SCPSecureCopyProtocol,
            SFTPSecureFileTransferProtocol,
            LocalFilesystemLimited,
        ],
        reader_options: Optional[str] = None,
    ):
        """
        Airbyte Source for File

        Documentation can be found at https://docs.airbyte.com/integrations/sources/file
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
    def __init__(self, name: str, api_key: str):
        """
        Airbyte Source for Glassfrog

        Documentation can be found at https://docs.airbyte.com/integrations/sources/glassfrog
        """
        self.api_key = check.str_param(api_key, "api_key")
        super().__init__("Glassfrog", name)


class ChartmogulSource(GeneratedAirbyteSource):
    def __init__(self, name: str, api_key: str, start_date: str, interval: str):
        """
        Airbyte Source for Chartmogul

        Documentation can be found at https://docs.airbyte.com/integrations/sources/chartmogul
        """
        self.api_key = check.str_param(api_key, "api_key")
        self.start_date = check.str_param(start_date, "start_date")
        self.interval = check.str_param(interval, "interval")
        super().__init__("Chartmogul", name)


class OrbSource(GeneratedAirbyteSource):
    def __init__(
        self,
        name: str,
        api_key: str,
        start_date: Optional[str] = None,
        lookback_window_days: Optional[int] = None,
        string_event_properties_keys: Optional[List[str]] = None,
        numeric_event_properties_keys: Optional[List[str]] = None,
    ):
        """
        Airbyte Source for Orb

        Documentation can be found at https://docs.withorb.com/
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
        """
        Airbyte Source for Cockroachdb

        Documentation can be found at https://docs.airbyte.com/integrations/sources/cockroachdb
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
    def __init__(self, name: str, api_token: str, domain_name: str, email: str):
        """
        Airbyte Source for Confluence

        Documentation can be found at https://docsurl.com
        """
        self.api_token = check.str_param(api_token, "api_token")
        self.domain_name = check.str_param(domain_name, "domain_name")
        self.email = check.str_param(email, "email")
        super().__init__("Confluence", name)


class PlaidSource(GeneratedAirbyteSource):
    def __init__(
        self,
        name: str,
        access_token: str,
        api_key: str,
        client_id: str,
        plaid_env: str,
        start_date: Optional[str] = None,
    ):
        """
        Airbyte Source for Plaid

        Documentation can be found at https://plaid.com/docs/api/
        """
        self.access_token = check.str_param(access_token, "access_token")
        self.api_key = check.str_param(api_key, "api_key")
        self.client_id = check.str_param(client_id, "client_id")
        self.plaid_env = check.str_param(plaid_env, "plaid_env")
        self.start_date = check.opt_str_param(start_date, "start_date")
        super().__init__("Plaid", name)


class SnapchatMarketingSource(GeneratedAirbyteSource):
    def __init__(
        self,
        name: str,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ):
        """
        Airbyte Source for Snapchat Marketing

        Documentation can be found at https://docs.airbyte.com/integrations/sources/snapchat-marketing
        """
        self.client_id = check.str_param(client_id, "client_id")
        self.client_secret = check.str_param(client_secret, "client_secret")
        self.refresh_token = check.str_param(refresh_token, "refresh_token")
        self.start_date = check.opt_str_param(start_date, "start_date")
        self.end_date = check.opt_str_param(end_date, "end_date")
        super().__init__("Snapchat Marketing", name)


class MicrosoftTeamsSource(GeneratedAirbyteSource):
    class AuthenticateViaMicrosoftOAuth20:
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

    def __init__(
        self,
        name: str,
        period: str,
        credentials: Union[AuthenticateViaMicrosoftOAuth20, AuthenticateViaMicrosoft],
    ):
        """
        Airbyte Source for Microsoft Teams

        Documentation can be found at https://docs.airbyte.com/integrations/sources/microsoft-teams
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

    def __init__(
        self,
        name: str,
        credentials: OAuthCredentials,
        start_date: str,
        environment: Optional[str] = None,
    ):
        """
        Airbyte Source for Lever Hiring

        Documentation can be found at https://docs.airbyte.com/integrations/sources/lever-hiring
        """
        self.credentials = check.inst_param(
            credentials, "credentials", LeverHiringSource.OAuthCredentials
        )
        self.start_date = check.str_param(start_date, "start_date")
        self.environment = check.opt_str_param(environment, "environment")
        super().__init__("Lever Hiring", name)


class TwilioSource(GeneratedAirbyteSource):
    def __init__(
        self,
        name: str,
        account_sid: str,
        auth_token: str,
        start_date: str,
        lookback_window: Optional[int] = None,
    ):
        """
        Airbyte Source for Twilio

        Documentation can be found at https://docs.airbyte.com/integrations/sources/twilio
        """
        self.account_sid = check.str_param(account_sid, "account_sid")
        self.auth_token = check.str_param(auth_token, "auth_token")
        self.start_date = check.str_param(start_date, "start_date")
        self.lookback_window = check.opt_int_param(lookback_window, "lookback_window")
        super().__init__("Twilio", name)


class StripeSource(GeneratedAirbyteSource):
    def __init__(
        self,
        name: str,
        account_id: str,
        client_secret: str,
        start_date: str,
        lookback_window_days: Optional[int] = None,
        slice_range: Optional[int] = None,
    ):
        """
        Airbyte Source for Stripe

        Documentation can be found at https://docs.airbyte.com/integrations/sources/stripe
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
        def __init__(
            self,
        ):
            self.encryption_method = "unencrypted"

    class TLSEncryptedVerifyCertificate:
        def __init__(self, ssl_certificate: str, key_store_password: Optional[str] = None):
            self.encryption_method = "encrypted_verify_certificate"
            self.ssl_certificate = check.str_param(ssl_certificate, "ssl_certificate")
            self.key_store_password = check.opt_str_param(key_store_password, "key_store_password")

    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        db: str,
        username: str,
        password: str,
        encryption: Union[Unencrypted, TLSEncryptedVerifyCertificate],
        jdbc_url_params: Optional[str] = None,
    ):
        """
        Airbyte Source for Db2

        Documentation can be found at https://docs.airbyte.com/integrations/sources/db2
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
        def __init__(self, api_token: str):
            self.api_token = check.str_param(api_token, "api_token")

    def __init__(
        self,
        name: str,
        start_date: str,
        lookback_window: int,
        join_channels: bool,
        credentials: Union[DefaultOAuth20Authorization, APITokenCredentials],
        channel_filter: Optional[List[str]] = None,
    ):
        """
        Airbyte Source for Slack

        Documentation can be found at https://docs.airbyte.com/integrations/sources/slack
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
    def __init__(self, name: str, start_date: str, access_token: str):
        """
        Airbyte Source for Recharge

        Documentation can be found at https://docs.airbyte.com/integrations/sources/recharge
        """
        self.start_date = check.str_param(start_date, "start_date")
        self.access_token = check.str_param(access_token, "access_token")
        super().__init__("Recharge", name)


class OpenweatherSource(GeneratedAirbyteSource):
    def __init__(
        self,
        name: str,
        lat: str,
        lon: str,
        appid: str,
        units: Optional[str] = None,
        lang: Optional[str] = None,
    ):
        """
        Airbyte Source for Openweather

        Documentation can be found at https://docsurl.com
        """
        self.lat = check.str_param(lat, "lat")
        self.lon = check.str_param(lon, "lon")
        self.appid = check.str_param(appid, "appid")
        self.units = check.opt_str_param(units, "units")
        self.lang = check.opt_str_param(lang, "lang")
        super().__init__("Openweather", name)


class RetentlySource(GeneratedAirbyteSource):
    class AuthenticateViaRetentlyOAuth:
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
        def __init__(self, api_key: str, auth_type: Optional[str] = None):
            self.auth_type = check.opt_str_param(auth_type, "auth_type")
            self.api_key = check.str_param(api_key, "api_key")

    def __init__(
        self, name: str, credentials: Union[AuthenticateViaRetentlyOAuth, AuthenticateWithAPIToken]
    ):
        """
        Airbyte Source for Retently

        Documentation can be found at https://docsurl.com
        """
        self.credentials = check.inst_param(
            credentials,
            "credentials",
            (RetentlySource.AuthenticateViaRetentlyOAuth, RetentlySource.AuthenticateWithAPIToken),
        )
        super().__init__("Retently", name)


class ScaffoldSourceHttpSource(GeneratedAirbyteSource):
    def __init__(self, name: str, TODO: str):
        """
        Airbyte Source for Scaffold Source Http

        Documentation can be found at https://docsurl.com
        """
        self.TODO = check.str_param(TODO, "TODO")
        super().__init__("Scaffold Source Http", name)


class YandexMetricaSource(GeneratedAirbyteSource):
    def __init__(self, name: str, auth_token: str, counter_id: str, start_date: str, end_date: str):
        """
        Airbyte Source for Yandex Metrica

        Documentation can be found at https://docsurl.com
        """
        self.auth_token = check.str_param(auth_token, "auth_token")
        self.counter_id = check.str_param(counter_id, "counter_id")
        self.start_date = check.str_param(start_date, "start_date")
        self.end_date = check.str_param(end_date, "end_date")
        super().__init__("Yandex Metrica", name)


class TalkdeskExploreSource(GeneratedAirbyteSource):
    def __init__(
        self,
        name: str,
        start_date: str,
        auth_url: str,
        api_key: str,
        timezone: Optional[str] = None,
    ):
        """
        Airbyte Source for Talkdesk Explore

        Documentation can be found at https://docsurl.com
        """
        self.start_date = check.str_param(start_date, "start_date")
        self.timezone = check.opt_str_param(timezone, "timezone")
        self.auth_url = check.str_param(auth_url, "auth_url")
        self.api_key = check.str_param(api_key, "api_key")
        super().__init__("Talkdesk Explore", name)


class ChargifySource(GeneratedAirbyteSource):
    def __init__(self, name: str, api_key: str, domain: str):
        """
        Airbyte Source for Chargify

        Documentation can be found at https://docs.airbyte.com/integrations/sources/chargify
        """
        self.api_key = check.str_param(api_key, "api_key")
        self.domain = check.str_param(domain, "domain")
        super().__init__("Chargify", name)


class RkiCovidSource(GeneratedAirbyteSource):
    def __init__(self, name: str, start_date: str):
        """
        Airbyte Source for Rki Covid

        Documentation can be found at https://docs.airbyte.com/integrations/sources/rki-covid
        """
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Rki Covid", name)


class PostgresSource(GeneratedAirbyteSource):
    class Disable:
        def __init__(
            self,
        ):
            self.mode = "disable"

    class Allow:
        def __init__(
            self,
        ):
            self.mode = "allow"

    class Prefer:
        def __init__(
            self,
        ):
            self.mode = "prefer"

    class Require:
        def __init__(
            self,
        ):
            self.mode = "require"

    class VerifyCa:
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
        def __init__(
            self,
        ):
            self.method = "Standard"

    class LogicalReplicationCDC:
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
        def __init__(
            self,
        ):
            self.tunnel_method = "NO_TUNNEL"

    class SSHKeyAuthentication:
        def __init__(self, tunnel_host: str, tunnel_port: int, tunnel_user: str, ssh_key: str):
            self.tunnel_method = "SSH_KEY_AUTH"
            self.tunnel_host = check.str_param(tunnel_host, "tunnel_host")
            self.tunnel_port = check.int_param(tunnel_port, "tunnel_port")
            self.tunnel_user = check.str_param(tunnel_user, "tunnel_user")
            self.ssh_key = check.str_param(ssh_key, "ssh_key")

    class PasswordAuthentication:
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

    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        database: str,
        username: str,
        ssl_mode: Union[Disable, Allow, Prefer, Require, VerifyCa, VerifyFull],
        replication_method: Union[Standard, LogicalReplicationCDC],
        tunnel_method: Union[NoTunnel, SSHKeyAuthentication, PasswordAuthentication],
        schemas: Optional[List[str]] = None,
        password: Optional[str] = None,
        jdbc_url_params: Optional[str] = None,
        ssl: Optional[bool] = None,
    ):
        """
        Airbyte Source for Postgres

        Documentation can be found at https://docs.airbyte.com/integrations/sources/postgres
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
    def __init__(
        self,
        name: str,
        token: str,
        key: str,
        start_date: str,
        board_ids: Optional[List[str]] = None,
    ):
        """
        Airbyte Source for Trello

        Documentation can be found at https://docs.airbyte.com/integrations/sources/trello
        """
        self.token = check.str_param(token, "token")
        self.key = check.str_param(key, "key")
        self.start_date = check.str_param(start_date, "start_date")
        self.board_ids = check.opt_nullable_list_param(board_ids, "board_ids", str)
        super().__init__("Trello", name)


class PrestashopSource(GeneratedAirbyteSource):
    def __init__(self, name: str, url: str, access_key: str):
        """
        Airbyte Source for Prestashop

        Documentation can be found at https://docsurl.com
        """
        self.url = check.str_param(url, "url")
        self.access_key = check.str_param(access_key, "access_key")
        super().__init__("Prestashop", name)


class PaystackSource(GeneratedAirbyteSource):
    def __init__(
        self,
        name: str,
        secret_key: str,
        start_date: str,
        lookback_window_days: Optional[int] = None,
    ):
        """
        Airbyte Source for Paystack

        Documentation can be found at https://docs.airbyte.com/integrations/sources/paystack
        """
        self.secret_key = check.str_param(secret_key, "secret_key")
        self.start_date = check.str_param(start_date, "start_date")
        self.lookback_window_days = check.opt_int_param(
            lookback_window_days, "lookback_window_days"
        )
        super().__init__("Paystack", name)


class S3Source(GeneratedAirbyteSource):
    class CSV:
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
        def __init__(self, filetype: Optional[str] = None):
            self.filetype = check.opt_str_param(filetype, "filetype")

    class Jsonl:
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

    def __init__(
        self,
        name: str,
        dataset: str,
        path_pattern: str,
        format: Union[CSV, Parquet, Avro, Jsonl],
        provider: S3AmazonWebServices,
        schema: Optional[str] = None,
    ):
        """
        Airbyte Source for S3

        Documentation can be found at https://docs.airbyte.com/integrations/sources/s3
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
        def __init__(self, username: str, password: str):
            self.auth_type = "username/password"
            self.username = check.str_param(username, "username")
            self.password = check.str_param(password, "password")

    def __init__(
        self,
        name: str,
        credentials: Union[OAuth20, UsernameAndPassword],
        host: str,
        role: str,
        warehouse: str,
        database: str,
        schema: str,
        jdbc_url_params: Optional[str] = None,
    ):
        """
        Airbyte Source for Snowflake

        Documentation can be found at https://docs.airbyte.com/integrations/sources/snowflake
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
    def __init__(self, name: str, api_key: str, secret_key: str, start_date: str):
        """
        Airbyte Source for Amplitude

        Documentation can be found at https://docs.airbyte.com/integrations/sources/amplitude
        """
        self.api_key = check.str_param(api_key, "api_key")
        self.secret_key = check.str_param(secret_key, "secret_key")
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Amplitude", name)


class PosthogSource(GeneratedAirbyteSource):
    def __init__(self, name: str, start_date: str, api_key: str, base_url: Optional[str] = None):
        """
        Airbyte Source for Posthog

        Documentation can be found at https://docs.airbyte.com/integrations/sources/posthog
        """
        self.start_date = check.str_param(start_date, "start_date")
        self.api_key = check.str_param(api_key, "api_key")
        self.base_url = check.opt_str_param(base_url, "base_url")
        super().__init__("Posthog", name)


class PaypalTransactionSource(GeneratedAirbyteSource):
    def __init__(
        self,
        name: str,
        start_date: str,
        is_sandbox: bool,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ):
        """
        Airbyte Source for Paypal Transaction

        Documentation can be found at https://docs.airbyte.com/integrations/sources/paypal-transactions
        """
        self.client_id = check.opt_str_param(client_id, "client_id")
        self.client_secret = check.opt_str_param(client_secret, "client_secret")
        self.refresh_token = check.opt_str_param(refresh_token, "refresh_token")
        self.start_date = check.str_param(start_date, "start_date")
        self.is_sandbox = check.bool_param(is_sandbox, "is_sandbox")
        super().__init__("Paypal Transaction", name)


class MssqlSource(GeneratedAirbyteSource):
    class Unencrypted:
        def __init__(
            self,
        ):
            self.ssl_method = "unencrypted"

    class EncryptedTrustServerCertificate:
        def __init__(
            self,
        ):
            self.ssl_method = "encrypted_trust_server_certificate"

    class EncryptedVerifyCertificate:
        def __init__(self, hostNameInCertificate: Optional[str] = None):
            self.ssl_method = "encrypted_verify_certificate"
            self.hostNameInCertificate = check.opt_str_param(
                hostNameInCertificate, "hostNameInCertificate"
            )

    class Standard:
        def __init__(
            self,
        ):
            self.method = "STANDARD"

    class LogicalReplicationCDC:
        def __init__(
            self, data_to_sync: Optional[str] = None, snapshot_isolation: Optional[str] = None
        ):
            self.method = "CDC"
            self.data_to_sync = check.opt_str_param(data_to_sync, "data_to_sync")
            self.snapshot_isolation = check.opt_str_param(snapshot_isolation, "snapshot_isolation")

    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        database: str,
        username: str,
        ssl_method: Union[Unencrypted, EncryptedTrustServerCertificate, EncryptedVerifyCertificate],
        replication_method: Union[Standard, LogicalReplicationCDC],
        schemas: Optional[List[str]] = None,
        password: Optional[str] = None,
        jdbc_url_params: Optional[str] = None,
    ):
        """
        Airbyte Source for Mssql

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/mssql
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
        """
        Airbyte Source for Zoho Crm

        Documentation can be found at https://docs.airbyte.com/integrations/sources/zoho-crm
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
        """
        Airbyte Source for Redshift

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/redshift
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
        def __init__(self, personal_access_token: str):
            self.personal_access_token = check.str_param(
                personal_access_token, "personal_access_token"
            )

    class OAuthCredentials:
        def __init__(self, client_id: str, client_secret: str, refresh_token: str):
            self.client_id = check.str_param(client_id, "client_id")
            self.client_secret = check.str_param(client_secret, "client_secret")
            self.refresh_token = check.str_param(refresh_token, "refresh_token")

    def __init__(self, name: str, credentials: Union[PATCredentials, OAuthCredentials]):
        """
        Airbyte Source for Asana

        Documentation can be found at https://docsurl.com
        """
        self.credentials = check.inst_param(
            credentials, "credentials", (AsanaSource.PATCredentials, AsanaSource.OAuthCredentials)
        )
        super().__init__("Asana", name)


class SmartsheetsSource(GeneratedAirbyteSource):
    def __init__(
        self,
        name: str,
        access_token: str,
        spreadsheet_id: str,
        start_datetime: Optional[str] = None,
    ):
        """
        Airbyte Source for Smartsheets

        Documentation can be found at https://docs.airbyte.com/integrations/sources/smartsheets
        """
        self.access_token = check.str_param(access_token, "access_token")
        self.spreadsheet_id = check.str_param(spreadsheet_id, "spreadsheet_id")
        self.start_datetime = check.opt_str_param(start_datetime, "start_datetime")
        super().__init__("Smartsheets", name)


class MailchimpSource(GeneratedAirbyteSource):
    class OAuth20:
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
        def __init__(self, apikey: str):
            self.auth_type = "apikey"
            self.apikey = check.str_param(apikey, "apikey")

    def __init__(self, name: str, credentials: Union[OAuth20, APIKey]):
        """
        Airbyte Source for Mailchimp

        Documentation can be found at https://docs.airbyte.com/integrations/sources/mailchimp
        """
        self.credentials = check.inst_param(
            credentials, "credentials", (MailchimpSource.OAuth20, MailchimpSource.APIKey)
        )
        super().__init__("Mailchimp", name)


class SentrySource(GeneratedAirbyteSource):
    def __init__(
        self,
        name: str,
        auth_token: str,
        organization: str,
        project: str,
        hostname: Optional[str] = None,
        discover_fields: Optional[List[str]] = None,
    ):
        """
        Airbyte Source for Sentry

        Documentation can be found at https://docs.airbyte.com/integrations/sources/sentry
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
    def __init__(
        self,
        name: str,
        private_key: str,
        domain_region: Optional[str] = None,
        start_date: Optional[str] = None,
    ):
        """
        Airbyte Source for Mailgun

        Documentation can be found at https://docs.airbyte.com/integrations/sources/mailgun
        """
        self.private_key = check.str_param(private_key, "private_key")
        self.domain_region = check.opt_str_param(domain_region, "domain_region")
        self.start_date = check.opt_str_param(start_date, "start_date")
        super().__init__("Mailgun", name)


class OnesignalSource(GeneratedAirbyteSource):
    def __init__(self, name: str, user_auth_key: str, start_date: str, outcome_names: str):
        """
        Airbyte Source for Onesignal

        Documentation can be found at https://docs.airbyte.com/integrations/sources/onesignal
        """
        self.user_auth_key = check.str_param(user_auth_key, "user_auth_key")
        self.start_date = check.str_param(start_date, "start_date")
        self.outcome_names = check.str_param(outcome_names, "outcome_names")
        super().__init__("Onesignal", name)


class PythonHttpTutorialSource(GeneratedAirbyteSource):
    def __init__(self, name: str, start_date: str, base: str, access_key: Optional[str] = None):
        """
        Airbyte Source for Python Http Tutorial

        Documentation can be found at https://docs.airbyte.com/integrations/sources/exchangeratesapi
        """
        self.access_key = check.opt_str_param(access_key, "access_key")
        self.start_date = check.str_param(start_date, "start_date")
        self.base = check.str_param(base, "base")
        super().__init__("Python Http Tutorial", name)


class AirtableSource(GeneratedAirbyteSource):
    def __init__(self, name: str, api_key: str, base_id: str, tables: List[str]):
        """
        Airbyte Source for Airtable

        Documentation can be found at https://docs.airbyte.com/integrations/sources/airtable
        """
        self.api_key = check.str_param(api_key, "api_key")
        self.base_id = check.str_param(base_id, "base_id")
        self.tables = check.list_param(tables, "tables", str)
        super().__init__("Airtable", name)


class MongodbV2Source(GeneratedAirbyteSource):
    class StandaloneMongoDbInstance:
        def __init__(self, instance: str, host: str, port: int, tls: Optional[bool] = None):
            self.instance = check.str_param(instance, "instance")
            self.host = check.str_param(host, "host")
            self.port = check.int_param(port, "port")
            self.tls = check.opt_bool_param(tls, "tls")

    class ReplicaSet:
        def __init__(self, instance: str, server_addresses: str, replica_set: Optional[str] = None):
            self.instance = check.str_param(instance, "instance")
            self.server_addresses = check.str_param(server_addresses, "server_addresses")
            self.replica_set = check.opt_str_param(replica_set, "replica_set")

    class MongoDBAtlas:
        def __init__(self, instance: str, cluster_url: str):
            self.instance = check.str_param(instance, "instance")
            self.cluster_url = check.str_param(cluster_url, "cluster_url")

    def __init__(
        self,
        name: str,
        instance_type: Union[StandaloneMongoDbInstance, ReplicaSet, MongoDBAtlas],
        database: str,
        user: Optional[str] = None,
        password: Optional[str] = None,
        auth_source: Optional[str] = None,
    ):
        """
        Airbyte Source for Mongodb V2

        Documentation can be found at https://docs.airbyte.com/integrations/sources/mongodb-v2
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
        def __init__(self, user_agent: Optional[bool] = None):
            self.storage = "HTTPS"
            self.user_agent = check.opt_bool_param(user_agent, "user_agent")

    class GCSGoogleCloudStorage:
        def __init__(self, service_account_json: Optional[str] = None):
            self.storage = "GCS"
            self.service_account_json = check.opt_str_param(
                service_account_json, "service_account_json"
            )

    class S3AmazonWebServices:
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
        def __init__(
            self, user: str, host: str, password: Optional[str] = None, port: Optional[str] = None
        ):
            self.storage = "SSH"
            self.user = check.str_param(user, "user")
            self.password = check.opt_str_param(password, "password")
            self.host = check.str_param(host, "host")
            self.port = check.opt_str_param(port, "port")

    class SCPSecureCopyProtocol:
        def __init__(
            self, user: str, host: str, password: Optional[str] = None, port: Optional[str] = None
        ):
            self.storage = "SCP"
            self.user = check.str_param(user, "user")
            self.password = check.opt_str_param(password, "password")
            self.host = check.str_param(host, "host")
            self.port = check.opt_str_param(port, "port")

    class SFTPSecureFileTransferProtocol:
        def __init__(
            self, user: str, host: str, password: Optional[str] = None, port: Optional[str] = None
        ):
            self.storage = "SFTP"
            self.user = check.str_param(user, "user")
            self.password = check.opt_str_param(password, "password")
            self.host = check.str_param(host, "host")
            self.port = check.opt_str_param(port, "port")

    def __init__(
        self,
        name: str,
        dataset_name: str,
        format: str,
        url: str,
        provider: Union[
            HTTPSPublicWeb,
            GCSGoogleCloudStorage,
            S3AmazonWebServices,
            AzBlobAzureBlobStorage,
            SSHSecureShell,
            SCPSecureCopyProtocol,
            SFTPSecureFileTransferProtocol,
        ],
        reader_options: Optional[str] = None,
    ):
        """
        Airbyte Source for File Secure

        Documentation can be found at https://docs.airbyte.com/integrations/sources/file
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
        def __init__(self, access_token: str, credentials: Optional[str] = None):
            self.credentials = check.opt_str_param(credentials, "credentials")
            self.access_token = check.str_param(access_token, "access_token")

    class APIToken:
        def __init__(self, email: str, api_token: str, credentials: Optional[str] = None):
            self.credentials = check.opt_str_param(credentials, "credentials")
            self.email = check.str_param(email, "email")
            self.api_token = check.str_param(api_token, "api_token")

    def __init__(
        self, name: str, start_date: str, subdomain: str, credentials: Union[OAuth20, APIToken]
    ):
        """
        Airbyte Source for Zendesk Support

        Documentation can be found at https://docs.airbyte.com/integrations/sources/zendesk-support
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
    def __init__(self, name: str, api_token: str):
        """
        Airbyte Source for Tempo

        Documentation can be found at https://docs.airbyte.com/integrations/sources/
        """
        self.api_token = check.str_param(api_token, "api_token")
        super().__init__("Tempo", name)


class BraintreeSource(GeneratedAirbyteSource):
    def __init__(
        self,
        name: str,
        merchant_id: str,
        public_key: str,
        private_key: str,
        environment: str,
        start_date: Optional[str] = None,
    ):
        """
        Airbyte Source for Braintree

        Documentation can be found at https://docs.airbyte.com/integrations/sources/braintree
        """
        self.merchant_id = check.str_param(merchant_id, "merchant_id")
        self.public_key = check.str_param(public_key, "public_key")
        self.private_key = check.str_param(private_key, "private_key")
        self.start_date = check.opt_str_param(start_date, "start_date")
        self.environment = check.str_param(environment, "environment")
        super().__init__("Braintree", name)


class SalesloftSource(GeneratedAirbyteSource):
    def __init__(
        self, name: str, client_id: str, client_secret: str, refresh_token: str, start_date: str
    ):
        """
        Airbyte Source for Salesloft

        Documentation can be found at https://docs.airbyte.com/integrations/sources/salesloft
        """
        self.client_id = check.str_param(client_id, "client_id")
        self.client_secret = check.str_param(client_secret, "client_secret")
        self.refresh_token = check.str_param(refresh_token, "refresh_token")
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Salesloft", name)


class LinnworksSource(GeneratedAirbyteSource):
    def __init__(
        self, name: str, application_id: str, application_secret: str, token: str, start_date: str
    ):
        """
        Airbyte Source for Linnworks

        Documentation can be found at https://docs.airbyte.com/integrations/sources/linnworks
        """
        self.application_id = check.str_param(application_id, "application_id")
        self.application_secret = check.str_param(application_secret, "application_secret")
        self.token = check.str_param(token, "token")
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Linnworks", name)


class ChargebeeSource(GeneratedAirbyteSource):
    def __init__(
        self, name: str, site: str, site_api_key: str, start_date: str, product_catalog: str
    ):
        """
        Airbyte Source for Chargebee

        Documentation can be found at https://apidocs.chargebee.com/docs/api
        """
        self.site = check.str_param(site, "site")
        self.site_api_key = check.str_param(site_api_key, "site_api_key")
        self.start_date = check.str_param(start_date, "start_date")
        self.product_catalog = check.str_param(product_catalog, "product_catalog")
        super().__init__("Chargebee", name)


class GoogleAnalyticsDataApiSource(GeneratedAirbyteSource):
    class AuthenticateViaGoogleOauth:
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
        def __init__(self, credentials_json: str, auth_type: Optional[str] = None):
            self.auth_type = check.opt_str_param(auth_type, "auth_type")
            self.credentials_json = check.str_param(credentials_json, "credentials_json")

    def __init__(
        self,
        name: str,
        property_id: str,
        credentials: Union[AuthenticateViaGoogleOauth, ServiceAccountKeyAuthentication],
        date_ranges_start_date: str,
        custom_reports: Optional[str] = None,
        window_in_days: Optional[int] = None,
    ):
        """
        Airbyte Source for Google Analytics Data Api

        Documentation can be found at https://docs.airbyte.com/integrations/sources/google-analytics-v4
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
    def __init__(
        self,
        name: str,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        redirect_uri: str,
        start_date: str,
    ):
        """
        Airbyte Source for Outreach

        Documentation can be found at https://docs.airbyte.com/integrations/sources/outreach
        """
        self.client_id = check.str_param(client_id, "client_id")
        self.client_secret = check.str_param(client_secret, "client_secret")
        self.refresh_token = check.str_param(refresh_token, "refresh_token")
        self.redirect_uri = check.str_param(redirect_uri, "redirect_uri")
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Outreach", name)


class LemlistSource(GeneratedAirbyteSource):
    def __init__(self, name: str, api_key: str):
        """
        Airbyte Source for Lemlist

        Documentation can be found at https://docs.airbyte.com/integrations/sources/lemlist
        """
        self.api_key = check.str_param(api_key, "api_key")
        super().__init__("Lemlist", name)


class ApifyDatasetSource(GeneratedAirbyteSource):
    def __init__(self, name: str, datasetId: str, clean: Optional[bool] = None):
        """
        Airbyte Source for Apify Dataset

        Documentation can be found at https://docs.airbyte.com/integrations/sources/apify-dataset
        """
        self.datasetId = check.str_param(datasetId, "datasetId")
        self.clean = check.opt_bool_param(clean, "clean")
        super().__init__("Apify Dataset", name)


class RecurlySource(GeneratedAirbyteSource):
    def __init__(
        self,
        name: str,
        api_key: str,
        begin_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ):
        """
        Airbyte Source for Recurly

        Documentation can be found at https://docs.airbyte.com/integrations/sources/recurly
        """
        self.api_key = check.str_param(api_key, "api_key")
        self.begin_time = check.opt_str_param(begin_time, "begin_time")
        self.end_time = check.opt_str_param(end_time, "end_time")
        super().__init__("Recurly", name)


class ZendeskTalkSource(GeneratedAirbyteSource):
    class APIToken:
        def __init__(self, email: str, api_token: str, auth_type: Optional[str] = None):
            self.auth_type = check.opt_str_param(auth_type, "auth_type")
            self.email = check.str_param(email, "email")
            self.api_token = check.str_param(api_token, "api_token")

    class OAuth20:
        def __init__(self, access_token: str, auth_type: Optional[str] = None):
            self.auth_type = check.opt_str_param(auth_type, "auth_type")
            self.access_token = check.str_param(access_token, "access_token")

    def __init__(
        self, name: str, subdomain: str, credentials: Union[APIToken, OAuth20], start_date: str
    ):
        """
        Airbyte Source for Zendesk Talk

        Documentation can be found at https://docs.airbyte.com/integrations/sources/zendesk-talk
        """
        self.subdomain = check.str_param(subdomain, "subdomain")
        self.credentials = check.inst_param(
            credentials, "credentials", (ZendeskTalkSource.APIToken, ZendeskTalkSource.OAuth20)
        )
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Zendesk Talk", name)


class SftpSource(GeneratedAirbyteSource):
    class PasswordAuthentication:
        def __init__(self, auth_user_password: str):
            self.auth_method = "SSH_PASSWORD_AUTH"
            self.auth_user_password = check.str_param(auth_user_password, "auth_user_password")

    class SSHKeyAuthentication:
        def __init__(self, auth_ssh_key: str):
            self.auth_method = "SSH_KEY_AUTH"
            self.auth_ssh_key = check.str_param(auth_ssh_key, "auth_ssh_key")

    def __init__(
        self,
        name: str,
        user: str,
        host: str,
        port: int,
        credentials: Union[PasswordAuthentication, SSHKeyAuthentication],
        file_types: Optional[str] = None,
        folder_path: Optional[str] = None,
        file_pattern: Optional[str] = None,
    ):
        """
        Airbyte Source for Sftp

        Documentation can be found at https://docs.airbyte.com/integrations/source/sftp
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
    def __init__(
        self,
        name: str,
    ):
        """
        Airbyte Source for Whisky Hunter

        Documentation can be found at https://docs.airbyte.io/integrations/sources/whisky-hunter
        """

        super().__init__("Whisky Hunter", name)


class FreshdeskSource(GeneratedAirbyteSource):
    def __init__(
        self,
        name: str,
        domain: str,
        api_key: str,
        requests_per_minute: Optional[int] = None,
        start_date: Optional[str] = None,
    ):
        """
        Airbyte Source for Freshdesk

        Documentation can be found at https://docs.airbyte.com/integrations/sources/freshdesk
        """
        self.domain = check.str_param(domain, "domain")
        self.api_key = check.str_param(api_key, "api_key")
        self.requests_per_minute = check.opt_int_param(requests_per_minute, "requests_per_minute")
        self.start_date = check.opt_str_param(start_date, "start_date")
        super().__init__("Freshdesk", name)


class GocardlessSource(GeneratedAirbyteSource):
    def __init__(
        self,
        name: str,
        access_token: str,
        gocardless_environment: str,
        gocardless_version: str,
        start_date: str,
    ):
        """
        Airbyte Source for Gocardless

        Documentation can be found at https://docs.airbyte.com/integrations/sources/gocardless
        """
        self.access_token = check.str_param(access_token, "access_token")
        self.gocardless_environment = check.str_param(
            gocardless_environment, "gocardless_environment"
        )
        self.gocardless_version = check.str_param(gocardless_version, "gocardless_version")
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Gocardless", name)


class ZuoraSource(GeneratedAirbyteSource):
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
        """
        Airbyte Source for Zuora

        Documentation can be found at https://docs.airbyte.com/integrations/sources/zuora
        """
        self.start_date = check.str_param(start_date, "start_date")
        self.window_in_days = check.opt_str_param(window_in_days, "window_in_days")
        self.tenant_endpoint = check.str_param(tenant_endpoint, "tenant_endpoint")
        self.data_query = check.str_param(data_query, "data_query")
        self.client_id = check.str_param(client_id, "client_id")
        self.client_secret = check.str_param(client_secret, "client_secret")
        super().__init__("Zuora", name)


class MarketoSource(GeneratedAirbyteSource):
    def __init__(
        self, name: str, domain_url: str, client_id: str, client_secret: str, start_date: str
    ):
        """
        Airbyte Source for Marketo

        Documentation can be found at https://docs.airbyte.com/integrations/sources/marketo
        """
        self.domain_url = check.str_param(domain_url, "domain_url")
        self.client_id = check.str_param(client_id, "client_id")
        self.client_secret = check.str_param(client_secret, "client_secret")
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Marketo", name)


class DriftSource(GeneratedAirbyteSource):
    class OAuth20:
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
        def __init__(self, access_token: str, credentials: Optional[str] = None):
            self.credentials = check.opt_str_param(credentials, "credentials")
            self.access_token = check.str_param(access_token, "access_token")

    def __init__(self, name: str, credentials: Union[OAuth20, AccessToken]):
        """
        Airbyte Source for Drift

        Documentation can be found at https://docs.airbyte.com/integrations/sources/drift
        """
        self.credentials = check.inst_param(
            credentials, "credentials", (DriftSource.OAuth20, DriftSource.AccessToken)
        )
        super().__init__("Drift", name)


class PokeapiSource(GeneratedAirbyteSource):
    def __init__(self, name: str, pokemon_name: str):
        """
        Airbyte Source for Pokeapi

        Documentation can be found at https://docs.airbyte.com/integrations/sources/pokeapi
        """
        self.pokemon_name = check.str_param(pokemon_name, "pokemon_name")
        super().__init__("Pokeapi", name)


class NetsuiteSource(GeneratedAirbyteSource):
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
        """
        Airbyte Source for Netsuite

        Documentation can be found at https://docsurl.com
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
    def __init__(self, name: str, api_key: str):
        """
        Airbyte Source for Hubplanner

        Documentation can be found at https://docs.airbyte.com/integrations/sources/hubplanner
        """
        self.api_key = check.str_param(api_key, "api_key")
        super().__init__("Hubplanner", name)


class Dv360Source(GeneratedAirbyteSource):
    class Oauth2Credentials:
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

    def __init__(
        self,
        name: str,
        credentials: Oauth2Credentials,
        partner_id: int,
        start_date: str,
        end_date: Optional[str] = None,
        filters: Optional[List[str]] = None,
    ):
        """
        Airbyte Source for Dv 360

        Documentation can be found at https://docsurl.com
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
        def __init__(self, client_id: str, client_secret: str, access_token: str):
            self.auth_type = "OAuth2.0"
            self.client_id = check.str_param(client_id, "client_id")
            self.client_secret = check.str_param(client_secret, "client_secret")
            self.access_token = check.str_param(access_token, "access_token")

    class AccessToken:
        def __init__(self, token: str):
            self.auth_type = "token"
            self.token = check.str_param(token, "token")

    def __init__(self, name: str, start_date: str, credentials: Union[OAuth20, AccessToken]):
        """
        Airbyte Source for Notion

        Documentation can be found at https://docs.airbyte.com/integrations/sources/notion
        """
        self.start_date = check.str_param(start_date, "start_date")
        self.credentials = check.inst_param(
            credentials, "credentials", (NotionSource.OAuth20, NotionSource.AccessToken)
        )
        super().__init__("Notion", name)


class ZendeskSunshineSource(GeneratedAirbyteSource):
    class OAuth20:
        def __init__(self, client_id: str, client_secret: str, access_token: str):
            self.auth_method = "oauth2.0"
            self.client_id = check.str_param(client_id, "client_id")
            self.client_secret = check.str_param(client_secret, "client_secret")
            self.access_token = check.str_param(access_token, "access_token")

    class APIToken:
        def __init__(self, api_token: str, email: str):
            self.auth_method = "api_token"
            self.api_token = check.str_param(api_token, "api_token")
            self.email = check.str_param(email, "email")

    def __init__(
        self, name: str, subdomain: str, start_date: str, credentials: Union[OAuth20, APIToken]
    ):
        """
        Airbyte Source for Zendesk Sunshine

        Documentation can be found at https://docs.airbyte.com/integrations/sources/zendesk_sunshine
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
        def __init__(self, access_token: str):
            self.auth_method = "access_token"
            self.access_token = check.str_param(access_token, "access_token")

    def __init__(self, name: str, start_date: str, credentials: Union[OAuth20, AccessToken]):
        """
        Airbyte Source for Pinterest

        Documentation can be found at https://docs.airbyte.com/integrations/sources/pinterest
        """
        self.start_date = check.str_param(start_date, "start_date")
        self.credentials = check.inst_param(
            credentials, "credentials", (PinterestSource.OAuth20, PinterestSource.AccessToken)
        )
        super().__init__("Pinterest", name)


class MetabaseSource(GeneratedAirbyteSource):
    def __init__(
        self,
        name: str,
        instance_api_url: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        session_token: Optional[str] = None,
    ):
        """
        Airbyte Source for Metabase

        Documentation can be found at https://docs.airbyte.com/integrations/sources/metabase
        """
        self.instance_api_url = check.str_param(instance_api_url, "instance_api_url")
        self.username = check.opt_str_param(username, "username")
        self.password = check.opt_str_param(password, "password")
        self.session_token = check.opt_str_param(session_token, "session_token")
        super().__init__("Metabase", name)


class HubspotSource(GeneratedAirbyteSource):
    class OAuth:
        def __init__(self, client_id: str, client_secret: str, refresh_token: str):
            self.credentials_title = "OAuth Credentials"
            self.client_id = check.str_param(client_id, "client_id")
            self.client_secret = check.str_param(client_secret, "client_secret")
            self.refresh_token = check.str_param(refresh_token, "refresh_token")

    class APIKey:
        def __init__(self, api_key: str):
            self.credentials_title = "API Key Credentials"
            self.api_key = check.str_param(api_key, "api_key")

    class PrivateAPP:
        def __init__(self, access_token: str):
            self.credentials_title = "Private App Credentials"
            self.access_token = check.str_param(access_token, "access_token")

    def __init__(self, name: str, start_date: str, credentials: Union[OAuth, APIKey, PrivateAPP]):
        """
        Airbyte Source for Hubspot

        Documentation can be found at https://docs.airbyte.com/integrations/sources/hubspot
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
        def __init__(self, api_token: str, auth_type: Optional[str] = None):
            self.auth_type = check.opt_str_param(auth_type, "auth_type")
            self.api_token = check.str_param(api_token, "api_token")

    def __init__(
        self,
        name: str,
        account_id: str,
        replication_start_date: str,
        credentials: Union[AuthenticateViaHarvestOAuth, AuthenticateWithPersonalAccessToken],
    ):
        """
        Airbyte Source for Harvest

        Documentation can be found at https://docs.airbyte.com/integrations/sources/harvest
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
        def __init__(self, access_token: str):
            self.access_token = check.str_param(access_token, "access_token")

    class PATCredentials:
        def __init__(self, personal_access_token: str):
            self.personal_access_token = check.str_param(
                personal_access_token, "personal_access_token"
            )

    def __init__(
        self,
        name: str,
        credentials: Union[OAuthCredentials, PATCredentials],
        start_date: str,
        repository: str,
        branch: Optional[str] = None,
        page_size_for_large_streams: Optional[int] = None,
    ):
        """
        Airbyte Source for Github

        Documentation can be found at https://docs.airbyte.com/integrations/sources/github
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
        def __init__(
            self, stream_name: str, stream_schema: str, stream_duplication: Optional[int] = None
        ):
            self.type = "SINGLE_STREAM"
            self.stream_name = check.str_param(stream_name, "stream_name")
            self.stream_schema = check.str_param(stream_schema, "stream_schema")
            self.stream_duplication = check.opt_int_param(stream_duplication, "stream_duplication")

    class MultiSchema:
        def __init__(self, stream_schemas: str):
            self.type = "MULTI_STREAM"
            self.stream_schemas = check.str_param(stream_schemas, "stream_schemas")

    def __init__(
        self,
        name: str,
        max_messages: int,
        mock_catalog: Union[SingleSchema, MultiSchema],
        type: Optional[str] = None,
        seed: Optional[int] = None,
        message_interval_ms: Optional[int] = None,
    ):
        """
        Airbyte Source for E2e Test

        Documentation can be found at https://docs.airbyte.com/integrations/sources/e2e-test
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
        def __init__(
            self,
        ):
            self.mode = "preferred"

    class Required:
        def __init__(
            self,
        ):
            self.mode = "required"

    class VerifyCA:
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
        def __init__(
            self,
        ):
            self.method = "STANDARD"

    class LogicalReplicationCDC:
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

    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        database: str,
        username: str,
        ssl_mode: Union[Preferred, Required, VerifyCA, VerifyIdentity],
        replication_method: Union[Standard, LogicalReplicationCDC],
        password: Optional[str] = None,
        jdbc_url_params: Optional[str] = None,
        ssl: Optional[bool] = None,
    ):
        """
        Airbyte Source for Mysql

        Documentation can be found at https://docs.airbyte.com/integrations/sources/mysql
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
    def __init__(
        self,
        name: str,
        email: str,
        password: str,
        start_date: str,
        logs_batch_size: Optional[int] = None,
    ):
        """
        Airbyte Source for My Hours

        Documentation can be found at https://docs.airbyte.com/integrations/sources/my-hours
        """
        self.email = check.str_param(email, "email")
        self.password = check.str_param(password, "password")
        self.start_date = check.str_param(start_date, "start_date")
        self.logs_batch_size = check.opt_int_param(logs_batch_size, "logs_batch_size")
        super().__init__("My Hours", name)


class KyribaSource(GeneratedAirbyteSource):
    def __init__(
        self,
        name: str,
        domain: str,
        username: str,
        password: str,
        start_date: str,
        end_date: Optional[str] = None,
    ):
        """
        Airbyte Source for Kyriba

        Documentation can be found at https://docsurl.com
        """
        self.domain = check.str_param(domain, "domain")
        self.username = check.str_param(username, "username")
        self.password = check.str_param(password, "password")
        self.start_date = check.str_param(start_date, "start_date")
        self.end_date = check.opt_str_param(end_date, "end_date")
        super().__init__("Kyriba", name)


class GoogleSearchConsoleSource(GeneratedAirbyteSource):
    class OAuth:
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
        def __init__(self, service_account_info: str, email: str):
            self.auth_type = "Service"
            self.service_account_info = check.str_param(
                service_account_info, "service_account_info"
            )
            self.email = check.str_param(email, "email")

    def __init__(
        self,
        name: str,
        site_urls: List[str],
        start_date: str,
        authorization: Union[OAuth, ServiceAccountKeyAuthentication],
        end_date: Optional[str] = None,
        custom_reports: Optional[str] = None,
    ):
        """
        Airbyte Source for Google Search Console

        Documentation can be found at https://docs.airbyte.com/integrations/sources/google-search-console
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
        """
        Airbyte Source for Facebook Marketing

        Documentation can be found at https://docs.airbyte.com/integrations/sources/facebook-marketing
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
    def __init__(
        self, name: str, access_token: str, start_date: str, survey_ids: Optional[List[str]] = None
    ):
        """
        Airbyte Source for Surveymonkey

        Documentation can be found at https://docs.airbyte.com/integrations/sources/surveymonkey
        """
        self.access_token = check.str_param(access_token, "access_token")
        self.start_date = check.str_param(start_date, "start_date")
        self.survey_ids = check.opt_nullable_list_param(survey_ids, "survey_ids", str)
        super().__init__("Surveymonkey", name)


class PardotSource(GeneratedAirbyteSource):
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
        """
        Airbyte Source for Pardot

        Documentation can be found at https://docsurl.com
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
    def __init__(self, name: str, api_key: str, start_date: str):
        """
        Airbyte Source for Flexport

        Documentation can be found at https://docs.airbyte.com/integrations/sources/flexport
        """
        self.api_key = check.str_param(api_key, "api_key")
        self.start_date = check.str_param(start_date, "start_date")
        super().__init__("Flexport", name)


class ZenefitsSource(GeneratedAirbyteSource):
    def __init__(self, name: str, token: str):
        """
        Airbyte Source for Zenefits

        Documentation can be found at https://docsurl.com
        """
        self.token = check.str_param(token, "token")
        super().__init__("Zenefits", name)


class KafkaSource(GeneratedAirbyteSource):
    class JSON:
        def __init__(self, deserialization_type: Optional[str] = None):
            self.deserialization_type = check.opt_str_param(
                deserialization_type, "deserialization_type"
            )

    class AVRO:
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
        def __init__(self, topic_partitions: str):
            self.subscription_type = "assign"
            self.topic_partitions = check.str_param(topic_partitions, "topic_partitions")

    class SubscribeToAllTopicsMatchingSpecifiedPattern:
        def __init__(self, topic_pattern: str):
            self.subscription_type = "subscribe"
            self.topic_pattern = check.str_param(topic_pattern, "topic_pattern")

    class PLAINTEXT:
        def __init__(self, security_protocol: str):
            self.security_protocol = check.str_param(security_protocol, "security_protocol")

    class SASLPLAINTEXT:
        def __init__(self, security_protocol: str, sasl_mechanism: str, sasl_jaas_config: str):
            self.security_protocol = check.str_param(security_protocol, "security_protocol")
            self.sasl_mechanism = check.str_param(sasl_mechanism, "sasl_mechanism")
            self.sasl_jaas_config = check.str_param(sasl_jaas_config, "sasl_jaas_config")

    class SASLSSL:
        def __init__(self, security_protocol: str, sasl_mechanism: str, sasl_jaas_config: str):
            self.security_protocol = check.str_param(security_protocol, "security_protocol")
            self.sasl_mechanism = check.str_param(sasl_mechanism, "sasl_mechanism")
            self.sasl_jaas_config = check.str_param(sasl_jaas_config, "sasl_jaas_config")

    def __init__(
        self,
        name: str,
        MessageFormat: Union[JSON, AVRO],
        bootstrap_servers: str,
        subscription: Union[
            ManuallyAssignAListOfPartitions, SubscribeToAllTopicsMatchingSpecifiedPattern
        ],
        protocol: Union[PLAINTEXT, SASLPLAINTEXT, SASLSSL],
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
        """
        Airbyte Source for Kafka

        Documentation can be found at https://docs.airbyte.com/integrations/sources/kafka
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
