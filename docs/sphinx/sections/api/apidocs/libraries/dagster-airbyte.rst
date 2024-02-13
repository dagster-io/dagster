Airbyte (dagster-airbyte)
---------------------------

This library provides a Dagster integration with `Airbyte <https://www.airbyte.com/>`_.

For more information on getting started, see the `Airbyte integration guide </integrations/airbyte>`_.

.. currentmodule:: dagster_airbyte



Resources
=========

.. autoconfigurable:: AirbyteResource
    :annotation: ResourceDefinition


Assets
======

.. autofunction:: load_assets_from_airbyte_instance

.. autofunction:: load_assets_from_airbyte_project

.. autofunction:: build_airbyte_assets


Ops
===

.. autoconfigurable:: airbyte_sync_op


Managed Config
==============

The following APIs are used as part of the experimental ingestion-as-code functionality.
For more information, see the `Airbyte ingestion as code guide </guides/dagster/airbyte-ingestion-as-code>`_.

.. autoclass:: AirbyteManagedElementReconciler
   :members:
   :special-members: __init__

.. autofunction:: load_assets_from_connections

.. autoclass:: AirbyteConnection
   :members:
   :special-members: __init__
.. autoclass:: AirbyteSource
   :members:
   :special-members: __init__
.. autoclass:: AirbyteDestination
   :members:
   :special-members: __init__
.. autoclass:: AirbyteSyncMode
   :members:

Managed Config Generated Sources
================================

.. currentmodule:: dagster_airbyte.managed.generated.sources
.. autoclass:: StravaSource
    :special-members: __init__

.. autoclass:: AppsflyerSource
    :special-members: __init__

.. autoclass:: GoogleWorkspaceAdminReportsSource
    :special-members: __init__

.. autoclass:: CartSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::CartSource.CentralAPIRouter
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::CartSource.SingleStoreAccessToken
    :special-members: __init__

.. autoclass:: LinkedinAdsSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::LinkedinAdsSource.OAuth20
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::LinkedinAdsSource.AccessToken
    :special-members: __init__

.. autoclass:: MongodbSource
    :special-members: __init__

.. autoclass:: TimelySource
    :special-members: __init__

.. autoclass:: StockTickerApiTutorialSource
    :special-members: __init__

.. autoclass:: WrikeSource
    :special-members: __init__

.. autoclass:: CommercetoolsSource
    :special-members: __init__

.. autoclass:: GutendexSource
    :special-members: __init__

.. autoclass:: IterableSource
    :special-members: __init__

.. autoclass:: QuickbooksSingerSource
    :special-members: __init__

.. autoclass:: BigcommerceSource
    :special-members: __init__

.. autoclass:: ShopifySource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::ShopifySource.APIPassword
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::ShopifySource.OAuth20
    :special-members: __init__

.. autoclass:: AppstoreSingerSource
    :special-members: __init__

.. autoclass:: GreenhouseSource
    :special-members: __init__

.. autoclass:: ZoomSingerSource
    :special-members: __init__

.. autoclass:: TiktokMarketingSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::TiktokMarketingSource.OAuth20
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::TiktokMarketingSource.SandboxAccessToken
    :special-members: __init__

.. autoclass:: ZendeskChatSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::ZendeskChatSource.OAuth20
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::ZendeskChatSource.AccessToken
    :special-members: __init__

.. autoclass:: AwsCloudtrailSource
    :special-members: __init__

.. autoclass:: OktaSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::OktaSource.OAuth20
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::OktaSource.APIToken
    :special-members: __init__

.. autoclass:: InsightlySource
    :special-members: __init__

.. autoclass:: LinkedinPagesSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::LinkedinPagesSource.OAuth20
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::LinkedinPagesSource.AccessToken
    :special-members: __init__

.. autoclass:: PersistiqSource
    :special-members: __init__

.. autoclass:: FreshcallerSource
    :special-members: __init__

.. autoclass:: AppfollowSource
    :special-members: __init__

.. autoclass:: FacebookPagesSource
    :special-members: __init__

.. autoclass:: JiraSource
    :special-members: __init__

.. autoclass:: GoogleSheetsSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::GoogleSheetsSource.AuthenticateViaGoogleOAuth
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::GoogleSheetsSource.ServiceAccountKeyAuthentication
    :special-members: __init__

.. autoclass:: DockerhubSource
    :special-members: __init__

.. autoclass:: UsCensusSource
    :special-members: __init__

.. autoclass:: KustomerSingerSource
    :special-members: __init__

.. autoclass:: AzureTableSource
    :special-members: __init__

.. autoclass:: ScaffoldJavaJdbcSource
    :special-members: __init__

.. autoclass:: TidbSource
    :special-members: __init__

.. autoclass:: QualarooSource
    :special-members: __init__

.. autoclass:: YahooFinancePriceSource
    :special-members: __init__

.. autoclass:: GoogleAnalyticsV4Source
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::GoogleAnalyticsV4Source.AuthenticateViaGoogleOauth
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::GoogleAnalyticsV4Source.ServiceAccountKeyAuthentication
    :special-members: __init__

.. autoclass:: JdbcSource
    :special-members: __init__

.. autoclass:: FakerSource
    :special-members: __init__

.. autoclass:: TplcentralSource
    :special-members: __init__

.. autoclass:: ClickhouseSource
    :special-members: __init__

.. autoclass:: FreshserviceSource
    :special-members: __init__

.. autoclass:: ZenloopSource
    :special-members: __init__

.. autoclass:: OracleSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::OracleSource.ServiceName
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::OracleSource.SystemIDSID
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::OracleSource.Unencrypted
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::OracleSource.NativeNetworkEncryptionNNE
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::OracleSource.TLSEncryptedVerifyCertificate
    :special-members: __init__

.. autoclass:: KlaviyoSource
    :special-members: __init__

.. autoclass:: GoogleDirectorySource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::GoogleDirectorySource.SignInViaGoogleOAuth
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::GoogleDirectorySource.ServiceAccountKey
    :special-members: __init__

.. autoclass:: InstagramSource
    :special-members: __init__

.. autoclass:: ShortioSource
    :special-members: __init__

.. autoclass:: SquareSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::SquareSource.OauthAuthentication
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::SquareSource.APIKey
    :special-members: __init__

.. autoclass:: DelightedSource
    :special-members: __init__

.. autoclass:: AmazonSqsSource
    :special-members: __init__

.. autoclass:: YoutubeAnalyticsSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::YoutubeAnalyticsSource.AuthenticateViaOAuth20
    :special-members: __init__

.. autoclass:: ScaffoldSourcePythonSource
    :special-members: __init__

.. autoclass:: LookerSource
    :special-members: __init__

.. autoclass:: GitlabSource
    :special-members: __init__

.. autoclass:: ExchangeRatesSource
    :special-members: __init__

.. autoclass:: AmazonAdsSource
    :special-members: __init__

.. autoclass:: MixpanelSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MixpanelSource.ServiceAccount
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MixpanelSource.ProjectSecret
    :special-members: __init__

.. autoclass:: OrbitSource
    :special-members: __init__

.. autoclass:: AmazonSellerPartnerSource
    :special-members: __init__

.. autoclass:: CourierSource
    :special-members: __init__

.. autoclass:: CloseComSource
    :special-members: __init__

.. autoclass:: BingAdsSource
    :special-members: __init__

.. autoclass:: PrimetricSource
    :special-members: __init__

.. autoclass:: PivotalTrackerSource
    :special-members: __init__

.. autoclass:: ElasticsearchSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::ElasticsearchSource.None_
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::ElasticsearchSource.ApiKeySecret
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::ElasticsearchSource.UsernamePassword
    :special-members: __init__

.. autoclass:: BigquerySource
    :special-members: __init__

.. autoclass:: WoocommerceSource
    :special-members: __init__

.. autoclass:: SearchMetricsSource
    :special-members: __init__

.. autoclass:: TypeformSource
    :special-members: __init__

.. autoclass:: WebflowSource
    :special-members: __init__

.. autoclass:: FireboltSource
    :special-members: __init__

.. autoclass:: FaunaSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::FaunaSource.Disabled
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::FaunaSource.Enabled
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::FaunaSource.Collection
    :special-members: __init__

.. autoclass:: IntercomSource
    :special-members: __init__

.. autoclass:: FreshsalesSource
    :special-members: __init__

.. autoclass:: AdjustSource
    :special-members: __init__

.. autoclass:: BambooHrSource
    :special-members: __init__

.. autoclass:: GoogleAdsSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::GoogleAdsSource.GoogleCredentials
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::GoogleAdsSource.CustomGAQLQueriesEntry
    :special-members: __init__

.. autoclass:: HellobatonSource
    :special-members: __init__

.. autoclass:: SendgridSource
    :special-members: __init__

.. autoclass:: MondaySource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MondaySource.OAuth20
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MondaySource.APIToken
    :special-members: __init__

.. autoclass:: DixaSource
    :special-members: __init__

.. autoclass:: SalesforceSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::SalesforceSource.FilterSalesforceObjectsEntry
    :special-members: __init__

.. autoclass:: PipedriveSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::PipedriveSource.SignInViaPipedriveOAuth
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::PipedriveSource.APIKeyAuthentication
    :special-members: __init__

.. autoclass:: FileSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::FileSource.HTTPSPublicWeb
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::FileSource.GCSGoogleCloudStorage
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::FileSource.S3AmazonWebServices
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::FileSource.AzBlobAzureBlobStorage
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::FileSource.SSHSecureShell
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::FileSource.SCPSecureCopyProtocol
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::FileSource.SFTPSecureFileTransferProtocol
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::FileSource.LocalFilesystemLimited
    :special-members: __init__

.. autoclass:: GlassfrogSource
    :special-members: __init__

.. autoclass:: ChartmogulSource
    :special-members: __init__

.. autoclass:: OrbSource
    :special-members: __init__

.. autoclass:: CockroachdbSource
    :special-members: __init__

.. autoclass:: ConfluenceSource
    :special-members: __init__

.. autoclass:: PlaidSource
    :special-members: __init__

.. autoclass:: SnapchatMarketingSource
    :special-members: __init__

.. autoclass:: MicrosoftTeamsSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MicrosoftTeamsSource.AuthenticateViaMicrosoftOAuth20
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MicrosoftTeamsSource.AuthenticateViaMicrosoft
    :special-members: __init__

.. autoclass:: LeverHiringSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::LeverHiringSource.OAuthCredentials
    :special-members: __init__

.. autoclass:: TwilioSource
    :special-members: __init__

.. autoclass:: StripeSource
    :special-members: __init__

.. autoclass:: Db2Source
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::Db2Source.Unencrypted
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::Db2Source.TLSEncryptedVerifyCertificate
    :special-members: __init__

.. autoclass:: SlackSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::SlackSource.DefaultOAuth20Authorization
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::SlackSource.APITokenCredentials
    :special-members: __init__

.. autoclass:: RechargeSource
    :special-members: __init__

.. autoclass:: OpenweatherSource
    :special-members: __init__

.. autoclass:: RetentlySource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::RetentlySource.AuthenticateViaRetentlyOAuth
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::RetentlySource.AuthenticateWithAPIToken
    :special-members: __init__

.. autoclass:: ScaffoldSourceHttpSource
    :special-members: __init__

.. autoclass:: YandexMetricaSource
    :special-members: __init__

.. autoclass:: TalkdeskExploreSource
    :special-members: __init__

.. autoclass:: ChargifySource
    :special-members: __init__

.. autoclass:: RkiCovidSource
    :special-members: __init__

.. autoclass:: PostgresSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::PostgresSource.Disable
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::PostgresSource.Allow
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::PostgresSource.Prefer
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::PostgresSource.Require
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::PostgresSource.VerifyCa
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::PostgresSource.VerifyFull
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::PostgresSource.Standard
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::PostgresSource.LogicalReplicationCDC
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::PostgresSource.NoTunnel
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::PostgresSource.SSHKeyAuthentication
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::PostgresSource.PasswordAuthentication
    :special-members: __init__

.. autoclass:: TrelloSource
    :special-members: __init__

.. autoclass:: PrestashopSource
    :special-members: __init__

.. autoclass:: PaystackSource
    :special-members: __init__

.. autoclass:: S3Source
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::S3Source.CSV
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::S3Source.Parquet
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::S3Source.Avro
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::S3Source.Jsonl
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::S3Source.S3AmazonWebServices
    :special-members: __init__

.. autoclass:: SnowflakeSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::SnowflakeSource.OAuth20
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::SnowflakeSource.UsernameAndPassword
    :special-members: __init__

.. autoclass:: AmplitudeSource
    :special-members: __init__

.. autoclass:: PosthogSource
    :special-members: __init__

.. autoclass:: PaypalTransactionSource
    :special-members: __init__

.. autoclass:: MssqlSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MssqlSource.Unencrypted
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MssqlSource.EncryptedTrustServerCertificate
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MssqlSource.EncryptedVerifyCertificate
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MssqlSource.Standard
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MssqlSource.LogicalReplicationCDC
    :special-members: __init__

.. autoclass:: ZohoCrmSource
    :special-members: __init__

.. autoclass:: RedshiftSource
    :special-members: __init__

.. autoclass:: AsanaSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::AsanaSource.PATCredentials
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::AsanaSource.OAuthCredentials
    :special-members: __init__

.. autoclass:: SmartsheetsSource
    :special-members: __init__

.. autoclass:: MailchimpSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MailchimpSource.OAuth20
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MailchimpSource.APIKey
    :special-members: __init__

.. autoclass:: SentrySource
    :special-members: __init__

.. autoclass:: MailgunSource
    :special-members: __init__

.. autoclass:: OnesignalSource
    :special-members: __init__

.. autoclass:: PythonHttpTutorialSource
    :special-members: __init__

.. autoclass:: AirtableSource
    :special-members: __init__

.. autoclass:: MongodbV2Source
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MongodbV2Source.StandaloneMongoDbInstance
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MongodbV2Source.ReplicaSet
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MongodbV2Source.MongoDBAtlas
    :special-members: __init__

.. autoclass:: FileSecureSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::FileSecureSource.HTTPSPublicWeb
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::FileSecureSource.GCSGoogleCloudStorage
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::FileSecureSource.S3AmazonWebServices
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::FileSecureSource.AzBlobAzureBlobStorage
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::FileSecureSource.SSHSecureShell
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::FileSecureSource.SCPSecureCopyProtocol
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::FileSecureSource.SFTPSecureFileTransferProtocol
    :special-members: __init__

.. autoclass:: ZendeskSupportSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::ZendeskSupportSource.OAuth20
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::ZendeskSupportSource.APIToken
    :special-members: __init__

.. autoclass:: TempoSource
    :special-members: __init__

.. autoclass:: BraintreeSource
    :special-members: __init__

.. autoclass:: SalesloftSource
    :special-members: __init__

.. autoclass:: LinnworksSource
    :special-members: __init__

.. autoclass:: ChargebeeSource
    :special-members: __init__

.. autoclass:: GoogleAnalyticsDataApiSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::GoogleAnalyticsDataApiSource.AuthenticateViaGoogleOauth
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::GoogleAnalyticsDataApiSource.ServiceAccountKeyAuthentication
    :special-members: __init__

.. autoclass:: OutreachSource
    :special-members: __init__

.. autoclass:: LemlistSource
    :special-members: __init__

.. autoclass:: ApifyDatasetSource
    :special-members: __init__

.. autoclass:: RecurlySource
    :special-members: __init__

.. autoclass:: ZendeskTalkSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::ZendeskTalkSource.APIToken
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::ZendeskTalkSource.OAuth20
    :special-members: __init__

.. autoclass:: SftpSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::SftpSource.PasswordAuthentication
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::SftpSource.SSHKeyAuthentication
    :special-members: __init__

.. autoclass:: WhiskyHunterSource
    :special-members: __init__

.. autoclass:: FreshdeskSource
    :special-members: __init__

.. autoclass:: GocardlessSource
    :special-members: __init__

.. autoclass:: ZuoraSource
    :special-members: __init__

.. autoclass:: MarketoSource
    :special-members: __init__

.. autoclass:: DriftSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::DriftSource.OAuth20
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::DriftSource.AccessToken
    :special-members: __init__

.. autoclass:: PokeapiSource
    :special-members: __init__

.. autoclass:: NetsuiteSource
    :special-members: __init__

.. autoclass:: HubplannerSource
    :special-members: __init__

.. autoclass:: Dv360Source
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::Dv360Source.Oauth2Credentials
    :special-members: __init__

.. autoclass:: NotionSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::NotionSource.OAuth20
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::NotionSource.AccessToken
    :special-members: __init__

.. autoclass:: ZendeskSunshineSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::ZendeskSunshineSource.OAuth20
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::ZendeskSunshineSource.APIToken
    :special-members: __init__

.. autoclass:: PinterestSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::PinterestSource.OAuth20
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::PinterestSource.AccessToken
    :special-members: __init__

.. autoclass:: MetabaseSource
    :special-members: __init__

.. autoclass:: HubspotSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::HubspotSource.OAuth
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::HubspotSource.APIKey
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::HubspotSource.PrivateAPP
    :special-members: __init__

.. autoclass:: HarvestSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::HarvestSource.AuthenticateViaHarvestOAuth
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::HarvestSource.AuthenticateWithPersonalAccessToken
    :special-members: __init__

.. autoclass:: GithubSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::GithubSource.OAuthCredentials
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::GithubSource.PATCredentials
    :special-members: __init__

.. autoclass:: E2eTestSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::E2eTestSource.SingleSchema
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::E2eTestSource.MultiSchema
    :special-members: __init__

.. autoclass:: MysqlSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MysqlSource.Preferred
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MysqlSource.Required
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MysqlSource.VerifyCA
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MysqlSource.VerifyIdentity
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MysqlSource.Standard
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MysqlSource.LogicalReplicationCDC
    :special-members: __init__

.. autoclass:: MyHoursSource
    :special-members: __init__

.. autoclass:: KyribaSource
    :special-members: __init__

.. autoclass:: GoogleSearchConsoleSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::GoogleSearchConsoleSource.OAuth
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::GoogleSearchConsoleSource.ServiceAccountKeyAuthentication
    :special-members: __init__

.. autoclass:: FacebookMarketingSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::FacebookMarketingSource.InsightConfig
    :special-members: __init__

.. autoclass:: SurveymonkeySource
    :special-members: __init__

.. autoclass:: PardotSource
    :special-members: __init__

.. autoclass:: FlexportSource
    :special-members: __init__

.. autoclass:: ZenefitsSource
    :special-members: __init__

.. autoclass:: KafkaSource
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::KafkaSource.JSON
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::KafkaSource.AVRO
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::KafkaSource.ManuallyAssignAListOfPartitions
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::KafkaSource.SubscribeToAllTopicsMatchingSpecifiedPattern
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::KafkaSource.PLAINTEXT
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::KafkaSource.SASLPLAINTEXT
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::KafkaSource.SASLSSL
    :special-members: __init__


Managed Config Generated Destinations
=====================================

.. currentmodule:: dagster_airbyte.managed.generated.destinations

.. autoclass:: DynamodbDestination
    :special-members: __init__

.. autoclass:: BigqueryDestination
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::BigqueryDestination.StandardInserts
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::BigqueryDestination.HMACKey
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::BigqueryDestination.GCSStaging
    :special-members: __init__

.. autoclass:: RabbitmqDestination
    :special-members: __init__

.. autoclass:: KvdbDestination
    :special-members: __init__

.. autoclass:: ClickhouseDestination
    :special-members: __init__

.. autoclass:: AmazonSqsDestination
    :special-members: __init__

.. autoclass:: MariadbColumnstoreDestination
    :special-members: __init__

.. autoclass:: KinesisDestination
    :special-members: __init__

.. autoclass:: AzureBlobStorageDestination
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::AzureBlobStorageDestination.CSVCommaSeparatedValues
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::AzureBlobStorageDestination.JSONLinesNewlineDelimitedJSON
    :special-members: __init__

.. autoclass:: KafkaDestination
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::KafkaDestination.PLAINTEXT
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::KafkaDestination.SASLPLAINTEXT
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::KafkaDestination.SASLSSL
    :special-members: __init__

.. autoclass:: ElasticsearchDestination
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::ElasticsearchDestination.None_
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::ElasticsearchDestination.ApiKeySecret
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::ElasticsearchDestination.UsernamePassword
    :special-members: __init__

.. autoclass:: MysqlDestination
    :special-members: __init__

.. autoclass:: SftpJsonDestination
    :special-members: __init__

.. autoclass:: GcsDestination
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::GcsDestination.HMACKey
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::GcsDestination.NoCompression
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::GcsDestination.Deflate
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::GcsDestination.Bzip2
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::GcsDestination.Xz
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::GcsDestination.Zstandard
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::GcsDestination.Snappy
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::GcsDestination.AvroApacheAvro
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::GcsDestination.GZIP
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::GcsDestination.CSVCommaSeparatedValues
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::GcsDestination.JSONLinesNewlineDelimitedJSON
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::GcsDestination.ParquetColumnarStorage
    :special-members: __init__

.. autoclass:: CassandraDestination
    :special-members: __init__

.. autoclass:: FireboltDestination
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::FireboltDestination.SQLInserts
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::FireboltDestination.ExternalTableViaS3
    :special-members: __init__

.. autoclass:: GoogleSheetsDestination
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::GoogleSheetsDestination.AuthenticationViaGoogleOAuth
    :special-members: __init__

.. autoclass:: DatabricksDestination
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::DatabricksDestination.AmazonS3
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::DatabricksDestination.AzureBlobStorage
    :special-members: __init__

.. autoclass:: BigqueryDenormalizedDestination
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::BigqueryDenormalizedDestination.StandardInserts
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::BigqueryDenormalizedDestination.HMACKey
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::BigqueryDenormalizedDestination.GCSStaging
    :special-members: __init__

.. autoclass:: SqliteDestination
    :special-members: __init__

.. autoclass:: MongodbDestination
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::MongodbDestination.StandaloneMongoDbInstance
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::MongodbDestination.ReplicaSet
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::MongodbDestination.MongoDBAtlas
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::MongodbDestination.None_
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::MongodbDestination.LoginPassword
    :special-members: __init__

.. autoclass:: RocksetDestination
    :special-members: __init__

.. autoclass:: OracleDestination
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::OracleDestination.Unencrypted
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::OracleDestination.NativeNetworkEncryptionNNE
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::OracleDestination.TLSEncryptedVerifyCertificate
    :special-members: __init__

.. autoclass:: CsvDestination
    :special-members: __init__

.. autoclass:: S3Destination
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::S3Destination.NoCompression
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::S3Destination.Deflate
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::S3Destination.Bzip2
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::S3Destination.Xz
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::S3Destination.Zstandard
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::S3Destination.Snappy
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::S3Destination.AvroApacheAvro
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::S3Destination.GZIP
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::S3Destination.CSVCommaSeparatedValues
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::S3Destination.JSONLinesNewlineDelimitedJSON
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::S3Destination.ParquetColumnarStorage
    :special-members: __init__

.. autoclass:: AwsDatalakeDestination
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::AwsDatalakeDestination.IAMRole
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::AwsDatalakeDestination.IAMUser
    :special-members: __init__

.. autoclass:: MssqlDestination
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::MssqlDestination.Unencrypted
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::MssqlDestination.EncryptedTrustServerCertificate
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::MssqlDestination.EncryptedVerifyCertificate
    :special-members: __init__

.. autoclass:: PubsubDestination
    :special-members: __init__

.. autoclass:: R2Destination
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::R2Destination.NoCompression
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::R2Destination.Deflate
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::R2Destination.Bzip2
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::R2Destination.Xz
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::R2Destination.Zstandard
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::R2Destination.Snappy
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::R2Destination.AvroApacheAvro
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::R2Destination.GZIP
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::R2Destination.CSVCommaSeparatedValues
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::R2Destination.JSONLinesNewlineDelimitedJSON
    :special-members: __init__

.. autoclass:: JdbcDestination
    :special-members: __init__

.. autoclass:: KeenDestination
    :special-members: __init__

.. autoclass:: TidbDestination
    :special-members: __init__

.. autoclass:: FirestoreDestination
    :special-members: __init__

.. autoclass:: ScyllaDestination
    :special-members: __init__

.. autoclass:: RedisDestination
    :special-members: __init__

.. autoclass:: MqttDestination
    :special-members: __init__

.. autoclass:: RedshiftDestination
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::RedshiftDestination.Standard
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::RedshiftDestination.NoEncryption
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::RedshiftDestination.AESCBCEnvelopeEncryption
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::RedshiftDestination.S3Staging
    :special-members: __init__

.. autoclass:: PulsarDestination
    :special-members: __init__

.. autoclass:: SnowflakeDestination
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::SnowflakeDestination.OAuth20
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::SnowflakeDestination.KeyPairAuthentication
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::SnowflakeDestination.UsernameAndPassword
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::SnowflakeDestination.SelectAnotherOption
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::SnowflakeDestination.RecommendedInternalStaging
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::SnowflakeDestination.NoEncryption
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::SnowflakeDestination.AESCBCEnvelopeEncryption
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::SnowflakeDestination.AWSS3Staging
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::SnowflakeDestination.GoogleCloudStorageStaging
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::SnowflakeDestination.AzureBlobStorageStaging
    :special-members: __init__

.. autoclass:: PostgresDestination
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::PostgresDestination.Disable
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::PostgresDestination.Allow
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::PostgresDestination.Prefer
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::PostgresDestination.Require
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::PostgresDestination.VerifyCa
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::PostgresDestination.VerifyFull
    :special-members: __init__

.. autoclass:: ScaffoldDestinationPythonDestination
    :special-members: __init__

.. autoclass:: LocalJsonDestination
    :special-members: __init__

.. autoclass:: MeilisearchDestination
    :special-members: __init__


Legacy
=========
.. currentmodule:: dagster_airbyte
    
.. autoconfigurable:: airbyte_resource
    :annotation: ResourceDefinition