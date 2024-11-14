-- MySQL dump 10.13  Distrib 8.4.3, for macos14.4 (arm64)
--
-- Host: 127.0.0.1    Database: test
-- ------------------------------------------------------
-- Server version	8.3.0

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
INSERT INTO `alembic_version` VALUES ('16e3655b4d9b');
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
-- Table structure for table `backfill_tags`
--

DROP TABLE IF EXISTS `backfill_tags`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `backfill_tags` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `backfill_id` varchar(255) DEFAULT NULL,
  `key` text,
  `value` text,
  PRIMARY KEY (`id`),
  KEY `idx_backfill_tags_backfill_id` (`backfill_id`,`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `backfill_tags`
--

LOCK TABLES `backfill_tags` WRITE;
/*!40000 ALTER TABLE `backfill_tags` DISABLE KEYS */;
/*!40000 ALTER TABLE `backfill_tags` ENABLE KEYS */;
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
  `job_name` text,
  PRIMARY KEY (`id`),
  UNIQUE KEY `key` (`key`),
  KEY `idx_bulk_actions_status` (`status`(32)),
  KEY `idx_bulk_actions_action_type` (`action_type`),
  KEY `idx_bulk_actions` (`key`),
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
  KEY `idx_events_by_asset` (`asset_key`(64),`dagster_event_type`(64),`id`),
  KEY `idx_step_key` (`step_key`(32)),
  KEY `idx_event_type` (`dagster_event_type`(64),`id`),
  KEY `idx_events_by_asset_partition` (`asset_key`(64),`dagster_event_type`(64),`partition`(64),`id`),
  KEY `idx_events_by_run_id` (`run_id`(64),`id`)
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
  `id` bigint NOT NULL AUTO_INCREMENT,
  `run_storage_id` text,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `instance_info`
--

LOCK TABLES `instance_info` WRITE;
/*!40000 ALTER TABLE `instance_info` DISABLE KEYS */;
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
  KEY `idx_job_tick_timestamp` (`job_origin_id`,`timestamp`),
  KEY `idx_job_tick_status` (`job_origin_id`(32),`status`(32)),
  KEY `idx_tick_selector_timestamp` (`selector_id`,`timestamp`),
  KEY `ix_job_ticks_job_origin_id` (`job_origin_id`)
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
  `backfill_id` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `run_id` (`run_id`),
  KEY `fk_runs_snapshot_id_snapshots_snapshot_id` (`snapshot_id`),
  KEY `idx_run_partitions` (`partition_set`(64),`partition`(64)),
  KEY `idx_run_status` (`status`(32)),
  KEY `idx_runs_by_job` (`pipeline_name`(255),`id`),
  KEY `idx_run_range` (`status`(32),`update_timestamp`,`create_timestamp`),
  KEY `idx_runs_by_backfill_id` (`backfill_id`,`id`),
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
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(512) DEFAULT NULL,
  `create_timestamp` datetime(6) DEFAULT CURRENT_TIMESTAMP(6),
  `migration_completed` datetime(6) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `secondary_indexes`
--

LOCK TABLES `secondary_indexes` WRITE;
/*!40000 ALTER TABLE `secondary_indexes` DISABLE KEYS */;
INSERT INTO `secondary_indexes` VALUES (1,'run_partitions','2024-11-15 12:32:29.158543','2024-11-15 13:32:29.899885'),(2,'run_repo_label_tags','2024-11-15 12:32:29.183724','2024-11-15 13:32:29.926257'),(3,'bulk_action_types','2024-11-15 12:32:29.210778','2024-11-15 13:32:29.952917'),(4,'run_backfill_id','2024-11-15 12:32:29.248236','2024-11-15 13:32:29.988794'),(5,'backfill_job_name_and_tags','2024-11-15 12:32:29.281599','2024-11-15 13:32:30.022194'),(6,'run_start_end_overwritten','2024-11-15 12:32:29.331170','2024-11-15 13:32:30.071656'),(7,'asset_key_table','2024-11-15 12:32:29.595566','2024-11-15 13:32:30.336929'),(8,'asset_key_index_columns','2024-11-15 12:32:29.623227','2024-11-15 13:32:30.364828'),(9,'schedule_jobs_selector_id','2024-11-15 12:32:29.831446','2024-11-15 13:32:30.573486'),(10,'schedule_ticks_selector_id','2024-11-15 12:32:29.900756','2024-11-15 13:32:30.641064');
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

-- Dump completed on 2024-11-15 13:39:31
