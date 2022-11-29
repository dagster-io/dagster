-- MySQL dump 10.13  Distrib 8.0.31, for macos12.6 (x86_64)
--
-- Host: localhost    Database: test_2
-- ------------------------------------------------------
-- Server version	8.0.31

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
INSERT INTO `alembic_version` VALUES ('958a9495162d');
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
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `asset_event_tags`
--

LOCK TABLES `asset_event_tags` WRITE;
/*!40000 ALTER TABLE `asset_event_tags` DISABLE KEYS */;
INSERT INTO `asset_event_tags` VALUES (1,14,'[\"upstream_asset\"]','dagster/code_version','b2f62146-f2f9-4e21-816c-813d40face9b','2022-11-17 08:32:39.217428'),(2,14,'[\"upstream_asset\"]','dagster/logical_version','a6b37da4cf9895227adf8c3a20507d9b465c1e39b159429582c07db0db6fd1fa','2022-11-17 08:32:39.217428');
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
  PRIMARY KEY (`id`),
  UNIQUE KEY `asset_key` (`asset_key`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `asset_keys`
--

LOCK TABLES `asset_keys` WRITE;
/*!40000 ALTER TABLE `asset_keys` DISABLE KEYS */;
INSERT INTO `asset_keys` VALUES (1,'[\"upstream_asset\"]','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"StepMaterializationData\", \"asset_lineage\": [], \"materialization\": {\"__class__\": \"AssetMaterialization\", \"asset_key\": {\"__class__\": \"AssetKey\", \"path\": [\"upstream_asset\"]}, \"description\": null, \"metadata_entries\": [{\"__class__\": \"EventMetadataEntry\", \"description\": null, \"entry_data\": {\"__class__\": \"PathMetadataEntryData\", \"path\": \"/Users/claire/dagster_home_mysql/storage/upstream_asset\"}, \"label\": \"path\"}], \"partition\": null, \"tags\": {\"dagster/code_version\": \"b2f62146-f2f9-4e21-816c-813d40face9b\", \"dagster/logical_version\": \"a6b37da4cf9895227adf8c3a20507d9b465c1e39b159429582c07db0db6fd1fa\"}}}, \"event_type_value\": \"ASSET_MATERIALIZATION\", \"logging_tags\": {\"pipeline_name\": \"__ASSET_JOB\", \"pipeline_tags\": \"{\'.dagster/grpc_info\': \'{\\\"host\\\": \\\"localhost\\\", \\\"socket\\\": \\\"/var/folders/lr/mcmhlx2177953tcj5m7v8l3h0000gn/T/tmpxpq1vx51\\\"}\', \'dagster/step_selection\': \'upstream_asset\'}\", \"resource_fn_name\": \"None\", \"resource_name\": \"None\", \"run_id\": \"b2f62146-f2f9-4e21-816c-813d40face9b\", \"solid_name\": \"upstream_asset\", \"step_key\": \"upstream_asset\"}, \"message\": \"Materialized value upstream_asset.\", \"pid\": 48179, \"pipeline_name\": \"__ASSET_JOB\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"upstream_asset\", \"parent\": null}, \"step_handle\": {\"__class__\": \"StepHandle\", \"key\": \"upstream_asset\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"upstream_asset\", \"parent\": null}}, \"step_key\": \"upstream_asset\", \"step_kind_value\": \"COMPUTE\"}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"b2f62146-f2f9-4e21-816c-813d40face9b\", \"step_key\": \"upstream_asset\", \"timestamp\": 1668645159.217428, \"user_message\": \"Materialized value upstream_asset.\"}','b2f62146-f2f9-4e21-816c-813d40face9b',NULL,NULL,'2022-11-17 08:32:39.217428',NULL,'2022-11-16 16:32:31.142155');
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
  KEY `idx_bulk_actions_action_type` (`action_type`),
  KEY `idx_bulk_actions` (`key`),
  KEY `idx_bulk_actions_selector_id` (`selector_id`(64)),
  KEY `idx_bulk_actions_status` (`status`(32))
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
  KEY `idx_events_by_run_id` (`run_id`(64),`id`),
  KEY `idx_step_key` (`step_key`(32)),
  KEY `idx_event_type` (`dagster_event_type`(64),`id`),
  KEY `idx_events_by_asset` (`asset_key`(64),`dagster_event_type`(64),`id`),
  KEY `idx_events_by_asset_partition` (`asset_key`(64),`dagster_event_type`(64),`partition`(64),`id`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `event_logs`
--

LOCK TABLES `event_logs` WRITE;
/*!40000 ALTER TABLE `event_logs` DISABLE KEYS */;
INSERT INTO `event_logs` VALUES (1,'b2f62146-f2f9-4e21-816c-813d40face9b','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"AssetMaterializationPlannedData\", \"asset_key\": {\"__class__\": \"AssetKey\", \"path\": [\"upstream_asset\"]}}, \"event_type_value\": \"ASSET_MATERIALIZATION_PLANNED\", \"logging_tags\": {}, \"message\": \"__ASSET_JOB intends to materialize asset [\\\"upstream_asset\\\"]\", \"pid\": null, \"pipeline_name\": \"__ASSET_JOB\", \"solid_handle\": null, \"step_handle\": null, \"step_key\": null, \"step_kind_value\": null}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"b2f62146-f2f9-4e21-816c-813d40face9b\", \"step_key\": null, \"timestamp\": 1668645151.1392808, \"user_message\": \"\"}','ASSET_MATERIALIZATION_PLANNED','2022-11-17 08:32:31.139281',NULL,'[\"upstream_asset\"]',NULL),(2,'b2f62146-f2f9-4e21-816c-813d40face9b','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": null, \"event_type_value\": \"PIPELINE_STARTING\", \"logging_tags\": {}, \"message\": null, \"pid\": null, \"pipeline_name\": \"__ASSET_JOB\", \"solid_handle\": null, \"step_handle\": null, \"step_key\": null, \"step_kind_value\": null}, \"error_info\": null, \"level\": 20, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"b2f62146-f2f9-4e21-816c-813d40face9b\", \"step_key\": null, \"timestamp\": 1668645151.1452742, \"user_message\": \"\"}','PIPELINE_STARTING','2022-11-17 08:32:31.145274',NULL,NULL,NULL),(3,'b2f62146-f2f9-4e21-816c-813d40face9b','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"EngineEventData\", \"error\": null, \"marker_end\": null, \"marker_start\": null, \"metadata_entries\": [{\"__class__\": \"EventMetadataEntry\", \"description\": null, \"entry_data\": {\"__class__\": \"TextMetadataEntryData\", \"text\": \"48176\"}, \"label\": \"pid\"}]}, \"event_type_value\": \"ENGINE_EVENT\", \"logging_tags\": {}, \"message\": \"Started process for run (pid: 48176).\", \"pid\": null, \"pipeline_name\": \"__ASSET_JOB\", \"solid_handle\": null, \"step_handle\": null, \"step_key\": null, \"step_kind_value\": null}, \"error_info\": null, \"level\": 20, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"b2f62146-f2f9-4e21-816c-813d40face9b\", \"step_key\": null, \"timestamp\": 1668645153.2225559, \"user_message\": \"\"}','ENGINE_EVENT','2022-11-17 08:32:33.222556',NULL,NULL,NULL),(4,'b2f62146-f2f9-4e21-816c-813d40face9b','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": null, \"event_type_value\": \"PIPELINE_START\", \"logging_tags\": {}, \"message\": \"Started execution of run for \\\"__ASSET_JOB\\\".\", \"pid\": 48176, \"pipeline_name\": \"__ASSET_JOB\", \"solid_handle\": null, \"step_handle\": null, \"step_key\": null, \"step_kind_value\": null}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"b2f62146-f2f9-4e21-816c-813d40face9b\", \"step_key\": null, \"timestamp\": 1668645155.6940742, \"user_message\": \"Started execution of run for \\\"__ASSET_JOB\\\".\"}','PIPELINE_START','2022-11-17 08:32:35.694074',NULL,NULL,NULL),(5,'b2f62146-f2f9-4e21-816c-813d40face9b','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"EngineEventData\", \"error\": null, \"marker_end\": null, \"marker_start\": null, \"metadata_entries\": [{\"__class__\": \"EventMetadataEntry\", \"description\": null, \"entry_data\": {\"__class__\": \"TextMetadataEntryData\", \"text\": \"48176\"}, \"label\": \"pid\"}, {\"__class__\": \"EventMetadataEntry\", \"description\": null, \"entry_data\": {\"__class__\": \"TextMetadataEntryData\", \"text\": \"[\'upstream_asset\']\"}, \"label\": \"step_keys\"}]}, \"event_type_value\": \"ENGINE_EVENT\", \"logging_tags\": {}, \"message\": \"Executing steps using multiprocess executor: parent process (pid: 48176)\", \"pid\": 48176, \"pipeline_name\": \"__ASSET_JOB\", \"solid_handle\": null, \"step_handle\": null, \"step_key\": null, \"step_kind_value\": null}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"b2f62146-f2f9-4e21-816c-813d40face9b\", \"step_key\": null, \"timestamp\": 1668645155.747735, \"user_message\": \"Executing steps using multiprocess executor: parent process (pid: 48176)\"}','ENGINE_EVENT','2022-11-17 08:32:35.747735',NULL,NULL,NULL),(6,'b2f62146-f2f9-4e21-816c-813d40face9b','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"EngineEventData\", \"error\": null, \"marker_end\": null, \"marker_start\": \"step_process_start\", \"metadata_entries\": []}, \"event_type_value\": \"STEP_WORKER_STARTING\", \"logging_tags\": {\"pipeline_name\": \"__ASSET_JOB\", \"pipeline_tags\": \"{\'.dagster/grpc_info\': \'{\\\"host\\\": \\\"localhost\\\", \\\"socket\\\": \\\"/var/folders/lr/mcmhlx2177953tcj5m7v8l3h0000gn/T/tmpxpq1vx51\\\"}\', \'dagster/step_selection\': \'upstream_asset\'}\", \"resource_fn_name\": \"None\", \"resource_name\": \"None\", \"run_id\": \"b2f62146-f2f9-4e21-816c-813d40face9b\", \"solid_name\": \"upstream_asset\", \"step_key\": \"upstream_asset\"}, \"message\": \"Launching subprocess for \\\"upstream_asset\\\".\", \"pid\": 48176, \"pipeline_name\": \"__ASSET_JOB\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"upstream_asset\", \"parent\": null}, \"step_handle\": {\"__class__\": \"StepHandle\", \"key\": \"upstream_asset\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"upstream_asset\", \"parent\": null}}, \"step_key\": \"upstream_asset\", \"step_kind_value\": \"COMPUTE\"}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"b2f62146-f2f9-4e21-816c-813d40face9b\", \"step_key\": \"upstream_asset\", \"timestamp\": 1668645155.774718, \"user_message\": \"Launching subprocess for \\\"upstream_asset\\\".\"}','STEP_WORKER_STARTING','2022-11-17 08:32:35.774718','upstream_asset',NULL,NULL),(7,'b2f62146-f2f9-4e21-816c-813d40face9b','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"EngineEventData\", \"error\": null, \"marker_end\": \"step_process_start\", \"marker_start\": null, \"metadata_entries\": [{\"__class__\": \"EventMetadataEntry\", \"description\": null, \"entry_data\": {\"__class__\": \"TextMetadataEntryData\", \"text\": \"48179\"}, \"label\": \"pid\"}]}, \"event_type_value\": \"STEP_WORKER_STARTED\", \"logging_tags\": {}, \"message\": \"Executing step \\\"upstream_asset\\\" in subprocess.\", \"pid\": 48179, \"pipeline_name\": \"__ASSET_JOB\", \"solid_handle\": null, \"step_handle\": null, \"step_key\": \"upstream_asset\", \"step_kind_value\": null}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"b2f62146-f2f9-4e21-816c-813d40face9b\", \"step_key\": \"upstream_asset\", \"timestamp\": 1668645159.118706, \"user_message\": \"Executing step \\\"upstream_asset\\\" in subprocess.\"}','STEP_WORKER_STARTED','2022-11-17 08:32:39.118706','upstream_asset',NULL,NULL),(8,'b2f62146-f2f9-4e21-816c-813d40face9b','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"EngineEventData\", \"error\": null, \"marker_end\": null, \"marker_start\": \"resources\", \"metadata_entries\": []}, \"event_type_value\": \"RESOURCE_INIT_STARTED\", \"logging_tags\": {}, \"message\": \"Starting initialization of resources [io_manager].\", \"pid\": 48179, \"pipeline_name\": \"__ASSET_JOB\", \"solid_handle\": null, \"step_handle\": {\"__class__\": \"StepHandle\", \"key\": \"upstream_asset\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"upstream_asset\", \"parent\": null}}, \"step_key\": \"upstream_asset\", \"step_kind_value\": null}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"b2f62146-f2f9-4e21-816c-813d40face9b\", \"step_key\": \"upstream_asset\", \"timestamp\": 1668645159.127358, \"user_message\": \"Starting initialization of resources [io_manager].\"}','RESOURCE_INIT_STARTED','2022-11-17 08:32:39.127358','upstream_asset',NULL,NULL),(9,'b2f62146-f2f9-4e21-816c-813d40face9b','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"EngineEventData\", \"error\": null, \"marker_end\": \"resources\", \"marker_start\": null, \"metadata_entries\": [{\"__class__\": \"EventMetadataEntry\", \"description\": null, \"entry_data\": {\"__class__\": \"PythonArtifactMetadataEntryData\", \"module\": \"dagster._core.storage.fs_io_manager\", \"name\": \"PickledObjectFilesystemIOManager\"}, \"label\": \"io_manager\"}, {\"__class__\": \"EventMetadataEntry\", \"description\": null, \"entry_data\": {\"__class__\": \"TextMetadataEntryData\", \"text\": \"0.14ms\"}, \"label\": \"io_manager:init_time\"}]}, \"event_type_value\": \"RESOURCE_INIT_SUCCESS\", \"logging_tags\": {}, \"message\": \"Finished initialization of resources [io_manager].\", \"pid\": 48179, \"pipeline_name\": \"__ASSET_JOB\", \"solid_handle\": null, \"step_handle\": {\"__class__\": \"StepHandle\", \"key\": \"upstream_asset\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"upstream_asset\", \"parent\": null}}, \"step_key\": \"upstream_asset\", \"step_kind_value\": null}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"b2f62146-f2f9-4e21-816c-813d40face9b\", \"step_key\": \"upstream_asset\", \"timestamp\": 1668645159.1342359, \"user_message\": \"Finished initialization of resources [io_manager].\"}','RESOURCE_INIT_SUCCESS','2022-11-17 08:32:39.134236','upstream_asset',NULL,NULL),(10,'b2f62146-f2f9-4e21-816c-813d40face9b','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"ComputeLogsCaptureData\", \"external_url\": null, \"log_key\": \"qrqrjkzj\", \"step_keys\": [\"upstream_asset\"]}, \"event_type_value\": \"LOGS_CAPTURED\", \"logging_tags\": {}, \"message\": \"Started capturing logs in process (pid: 48179).\", \"pid\": 48179, \"pipeline_name\": \"__ASSET_JOB\", \"solid_handle\": null, \"step_handle\": null, \"step_key\": null, \"step_kind_value\": null}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"b2f62146-f2f9-4e21-816c-813d40face9b\", \"step_key\": null, \"timestamp\": 1668645159.166634, \"user_message\": \"Started capturing logs in process (pid: 48179).\"}','LOGS_CAPTURED','2022-11-17 08:32:39.166634',NULL,NULL,NULL),(11,'b2f62146-f2f9-4e21-816c-813d40face9b','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": null, \"event_type_value\": \"STEP_START\", \"logging_tags\": {\"pipeline_name\": \"__ASSET_JOB\", \"pipeline_tags\": \"{\'.dagster/grpc_info\': \'{\\\"host\\\": \\\"localhost\\\", \\\"socket\\\": \\\"/var/folders/lr/mcmhlx2177953tcj5m7v8l3h0000gn/T/tmpxpq1vx51\\\"}\', \'dagster/step_selection\': \'upstream_asset\'}\", \"resource_fn_name\": \"None\", \"resource_name\": \"None\", \"run_id\": \"b2f62146-f2f9-4e21-816c-813d40face9b\", \"solid_name\": \"upstream_asset\", \"step_key\": \"upstream_asset\"}, \"message\": \"Started execution of step \\\"upstream_asset\\\".\", \"pid\": 48179, \"pipeline_name\": \"__ASSET_JOB\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"upstream_asset\", \"parent\": null}, \"step_handle\": {\"__class__\": \"StepHandle\", \"key\": \"upstream_asset\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"upstream_asset\", \"parent\": null}}, \"step_key\": \"upstream_asset\", \"step_kind_value\": \"COMPUTE\"}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"b2f62146-f2f9-4e21-816c-813d40face9b\", \"step_key\": \"upstream_asset\", \"timestamp\": 1668645159.1786811, \"user_message\": \"Started execution of step \\\"upstream_asset\\\".\"}','STEP_START','2022-11-17 08:32:39.178681','upstream_asset',NULL,NULL),(12,'b2f62146-f2f9-4e21-816c-813d40face9b','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"StepOutputData\", \"metadata_entries\": [], \"step_output_handle\": {\"__class__\": \"StepOutputHandle\", \"mapping_key\": null, \"output_name\": \"result\", \"step_key\": \"upstream_asset\"}, \"type_check_data\": {\"__class__\": \"TypeCheckData\", \"description\": null, \"label\": \"result\", \"metadata_entries\": [], \"success\": true}, \"version\": null}, \"event_type_value\": \"STEP_OUTPUT\", \"logging_tags\": {\"pipeline_name\": \"__ASSET_JOB\", \"pipeline_tags\": \"{\'.dagster/grpc_info\': \'{\\\"host\\\": \\\"localhost\\\", \\\"socket\\\": \\\"/var/folders/lr/mcmhlx2177953tcj5m7v8l3h0000gn/T/tmpxpq1vx51\\\"}\', \'dagster/step_selection\': \'upstream_asset\'}\", \"resource_fn_name\": \"None\", \"resource_name\": \"None\", \"run_id\": \"b2f62146-f2f9-4e21-816c-813d40face9b\", \"solid_name\": \"upstream_asset\", \"step_key\": \"upstream_asset\"}, \"message\": \"Yielded output \\\"result\\\" of type \\\"Any\\\". (Type check passed).\", \"pid\": 48179, \"pipeline_name\": \"__ASSET_JOB\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"upstream_asset\", \"parent\": null}, \"step_handle\": {\"__class__\": \"StepHandle\", \"key\": \"upstream_asset\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"upstream_asset\", \"parent\": null}}, \"step_key\": \"upstream_asset\", \"step_kind_value\": \"COMPUTE\"}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"b2f62146-f2f9-4e21-816c-813d40face9b\", \"step_key\": \"upstream_asset\", \"timestamp\": 1668645159.187447, \"user_message\": \"Yielded output \\\"result\\\" of type \\\"Any\\\". (Type check passed).\"}','STEP_OUTPUT','2022-11-17 08:32:39.187447','upstream_asset',NULL,NULL),(13,'b2f62146-f2f9-4e21-816c-813d40face9b','{\"__class__\": \"EventLogEntry\", \"dagster_event\": null, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"b2f62146-f2f9-4e21-816c-813d40face9b\", \"step_key\": \"upstream_asset\", \"timestamp\": 1668645159.19417, \"user_message\": \"Writing file at: /Users/claire/dagster_home_mysql/storage/upstream_asset\"}',NULL,'2022-11-17 08:32:39.194170','upstream_asset',NULL,NULL),(14,'b2f62146-f2f9-4e21-816c-813d40face9b','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"StepMaterializationData\", \"asset_lineage\": [], \"materialization\": {\"__class__\": \"AssetMaterialization\", \"asset_key\": {\"__class__\": \"AssetKey\", \"path\": [\"upstream_asset\"]}, \"description\": null, \"metadata_entries\": [{\"__class__\": \"EventMetadataEntry\", \"description\": null, \"entry_data\": {\"__class__\": \"PathMetadataEntryData\", \"path\": \"/Users/claire/dagster_home_mysql/storage/upstream_asset\"}, \"label\": \"path\"}], \"partition\": null, \"tags\": {\"dagster/code_version\": \"b2f62146-f2f9-4e21-816c-813d40face9b\", \"dagster/logical_version\": \"a6b37da4cf9895227adf8c3a20507d9b465c1e39b159429582c07db0db6fd1fa\"}}}, \"event_type_value\": \"ASSET_MATERIALIZATION\", \"logging_tags\": {\"pipeline_name\": \"__ASSET_JOB\", \"pipeline_tags\": \"{\'.dagster/grpc_info\': \'{\\\"host\\\": \\\"localhost\\\", \\\"socket\\\": \\\"/var/folders/lr/mcmhlx2177953tcj5m7v8l3h0000gn/T/tmpxpq1vx51\\\"}\', \'dagster/step_selection\': \'upstream_asset\'}\", \"resource_fn_name\": \"None\", \"resource_name\": \"None\", \"run_id\": \"b2f62146-f2f9-4e21-816c-813d40face9b\", \"solid_name\": \"upstream_asset\", \"step_key\": \"upstream_asset\"}, \"message\": \"Materialized value upstream_asset.\", \"pid\": 48179, \"pipeline_name\": \"__ASSET_JOB\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"upstream_asset\", \"parent\": null}, \"step_handle\": {\"__class__\": \"StepHandle\", \"key\": \"upstream_asset\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"upstream_asset\", \"parent\": null}}, \"step_key\": \"upstream_asset\", \"step_kind_value\": \"COMPUTE\"}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"b2f62146-f2f9-4e21-816c-813d40face9b\", \"step_key\": \"upstream_asset\", \"timestamp\": 1668645159.217428, \"user_message\": \"Materialized value upstream_asset.\"}','ASSET_MATERIALIZATION','2022-11-17 08:32:39.217428','upstream_asset','[\"upstream_asset\"]',NULL),(15,'b2f62146-f2f9-4e21-816c-813d40face9b','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"HandledOutputData\", \"manager_key\": \"io_manager\", \"metadata_entries\": [{\"__class__\": \"EventMetadataEntry\", \"description\": null, \"entry_data\": {\"__class__\": \"PathMetadataEntryData\", \"path\": \"/Users/claire/dagster_home_mysql/storage/upstream_asset\"}, \"label\": \"path\"}], \"output_name\": \"result\"}, \"event_type_value\": \"HANDLED_OUTPUT\", \"logging_tags\": {\"pipeline_name\": \"__ASSET_JOB\", \"pipeline_tags\": \"{\'.dagster/grpc_info\': \'{\\\"host\\\": \\\"localhost\\\", \\\"socket\\\": \\\"/var/folders/lr/mcmhlx2177953tcj5m7v8l3h0000gn/T/tmpxpq1vx51\\\"}\', \'dagster/step_selection\': \'upstream_asset\'}\", \"resource_fn_name\": \"None\", \"resource_name\": \"None\", \"run_id\": \"b2f62146-f2f9-4e21-816c-813d40face9b\", \"solid_name\": \"upstream_asset\", \"step_key\": \"upstream_asset\"}, \"message\": \"Handled output \\\"result\\\" using IO manager \\\"io_manager\\\"\", \"pid\": 48179, \"pipeline_name\": \"__ASSET_JOB\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"upstream_asset\", \"parent\": null}, \"step_handle\": {\"__class__\": \"StepHandle\", \"key\": \"upstream_asset\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"upstream_asset\", \"parent\": null}}, \"step_key\": \"upstream_asset\", \"step_kind_value\": \"COMPUTE\"}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"b2f62146-f2f9-4e21-816c-813d40face9b\", \"step_key\": \"upstream_asset\", \"timestamp\": 1668645159.244406, \"user_message\": \"Handled output \\\"result\\\" using IO manager \\\"io_manager\\\"\"}','HANDLED_OUTPUT','2022-11-17 08:32:39.244406','upstream_asset',NULL,NULL),(16,'b2f62146-f2f9-4e21-816c-813d40face9b','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"StepSuccessData\", \"duration_ms\": 82.88181700000008}, \"event_type_value\": \"STEP_SUCCESS\", \"logging_tags\": {\"pipeline_name\": \"__ASSET_JOB\", \"pipeline_tags\": \"{\'.dagster/grpc_info\': \'{\\\"host\\\": \\\"localhost\\\", \\\"socket\\\": \\\"/var/folders/lr/mcmhlx2177953tcj5m7v8l3h0000gn/T/tmpxpq1vx51\\\"}\', \'dagster/step_selection\': \'upstream_asset\'}\", \"resource_fn_name\": \"None\", \"resource_name\": \"None\", \"run_id\": \"b2f62146-f2f9-4e21-816c-813d40face9b\", \"solid_name\": \"upstream_asset\", \"step_key\": \"upstream_asset\"}, \"message\": \"Finished execution of step \\\"upstream_asset\\\" in 82ms.\", \"pid\": 48179, \"pipeline_name\": \"__ASSET_JOB\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"upstream_asset\", \"parent\": null}, \"step_handle\": {\"__class__\": \"StepHandle\", \"key\": \"upstream_asset\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"upstream_asset\", \"parent\": null}}, \"step_key\": \"upstream_asset\", \"step_kind_value\": \"COMPUTE\"}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"b2f62146-f2f9-4e21-816c-813d40face9b\", \"step_key\": \"upstream_asset\", \"timestamp\": 1668645159.269, \"user_message\": \"Finished execution of step \\\"upstream_asset\\\" in 82ms.\"}','STEP_SUCCESS','2022-11-17 08:32:39.269000','upstream_asset',NULL,NULL),(17,'b2f62146-f2f9-4e21-816c-813d40face9b','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"EngineEventData\", \"error\": null, \"marker_end\": null, \"marker_start\": null, \"metadata_entries\": [{\"__class__\": \"EventMetadataEntry\", \"description\": null, \"entry_data\": {\"__class__\": \"TextMetadataEntryData\", \"text\": \"48176\"}, \"label\": \"pid\"}]}, \"event_type_value\": \"ENGINE_EVENT\", \"logging_tags\": {}, \"message\": \"Multiprocess executor: parent process exiting after 3.89s (pid: 48176)\", \"pid\": 48176, \"pipeline_name\": \"__ASSET_JOB\", \"solid_handle\": null, \"step_handle\": null, \"step_key\": null, \"step_kind_value\": null}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"b2f62146-f2f9-4e21-816c-813d40face9b\", \"step_key\": null, \"timestamp\": 1668645159.664862, \"user_message\": \"Multiprocess executor: parent process exiting after 3.89s (pid: 48176)\"}','ENGINE_EVENT','2022-11-17 08:32:39.664862',NULL,NULL,NULL),(18,'b2f62146-f2f9-4e21-816c-813d40face9b','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": null, \"event_type_value\": \"PIPELINE_SUCCESS\", \"logging_tags\": {}, \"message\": \"Finished execution of run for \\\"__ASSET_JOB\\\".\", \"pid\": 48176, \"pipeline_name\": \"__ASSET_JOB\", \"solid_handle\": null, \"step_handle\": null, \"step_key\": null, \"step_kind_value\": null}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"b2f62146-f2f9-4e21-816c-813d40face9b\", \"step_key\": null, \"timestamp\": 1668645159.675392, \"user_message\": \"Finished execution of run for \\\"__ASSET_JOB\\\".\"}','PIPELINE_SUCCESS','2022-11-17 08:32:39.675392',NULL,NULL,NULL),(19,'b2f62146-f2f9-4e21-816c-813d40face9b','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"EngineEventData\", \"error\": null, \"marker_end\": null, \"marker_start\": null, \"metadata_entries\": []}, \"event_type_value\": \"ENGINE_EVENT\", \"logging_tags\": {}, \"message\": \"Process for run exited (pid: 48176).\", \"pid\": null, \"pipeline_name\": \"__ASSET_JOB\", \"solid_handle\": null, \"step_handle\": null, \"step_key\": null, \"step_kind_value\": null}, \"error_info\": null, \"level\": 20, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"b2f62146-f2f9-4e21-816c-813d40face9b\", \"step_key\": null, \"timestamp\": 1668645159.717071, \"user_message\": \"\"}','ENGINE_EVENT','2022-11-17 08:32:39.717071',NULL,NULL,NULL);
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
INSERT INTO `instance_info` VALUES ('e6b1355e-a85f-44f5-87bc-3c8b20fc836b');
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `instigators`
--

LOCK TABLES `instigators` WRITE;
/*!40000 ALTER TABLE `instigators` DISABLE KEYS */;
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
  KEY `idx_job_tick_timestamp` (`job_origin_id`,`timestamp`),
  KEY `idx_tick_selector_timestamp` (`selector_id`,`timestamp`),
  KEY `ix_job_ticks_job_origin_id` (`job_origin_id`),
  KEY `idx_job_tick_status` (`job_origin_id`(32),`status`(32))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `job_ticks`
--

LOCK TABLES `job_ticks` WRITE;
/*!40000 ALTER TABLE `job_ticks` DISABLE KEYS */;
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `jobs`
--

LOCK TABLES `jobs` WRITE;
/*!40000 ALTER TABLE `jobs` DISABLE KEYS */;
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
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `run_tags`
--

LOCK TABLES `run_tags` WRITE;
/*!40000 ALTER TABLE `run_tags` DISABLE KEYS */;
INSERT INTO `run_tags` VALUES (1,'b2f62146-f2f9-4e21-816c-813d40face9b','.dagster/repository','upstream_assets_repository@dagster_test.toys.repo'),(2,'b2f62146-f2f9-4e21-816c-813d40face9b','dagster/step_selection','upstream_asset'),(3,'b2f62146-f2f9-4e21-816c-813d40face9b','.dagster/grpc_info','{\"host\": \"localhost\", \"socket\": \"/var/folders/lr/mcmhlx2177953tcj5m7v8l3h0000gn/T/tmpxpq1vx51\"}');
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
  KEY `idx_run_partitions` (`partition_set`(64),`partition`(64)),
  KEY `idx_run_range` (`status`(32),`update_timestamp`,`create_timestamp`),
  KEY `idx_run_status` (`status`(32)),
  CONSTRAINT `fk_runs_snapshot_id_snapshots_snapshot_id` FOREIGN KEY (`snapshot_id`) REFERENCES `snapshots` (`snapshot_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `runs`
--

LOCK TABLES `runs` WRITE;
/*!40000 ALTER TABLE `runs` DISABLE KEYS */;
INSERT INTO `runs` VALUES (1,'b2f62146-f2f9-4e21-816c-813d40face9b','be10d19e5c8d18d6b7adb5124f5bfa4746f41bbc','__ASSET_JOB',NULL,'SUCCESS','{\"__class__\": \"PipelineRun\", \"asset_selection\": {\"__frozenset__\": [{\"__class__\": \"AssetKey\", \"path\": [\"upstream_asset\"]}]}, \"execution_plan_snapshot_id\": \"5fda2f5076f6375c2f0e7bd89296103ade204651\", \"external_pipeline_origin\": {\"__class__\": \"ExternalPipelineOrigin\", \"external_repository_origin\": {\"__class__\": \"ExternalRepositoryOrigin\", \"repository_location_origin\": {\"__class__\": \"ManagedGrpcPythonEnvRepositoryLocationOrigin\", \"loadable_target_origin\": {\"__class__\": \"LoadableTargetOrigin\", \"attribute\": null, \"executable_path\": null, \"module_name\": \"dagster_test.toys.repo\", \"package_name\": null, \"python_file\": null, \"working_directory\": null}, \"location_name\": \"dagster_test.toys.repo\"}, \"repository_name\": \"upstream_assets_repository\"}, \"pipeline_name\": \"__ASSET_JOB\"}, \"has_repository_load_data\": false, \"mode\": \"default\", \"parent_run_id\": null, \"pipeline_code_origin\": {\"__class__\": \"PipelinePythonOrigin\", \"pipeline_name\": \"__ASSET_JOB\", \"repository_origin\": {\"__class__\": \"RepositoryPythonOrigin\", \"code_pointer\": {\"__class__\": \"ModuleCodePointer\", \"fn_name\": \"upstream_assets_repository\", \"module\": \"dagster_test.toys.repo\", \"working_directory\": \"/Users/claire/dagster\"}, \"container_context\": {}, \"container_image\": null, \"entry_point\": [\"dagster\"], \"executable_path\": \"/Users/claire/.virtualenvs/dagster-dev/bin/python\"}}, \"pipeline_name\": \"__ASSET_JOB\", \"pipeline_snapshot_id\": \"be10d19e5c8d18d6b7adb5124f5bfa4746f41bbc\", \"root_run_id\": null, \"run_config\": {}, \"run_id\": \"b2f62146-f2f9-4e21-816c-813d40face9b\", \"solid_selection\": null, \"solids_to_execute\": null, \"status\": {\"__enum__\": \"PipelineRunStatus.SUCCESS\"}, \"step_keys_to_execute\": null, \"tags\": {\".dagster/grpc_info\": \"{\\\"host\\\": \\\"localhost\\\", \\\"socket\\\": \\\"/var/folders/lr/mcmhlx2177953tcj5m7v8l3h0000gn/T/tmpxpq1vx51\\\"}\", \"dagster/step_selection\": \"upstream_asset\"}}',NULL,NULL,'2022-11-16 16:32:31.136468','2022-11-17 00:32:39.692435',1668645155.740731,1668645159.692435);
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
INSERT INTO `secondary_indexes` VALUES (1,'run_partitions','2022-11-16 16:32:16.471525','2022-11-16 16:32:16.465316'),(2,'run_repo_label_tags','2022-11-16 16:32:16.489310','2022-11-16 16:32:16.485745'),(3,'bulk_action_types','2022-11-16 16:32:16.523751','2022-11-16 16:32:16.519118'),(4,'run_start_end_overwritten','2022-11-16 16:32:16.576582','2022-11-16 16:32:16.571836'),(5,'asset_key_table','2022-11-16 16:32:16.833904','2022-11-16 16:32:16.828432'),(6,'asset_key_index_columns','2022-11-16 16:32:16.870300','2022-11-16 16:32:16.847210'),(7,'schedule_jobs_selector_id','2022-11-16 16:32:17.139400','2022-11-16 16:32:17.132622'),(8,'schedule_ticks_selector_id','2022-11-16 16:32:17.193070','2022-11-16 16:32:17.189040');
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
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `snapshots`
--

LOCK TABLES `snapshots` WRITE;
/*!40000 ALTER TABLE `snapshots` DISABLE KEYS */;
INSERT INTO `snapshots` VALUES (1,'be798c95a00e2f274e9cca79fe0502fc356f02b8',_binary 'xú\Ì]is\€\»˝+(\ÊCí*[\∆58\ˆõl\ÀY%é¥ei+ï≤T\=\"\÷ ¿\0†l∆•ˇûºDPCä§(GªeK sº~\›\”\›s¯G/äxBã\"äzøΩ\ﬂ\‚!$q\n)˝¨\ÏΩ2z<Ke|º\Z\Ì7ø?\Ê\ﬂ}Wïª®äÕæOì$j\ÎPGl}ÖqU¡q:\Ó™\Ër<¨∫°™P\<ñqñbÅtî$¯!§£AtKì\”eâòyæâo!çR:\0U≥j?¨[ü<≈©h:QUπ–á\‡\◊G\«gˇ\Ó\›aŸÇ”Ñ\ÊQ\ÛJ\”Fâ•¢!\Õ\È@ç´m\\?\Œs:>∫\Ë\”!πñ\0l\·3ü\€%ñi\"L&(|\€\·û\¬a\Î\„\—˚•ëIc£\Ê6B≤˘¨r\√vµêˇ\Ù\Èx-\Ï?\˜\÷\Ï\»\ıå§\ <No/Å∫ö\Ì!;©oWà\’\rTHºÕ≤d6m\›\⁄tºìGçq^º;˛x¸i\…@óΩuQï®\ﬁ{{~˛±z´[o?$\Ì¥p\€°nnä\¬\Ùyá0|¯x~|˘\0ß\ÈQPçM1hüvà¿\È\ŸC\„Øˇû\‚¿é5__@º\Ã\Ú#D+`NÅG]áip*âpKz\‹\˜-ãëpè≥€º\Â\ÿB\◊◊Ç?˙˝\Ï\Ù¸l=≥\”j˚˙]ª^îN•2\”1\n”§éN`˙\¬\Òy(Ωês\œCüªîHóZæÑ;!ûM˚æs˘L\Ï\–˙}ª\' \‘\Á\Èi\Ëá!}KX6\Â\‡õ\‘A`:<\èÁ∏ñ/L\ﬂ&!û\Õzæs\·4r˝û\›M=˚O\«¶´§PÑ°í5e∂eõû\Îf€∂\Îsâj\Z\ÿ\ﬁaÿ∂ç;øsMΩ∂\ı;WÀ®}\ÕbíYûOÅÜ¶òîz~HB¸\Õ\‰æ\≈D¿=\Ë\Ÿ\⁄;\»Á•ï~P_Okïtîî\—0\œnc\nô2¡\Ã7U\Ì-¢?ä,çä2W5˝∏\Î\ÏR\\D9¸g\ÁUeí&Ö™≠\ıD\\Pñ\‡W-\ˆ-3*\◊_P\'§\0èπ\ÃéMì C\‚ôVöT\n4`f®\‰yxcÉt+Cª~@á\÷&óÆ¬ú|<ywyæ\Ã{0^ût\ &>\∆k°¥(±q\\\ƒñe:∂\Â\  ékzæ\ƒ«Éb|+\»U¥hZ“†E√±)+n\Ô1¢60⁄í\÷uüív¿§¬ó4éThˇ∏P\ ,?`ü\Ô⁄∂´^(!(ÆTﬂØZΩÆû\Ó\ÓñXá\ﬁ\…w\‡£ö$FQ¬∞0\‚‘†FÅRN¿¿\ˆ9\≈Q\ÔAßQSxπq]iªîbíPP}{è£-\¡\·8∂M,æ[˚x\’\–\Ô*3\»Gyi©Ä1_õ\√î\˜+\‹*\ÿR¸[\ƒÿ£M\÷¿nÄéW¢\'-\◊q=.à>»ÄJ\ [\ÿaÜ\Ë˛˙ûÂÖÅ2__1µu`üä8V 	ïHa\‚ê(\·æ!Y\»\˜âögLO∞\‡˘)\Ê2\’’èr0\ >≥$0†¢WñeÜ\Ï¢yi#\÷|	Ö1R\Íi|ëY˛µÄ¸\Ú/\Z,õñ\Ó\–PÜAÇ\œlSH«≤=\?0\n6=SZ\Ã\rMaw\Ô\Ã\„Å*Ü\Ù[™ÉQUp_^ê6\€\˜©ÇO&†§\Í\Ë\‘á˘jãk;Å%îzp\"\œ\n¡√ê≥\–\Û=∞7÷òùék\ÛØ	¸å#´*[ò\ ]h´\Ê\÷S.\€P\Õ\'\Œˇæ®\Êãj\ÓF5´úº∂nn}-a∫˘\ƒ\…ˇ\›|\—\Õ\›\ËfΩ£≠ú[_H⁄Ür>\Ò\‚¬ãræ(\Ánîs\›l\Ï\÷™∂¢ùƒñ‘°™m\«!±\ÒTøTr*∂¯>\Ò\›\√\ ∆æh\Áìiß6\ŸuyµO≤K[Ç\'§\‡ûI≠\–\ıi \9Œï>5-õπæ\È\∆ˇèô^\»˛\‹F∂t*RõµUS[\ˆ°öïD\Ã¿rà\ÎyÖ\À…§∞8¿!Å\Ô9°eáˇv\‰A\È•NB˝™wz\ˆ\·¸™∑$≠~\Ÿ#\…nn ˇsaî˝ä~ñç,9æ%pIó?≤\√Ç´û†7E	y\ÁêT/’æ\Ëq6 õ\Òiå©˙π°{µÉt9}˘\È\Ù\›et\Ò\Î\Òo\'è‡µÑ¿!é\qm π§\"d¿ô`XhK\œ\rÅ±ê>;^ˇ∏ö\“P≠”∂<WãπJJ\ıgÆ,[VRdi\⁄0xñdH¸ôY˙º©Oô,7\Û⁄î\–dòÆ,\˜\ 0+`\ËXQiÅ\ƒ$é\ÔJ_\⁄Dr\ÊY H\»a\Î†∂\›˘qëåâ¯˛:keO.\–.qP\√÷îª6\¬{ïªMM$Öiv êÉæeqaõ¿\Õ¿‘µô∞ÄÇ˝¸fLµIdfâπ\Ÿ≤\·∆∫\Û∞\ˆ.=¶h\ÀdØL\Ÿ\›)¥gk!\–\◊\¬J;i°∫\Í\—b\€\Á\„∂D\›a?-züﬂü¸\ˆ\È\‰\›\Ò\Â\…˚kç-a4ˇ\nyTf\ÿ≈¨\Ë\ÙLwªWn~\‹\Í_}(˚ê\Õ\Ó9É\Ê`4/Yn§Yydº∑N÷´e\Â4\\¨\Ê≠Nm\—\ﬁM¨©-∫º‹ª∂P\ﬂr<üò>a°\È°#\‡Ñ∂ms\◊¡®\Ÿ\ÒBÎ∞å\ËN\˜¨Ø\Úºµ]&}JhÅø_J\ËfëâªÕπ—≤ˇ® ^\“}Zog\ÊO!\Ë\ﬁ\…\˜a\Û∏L\∆F1\ÀqΩ\Ô3£\'è23Ü9$jœµ˙f∫≥\ı\»8W“∑X5≠~ÉjÆ)øeßjC(ù\ƒ¸\ıÄçXN™Veq\“jöçqv2Ne\’\ƒ˚:ë`¸ë1\„-\’<Nr2\œmﬁØZ4\nï~™?0æ\≈Ib0h˚\€‘á-\‘Eø4\Èâ/m˘∏ò)˙\\ƒÿîçö\Ó\ﬂK\…\Œ\‰\◊\Êø\”\ˆ\ \ﬂ•+\€ra–êKãJóU˚\Ú\Œ\Õˇò\Ô\ÌÄˇMbEú™\Íl®~\ˆä,âQ1\Ó\ˆé\÷3]s6\·^l∫ŸôÜ•˛\‹t£u?˚\÷©|µ˙¥É@Bó˝\Í|H>J5Zøw-\há´O∏\„\\Q\'qiwzÉ\∆bM,öJñ#AH0\Œ\Ñ	\ı,\\\Ó{\“u©Môo°4π≤]{¸£!˛®áX=î›éˇ|£≈´\‘Jì≤±®**®™\—9£Tk)2ú\‚r\‘t\r≥8Ñpvë3vP¸c;\Ê\»U/Œ¢MQ\y£O3J©•L}™\Ú\À¯W\ÈøZØ\‚¡0Å\Í\Ï˙™5©h9l!ò&s)	VH\Í\ÿ\¬A\◊\’!Æ\…m¸(0\»\—N,i[\‡Ω\Œ⁄É<$øh}õøî]oGqRæF\¬\»ß˛1\⁄\ÍÅqzn4E\˜Ç¢É—±bZ*ö\»˚ü\ZØß>S-R\„/:¸&\n–±¶≠#\È1N[∂{eú∂5˙)=ëM#\ı˘Y•cT«É\…e(≠¿£\ÒB¶\Ú,~(8∑¿ì«à&}¥µW˙hü!€ë¡“ÇNªì{ÖNõ\œM\Ûvª–∞<IVm\÷9à≠E\˜¸¿Q9ï]°\Ïz´zñBõX˚•ªn@pHÆ\ÕŒ©¨∂ftlµ\–\›°I\n]¯\˜J\n\Ì[\0â:ûÖŸµïk4`\Ë\Ãf≤ΩLA•ˇîg;†c\'”¨G2û_j\¬`™P˘4t8T∆ê\’g\«\—\r\Âi\Ì´jø\ÃfSîÃá£àg\”˛\ÂØ:\Á\≈\Á3/ã‘¨éúæ,—≠µD∑\ÔY©\Èc£\œ^†\0\‡Ëµñ*k;ãPsõ@M.\ıÆ*p\Êó\Â∞¯\Â\Õë\Ò\‚h8.˚Yzî\Â7oú7I\Ãröè\ﬂ,≤≠_í?!J¯^Ø1N{]\›a\zÄ2ÀÑNﬁ§*\’\Â;\—◊æh@\œ8jõ°}\«Mo\–\Ì=h\Úö\Á˘KCgÆ∆ù[b\“\ÓÜWá*ò\Œ˛\ˆ\–\Ì°ã[ÃûÏæº≈é¨ÖŒñ\Óæ”æ}\Í˙\ÓNµ’¨\«DU\ıjX®\ÍV\‹?\ﬁ,©ﬁüµ\≈\Ô!ü´T\Ô6\ÚôjW\nI\ƒ\≈0°\„≈ª\∆\—d0ïä\”\ÈD¢qˇ¯L´sêW\ÎQy{˚c\ˆ\Ú–ö\Ê1ÜSˇ\ÌÆoùc;\„^¬ä\◊Ko\nr{É\Ï\nîW^)Ω\Ûå=Xé\ÙVn\’\›\Ù\ÌPª∞\Ô∏\÷zS\\'\◊√Æ@\ıU÷èÅˇ∑\Ê\Ó\nˇ\…`ª∞\Ù>\ÌM\·o.Ä]˛™;¥˝\∆7\‚\Ó\n¯\”t%\ÏgôZ\ŒY\‚ïl\n}[\·j¯gJiâ\‡\Ï¸\Ú\◊÷´X&É¶3\› 6ñ\Ù≤ô.wmS`¶\Û˛\n\\p\—\√\Ã\«\‹º+rNáªT\nµ≥Cç8Ü\ƒ+}B* \Â„ã∂\Ù¨ãSeB£8Ω\Õ8UÇ™k\Í\›O\\®Çßìr≠å\„t8*£™3\Ìã◊µ,\≈á\Ûh@á√π\‡ßn≤®{Ö°.≥b%^\Õ\◊w]Lª\…\È∞?\◊N_\\ú\\F?´*Qˇl\rΩôØUòL@\ıf\Zˇ\ƒ\ÔAÆdzΩe`e5´\"3\’	ﬂ®N\\´∑∫\"ÄóCXãá∞6\Ó\‹bÜ≤\n£\'\◊F\◊\Ô´r\Ìö˝Jâ~j\n=ôLüv?\Ó}!\Ï`•{…öv%≥<\À\ \ˆﬂç\⁄lˇ√ú\Ë¨\≈\ƒl\≈i¨W¨0∫ï±|?-:ˇèc\rÜYóhw&Üp\Œv.˘∏£˙≠3\Ï	W≥:*l¶óà∫\'Üzj%z\ÁUëY\Î=\‚\œG\⁄]£l&∑ôAÆ\‹\Ÿ\‹™Y⁄îä&\ˆd2≥ﬂüÿ¶èˇ˘\Ë\–\«','PIPELINE'),(2,'be10d19e5c8d18d6b7adb5124f5bfa4746f41bbc',_binary 'xú\Ì]˚s\€\∆˛W0\ÏmgbØp˘M∂\ÂFç+e,e:ùH\ﬂcOD,\0\ f<˙ﬂªÄO‘ë\")\ŸU2∂\Úpèoø\›\€\›{¯k/éE\ \ 2é{?ZΩ_í!§Iñ˝º\Í˝`\ıDû©\‰&.E,.\'\ﬂ¸h}]|\˜m]\Ó¢.6ˇ>K\”xRá˛8\Ê\„¯\◊g„Æä.\«√∫∫\n	•(íaï\‰\»FiäB6\Zƒ∑,A9˚P%ê π\Áõ\‰≤8c\–5\Î\Ê\√¶\ı\ÈSí…∂uïK}¯ø>:>˚O\ÔÀñÇ•¨à\€W\⁄6*,Y¡z\\ì\∆u\Ò\„¢`„£ã>¬ë\ÔH∞¡ï!	q}\‚\ÿ!\“\Êí\Ò(t=( =æ9ΩIYYπ≤∂jn+$\€\œ&@nŸÆ\Ú?oÑ˝oΩ\r;r=\'©™H≤õ\«K†©fw\»N\Î\€bM5o\Ú<\›Å\ÌF€¥6\Ô\Ù\—`úoè?\\1\–Uo]\‘%\Í\˜ﬁúü®\ﬂ\Í\÷\€\˜i\Œ:-\‹\ÓAhöõ°0{\ﬁ#\Ô?ú_>Ä\√iv@tc3&O{D\‡\Ù\Ï°\Ò7Ö\Õp`GööØ. Q\Â\≈\"âqèB0\ﬂDπ\0Ç)\‚E\¬QÅC\«\·Ñpv[¥;\Ë˙F\«øûùûümfv&⁄æy◊Æó•S´\Ãlå“∂ôÇŸ°\ÙBAU@Ö\\JC\·3¢|\ÊÑ\·=\Òl\€\˜Ω\Àgjá6\Ô\€=°>œÜ\»hH)ß°#ó	m\Ê\ (≤=E¯\'\|\'îv\Ëíg!û\Ìzæw\·¥r\Ûû\›M3˚\œ\∆∂Ø$*)’≤f\‹u\\;\=\¬]\◊\ıC°PM#7x∂m\Î\Œ\Ô]@3Øm\Û\Œ52öº\Êp≈ù d¿®F6cAH	\≈\ﬂl:\\F\" Äû≠ª\'Å¸∂≤\“\˜˙\ÎY≠äç\“*˘m\"A#S#ò˚¶Æ=fe¸{ôgqY∫¶Øwù]J ∏Äˇéí¢ÆL±¥‘µM|ôîåß¯\’˚	3j\◊_2è2Ä@¿}nK\œ%Ñ+Pî∂Qõ)âÃ¶Zû\œolê\Ìdh\◊\Ë\–\∆\‰2Uòì\'o/\œW˘c\∆\À\”Nπ$\ƒxç*á\«E<\È8∂\Á:>a\¬\‚˘v*||Våür-⁄ñh\—rl∆ä\€{åhå±§çA=§§=∞ôï\«\0ç#S\⁄?\·Dåâ(\'å∏$\‰$¯m\€UØ\0îîW∫\ÔWΩÆü\Ó\ÓVXá\ﬁ\…£\n,ñ¶VY¡∞¥í\ÃbVâRN¡\¬\ˆî\ÂQ\ÔAídq[xµ\Ò}\Â˙Lb*ôÉæDà} \–Ñ`É\Ù<\◊%éÿØ}º\Í\r\ÿù£¢Ä¨\“¿\ÿ?X\€\√L\Ùk\‹j\ÿ2¸[&ÿ£K7¿nÄN÷¢ß\ﬂ\Û!âî!®à)\∆=W∫4¢\›\ﬂ0p\ZŸîá\Êäi¨áT\Ã\»s\"EòBZHáƒàH\≈)ó\"$zû±…£oO1Wq®©~TÄU\ı¡ö\'Å5Ω\Ú¬™rd+*´\Ò\ˆK(≠ëVO\Îì ã?J(n°¯d¿≤Y\È\r\ÂD!¯‹µ•\Ú7\0ˇ£`;∞ï\√}jKõ¯\˜`T9dü3åÍÇá\ÚÇå\Ÿ~H|\‚0˘zA∫éNç\ÒxË°∂¯Æ9R´á \ ú»ìÇR¡i\‡n≠1{\◊0§\=é¨Æly`:wa¨ö;Oπ\ÏB5ü8ˇ˚¢ö/™π’¨s\Ú∆∫π\ÛµÑ]\Ë\Ê\'ˇ_t\ÛE7\˜£õ\Õzå±r\Ó|!i\ ˘ƒã/\ ˘¢ú˚Q\ŒM≥±;_®⁄âvW1è\È∂=GR\‚\‚#\Ë~\È\‰ïÆÖ!	˝Áïç}\—\Œ\'\”Nc≤õ\Ú\ÍêdWÆÇ@*)õ9\‘Y§\"Œï!≥ó˚°.˛èô^\»˛≠çl\ÂT§76´¶±B5kâÿë\„?<N•\œ#≈ïtè¿#Qx\‘q)¡ø=\ı¨\Ù\“$°~\’;={~\’[ëVøÏÉï\Ê77P¸µ¥™~e?O•Añ_äS∏Ö¥\À\Ÿ\„¡UO≤õ≤Ç¢sH∫óz_\Ù8\Ì¯\∆Tˇ\‹“Ω⁄åA¶úæ¸x˙\ˆ2æ¯\È¯óìG\ZA\‰Oú¯.B1I9.9N]¯8ß\Ïõ\„\ı◊´\r\ı:\ÌÑ\Áz1WK©˘l ïU\ÀJö,mñ\»\”âÅ?≥2O¡ú7\Õ)ì\’fﬁòÜ3ï\ÂA\ÊD+¶Pí\ÿ\ƒ}*ó(¡$°\\qû\√v;?.sÇ≥bô\‹_g≠\Ì\…\⁄%zÿÜr7F¯†rwôçÅ§¥ù»ç$r0t!]ÑŸí˘.ó0pøΩSoô[bn7Ålπ±Æ\√<lº√å)\∆29(S\ˆw\nÌõµ\Ëka•ù¥0]\Õh±\Î\Ûq;¢ÖÈé∞\ÔÇΩ\ﬂﬁù¸\Ú\Ò\‰\Ì\Ò\Â…ªkÉ-a¨¯ä∏ ±ãy\Ÿ\Èô\ÓwØ\‹\‚6∏‘ø˚P\ı°∞\⁄\›s+¿j_≤\Ú\¬\ \Ú\Í\»z3û8Y?¨*g\‡bµoujã\ÒnbCm1\Â\Â¡µÖÖéÑ\ƒAJ˝\»\0è∫Æ+|£f/†\Œ\Û2¢{›≥æ\Œ\Û6vô\Ã)a˛a)aöEzNî\ÿoŒçU˝G\Ò∆êZ\–f;3øA\˜Næ\”D$U:∂\ !àDçõ}üπ•8yTπ5, Õô\‘{Æ\ı7≥ù≠G÷πûê>\'∫i˝\‘sM\ı9∑\”B±\Ë4\Êol%jZµ.ãìV\€lÇ≥ìu™\Í&\ﬁ5â\Î\˜ú[üYi\È\ÊqíSE>∞X˚~›¢U\Í\ÙS\ÛÅ\ı9ISã√§øm}\ÿBS\ÙSõû¯4)üîsEû€≤q\€˝{)\Ÿ˘É¸\∆¸7c\⁄A˘T˘2r?\¬\rπrò\ÚyΩ/è\„\‹,\Òˇàá¡¯≥4\—ƒ©´Œá˙gØ\Ã\”\„\Ó`\·h3”µg\Ó≈¶€ùiX\È\œ\Õ6Z\˜\Û\œ\Ìqê\⁄WkN;H$t’Øœá£ÃÄ†\Õ{I\◊èq∏˙Ñ;\Œ5M2∞¥`êT\÷\0qg7h,6ƒ¢≠d5QÇq@ mP®gQ\‰ã0Pæ\œ\\\∆C;¢\ >\Â˚\ˆ¯GC¸P±z®∫ˇ>8¯*AãW´/T\Z&mcQUtPWcrF´\÷Jd#\ƒD®\È\Z\"\Ó†\npv¶\»7ä˛q¢=s‰™ó\‰\ÒÄe(¯¢’ß9•4R¶>\”˘e¸\Î\Ù_£W\…`ò\¬\0uvs’öV¥\Z6\n∂\Õ=O\…HÅCI\ƒ<Wz\Ë∫zƒ∑ÖãE9∆â%c|\–y¡xê\œ\…/\⁄\‹\ÊØd◊õQíVØê0*¡©å∂z`ùû[-G—Ω`\Ë\∆`t¨ôñ\…6\Úæ≈ß\÷\ÎiN\∆‘ã\‘¯ã\…ø©t¨iõ\∆Hfå3ñ\ÌAglçæKOd\€H}qV\Èò\ı\Ò`O	Eï, \Â:\œR)ÑÅba8F\Èc,®É\“\«¯Ÿûñt∆ù<(t\∆¸¯\÷4oø\r´ìd\ıfùg±µ\Ëû8™Ü£™+î\›l5\√\ÃR\Î∞t7\rûìk≥w*\Î≠[-L\˜Fí\¬˛Éí\¬¯Ä\ÁD\n\œ\¬\Ó\⁄\ 5\Zptfs5πLAßˇ¥g;`c\'Y≥¨G:^\\j\¬`™\‘˘4t8t∆ê7g\«\—\rY\„\Îj?\ÕgS¥,Ü£X\‰\”˛\Ì\Ô&\Á\≈3/\À‘¨èúæ,\—m¥Dw\ËY©\Ìc£\œ_†\ËµV:k;èP{õ@C.˝Æ.p\ÊW’∞¸\Ò\ıkôã\Úh8Æ˙yvî7ØΩ\◊i\¬Vå_/≥≠_\r“ø *¯RïØ0N{U\ﬂa\jÄ2À•Iﬁ§.7\Â;\—7æh¿\Ã8\Zõ°C\«mo\–\Ì=h\Ú\⁄\Á\≈KC\ÁÆ\∆]Xb2\ÓñWájò\Œ˛\Ò\–\Ì°\À[ÃûÏæº\ÂélÑŒé\Óæ3æ}\Í˙\ÓN∑’Æ\«\ƒu\ızX®\Í\÷\‹?\ﬁ.\ÈﬁüMä/\ﬂCæP©\Ÿm\‰s’ÆíL\ a\ \∆\Àwç£\…\‡:=îd≥â\ƒ\‡˛\ÒπV. Ø◊£ä\…e\Ïè\Ÿ\À?@kZ$N˝\Ÿ]\ﬂ&\«vñ∆ΩÇkÆó\ﬁ\‰\…\r≤kP^{•\Ù2\Ãs\ˆ`5\“;πUw_\–OÜ⁄Ö}«µ\÷€Ç?Ωv\r˙ÎØ≤~¸è∏5w_¯O\€%Äï\˜io{\Ï\Z\\◊›°˝Ë∑æw_¿üfka?\À\ır\Œ\nØd[\Ë\'ÆáÆîë\Œ\Œ/öx´d\–v¶ƒ∂¿ä^v!\”\ÂÆm\Ãl\ﬁ_É\À.\⁄cò˘ò€Ä\˜E\Œ\ŸpWJ°qv`®£ë¿êx≠èC\»$db|1)=\Ô\‚‘ô\–8\…ns¡¥†ööz\˜\”∫\‡\È¥\‹D\∆I6Uq›ô…ã◊ç,\Âáìàx¿Ü√Ö\‡ßi≤∏{Ö°)≥f%\ﬁ\Õ\◊w]Lª)ÿ∞ø\–N_\\ú\\\∆ˇ<£+\—ˇl\rªY\ﬁ\Ú?n\Û°y£\ˆ\ruW\‚&Ñlö\’\Ô™\"ˇ2˝Mº\√c˝\Œ\œP{;\ıf7\Ì¯.\r\Ó∫\ ≤j⁄µ8\—\ˆ8Ñ4î0\€Wπ°8e±ê*∞â\Ì*\·ë@\Ÿns\Á\\\·|[\\ö\‰∑ﬁú\‹nô@πÑ\Z≤.\Z¸ºµV≈õΩk´˘Pô´®\…t\«M\∆^ø\’˙ºú>[>}∂u\ÁñS≥u˛`z_v\Ûæ.7Ÿ¨∞V¢\€BO&”ß›à|_{X\‚_±ò_À¨\»\—B¥ho∑\ÒcA\ÙKfrjØì,—É+\◊\Ãzñx7+∫¯ØÇ\rÜyôThpß3¿¬§±\‚\„é\ÍwŒ∞\'\\\∆Î®∞ùWó \Íûõ•∑µ\Ëù\◊E\Ê≠\˜|nc1\≈\–5\ vVü\‰\⁄-\›\ÌI©Ü•m©xjO¶.\Õ˝}\ˆ¯?I%=','PIPELINE'),(3,'5fda2f5076f6375c2f0e7bd89296103ade204651',_binary 'xúµS¡n\€0˝ï\¬\Áaòá§\Ìv+ÜÇ°≤ùÇÄê-∫*KöDwsÉ¸˚H[q∫§\ŸmGë|O\‰\„\„Æ\0®≠J	†¯|U\‹ˇ∆∫#\„\›\“*∑r*§≠ß\‚\›U°\"ôF’î `L&jÆß\ÿ!\'q@˘Nµ(4mg\…\0åÉ}ç\Ã(6\„e\·\…˘_)\ÿ\Ó\Ô^íú\ZZ\rEå\’=ˇbjhU\∆=&\Ó9TDGôÎ¨ïh\ƒg\„ª)\ˆ†à∞\r4Å\"*›É\Ô(tcê[h¢AóêÜ6\÷©\„yC.Ég¿ª4%É	hçCHY00\"NQa˘Aóüp^\ﬂ\Í\ÚV_W7JW\Û\Ú„¨ôWçö\›ÃÆõYYUµL5A3;\„\À√øO\ÿ\' üî\·\÷Eq\Û-∞\\H\≈&\◊M\Ì.\Ït\≈≤\”qy\‚µ@˘©<!ïÑq:ÀÇÆkGB\·Yp\‚˝óáo\À\ﬂ\Ô°ERZë\√\nO\ƒGeˇ\Ÿ\’\√Pv\ËM´Gû%\ı!∑v\ÁzI1±≈äa¡ûI”πÉé\‘\ÀcïòY\∆\À\Ã\'ê;I-p¯,(⁄æ)∂\ÃkR~MW¿ë\ÏMé5 ¶å¯≥3\Ò\ıΩ\¢;´\Ÿ¡<%üÅy¡b\ö∑F\√V9mﬂ∏äïdøé\…WÇúØnºá|	˚˝\ÊÑ9{\Ù7X\Ó\‚\Ôú<~~\—6ˇgéê\ ø\ﬂ\Ïˇ\0\”C°ß','EXECUTION_PLAN');
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

-- Dump completed on 2022-11-16 16:36:08
