-- MySQL dump 10.13  Distrib 9.1.0, for macos14 (arm64)
--
-- Host: localhost    Database: test
-- ------------------------------------------------------
-- Server version	9.1.0

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
INSERT INTO `alembic_version` VALUES ('284a732df317');
/*!40000 ALTER TABLE `alembic_version` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `asset_check_executions`
--

DROP TABLE IF EXISTS `asset_check_executions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `asset_check_executions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `asset_key` text,
  `check_name` text,
  `partition` text,
  `run_id` varchar(255) DEFAULT NULL,
  `execution_status` varchar(255) DEFAULT NULL,
  `evaluation_event` text,
  `evaluation_event_timestamp` datetime(6) DEFAULT NULL,
  `evaluation_event_storage_id` bigint DEFAULT NULL,
  `materialization_event_storage_id` bigint DEFAULT NULL,
  `create_timestamp` datetime(6) DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_asset_check_executions_unique` (`asset_key`(64),`check_name`(64),`run_id`,`partition`(64)),
  KEY `idx_asset_check_executions` (`asset_key`(64),`check_name`(64),`materialization_event_storage_id`,`partition`(64))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `asset_check_executions`
--

LOCK TABLES `asset_check_executions` WRITE;
/*!40000 ALTER TABLE `asset_check_executions` DISABLE KEYS */;
/*!40000 ALTER TABLE `asset_check_executions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `asset_daemon_asset_evaluations`
--

DROP TABLE IF EXISTS `asset_daemon_asset_evaluations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `asset_daemon_asset_evaluations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `evaluation_id` bigint DEFAULT NULL,
  `asset_key` text,
  `asset_evaluation_body` text,
  `num_requested` int DEFAULT NULL,
  `num_skipped` int DEFAULT NULL,
  `num_discarded` int DEFAULT NULL,
  `create_timestamp` datetime(6) DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_asset_daemon_asset_evaluations_asset_key_evaluation_id` (`asset_key`(64),`evaluation_id`),
  KEY `ix_asset_daemon_asset_evaluations_evaluation_id` (`evaluation_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `asset_daemon_asset_evaluations`
--

LOCK TABLES `asset_daemon_asset_evaluations` WRITE;
/*!40000 ALTER TABLE `asset_daemon_asset_evaluations` DISABLE KEYS */;
/*!40000 ALTER TABLE `asset_daemon_asset_evaluations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `asset_event_tags`
--

DROP TABLE IF EXISTS `asset_event_tags`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `asset_event_tags` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `event_id` bigint DEFAULT NULL,
  `asset_key` text NOT NULL,
  `key` text NOT NULL,
  `value` text,
  `event_timestamp` timestamp(6) NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_asset_event_tags_event_id` (`event_id`),
  KEY `idx_asset_event_tags` (`asset_key`(64),`key`(64),`value`(64))
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `asset_event_tags`
--

LOCK TABLES `asset_event_tags` WRITE;
/*!40000 ALTER TABLE `asset_event_tags` DISABLE KEYS */;
INSERT INTO `asset_event_tags` VALUES (1,14,'[\"not_partitioned\"]','dagster/data_version','2f1b54df025779ce37abfdac7c0370f8467406c8138a2738b88e012384b4a7ce','2024-10-21 18:17:34.094080');
/*!40000 ALTER TABLE `asset_event_tags` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `asset_keys`
--

DROP TABLE IF EXISTS `asset_keys`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `asset_keys` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `asset_key` varchar(512) DEFAULT NULL,
  `last_materialization` longtext,
  `last_run_id` varchar(255) DEFAULT NULL,
  `asset_details` text,
  `wipe_timestamp` timestamp(6) NULL DEFAULT NULL,
  `last_materialization_timestamp` timestamp(6) NULL DEFAULT NULL,
  `tags` text,
  `create_timestamp` datetime(6) DEFAULT CURRENT_TIMESTAMP(6),
  `cached_status_data` text,
  PRIMARY KEY (`id`),
  UNIQUE KEY `asset_key` (`asset_key`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `asset_keys`
--

LOCK TABLES `asset_keys` WRITE;
/*!40000 ALTER TABLE `asset_keys` DISABLE KEYS */;
INSERT INTO `asset_keys` VALUES (1,'[\"not_partitioned\"]','{\"__class__\": \"EventLogRecord\", \"event_log_entry\": {\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"StepMaterializationData\", \"asset_lineage\": [], \"materialization\": {\"__class__\": \"AssetMaterialization\", \"asset_key\": {\"__class__\": \"AssetKey\", \"path\": [\"not_partitioned\"]}, \"description\": null, \"metadata_entries\": [{\"__class__\": \"EventMetadataEntry\", \"description\": null, \"entry_data\": {\"__class__\": \"PathMetadataEntryData\", \"path\": \"/Users/jamie/temp_dagster_home/storage/not_partitioned\"}, \"label\": \"path\"}], \"partition\": null, \"tags\": {\"dagster/code_version\": \"c18f0585-c495-415f-8f2c-4a446e92a05a\", \"dagster/data_version\": \"2f1b54df025779ce37abfdac7c0370f8467406c8138a2738b88e012384b4a7ce\"}}}, \"event_type_value\": \"ASSET_MATERIALIZATION\", \"logging_tags\": {\"job_name\": \"__ASSET_JOB\", \"op_name\": \"not_partitioned\", \"resource_fn_name\": \"None\", \"resource_name\": \"None\", \"run_id\": \"c18f0585-c495-415f-8f2c-4a446e92a05a\", \"step_key\": \"not_partitioned\"}, \"message\": \"Materialized value not_partitioned.\", \"pid\": 40638, \"pipeline_name\": \"__ASSET_JOB\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"not_partitioned\", \"parent\": null}, \"step_handle\": {\"__class__\": \"StepHandle\", \"key\": \"not_partitioned\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"not_partitioned\", \"parent\": null}}, \"step_key\": \"not_partitioned\", \"step_kind_value\": \"COMPUTE\"}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"c18f0585-c495-415f-8f2c-4a446e92a05a\", \"step_key\": \"not_partitioned\", \"timestamp\": 1729520254.09408, \"user_message\": \"Materialized value not_partitioned.\"}, \"storage_id\": 14}','c18f0585-c495-415f-8f2c-4a446e92a05a',NULL,NULL,'2024-10-21 18:17:34.094080',NULL,'2024-10-21 10:17:29.507021',NULL);
/*!40000 ALTER TABLE `asset_keys` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bulk_actions`
--

DROP TABLE IF EXISTS `bulk_actions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bulk_actions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `key` varchar(32) NOT NULL,
  `status` varchar(255) NOT NULL,
  `timestamp` timestamp(6) NOT NULL,
  `body` text,
  `action_type` varchar(32) DEFAULT NULL,
  `selector_id` text,
  PRIMARY KEY (`id`),
  UNIQUE KEY `key` (`key`),
  KEY `idx_bulk_actions_status` (`status`(32)),
  KEY `idx_bulk_actions_action_type` (`action_type`),
  KEY `idx_bulk_actions_selector_id` (`selector_id`(64)),
  KEY `idx_bulk_actions` (`key`)
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
-- Table structure for table `concurrency_limits`
--

DROP TABLE IF EXISTS `concurrency_limits`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `concurrency_limits` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `concurrency_key` varchar(512) NOT NULL,
  `limit` int NOT NULL,
  `update_timestamp` datetime(6) DEFAULT CURRENT_TIMESTAMP(6),
  `create_timestamp` datetime(6) DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `concurrency_key` (`concurrency_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `concurrency_limits`
--

LOCK TABLES `concurrency_limits` WRITE;
/*!40000 ALTER TABLE `concurrency_limits` DISABLE KEYS */;
/*!40000 ALTER TABLE `concurrency_limits` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `concurrency_slots`
--

DROP TABLE IF EXISTS `concurrency_slots`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `concurrency_slots` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `concurrency_key` text NOT NULL,
  `run_id` text,
  `step_key` text,
  `deleted` tinyint(1) NOT NULL,
  `create_timestamp` datetime(6) DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `concurrency_slots`
--

LOCK TABLES `concurrency_slots` WRITE;
/*!40000 ALTER TABLE `concurrency_slots` DISABLE KEYS */;
/*!40000 ALTER TABLE `concurrency_slots` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `daemon_heartbeats`
--

DROP TABLE IF EXISTS `daemon_heartbeats`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `daemon_heartbeats` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `daemon_type` varchar(255) NOT NULL,
  `daemon_id` varchar(255) DEFAULT NULL,
  `timestamp` timestamp(6) NOT NULL,
  `body` text,
  PRIMARY KEY (`id`),
  UNIQUE KEY `daemon_type` (`daemon_type`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `daemon_heartbeats`
--

LOCK TABLES `daemon_heartbeats` WRITE;
/*!40000 ALTER TABLE `daemon_heartbeats` DISABLE KEYS */;
INSERT INTO `daemon_heartbeats` VALUES (1,'SENSOR','520ae364-0f49-47de-9435-d1b7b544651b','2024-10-21 18:17:55.763635','{\"__class__\": \"DaemonHeartbeat\", \"daemon_id\": \"520ae364-0f49-47de-9435-d1b7b544651b\", \"daemon_type\": \"SENSOR\", \"errors\": [], \"timestamp\": 1729520275.763635}'),(2,'ASSET','520ae364-0f49-47de-9435-d1b7b544651b','2024-10-21 18:17:55.765283','{\"__class__\": \"DaemonHeartbeat\", \"daemon_id\": \"520ae364-0f49-47de-9435-d1b7b544651b\", \"daemon_type\": \"ASSET\", \"errors\": [], \"timestamp\": 1729520275.765283}'),(3,'BACKFILL','520ae364-0f49-47de-9435-d1b7b544651b','2024-10-21 18:17:56.514416','{\"__class__\": \"DaemonHeartbeat\", \"daemon_id\": \"520ae364-0f49-47de-9435-d1b7b544651b\", \"daemon_type\": \"BACKFILL\", \"errors\": [], \"timestamp\": 1729520276.514416}'),(4,'SCHEDULER','520ae364-0f49-47de-9435-d1b7b544651b','2024-10-21 18:18:00.001298','{\"__class__\": \"DaemonHeartbeat\", \"daemon_id\": \"520ae364-0f49-47de-9435-d1b7b544651b\", \"daemon_type\": \"SCHEDULER\", \"errors\": [], \"timestamp\": 1729520280.001298}');
/*!40000 ALTER TABLE `daemon_heartbeats` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `dynamic_partitions`
--

DROP TABLE IF EXISTS `dynamic_partitions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dynamic_partitions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `partitions_def_name` text NOT NULL,
  `partition` text NOT NULL,
  `create_timestamp` datetime(6) DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_dynamic_partitions` (`partitions_def_name`(64),`partition`(64))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dynamic_partitions`
--

LOCK TABLES `dynamic_partitions` WRITE;
/*!40000 ALTER TABLE `dynamic_partitions` DISABLE KEYS */;
/*!40000 ALTER TABLE `dynamic_partitions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `event_logs`
--

DROP TABLE IF EXISTS `event_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `event_logs` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `run_id` varchar(255) DEFAULT NULL,
  `event` longtext NOT NULL,
  `dagster_event_type` text,
  `timestamp` timestamp(6) NULL DEFAULT NULL,
  `step_key` text,
  `asset_key` text,
  `partition` text,
  PRIMARY KEY (`id`),
  KEY `idx_events_by_asset_partition` (`asset_key`(64),`dagster_event_type`(64),`partition`(64),`id`),
  KEY `idx_events_by_run_id` (`run_id`(64),`id`),
  KEY `idx_event_type` (`dagster_event_type`(64),`id`),
  KEY `idx_events_by_asset` (`asset_key`(64),`dagster_event_type`(64),`id`),
  KEY `idx_step_key` (`step_key`(32))
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `event_logs`
--

LOCK TABLES `event_logs` WRITE;
/*!40000 ALTER TABLE `event_logs` DISABLE KEYS */;
INSERT INTO `event_logs` VALUES (1,'c18f0585-c495-415f-8f2c-4a446e92a05a','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"AssetMaterializationPlannedData\", \"asset_key\": {\"__class__\": \"AssetKey\", \"path\": [\"not_partitioned\"]}, \"partition\": null, \"partitions_subset\": null}, \"event_type_value\": \"ASSET_MATERIALIZATION_PLANNED\", \"logging_tags\": {}, \"message\": \"__ASSET_JOB intends to materialize asset [\\\"not_partitioned\\\"]\", \"pid\": null, \"pipeline_name\": \"__ASSET_JOB\", \"solid_handle\": null, \"step_handle\": null, \"step_key\": \"not_partitioned\", \"step_kind_value\": null}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"c18f0585-c495-415f-8f2c-4a446e92a05a\", \"step_key\": \"not_partitioned\", \"timestamp\": 1729520249.504714, \"user_message\": \"\"}','ASSET_MATERIALIZATION_PLANNED','2024-10-21 18:17:29.504714','not_partitioned','[\"not_partitioned\"]',NULL),(2,'c18f0585-c495-415f-8f2c-4a446e92a05a','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": null, \"event_type_value\": \"PIPELINE_STARTING\", \"logging_tags\": {}, \"message\": null, \"pid\": null, \"pipeline_name\": \"__ASSET_JOB\", \"solid_handle\": null, \"step_handle\": null, \"step_key\": null, \"step_kind_value\": null}, \"error_info\": null, \"level\": 20, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"c18f0585-c495-415f-8f2c-4a446e92a05a\", \"step_key\": null, \"timestamp\": 1729520249.513546, \"user_message\": \"\"}','PIPELINE_STARTING','2024-10-21 18:17:29.513546',NULL,NULL,NULL),(3,'c18f0585-c495-415f-8f2c-4a446e92a05a','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"EngineEventData\", \"error\": null, \"marker_end\": null, \"marker_start\": null, \"metadata_entries\": [{\"__class__\": \"EventMetadataEntry\", \"description\": null, \"entry_data\": {\"__class__\": \"TextMetadataEntryData\", \"text\": \"40632\"}, \"label\": \"pid\"}]}, \"event_type_value\": \"ENGINE_EVENT\", \"logging_tags\": {}, \"message\": \"Started process for run (pid: 40632).\", \"pid\": null, \"pipeline_name\": \"__ASSET_JOB\", \"solid_handle\": null, \"step_handle\": null, \"step_key\": null, \"step_kind_value\": null}, \"error_info\": null, \"level\": 20, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"c18f0585-c495-415f-8f2c-4a446e92a05a\", \"step_key\": null, \"timestamp\": 1729520252.595465, \"user_message\": \"\"}','ENGINE_EVENT','2024-10-21 18:17:32.595465',NULL,NULL,NULL),(4,'c18f0585-c495-415f-8f2c-4a446e92a05a','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": null, \"event_type_value\": \"PIPELINE_START\", \"logging_tags\": {}, \"message\": \"Started execution of run for \\\"__ASSET_JOB\\\".\", \"pid\": 40632, \"pipeline_name\": \"__ASSET_JOB\", \"solid_handle\": null, \"step_handle\": null, \"step_key\": null, \"step_kind_value\": null}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"c18f0585-c495-415f-8f2c-4a446e92a05a\", \"step_key\": null, \"timestamp\": 1729520252.673173, \"user_message\": \"Started execution of run for \\\"__ASSET_JOB\\\".\"}','PIPELINE_START','2024-10-21 18:17:32.673173',NULL,NULL,NULL),(5,'c18f0585-c495-415f-8f2c-4a446e92a05a','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"EngineEventData\", \"error\": null, \"marker_end\": null, \"marker_start\": null, \"metadata_entries\": [{\"__class__\": \"EventMetadataEntry\", \"description\": null, \"entry_data\": {\"__class__\": \"TextMetadataEntryData\", \"text\": \"40632\"}, \"label\": \"pid\"}, {\"__class__\": \"EventMetadataEntry\", \"description\": null, \"entry_data\": {\"__class__\": \"TextMetadataEntryData\", \"text\": \"[\'not_partitioned\']\"}, \"label\": \"step_keys\"}]}, \"event_type_value\": \"ENGINE_EVENT\", \"logging_tags\": {}, \"message\": \"Executing steps using multiprocess executor: parent process (pid: 40632)\", \"pid\": 40632, \"pipeline_name\": \"__ASSET_JOB\", \"solid_handle\": null, \"step_handle\": null, \"step_key\": null, \"step_kind_value\": null}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"c18f0585-c495-415f-8f2c-4a446e92a05a\", \"step_key\": null, \"timestamp\": 1729520252.7089531, \"user_message\": \"Executing steps using multiprocess executor: parent process (pid: 40632)\"}','ENGINE_EVENT','2024-10-21 18:17:32.708953',NULL,NULL,NULL),(6,'c18f0585-c495-415f-8f2c-4a446e92a05a','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"EngineEventData\", \"error\": null, \"marker_end\": null, \"marker_start\": \"step_process_start\", \"metadata_entries\": []}, \"event_type_value\": \"STEP_WORKER_STARTING\", \"logging_tags\": {\"job_name\": \"__ASSET_JOB\", \"op_name\": \"not_partitioned\", \"resource_fn_name\": \"None\", \"resource_name\": \"None\", \"run_id\": \"c18f0585-c495-415f-8f2c-4a446e92a05a\", \"step_key\": \"not_partitioned\"}, \"message\": \"Launching subprocess for \\\"not_partitioned\\\".\", \"pid\": 40632, \"pipeline_name\": \"__ASSET_JOB\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"not_partitioned\", \"parent\": null}, \"step_handle\": {\"__class__\": \"StepHandle\", \"key\": \"not_partitioned\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"not_partitioned\", \"parent\": null}}, \"step_key\": \"not_partitioned\", \"step_kind_value\": \"COMPUTE\"}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"c18f0585-c495-415f-8f2c-4a446e92a05a\", \"step_key\": \"not_partitioned\", \"timestamp\": 1729520252.718335, \"user_message\": \"Launching subprocess for \\\"not_partitioned\\\".\"}','STEP_WORKER_STARTING','2024-10-21 18:17:32.718335','not_partitioned',NULL,NULL),(7,'c18f0585-c495-415f-8f2c-4a446e92a05a','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"EngineEventData\", \"error\": null, \"marker_end\": \"step_process_start\", \"marker_start\": null, \"metadata_entries\": [{\"__class__\": \"EventMetadataEntry\", \"description\": null, \"entry_data\": {\"__class__\": \"TextMetadataEntryData\", \"text\": \"40638\"}, \"label\": \"pid\"}]}, \"event_type_value\": \"STEP_WORKER_STARTED\", \"logging_tags\": {}, \"message\": \"Executing step \\\"not_partitioned\\\" in subprocess.\", \"pid\": 40638, \"pipeline_name\": \"__ASSET_JOB\", \"solid_handle\": null, \"step_handle\": null, \"step_key\": \"not_partitioned\", \"step_kind_value\": null}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"c18f0585-c495-415f-8f2c-4a446e92a05a\", \"step_key\": \"not_partitioned\", \"timestamp\": 1729520253.902018, \"user_message\": \"Executing step \\\"not_partitioned\\\" in subprocess.\"}','STEP_WORKER_STARTED','2024-10-21 18:17:33.902018','not_partitioned',NULL,NULL),(8,'c18f0585-c495-415f-8f2c-4a446e92a05a','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"EngineEventData\", \"error\": null, \"marker_end\": null, \"marker_start\": \"resources\", \"metadata_entries\": []}, \"event_type_value\": \"RESOURCE_INIT_STARTED\", \"logging_tags\": {}, \"message\": \"Starting initialization of resources [io_manager].\", \"pid\": 40638, \"pipeline_name\": \"__ASSET_JOB\", \"solid_handle\": null, \"step_handle\": {\"__class__\": \"StepHandle\", \"key\": \"not_partitioned\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"not_partitioned\", \"parent\": null}}, \"step_key\": \"not_partitioned\", \"step_kind_value\": null}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"c18f0585-c495-415f-8f2c-4a446e92a05a\", \"step_key\": \"not_partitioned\", \"timestamp\": 1729520253.939075, \"user_message\": \"Starting initialization of resources [io_manager].\"}','RESOURCE_INIT_STARTED','2024-10-21 18:17:33.939075','not_partitioned',NULL,NULL),(9,'c18f0585-c495-415f-8f2c-4a446e92a05a','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"EngineEventData\", \"error\": null, \"marker_end\": \"resources\", \"marker_start\": null, \"metadata_entries\": [{\"__class__\": \"EventMetadataEntry\", \"description\": null, \"entry_data\": {\"__class__\": \"PythonArtifactMetadataEntryData\", \"module\": \"dagster._core.storage.fs_io_manager\", \"name\": \"PickledObjectFilesystemIOManager\"}, \"label\": \"io_manager\"}, {\"__class__\": \"EventMetadataEntry\", \"description\": null, \"entry_data\": {\"__class__\": \"TextMetadataEntryData\", \"text\": \"32ms\"}, \"label\": \"io_manager:init_time\"}]}, \"event_type_value\": \"RESOURCE_INIT_SUCCESS\", \"logging_tags\": {}, \"message\": \"Finished initialization of resources [io_manager].\", \"pid\": 40638, \"pipeline_name\": \"__ASSET_JOB\", \"solid_handle\": null, \"step_handle\": {\"__class__\": \"StepHandle\", \"key\": \"not_partitioned\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"not_partitioned\", \"parent\": null}}, \"step_key\": \"not_partitioned\", \"step_kind_value\": null}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"c18f0585-c495-415f-8f2c-4a446e92a05a\", \"step_key\": \"not_partitioned\", \"timestamp\": 1729520253.98586, \"user_message\": \"Finished initialization of resources [io_manager].\"}','RESOURCE_INIT_SUCCESS','2024-10-21 18:17:33.985860','not_partitioned',NULL,NULL),(10,'c18f0585-c495-415f-8f2c-4a446e92a05a','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"ComputeLogsCaptureData\", \"external_stderr_url\": null, \"external_stdout_url\": null, \"external_url\": null, \"log_key\": \"uvuunmkd\", \"step_keys\": [\"not_partitioned\"]}, \"event_type_value\": \"LOGS_CAPTURED\", \"logging_tags\": {}, \"message\": \"Started capturing logs in process (pid: 40638).\", \"pid\": 40638, \"pipeline_name\": \"__ASSET_JOB\", \"solid_handle\": null, \"step_handle\": null, \"step_key\": null, \"step_kind_value\": null}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"c18f0585-c495-415f-8f2c-4a446e92a05a\", \"step_key\": null, \"timestamp\": 1729520254.0351481, \"user_message\": \"Started capturing logs in process (pid: 40638).\"}','LOGS_CAPTURED','2024-10-21 18:17:34.035148',NULL,NULL,NULL),(11,'c18f0585-c495-415f-8f2c-4a446e92a05a','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": null, \"event_type_value\": \"STEP_START\", \"logging_tags\": {\"job_name\": \"__ASSET_JOB\", \"op_name\": \"not_partitioned\", \"resource_fn_name\": \"None\", \"resource_name\": \"None\", \"run_id\": \"c18f0585-c495-415f-8f2c-4a446e92a05a\", \"step_key\": \"not_partitioned\"}, \"message\": \"Started execution of step \\\"not_partitioned\\\".\", \"pid\": 40638, \"pipeline_name\": \"__ASSET_JOB\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"not_partitioned\", \"parent\": null}, \"step_handle\": {\"__class__\": \"StepHandle\", \"key\": \"not_partitioned\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"not_partitioned\", \"parent\": null}}, \"step_key\": \"not_partitioned\", \"step_kind_value\": \"COMPUTE\"}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"c18f0585-c495-415f-8f2c-4a446e92a05a\", \"step_key\": \"not_partitioned\", \"timestamp\": 1729520254.05652, \"user_message\": \"Started execution of step \\\"not_partitioned\\\".\"}','STEP_START','2024-10-21 18:17:34.056520','not_partitioned',NULL,NULL),(12,'c18f0585-c495-415f-8f2c-4a446e92a05a','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"StepOutputData\", \"metadata_entries\": [], \"step_output_handle\": {\"__class__\": \"StepOutputHandle\", \"mapping_key\": null, \"output_name\": \"result\", \"step_key\": \"not_partitioned\"}, \"type_check_data\": {\"__class__\": \"TypeCheckData\", \"description\": null, \"label\": \"result\", \"metadata_entries\": [], \"success\": true}, \"version\": null}, \"event_type_value\": \"STEP_OUTPUT\", \"logging_tags\": {\"job_name\": \"__ASSET_JOB\", \"op_name\": \"not_partitioned\", \"resource_fn_name\": \"None\", \"resource_name\": \"None\", \"run_id\": \"c18f0585-c495-415f-8f2c-4a446e92a05a\", \"step_key\": \"not_partitioned\"}, \"message\": \"Yielded output \\\"result\\\" of type \\\"Any\\\". (Type check passed).\", \"pid\": 40638, \"pipeline_name\": \"__ASSET_JOB\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"not_partitioned\", \"parent\": null}, \"step_handle\": {\"__class__\": \"StepHandle\", \"key\": \"not_partitioned\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"not_partitioned\", \"parent\": null}}, \"step_key\": \"not_partitioned\", \"step_kind_value\": \"COMPUTE\"}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"c18f0585-c495-415f-8f2c-4a446e92a05a\", \"step_key\": \"not_partitioned\", \"timestamp\": 1729520254.069696, \"user_message\": \"Yielded output \\\"result\\\" of type \\\"Any\\\". (Type check passed).\"}','STEP_OUTPUT','2024-10-21 18:17:34.069696','not_partitioned',NULL,NULL),(13,'c18f0585-c495-415f-8f2c-4a446e92a05a','{\"__class__\": \"EventLogEntry\", \"dagster_event\": null, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"c18f0585-c495-415f-8f2c-4a446e92a05a\", \"step_key\": \"not_partitioned\", \"timestamp\": 1729520254.084224, \"user_message\": \"Writing file at: /Users/jamie/temp_dagster_home/storage/not_partitioned using PickledObjectFilesystemIOManager...\"}',NULL,'2024-10-21 18:17:34.084224','not_partitioned',NULL,NULL),(14,'c18f0585-c495-415f-8f2c-4a446e92a05a','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"StepMaterializationData\", \"asset_lineage\": [], \"materialization\": {\"__class__\": \"AssetMaterialization\", \"asset_key\": {\"__class__\": \"AssetKey\", \"path\": [\"not_partitioned\"]}, \"description\": null, \"metadata_entries\": [{\"__class__\": \"EventMetadataEntry\", \"description\": null, \"entry_data\": {\"__class__\": \"PathMetadataEntryData\", \"path\": \"/Users/jamie/temp_dagster_home/storage/not_partitioned\"}, \"label\": \"path\"}], \"partition\": null, \"tags\": {\"dagster/code_version\": \"c18f0585-c495-415f-8f2c-4a446e92a05a\", \"dagster/data_version\": \"2f1b54df025779ce37abfdac7c0370f8467406c8138a2738b88e012384b4a7ce\"}}}, \"event_type_value\": \"ASSET_MATERIALIZATION\", \"logging_tags\": {\"job_name\": \"__ASSET_JOB\", \"op_name\": \"not_partitioned\", \"resource_fn_name\": \"None\", \"resource_name\": \"None\", \"run_id\": \"c18f0585-c495-415f-8f2c-4a446e92a05a\", \"step_key\": \"not_partitioned\"}, \"message\": \"Materialized value not_partitioned.\", \"pid\": 40638, \"pipeline_name\": \"__ASSET_JOB\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"not_partitioned\", \"parent\": null}, \"step_handle\": {\"__class__\": \"StepHandle\", \"key\": \"not_partitioned\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"not_partitioned\", \"parent\": null}}, \"step_key\": \"not_partitioned\", \"step_kind_value\": \"COMPUTE\"}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"c18f0585-c495-415f-8f2c-4a446e92a05a\", \"step_key\": \"not_partitioned\", \"timestamp\": 1729520254.09408, \"user_message\": \"Materialized value not_partitioned.\"}','ASSET_MATERIALIZATION','2024-10-21 18:17:34.094080','not_partitioned','[\"not_partitioned\"]',NULL),(15,'c18f0585-c495-415f-8f2c-4a446e92a05a','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"HandledOutputData\", \"manager_key\": \"io_manager\", \"metadata_entries\": [{\"__class__\": \"EventMetadataEntry\", \"description\": null, \"entry_data\": {\"__class__\": \"PathMetadataEntryData\", \"path\": \"/Users/jamie/temp_dagster_home/storage/not_partitioned\"}, \"label\": \"path\"}], \"output_name\": \"result\"}, \"event_type_value\": \"HANDLED_OUTPUT\", \"logging_tags\": {\"job_name\": \"__ASSET_JOB\", \"op_name\": \"not_partitioned\", \"resource_fn_name\": \"None\", \"resource_name\": \"None\", \"run_id\": \"c18f0585-c495-415f-8f2c-4a446e92a05a\", \"step_key\": \"not_partitioned\"}, \"message\": \"Handled output \\\"result\\\" using IO manager \\\"io_manager\\\"\", \"pid\": 40638, \"pipeline_name\": \"__ASSET_JOB\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"not_partitioned\", \"parent\": null}, \"step_handle\": {\"__class__\": \"StepHandle\", \"key\": \"not_partitioned\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"not_partitioned\", \"parent\": null}}, \"step_key\": \"not_partitioned\", \"step_kind_value\": \"COMPUTE\"}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"c18f0585-c495-415f-8f2c-4a446e92a05a\", \"step_key\": \"not_partitioned\", \"timestamp\": 1729520254.148461, \"user_message\": \"Handled output \\\"result\\\" using IO manager \\\"io_manager\\\"\"}','HANDLED_OUTPUT','2024-10-21 18:17:34.148461','not_partitioned',NULL,NULL),(16,'c18f0585-c495-415f-8f2c-4a446e92a05a','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"StepSuccessData\", \"duration_ms\": 94.62320798775181}, \"event_type_value\": \"STEP_SUCCESS\", \"logging_tags\": {\"job_name\": \"__ASSET_JOB\", \"op_name\": \"not_partitioned\", \"resource_fn_name\": \"None\", \"resource_name\": \"None\", \"run_id\": \"c18f0585-c495-415f-8f2c-4a446e92a05a\", \"step_key\": \"not_partitioned\"}, \"message\": \"Finished execution of step \\\"not_partitioned\\\" in 94ms.\", \"pid\": 40638, \"pipeline_name\": \"__ASSET_JOB\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"not_partitioned\", \"parent\": null}, \"step_handle\": {\"__class__\": \"StepHandle\", \"key\": \"not_partitioned\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"not_partitioned\", \"parent\": null}}, \"step_key\": \"not_partitioned\", \"step_kind_value\": \"COMPUTE\"}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"c18f0585-c495-415f-8f2c-4a446e92a05a\", \"step_key\": \"not_partitioned\", \"timestamp\": 1729520254.162733, \"user_message\": \"Finished execution of step \\\"not_partitioned\\\" in 94ms.\"}','STEP_SUCCESS','2024-10-21 18:17:34.162733','not_partitioned',NULL,NULL),(17,'c18f0585-c495-415f-8f2c-4a446e92a05a','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"EngineEventData\", \"error\": null, \"marker_end\": null, \"marker_start\": null, \"metadata_entries\": [{\"__class__\": \"EventMetadataEntry\", \"description\": null, \"entry_data\": {\"__class__\": \"TextMetadataEntryData\", \"text\": \"40632\"}, \"label\": \"pid\"}]}, \"event_type_value\": \"ENGINE_EVENT\", \"logging_tags\": {}, \"message\": \"Multiprocess executor: parent process exiting after 1.67s (pid: 40632)\", \"pid\": 40632, \"pipeline_name\": \"__ASSET_JOB\", \"solid_handle\": null, \"step_handle\": null, \"step_key\": null, \"step_kind_value\": null}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"c18f0585-c495-415f-8f2c-4a446e92a05a\", \"step_key\": null, \"timestamp\": 1729520254.388716, \"user_message\": \"Multiprocess executor: parent process exiting after 1.67s (pid: 40632)\"}','ENGINE_EVENT','2024-10-21 18:17:34.388716',NULL,NULL,NULL),(18,'c18f0585-c495-415f-8f2c-4a446e92a05a','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": null, \"event_type_value\": \"PIPELINE_SUCCESS\", \"logging_tags\": {}, \"message\": \"Finished execution of run for \\\"__ASSET_JOB\\\".\", \"pid\": 40632, \"pipeline_name\": \"__ASSET_JOB\", \"solid_handle\": null, \"step_handle\": null, \"step_key\": null, \"step_kind_value\": null}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"c18f0585-c495-415f-8f2c-4a446e92a05a\", \"step_key\": null, \"timestamp\": 1729520254.402448, \"user_message\": \"Finished execution of run for \\\"__ASSET_JOB\\\".\"}','PIPELINE_SUCCESS','2024-10-21 18:17:34.402448',NULL,NULL,NULL),(19,'c18f0585-c495-415f-8f2c-4a446e92a05a','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"EngineEventData\", \"error\": null, \"marker_end\": null, \"marker_start\": null, \"metadata_entries\": []}, \"event_type_value\": \"ENGINE_EVENT\", \"logging_tags\": {}, \"message\": \"Process for run exited (pid: 40632).\", \"pid\": null, \"pipeline_name\": \"__ASSET_JOB\", \"solid_handle\": null, \"step_handle\": null, \"step_key\": null, \"step_kind_value\": null}, \"error_info\": null, \"level\": 20, \"message\": \"\", \"pipeline_name\": \"__ASSET_JOB\", \"run_id\": \"c18f0585-c495-415f-8f2c-4a446e92a05a\", \"step_key\": null, \"timestamp\": 1729520254.452232, \"user_message\": \"\"}','ENGINE_EVENT','2024-10-21 18:17:34.452232',NULL,NULL,NULL);
/*!40000 ALTER TABLE `event_logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `instance_info`
--

DROP TABLE IF EXISTS `instance_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `instance_info` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `run_storage_id` text,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `instance_info`
--

LOCK TABLES `instance_info` WRITE;
/*!40000 ALTER TABLE `instance_info` DISABLE KEYS */;
INSERT INTO `instance_info` VALUES (1,'9c50caea-e992-4d42-8e6d-781df0cdf237');
/*!40000 ALTER TABLE `instance_info` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `instigators`
--

DROP TABLE IF EXISTS `instigators`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `instigators` (
  `id` bigint NOT NULL AUTO_INCREMENT,
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
  `id` bigint NOT NULL AUTO_INCREMENT,
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
  `id` bigint NOT NULL AUTO_INCREMENT,
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
  `id` bigint NOT NULL AUTO_INCREMENT,
  `key` text NOT NULL,
  `value` text,
  PRIMARY KEY (`id`),
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
-- Table structure for table `pending_steps`
--

DROP TABLE IF EXISTS `pending_steps`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pending_steps` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `concurrency_key` text NOT NULL,
  `run_id` text,
  `step_key` text,
  `priority` int DEFAULT NULL,
  `assigned_timestamp` datetime(6) DEFAULT NULL,
  `create_timestamp` datetime(6) DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_pending_steps` (`concurrency_key`(255),`run_id`(255),`step_key`(32))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pending_steps`
--

LOCK TABLES `pending_steps` WRITE;
/*!40000 ALTER TABLE `pending_steps` DISABLE KEYS */;
/*!40000 ALTER TABLE `pending_steps` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `run_tags`
--

DROP TABLE IF EXISTS `run_tags`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `run_tags` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `run_id` varchar(255) DEFAULT NULL,
  `key` text,
  `value` text,
  PRIMARY KEY (`id`),
  KEY `run_id` (`run_id`),
  KEY `idx_run_tags` (`key`(64),`value`(64)),
  KEY `idx_run_tags_run_idx` (`run_id`,`id`),
  CONSTRAINT `run_tags_ibfk_1` FOREIGN KEY (`run_id`) REFERENCES `runs` (`run_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `run_tags`
--

LOCK TABLES `run_tags` WRITE;
/*!40000 ALTER TABLE `run_tags` DISABLE KEYS */;
INSERT INTO `run_tags` VALUES (1,'c18f0585-c495-415f-8f2c-4a446e92a05a','.dagster/repository','__repository__@backfill_multiple_iterations.py'),(2,'c18f0585-c495-415f-8f2c-4a446e92a05a','.dagster/grpc_info','{\"host\": \"localhost\", \"socket\": \"/var/folders/ns/r7rp0cg558zdj1yjm3p66qn80000gn/T/tmpu8pljpug\"}');
/*!40000 ALTER TABLE `run_tags` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `runs`
--

DROP TABLE IF EXISTS `runs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `runs` (
  `id` bigint NOT NULL AUTO_INCREMENT,
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
  KEY `idx_run_status` (`status`(32)),
  KEY `idx_run_range` (`status`(32),`update_timestamp`,`create_timestamp`),
  KEY `idx_runs_by_job` (`pipeline_name`(255),`id`),
  CONSTRAINT `fk_runs_snapshot_id_snapshots_snapshot_id` FOREIGN KEY (`snapshot_id`) REFERENCES `snapshots` (`snapshot_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `runs`
--

LOCK TABLES `runs` WRITE;
/*!40000 ALTER TABLE `runs` DISABLE KEYS */;
INSERT INTO `runs` VALUES (1,'c18f0585-c495-415f-8f2c-4a446e92a05a','dd6c6dd475cd4d91c23a9dbaf55eb56b2b1d0d25','__ASSET_JOB',NULL,'SUCCESS','{\"__class__\": \"PipelineRun\", \"asset_check_selection\": {\"__frozenset__\": []}, \"asset_selection\": {\"__frozenset__\": [{\"__class__\": \"AssetKey\", \"path\": [\"not_partitioned\"]}]}, \"execution_plan_snapshot_id\": \"93b84fd7cd172f878122450c2dae6901be99048f\", \"external_pipeline_origin\": {\"__class__\": \"ExternalPipelineOrigin\", \"external_repository_origin\": {\"__class__\": \"ExternalRepositoryOrigin\", \"repository_location_origin\": {\"__class__\": \"ManagedGrpcPythonEnvRepositoryLocationOrigin\", \"loadable_target_origin\": {\"__class__\": \"LoadableTargetOrigin\", \"attribute\": null, \"executable_path\": null, \"module_name\": null, \"package_name\": null, \"python_file\": \"../jamie_examples/backfill_multiple_iterations.py\", \"working_directory\": \"/Users/jamie/dev/dagster\"}, \"location_name\": \"backfill_multiple_iterations.py\"}, \"repository_name\": \"__repository__\"}, \"pipeline_name\": \"__ASSET_JOB\"}, \"has_repository_load_data\": false, \"mode\": null, \"parent_run_id\": null, \"pipeline_code_origin\": {\"__class__\": \"PipelinePythonOrigin\", \"pipeline_name\": \"__ASSET_JOB\", \"repository_origin\": {\"__class__\": \"RepositoryPythonOrigin\", \"code_pointer\": {\"__class__\": \"FileCodePointer\", \"fn_name\": \"defs\", \"python_file\": \"../jamie_examples/backfill_multiple_iterations.py\", \"working_directory\": \"/Users/jamie/dev/dagster\"}, \"container_context\": {}, \"container_image\": null, \"entry_point\": [\"dagster\"], \"executable_path\": \"/Users/jamie/.pyenv/versions/3.11.1/envs/dagster-3.11/bin/python3\"}}, \"pipeline_name\": \"__ASSET_JOB\", \"pipeline_snapshot_id\": \"dd6c6dd475cd4d91c23a9dbaf55eb56b2b1d0d25\", \"root_run_id\": null, \"run_config\": {}, \"run_id\": \"c18f0585-c495-415f-8f2c-4a446e92a05a\", \"run_op_concurrency\": null, \"solid_selection\": null, \"solids_to_execute\": null, \"status\": {\"__enum__\": \"PipelineRunStatus.SUCCESS\"}, \"step_keys_to_execute\": [\"not_partitioned\"], \"tags\": {\".dagster/grpc_info\": \"{\\\"host\\\": \\\"localhost\\\", \\\"socket\\\": \\\"/var/folders/ns/r7rp0cg558zdj1yjm3p66qn80000gn/T/tmpu8pljpug\\\"}\"}}',NULL,NULL,'2024-10-21 10:17:29.501248','2024-10-21 14:17:34.438747',1729520252.697955,1729520254.438747);
/*!40000 ALTER TABLE `runs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `secondary_indexes`
--

DROP TABLE IF EXISTS `secondary_indexes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `secondary_indexes` (
  `id` bigint NOT NULL AUTO_INCREMENT,
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
INSERT INTO `secondary_indexes` VALUES (1,'run_partitions','2024-10-21 10:16:51.999764','2024-10-21 10:16:51.972696'),(2,'run_repo_label_tags','2024-10-21 10:16:52.247391','2024-10-21 10:16:52.145128'),(3,'bulk_action_types','2024-10-21 10:16:52.333973','2024-10-21 10:16:52.322206'),(4,'run_start_end_overwritten','2024-10-21 10:16:52.394137','2024-10-21 10:16:52.382596'),(5,'asset_key_table','2024-10-21 10:16:52.565227','2024-10-21 10:16:52.559331'),(6,'asset_key_index_columns','2024-10-21 10:16:52.586322','2024-10-21 10:16:52.580242'),(7,'schedule_jobs_selector_id','2024-10-21 10:16:52.686899','2024-10-21 10:16:52.682249'),(8,'schedule_ticks_selector_id','2024-10-21 10:16:52.727521','2024-10-21 10:16:52.722314');
/*!40000 ALTER TABLE `secondary_indexes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `snapshots`
--

DROP TABLE IF EXISTS `snapshots`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `snapshots` (
  `id` bigint NOT NULL AUTO_INCREMENT,
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
INSERT INTO `snapshots` VALUES (1,'653890b7bc24ce4415c9f2704bf15f80c2bb8f65',_binary 'xœ\í][sÛ¸þ+\õ¡\í\Ì\Æ\áÄ¾9‰\Óu\ëÚ™\Ø\ÛNgapµØ¥H.I9Qwü\ß{\0R%“2$K²\ì\õ\ÎlR\àÁÁw®8\0\È\ßQD\\–Q4ø\Ñ|Šsž\Ä)¿Lq^³j\ðƒ1 Y*â›¨¤C>\ÂQ9ý\åG\ã\÷\Ågß«v—ªYûyœ$Ñ”†¼‘I\ô+Ÿ(\Çé¤\Ð\Õ$WlHŒ—´ˆ\ó*\ÎRhŽ“n\òt<Šnq2\æ\åü¦ˆy\ÂZ\×7\ñ-O£¸¤,»ƒ›uï³«8e\rŠ\äÿ€ŸŽ\Ïÿ3¸ƒ¶%\Å	.¢æ‘¦\nZE9.\ðHŽkÚ¹l~\\xrt9\Ä9?2©\Åiˆ„bù,@‚™>&|J|‹!\ê‘\0‡l}<gqY™06\ên#$›{S 7\ìWùÏŸ\×\Âþ—ÁšŒ|iIª*\â\ô\æ\ñ¨\Él\Ù½]!Vw x—e\Él6Úº·ùxg—\Z\ã¼||vü¹c ]O]ª\ê¹wg\ê©~»ý˜d¸\×\Ãm„º»9\n\ó\ë\Â\ð\ñ\ì\âø\êN\Ó=¢ ;›c0½\Ú!§\çÿ<K9&	?\Úˆ\ãÔ¢X`B’\ó‹\ó“\ãwg\'\ë¹Ù\ò5H?§0Ž#i’o.y\Âi•G„{Ì³B\â ú\Øu¨\'l\Î)žRKø4,‹x\è\É\Ð\Ú\ëk©]\ô\óù\é\Åùz8O½\Üú¬Ý“Žr\ó12\Ó\ÄNÀ\Ð˜P$|D©o#P{\Â\ÅV\às:!žMyß¹|fþw}\Þ\î	lj>DŒ„\n,fÙ˜\òÀ\Ä6CÓ¡aÿûŽk\Ìl\ï Ä³\ç;N\ã\×\ç\ìžh\ê¬g>Fnº\íP\Ä’²\ÆÄ¶l\ÓwØ¶\íT€™†¶¾mc\æw. y¶º>s½2R)½\í2&B†mâº¡K1¢\È4¹m#nv\èC\Â¾’‡‡a>›q¾O\é¬\ÇY-š©D-\"ˆ\å˜cd¡‰± Á¿L\ZX„…\Ô\÷83‰½#Qü\ÒI\ô£üyNU\àqREy‘\ÝÆŒKXªb\Ì[¿(\ê.£ÿ–Y\Z•U!)ý~\×\ËR\\FÿmŠ˜ÀI)©M\ÓW—2KS[üT\'\Ì;;œ{\Ü\'.1™c{\\ \Ï7­™X0ˆ-&’\Â<¼±\ñt+Cû\ò€\õ¬­\\º\Örrv\òþ\ê¢kŠ\ð`	gÆ”\í–i!aaÏ†qy³,Ó±-\×\Ã\Ô\áž\ãš~ \à\ò 4~*\ÈUj\Ñ\ô¤¡ŽÍµ\â\öžF\Ô\ÞE[\ÒÚ \îSÒ¾\áˆ@\Þ\Ð!‚:¦‡y\è\à¹ ƒ6A\Â<(Ik\Ùÿ\õ \à !^^KÞ¯§v­®\î\î:¼\Ã\à\ä;§\ãŠ8IŒ²\âyiÄ©¤œpú§¼,z8š\Æ\ÝN\Äu…\íb\êy¦‡¶ mã¡‹a\æ¾ \à&gŽcÛžEw\ë¯#ü]«\é¸(xZ]\ÏÄ³9rÓ¡‚N!—ÂŸ,¦\Æ8Y¾\ð¯˜#r\æ„,K¸\àv=$\íˆ8~\è[‡-L,\æ¯á…µ\Í`Ÿ¶:V(<,@3˜\é£{4œ	‚£\'C\é3>?\Û\ìÒ¡šü¸\àF5\äF[	®\Ô++Œ*\í\ÂEe”c\Òü\ÈKc,-\Ôø*²\â×’·¼øª¡e\ó\Ö=FJ`Š\à\ÛdÂ±l\ß\ç\ð_ÀCj™¾),j\ÇL\Ï\Ý{\óx \ÊKu0R\r\÷•ikû>M\ð‰‹˜I\Z½\ãÀkqm\'´˜4\ê	Ç·B‡Q„(A~\às{c‹\Ù\é¸\ò˜þš\ð—82Ely`²²¤mš[/ˆm\Ã4Ÿ¸:ÿjš¯¦¹\ÓT+&Ú¶¹\õ•žm\Ø\æ/Í¼\Ú\æ«m\î\Æ6\ë\Õ2m\ã\Üú2\ß6Œ\ó‰—~^\ó\Õ8wcœ\ëd·¾Œ¸\r\ë¶\à>Œú&¶\àP„< \à>lZ6q\Ó\÷ý•\Þ_­ó¹¬\Ó:\ådm\ÓÔ¶‚}˜f½\Å6´\Ï\õ}‡ \æ’PÁ,JB\îxa\à;È²‘:\â \ìR§\Æx=8=ÿxq=\è¨4^\r¹‘d77¼øsiTÃ‚—\Ã,a\Z…Cx(Jø-Oú\\\ôk¦\×†oÊŠ½C’\\\Ê\rÌ“l\\4\ã\Ó“ú{Ãˆ³ž\é\ê\ô\Õ\ç\Ó\÷W\Ñ\åOÇŸ\Ö\Úû¸¤\×;Ûªÿ\\\ã\Úv\Õv§\ì&\ñ(®:\Ë{Á\í²ugn\ÞK¤i‚[>°±%<t<‡ù\ÄsmL©ÀN	#˜d\ßEœ„\Ê5×˜g‘@®OC\\b–Rª\ï\Í\Üu\×b—\ô\×MÍ’”\nþN\Ë,\áú®»>‘Õii{eM\rÓ•\å^5\Ì\n„@Ž;$8À¶GM&LoL\æ0C–ú\ÏP\Ã6\Ý\å…Ó¬\Z\ò\"\ZBL€l\É\ï9\Ñ\Z»Àu¸ ¹cÇ£\Äv=˜\"2\æ;·­€J\\\0\Ï\ÂÁa\îfK²\ô&*\ÆiÚ·\Îý¼‡R”z_\Å\ò¡¾M{\Ï{ˆ ¦\Ã\ñKVR9\Äm\Z¢–§\Ö\ö‰û\õ\ÔÀÀXX\\0\Ï\ôœÀ°=!\Ó\Î<D˜G ß±\ÊS\ï6c$¸ˆ\ïû/•(^‚\ÞP.‡­+w]„\÷*\÷\'\Þ\îr_š\×\à<O&grr\ó‰Ë©Áocþ¯Í—Kws2a+¢\×\Þú\"D?ø\å\ÃÉ§\Ï\'ï¯N>|\Ñ\ØŠ‹_!M«2`1+{0»\Ý(»¸¶c–\ò\ï!—Ù¤\Ñ\ì›5pÁ\æ!#+\ÈRŽŒw“\éDæ‡®v\ZÓ˜\æ©{¬}”@\ÏZ´\õr\ïÖ‚\Ë\ñ\Ï8c\Ì\Õ|p\á²m›ºŽe\ÇG9(k\Ùi\ö´jv«\ì\ôUBüýª„\îb\É!©\Än—–p5|T­Z\Ò}ZoO\ö‹\ô\à\ä{ž\Ä4®’‰Q\æœ\ÆbR\ïø\Î\Ø8\àQeF^\ð$\ÃLž¶¿\Ì\÷´2 }‹e\×\ò_\\Åš\ê[fP,·‚C\ÓY]­°‹i\Ù‚V\Óm\Ñ\É8ª‹u±\ÎøoFŒo¸4d\÷\äD‘\Ü<¯z4J¹\ÊR\ß0¾\ÅIb>å·¡=\ÔM¿6%À¯\Ó\öq\Ùjúp`l\ÚF\rû\÷V\Û/–\Ñ\Ö=MÛ«þkÏ€_„þ?\"øi­5¯\é^z!s]H\×<991\á\Z¹¢4ˆ\éY¶±\Ã\Ú?©™L\×kŽ–µO¯Lomv*­3/Ÿ•fßš3}*\ç®Ï«1pL\ÕP\ò+Æ©†£©Ÿ‹û\ö£P;°mRcŽCW€\ä\Û1CN!°Ox6%<\Øn	ˆz\á¤48L®@oÀé¯‰EC¤	\"!sŸ™\\€¿a¾ø”\Ú\Æ$0C$L\ê\"²\ë™[W™¿\Ö©P­\âøü\æRIyþ\ÃR!v\ñ‡û¬\ôZ\Å •\à•”†\É((ü¥\Èèœ•„\ö=‰¿nus\Çˆ³h„SÐ¯¢1Û–ùk\Ù\ì\Ë%¿‚—ª\ÎW›o<\Ê>ï°¾\ÏuÃ†¸i\Ç,\ÜB^ˆ›90\Óq<×¤6\Ü\nC˜ûºShm?¾\×\è¢=\È\ç]:µ\ë\Ý8Nª7 0\"†Lq!adœ^ŽB6Š!ë­²BjZÊšB\Í-\\5Ir}„RmÝƒ\èŸ@\ÏN?\Ý)µž\Æi\Ëv¯\Z§}`û¹iœ\ì©o—\ÙxD@£21=ú.§lR½Fx\"•1Or’\Éby<Z)\ç@\ä,\Ô\'}A\ÇEZ+¢$ûµ<Ie¤ù2\',ù«\Î\é\Þ\ÅDkY;\Þ\Ä\÷Z_]¯¾º\ïW\ru\ÄlŸø–\0Ð‚\ãJN¹\Û5‡Àk-“\Ï\Ê—‚nU\å\åoß²Œ–Gù¤\Zf\éQVÜ¼u\Þ&1)p1y»¬v\Ãj”ü	©\âß«\ò\rx\Í7\ê\èùHk†\Ó\ÉbTû¨nß‹¾\öù\ðý£¬,LR\í\Åk\Ì\\B/×°b\ÐQu_N>d¶b¨ì’ŽÁ\Z¾)U-7v][}]Q\Ô\ä™,M&5}À\çMýLŽ\ã¢)¨\èPÁ´\È\ÊR½\å¤	j™˜‘œzÚ„d\Ç\Ø`1h˜\ZÀ×¾µ¹\Úâ¿¶;V¥\Õ^R©\ãX=9\åB\æ¿s6Î³Š×—\ðLÉ§\ÐJTs\é	\Æ\éªDu“d\'\ZJP\Ï\ÝD5ÁžZ\Ñz»\õB³v\ÜkhÖž³>·\Ð\ÜU]\è\n.YcYû\õ1zš¢-“½jŠ\ö+?v¤)Z\Ði3¹W\è´\Ë!‡dd;/\Ü\ÊM¼=›ruw\Ñ\êÙ“6üûRŠM_½?xP\Ô\Í\õ\â\Û\Æ[\ï\Ô_X\Ô\î†\ï—0ÿ\í×Ž\ß\Û\Å\õd\ï3]fd-t¶\ô\òX\íw~¹»“}5g‘\"/‡i=\å+>\\Ò¬\ßI\îÏ§Í—?`²@T\ï3&-²+…\Ä\â2O\ðdù#%\à*ˆ,\Ì\Ä\é<¸·–rú$\Ñ\êu\á\Ë%já°˜~\Å\å1gG0s*bœ\Äÿ[¦\×hi b^\ñ¡‰MQ›¾S}l+?.±Œ[\ËÀ»¡\Û\Ê{æµ±œ\ò\Þf\Ï+6Es\ö\ôp®þJ\Åc\ð|Ä‹\áµqß‡h\ç\'6Å³yiù\n4W}\Ü\á1Xnüwm$OÓ•8Â¤u\Ø\Ù7\ÅrJp5ž­VZ˜ž_\\ý4\Ì] 6\Ìh£\Ò\ê¿™¾”gS`\æ±s.¤9QµÇ¼’^\×9ÿ°\Ö\0\Ïe.>¦Õ¸Xøy\ÎS&+—\Ó\Ö\í¸¹xÌ¢8½\Í(–\È×”:\æ—²\á\é¬\ÝThqš«H1\Ó\ó\à©l\Ñ\âb\áÁU\'A@Àl\rb\Z\Ñ,‘x·¦\ã\Ï–l\\IB}½_¨Ÿ\Â)KfŠ\Ö<\ÒZ\Z„i\ÎŒ^žî¾¨iG‹¯\Î\ó…YNMfN3*}\Îû\ê=–ª:PŒ{\ÅM}¬\Ï\ô\Ò\é±E^—–=\r‹\'À\Ù\ì:\"¶\rV_Õ»-†ŽSj\÷»Y>\Æ\ö4\Z\Ó%„ Y`\ö\Ë]_º)p>\\\è+ŠŽ//O®¢¿_¼“D\ä\ç&\ñÍ‚›ž\ÆÚŒq\õdŸ„ÿ	\r>p±2H\Ö[rV’9SMZ„\ê\Êf¤&\Ê\ê©û¡\ã\õ@x\÷\ð™[®){›}[£~^¶›nVY)\Ñ\ÏM£\'“\éÓž[¸/„l\ñ\è\ØÌ¡dVd\\\Z´7\Ûø³ ú%o1s]qª‚W¹\"½S\óÃ¼i;·£\Ù(\ÏÊ¸¿3s†þ³\ãvù­kØ“\í\î%Ø„˜~,šH?w\Å\ír\ÙbÕª³‡·\õk_&\ØD\õU\Ö\ÉÀ#8œ\Ç\Ó¦+œ4\ÉEmM«h\æ¾fS ÿGU²¶\ì—2\ëW‘¿|‘w\ÌR^\Åþ2\Åþ$\á¤cú\õª_/S¿–\Åþr35Ÿ_þbU\Õ','PIPELINE'),(2,'dd6c6dd475cd4d91c23a9dbaf55eb56b2b1d0d25',_binary 'xœ\í][s\Û6þ+\í\Ã\î\Î4o\à¥oN\âl½\õÚ™\ØÝ:\Ã\àr`±¡H•¤œ¨ü\÷=\0©‹eQ†dIV²\î´MHÀw®\0ˆ?{I\Â3ZUI\Òû\Ñ\ê½K‡¥9\\\ætX\õ‹º\÷ƒ\Õ\ãE.Ó›¤\â}Ð¤šü\ò£\õ\çÝº¯u¹K]l¾>Í²dBC½N\Ø8ùcM\à8wº\Zu7	/\Óa9\ÈGY†/!\r’[š š½”)db\îù&½…<\É\é\0e\Õ¾lZŸ>¥¹h;¡I.\ô\ágüù\èøü¿½¯X¶\â4£e\ÒViÛ¨±T2¤%¨qM\ZWÅË’Ž.ûtG6w€G±\ô\"\êÇc)\ì@HÂ€³À1\',¤‘X\ÞYZ\ÕV!­š\Û\É\ö\Ý\È\r\Û5Bþýûãµ°ÿµ·fG>\Ìqª.\Óü\æ\ñh\Èl\Ù)½]!\Ö4 ‘xU\Ùl6Ú¦µ\Ùx§\ã¼|}|vü~\É@—Õº\Ô%t½WgºV·Þ¾\Í\n\Úi\á¶B\Ó\Ü…\Ù\óax{vq|\õ\0§ùQP\Í0˜<\í\Ó\ó‡\Æ^\ä@YG±±Ÿºk\ît\Â’\ó‹\ó“\ãWg\'\ë™Õ€¶\rH¿\ä8Ž#¥’/.!^\å\"ˆ1/†( ¾Ç‰t8•Ä‹¸#†Ž\ÃHüdhm¡\ëk‰]\ò\Ëù\é\Åùz8O¬\Üú]»\Çm*fc¶M½¼\È…\òX1\ç\Ç!\÷)‘>u\Â\0\÷‚=›\ö}\çü™\Ú\ß\õûvA¨S³!\Ò8Œc‡Žp\\\Ê!´©+¢\È\öx\á\ç;¡°C—{6\ëùÎ™\ÓZÁ\õ{v5M\Ô3#\Ø~\èz<q¬xM™\ë¸v\à{„¹®\ë‡\\¢šFnp¶m\ã\Î\ïœA³huý\Îu\òH‡\ô®/„Œu™\ïG>§1m\\7\'t£\0~´•†úl\Ö\ó}rg½ž5¬™p\Ôa’9AH\ÆvÙ”aLbü›\ÍC‡‰ˆ„\Í\Ü±\â×¥DßªŸgT%eu2,‹\ÛT€‚¥.G0\÷‹¦ž\Ð*ù­*\ò¤ªKE\éÏ¯]J«¤„\ßGi©‰IšUŠ\Ú$|i¥¢4=±\ÕÀOdB\Ã,¨S€@À|f\Ï%„I1	l\'Šm*ú;V\Ì<¼±A¾•¡}x@{\Ö.Sm99;y}u±lŠ\ð\àÎ´S.	Û‰¥C‰‹\ã\"žp\ÛsŸP\î\ñ|;%>”\ÄO¹J,Ú–Ä¢•±™T\ÜÞ“ˆÆºs\Ú\Ô}r:2dC\Ê8\ô\Ñ\ZzLr\Ï&\"F±2\è²X\Ú\Åi#ý¿î•€‚\êZ\õýz¢\×ú\é\ë\×%Ö¡w\òø¨‹f™U\Õ0¬¬4·¨U!—3°°}Uu\Ô{Ð‚¤y\Ò^nD|_º>\å„\Ø$\ÔÁ°\r\"Ÿ\â\ÌmA6\Ïs]\â\ð\Ý\Ú\Ç\ëÞ€~Q‹\Õ|T–\×\×S\ölŽP\Þ\×\Ði\ärü¿H±S#š­\ß\0ûœ®1œ#‚@uŠGúhvI¬\ôˆyA8!¡eŽÖ°\Â\Æj°OÝŒ<\'’„J”aqD	%\Éb&xH”«±Á¢oO7—\ÉPC~T‚U\÷Áš´x¥U(]´¬­j\Ä\Ú¡²FJC­²(?UP\ÞBù\Ñ@\Êf¥;””\áÁg®-¤\ç¸A\0øOw\ìÀ–C±6\ñ\÷\Ä<¨jH?\ç&\é‚û\n„Œ¥}Ÿ*øÄ‹)\Z\Z\ã±\ÐCm\ñ]/r„RN¤8‘\'xsa\0\î\Æ\Z³\Óq\rSþ)ƒ\ïqdš\Ø\âÀ\ÔÊ’±jn}AlªùÄ«\óÏªù¬š»QM½cb¬›[\ß\éÙ†n>\ñ\ÖÌ³n>\ë\ænt³\Ù-3VÎ­o\ómC9Ÿx\ë\çY9Ÿ•s7Ê¹\î‚\ìÖ··¡Ò•)x`S\'\öC\Z\ÉBŽ\æ#¤¶\ã2?´\Âøÿ\Ñ\Òû³v~k#[ª*\ÙX5µ`ªÙ¤\ØFŽGü \ðX,|I&…\ÃY‰\ÂÀ‹7&øO”^š¬1^\÷N\Ï\ß^\\\÷–¬4^\õÁÊŠ›(ÿZYu¿„ª_d\Â`\á+%\ÜB\Öe¢w¸fz\Ý\ô¦ª¡\ì’\ê¥J`£²ŸÁ˜\ôŸzœ\õ$\ÈT¦¯ÞŸ¾¾J.:~·V\î\ã‚\\\ï,Uÿ[\õ7Ši\ÛÛv7Ki½ty\ï z»¨F\Ë#·G\çª\à–llI%D\ñDÀˆ\ïR\Î%1\Î£ÀbW~Œ\Å\ô T\Ðpy\ê	\Ô\î\ñ\ÄÕ¨-fÅ¥\æ\Ý\Ô\\/\Û\ìR\öºm\Ã\âEV P\áŸyUd`nº›Y\Ë#-c«l(a¦¼Ü«„9s%¥\Ò)ˆM¼Ð—¡t‰TB‚\ÄL†Z\ä”„\í\Ö1ZA\"\Òû»¿\Úü\\bhÀA\rÛ\ï\Æ\ï—\ï\Ì©\ï	×‘8Â‡ˆG¡³ZJAF$Ž‰‹ï†–¥Q\ê6Ee~|\òj³ì–¥ù-³-\÷~\ñ¹\Í\r¢ø\Ôì·£Iúœ\Ö},TŽrƒ\Ô\ÔK»\æµ\Ü\r]7\0€F¾dB×³#à¡”4\à^—3Ã§\Ì=P@4¸²\0#k€\Ð\Ó¨\ÖÅ¢%²	ˆb\"b8´AJ‡E„\ô}\êR\Ú\è\Ëm\î\Çl×©RyQ+=«S\ÄTXV„£¯Sœhh\õ„Z\á$‹\Ò*Pt\ð\ì&\Ô&\ÙPX¾CHÀw•\à¶³€€\ëy¾K\Ð\ÎIb\Í&8s\öƒ]C“É€\æ\Èù²U¨9\Å4Ò¦>UN\'—\Ú\æ6Š•†Po\××­)¡\å°\Å`\Û\Ì\ó¤ˆ$81ZB\Ï^ƒ\0›»ø*Š\\Ÿ®©\Ý7µ°{µûO|x\àüý\Â,‰‡\ÙøLM•Þšhü>‚o¾ùº›s[a½qr\éwÁúÞ¯oNÞ½?y}|u\ò\æƒAj)-?A™\Ôv±¨:—svk0\ïK\ì\ãúP\÷¡´\Ú8¥‰4šJ\Êu /:²^\'Ó¢–•3²“º\Ö=\Ö>˜`¦-\Ær¹wm¡¡\ã!±\Ñ	0 À\ÐÝ‹]\×\å¾\ç¸\Ìb‡”¶\ì\ôøËª¹²\ñ$\Ç\\$ŒÀß¯H˜n½’H\ìv£Š\ÖýG­|CºoF›exŒ\î|f)O\ëllUC\à©7ù\ã…e\è<\ê\Â\Z–T¨³\ê—Y†ü‘u¡\Ò\çT5­þ\Ú\×ÔŸ‹S•X®&6“UºfÀV*§¤UYtZm³)z\'\ëT\ê&\Þ4K\Öo³>\Ó\ÊRÍ£““e1Àx¿©¯[´*µgÓ¼À	A–Y&ým\éaMÑ\í‚\â\ÇIù´š+ú°cl\Ë&m\÷\ï\íc\Î¦\ÆXþ\Í$m¯\òúøa¬Ž¢\Î\\Ÿ\ØF´\ç\ë„ºSÇ¡\á\÷!ÿp~F;\×\ëAºWFOy‰\Ñ\ë¯.¥_Ò¬~M¦¨\Ëc´\ë\ô\ÂjW,\Ð^P´K\î*3•‹6”¾Å§ÖŒ5Gftªþ\Å\ä\ð\ßt9¤#³\Ã4\è1“8c\Þ\îU\âŒ\è}k§Z\ê\Ê*\rJT!\'G•SU\â5 cµte\Í£³\ñ\Ý	\\\ÝG…ÿVP+?Ìš“](‹£2oQ‘ý8¿È­„‘G	/Fyý·¿›œæº» ¾(w¾¼\ô<^o¼\ï\ö¶\Íú\éü	?\0/\Ö*(šG¨=\ô\×H™ª«\n\\XýºV?¾|)\n^\r\Çu¿ÈŠ\ò\æ¥\÷2KYI\Ë\ñ\ËE±\ë×ƒ\ì/(H5|©«h5_è£†/È³B˜¬i\ë\òIS¾}\ã\ó€ûGÿXk*ª¤Î½h\Õ\\A¯V1¾mŽ_ªM\"µvm\é>B3j\Õš\êh•¶z\Ýh}¸jj\ê\Í™\"\Ï\Æ\r}\Ä\çESgHÓ²\ryM¨P^U¥Oµ·N­S’\ÓP|žj˜Z\"E	\ÓøØµz\Úhü\Çù†up®\Ë+*\õ\Ã8\Ò5\'½P“†Y7Î‹\ZšG¬SÁZ…\êPY‚QþƒžD\Üd£™!\Ô3s\Ç\ÇIC°#š_/;\Ä\Ì5;Á½ºf\ã½\Åo\Í5/\Û^\æ\\³\n¶\ö\ç\Ì$Å˜\'û•‡D‹	/¦•	mŠŠ\à\ê)f,`C\Ö\ÃJx²ù\áÞÐ•\n\Z‹¡2\Ù\Ê.q\nƒa\Ýd\ñ¦\òT\Æ\ßc­\ÆL§ùp¤r©T\ï&¦Xû®,+>£»`økz“«L+£o µ®\Í{NqB\Ç	$DŒzp:‚º\ã\á|\Ø\ñ)q#L§:\Æ\ò¸_-1Ý†ÿ.´dc©Û–¼QlgI¿•\Ù8\Ñiù¦\â\ò\í¨\î¶@ÌŠü&Áˆ*\ïZ¤0^\Ç:\È/¸-$\ë<\Ñ¿]\ñ@Z‰ \é³z=¿‡í“¹\0šyGS?´W\ïhü™ yG#\èŒ;¹W\èŒS¿‹À\Â4üV‰ÿ‰ü¦™\÷fúdÿ~…\Â4¤þ~…b!9\áAc»\ö‘RCù0\åÄ¾\äc\Ó\ë\\zr½}¾{ƒ\Å\Ü=-w2BL‡»\á=\n¦\ó<p•Å½3O\ö\ìÅŽ¬…Î–>Hnü\Ý\Ù_¿ª¶\Ú\ô‰D“WÃª†”ÃŠË°\Ú,\Õû\óI\ñ\ÅK±\î5»\ZkŽ\ìJ&‰´\Zft¼x\ñZ\r¦6\Ó|f4\ælº81\×js\ÃP{–N)\'7ƒ=\æ¼ú€\"ý”f\é‹\ô\Ú-d	›W\\^´)j“{:VÀ¶\òÂ¢E\Ü\æ|9t[¹»\Ä\ËIß»À\ì¸iS4§·j¬€s\õ\ÍGÁ\ó—:\í}¢K¯\Ú\Ï\ö\"Œh®º0\è1Xn|3ˆ1’§ùJ\Ïuüe‰g\ß\Ë	Á\ÕxÎ•2\Â\ôü\âê§‰g^j\ÛcT\æ\Ú\ïB¦+\ä\Ù˜™\ï\\\Ëa\ÎcD\í1×œ\ã:\ëÿRX›\0†*,\ñzT®tü0„\\¨\Ý\Õ\ËI\éy¿sµT$i~[pªo(-™F\\ª‚§\Ór¦é½…DwfR\ñC\Ã1\Æ\á¤<\Ð\á\ð\Î£i\'\ZÉŠ\ÅÀ¦Ðª\ÕBdbOo~ø\Ú%<7%\öï´”$Ç——\'W\É?/^)\"\êjQz³\n¾\ÅHÏš\Z:dRS™\Ù\È?%\ÓUª–‚,‹? W¿\'SUh\Ê/–œ–YhøX•þ¹ùÌ…N\îV‘\ã\"šÁ\ã+\È\ë\é(’TÁ\Ý\Ð\Ç6w}¾\ït+nhûL:DF6w‹d@fp\Ï\÷­…PÿP©\Ó8\í9Ú¹~P\Ð\èv\ÉÌ¿°À+¼9Zº’Ì™.2G¨YLt¯kuMž?°ø„;·¸¾£g\àÓ»fšúª\Ü\äh\çJŽ¾o=OŸ\ö\ä\Í}&\ì vI²«\æYY …h\Ñ\Þ\ì˜\ì\Ö/XÔ©qOsm¤ª¶U»”7³¢\ó~‰ƒaQ¥5\Úæ©»¸\ãa–¼\î ¿u	{\Âü…‚­^€h…\÷,F\õ½*X\\\è\"\ó\æ{~y\à\î,½k˜m07Ê•\ë„(\ÞÊŠ4bÚ–J¦e\Z\0\Ý\÷þ³\ÇÿµbÕ™','PIPELINE'),(3,'93b84fd7cd172f878122450c2dae6901be99048f',_binary 'xœµTÁn\Z1ý•h\ÏUUh JnQ©ª‚D{Bhd\ÖC°\ðÚ®=›vƒø\÷\Î\ìz—@¡·^\ç½y¿y\ö¾\0(­J	 ¸¿)ž~cY“\ñnn•[8\Ò\ÖS\ñ\á¦P‘\ÌF•” `L&j\æS¬‘Al»|§*™ª¶d€\ÆAˆ¾D\Ö\ïI¢fœ!£,\ìœÿ\å ‘\"iÛŸ\Î2phÑ’¸W7|Š)¡R!\÷’¤\ñÀ\õ \":\Z\Ä\\m­T#¾\Z_\'ˆH±E„U ¡)¢\Ò\røšB\Ýy„M\ôo\èR;\Ær%<¾o\È4x¼KL@kBÊ†s\n­§\åT\ë\Û/“R\ß\ê»Q9þ¬\î\ôZm&\\O¦\ë\ñz¤?\é\ñDn5´fu\î\õ\ç\î°I@>;(—[Ž©A–\"\Þ\ð.V™\ÜNµ¿²\Ôd©\Ý\n\ò•—\Ò\ÊG\ó\\U\ãt6]]uŠ\"4c\à\ã\ã\ó·ù\ïO…\ØP!)­Haå£·ÿë¹¥\õ\Ãi\õÂ—‰@M@È³=¸F >b‡¬hW\ì9“d0ý¡£\ôüÈ’8\'\Ùo¹\År—\õs^: +i=4\ÃvŠ h{y\â„I\Ð\ê_H_9\á\Þ\ßl”MÎ±>-FüY›øþ©qFj«9ül¿ \ó†}GSo†­r\Ú^xPA¿v\à;\'/,½{KÙ•\Ãau&\ó}¡±\Í\ë\Õ\ó<=rÿ\é\\!•ÿ‹\Ã\ê\ð0¼¸¨','EXECUTION_PLAN');
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

-- Dump completed on 2024-10-21 10:22:00
