Airbyte (dagster-airbyte)
---------------------------

This library provides a Dagster integration with `Airbyte <https://www.airbyte.com/>`_.

For more information on getting started, see the `Airbyte integration guide </integrations/airbyte>`_.

.. currentmodule:: dagster_airbyte

Ops
===

.. autoconfigurable:: airbyte_sync_op

Resources
=========

.. autoconfigurable:: airbyte_resource
    :annotation: ResourceDefinition

.. autoclass:: AirbyteResource
    :members:

Assets
======

.. autofunction:: load_assets_from_airbyte_instance

.. autofunction:: load_assets_from_airbyte_project

.. autofunction:: build_airbyte_assets

Managed Config
==============

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
    :members:
    :special-members: __init__

.. autoclass:: AppsflyerSource
    :members:
    :special-members: __init__

.. autoclass:: GoogleWorkspaceAdminReportsSource
    :members:
    :special-members: __init__

.. autoclass:: CartSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::CartSource.CentralAPIRouter
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::CartSource.SingleStoreAccessToken
    :members:
    :special-members: __init__

.. autoclass:: LinkedinAdsSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::LinkedinAdsSource.OAuth20
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::LinkedinAdsSource.AccessToken
    :members:
    :special-members: __init__

.. autoclass:: MongodbSource
    :members:
    :special-members: __init__

.. autoclass:: TimelySource
    :members:
    :special-members: __init__
 
.. autoclass:: StockTickerApiTutorialSource
    :members:
    :special-members: __init__

.. autoclass:: WrikeSource
    :members:
    :special-members: __init__

.. autoclass:: CommercetoolsSource
    :members:
    :special-members: __init__

.. autoclass:: GutendexSource
    :members:
    :special-members: __init__

.. autoclass:: IterableSource
    :members:
    :special-members: __init__

.. autoclass:: QuickbooksSingerSource
    :members:
    :special-members: __init__

.. autoclass:: BigcommerceSource
    :members:
    :special-members: __init__

.. autoclass:: ShopifySource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::ShopifySource.APIPassword
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::ShopifySource.OAuth20
    :members:
    :special-members: __init__

.. autoclass:: AppstoreSingerSource
    :members:
    :special-members: __init__

.. autoclass:: GreenhouseSource
    :members:
    :special-members: __init__

.. autoclass:: ZoomSingerSource
    :members:
    :special-members: __init__

.. autoclass:: TiktokMarketingSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::TiktokMarketingSource.OAuth20
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::TiktokMarketingSource.SandboxAccessToken
    :members:
    :special-members: __init__

.. autoclass:: ZendeskChatSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::ZendeskChatSource.OAuth20
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::ZendeskChatSource.AccessToken
    :members:
    :special-members: __init__

.. autoclass:: AwsCloudtrailSource
    :members:
    :special-members: __init__

.. autoclass:: OktaSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::OktaSource.OAuth20
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::OktaSource.APIToken
    :members:
    :special-members: __init__

.. autoclass:: InsightlySource
    :members:
    :special-members: __init__

.. autoclass:: LinkedinPagesSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::LinkedinPagesSource.OAuth20
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::LinkedinPagesSource.AccessToken
    :members:
    :special-members: __init__

.. autoclass:: PersistiqSource
    :members:
    :special-members: __init__

.. autoclass:: FreshcallerSource
    :members:
    :special-members: __init__

.. autoclass:: AppfollowSource
    :members:
    :special-members: __init__

.. autoclass:: FacebookPagesSource
    :members:
    :special-members: __init__

.. autoclass:: JiraSource
    :members:
    :special-members: __init__

.. autoclass:: GoogleSheetsSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::GoogleSheetsSource.AuthenticateViaGoogleOAuth
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::GoogleSheetsSource.ServiceAccountKeyAuthentication
    :members:
    :special-members: __init__

.. autoclass:: DockerhubSource
    :members:
    :special-members: __init__

.. autoclass:: UsCensusSource
    :members:
    :special-members: __init__

.. autoclass:: KustomerSingerSource
    :members:
    :special-members: __init__

.. autoclass:: AzureTableSource
    :members:
    :special-members: __init__

.. autoclass:: ScaffoldJavaJdbcSource
    :members:
    :special-members: __init__

.. autoclass:: TidbSource
    :members:
    :special-members: __init__

.. autoclass:: QualarooSource
    :members:
    :special-members: __init__

.. autoclass:: YahooFinancePriceSource
    :members:
    :special-members: __init__

.. autoclass:: GoogleAnalyticsV4Source
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::GoogleAnalyticsV4Source.AuthenticateViaGoogleOauth
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::GoogleAnalyticsV4Source.ServiceAccountKeyAuthentication
    :members:
    :special-members: __init__

.. autoclass:: JdbcSource
    :members:
    :special-members: __init__

.. autoclass:: FakerSource
    :members:
    :special-members: __init__

.. autoclass:: TplcentralSource
    :members:
    :special-members: __init__

.. autoclass:: ClickhouseSource
    :members:
    :special-members: __init__

.. autoclass:: FreshserviceSource
    :members:
    :special-members: __init__

.. autoclass:: ZenloopSource
    :members:
    :special-members: __init__

.. autoclass:: OracleSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::OracleSource.ServiceName
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::OracleSource.SystemIDSID
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::OracleSource.Unencrypted
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::OracleSource.NativeNetworkEncryptionNNE
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::OracleSource.TLSEncryptedVerifyCertificate
    :members:
    :special-members: __init__

.. autoclass:: KlaviyoSource
    :members:
    :special-members: __init__

.. autoclass:: GoogleDirectorySource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::GoogleDirectorySource.SignInViaGoogleOAuth
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::GoogleDirectorySource.ServiceAccountKey
    :members:
    :special-members: __init__

.. autoclass:: InstagramSource
    :members:
    :special-members: __init__

.. autoclass:: ShortioSource
    :members:
    :special-members: __init__

.. autoclass:: SquareSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::SquareSource.OauthAuthentication
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::SquareSource.APIKey
    :members:
    :special-members: __init__

.. autoclass:: DelightedSource
    :members:
    :special-members: __init__

.. autoclass:: AmazonSqsSource
    :members:
    :special-members: __init__

.. autoclass:: YoutubeAnalyticsSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::YoutubeAnalyticsSource.AuthenticateViaOAuth20
    :members:
    :special-members: __init__

.. autoclass:: ScaffoldSourcePythonSource
    :members:
    :special-members: __init__

.. autoclass:: LookerSource
    :members:
    :special-members: __init__

.. autoclass:: GitlabSource
    :members:
    :special-members: __init__

.. autoclass:: ExchangeRatesSource
    :members:
    :special-members: __init__

.. autoclass:: AmazonAdsSource
    :members:
    :special-members: __init__

.. autoclass:: MixpanelSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MixpanelSource.ServiceAccount
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MixpanelSource.ProjectSecret
    :members:
    :special-members: __init__

.. autoclass:: OrbitSource
    :members:
    :special-members: __init__

.. autoclass:: AmazonSellerPartnerSource
    :members:
    :special-members: __init__

.. autoclass:: CourierSource
    :members:
    :special-members: __init__

.. autoclass:: CloseComSource
    :members:
    :special-members: __init__

.. autoclass:: BingAdsSource
    :members:
    :special-members: __init__

.. autoclass:: PrimetricSource
    :members:
    :special-members: __init__

.. autoclass:: PivotalTrackerSource
    :members:
    :special-members: __init__

.. autoclass:: ElasticsearchSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::ElasticsearchSource.None_
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::ElasticsearchSource.ApiKeySecret
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::ElasticsearchSource.UsernamePassword
    :members:
    :special-members: __init__

.. autoclass:: BigquerySource
    :members:
    :special-members: __init__

.. autoclass:: WoocommerceSource
    :members:
    :special-members: __init__

.. autoclass:: SearchMetricsSource
    :members:
    :special-members: __init__

.. autoclass:: TypeformSource
    :members:
    :special-members: __init__

.. autoclass:: WebflowSource
    :members:
    :special-members: __init__

.. autoclass:: FireboltSource
    :members:
    :special-members: __init__

.. autoclass:: FaunaSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::FaunaSource.Disabled
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::FaunaSource.Enabled
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::FaunaSource.Collection
    :members:
    :special-members: __init__

.. autoclass:: IntercomSource
    :members:
    :special-members: __init__

.. autoclass:: FreshsalesSource
    :members:
    :special-members: __init__

.. autoclass:: AdjustSource
    :members:
    :special-members: __init__

.. autoclass:: BambooHrSource
    :members:
    :special-members: __init__

.. autoclass:: GoogleAdsSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::GoogleAdsSource.GoogleCredentials
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::GoogleAdsSource.CustomGAQLQueriesEntry
    :members:
    :special-members: __init__

.. autoclass:: HellobatonSource
    :members:
    :special-members: __init__

.. autoclass:: SendgridSource
    :members:
    :special-members: __init__

.. autoclass:: MondaySource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MondaySource.OAuth20
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MondaySource.APIToken
    :members:
    :special-members: __init__

.. autoclass:: DixaSource
    :members:
    :special-members: __init__

.. autoclass:: SalesforceSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::SalesforceSource.FilterSalesforceObjectsEntry
    :members:
    :special-members: __init__

.. autoclass:: PipedriveSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::PipedriveSource.SignInViaPipedriveOAuth
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::PipedriveSource.APIKeyAuthentication
    :members:
    :special-members: __init__

.. autoclass:: FileSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::FileSource.HTTPSPublicWeb
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::FileSource.GCSGoogleCloudStorage
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::FileSource.S3AmazonWebServices
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::FileSource.AzBlobAzureBlobStorage
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::FileSource.SSHSecureShell
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::FileSource.SCPSecureCopyProtocol
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::FileSource.SFTPSecureFileTransferProtocol
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::FileSource.LocalFilesystemLimited
    :members:
    :special-members: __init__

.. autoclass:: GlassfrogSource
    :members:
    :special-members: __init__

.. autoclass:: ChartmogulSource
    :members:
    :special-members: __init__

.. autoclass:: OrbSource
    :members:
    :special-members: __init__

.. autoclass:: CockroachdbSource
    :members:
    :special-members: __init__

.. autoclass:: ConfluenceSource
    :members:
    :special-members: __init__

.. autoclass:: PlaidSource
    :members:
    :special-members: __init__

.. autoclass:: SnapchatMarketingSource
    :members:
    :special-members: __init__

.. autoclass:: MicrosoftTeamsSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MicrosoftTeamsSource.AuthenticateViaMicrosoftOAuth20
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MicrosoftTeamsSource.AuthenticateViaMicrosoft
    :members:
    :special-members: __init__

.. autoclass:: LeverHiringSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::LeverHiringSource.OAuthCredentials
    :members:
    :special-members: __init__

.. autoclass:: TwilioSource
    :members:
    :special-members: __init__

.. autoclass:: StripeSource
    :members:
    :special-members: __init__

.. autoclass:: Db2Source
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::Db2Source.Unencrypted
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::Db2Source.TLSEncryptedVerifyCertificate
    :members:
    :special-members: __init__

.. autoclass:: SlackSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::SlackSource.DefaultOAuth20Authorization
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::SlackSource.APITokenCredentials
    :members:
    :special-members: __init__

.. autoclass:: RechargeSource
    :members:
    :special-members: __init__

.. autoclass:: OpenweatherSource
    :members:
    :special-members: __init__

.. autoclass:: RetentlySource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::RetentlySource.AuthenticateViaRetentlyOAuth
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::RetentlySource.AuthenticateWithAPIToken
    :members:
    :special-members: __init__

.. autoclass:: ScaffoldSourceHttpSource
    :members:
    :special-members: __init__

.. autoclass:: YandexMetricaSource
    :members:
    :special-members: __init__

.. autoclass:: TalkdeskExploreSource
    :members:
    :special-members: __init__

.. autoclass:: ChargifySource
    :members:
    :special-members: __init__

.. autoclass:: RkiCovidSource
    :members:
    :special-members: __init__

.. autoclass:: PostgresSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::PostgresSource.Disable
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::PostgresSource.Allow
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::PostgresSource.Prefer
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::PostgresSource.Require
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::PostgresSource.VerifyCa
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::PostgresSource.VerifyFull
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::PostgresSource.Standard
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::PostgresSource.LogicalReplicationCDC
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::PostgresSource.NoTunnel
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::PostgresSource.SSHKeyAuthentication
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::PostgresSource.PasswordAuthentication
    :members:
    :special-members: __init__

.. autoclass:: TrelloSource
    :members:
    :special-members: __init__

.. autoclass:: PrestashopSource
    :members:
    :special-members: __init__

.. autoclass:: PaystackSource
    :members:
    :special-members: __init__

.. autoclass:: S3Source
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::S3Source.CSV
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::S3Source.Parquet
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::S3Source.Avro
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::S3Source.Jsonl
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::S3Source.S3AmazonWebServices
    :members:
    :special-members: __init__

.. autoclass:: SnowflakeSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::SnowflakeSource.OAuth20
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::SnowflakeSource.UsernameAndPassword
    :members:
    :special-members: __init__

.. autoclass:: AmplitudeSource
    :members:
    :special-members: __init__

.. autoclass:: PosthogSource
    :members:
    :special-members: __init__

.. autoclass:: PaypalTransactionSource
    :members:
    :special-members: __init__

.. autoclass:: MssqlSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MssqlSource.Unencrypted
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MssqlSource.EncryptedTrustServerCertificate
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MssqlSource.EncryptedVerifyCertificate
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MssqlSource.Standard
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MssqlSource.LogicalReplicationCDC
    :members:
    :special-members: __init__

.. autoclass:: ZohoCrmSource
    :members:
    :special-members: __init__

.. autoclass:: RedshiftSource
    :members:
    :special-members: __init__

.. autoclass:: AsanaSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::AsanaSource.PATCredentials
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::AsanaSource.OAuthCredentials
    :members:
    :special-members: __init__

.. autoclass:: SmartsheetsSource
    :members:
    :special-members: __init__

.. autoclass:: MailchimpSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MailchimpSource.OAuth20
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MailchimpSource.APIKey
    :members:
    :special-members: __init__

.. autoclass:: SentrySource
    :members:
    :special-members: __init__

.. autoclass:: MailgunSource
    :members:
    :special-members: __init__

.. autoclass:: OnesignalSource
    :members:
    :special-members: __init__

.. autoclass:: PythonHttpTutorialSource
    :members:
    :special-members: __init__

.. autoclass:: AirtableSource
    :members:
    :special-members: __init__

.. autoclass:: MongodbV2Source
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MongodbV2Source.StandaloneMongoDbInstance
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MongodbV2Source.ReplicaSet
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MongodbV2Source.MongoDBAtlas
    :members:
    :special-members: __init__

.. autoclass:: FileSecureSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::FileSecureSource.HTTPSPublicWeb
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::FileSecureSource.GCSGoogleCloudStorage
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::FileSecureSource.S3AmazonWebServices
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::FileSecureSource.AzBlobAzureBlobStorage
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::FileSecureSource.SSHSecureShell
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::FileSecureSource.SCPSecureCopyProtocol
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::FileSecureSource.SFTPSecureFileTransferProtocol
    :members:
    :special-members: __init__

.. autoclass:: ZendeskSupportSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::ZendeskSupportSource.OAuth20
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::ZendeskSupportSource.APIToken
    :members:
    :special-members: __init__

.. autoclass:: TempoSource
    :members:
    :special-members: __init__

.. autoclass:: BraintreeSource
    :members:
    :special-members: __init__

.. autoclass:: SalesloftSource
    :members:
    :special-members: __init__

.. autoclass:: LinnworksSource
    :members:
    :special-members: __init__

.. autoclass:: ChargebeeSource
    :members:
    :special-members: __init__

.. autoclass:: GoogleAnalyticsDataApiSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::GoogleAnalyticsDataApiSource.AuthenticateViaGoogleOauth
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::GoogleAnalyticsDataApiSource.ServiceAccountKeyAuthentication
    :members:
    :special-members: __init__

.. autoclass:: OutreachSource
    :members:
    :special-members: __init__

.. autoclass:: LemlistSource
    :members:
    :special-members: __init__

.. autoclass:: ApifyDatasetSource
    :members:
    :special-members: __init__

.. autoclass:: RecurlySource
    :members:
    :special-members: __init__

.. autoclass:: ZendeskTalkSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::ZendeskTalkSource.APIToken
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::ZendeskTalkSource.OAuth20
    :members:
    :special-members: __init__

.. autoclass:: SftpSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::SftpSource.PasswordAuthentication
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::SftpSource.SSHKeyAuthentication
    :members:
    :special-members: __init__

.. autoclass:: WhiskyHunterSource
    :members:
    :special-members: __init__

.. autoclass:: FreshdeskSource
    :members:
    :special-members: __init__

.. autoclass:: GocardlessSource
    :members:
    :special-members: __init__

.. autoclass:: ZuoraSource
    :members:
    :special-members: __init__

.. autoclass:: MarketoSource
    :members:
    :special-members: __init__

.. autoclass:: DriftSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::DriftSource.OAuth20
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::DriftSource.AccessToken
    :members:
    :special-members: __init__

.. autoclass:: PokeapiSource
    :members:
    :special-members: __init__

.. autoclass:: NetsuiteSource
    :members:
    :special-members: __init__

.. autoclass:: HubplannerSource
    :members:
    :special-members: __init__

.. autoclass:: Dv360Source
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::Dv360Source.Oauth2Credentials
    :members:
    :special-members: __init__

.. autoclass:: NotionSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::NotionSource.OAuth20
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::NotionSource.AccessToken
    :members:
    :special-members: __init__

.. autoclass:: ZendeskSunshineSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::ZendeskSunshineSource.OAuth20
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::ZendeskSunshineSource.APIToken
    :members:
    :special-members: __init__

.. autoclass:: PinterestSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::PinterestSource.OAuth20
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::PinterestSource.AccessToken
    :members:
    :special-members: __init__

.. autoclass:: MetabaseSource
    :members:
    :special-members: __init__

.. autoclass:: HubspotSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::HubspotSource.OAuth
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::HubspotSource.APIKey
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::HubspotSource.PrivateAPP
    :members:
    :special-members: __init__

.. autoclass:: HarvestSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::HarvestSource.AuthenticateViaHarvestOAuth
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::HarvestSource.AuthenticateWithPersonalAccessToken
    :members:
    :special-members: __init__

.. autoclass:: GithubSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::GithubSource.OAuthCredentials
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::GithubSource.PATCredentials
    :members:
    :special-members: __init__

.. autoclass:: E2eTestSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::E2eTestSource.SingleSchema
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::E2eTestSource.MultiSchema
    :members:
    :special-members: __init__

.. autoclass:: MysqlSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MysqlSource.Preferred
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MysqlSource.Required
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MysqlSource.VerifyCA
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MysqlSource.VerifyIdentity
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MysqlSource.Standard
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::MysqlSource.LogicalReplicationCDC
    :members:
    :special-members: __init__

.. autoclass:: MyHoursSource
    :members:
    :special-members: __init__

.. autoclass:: KyribaSource
    :members:
    :special-members: __init__

.. autoclass:: GoogleSearchConsoleSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::GoogleSearchConsoleSource.OAuth
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::GoogleSearchConsoleSource.ServiceAccountKeyAuthentication
    :members:
    :special-members: __init__

.. autoclass:: FacebookMarketingSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::FacebookMarketingSource.InsightConfig
    :members:
    :special-members: __init__

.. autoclass:: SurveymonkeySource
    :members:
    :special-members: __init__

.. autoclass:: PardotSource
    :members:
    :special-members: __init__

.. autoclass:: FlexportSource
    :members:
    :special-members: __init__

.. autoclass:: ZenefitsSource
    :members:
    :special-members: __init__

.. autoclass:: KafkaSource
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::KafkaSource.JSON
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::KafkaSource.AVRO
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::KafkaSource.ManuallyAssignAListOfPartitions
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::KafkaSource.SubscribeToAllTopicsMatchingSpecifiedPattern
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::KafkaSource.PLAINTEXT
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::KafkaSource.SASLPLAINTEXT
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.sources::KafkaSource.SASLSSL
    :members:
    :special-members: __init__


Managed Config Generated Destinations
=====================================

.. currentmodule:: dagster_airbyte.managed.generated.destinations
    
.. autoclass:: DynamodbDestination
    :members:
    :special-members: __init__

.. autoclass:: BigqueryDestination
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::BigqueryDestination.StandardInserts
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::BigqueryDestination.HMACKey
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::BigqueryDestination.GCSStaging
    :members:
    :special-members: __init__

.. autoclass:: RabbitmqDestination
    :members:
    :special-members: __init__

.. autoclass:: KvdbDestination
    :members:
    :special-members: __init__

.. autoclass:: ClickhouseDestination
    :members:
    :special-members: __init__

.. autoclass:: AmazonSqsDestination
    :members:
    :special-members: __init__

.. autoclass:: MariadbColumnstoreDestination
    :members:
    :special-members: __init__

.. autoclass:: KinesisDestination
    :members:
    :special-members: __init__

.. autoclass:: AzureBlobStorageDestination
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::AzureBlobStorageDestination.CSVCommaSeparatedValues
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::AzureBlobStorageDestination.JSONLinesNewlineDelimitedJSON
    :members:
    :special-members: __init__

.. autoclass:: KafkaDestination
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::KafkaDestination.PLAINTEXT
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::KafkaDestination.SASLPLAINTEXT
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::KafkaDestination.SASLSSL
    :members:
    :special-members: __init__

.. autoclass:: ElasticsearchDestination
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::ElasticsearchDestination.None_
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::ElasticsearchDestination.ApiKeySecret
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::ElasticsearchDestination.UsernamePassword
    :members:
    :special-members: __init__

.. autoclass:: MysqlDestination
    :members:
    :special-members: __init__

.. autoclass:: SftpJsonDestination
    :members:
    :special-members: __init__

.. autoclass:: GcsDestination
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::GcsDestination.HMACKey
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::GcsDestination.NoCompression
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::GcsDestination.Deflate
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::GcsDestination.Bzip2
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::GcsDestination.Xz
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::GcsDestination.Zstandard
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::GcsDestination.Snappy
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::GcsDestination.AvroApacheAvro
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::GcsDestination.GZIP
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::GcsDestination.CSVCommaSeparatedValues
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::GcsDestination.JSONLinesNewlineDelimitedJSON
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::GcsDestination.ParquetColumnarStorage
    :members:
    :special-members: __init__

.. autoclass:: CassandraDestination
    :members:
    :special-members: __init__

.. autoclass:: FireboltDestination
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::FireboltDestination.SQLInserts
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::FireboltDestination.ExternalTableViaS3
    :members:
    :special-members: __init__

.. autoclass:: GoogleSheetsDestination
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::GoogleSheetsDestination.AuthenticationViaGoogleOAuth
    :members:
    :special-members: __init__

.. autoclass:: DatabricksDestination
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::DatabricksDestination.AmazonS3
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::DatabricksDestination.AzureBlobStorage
    :members:
    :special-members: __init__

.. autoclass:: BigqueryDenormalizedDestination
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::BigqueryDenormalizedDestination.StandardInserts
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::BigqueryDenormalizedDestination.HMACKey
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::BigqueryDenormalizedDestination.GCSStaging
    :members:
    :special-members: __init__

.. autoclass:: SqliteDestination
    :members:
    :special-members: __init__

.. autoclass:: MongodbDestination
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::MongodbDestination.StandaloneMongoDbInstance
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::MongodbDestination.ReplicaSet
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::MongodbDestination.MongoDBAtlas
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::MongodbDestination.None_
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::MongodbDestination.LoginPassword
    :members:
    :special-members: __init__

.. autoclass:: RocksetDestination
    :members:
    :special-members: __init__

.. autoclass:: OracleDestination
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::OracleDestination.Unencrypted
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::OracleDestination.NativeNetworkEncryptionNNE
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::OracleDestination.TLSEncryptedVerifyCertificate
    :members:
    :special-members: __init__

.. autoclass:: CsvDestination
    :members:
    :special-members: __init__

.. autoclass:: S3Destination
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::S3Destination.NoCompression
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::S3Destination.Deflate
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::S3Destination.Bzip2
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::S3Destination.Xz
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::S3Destination.Zstandard
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::S3Destination.Snappy
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::S3Destination.AvroApacheAvro
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::S3Destination.GZIP
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::S3Destination.CSVCommaSeparatedValues
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::S3Destination.JSONLinesNewlineDelimitedJSON
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::S3Destination.ParquetColumnarStorage
    :members:
    :special-members: __init__

.. autoclass:: AwsDatalakeDestination
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::AwsDatalakeDestination.IAMRole
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::AwsDatalakeDestination.IAMUser
    :members:
    :special-members: __init__

.. autoclass:: MssqlDestination
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::MssqlDestination.Unencrypted
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::MssqlDestination.EncryptedTrustServerCertificate
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::MssqlDestination.EncryptedVerifyCertificate
    :members:
    :special-members: __init__

.. autoclass:: PubsubDestination
    :members:
    :special-members: __init__

.. autoclass:: R2Destination
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::R2Destination.NoCompression
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::R2Destination.Deflate
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::R2Destination.Bzip2
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::R2Destination.Xz
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::R2Destination.Zstandard
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::R2Destination.Snappy
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::R2Destination.AvroApacheAvro
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::R2Destination.GZIP
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::R2Destination.CSVCommaSeparatedValues
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::R2Destination.JSONLinesNewlineDelimitedJSON
    :members:
    :special-members: __init__

.. autoclass:: JdbcDestination
    :members:
    :special-members: __init__

.. autoclass:: KeenDestination
    :members:
    :special-members: __init__

.. autoclass:: TidbDestination
    :members:
    :special-members: __init__

.. autoclass:: FirestoreDestination
    :members:
    :special-members: __init__

.. autoclass:: ScyllaDestination
    :members:
    :special-members: __init__

.. autoclass:: RedisDestination
    :members:
    :special-members: __init__

.. autoclass:: MqttDestination
    :members:
    :special-members: __init__

.. autoclass:: RedshiftDestination
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::RedshiftDestination.Standard
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::RedshiftDestination.NoEncryption
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::RedshiftDestination.AESCBCEnvelopeEncryption
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::RedshiftDestination.S3Staging
    :members:
    :special-members: __init__

.. autoclass:: PulsarDestination
    :members:
    :special-members: __init__

.. autoclass:: SnowflakeDestination
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::SnowflakeDestination.OAuth20
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::SnowflakeDestination.KeyPairAuthentication
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::SnowflakeDestination.UsernameAndPassword
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::SnowflakeDestination.SelectAnotherOption
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::SnowflakeDestination.RecommendedInternalStaging
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::SnowflakeDestination.NoEncryption
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::SnowflakeDestination.AESCBCEnvelopeEncryption
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::SnowflakeDestination.AWSS3Staging
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::SnowflakeDestination.GoogleCloudStorageStaging
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::SnowflakeDestination.AzureBlobStorageStaging
    :members:
    :special-members: __init__

.. autoclass:: PostgresDestination
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::PostgresDestination.Disable
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::PostgresDestination.Allow
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::PostgresDestination.Prefer
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::PostgresDestination.Require
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::PostgresDestination.VerifyCa
    :members:
    :special-members: __init__

.. autoclass:: dagster_airbyte.managed.generated.destinations::PostgresDestination.VerifyFull
    :members:
    :special-members: __init__

.. autoclass:: ScaffoldDestinationPythonDestination
    :members:
    :special-members: __init__

.. autoclass:: LocalJsonDestination
    :members:
    :special-members: __init__

.. autoclass:: MeilisearchDestination
    :members:
    :special-members: __init__

