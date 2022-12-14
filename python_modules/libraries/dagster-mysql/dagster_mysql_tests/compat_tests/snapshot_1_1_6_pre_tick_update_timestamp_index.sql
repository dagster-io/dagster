-- MySQL dump 10.13  Distrib 8.0.30, for macos12.4 (x86_64)
--
-- Host: localhost    Database: test
-- ------------------------------------------------------
-- Server version	8.0.30

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `alembic_version`
--

DROP TABLE IF EXISTS `alembic_version`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `alembic_version`
--

LOCK TABLES `alembic_version` WRITE;
/*!40000 ALTER TABLE `alembic_version` DISABLE KEYS */;
INSERT INTO `alembic_version` VALUES ('6df03f4b1efb');
/*!40000 ALTER TABLE `alembic_version` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `asset_event_tags`
--

DROP TABLE IF EXISTS `asset_event_tags`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `asset_event_tags` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `event_id` int DEFAULT NULL,
  `asset_key` text NOT NULL,
  `key` text NOT NULL,
  `value` text,
  `event_timestamp` timestamp(6) NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_asset_event_tags_event_id` (`event_id`),
  KEY `idx_asset_event_tags` (`asset_key`(64),`key`(64),`value`(64)),
  CONSTRAINT `asset_event_tags_ibfk_1` FOREIGN KEY (`event_id`) REFERENCES `event_logs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `asset_event_tags`
--

LOCK TABLES `asset_event_tags` WRITE;
/*!40000 ALTER TABLE `asset_event_tags` DISABLE KEYS */;
/*!40000 ALTER TABLE `asset_event_tags` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `asset_keys`
--

DROP TABLE IF EXISTS `asset_keys`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `asset_keys` (
  `id` int NOT NULL AUTO_INCREMENT,
  `asset_key` varchar(512) DEFAULT NULL,
  `last_materialization` text,
  `last_run_id` varchar(255) DEFAULT NULL,
  `asset_details` text,
  `wipe_timestamp` timestamp(6) NULL DEFAULT NULL,
  `last_materialization_timestamp` timestamp(6) NULL DEFAULT NULL,
  `tags` text,
  `create_timestamp` datetime(6) DEFAULT CURRENT_TIMESTAMP(6),
  `cached_status_data` text,
  PRIMARY KEY (`id`),
  UNIQUE KEY `asset_key` (`asset_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `asset_keys`
--

LOCK TABLES `asset_keys` WRITE;
/*!40000 ALTER TABLE `asset_keys` DISABLE KEYS */;
/*!40000 ALTER TABLE `asset_keys` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bulk_actions`
--

DROP TABLE IF EXISTS `bulk_actions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bulk_actions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `key` varchar(32) NOT NULL,
  `status` varchar(255) NOT NULL,
  `timestamp` timestamp(6) NOT NULL,
  `body` text,
  `action_type` varchar(32) DEFAULT NULL,
  `selector_id` text,
  PRIMARY KEY (`id`),
  UNIQUE KEY `key` (`key`),
  KEY `idx_bulk_actions` (`key`),
  KEY `idx_bulk_actions_action_type` (`action_type`),
  KEY `idx_bulk_actions_status` (`status`(32)),
  KEY `idx_bulk_actions_selector_id` (`selector_id`(64))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bulk_actions`
--

LOCK TABLES `bulk_actions` WRITE;
/*!40000 ALTER TABLE `bulk_actions` DISABLE KEYS */;
/*!40000 ALTER TABLE `bulk_actions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `daemon_heartbeats`
--

DROP TABLE IF EXISTS `daemon_heartbeats`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `daemon_heartbeats` (
  `daemon_type` varchar(255) NOT NULL,
  `daemon_id` varchar(255) DEFAULT NULL,
  `timestamp` timestamp(6) NOT NULL,
  `body` text,
  UNIQUE KEY `daemon_type` (`daemon_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `daemon_heartbeats`
--

LOCK TABLES `daemon_heartbeats` WRITE;
/*!40000 ALTER TABLE `daemon_heartbeats` DISABLE KEYS */;
INSERT INTO `daemon_heartbeats` VALUES ('BACKFILL','db624095-04b7-44f8-863a-3b9e5af7c527','2022-12-15 07:26:51.097595','{\"__class__\": \"DaemonHeartbeat\", \"daemon_id\": \"db624095-04b7-44f8-863a-3b9e5af7c527\", \"daemon_type\": \"BACKFILL\", \"errors\": [], \"timestamp\": 1671060411.097595}'),('SCHEDULER','db624095-04b7-44f8-863a-3b9e5af7c527','2022-12-15 07:27:00.004716','{\"__class__\": \"DaemonHeartbeat\", \"daemon_id\": \"db624095-04b7-44f8-863a-3b9e5af7c527\", \"daemon_type\": \"SCHEDULER\", \"errors\": [], \"timestamp\": 1671060420.004716}'),('SENSOR','db624095-04b7-44f8-863a-3b9e5af7c527','2022-12-15 07:26:55.332848','{\"__class__\": \"DaemonHeartbeat\", \"daemon_id\": \"db624095-04b7-44f8-863a-3b9e5af7c527\", \"daemon_type\": \"SENSOR\", \"errors\": [], \"timestamp\": 1671060415.332848}');
/*!40000 ALTER TABLE `daemon_heartbeats` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `event_logs`
--

DROP TABLE IF EXISTS `event_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `event_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `run_id` varchar(255) DEFAULT NULL,
  `event` text NOT NULL,
  `dagster_event_type` text,
  `timestamp` timestamp(6) NULL DEFAULT NULL,
  `step_key` text,
  `asset_key` text,
  `partition` text,
  PRIMARY KEY (`id`),
  KEY `idx_step_key` (`step_key`(32)),
  KEY `idx_events_by_asset_partition` (`asset_key`(64),`dagster_event_type`(64),`partition`(64),`id`),
  KEY `idx_events_by_run_id` (`run_id`(64),`id`),
  KEY `idx_event_type` (`dagster_event_type`(64),`id`),
  KEY `idx_events_by_asset` (`asset_key`(64),`dagster_event_type`(64),`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `event_logs`
--

LOCK TABLES `event_logs` WRITE;
/*!40000 ALTER TABLE `event_logs` DISABLE KEYS */;
/*!40000 ALTER TABLE `event_logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `instance_info`
--

DROP TABLE IF EXISTS `instance_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `instance_info` (
  `run_storage_id` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `instance_info`
--

LOCK TABLES `instance_info` WRITE;
/*!40000 ALTER TABLE `instance_info` DISABLE KEYS */;
INSERT INTO `instance_info` VALUES ('37a8dcc4-f886-4400-92a1-0287610f10ed');
/*!40000 ALTER TABLE `instance_info` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `instigators`
--

DROP TABLE IF EXISTS `instigators`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `instigators` (
  `id` int NOT NULL AUTO_INCREMENT,
  `selector_id` varchar(255) DEFAULT NULL,
  `repository_selector_id` varchar(255) DEFAULT NULL,
  `status` varchar(63) DEFAULT NULL,
  `instigator_type` varchar(63) DEFAULT NULL,
  `instigator_body` text,
  `create_timestamp` datetime(6) DEFAULT CURRENT_TIMESTAMP(6),
  `update_timestamp` datetime(6) DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `selector_id` (`selector_id`),
  KEY `ix_instigators_instigator_type` (`instigator_type`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `instigators`
--

LOCK TABLES `instigators` WRITE;
/*!40000 ALTER TABLE `instigators` DISABLE KEYS */;
INSERT INTO `instigators` VALUES (1,'f854ee7d4c336f1c9ccbc49f33b4907ec94f62f5','e8620a72936699d5150b334ce7ab970a9c6fc9eb','RUNNING','SENSOR','{\"__class__\": \"InstigatorState\", \"job_specific_data\": {\"__class__\": \"SensorInstigatorData\", \"cursor\": null, \"last_run_key\": null, \"last_tick_start_timestamp\": 1671060420.330343, \"last_tick_timestamp\": 1671060420.330343, \"min_interval\": 30}, \"job_type\": {\"__enum__\": \"InstigatorType.SENSOR\"}, \"origin\": {\"__class__\": \"ExternalJobOrigin\", \"external_repository_origin\": {\"__class__\": \"ExternalRepositoryOrigin\", \"repository_location_origin\": {\"__class__\": \"ManagedGrpcPythonEnvRepositoryLocationOrigin\", \"loadable_target_origin\": {\"__class__\": \"LoadableTargetOrigin\", \"attribute\": null, \"executable_path\": null, \"module_name\": null, \"package_name\": null, \"python_file\": \"/Users/christopherdecarolis/dagster/python_modules/dagster/dagster_tests/core_tests/graph_tests/blah.py\", \"working_directory\": null}, \"location_name\": \"blah.py\"}, \"repository_name\": \"the_repo\"}, \"job_name\": \"the_sensor\"}, \"status\": {\"__enum__\": \"InstigatorStatus.RUNNING\"}}','2022-12-14 15:22:59.994869','2022-12-14 23:27:00.477040');
/*!40000 ALTER TABLE `instigators` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `job_ticks`
--

DROP TABLE IF EXISTS `job_ticks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `job_ticks` (
  `id` int NOT NULL AUTO_INCREMENT,
  `job_origin_id` varchar(255) DEFAULT NULL,
  `selector_id` varchar(255) DEFAULT NULL,
  `status` varchar(63) DEFAULT NULL,
  `type` varchar(63) DEFAULT NULL,
  `timestamp` timestamp(6) NULL DEFAULT NULL,
  `tick_body` text,
  `create_timestamp` datetime(6) DEFAULT CURRENT_TIMESTAMP(6),
  `update_timestamp` datetime(6) DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `ix_job_ticks_job_origin_id` (`job_origin_id`),
  KEY `idx_job_tick_status` (`job_origin_id`(32),`status`(32)),
  KEY `idx_job_tick_timestamp` (`job_origin_id`,`timestamp`),
  KEY `idx_tick_selector_timestamp` (`selector_id`,`timestamp`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `job_ticks`
--

LOCK TABLES `job_ticks` WRITE;
/*!40000 ALTER TABLE `job_ticks` DISABLE KEYS */;
INSERT INTO `job_ticks` VALUES (1,'935580f8dfa3cf21502200fefce7f48baedb0468','f854ee7d4c336f1c9ccbc49f33b4907ec94f62f5','SKIPPED','SENSOR','2022-12-15 07:25:30.250586','{\"__class__\": \"TickData\", \"cursor\": null, \"error\": null, \"failure_count\": 0, \"job_name\": \"the_sensor\", \"job_origin_id\": \"935580f8dfa3cf21502200fefce7f48baedb0468\", \"job_type\": {\"__enum__\": \"InstigatorType.SENSOR\"}, \"log_key\": null, \"origin_run_ids\": [], \"run_ids\": [], \"run_keys\": [], \"selector_id\": \"f854ee7d4c336f1c9ccbc49f33b4907ec94f62f5\", \"skip_reason\": \"Sensor function returned an empty result\", \"status\": {\"__enum__\": \"TickStatus.SKIPPED\"}, \"timestamp\": 1671060330.250586}','2022-12-14 15:25:30.307546','2022-12-14 15:25:30.307546'),(2,'935580f8dfa3cf21502200fefce7f48baedb0468','f854ee7d4c336f1c9ccbc49f33b4907ec94f62f5','SKIPPED','SENSOR','2022-12-15 07:26:00.302501','{\"__class__\": \"TickData\", \"cursor\": null, \"error\": null, \"failure_count\": 0, \"job_name\": \"the_sensor\", \"job_origin_id\": \"935580f8dfa3cf21502200fefce7f48baedb0468\", \"job_type\": {\"__enum__\": \"InstigatorType.SENSOR\"}, \"log_key\": null, \"origin_run_ids\": [], \"run_ids\": [], \"run_keys\": [], \"selector_id\": \"f854ee7d4c336f1c9ccbc49f33b4907ec94f62f5\", \"skip_reason\": \"Sensor function returned an empty result\", \"status\": {\"__enum__\": \"TickStatus.SKIPPED\"}, \"timestamp\": 1671060360.302501}','2022-12-14 15:26:00.365969','2022-12-14 15:26:00.365969'),(3,'935580f8dfa3cf21502200fefce7f48baedb0468','f854ee7d4c336f1c9ccbc49f33b4907ec94f62f5','SKIPPED','SENSOR','2022-12-15 07:26:30.309093','{\"__class__\": \"TickData\", \"cursor\": null, \"error\": null, \"failure_count\": 0, \"job_name\": \"the_sensor\", \"job_origin_id\": \"935580f8dfa3cf21502200fefce7f48baedb0468\", \"job_type\": {\"__enum__\": \"InstigatorType.SENSOR\"}, \"log_key\": null, \"origin_run_ids\": [], \"run_ids\": [], \"run_keys\": [], \"selector_id\": \"f854ee7d4c336f1c9ccbc49f33b4907ec94f62f5\", \"skip_reason\": \"Sensor function returned an empty result\", \"status\": {\"__enum__\": \"TickStatus.SKIPPED\"}, \"timestamp\": 1671060390.309093}','2022-12-14 15:26:30.373061','2022-12-14 15:26:30.373061'),(4,'935580f8dfa3cf21502200fefce7f48baedb0468','f854ee7d4c336f1c9ccbc49f33b4907ec94f62f5','FAILURE','SENSOR','2022-12-15 07:27:00.330343','{\"__class__\": \"TickData\", \"cursor\": null, \"error\": {\"__class__\": \"SerializableErrorInfo\", \"cause\": {\"__class__\": \"SerializableErrorInfo\", \"cause\": null, \"cls_name\": \"_MultiThreadedRendezvous\", \"message\": \"grpc._channel._MultiThreadedRendezvous: <_MultiThreadedRendezvous of RPC that terminated with:\\n\\tstatus = StatusCode.UNAVAILABLE\\n\\tdetails = \\\"failed to connect to all addresses\\\"\\n\\tdebug_error_string = \\\"{\\\"created\\\":\\\"@1671060420.386189000\\\",\\\"description\\\":\\\"Failed to pick subchannel\\\",\\\"file\\\":\\\"src/core/ext/filters/client_channel/client_channel.cc\\\",\\\"file_line\\\":3261,\\\"referenced_errors\\\":[{\\\"created\\\":\\\"@1671060420.386189000\\\",\\\"description\\\":\\\"failed to connect to all addresses\\\",\\\"file\\\":\\\"src/core/lib/transport/error_utils.cc\\\",\\\"file_line\\\":167,\\\"grpc_status\\\":14}]}\\\"\\n>\\n\", \"stack\": [\"  File \\\"/Users/christopherdecarolis/dagster/python_modules/dagster/dagster/_grpc/client.py\\\", line 162, in _streaming_query\\n    yield from self._get_streaming_response(\\n\", \"  File \\\"/Users/christopherdecarolis/dagster/python_modules/dagster/dagster/_grpc/client.py\\\", line 152, in _get_streaming_response\\n    yield from getattr(stub, method)(request, metadata=self._metadata, timeout=timeout)\\n\", \"  File \\\"/Users/christopherdecarolis/.pyenv/versions/3.9.13/envs/dev-dcloud-3.9.13/lib/python3.9/site-packages/grpc/_channel.py\\\", line 426, in __next__\\n    return self._next()\\n\", \"  File \\\"/Users/christopherdecarolis/.pyenv/versions/3.9.13/envs/dev-dcloud-3.9.13/lib/python3.9/site-packages/grpc/_channel.py\\\", line 826, in _next\\n    raise self\\n\"]}, \"cls_name\": \"DagsterUserCodeUnreachableError\", \"message\": \"dagster._core.errors.DagsterUserCodeUnreachableError: Could not reach user code server\\n\", \"stack\": [\"  File \\\"/Users/christopherdecarolis/dagster/python_modules/dagster/dagster/_daemon/sensor.py\\\", line 484, in _process_tick_generator\\n    yield from _evaluate_sensor(\\n\", \"  File \\\"/Users/christopherdecarolis/dagster/python_modules/dagster/dagster/_daemon/sensor.py\\\", line 549, in _evaluate_sensor\\n    sensor_runtime_data = repo_location.get_external_sensor_execution_data(\\n\", \"  File \\\"/Users/christopherdecarolis/dagster/python_modules/dagster/dagster/_core/host_representation/repository_location.py\\\", line 822, in get_external_sensor_execution_data\\n    return sync_get_external_sensor_execution_data_grpc(\\n\", \"  File \\\"/Users/christopherdecarolis/dagster/python_modules/dagster/dagster/_api/snapshot_sensor.py\\\", line 59, in sync_get_external_sensor_execution_data_grpc\\n    api_client.external_sensor_execution(\\n\", \"  File \\\"/Users/christopherdecarolis/dagster/python_modules/dagster/dagster/_grpc/client.py\\\", line 369, in external_sensor_execution\\n    chunks = list(\\n\", \"  File \\\"/Users/christopherdecarolis/dagster/python_modules/dagster/dagster/_grpc/client.py\\\", line 166, in _streaming_query\\n    raise DagsterUserCodeUnreachableError(\\\"Could not reach user code server\\\") from e\\n\"]}, \"failure_count\": 0, \"job_name\": \"the_sensor\", \"job_origin_id\": \"935580f8dfa3cf21502200fefce7f48baedb0468\", \"job_type\": {\"__enum__\": \"InstigatorType.SENSOR\"}, \"log_key\": null, \"origin_run_ids\": [], \"run_ids\": [], \"run_keys\": [], \"selector_id\": \"f854ee7d4c336f1c9ccbc49f33b4907ec94f62f5\", \"skip_reason\": null, \"status\": {\"__enum__\": \"TickStatus.FAILURE\"}, \"timestamp\": 1671060420.330343}','2022-12-14 15:27:00.384185','2022-12-14 15:27:00.384185');
/*!40000 ALTER TABLE `job_ticks` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `jobs`
--

DROP TABLE IF EXISTS `jobs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `jobs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `job_origin_id` varchar(255) DEFAULT NULL,
  `selector_id` varchar(255) DEFAULT NULL,
  `repository_origin_id` varchar(255) DEFAULT NULL,
  `status` varchar(63) DEFAULT NULL,
  `job_type` varchar(63) DEFAULT NULL,
  `job_body` text,
  `create_timestamp` datetime(6) DEFAULT CURRENT_TIMESTAMP(6),
  `update_timestamp` datetime(6) DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `job_origin_id` (`job_origin_id`),
  KEY `ix_jobs_job_type` (`job_type`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `jobs`
--

LOCK TABLES `jobs` WRITE;
/*!40000 ALTER TABLE `jobs` DISABLE KEYS */;
INSERT INTO `jobs` VALUES (1,'935580f8dfa3cf21502200fefce7f48baedb0468','f854ee7d4c336f1c9ccbc49f33b4907ec94f62f5','61a139b971f6b1ef0d958779a1e19bdede7129c3','RUNNING','SENSOR','{\"__class__\": \"InstigatorState\", \"job_specific_data\": {\"__class__\": \"SensorInstigatorData\", \"cursor\": null, \"last_run_key\": null, \"last_tick_start_timestamp\": 1671060420.330343, \"last_tick_timestamp\": 1671060420.330343, \"min_interval\": 30}, \"job_type\": {\"__enum__\": \"InstigatorType.SENSOR\"}, \"origin\": {\"__class__\": \"ExternalJobOrigin\", \"external_repository_origin\": {\"__class__\": \"ExternalRepositoryOrigin\", \"repository_location_origin\": {\"__class__\": \"ManagedGrpcPythonEnvRepositoryLocationOrigin\", \"loadable_target_origin\": {\"__class__\": \"LoadableTargetOrigin\", \"attribute\": null, \"executable_path\": null, \"module_name\": null, \"package_name\": null, \"python_file\": \"/Users/christopherdecarolis/dagster/python_modules/dagster/dagster_tests/core_tests/graph_tests/blah.py\", \"working_directory\": null}, \"location_name\": \"blah.py\"}, \"repository_name\": \"the_repo\"}, \"job_name\": \"the_sensor\"}, \"status\": {\"__enum__\": \"InstigatorStatus.RUNNING\"}}','2022-12-14 15:22:59.989238','2022-12-14 23:27:00.463240');
/*!40000 ALTER TABLE `jobs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `kvs`
--

DROP TABLE IF EXISTS `kvs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `kvs` (
  `key` text NOT NULL,
  `value` text,
  UNIQUE KEY `idx_kvs_keys_unique` (`key`(64))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kvs`
--

LOCK TABLES `kvs` WRITE;
/*!40000 ALTER TABLE `kvs` DISABLE KEYS */;
/*!40000 ALTER TABLE `kvs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `run_tags`
--

DROP TABLE IF EXISTS `run_tags`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `run_tags` (
  `id` int NOT NULL AUTO_INCREMENT,
  `run_id` varchar(255) DEFAULT NULL,
  `key` text,
  `value` text,
  PRIMARY KEY (`id`),
  KEY `run_id` (`run_id`),
  KEY `idx_run_tags` (`key`(64),`value`(64)),
  CONSTRAINT `run_tags_ibfk_1` FOREIGN KEY (`run_id`) REFERENCES `runs` (`run_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `run_tags`
--

LOCK TABLES `run_tags` WRITE;
/*!40000 ALTER TABLE `run_tags` DISABLE KEYS */;
/*!40000 ALTER TABLE `run_tags` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `runs`
--

DROP TABLE IF EXISTS `runs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `runs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `run_id` varchar(255) DEFAULT NULL,
  `snapshot_id` varchar(255) DEFAULT NULL,
  `pipeline_name` text,
  `mode` text,
  `status` varchar(63) DEFAULT NULL,
  `run_body` text,
  `partition` text,
  `partition_set` text,
  `create_timestamp` datetime(6) DEFAULT CURRENT_TIMESTAMP(6),
  `update_timestamp` datetime(6) DEFAULT CURRENT_TIMESTAMP(6),
  `start_time` double DEFAULT NULL,
  `end_time` double DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `run_id` (`run_id`),
  KEY `fk_runs_snapshot_id_snapshots_snapshot_id` (`snapshot_id`),
  KEY `idx_run_status` (`status`(32)),
  KEY `idx_run_range` (`status`(32),`update_timestamp`,`create_timestamp`),
  KEY `idx_run_partitions` (`partition_set`(64),`partition`(64)),
  CONSTRAINT `fk_runs_snapshot_id_snapshots_snapshot_id` FOREIGN KEY (`snapshot_id`) REFERENCES `snapshots` (`snapshot_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `runs`
--

LOCK TABLES `runs` WRITE;
/*!40000 ALTER TABLE `runs` DISABLE KEYS */;
/*!40000 ALTER TABLE `runs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `secondary_indexes`
--

DROP TABLE IF EXISTS `secondary_indexes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `secondary_indexes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(512) DEFAULT NULL,
  `create_timestamp` datetime(6) DEFAULT CURRENT_TIMESTAMP(6),
  `migration_completed` datetime(6) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `secondary_indexes`
--

LOCK TABLES `secondary_indexes` WRITE;
/*!40000 ALTER TABLE `secondary_indexes` DISABLE KEYS */;
INSERT INTO `secondary_indexes` VALUES (1,'run_partitions','2022-12-14 15:22:45.220202','2022-12-14 15:22:45.215905'),(2,'run_repo_label_tags','2022-12-14 15:22:45.236045','2022-12-14 15:22:45.232440'),(3,'bulk_action_types','2022-12-14 15:22:45.250694','2022-12-14 15:22:45.246760'),(4,'run_start_end_overwritten','2022-12-14 15:22:45.299954','2022-12-14 15:22:45.295713'),(5,'asset_key_table','2022-12-14 15:22:45.443690','2022-12-14 15:22:45.438270'),(6,'asset_key_index_columns','2022-12-14 15:22:45.464114','2022-12-14 15:22:45.459206'),(7,'schedule_jobs_selector_id','2022-12-14 15:22:45.635658','2022-12-14 15:22:45.619689'),(8,'schedule_ticks_selector_id','2022-12-14 15:22:45.703628','2022-12-14 15:22:45.691574');
/*!40000 ALTER TABLE `secondary_indexes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `snapshots`
--

DROP TABLE IF EXISTS `snapshots`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `snapshots` (
  `id` int NOT NULL AUTO_INCREMENT,
  `snapshot_id` varchar(255) NOT NULL,
  `snapshot_body` blob NOT NULL,
  `snapshot_type` varchar(63) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `snapshot_id` (`snapshot_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `snapshots`
--

LOCK TABLES `snapshots` WRITE;
/*!40000 ALTER TABLE `snapshots` DISABLE KEYS */;
/*!40000 ALTER TABLE `snapshots` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2022-12-14 15:30:41
