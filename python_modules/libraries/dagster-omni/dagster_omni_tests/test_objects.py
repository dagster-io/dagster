from dagster_omni.objects import OmniLabel


class TestOmniLabel:
    def test_from_json_with_string(self):
        """Test OmniLabel.from_json handles string labels from documents endpoint."""
        label = OmniLabel.from_json("Marketing")

        assert label.name == "Marketing"
        assert label.verified is False

    def test_from_json_with_dict(self):
        """Test OmniLabel.from_json handles dict labels from labels endpoint."""
        label = OmniLabel.from_json({"name": "Production", "verified": True})

        assert label.name == "Production"
        assert label.verified is True

    def test_from_json_with_dict_unverified(self):
        """Test OmniLabel.from_json handles unverified dict labels."""
        label = OmniLabel.from_json({"name": "Draft", "verified": False})

        assert label.name == "Draft"
        assert label.verified is False
