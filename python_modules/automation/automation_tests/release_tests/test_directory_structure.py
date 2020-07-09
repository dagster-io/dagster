from automation.release.dagster_module_publisher import DagsterModulePublisher


def test_directory_structure():
    dmp = DagsterModulePublisher()
    dmp.check_directory_structure()
