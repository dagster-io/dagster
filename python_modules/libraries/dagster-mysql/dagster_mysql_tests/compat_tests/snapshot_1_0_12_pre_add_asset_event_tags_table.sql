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
INSERT INTO `alembic_version` VALUES ('5e139331e376');
/*!40000 ALTER TABLE `alembic_version` ENABLE KEYS */;
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
  KEY `idx_bulk_actions_selector_id` (`selector_id`(64)),
  KEY `idx_bulk_actions_status` (`status`(32)),
  KEY `idx_bulk_actions_action_type` (`action_type`)
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
  KEY `idx_run_id` (`run_id`),
  KEY `idx_step_key` (`step_key`(32)),
  KEY `idx_asset_partition` (`asset_key`(64),`partition`(64)),
  KEY `idx_event_type` (`dagster_event_type`(64),`id`),
  KEY `idx_asset_key` (`asset_key`(32))
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `event_logs`
--

LOCK TABLES `event_logs` WRITE;
/*!40000 ALTER TABLE `event_logs` DISABLE KEYS */;
INSERT INTO `event_logs` VALUES (1,'9de2a48b-74a9-4fb4-ad14-70d6db695fab','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": null, \"event_type_value\": \"PIPELINE_STARTING\", \"logging_tags\": {}, \"message\": null, \"pid\": null, \"pipeline_name\": \"succeeds_job\", \"solid_handle\": null, \"step_handle\": null, \"step_key\": null, \"step_kind_value\": null}, \"error_info\": null, \"level\": 20, \"message\": \"\", \"pipeline_name\": \"succeeds_job\", \"run_id\": \"9de2a48b-74a9-4fb4-ad14-70d6db695fab\", \"step_key\": null, \"timestamp\": 1665620459.2220001, \"user_message\": \"\"}','PIPELINE_STARTING','2022-10-13 07:20:59.222000',NULL,NULL,NULL),(2,'9de2a48b-74a9-4fb4-ad14-70d6db695fab','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"EngineEventData\", \"error\": null, \"marker_end\": null, \"marker_start\": null, \"metadata_entries\": [{\"__class__\": \"EventMetadataEntry\", \"description\": null, \"entry_data\": {\"__class__\": \"TextMetadataEntryData\", \"text\": \"66435\"}, \"label\": \"pid\"}]}, \"event_type_value\": \"ENGINE_EVENT\", \"logging_tags\": {}, \"message\": \"Started process for run (pid: 66435).\", \"pid\": null, \"pipeline_name\": \"succeeds_job\", \"solid_handle\": null, \"step_handle\": null, \"step_key\": null, \"step_kind_value\": null}, \"error_info\": null, \"level\": 20, \"message\": \"\", \"pipeline_name\": \"succeeds_job\", \"run_id\": \"9de2a48b-74a9-4fb4-ad14-70d6db695fab\", \"step_key\": null, \"timestamp\": 1665620460.9561012, \"user_message\": \"\"}','ENGINE_EVENT','2022-10-13 07:21:00.956101',NULL,NULL,NULL),(3,'9de2a48b-74a9-4fb4-ad14-70d6db695fab','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": null, \"event_type_value\": \"PIPELINE_START\", \"logging_tags\": {}, \"message\": \"Started execution of run for \\\"succeeds_job\\\".\", \"pid\": 66435, \"pipeline_name\": \"succeeds_job\", \"solid_handle\": null, \"step_handle\": null, \"step_key\": null, \"step_kind_value\": null}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"succeeds_job\", \"run_id\": \"9de2a48b-74a9-4fb4-ad14-70d6db695fab\", \"step_key\": null, \"timestamp\": 1665620463.470655, \"user_message\": \"Started execution of run for \\\"succeeds_job\\\".\"}','PIPELINE_START','2022-10-13 07:21:03.470655',NULL,NULL,NULL),(4,'9de2a48b-74a9-4fb4-ad14-70d6db695fab','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"EngineEventData\", \"error\": null, \"marker_end\": null, \"marker_start\": null, \"metadata_entries\": [{\"__class__\": \"EventMetadataEntry\", \"description\": null, \"entry_data\": {\"__class__\": \"TextMetadataEntryData\", \"text\": \"66435\"}, \"label\": \"pid\"}, {\"__class__\": \"EventMetadataEntry\", \"description\": null, \"entry_data\": {\"__class__\": \"TextMetadataEntryData\", \"text\": \"[\'succeeds\']\"}, \"label\": \"step_keys\"}]}, \"event_type_value\": \"ENGINE_EVENT\", \"logging_tags\": {}, \"message\": \"Executing steps using multiprocess executor: parent process (pid: 66435)\", \"pid\": 66435, \"pipeline_name\": \"succeeds_job\", \"solid_handle\": null, \"step_handle\": null, \"step_key\": null, \"step_kind_value\": null}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"succeeds_job\", \"run_id\": \"9de2a48b-74a9-4fb4-ad14-70d6db695fab\", \"step_key\": null, \"timestamp\": 1665620463.521247, \"user_message\": \"Executing steps using multiprocess executor: parent process (pid: 66435)\"}','ENGINE_EVENT','2022-10-13 07:21:03.521247',NULL,NULL,NULL),(5,'9de2a48b-74a9-4fb4-ad14-70d6db695fab','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"EngineEventData\", \"error\": null, \"marker_end\": null, \"marker_start\": \"step_process_start\", \"metadata_entries\": []}, \"event_type_value\": \"STEP_WORKER_STARTING\", \"logging_tags\": {\"pipeline_name\": \"succeeds_job\", \"pipeline_tags\": \"{\'.dagster/grpc_info\': \'{\\\"host\\\": \\\"localhost\\\", \\\"socket\\\": \\\"/var/folders/lr/mcmhlx2177953tcj5m7v8l3h0000gn/T/tmpqfw3zqh5\\\"}\', \'dagster/solid_selection\': \'*\'}\", \"resource_fn_name\": \"None\", \"resource_name\": \"None\", \"run_id\": \"9de2a48b-74a9-4fb4-ad14-70d6db695fab\", \"solid_name\": \"succeeds\", \"step_key\": \"succeeds\"}, \"message\": \"Launching subprocess for \\\"succeeds\\\".\", \"pid\": 66435, \"pipeline_name\": \"succeeds_job\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"succeeds\", \"parent\": null}, \"step_handle\": {\"__class__\": \"StepHandle\", \"key\": \"succeeds\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"succeeds\", \"parent\": null}}, \"step_key\": \"succeeds\", \"step_kind_value\": \"COMPUTE\"}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"succeeds_job\", \"run_id\": \"9de2a48b-74a9-4fb4-ad14-70d6db695fab\", \"step_key\": \"succeeds\", \"timestamp\": 1665620463.527574, \"user_message\": \"Launching subprocess for \\\"succeeds\\\".\"}','STEP_WORKER_STARTING','2022-10-13 07:21:03.527574','succeeds',NULL,NULL),(6,'9de2a48b-74a9-4fb4-ad14-70d6db695fab','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"EngineEventData\", \"error\": null, \"marker_end\": \"step_process_start\", \"marker_start\": null, \"metadata_entries\": [{\"__class__\": \"EventMetadataEntry\", \"description\": null, \"entry_data\": {\"__class__\": \"TextMetadataEntryData\", \"text\": \"66438\"}, \"label\": \"pid\"}]}, \"event_type_value\": \"STEP_WORKER_STARTED\", \"logging_tags\": {}, \"message\": \"Executing step \\\"succeeds\\\" in subprocess.\", \"pid\": 66438, \"pipeline_name\": \"succeeds_job\", \"solid_handle\": null, \"step_handle\": null, \"step_key\": \"succeeds\", \"step_kind_value\": null}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"succeeds_job\", \"run_id\": \"9de2a48b-74a9-4fb4-ad14-70d6db695fab\", \"step_key\": \"succeeds\", \"timestamp\": 1665620467.191471, \"user_message\": \"Executing step \\\"succeeds\\\" in subprocess.\"}','STEP_WORKER_STARTED','2022-10-13 07:21:07.191471','succeeds',NULL,NULL),(7,'9de2a48b-74a9-4fb4-ad14-70d6db695fab','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"EngineEventData\", \"error\": null, \"marker_end\": null, \"marker_start\": \"resources\", \"metadata_entries\": []}, \"event_type_value\": \"RESOURCE_INIT_STARTED\", \"logging_tags\": {}, \"message\": \"Starting initialization of resources [io_manager].\", \"pid\": 66438, \"pipeline_name\": \"succeeds_job\", \"solid_handle\": null, \"step_handle\": {\"__class__\": \"StepHandle\", \"key\": \"succeeds\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"succeeds\", \"parent\": null}}, \"step_key\": \"succeeds\", \"step_kind_value\": null}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"succeeds_job\", \"run_id\": \"9de2a48b-74a9-4fb4-ad14-70d6db695fab\", \"step_key\": \"succeeds\", \"timestamp\": 1665620467.2102, \"user_message\": \"Starting initialization of resources [io_manager].\"}','RESOURCE_INIT_STARTED','2022-10-13 07:21:07.210200','succeeds',NULL,NULL),(8,'9de2a48b-74a9-4fb4-ad14-70d6db695fab','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"EngineEventData\", \"error\": null, \"marker_end\": \"resources\", \"marker_start\": null, \"metadata_entries\": [{\"__class__\": \"EventMetadataEntry\", \"description\": null, \"entry_data\": {\"__class__\": \"PythonArtifactMetadataEntryData\", \"module\": \"dagster._core.storage.fs_io_manager\", \"name\": \"PickledObjectFilesystemIOManager\"}, \"label\": \"io_manager\"}, {\"__class__\": \"EventMetadataEntry\", \"description\": null, \"entry_data\": {\"__class__\": \"TextMetadataEntryData\", \"text\": \"0.08ms\"}, \"label\": \"io_manager:init_time\"}]}, \"event_type_value\": \"RESOURCE_INIT_SUCCESS\", \"logging_tags\": {}, \"message\": \"Finished initialization of resources [io_manager].\", \"pid\": 66438, \"pipeline_name\": \"succeeds_job\", \"solid_handle\": null, \"step_handle\": {\"__class__\": \"StepHandle\", \"key\": \"succeeds\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"succeeds\", \"parent\": null}}, \"step_key\": \"succeeds\", \"step_kind_value\": null}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"succeeds_job\", \"run_id\": \"9de2a48b-74a9-4fb4-ad14-70d6db695fab\", \"step_key\": \"succeeds\", \"timestamp\": 1665620467.217094, \"user_message\": \"Finished initialization of resources [io_manager].\"}','RESOURCE_INIT_SUCCESS','2022-10-13 07:21:07.217094','succeeds',NULL,NULL),(9,'9de2a48b-74a9-4fb4-ad14-70d6db695fab','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"ComputeLogsCaptureData\", \"log_key\": \"succeeds\", \"step_keys\": [\"succeeds\"]}, \"event_type_value\": \"LOGS_CAPTURED\", \"logging_tags\": {\"pipeline_name\": \"succeeds_job\", \"pipeline_tags\": \"{\'.dagster/grpc_info\': \'{\\\"host\\\": \\\"localhost\\\", \\\"socket\\\": \\\"/var/folders/lr/mcmhlx2177953tcj5m7v8l3h0000gn/T/tmpqfw3zqh5\\\"}\', \'dagster/solid_selection\': \'*\'}\", \"resource_fn_name\": \"None\", \"resource_name\": \"None\", \"run_id\": \"9de2a48b-74a9-4fb4-ad14-70d6db695fab\", \"solid_name\": \"succeeds\", \"step_key\": \"succeeds\"}, \"message\": \"Started capturing logs for step: succeeds.\", \"pid\": 66438, \"pipeline_name\": \"succeeds_job\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"succeeds\", \"parent\": null}, \"step_handle\": {\"__class__\": \"StepHandle\", \"key\": \"succeeds\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"succeeds\", \"parent\": null}}, \"step_key\": \"succeeds\", \"step_kind_value\": \"COMPUTE\"}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"succeeds_job\", \"run_id\": \"9de2a48b-74a9-4fb4-ad14-70d6db695fab\", \"step_key\": \"succeeds\", \"timestamp\": 1665620467.27223, \"user_message\": \"Started capturing logs for step: succeeds.\"}','LOGS_CAPTURED','2022-10-13 07:21:07.272230','succeeds',NULL,NULL),(10,'9de2a48b-74a9-4fb4-ad14-70d6db695fab','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": null, \"event_type_value\": \"STEP_START\", \"logging_tags\": {\"pipeline_name\": \"succeeds_job\", \"pipeline_tags\": \"{\'.dagster/grpc_info\': \'{\\\"host\\\": \\\"localhost\\\", \\\"socket\\\": \\\"/var/folders/lr/mcmhlx2177953tcj5m7v8l3h0000gn/T/tmpqfw3zqh5\\\"}\', \'dagster/solid_selection\': \'*\'}\", \"resource_fn_name\": \"None\", \"resource_name\": \"None\", \"run_id\": \"9de2a48b-74a9-4fb4-ad14-70d6db695fab\", \"solid_name\": \"succeeds\", \"step_key\": \"succeeds\"}, \"message\": \"Started execution of step \\\"succeeds\\\".\", \"pid\": 66438, \"pipeline_name\": \"succeeds_job\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"succeeds\", \"parent\": null}, \"step_handle\": {\"__class__\": \"StepHandle\", \"key\": \"succeeds\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"succeeds\", \"parent\": null}}, \"step_key\": \"succeeds\", \"step_kind_value\": \"COMPUTE\"}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"succeeds_job\", \"run_id\": \"9de2a48b-74a9-4fb4-ad14-70d6db695fab\", \"step_key\": \"succeeds\", \"timestamp\": 1665620467.283252, \"user_message\": \"Started execution of step \\\"succeeds\\\".\"}','STEP_START','2022-10-13 07:21:07.283252','succeeds',NULL,NULL),(11,'9de2a48b-74a9-4fb4-ad14-70d6db695fab','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"StepOutputData\", \"metadata_entries\": [], \"step_output_handle\": {\"__class__\": \"StepOutputHandle\", \"mapping_key\": null, \"output_name\": \"result\", \"step_key\": \"succeeds\"}, \"type_check_data\": {\"__class__\": \"TypeCheckData\", \"description\": null, \"label\": \"result\", \"metadata_entries\": [], \"success\": true}, \"version\": null}, \"event_type_value\": \"STEP_OUTPUT\", \"logging_tags\": {\"pipeline_name\": \"succeeds_job\", \"pipeline_tags\": \"{\'.dagster/grpc_info\': \'{\\\"host\\\": \\\"localhost\\\", \\\"socket\\\": \\\"/var/folders/lr/mcmhlx2177953tcj5m7v8l3h0000gn/T/tmpqfw3zqh5\\\"}\', \'dagster/solid_selection\': \'*\'}\", \"resource_fn_name\": \"None\", \"resource_name\": \"None\", \"run_id\": \"9de2a48b-74a9-4fb4-ad14-70d6db695fab\", \"solid_name\": \"succeeds\", \"step_key\": \"succeeds\"}, \"message\": \"Yielded output \\\"result\\\" of type \\\"Any\\\". (Type check passed).\", \"pid\": 66438, \"pipeline_name\": \"succeeds_job\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"succeeds\", \"parent\": null}, \"step_handle\": {\"__class__\": \"StepHandle\", \"key\": \"succeeds\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"succeeds\", \"parent\": null}}, \"step_key\": \"succeeds\", \"step_kind_value\": \"COMPUTE\"}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"succeeds_job\", \"run_id\": \"9de2a48b-74a9-4fb4-ad14-70d6db695fab\", \"step_key\": \"succeeds\", \"timestamp\": 1665620467.307748, \"user_message\": \"Yielded output \\\"result\\\" of type \\\"Any\\\". (Type check passed).\"}','STEP_OUTPUT','2022-10-13 07:21:07.307748','succeeds',NULL,NULL),(12,'9de2a48b-74a9-4fb4-ad14-70d6db695fab','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"HandledOutputData\", \"manager_key\": \"io_manager\", \"metadata_entries\": [{\"__class__\": \"EventMetadataEntry\", \"description\": null, \"entry_data\": {\"__class__\": \"PathMetadataEntryData\", \"path\": \"/Users/claire/dagster_home/storage/9de2a48b-74a9-4fb4-ad14-70d6db695fab/succeeds/result\"}, \"label\": \"path\"}], \"output_name\": \"result\"}, \"event_type_value\": \"HANDLED_OUTPUT\", \"logging_tags\": {\"pipeline_name\": \"succeeds_job\", \"pipeline_tags\": \"{\'.dagster/grpc_info\': \'{\\\"host\\\": \\\"localhost\\\", \\\"socket\\\": \\\"/var/folders/lr/mcmhlx2177953tcj5m7v8l3h0000gn/T/tmpqfw3zqh5\\\"}\', \'dagster/solid_selection\': \'*\'}\", \"resource_fn_name\": \"None\", \"resource_name\": \"None\", \"run_id\": \"9de2a48b-74a9-4fb4-ad14-70d6db695fab\", \"solid_name\": \"succeeds\", \"step_key\": \"succeeds\"}, \"message\": \"Handled output \\\"result\\\" using IO manager \\\"io_manager\\\"\", \"pid\": 66438, \"pipeline_name\": \"succeeds_job\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"succeeds\", \"parent\": null}, \"step_handle\": {\"__class__\": \"StepHandle\", \"key\": \"succeeds\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"succeeds\", \"parent\": null}}, \"step_key\": \"succeeds\", \"step_kind_value\": \"COMPUTE\"}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"succeeds_job\", \"run_id\": \"9de2a48b-74a9-4fb4-ad14-70d6db695fab\", \"step_key\": \"succeeds\", \"timestamp\": 1665620467.317577, \"user_message\": \"Handled output \\\"result\\\" using IO manager \\\"io_manager\\\"\"}','HANDLED_OUTPUT','2022-10-13 07:21:07.317577','succeeds',NULL,NULL),(13,'9de2a48b-74a9-4fb4-ad14-70d6db695fab','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"StepSuccessData\", \"duration_ms\": 17.79951000000013}, \"event_type_value\": \"STEP_SUCCESS\", \"logging_tags\": {\"pipeline_name\": \"succeeds_job\", \"pipeline_tags\": \"{\'.dagster/grpc_info\': \'{\\\"host\\\": \\\"localhost\\\", \\\"socket\\\": \\\"/var/folders/lr/mcmhlx2177953tcj5m7v8l3h0000gn/T/tmpqfw3zqh5\\\"}\', \'dagster/solid_selection\': \'*\'}\", \"resource_fn_name\": \"None\", \"resource_name\": \"None\", \"run_id\": \"9de2a48b-74a9-4fb4-ad14-70d6db695fab\", \"solid_name\": \"succeeds\", \"step_key\": \"succeeds\"}, \"message\": \"Finished execution of step \\\"succeeds\\\" in 17ms.\", \"pid\": 66438, \"pipeline_name\": \"succeeds_job\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"succeeds\", \"parent\": null}, \"step_handle\": {\"__class__\": \"StepHandle\", \"key\": \"succeeds\", \"solid_handle\": {\"__class__\": \"SolidHandle\", \"name\": \"succeeds\", \"parent\": null}}, \"step_key\": \"succeeds\", \"step_kind_value\": \"COMPUTE\"}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"succeeds_job\", \"run_id\": \"9de2a48b-74a9-4fb4-ad14-70d6db695fab\", \"step_key\": \"succeeds\", \"timestamp\": 1665620467.324287, \"user_message\": \"Finished execution of step \\\"succeeds\\\" in 17ms.\"}','STEP_SUCCESS','2022-10-13 07:21:07.324287','succeeds',NULL,NULL),(14,'9de2a48b-74a9-4fb4-ad14-70d6db695fab','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"EngineEventData\", \"error\": null, \"marker_end\": null, \"marker_start\": null, \"metadata_entries\": [{\"__class__\": \"EventMetadataEntry\", \"description\": null, \"entry_data\": {\"__class__\": \"TextMetadataEntryData\", \"text\": \"66435\"}, \"label\": \"pid\"}]}, \"event_type_value\": \"ENGINE_EVENT\", \"logging_tags\": {}, \"message\": \"Multiprocess executor: parent process exiting after 4.2s (pid: 66435)\", \"pid\": 66435, \"pipeline_name\": \"succeeds_job\", \"solid_handle\": null, \"step_handle\": null, \"step_key\": null, \"step_kind_value\": null}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"succeeds_job\", \"run_id\": \"9de2a48b-74a9-4fb4-ad14-70d6db695fab\", \"step_key\": null, \"timestamp\": 1665620467.726439, \"user_message\": \"Multiprocess executor: parent process exiting after 4.2s (pid: 66435)\"}','ENGINE_EVENT','2022-10-13 07:21:07.726439',NULL,NULL,NULL),(15,'9de2a48b-74a9-4fb4-ad14-70d6db695fab','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": null, \"event_type_value\": \"PIPELINE_SUCCESS\", \"logging_tags\": {}, \"message\": \"Finished execution of run for \\\"succeeds_job\\\".\", \"pid\": 66435, \"pipeline_name\": \"succeeds_job\", \"solid_handle\": null, \"step_handle\": null, \"step_key\": null, \"step_kind_value\": null}, \"error_info\": null, \"level\": 10, \"message\": \"\", \"pipeline_name\": \"succeeds_job\", \"run_id\": \"9de2a48b-74a9-4fb4-ad14-70d6db695fab\", \"step_key\": null, \"timestamp\": 1665620467.7534678, \"user_message\": \"Finished execution of run for \\\"succeeds_job\\\".\"}','PIPELINE_SUCCESS','2022-10-13 07:21:07.753468',NULL,NULL,NULL),(16,'9de2a48b-74a9-4fb4-ad14-70d6db695fab','{\"__class__\": \"EventLogEntry\", \"dagster_event\": {\"__class__\": \"DagsterEvent\", \"event_specific_data\": {\"__class__\": \"EngineEventData\", \"error\": null, \"marker_end\": null, \"marker_start\": null, \"metadata_entries\": []}, \"event_type_value\": \"ENGINE_EVENT\", \"logging_tags\": {}, \"message\": \"Process for run exited (pid: 66435).\", \"pid\": null, \"pipeline_name\": \"succeeds_job\", \"solid_handle\": null, \"step_handle\": null, \"step_key\": null, \"step_kind_value\": null}, \"error_info\": null, \"level\": 20, \"message\": \"\", \"pipeline_name\": \"succeeds_job\", \"run_id\": \"9de2a48b-74a9-4fb4-ad14-70d6db695fab\", \"step_key\": null, \"timestamp\": 1665620467.7794182, \"user_message\": \"\"}','ENGINE_EVENT','2022-10-13 07:21:07.779418',NULL,NULL,NULL);
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
INSERT INTO `instance_info` VALUES ('80859556-21b8-4876-83e6-830b4a61bc1d');
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
INSERT INTO `run_tags` VALUES (1,'9de2a48b-74a9-4fb4-ad14-70d6db695fab','.dagster/repository','more_toys_repository@dagster_test.toys.repo'),(2,'9de2a48b-74a9-4fb4-ad14-70d6db695fab','dagster/solid_selection','*'),(3,'9de2a48b-74a9-4fb4-ad14-70d6db695fab','.dagster/grpc_info','{\"host\": \"localhost\", \"socket\": \"/var/folders/lr/mcmhlx2177953tcj5m7v8l3h0000gn/T/tmpqfw3zqh5\"}');
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
INSERT INTO `runs` VALUES (1,'9de2a48b-74a9-4fb4-ad14-70d6db695fab','1deccee186d4c5a6c7e9d4859e07c550c2c2dd72','succeeds_job',NULL,'SUCCESS','{\"__class__\": \"PipelineRun\", \"asset_selection\": null, \"execution_plan_snapshot_id\": \"0bbe5d437908a00de4548c6f4dbe4a00ed54c9e8\", \"external_pipeline_origin\": {\"__class__\": \"ExternalPipelineOrigin\", \"external_repository_origin\": {\"__class__\": \"ExternalRepositoryOrigin\", \"repository_location_origin\": {\"__class__\": \"ManagedGrpcPythonEnvRepositoryLocationOrigin\", \"loadable_target_origin\": {\"__class__\": \"LoadableTargetOrigin\", \"attribute\": null, \"executable_path\": null, \"module_name\": \"dagster_test.toys.repo\", \"package_name\": null, \"python_file\": null, \"working_directory\": null}, \"location_name\": \"dagster_test.toys.repo\"}, \"repository_name\": \"more_toys_repository\"}, \"pipeline_name\": \"succeeds_job\"}, \"has_repository_load_data\": false, \"mode\": \"default\", \"parent_run_id\": null, \"pipeline_code_origin\": {\"__class__\": \"PipelinePythonOrigin\", \"pipeline_name\": \"succeeds_job\", \"repository_origin\": {\"__class__\": \"RepositoryPythonOrigin\", \"code_pointer\": {\"__class__\": \"ModuleCodePointer\", \"fn_name\": \"more_toys_repository\", \"module\": \"dagster_test.toys.repo\", \"working_directory\": \"/Users/claire/dagster\"}, \"container_context\": {}, \"container_image\": null, \"entry_point\": [\"dagster\"], \"executable_path\": \"/Users/claire/.virtualenvs/dagster-dev-3.9/bin/python\"}}, \"pipeline_name\": \"succeeds_job\", \"pipeline_snapshot_id\": \"1deccee186d4c5a6c7e9d4859e07c550c2c2dd72\", \"root_run_id\": null, \"run_config\": {}, \"run_id\": \"9de2a48b-74a9-4fb4-ad14-70d6db695fab\", \"solid_selection\": null, \"solids_to_execute\": null, \"status\": {\"__enum__\": \"PipelineRunStatus.SUCCESS\"}, \"step_keys_to_execute\": null, \"tags\": {\".dagster/grpc_info\": \"{\\\"host\\\": \\\"localhost\\\", \\\"socket\\\": \\\"/var/folders/lr/mcmhlx2177953tcj5m7v8l3h0000gn/T/tmpqfw3zqh5\\\"}\", \"dagster/solid_selection\": \"*\"}}',NULL,NULL,'2022-10-12 17:20:59.217066','2022-10-13 00:21:07.771650',1665620463.515243,1665620467.77165);
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
INSERT INTO `secondary_indexes` VALUES (1,'run_partitions','2022-10-12 17:20:46.276165','2022-10-12 17:20:46.272602'),(2,'run_repo_label_tags','2022-10-12 17:20:46.312146','2022-10-12 17:20:46.307311'),(3,'bulk_action_types','2022-10-12 17:20:46.327267','2022-10-12 17:20:46.323582'),(4,'run_start_end_overwritten','2022-10-12 17:20:46.374806','2022-10-12 17:20:46.371241'),(5,'asset_key_table','2022-10-12 17:20:46.568788','2022-10-12 17:20:46.564050'),(6,'asset_key_index_columns','2022-10-12 17:20:46.601679','2022-10-12 17:20:46.579971'),(7,'schedule_jobs_selector_id','2022-10-12 17:20:46.829684','2022-10-12 17:20:46.822652'),(8,'schedule_ticks_selector_id','2022-10-12 17:20:46.907758','2022-10-12 17:20:46.904241');
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
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `snapshots`
--

LOCK TABLES `snapshots` WRITE;
/*!40000 ALTER TABLE `snapshots` DISABLE KEYS */;
INSERT INTO `snapshots` VALUES (1,'1deccee186d4c5a6c7e9d4859e07c550c2c2dd72',_binary 'xœ\í]io\Ü\Èý+\Ä\äC`-³y\÷~“m9+Ä‘–A°2\è>ª5\\sH.\ÙCÿ=\Ý<\æ\ÉQ\Ïh8’-°–H\öù\êUuu\õ¡¯“0d1)Š0œülL~2ˆ£.’Ó´œüdLXšˆ\è:,\Øf$,º/?_\×\ó¾®\Ó]\Ô\ÉV\ó“8»2\Ô\ë\Î\ÃO0¯8N\æC]Î³ºªË£¬Œ\ÒD&Hª8–/!©f\á\r‰+(–/E1_y¾Žn 	2U²ªN¾lj_<E	oQy§\rÿ”ŸŽ\Ïþ3¹•iFb’‡m–¶ŽR¦\n3’“™\êWW¹J~œ\çd~t1%9ˆƒ	\÷©ïº–\ã\"¹.7)\'4\ð-›yp›n\Ç\ä]T”F*Œª\Û	\É\ö]\äŽ\õj!ÿþý\ñV\Øÿ>Ù²!V$U\æQrýp	4\Å\ì\ÙEyc!\ÖTP#\ñ*M\ãØ­·Mm\Ëþ.5úy\ñúø\Ý\ñûžŽ\öåº¨S\Ôù^Ÿ¿«s\r\ë\í\Û8%ƒnÿ 4\Õ-QX>\Ã\Ûw\çÇ—\÷\àpšU\Ùƒ\îiDN\Ï\î\ë“ø·Dv\ìHQ\ó\Å\ÄÀ\Ê4?¢\àr\Ô\ÆxÄ±™+,\0F„k	ù>B\Ô\Å\Ý\Ö-\Çš¾ü\áog§\çgÛ™NÛ·oÚ‡»Ò©Uf\ÙGnš\Ä\öÁLŸ\Û>\Ã\ÂÃŒy\Æ>sˆ+‚|\\f?	\ñ\ì\Ú\ö\Ñå³°CÛ·\íI}^v‘`cŠ}Ä‘Eø&±x˜6ù¿g;\È\ç¦o¹OB<»µ|t\á´rû–}#šf\ô_\öLG9H˜c¬dM¨…,\Ósl—Z–\åøLH5\r,\ïiØ¶?º€–^\Û\ökd\ÔeCTP\äù6ýÀ$\Ä\ó±‹\åo&\ó\å\ó\\ž­5’@~\ï-\ô­ú¼,U*.\Ã,Oo\"\n™2¯`\åK]zHŠ\ð\"MÂ¢\ÌUI_o›aVQ^&H\\¨\Ò:_G¡±ü\Ôa\ß1£vý9±1±\\\ð¨CMn[®K\ìz&\n°I—\Ì\ÄJžO¯o\ì¥k\îÑ¡­É¥«0\'\ïN^_ž\÷ùc\÷Î—²Á$\Ü6©2DR+\na\È(×§®\÷2þj’ƒ4P\\©¶_uÒ®Ÿno{839ù¬*Á ql%d…%1\ni\\b0dýŠ\âhr/¯¢$l\÷S\Ëq„\åæº¦‹9ArÄ€@b\ï1\É_N¥¹m[–‹Ø¸Zs5™‘/*^Äª<‡¤TÀ˜?»\Ã„Mk\Üj\Øù/d‹*o\ÝL68Úˆž@Ž\íxŒ»œû \"µ-n\á\0c\éù\òp`b\ê\ë+¦¶R1\Â%BÒ‚›²K\Äe¾\0.(¦œù®²>¦\Çi\ðý)f‡š\â«Œr\n\Æ*	¨\é•\æF™Jv‘¼4ŠŠ¶¡0*¥ž\ÆG‘\æŸ\n\Èo ÿ¨Á²e\ê\r¥Òµ–\àS\Ë\ä\ÂF–\çü\Ï972=S \ê`“›®s\ðq\í\á@ùœ\è`T\'<\ÔØ¨\Í\öCª\à#OžvSÁNŒ›¨\ÕÖ¤\á2µ<\í8¡\Ê\Ô›ú¶\ÔÇ²Ä•z0W\Ø\nl\Î0f{r\Æj\í¬1£\ö+‹Ø§~ÄžÕ…\Ýí˜š\Ñj«\æ\Þ\'\âûP\ÍGŽ\n>«\æ³jŽ£šu¤V[7\÷aÞ‡n>rHøY7Ÿus\Ýl¢\ô\ÚÊ¹\÷\å…}(\ç#‡œŸ•\óY9\ÇQ\Îv@[;\÷¾|±\ít-Al¢\ê¶Ç®%AµK§0·œÀ\÷]\ßyZ\Ñ\Øg\í|4\í\Ô&».¯Iva	\ð¸\à\Ì3	ÂŽO€\Ï\äX\éY\Ô\ñMÏ¥\Ìy&û3ÙŸj\Ïz‡\"µ\ÝU[5µµ\àªYK\Ä\í:žgS\Ì\Z*8b4\0\Û\r|\Ï\Æ\ÈÂ®ü\×OJ/u\êW“Ó³·\çW“ž°ú\åŒ8½¾†ü¯…QNs(¦i\Ì5¢\ä2S\Ã\r\ÄCþÈˆWN®‹\òÁ.©VªÝ²\ó´\Ê\Ûþi\ô©þ¹£{µƒt9}ùþ\ô\õex\ñ\Ë\ñ¯\'àµ€Àvm\îQ×±c‚pLQN	Pl	\ÏÁ@)&\ß¯¿^-i¨\Öi;ž«\Å\\%¥\æÝ‚+}\ËJŠ,mK\ãTCþLŠ4}\Þ4gúÍ¼6%4¦+Ëƒ2¹¾\ì¦\Í\óÈ¾1Ì¤ƒ\ÅY\È\ê\"\ê\Ì\÷5\ÛWU—/¢\ÄQ\Å\\’kfœž3’\ÉiEIirˆƒ\Â 	7šm7\ò©\é@» Yû\ò}i\Ø\Þ\Ï1ß±Á\ñ±‰\×e\Ôr\\9Ÿ\ãÜ³m°O£&\ÛI\ó ³ˆ)\'­\\v\Ò\n¸ä»\ã–	\ÌLN‹r¬\ïotVRV–³\Û\r\';n\í\Z0E[\ïø\ÐcŠ¶LÊ”\ñ\ÎA}7ó«»´¶H:H\íi²-\ö}BkO´\Ð\Ý}\öC\Ðb\òû›“_ßŸ¼>¾<y\óAcû\É?A–©lbZzÁ\ã\î\Ë[\ßr\×3\òþ{\n\åT±\íN=ƒ\ä`´™Œ47’´<2^\Í;‡î§¾t\Z\Ãm›kP[´\÷³jj‹./«-	\ìy€ØŽ-§\æÈµ¥·é˜¦ .¦A€\É(“\á\Ä)\ê\×_\'i¦~N¤CI5º=Ø\Ü¤\í^\Ðo\Æ\ç\Ý\ö\örz¹±mš~n·\ß\Ö|mv—r\ãsTN\ëý¸y•h°·\É\rÔ´‡\ìG\Üá§€h&_…³¨4fw\éþ\Ûb\ÑÒØ•c€\ÇM\Ñ p˜\ï	\Ç!¡¾`a2Ó±­^Q1À‡¿dd·\ËhF­¸P*€„4|RI”ý“\íƒRg³±Rª^L`\å\íS@„)¦\Ä3©0Sp\É\r$$g\òÜ±1Y\ÎxtP©gJ\Ô\Ü]::i•³\Ö\æG³,†™\Ô\Ï\í\ÕhQP?P\Ús$\Í1@\×\Úv\Ð\rQÿ“V@Ÿ”\ÓEµ!=´ \õ¶}ÿ‚žœ|\É\âˆEe<7ŠX$\æÍ¦\ò”W±´ejd9\Ä)\á\ê@‡ú²\Ü6dœ+\ôs¤ªV¿Amh\ÊÏ©Á”\ÏR›\ã. \Ø\Æ{\"±(Z¥•^j[m$\ÝQ\ãT\ÔU¼i¢”\Æ)5>“\ÂP\ÕK«%\òt&mV“¿®\Ñ(Tl»y!Zº\ö¶\å\É\Zš¤\Û\Ø\ç\Ç.}T¬$½\ß¶iÃ¶ùß¬\÷¬\Þ¡\Í=¦”ÿ\Ú´‚ÿ$i­\ðm\éA­}€c$AkA§\ÝÈƒB–¬\ÜL`x®‡©š˜ú˜3†À9œq(d\Ü	\á£\éÑ“X\×ÿfjP•YU™ú\í\Â{z–B›X‡¥»\î\ì\ðÿjHP\ë¢ëœº“š¤Ð…ÿ ¤\Ð>‚û”H¡3\å6‡\öQT3*\ÒTt\'™•{¬\Ö7gd®&\Ò\Æ2\Ï\×c¯r¶](³€RyÔ´9¸™CY\åI\ã«b?®†\Ö\Ôj(Ëª¥URþ\í\ï:‡5\×\Ãp½ç½žc\Ö[Å¬=*µml‚8«\çv\0,RªY\Í*B\íQÞ†\\*¯Jp`L\Ë2+~~ù’§¬8\Ê\æ\å4MŽ\Òüú¥ý2ŽhN\òùË»l›–³ø/’?%|)‹$\á/\ê\Ä/fRf)\×	¥\Õ\é\Ã&ý úÚ§|\õŒ£¶:¬qÔ~o\â¨w±t\Ñßµ®o¤I]Š8»Þ†9¹w¬lŸ\×/\0\\¹\ær-v§\Û\Ý¯T0ýc\ÓM€·\ê[¬	\ë4ª\É\Ò\Î1\Øpn3R\í;\ë’ß½w­P½\ÛqWŠÝ¨<*²˜\Ì\ï\Þ}+ùN\Õ©(Y\êŽ\Æ}¸+µ®]ˆ[«\ò\îr\à‡\ì\"žÉ¡$¤©ø\ïpy\Û¸\Ó\ïžº6\\wº+\ÈÝ†P\Þx\Å\é]˜W8Ý\ô^nyú®«C\Ø\\³º+ø‹\ë\n7 ¿ùjÕ‡Àÿ€[\Ç\Â\Ñ\Ù!\ô\Þ\ïº+üí…„À\ßt§\ëC \ßù†Æ±€?M6\Â~–ª\ÅÎž‘uW\è»7Ã¿’JKgç—¿t#cŸ\Ú\Æƒ\Ø&\èi\å2C.Ç®À,=ˆ\r¸\Ü\ãf<„™¹r,r.»\Û+…\ÆÙLù\Î+«|£$6¿\èR¯º8µ—F\ÉMÊˆTSR«¡ž.\Òu2Ž’¬*Ãº1]\Æ,ù\\v\'b\áŒdÙš\ç\ÞT)gaŸ\ß|\í\õî¥”\'u”\à\Ã\í»®s’M{\ËÿH\ë`—ú\Û	\äz\r±NKRu\Ö!þ%¼±‘\ÞÍŽ™Å¼«“¬Ô„¸\Ãf&¦r\r9\ô\Ïg>\îžùØ¹qwc²\õüoqwi“_¥ë¶±l”\èû6\Ñ2}\ÄÕ•œ\Û\è9¡QK\"OÓ²û“$»m\ôY\è]#°0AQ©\Þhmø\Þ,“®ÿ\á•Y–Q)\Í\ÉÂ¨­\ÙÁž\×\ÅÿÀ\Ä\é\nl‡Š;\õ™úfm#n\çu’Us¼:Q_Ÿ/\õ¯¢Vº·q\óR{ !h›*\\ˆ\Åøü\íPµ|üª\"þd','PIPELINE'),(2,'0bbe5d437908a00de4548c6f4dbe4a00ed54c9e8',_binary 'xœ­SÁj1ý•°\çRb\ÇIo¥\n¡\Ä\à\öd\Ì ¤q\"¢•Ti”vc\ö\ß;³+¯&\é©\×7\óž\Þ\Ì<\í\0\íT\Î\0Í§³\æ\æ7\êB6ø•S~\íU\ÌšgJdwJS†ˆ)\ÛLh¸ŸRA.\âÀ\n	¼jQd\Ú\â\È\ÖCLA#\ëšD\ÍzKV9x\ôá—‡LŠ„¶\é\åVŠ“¡\õ\Ð\Ä\\\Ó\ñ+VC«b´þ>±g<ª„ž&1_œ4\á“\r%CBJ(\"l#M¤„\Êt\n\Å2‚la—\Â3úŒ4\Ø\Øl¥çµ\rždÁ\ç©mDg=B®+\ËifµFœ]]š½P—z‰\×\æ\âjq\çK½Xœë¹ž³œ\ËTµª3vx\÷»\êe¸M“‹H›\Ülk\×`gÿ\Î5\×\Ü \×w_g\Ý•µ¥s’\ÈzSW¾´£”(\Ür\áã—»o«\ßo\Z¼ERF‘\Ë[$\Ûü§Ÿ»¡\í\àÊ¨{ž\"u¡šú\ì;)B•0s¬šá¨SH\ó\ë\Ô¥W\Ç.	p–‹Ž\Ê56Ã€2²S.\ã\Õ|½þ,6fžUœ\á²kŽ²}\Æc\ÈKp\ÖÀƒ\òÆ½‘\ìµT¿ŽÅ“O0¦¹z\íû\í_š5a§Œ!*\ï¾\È\Å\ãƒoýf„Týœý¶ÿM?°','EXECUTION_PLAN');
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

-- Dump completed on 2022-10-12 17:23:43
