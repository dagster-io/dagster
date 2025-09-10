from dagster_omni.objects import OmniUser

from dagster_omni_tests.utils import create_sample_user, get_sample_users_api_response


class TestOmniUser:
    """Tests for OmniUser object creation and parsing."""

    def test_from_json_complete_data(self):
        """Test creating OmniUser from complete JSON data."""
        json_data = {
            "id": "user-789",
            "displayName": "Alice Cooper",
            "userName": "alice@example.com",
            "active": True,
            "emails": [{"value": "alice@example.com", "primary": True, "type": "work"}],
            "groups": [{"display": "Users", "value": "user-group-id"}],
            "meta": {
                "created": "2023-03-01T00:00:00Z",
                "lastModified": "2023-08-01T00:00:00Z",
            },
        }

        user = OmniUser.from_json(json_data)

        assert user.id == "user-789"
        assert user.name == "Alice Cooper"
        assert user.display_name == "Alice Cooper"
        assert user.user_name == "alice@example.com"
        assert user.active is True
        assert user.primary_email == "alice@example.com"
        assert user.groups == ["Users"]
        assert user.created == "2023-03-01T00:00:00Z"
        assert user.last_modified == "2023-08-01T00:00:00Z"

    def test_from_json_fallback_to_username(self):
        """Test name falls back to userName when displayName is missing."""
        json_data = {
            "id": "user-101",
            "userName": "system@example.com",
            "active": True,
        }

        user = OmniUser.from_json(json_data)

        assert user.id == "user-101"
        assert user.name == "system@example.com"
        assert user.user_name == "system@example.com"
        assert user.display_name == ""

    def test_from_json_empty_strings(self):
        """Test handling empty string values."""
        json_data = {
            "id": "user-102",
            "displayName": "",
            "userName": "",
        }

        user = OmniUser.from_json(json_data)

        assert user.id == "user-102"
        assert user.name == ""
        assert user.display_name == ""
        assert user.user_name == ""

    def test_from_json_minimal_data(self):
        """Test creating OmniUser from minimal JSON data with defaults."""
        json_data = {"id": "user-456"}

        user = OmniUser.from_json(json_data)

        assert user.id == "user-456"
        assert user.name == ""
        assert user.display_name == ""
        assert user.user_name == ""
        assert user.active is True
        assert user.primary_email is None
        assert user.groups == []
        assert user.created == ""
        assert user.last_modified == ""

    def test_from_json_partial_meta(self):
        """Test handling partial meta information."""
        json_data = {
            "id": "user-123",
            "displayName": "Jane Smith",
            "userName": "jane@example.com",
            "active": False,
            "meta": {"created": "2023-02-01T00:00:00Z"},
        }

        user = OmniUser.from_json(json_data)

        assert user.display_name == "Jane Smith"
        assert user.user_name == "jane@example.com"
        assert user.active is False
        assert user.created == "2023-02-01T00:00:00Z"
        assert user.last_modified == ""

    def test_empty_emails_and_groups(self):
        """Test handling empty emails and groups arrays."""
        json_data = {
            "id": "user-123",
            "displayName": "Bob Wilson",
            "userName": "bob@example.com",
            "emails": [],
            "groups": [],
        }

        user = OmniUser.from_json(json_data)

        assert user.display_name == "Bob Wilson"
        assert user.user_name == "bob@example.com"
        assert user.primary_email is None
        assert user.groups == []

    def test_sample_user_helpers(self):
        """Test the sample user creation helpers work correctly."""
        user = create_sample_user()
        assert user.id == "user-123"
        assert user.name == "John Doe"
        assert user.display_name == "John Doe"
        assert user.user_name == "john.doe@example.com"
        assert user.active is True

        # Test with custom values
        custom_user = create_sample_user("custom-id", "Custom Name", "Custom Display")
        assert custom_user.id == "custom-id"
        assert custom_user.name == "Custom Name"
        assert custom_user.display_name == "Custom Display"

    def test_real_api_response_format(self):
        """Test parsing users from actual API response format."""
        api_response = get_sample_users_api_response()
        users = [OmniUser.from_json(user_data) for user_data in api_response["Resources"]]

        assert len(users) == 2

        # Test first user (Blobby)
        user1 = users[0]
        assert user1.id == "9e8719d9-276a-4964-9395-a493189a247c"
        assert user1.name == "Blobby"
        assert user1.display_name == "Blobby"
        assert user1.user_name == "blobby@example.com"
        assert user1.active is True
        assert user1.primary_email == "blobby@example.com"
        assert user1.groups == ["Admins", "Analysts"]
        assert user1.created == "2023-01-01T00:00:00Z"
        assert user1.last_modified == "2023-06-01T00:00:00Z"

        # Test second user (Jane Smith)
        user2 = users[1]
        assert user2.id == "7f4219b8-165a-3854-8295-b483289b148d"
        assert user2.name == "Jane Smith"
        assert user2.display_name == "Jane Smith"
        assert user2.user_name == "jane.smith@example.com"
        assert user2.active is True
        assert user2.primary_email == "jane.smith@example.com"
        assert user2.groups == ["Analysts"]
        assert user2.created == "2023-02-15T00:00:00Z"
        assert user2.last_modified == "2023-07-01T00:00:00Z"
